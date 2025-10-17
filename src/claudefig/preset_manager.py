"""Preset management for claudefig."""

import sys
from pathlib import Path
from typing import Any, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from claudefig.exceptions import CircularDependencyError
from claudefig.models import FileType, Preset, PresetSource, ValidationResult


class PresetManager:
    """Manages presets for file generation.

    Presets can come from three sources:
    1. Built-in: Shipped with claudefig package
    2. User: Stored in ~/.claudefig/presets/
    3. Project: Stored in .claudefig/presets/ (gitignored)
    """

    def __init__(
        self,
        user_presets_dir: Optional[Path] = None,
        project_presets_dir: Optional[Path] = None,
    ):
        """Initialize preset manager.

        Args:
            user_presets_dir: Path to user presets directory (default: ~/.claudefig/presets/)
            project_presets_dir: Path to project presets directory (default: .claudefig/presets/)
        """
        self.user_presets_dir = user_presets_dir or (
            Path.home() / ".claudefig" / "presets"
        )
        self.project_presets_dir = project_presets_dir or (
            Path.cwd() / ".claudefig" / "presets"
        )

        # Cache for loaded presets
        self._preset_cache: dict[str, Preset] = {}
        self._cache_loaded = False
        self._load_errors: list[str] = []  # Track errors during preset loading

    def list_presets(
        self,
        file_type: Optional[FileType] = None,
        source: Optional[PresetSource] = None,
    ) -> list[Preset]:
        """List available presets.

        Args:
            file_type: Optional file type filter
            source: Optional source filter

        Returns:
            List of available presets
        """
        self._load_presets()

        presets = list(self._preset_cache.values())

        # Apply filters
        if file_type:
            presets = [p for p in presets if p.type == file_type]
        if source:
            presets = [p for p in presets if p.source == source]

        # Sort by file type, then name
        presets.sort(key=lambda p: (p.type.value, p.name))

        return presets

    def get_preset(self, preset_id: str) -> Optional[Preset]:
        """Get a specific preset by ID.

        Args:
            preset_id: Preset ID in format "{file_type}:{preset_name}"

        Returns:
            Preset if found, None otherwise
        """
        self._load_presets()
        return self._preset_cache.get(preset_id)

    def add_preset(
        self, preset: Preset, source: PresetSource = PresetSource.USER
    ) -> None:
        """Add a new preset.

        Args:
            preset: Preset to add
            source: Where to store the preset (USER or PROJECT)

        Raises:
            ValueError: If preset already exists or source is BUILT_IN
        """
        if source == PresetSource.BUILT_IN:
            raise ValueError("Cannot add built-in presets")

        self._load_presets()

        if preset.id in self._preset_cache:
            raise ValueError(f"Preset '{preset.id}' already exists")

        # Determine storage directory
        storage_dir = (
            self.user_presets_dir
            if source == PresetSource.USER
            else self.project_presets_dir
        )
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Save preset metadata
        preset_file = storage_dir / f"{preset.id.replace(':', '_')}.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump({"preset": preset.to_dict()}, f)

        # Update cache
        preset.source = source
        self._preset_cache[preset.id] = preset

    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset.

        Args:
            preset_id: ID of preset to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete a built-in preset
        """
        self._load_presets()

        preset = self._preset_cache.get(preset_id)
        if not preset:
            return False

        if preset.source == PresetSource.BUILT_IN:
            raise ValueError("Cannot delete built-in presets")

        # Determine storage directory
        storage_dir = (
            self.user_presets_dir
            if preset.source == PresetSource.USER
            else self.project_presets_dir
        )

        # Delete preset file
        preset_file = storage_dir / f"{preset_id.replace(':', '_')}.toml"
        if preset_file.exists():
            preset_file.unlink()

        # Remove from cache
        del self._preset_cache[preset_id]
        return True

    def render_preset(
        self, preset: Preset, variables: Optional[dict[str, Any]] = None
    ) -> str:
        """Render a preset with variables.

        Args:
            preset: Preset to render
            variables: Variables to use for rendering (overrides preset defaults)

        Returns:
            Rendered content

        Raises:
            FileNotFoundError: If preset template file not found
        """
        if not preset.template_path or not preset.template_path.exists():
            raise FileNotFoundError(f"Template file not found for preset '{preset.id}'")

        # Read template content
        content = preset.template_path.read_text(encoding="utf-8")

        # Merge variables (user overrides > preset defaults)
        final_variables = {**preset.variables, **(variables or {})}

        # Simple variable substitution using {variable_name} syntax
        for key, value in final_variables.items():
            placeholder = f"{{{key}}}"
            content = content.replace(placeholder, str(value))

        return content

    def extract_template_variables(self, template_content: str) -> set[str]:
        """Extract variable placeholders from template content.

        Args:
            template_content: Template content to analyze

        Returns:
            Set of variable names found in the template
        """
        import re

        # Find all {variable_name} patterns
        pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
        matches = re.findall(pattern, template_content)
        return set(matches)

    def validate_template_variables(
        self, preset: Preset, variables: Optional[dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate template variables for a preset.

        Args:
            preset: Preset to validate
            variables: Variables that will be provided during rendering

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(valid=True)

        # If no template file, nothing to validate
        if not preset.template_path:
            return result

        if not preset.template_path.exists():
            result.add_error(f"Template file not found: {preset.template_path}")
            return result

        try:
            # Read template content
            content = preset.template_path.read_text(encoding="utf-8")

            # Extract variables from template
            template_vars = self.extract_template_variables(content)

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

        except (OSError, IOError) as e:
            result.add_error(f"Failed to read template file: {e}")
        except Exception as e:
            result.add_error(f"Unexpected error validating template: {type(e).__name__}: {e}")

        return result

    def get_preset_by_name(
        self, file_type: FileType, preset_name: str
    ) -> Optional[Preset]:
        """Get a preset by file type and preset name.

        Args:
            file_type: Type of file
            preset_name: Name of preset (without file_type prefix)

        Returns:
            Preset if found, None otherwise
        """
        preset_id = f"{file_type.value}:{preset_name}"
        return self.get_preset(preset_id)

    def _load_presets(self) -> None:
        """Load all presets from all sources into cache."""
        if self._cache_loaded:
            return

        # Load built-in presets
        self._load_builtin_presets()

        # Load user presets
        if self.user_presets_dir.exists():
            self._load_presets_from_directory(self.user_presets_dir, PresetSource.USER)

        # Load project presets
        if self.project_presets_dir.exists():
            self._load_presets_from_directory(
                self.project_presets_dir, PresetSource.PROJECT
            )

        # Validate preset inheritance (check for circular dependencies)
        inheritance_errors = self.validate_preset_inheritance()
        if inheritance_errors:
            for error in inheritance_errors:
                self._load_errors.append(error)

        self._cache_loaded = True

    def _load_builtin_presets(self) -> None:
        """Load built-in presets shipped with claudefig."""
        # For now, create default presets programmatically
        # In Phase 2.5, we'll load these from template files

        builtin_presets = [
            # CLAUDE.md presets
            Preset(
                id="claude_md:default",
                type=FileType.CLAUDE_MD,
                name="Default",
                description="Standard Claude Code configuration file",
                source=PresetSource.BUILT_IN,
                tags=["standard", "general"],
            ),
            Preset(
                id="claude_md:minimal",
                type=FileType.CLAUDE_MD,
                name="Minimal",
                description="Minimal Claude Code configuration",
                source=PresetSource.BUILT_IN,
                tags=["minimal", "simple"],
            ),
            Preset(
                id="claude_md:backend",
                type=FileType.CLAUDE_MD,
                name="Backend Focused",
                description="Backend development focused configuration",
                source=PresetSource.BUILT_IN,
                tags=["backend", "api"],
            ),
            Preset(
                id="claude_md:frontend",
                type=FileType.CLAUDE_MD,
                name="Frontend Focused",
                description="Frontend development focused configuration",
                source=PresetSource.BUILT_IN,
                tags=["frontend", "ui"],
            ),
            # Settings presets
            Preset(
                id="settings_json:default",
                type=FileType.SETTINGS_JSON,
                name="Default",
                description="Standard team settings",
                source=PresetSource.BUILT_IN,
                tags=["standard", "team"],
            ),
            Preset(
                id="settings_json:strict",
                type=FileType.SETTINGS_JSON,
                name="Strict",
                description="Strict permissions and validation",
                source=PresetSource.BUILT_IN,
                tags=["strict", "secure"],
            ),
            # Settings local presets
            Preset(
                id="settings_local_json:default",
                type=FileType.SETTINGS_LOCAL_JSON,
                name="Default",
                description="Personal project settings",
                source=PresetSource.BUILT_IN,
                tags=["personal", "local"],
            ),
            # Gitignore presets
            Preset(
                id="gitignore:standard",
                type=FileType.GITIGNORE,
                name="Standard",
                description="Standard Claude Code gitignore entries",
                source=PresetSource.BUILT_IN,
                tags=["standard"],
            ),
            Preset(
                id="gitignore:python",
                type=FileType.GITIGNORE,
                name="Python",
                description="Python-specific gitignore patterns",
                source=PresetSource.BUILT_IN,
                tags=["python", "language"],
            ),
            # Commands preset
            Preset(
                id="commands:default",
                type=FileType.COMMANDS,
                name="Default",
                description="Standard slash command examples",
                source=PresetSource.BUILT_IN,
                tags=["standard", "examples"],
            ),
            # Agents preset
            Preset(
                id="agents:default",
                type=FileType.AGENTS,
                name="Default",
                description="Standard sub-agent examples",
                source=PresetSource.BUILT_IN,
                tags=["standard", "examples"],
            ),
            # Hooks preset
            Preset(
                id="hooks:default",
                type=FileType.HOOKS,
                name="Default",
                description="Standard hook examples",
                source=PresetSource.BUILT_IN,
                tags=["standard", "examples"],
            ),
            # Output styles preset
            Preset(
                id="output_styles:default",
                type=FileType.OUTPUT_STYLES,
                name="Default",
                description="Standard output style examples",
                source=PresetSource.BUILT_IN,
                tags=["standard", "examples"],
            ),
            # Statusline preset
            Preset(
                id="statusline:default",
                type=FileType.STATUSLINE,
                name="Default",
                description="Standard statusline script",
                source=PresetSource.BUILT_IN,
                tags=["standard"],
            ),
            # MCP preset
            Preset(
                id="mcp:default",
                type=FileType.MCP,
                name="Default",
                description="Standard MCP server examples",
                source=PresetSource.BUILT_IN,
                tags=["standard", "examples"],
            ),
        ]

        for preset in builtin_presets:
            self._preset_cache[preset.id] = preset

    def _load_presets_from_directory(
        self, directory: Path, source: PresetSource
    ) -> None:
        """Load presets from a directory.

        Args:
            directory: Directory to load from
            source: Source type for loaded presets
        """
        if not directory.exists():
            return

        for preset_file in directory.glob("*.toml"):
            try:
                with open(preset_file, "rb") as f:
                    data = tomllib.load(f)

                if "preset" not in data:
                    error_msg = f"Missing 'preset' key in {preset_file}"
                    self._load_errors.append(error_msg)
                    continue

                preset = Preset.from_dict(data["preset"])
                preset.source = source
                self._preset_cache[preset.id] = preset

            except (OSError, IOError) as e:
                # File system errors
                error_msg = f"Failed to read preset file {preset_file}: {e}"
                self._load_errors.append(error_msg)
            except (KeyError, ValueError, TypeError) as e:
                # Invalid preset data
                error_msg = f"Invalid preset data in {preset_file}: {e}"
                self._load_errors.append(error_msg)
            except Exception as e:
                # Unexpected errors - still catch but be explicit
                error_msg = f"Unexpected error loading preset from {preset_file}: {type(e).__name__}: {e}"
                self._load_errors.append(error_msg)

    def clear_cache(self) -> None:
        """Clear the preset cache to force reload."""
        self._preset_cache.clear()
        self._cache_loaded = False
        self._load_errors.clear()

    def get_load_errors(self) -> list[str]:
        """Get any errors that occurred during preset loading.

        Returns:
            List of error messages from preset loading failures
        """
        return self._load_errors.copy()

    def check_circular_dependency(self, preset_id: str, visited: Optional[set[str]] = None) -> None:
        """Check for circular dependencies in preset inheritance chain.

        Args:
            preset_id: ID of preset to check
            visited: Set of already visited preset IDs (used for recursion)

        Raises:
            CircularDependencyError: If circular dependency is detected
        """
        if visited is None:
            visited = set()

        if preset_id in visited:
            # Circular dependency detected
            cycle_path = list(visited) + [preset_id]
            raise CircularDependencyError(cycle_path)

        # Get the preset
        preset = self.get_preset(preset_id)
        if not preset or not preset.extends:
            # No inheritance or preset not found - no circular dependency
            return

        # Add current preset to visited set
        visited.add(preset_id)

        # Check the parent preset recursively
        self.check_circular_dependency(preset.extends, visited)

    def validate_preset_inheritance(self) -> list[str]:
        """Validate all preset inheritance chains for circular dependencies.

        Returns:
            List of error messages for any circular dependencies found
        """
        errors = []

        for preset_id, preset in self._preset_cache.items():
            if preset.extends:
                try:
                    self.check_circular_dependency(preset_id)
                except CircularDependencyError as e:
                    errors.append(str(e))

        return errors

    def resolve_preset_variables(self, preset: Preset) -> dict[str, Any]:
        """Resolve preset variables including inherited values.

        Args:
            preset: Preset to resolve variables for

        Returns:
            Dictionary of resolved variables (parent + child, child overrides parent)

        Raises:
            CircularDependencyError: If circular dependency is detected
        """
        # Check for circular dependencies first
        self.check_circular_dependency(preset.id)

        # Build inheritance chain from parent to child
        chain = []
        current_id = preset.id

        while current_id:
            current = self.get_preset(current_id)
            if not current:
                break
            chain.insert(0, current)  # Insert at beginning to go parent -> child
            current_id = current.extends

        # Merge variables from parent to child (child overrides parent)
        merged_variables = {}
        for p in chain:
            merged_variables.update(p.variables)

        return merged_variables
