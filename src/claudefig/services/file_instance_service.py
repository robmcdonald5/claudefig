"""File instance service layer for business logic.

This module provides reusable business logic for file instance management,
separated from data access and UI concerns.
"""

from pathlib import Path

from claudefig.models import FileInstance, FileType, ValidationResult
from claudefig.repositories import AbstractPresetRepository
from claudefig.services.validation_service import validate_plugin_components


def list_instances(
    instances: dict[str, FileInstance],
    file_type: FileType | None = None,
    enabled_only: bool = False,
) -> list[FileInstance]:
    """List file instances with optional filtering.

    Args:
        instances: Dictionary of file instances (id -> FileInstance).
        file_type: Optional file type filter.
        enabled_only: If True, only return enabled instances.

    Returns:
        List of file instances matching filters, sorted by type and path.
    """
    result = list(instances.values())

    # Apply filters
    if file_type:
        result = [i for i in result if i.type == file_type]
    if enabled_only:
        result = [i for i in result if i.enabled]

    # Sort by file type, then path
    result.sort(key=lambda i: (i.type.value, i.path))

    return result


def get_instance(
    instances: dict[str, FileInstance], instance_id: str
) -> FileInstance | None:
    """Get a specific file instance by ID.

    Args:
        instances: Dictionary of file instances.
        instance_id: Instance ID to retrieve.

    Returns:
        FileInstance if found, None otherwise.
    """
    return instances.get(instance_id)


def add_instance(
    instances: dict[str, FileInstance],
    instance: FileInstance,
    preset_repo: AbstractPresetRepository,
    repo_path: Path,
) -> ValidationResult:
    """Add a new file instance with validation.

    Business logic:
    1. Validate instance (preset exists, path valid, no duplicates)
    2. Add to instances dict if valid

    Args:
        instances: Dictionary of file instances (modified in-place).
        instance: File instance to add.
        preset_repo: Preset repository for validation.
        repo_path: Path to repository root.

    Returns:
        ValidationResult indicating success or failure.
    """
    result = validate_instance(
        instance, instances, preset_repo, repo_path, is_update=False
    )

    if result.valid:
        instances[instance.id] = instance

    return result


def update_instance(
    instances: dict[str, FileInstance],
    instance: FileInstance,
    preset_repo: AbstractPresetRepository,
    repo_path: Path,
) -> ValidationResult:
    """Update an existing file instance with validation.

    Args:
        instances: Dictionary of file instances (modified in-place).
        instance: File instance with updated values.
        preset_repo: Preset repository for validation.
        repo_path: Path to repository root.

    Returns:
        ValidationResult indicating success or failure.
    """
    if instance.id not in instances:
        result = ValidationResult(valid=False)
        result.add_error(f"Instance '{instance.id}' not found")
        return result

    result = validate_instance(
        instance, instances, preset_repo, repo_path, is_update=True
    )

    if result.valid:
        instances[instance.id] = instance

    return result


def remove_instance(instances: dict[str, FileInstance], instance_id: str) -> bool:
    """Remove a file instance.

    Args:
        instances: Dictionary of file instances (modified in-place).
        instance_id: ID of instance to remove.

    Returns:
        True if removed, False if not found.
    """
    if instance_id in instances:
        del instances[instance_id]
        return True
    return False


def enable_instance(instances: dict[str, FileInstance], instance_id: str) -> bool:
    """Enable a file instance.

    Args:
        instances: Dictionary of file instances (modified in-place).
        instance_id: ID of instance to enable.

    Returns:
        True if enabled, False if not found.
    """
    instance = instances.get(instance_id)
    if instance:
        instance.enabled = True
        return True
    return False


def disable_instance(instances: dict[str, FileInstance], instance_id: str) -> bool:
    """Disable a file instance.

    Args:
        instances: Dictionary of file instances (modified in-place).
        instance_id: ID of instance to disable.

    Returns:
        True if disabled, False if not found.
    """
    instance = instances.get(instance_id)
    if instance:
        instance.enabled = False
        return True
    return False


