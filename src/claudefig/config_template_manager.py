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

import tomli_w

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

        # Ensure directory exists and has default presets
        self._ensure_presets_directory()
        self._ensure_default_presets()

    def _ensure_presets_directory(self) -> None:
        """Create ~/.claudefig/presets/ if it doesn't exist."""
        self.global_presets_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_default_presets(self) -> None:
        """Create default preset configs in ~/.claudefig/presets/ if they don't exist.

        Loads preset definitions from library and converts them to config files.
        """
        # Get list of available presets from library
        available_presets = self.preset_loader.list_available_presets()

        for preset_name in available_presets:
            preset_path = self.global_presets_dir / f"{preset_name}.toml"
            if not preset_path.exists():
                try:
                    # Load preset definition from library
                    preset_def = self.preset_loader.load_preset(preset_name)
                    # Convert to config format
                    config_data = self._build_from_preset_definition(preset_def)
                    # Save to user presets directory
                    with open(preset_path, "wb") as f:
                        tomli_w.dump(config_data, f)
                except FileNotFoundError:
                    # Preset not found in library, skip
                    continue
                except (OSError, ValueError, KeyError, AttributeError):
                    # Error loading/converting preset, skip
                    continue

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

        Args:
            include_validation: If True, include validation status for each preset

        Returns:
            List of dicts with: name, path, description, file_count, (optional) validation
        """
        presets: list[dict[str, Any]] = []
        if not self.global_presets_dir.exists():
            return presets

        for preset_file in self.global_presets_dir.glob("*.toml"):
            try:
                with open(preset_file, "rb") as f:
                    preset_data = tomllib.load(f)

                preset_info = {
                    "name": preset_file.stem,
                    "path": preset_file,
                    "description": preset_data.get("claudefig", {}).get(
                        "description", ""
                    ),
                    "file_count": len(preset_data.get("files", [])),
                }

                # Add validation if requested
                if include_validation:
                    validation = self.validator.validate_preset_config(preset_file)
                    preset_info["validation"] = {
                        "valid": validation.valid,
                        "errors": validation.errors,
                        "warnings": validation.warnings,
                    }

                presets.append(preset_info)

            except tomllib.TOMLDecodeError as e:
                # Include corrupted presets with error info
                preset_info = {
                    "name": preset_file.stem,
                    "path": preset_file,
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
                    "name": preset_file.stem,
                    "path": preset_file,
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
            name: Preset name (without .toml extension)

        Returns:
            Config object loaded from preset

        Raises:
            FileNotFoundError: If preset not found
        """
        from claudefig.config import Config

        preset_path = self.global_presets_dir / f"{name}.toml"
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset '{name}' not found at {preset_path}")

        return Config(config_path=preset_path)

    def save_global_preset(self, name: str, description: str = "") -> None:
        """Save current project config as a new global preset.

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

        # Check if already exists
        preset_path = self.global_presets_dir / f"{name}.toml"
        if preset_path.exists():
            raise ValueError(f"Preset '{name}' already exists")

        # Load current project config
        config = Config()
        if not config.config_path or not config.config_path.exists():
            raise FileNotFoundError("No .claudefig.toml found in current directory")

        # Add description if provided
        if description:
            config.set("claudefig.description", description)

        # Save as preset
        config.save(preset_path)

    def delete_global_preset(self, name: str) -> None:
        """Delete a global preset.

        Args:
            name: Preset name

        Raises:
            ValueError: If trying to delete 'default'
            FileNotFoundError: If preset not found
        """
        if name == "default":
            raise ValueError("Cannot delete default preset")

        preset_path = self.global_presets_dir / f"{name}.toml"
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset '{name}' not found")

        preset_path.unlink()

    def apply_preset_to_project(
        self, preset_name: str, target_path: Optional[Path] = None
    ) -> None:
        """Apply a global preset to a project directory.

        Args:
            preset_name: Name of preset to apply
            target_path: Target directory (default: current directory)

        Raises:
            FileNotFoundError: If preset not found
            FileExistsError: If .claudefig.toml already exists in target
        """
        preset_path = self.global_presets_dir / f"{preset_name}.toml"
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset '{preset_name}' not found")

        target_dir = target_path or Path.cwd()
        target_config = target_dir / ".claudefig.toml"

        if target_config.exists():
            raise FileExistsError(f".claudefig.toml already exists at {target_dir}")

        # Copy preset to target
        shutil.copy2(preset_path, target_config)
