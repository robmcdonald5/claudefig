"""Preset service layer for business logic.

This module provides reusable business logic for preset management,
separated from data access (repositories) and UI (CLI/TUI).
"""

import re
from typing import Any

from claudefig.exceptions import (
    BuiltInModificationError,
    FileReadError,
    PresetExistsError,
    TemplateNotFoundError,
)
from claudefig.models import Preset, PresetSource, ValidationResult
from claudefig.repositories import AbstractPresetRepository


def list_presets(
    repo: AbstractPresetRepository,
    file_type: str | None = None,
    source: PresetSource | None = None,
) -> list[Preset]:
    """List available presets with optional filtering.

    Args:
        repo: Preset repository to query.
        file_type: Optional filter by file type (e.g., "claude_md").
        source: Optional filter by source (BUILT_IN, USER, PROJECT).

    Returns:
        List of Preset objects matching filters, sorted by type and name.
    """
    return repo.list_presets(file_type=file_type, source=source)


def get_preset(repo: AbstractPresetRepository, preset_id: str) -> Preset | None:
    """Get a specific preset by ID.

    Args:
        repo: Preset repository to query.
        preset_id: Preset identifier in format "file_type:preset_name".

    Returns:
        Preset object if found, None otherwise.
    """
    return repo.get_preset(preset_id)


def create_preset(
    repo: AbstractPresetRepository,
    preset: Preset,
    source: PresetSource = PresetSource.USER,
) -> Preset:
    """Create a new preset.

    Business logic:
    1. Validate preset data
    2. Check for duplicates
    3. Add to repository

    Args:
        repo: Preset repository to save to.
        preset: Preset object to create.
        source: Where to store (USER or PROJECT, not BUILT_IN).

    Returns:
        The created preset.

    Raises:
        BuiltInModificationError: If trying to add to BUILT_IN source.
        PresetExistsError: If preset already exists.
    """
    # Validate source
    if source == PresetSource.BUILT_IN:
        raise BuiltInModificationError("preset", "create")

    # Check for duplicates
    if repo.exists(preset.id):
        raise PresetExistsError(preset.id)

    # Add to repository
    repo.add_preset(preset, source)

    return preset


def delete_preset(repo: AbstractPresetRepository, preset_id: str) -> None:
    """Delete a preset.

    Args:
        repo: Preset repository.
        preset_id: ID of preset to delete.

    Raises:
        FileNotFoundError: If preset doesn't exist.
        ValueError: If trying to delete a built-in preset.
    """
    repo.delete_preset(preset_id)


def render_preset(
    repo: AbstractPresetRepository, preset: Preset, variables: dict[str, Any] | None = None
) -> str:
    """Render a preset template with variable substitution.

    Variables are merged with priority:
    1. Provided variables (highest)
    2. Preset default variables
    3. Empty string fallback

    Args:
        repo: Preset repository (to load template content).
        preset: Preset to render.
        variables: Variables to substitute in template.

    Returns:
        Rendered template content.

    Raises:
        FileNotFoundError: If template file doesn't exist.
        IOError: If template cannot be read.
    """
    # Load template content
    template_content = repo.get_template_content(preset)

    # Merge variables (provided overrides preset defaults)
    merged_vars = preset.variables.copy()
    if variables:
        merged_vars.update(variables)

    # Simple variable substitution: {variable_name} -> value
    rendered = template_content
    for var_name, var_value in merged_vars.items():
        placeholder = f"{{{var_name}}}"
        rendered = rendered.replace(placeholder, str(var_value))

    return rendered


def extract_template_variables(template_content: str) -> set[str]:
    """Extract variable names from template content.

    Finds all {variable_name} patterns.

    Args:
        template_content: Template content to analyze.

    Returns:
        Set of variable names found in the template.

    Example:
        >>> extract_template_variables("Hello {name}, you are {age} years old")
        {'name', 'age'}
    """
    # Find all {variable_name} patterns
    pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
    matches = re.findall(pattern, template_content)
    return set(matches)


def validate_preset_variables(
    repo: AbstractPresetRepository,
    preset: Preset,
    variables: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate that preset has all required template variables.

    Checks:
    - Template file exists
    - All variables used in template are defined
    - Warns about unused variables

    Args:
        repo: Preset repository (to load template).
        preset: Preset to validate.
        variables: Variables that will be provided during rendering.

    Returns:
        ValidationResult with any errors or warnings.
    """
    result = ValidationResult(valid=True)

    # If no template file, nothing to validate
    if not preset.template_path:
        return result

    try:
        # Load template content
        content = repo.get_template_content(preset)

        # Extract variables from template
        template_vars = extract_template_variables(content)

        # Merge preset variables with provided variables
        available_vars = set(preset.variables.keys())
        if variables:
            available_vars.update(variables.keys())

        # Check for missing variables
        missing_vars = template_vars - available_vars
        if missing_vars:
            for var in sorted(missing_vars):
                result.add_warning(
                    f"Template uses variable '{var}' but no default value is provided"
                )

        # Check for unused variables (in preset but not in template)
        unused_vars = set(preset.variables.keys()) - template_vars
        if unused_vars:
            for var in sorted(unused_vars):
                result.add_warning(
                    f"Preset defines variable '{var}' but it's not used in the template"
                )

    except TemplateNotFoundError as e:
        result.add_error(f"Template file not found: {e}")
    except FileReadError as e:
        result.add_error(f"Failed to read template file: {e}")
    except (FileNotFoundError, IOError) as e:
        # Catch any other file-related exceptions (for backward compatibility)
        result.add_error(f"Failed to read template file: {e}")
    except Exception as e:
        result.add_error(f"Unexpected error validating template: {type(e).__name__}: {e}")

    return result


def resolve_preset_variables(
    repo: AbstractPresetRepository, preset: Preset
) -> dict[str, Any]:
    """Resolve preset variables including inheritance chain.

    If preset extends another preset, merge variables from parent(s).
    Child variables override parent variables.

    Args:
        repo: Preset repository (to load parent presets).
        preset: Preset to resolve variables for.

    Returns:
        Merged variables dictionary.

    Raises:
        ValueError: If circular dependency detected.

    Note:
        This is a simplified version. Full implementation would:
        - Check for circular dependencies
        - Walk entire inheritance chain
        - Handle missing parent presets gracefully
    """
    if not preset.extends:
        # No inheritance, return preset's own variables
        return preset.variables.copy()

    # Load parent preset
    parent = repo.get_preset(preset.extends)
    if not parent:
        # Parent not found, return own variables
        return preset.variables.copy()

    # Recursively resolve parent variables
    parent_vars = resolve_preset_variables(repo, parent)

    # Merge: parent variables + child variables (child overrides)
    merged = parent_vars.copy()
    merged.update(preset.variables)

    return merged