def validate_instance(
    instance: FileInstance,
    existing_instances: dict[str, FileInstance],
    preset_repo: AbstractPresetRepository,
    repo_path: Path,
    is_update: bool = False,
) -> ValidationResult:
    """Validate a file instance comprehensively.

    Validates:
    - ID uniqueness (for new instances)
    - Preset exists and matches type
    - Path is valid and safe
    - No path conflicts with other instances
    - Single-instance file types have no duplicates

    Args:
        instance: File instance to validate.
        existing_instances: Dictionary of existing instances.
        preset_repo: Preset repository to validate preset reference.
        repo_path: Path to repository root for path validation.
        is_update: True if this is an update (allows same ID).

    Returns:
        ValidationResult with any errors or warnings.
    """
    result = ValidationResult(valid=True)

    # Check if ID already exists (for new instances)
    if not is_update and instance.id in existing_instances:
        result.add_error(f"Instance with ID '{instance.id}' already exists")

    # Check if preset exists (skip validation for component-based instances)
    # Component-based instances use "component:{name}" format and don't exist in preset repo
    if not instance.preset.startswith("component:"):
        preset = preset_repo.get_preset(instance.preset)
        if not preset:
            result.add_error(f"Preset '{instance.preset}' not found")
        elif preset.type != instance.type:
            result.add_error(
                f"Preset type mismatch: preset is for {preset.type.value}, "
                f"but instance is for {instance.type.value}"
            )

    # Validate path
    path_result = validate_path(instance.path, instance.type, repo_path)
    if path_result.has_errors:
        for error in path_result.errors:
            result.add_error(error)
    if path_result.has_warnings:
        for warning in path_result.warnings:
            result.add_warning(warning)

    # Check for path conflicts with other instances
    for existing_id, existing in existing_instances.items():
        # Skip self when updating
        if is_update and existing_id == instance.id:
            continue

        if existing.path == instance.path and existing.enabled:
            result.add_warning(
                f"Path '{instance.path}' is already used by instance '{existing_id}'"
            )

    # Check if file type supports multiple instances
    if not instance.type.supports_multiple:
        existing_count = sum(
            1
            for i in existing_instances.values()
            if i.type == instance.type and i.enabled
        )
        if existing_count > 0 and (not is_update or not instance.enabled):
            result.add_error(
                f"File type '{instance.type.value}' does not support multiple instances. "
                f"An instance already exists."
            )

    # Special validation for plugins: check component references
    if instance.type == FileType.PLUGINS:
        # Get component directories to search
        # Dynamic import to avoid circular dependency at module load time:
        # file_instance_service -> user_config -> structure_validator
        # This import is deferred to runtime when validate_instance() is called
        # for PLUGINS file type validation.
        from claudefig.user_config import get_components_dir, get_user_config_dir

        components_dirs = []

        # Add global components directory
        global_components = get_components_dir()
        if global_components.exists():
            components_dirs.append(global_components)

        # Add preset components directory (if available)
        # Extract preset name from instance.preset (format: "plugins:preset-name")
        preset_name = "default"
        if ":" in instance.preset:
            preset_name = instance.preset.split(":", 1)[1]

        user_config_dir = get_user_config_dir()
        preset_components = user_config_dir / "presets" / preset_name / "components"
        if preset_components.exists():
            components_dirs.append(preset_components)

        # Validate plugin if path points to an actual file (not just directory)
        plugin_file_path = repo_path / instance.path
        if plugin_file_path.is_file():
            plugin_result = validate_plugin_components(
                plugin_file_path, components_dirs, preset_name
            )
            # Merge warnings from plugin validation
            if plugin_result.has_warnings:
                for warning in plugin_result.warnings:
                    result.add_warning(warning)
            # Note: We don't fail validation even if plugin has errors,
            # just add warnings so user is informed

    return result


def validate_path(path: str, file_type: FileType, repo_path: Path) -> ValidationResult:
    """Validate a file path for safety and correctness.

    Validates:
    - Path is not empty
    - Path is relative (not absolute)
    - No parent directory references (../)
    - Path doesn't escape repository
    - Directory types end with /
    - Warns if file already exists

    Args:
        path: Path to validate (relative to repo root).
        file_type: Type of file.
        repo_path: Path to repository root.

    Returns:
        ValidationResult with any errors or warnings.
    """
    result = ValidationResult(valid=True)

    if not path:
        result.add_error("Path cannot be empty")
        return result

    # Validate path format
    try:
        path_obj = Path(path)

        # Check for absolute paths
        if path_obj.is_absolute():
            result.add_error("Path must be relative to repository root")

        # Check for parent directory references (../)
        if ".." in path_obj.parts:
            result.add_error("Path cannot contain parent directory references (../)")

        # For directories, ensure path ends with /
        if file_type.is_directory and not path.endswith("/"):
            result.add_warning(
                f"Path should end with '/' for directory types. Suggested: '{path}/'"
            )

        # Check if file would be created outside repo
        full_path = (repo_path / path_obj).resolve()
        if not full_path.is_relative_to(repo_path.resolve()):
            result.add_error("Path would create file outside repository")

        # Warn if file already exists (unless in append mode)
        if full_path.exists() and not file_type.append_mode:
            result.add_warning(
                f"File already exists at '{path}' and may be overwritten"
            )

    except (ValueError, OSError) as e:
        result.add_error(f"Invalid path: {e}")

    return result


