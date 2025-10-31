"""Config template management for claudefig.

This module manages global configuration preset templates stored in
~/.claudefig/presets/. These are different from file type presets -
they are complete project configurations that can be applied to new
or existing projects.
"""

import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


from claudefig.models import PresetDefinition
from claudefig.preset_validator import PresetValidator
from claudefig.services.preset_definition_loader import PresetDefinitionLoader

if TYPE_CHECKING:
    from claudefig.config import Config


class ConfigTemplateManager:
    """Manages global config preset templates.

    Handles creation, listing, and application of global preset templates
    that define complete project configurations.
    """

    def __init__(self, global_presets_dir: Optional[Path] = None):
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
            preset_def: PresetDefinition loaded from .claudefig.toml

        Returns:
            Complete config structure dict suitable for saving as .toml
        """
        # Build files list from component references
        files = []
        for i, component in enumerate(preset_def.components, 1):
            if not component.enabled:
                continue

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
                    "enabled": component.enabled,
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

        Looks for directory-based presets with .claudefig.toml files inside.

        Args:
            include_validation: If True, include validation status for each preset

        Returns:
            List of dicts with: name, path, description, component_count, (optional) validation
        """
        presets: list[dict[str, Any]] = []
        if not self.global_presets_dir.exists():
            return presets

        # Look for directories with .claudefig.toml inside them
        for preset_dir in self.global_presets_dir.iterdir():
            if not preset_dir.is_dir():
                continue

            preset_file = preset_dir / ".claudefig.toml"
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
        preset_file = preset_dir / ".claudefig.toml"

        if not preset_dir.exists():
            raise FileNotFoundError(
                f"Preset directory '{name}' not found at {preset_dir}"
            )

        if not preset_file.exists():
            raise FileNotFoundError(
                f"Preset '{name}' missing .claudefig.toml at {preset_file}"
            )

        return Config(config_path=preset_file)

    def save_global_preset(self, name: str, description: str = "") -> None:
        """Save current project config as a new global preset directory.

        Creates a preset directory with .claudefig.toml file inside.

        Args:
            name: Preset name
            description: Optional description

        Raises:
            ValueError: If preset name already exists or is invalid
            FileNotFoundError: If no .claudefig.toml in current directory
        """
        from claudefig.config import Config

        # Validate name
        if not name or "/" in name or "\\" in name:
            raise ValueError(f"Invalid preset name: '{name}'")

        # Check if already exists (directory-based structure)
        preset_dir = self.global_presets_dir / name
        if preset_dir.exists():
            raise ValueError(f"Preset '{name}' already exists")

        # Load current project config
        config = Config()
        if not config.config_path or not config.config_path.exists():
            raise FileNotFoundError("No .claudefig.toml found in current directory")

        # Add description if provided
        if description:
            config.set("claudefig.description", description)

        # Create preset directory
        preset_dir.mkdir(parents=True, exist_ok=True)

        # Save as .claudefig.toml inside preset directory
        preset_file = preset_dir / ".claudefig.toml"
        config.save(preset_file)

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
        self, preset_name: str, target_path: Optional[Path] = None
    ) -> None:
        """Apply a global preset to a project directory.

        Copies the preset's .claudefig.toml file to the target directory.

        Args:
            preset_name: Name of preset to apply
            target_path: Target directory (default: current directory)

        Raises:
            FileNotFoundError: If preset not found
            FileExistsError: If .claudefig.toml already exists in target
        """
        preset_dir = self.global_presets_dir / preset_name
        preset_file = preset_dir / ".claudefig.toml"

        if not preset_dir.exists():
            raise FileNotFoundError(
                f"Preset directory '{preset_name}' not found at {preset_dir}"
            )

        if not preset_file.exists():
            raise FileNotFoundError(f"Preset '{preset_name}' missing .claudefig.toml")

        target_dir = target_path or Path.cwd()
        target_config = target_dir / ".claudefig.toml"

        if target_config.exists():
            raise FileExistsError(f".claudefig.toml already exists at {target_dir}")

        # Copy preset's .claudefig.toml to target
        shutil.copy2(preset_file, target_config)
