"""File instance management for claudefig."""

import json
from pathlib import Path
from typing import Optional

from claudefig.models import FileInstance, FileType, ValidationResult
from claudefig.preset_manager import PresetManager
from claudefig.user_config import get_components_dir


class FileInstanceManager:
    """Manages file instances for configuration generation.

    File instances represent specific files that will be generated,
    combining a file type, preset, and target path.
    """

    def __init__(
        self,
        preset_manager: Optional[PresetManager] = None,
        repo_path: Optional[Path] = None,
    ):
        """Initialize file instance manager.

        Args:
            preset_manager: PresetManager instance (creates one if None)
            repo_path: Path to repository root (default: current directory)
        """
        self.preset_manager = preset_manager or PresetManager()
        self.repo_path = repo_path or Path.cwd()
        self._instances: dict[str, FileInstance] = {}
        self._load_errors: list[str] = []  # Track errors during instance loading

    def list_instances(
        self, file_type: Optional[FileType] = None, enabled_only: bool = False
    ) -> list[FileInstance]:
        """List file instances.

        Args:
            file_type: Optional file type filter
            enabled_only: If True, only return enabled instances

        Returns:
            List of file instances
        """
        instances = list(self._instances.values())

        # Apply filters
        if file_type:
            instances = [i for i in instances if i.type == file_type]
        if enabled_only:
            instances = [i for i in instances if i.enabled]

        # Sort by file type, then path
        instances.sort(key=lambda i: (i.type.value, i.path))

        return instances

    def get_instance(self, instance_id: str) -> Optional[FileInstance]:
        """Get a specific file instance by ID.

        Args:
            instance_id: Instance ID

        Returns:
            FileInstance if found, None otherwise
        """
        return self._instances.get(instance_id)

    def add_instance(self, instance: FileInstance) -> ValidationResult:
        """Add a new file instance.

        Args:
            instance: File instance to add

        Returns:
            ValidationResult indicating success or failure
        """
        result = self.validate_instance(instance)

        if result.valid:
            self._instances[instance.id] = instance

        return result

    def update_instance(self, instance: FileInstance) -> ValidationResult:
        """Update an existing file instance.

        Args:
            instance: File instance with updated values

        Returns:
            ValidationResult indicating success or failure
        """
        if instance.id not in self._instances:
            result = ValidationResult(valid=False)
            result.add_error(f"Instance '{instance.id}' not found")
            return result

        result = self.validate_instance(instance, is_update=True)

        if result.valid:
            self._instances[instance.id] = instance

        return result

    def remove_instance(self, instance_id: str) -> bool:
        """Remove a file instance.

        Args:
            instance_id: ID of instance to remove

        Returns:
            True if removed, False if not found
        """
        if instance_id in self._instances:
            del self._instances[instance_id]
            return True
        return False

    def enable_instance(self, instance_id: str) -> bool:
        """Enable a file instance.

        Args:
            instance_id: ID of instance to enable

        Returns:
            True if enabled, False if not found
        """
        instance = self._instances.get(instance_id)
        if instance:
            instance.enabled = True
            return True
        return False

    def disable_instance(self, instance_id: str) -> bool:
        """Disable a file instance.

        Args:
            instance_id: ID of instance to disable

        Returns:
            True if disabled, False if not found
        """
        instance = self._instances.get(instance_id)
        if instance:
            instance.enabled = False
            return True
        return False

    def validate_instance(
        self, instance: FileInstance, is_update: bool = False
    ) -> ValidationResult:
        """Validate a file instance.

        Args:
            instance: File instance to validate
            is_update: True if this is an update (allows same ID)

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(valid=True)

        # Check if ID already exists (for new instances)
        if not is_update and instance.id in self._instances:
            result.add_error(f"Instance with ID '{instance.id}' already exists")

        # Check if preset exists
        preset = self.preset_manager.get_preset(instance.preset)
        if not preset:
            result.add_error(f"Preset '{instance.preset}' not found")
        elif preset.type != instance.type:
            result.add_error(
                f"Preset type mismatch: preset is for {preset.type.value}, "
                f"but instance is for {instance.type.value}"
            )

        # Validate path
        path_result = self.validate_path(instance.path, instance.type)
        if path_result.has_errors:
            for error in path_result.errors:
                result.add_error(error)
        if path_result.has_warnings:
            for warning in path_result.warnings:
                result.add_warning(warning)

        # Check for path conflicts with other instances
        for existing_id, existing in self._instances.items():
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
                for i in self._instances.values()
                if i.type == instance.type and i.enabled
            )
            if existing_count > 0 and (not is_update or not instance.enabled):
                result.add_error(
                    f"File type '{instance.type.value}' does not support multiple instances. "
                    f"An instance already exists."
                )

        return result

    def validate_path(self, path: str, file_type: FileType) -> ValidationResult:
        """Validate a file path.

        Args:
            path: Path to validate (relative to repo root)
            file_type: Type of file

        Returns:
            ValidationResult with any errors or warnings
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
                result.add_error(
                    "Path cannot contain parent directory references (../)"
                )

            # For directories, ensure path ends with /
            if file_type.is_directory and not path.endswith("/"):
                result.add_warning(
                    f"Path should end with '/' for directory types. "
                    f"Suggested: '{path}/'"
                )

            # Check if file would be created outside repo
            full_path = (self.repo_path / path_obj).resolve()
            if not str(full_path).startswith(str(self.repo_path.resolve())):
                result.add_error("Path would create file outside repository")

            # Warn if file already exists
            if full_path.exists() and not file_type.append_mode:
                result.add_warning(
                    f"File already exists at '{path}' and may be overwritten"
                )

        except (ValueError, OSError) as e:
            result.add_error(f"Invalid path: {e}")

        return result

    def get_default_path(self, file_type: FileType) -> str:
        """Get the default path for a file type.

        Args:
            file_type: File type

        Returns:
            Default path for the file type
        """
        return file_type.default_path

    def generate_instance_id(
        self, file_type: FileType, preset_name: str, path: Optional[str] = None
    ) -> str:
        """Generate a unique instance ID.

        Args:
            file_type: File type
            preset_name: Preset name (without file type prefix)
            path: Optional path (used for uniqueness)

        Returns:
            Unique instance ID
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
        if base_id not in self._instances:
            return base_id

        counter = 1
        while f"{base_id}-{counter}" in self._instances:
            counter += 1

        return f"{base_id}-{counter}"

    def load_instances(self, instances_data: list[dict]) -> None:
        """Load file instances from configuration data.

        Args:
            instances_data: List of instance dictionaries
        """
        self._instances.clear()
        self._load_errors.clear()

        for data in instances_data:
            try:
                instance = FileInstance.from_dict(data)
                self._instances[instance.id] = instance
            except (KeyError, ValueError, TypeError) as e:
                # Invalid instance data
                instance_id = data.get("id", "<unknown>")
                error_msg = f"Invalid instance data for '{instance_id}': {e}"
                self._load_errors.append(error_msg)
            except Exception as e:
                # Unexpected errors - still catch but be explicit
                instance_id = data.get("id", "<unknown>")
                error_msg = f"Unexpected error loading instance '{instance_id}': {type(e).__name__}: {e}"
                self._load_errors.append(error_msg)

    def save_instances(self) -> list[dict]:
        """Save file instances to configuration format.

        Returns:
            List of instance dictionaries
        """
        return [instance.to_dict() for instance in self._instances.values()]

    def count_by_type(self) -> dict[FileType, int]:
        """Count instances by file type.

        Returns:
            Dictionary mapping file types to instance counts
        """
        counts: dict[FileType, int] = {}

        for instance in self._instances.values():
            if instance.enabled:
                counts[instance.type] = counts.get(instance.type, 0) + 1

        return counts

    def get_instances_by_type(self, file_type: FileType) -> list[FileInstance]:
        """Get all instances of a specific file type.

        Args:
            file_type: File type to filter by

        Returns:
            List of file instances
        """
        return [i for i in self._instances.values() if i.type == file_type]

    def get_load_errors(self) -> list[str]:
        """Get any errors that occurred during instance loading.

        Returns:
            List of error messages from instance loading failures
        """
        return self._load_errors.copy()

    # Component library methods

    @staticmethod
    def _get_component_type_dir(file_type: FileType) -> str:
        """Get the component subdirectory name for a file type.

        Args:
            file_type: File type

        Returns:
            Component subdirectory name (e.g., 'claude_md', 'gitignore')
        """
        return file_type.value

    def save_as_component(
        self, instance: FileInstance, component_name: str
    ) -> tuple[bool, str]:
        """Save a file instance as a reusable component.

        For CLAUDE.md and .gitignore files, components are saved in folders:
        ~/.claudefig/components/{file_type}/{component_name}/{actual_filename}

        For other file types, components are still saved as JSON metadata files.

        Args:
            instance: File instance to save
            component_name: Name for the component (without extension)

        Returns:
            Tuple of (success, message)
        """
        try:
            components_dir = get_components_dir()
            type_dir = components_dir / self._get_component_type_dir(instance.type)

            # Ensure type directory exists
            type_dir.mkdir(parents=True, exist_ok=True)

            # For CLAUDE.md and .gitignore, use folder-based storage
            if instance.type in (FileType.CLAUDE_MD, FileType.GITIGNORE):
                # Create component folder
                component_folder = type_dir / component_name

                # Check if component folder already exists
                if component_folder.exists():
                    return False, f"Component '{component_name}' already exists"

                component_folder.mkdir(parents=True, exist_ok=True)

                # Determine the actual filename to use
                actual_filename = Path(instance.path).name
                component_file = component_folder / actual_filename

                # Save minimal component metadata as JSON
                # Components are templates - only store type and default path
                # enabled, preset, variables are instance-specific (per-project)
                metadata_file = component_folder / "component.json"
                component_data = {
                    "type": instance.type.value,
                    "path": instance.path,
                    "component_name": component_name,
                }
                metadata_file.write_text(
                    json.dumps(component_data, indent=2), encoding="utf-8"
                )

                # Create placeholder file (user will edit this directly)
                component_file.write_text(
                    f"# Component: {component_name}\n"
                    f"# Edit this file to customize your {instance.type.display_name} component\n",
                    encoding="utf-8",
                )

                return True, f"Component saved to {component_folder}"
            else:
                # For other file types, use legacy JSON storage
                component_file = type_dir / f"{component_name}.json"

                # Check if component already exists
                if component_file.exists():
                    return False, f"Component '{component_name}' already exists"

                # Save component as JSON
                component_data = instance.to_dict()
                component_file.write_text(
                    json.dumps(component_data, indent=2), encoding="utf-8"
                )

                return True, f"Component saved to {component_file}"

        except Exception as e:
            return False, f"Failed to save component: {e}"

    def list_components(self, file_type: FileType) -> list[tuple[str, Path]]:
        """List available components for a file type.

        For CLAUDE.md and .gitignore, looks for component folders.
        For other file types, looks for .json component files.

        Args:
            file_type: File type to list components for

        Returns:
            List of (component_name, path) tuples where path is:
            - For folder-based: path to the component folder
            - For JSON-based: path to the .json file
        """
        try:
            components_dir = get_components_dir()
            type_dir = components_dir / self._get_component_type_dir(file_type)

            if not type_dir.exists():
                return []

            components = []

            # For CLAUDE.md and .gitignore, look for component folders
            if file_type in (FileType.CLAUDE_MD, FileType.GITIGNORE):
                for item in type_dir.iterdir():
                    # Only include directories (component folders)
                    if item.is_dir():
                        component_name = item.name
                        components.append((component_name, item))
            else:
                # For other file types, collect component names (avoiding duplicates)
                # Priority: .json files > raw files
                component_names = set()

                # First, collect all .json component files (these have priority)
                for component_file in type_dir.glob("*.json"):
                    component_name = component_file.stem
                    component_names.add(component_name)
                    components.append((component_name, component_file))

                # Then, look for raw files (only if no .json exists for that name)
                for component_file in type_dir.iterdir():
                    if component_file.is_file() and component_file.suffix != ".json":
                        component_name = component_file.stem
                        if component_name not in component_names:
                            component_names.add(component_name)
                            components.append((component_name, component_file))

            # Sort alphabetically
            components.sort(key=lambda x: x[0])
            return components

        except Exception:
            return []

    def load_component(
        self, file_type: FileType, component_name: str
    ) -> Optional[FileInstance]:
        """Load a component and create a file instance from it.

        For CLAUDE.md and .gitignore, loads from folder structure.
        For other file types, loads from .json files.

        Args:
            file_type: File type of the component
            component_name: Name of the component to load

        Returns:
            FileInstance if loaded successfully, None otherwise
        """
        try:
            components_dir = get_components_dir()
            type_dir = components_dir / self._get_component_type_dir(file_type)

            # For CLAUDE.md and .gitignore, load from folder structure
            if file_type in (FileType.CLAUDE_MD, FileType.GITIGNORE):
                component_folder = type_dir / component_name

                if not component_folder.exists() or not component_folder.is_dir():
                    return None

                # Check for metadata file
                metadata_file = component_folder / "component.json"
                if metadata_file.exists():
                    # Load minimal component metadata
                    component_data = json.loads(
                        metadata_file.read_text(encoding="utf-8")
                    )

                    # Create FileInstance with instance-specific defaults
                    # Components only store: type, path, component_name
                    # We add instance-specific fields: id, enabled, preset, variables
                    instance = FileInstance(
                        id=f"{file_type.value}-{component_name}",
                        type=file_type,
                        preset=f"component:{component_name}",  # Preset is now just component reference
                        path=component_data.get("path", file_type.default_path),
                        enabled=True,  # Default enabled (user can toggle per-project)
                        variables={
                            "component_folder": str(component_folder),
                            "component_name": component_name,
                        },
                    )
                    return instance
                else:
                    # Folder without metadata - create instance from defaults
                    instance = FileInstance(
                        id=f"{file_type.value}-{component_name}",
                        type=file_type,
                        preset=f"component:{component_name}",
                        path=file_type.default_path,
                        enabled=True,
                        variables={
                            "component_folder": str(component_folder),
                            "component_name": component_name,
                        },
                    )
                    return instance
            else:
                # For other file types, load from .json file or raw file
                json_file = type_dir / f"{component_name}.json"

                if json_file.exists():
                    # Load from .json metadata file
                    component_data = json.loads(json_file.read_text(encoding="utf-8"))
                    instance = FileInstance.from_dict(component_data)
                    return instance
                else:
                    # Look for raw file (simplified component)
                    for component_file in type_dir.iterdir():
                        if (
                            component_file.stem == component_name
                            and component_file.suffix != ".json"
                        ):
                            # Create a FileInstance with sensible defaults
                            preset_id = f"{file_type.value}:default"
                            instance = FileInstance(
                                id=f"{file_type.value}-{component_name}",
                                type=file_type,
                                preset=preset_id,
                                path=file_type.default_path,
                                enabled=True,
                                variables={"component_file": str(component_file)},
                            )
                            return instance

            return None

        except Exception:
            return None

    def delete_component(
        self, file_type: FileType, component_name: str
    ) -> tuple[bool, str]:
        """Delete a component from the library.

        For CLAUDE.md and .gitignore, deletes the component folder.
        For other file types, deletes the .json file.

        Args:
            file_type: File type of the component
            component_name: Name of the component to delete

        Returns:
            Tuple of (success, message)
        """
        try:
            import shutil

            components_dir = get_components_dir()
            type_dir = components_dir / self._get_component_type_dir(file_type)

            # For CLAUDE.md and .gitignore, delete the folder
            if file_type in (FileType.CLAUDE_MD, FileType.GITIGNORE):
                component_folder = type_dir / component_name

                if not component_folder.exists():
                    return False, f"Component '{component_name}' not found"

                # Remove the entire folder
                shutil.rmtree(component_folder)
                return True, f"Component '{component_name}' deleted"
            else:
                # For other file types, try to delete .json first, then raw file
                json_file = type_dir / f"{component_name}.json"

                if json_file.exists():
                    json_file.unlink()
                    return True, f"Component '{component_name}' deleted"

                # If no .json, look for raw file
                for component_file in type_dir.iterdir():
                    if (
                        component_file.is_file()
                        and component_file.stem == component_name
                        and component_file.suffix != ".json"
                    ):
                        component_file.unlink()
                        return True, f"Component '{component_name}' deleted"

                return False, f"Component '{component_name}' not found"

        except Exception as e:
            return False, f"Failed to delete component: {e}"
