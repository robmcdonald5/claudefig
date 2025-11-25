"""Config template management for claudefig.

This module manages global configuration preset templates stored in
~/.claudefig/presets/. These are different from file type presets -
they are complete project configurations that can be applied to new
or existing projects.
"""

import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


from claudefig.models import PresetDefinition
from claudefig.preset_validator import PresetValidator
from claudefig.services.preset_definition_loader import PresetDefinitionLoader
from claudefig.utils.paths import validate_not_symlink

if TYPE_CHECKING:
    from claudefig.config import Config


class ConfigTemplateManager:
    """Manages global config preset templates.

    Handles creation, listing, and application of global preset templates
    that define complete project configurations.
    """

    @staticmethod
    def _sanitize_path_component(name: str) -> str:
        """Sanitize a path component to prevent traversal attacks.

        Args:
            name: The name to sanitize (preset name or component name)

        Returns:
            Sanitized name safe for use in paths

        Raises:
            ValueError: If name is invalid after sanitization
        """
        sanitized = name.replace("/", "").replace("\\", "").replace("..", "")
        sanitized = sanitized.strip().strip(".")
        if not sanitized:
            raise ValueError(f"Invalid name after sanitization: '{name}'")
        return sanitized

    def __init__(self, global_presets_dir: Path | None = None):
        """Initialize config template manager.

        Args:
            global_presets_dir: Path to global presets directory
                               (default: ~/.claudefig/presets/)
        """
        self.global_presets_dir = global_presets_dir or (
            Path.home() / ".claudefig" / "presets"
        )
        self.validator = PresetValidator(self.global_presets_dir)

        # Initialize preset loader
        self.preset_loader = PresetDefinitionLoader(
            user_presets_path=self.global_presets_dir
        )

        # Ensure directory exists
        self._ensure_presets_directory()
        # Note: Default presets are now copied by user_config.py during initialization

    def _ensure_presets_directory(self) -> None:
        """Create ~/.claudefig/presets/ if it doesn't exist."""
        self.global_presets_dir.mkdir(parents=True, exist_ok=True)

    def _build_from_preset_definition(self, preset_def: PresetDefinition) -> dict:
        """Build a config file from a PresetDefinition.

        Args:
            preset_def: PresetDefinition loaded from claudefig.toml

        Returns:
            Complete config structure dict suitable for saving as .toml
        """
        # Build files list from component references
        # Include both enabled AND disabled components to preserve full state
        files = []
        for i, component in enumerate(preset_def.components, 1):
            # Generate file ID
            file_id = f"{preset_def.name}-{component.type.replace('_', '-')}-{i}"

            # Build preset reference in format "type:name"
            preset_ref = f"{component.type}:{component.name}"

            files.append(
                {
                    "id": file_id,
                    "type": component.type,
                    "preset": preset_ref,
                    "path": component.path,
                    "enabled": component.enabled,  # Preserve enabled/disabled state
                    "variables": component.variables if component.variables else {},
                }
            )

        # Return complete config structure
        return {
            "claudefig": {
                "version": "2.0",
                "schema_version": "2.0",
                "description": preset_def.description,
            },
            "init": {"overwrite_existing": False},
            "files": files,
            "custom": {"template_dir": "", "presets_dir": ""},
        }

    def list_global_presets(self, include_validation: bool = False) -> list[dict]:
        """List all global config preset templates.

        Looks for directory-based presets with claudefig.toml files inside.

        Args:
            include_validation: If True, include validation status for each preset

        Returns:
            List of dicts with: name, path, description, component_count, (optional) validation
        """
        presets: list[dict[str, Any]] = []
        if not self.global_presets_dir.exists():
            return presets

        # Look for directories with claudefig.toml inside them
        for preset_dir in self.global_presets_dir.iterdir():
            if not preset_dir.is_dir():
                continue

            preset_file = preset_dir / "claudefig.toml"
            if not preset_file.exists():
                continue

            try:
                with open(preset_file, "rb") as f:
                    preset_data = tomllib.load(f)

                # Get preset metadata
                preset_section = preset_data.get("preset", {})
                components_section = preset_data.get("components", [])

                # Count components (PresetDefinition format uses a list)
                if isinstance(components_section, list):
                    component_count = len(components_section)
                elif isinstance(components_section, dict):
                    # Legacy format: count variants in each component type
                    component_count = sum(
                        len(comp.get("variants", []))
                        for comp in components_section.values()
                        if isinstance(comp, dict)
                    )
                else:
                    component_count = 0

                preset_info = {
                    "name": preset_dir.name,
                    "path": preset_dir,
                    "description": preset_section.get("description", ""),
                    "file_count": component_count,  # Keep this key for backward compatibility
                }

                # Add validation if requested
                if include_validation:
                    from claudefig.services.structure_validator import (
                        validate_preset_integrity,
                    )

                    # Validate preset integrity (files exist)
                    validation = validate_preset_integrity(preset_dir, verbose=False)

                    # Also do basic schema validation
                    errors = list(validation.errors)
                    warnings = list(validation.warnings)

                    # Check for required preset sections
                    if "preset" not in preset_data:
                        errors.append("Missing required 'preset' section")
                    if "components" not in preset_data:
                        errors.append("Missing required 'components' section")

                    preset_info["validation"] = {
                        "valid": validation.is_valid and len(errors) == 0,
                        "errors": errors,
                        "warnings": warnings,
                    }

                presets.append(preset_info)

            except tomllib.TOMLDecodeError as e:
                # Include corrupted presets with error info
                preset_info = {
                    "name": preset_dir.name,
                    "path": preset_dir,
                    "description": "ERROR: Invalid TOML syntax",
                    "file_count": 0,
                }
                if include_validation:
                    preset_info["validation"] = {
                        "valid": False,
                        "errors": [f"Invalid TOML syntax: {e}"],
                        "warnings": [],
                    }
                presets.append(preset_info)
            except Exception as e:
                # Include other errors
                preset_info = {
                    "name": preset_dir.name,
                    "path": preset_dir,
                    "description": f"ERROR: {str(e)}",
                    "file_count": 0,
                }
                if include_validation:
                    preset_info["validation"] = {
                        "valid": False,
                        "errors": [str(e)],
                        "warnings": [],
                    }
                presets.append(preset_info)

        # Sort by name
        presets.sort(key=lambda p: p["name"])
        return presets

    def get_preset_config(self, name: str) -> "Config":
        """Load a global preset as a Config object.

        Args:
            name: Preset name (directory name)

        Returns:
            Config object loaded from preset

        Raises:
            FileNotFoundError: If preset not found
        """
        from claudefig.config import Config

        preset_dir = self.global_presets_dir / name
        preset_file = preset_dir / "claudefig.toml"

        if not preset_dir.exists():
            raise FileNotFoundError(
                f"Preset directory '{name}' not found at {preset_dir}"
            )

        if not preset_file.exists():
            raise FileNotFoundError(
                f"Preset '{name}' missing claudefig.toml at {preset_file}"
            )

        return Config(config_path=preset_file)

    def _collect_components_from_config(self, config: "Config") -> list[dict[str, Any]]:
        """Extract component information from project config.

        Args:
            config: Project configuration

        Returns:
            List of dicts with component info:
            - type: Component type (e.g., "claude_md")
            - name: Component name (e.g., "default")
            - path: Target path from instance
            - enabled: Whether instance is enabled
            - source_path: Absolute path to source component directory
            - variables: Any variables associated with the component
        """
        import logging

        from claudefig.component_loaders import create_component_loader_chain
        from claudefig.models import FileInstance
        from claudefig.services import config_service

        logger = logging.getLogger(__name__)
        components: list[dict[str, Any]] = []

        # Get file instances from config
        instances_data = config_service.get_file_instances(config.data)
        if not instances_data:
            return components

        # Get current preset name from config (for component discovery)
        current_preset = config_service.get_value(
            config.data, "claudefig.template_source", "default"
        )

        # Create component loader chain
        loader = create_component_loader_chain()

        # Process each file instance
        for instance_data in instances_data:
            try:
                instance = FileInstance.from_dict(instance_data)

                # Include both enabled AND disabled components
                # Only skip if component information is missing

                # Extract component name from preset field (format: "type:name")
                component_name = instance.get_component_name()
                if not component_name:
                    continue

                component_type = instance.type.value

                # Try to locate the component using loader chain
                source_path = loader.load(
                    current_preset, component_type, component_name
                )

                if source_path and source_path.exists():
                    # Component found - add with source path for copying
                    components.append(
                        {
                            "type": component_type,
                            "name": component_name,
                            "path": instance.path,
                            "enabled": instance.enabled,  # Preserve enabled/disabled state
                            "source_path": source_path,
                            "variables": instance.variables,
                        }
                    )
                else:
                    # Component not found - still include in preset definition
                    # but without source_path (won't copy files)
                    logger.warning(
                        f"Component {component_type}/{component_name} not found at source, "
                        f"including in preset without copying files"
                    )
                    components.append(
                        {
                            "type": component_type,
                            "name": component_name,
                            "path": instance.path,
                            "enabled": instance.enabled,
                            "source_path": None,  # No source to copy from
                            "variables": instance.variables,
                        }
                    )

            except Exception as e:
                # Log but continue processing other instances
                logger.warning(
                    f"Error processing instance {instance_data.get('id')}: {e}"
                )
                continue

        return components

    def _copy_component_to_preset(
        self, source_path: Path, preset_dir: Path, component_type: str, name: str
    ) -> None:
        """Copy a component directory to the new preset structure.

        Args:
            source_path: Absolute path to source component directory
            preset_dir: Root directory of the new preset
            component_type: Component type (e.g., "claude_md")
            name: Component name (e.g., "default")

        Raises:
            FileOperationError: If copy operation fails
        """
        from claudefig.exceptions import FileOperationError

        # Create destination directory structure
        dest_path = preset_dir / "components" / component_type / name

        try:
            # Security: Reject symlinks
            validate_not_symlink(source_path, context="component source")

            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy entire component directory (symlinks=False for security)
            if source_path.is_dir():
                shutil.copytree(
                    source_path,
                    dest_path,
                    dirs_exist_ok=True,
                    symlinks=False,
                    ignore_dangling_symlinks=True,
                )
            else:
                # If source is a file (shouldn't happen), copy it
                dest_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)

        except Exception as e:
            raise FileOperationError(
                f"copy component {component_type}/{name} to preset", str(e)
            ) from e

    def _build_preset_definition(
        self, name: str, description: str, components: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build PresetDefinition TOML structure.

        Args:
            name: Preset name
            description: Preset description
            components: List of component info from _collect_components_from_config()

        Returns:
            Dict in PresetDefinition format for TOML serialization
        """
        # Build preset metadata
        preset_data: dict[str, Any] = {
            "preset": {
                "name": name,
                "version": "1.0.0",
                "description": description,
            },
            "components": [],
        }

        # Add each component to the definition
        for component in components:
            component_entry = {
                "type": component["type"],
                "name": component["name"],
                "path": component["path"],
                "enabled": component["enabled"],
            }

            # Include variables if present
            if component.get("variables"):
                component_entry["variables"] = component["variables"]

            preset_data["components"].append(component_entry)

        return preset_data

    def save_global_preset(
        self, name: str, description: str = "", config_path: Path | None = None
    ) -> None:
        """Save current project config as a new global preset directory.

        Creates a preset directory with claudefig.toml file and component files.

        This method:
        1. Validates preset name
        2. Loads current project config
        3. Discovers all components used in the project
        4. Copies component files to new preset directory structure
        5. Generates PresetDefinition format claudefig.toml

        Args:
            name: Preset name
            description: Optional description
            config_path: Path to config file. If None, uses default Config() behavior.

        Raises:
            ValueError: If preset name already exists or is invalid
            FileNotFoundError: If no claudefig.toml found
            FileOperationError: If component copying fails
        """
        import tomli_w

        from claudefig.config import Config
        from claudefig.exceptions import FileOperationError

        # Validate name
        if not name or "/" in name or "\\" in name:
            raise ValueError(f"Invalid preset name: '{name}'")

        # Check if already exists (directory-based structure)
        preset_dir = self.global_presets_dir / name
        if preset_dir.exists():
            raise ValueError(f"Preset '{name}' already exists")

        # Load project config (from explicit path or default discovery)
        config = Config(config_path=config_path)
        if not config.config_path or not config.config_path.exists():
            raise FileNotFoundError("No claudefig.toml found")

        try:
            # Collect components from current config
            components = self._collect_components_from_config(config)

            # Create preset directory
            preset_dir.mkdir(parents=True, exist_ok=True)

            # Copy each component to preset structure (only if source exists)
            for component in components:
                if component["source_path"] is not None:
                    self._copy_component_to_preset(
                        source_path=component["source_path"],
                        preset_dir=preset_dir,
                        component_type=component["type"],
                        name=component["name"],
                    )

            # Build and save PresetDefinition
            preset_data = self._build_preset_definition(name, description, components)
            preset_file = preset_dir / "claudefig.toml"

            with open(preset_file, "wb") as f:
                tomli_w.dump(preset_data, f)

        except Exception as e:
            # Cleanup preset directory if creation failed
            if preset_dir.exists():
                import contextlib

                with contextlib.suppress(Exception):
                    shutil.rmtree(preset_dir)

            # Re-raise the original exception
            if isinstance(e, (ValueError, FileNotFoundError, FileOperationError)):
                raise
            else:
                raise FileOperationError(f"create preset '{name}'", str(e)) from e

    def create_preset_from_discovery(
        self,
        preset_name: str,
        description: str,
        components: list,
    ) -> None:
        """Create a preset from discovered components.

        Creates a preset directory with claudefig.toml file and component files
        from a list of discovered components.

        Args:
            preset_name: Name of the preset to create
            description: Optional description
            components: List of DiscoveredComponent objects to include

        Raises:
            ValueError: If preset name is invalid or already exists
            FileOperationError: If component copying fails
        """
        import tomli_w

        from claudefig.exceptions import FileOperationError

        if not preset_name:
            raise ValueError("Preset name cannot be empty")
        safe_preset_name = self._sanitize_path_component(preset_name)

        preset_dir = self.global_presets_dir / safe_preset_name

        try:
            # Use exist_ok=False to prevent race condition (TOCTOU)
            # This atomically checks existence and creates in one operation
            preset_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError as e:
            raise ValueError(f"Preset '{preset_name}' already exists") from e

        try:
            components_dir = preset_dir / "components"
            components_dir.mkdir(exist_ok=True)

            # Build component list for preset definition
            component_refs = []

            # Copy each component to preset directory structure
            for component in components:
                safe_comp_name = self._sanitize_path_component(component.name)

                comp_dir = components_dir / component.type.value / safe_comp_name
                comp_dir.mkdir(parents=True, exist_ok=True)

                # Security: Reject symlinks
                validate_not_symlink(component.path, context="discovered component")

                # Copy component file(s) (symlinks=False for security)
                if component.path.is_file():
                    dest_file = comp_dir / component.path.name
                    shutil.copy2(component.path, dest_file)
                elif component.path.is_dir():
                    shutil.copytree(
                        component.path,
                        comp_dir,
                        dirs_exist_ok=True,
                        symlinks=False,
                        ignore_dangling_symlinks=True,
                    )

                # Add component reference to preset definition
                component_refs.append(
                    {
                        "type": component.type.value,
                        "name": safe_comp_name,
                        "path": str(component.relative_path),
                        "enabled": True,
                        "variables": {},
                    }
                )

            # Build preset definition
            preset_data: dict[str, Any] = {
                "preset": {
                    "name": safe_preset_name,
                    "version": "1.0.0",
                    "description": description
                    or "Preset created from repository components",
                },
                "components": component_refs,
            }

            # Save preset TOML
            toml_path = preset_dir / "claudefig.toml"
            with open(toml_path, "wb") as f:
                tomli_w.dump(preset_data, f)

        except Exception as e:
            # Cleanup preset directory if creation failed
            if preset_dir.exists():
                import contextlib

                with contextlib.suppress(Exception):
                    shutil.rmtree(preset_dir)

            # Re-raise the original exception
            if isinstance(e, (ValueError, FileNotFoundError)):
                raise
            else:
                raise FileOperationError(
                    f"create preset '{preset_name}'", str(e)
                ) from e

    def delete_global_preset(self, name: str) -> None:
        """Delete a global preset directory.

        Args:
            name: Preset name

        Raises:
            ValueError: If trying to delete 'default'
            FileNotFoundError: If preset not found
        """
        if name == "default":
            raise ValueError("Cannot delete default preset")

        preset_dir = self.global_presets_dir / name
        if not preset_dir.exists():
            raise FileNotFoundError(f"Preset '{name}' not found")

        shutil.rmtree(preset_dir)

    def apply_preset_to_project(
        self,
        preset_name: str,
        target_path: Path | None = None,
        overwrite: bool = False,
    ) -> None:
        """Apply a global preset to a project directory.

        Converts the preset's PresetDefinition format to project config format
        and saves it to the target directory.

        Args:
            preset_name: Name of preset to apply
            target_path: Target directory (default: current directory)
            overwrite: If True, overwrite existing claudefig.toml (default: False)

        Raises:
            FileNotFoundError: If preset not found
            FileExistsError: If claudefig.toml already exists and overwrite=False
        """
        import tomli_w

        preset_dir = self.global_presets_dir / preset_name
        preset_file = preset_dir / "claudefig.toml"

        if not preset_dir.exists():
            raise FileNotFoundError(
                f"Preset directory '{preset_name}' not found at {preset_dir}"
            )

        if not preset_file.exists():
            raise FileNotFoundError(f"Preset '{preset_name}' missing claudefig.toml")

        target_dir = target_path or Path.cwd()
        target_config = target_dir / "claudefig.toml"

        if target_config.exists() and not overwrite:
            raise FileExistsError(f"claudefig.toml already exists at {target_dir}")

        # Load the preset definition
        preset_def = self.preset_loader.load_preset(preset_name)

        # Convert PresetDefinition to project config format
        config_data = self._build_from_preset_definition(preset_def)

        # Save as project config
        with open(target_config, "wb") as f:
            tomli_w.dump(config_data, f)