def generate_instance_id(
    file_type: FileType,
    preset_name: str,
    path: str | None,
    existing_instances: dict[str, FileInstance],
) -> str:
    """Generate a unique instance ID.

    ID format: {file_type}-{preset_name}[-{path_suffix}][-{counter}]

    Args:
        file_type: File type.
        preset_name: Preset name (without file type prefix).
        path: Optional path (used for uniqueness if different from default).
        existing_instances: Dictionary of existing instances to avoid collisions.

    Returns:
        Unique instance ID.

    Example:
        >>> generate_instance_id(FileType.CLAUDE_MD, "default", None, {})
        'claude_md-default'
        >>> generate_instance_id(FileType.CLAUDE_MD, "custom", "docs/CLAUDE.md", {})
        'claude_md-custom-docs'
    """
    # Base ID
    base_id = f"{file_type.value}-{preset_name}"

    # If path is provided and different from default, include it
    if path and path != file_type.default_path:
        # Use path components for uniqueness
        path_parts = Path(path).parts
        if path_parts:
            # Take the first unique part
            path_suffix = path_parts[0].replace(".", "").replace("/", "-")
            base_id = f"{base_id}-{path_suffix}"

    # Ensure uniqueness by appending counter if needed
    if base_id not in existing_instances:
        return base_id

    counter = 1
    while f"{base_id}-{counter}" in existing_instances:
        counter += 1

    return f"{base_id}-{counter}"


def get_default_path(file_type: FileType) -> str:
    """Get the default path for a file type.

    Args:
        file_type: File type.

    Returns:
        Default path for the file type.
    """
    return file_type.default_path


def count_by_type(instances: dict[str, FileInstance]) -> dict[FileType, int]:
    """Count enabled instances by file type.

    Args:
        instances: Dictionary of file instances.

    Returns:
        Dictionary mapping file types to enabled instance counts.
    """
    counts: dict[FileType, int] = {}

    for instance in instances.values():
        if instance.enabled:
            counts[instance.type] = counts.get(instance.type, 0) + 1

    return counts


def get_instances_by_type(
    instances: dict[str, FileInstance], file_type: FileType
) -> list[FileInstance]:
    """Get all instances of a specific file type.

    Args:
        instances: Dictionary of file instances.
        file_type: File type to filter by.

    Returns:
        List of file instances matching the type.
    """
    return [i for i in instances.values() if i.type == file_type]


def load_instances_from_config(
    instances_data: list[dict],
) -> tuple[dict[str, FileInstance], list[str]]:
    """Load file instances from configuration data.

    Args:
        instances_data: List of instance dictionaries from config.

    Returns:
        Tuple of (instances dict, error messages list).
    """
    instances: dict[str, FileInstance] = {}
    load_errors: list[str] = []

    for data in instances_data:
        try:
            instance = FileInstance.from_dict(data)
            instances[instance.id] = instance
        except (KeyError, ValueError, TypeError) as e:
            # Invalid instance data
            instance_id = data.get("id", "<unknown>")
            error_msg = f"Invalid instance data for '{instance_id}': {e}"
            load_errors.append(error_msg)
        except Exception as e:
            # Unexpected errors
            instance_id = data.get("id", "<unknown>")
            error_msg = (
                f"Unexpected error loading instance '{instance_id}': "
                f"{type(e).__name__}: {e}"
            )
            load_errors.append(error_msg)

    return instances, load_errors


def save_instances_to_config(instances: dict[str, FileInstance]) -> list[dict]:
    """Save file instances to configuration format.

    Args:
        instances: Dictionary of file instances.

    Returns:
        List of instance dictionaries suitable for config storage.
    """
    return [instance.to_dict() for instance in instances.values()]
