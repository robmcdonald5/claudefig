"""Config template management for claudefig.

This module manages global configuration preset templates stored in
~/.claudefig/presets/. These are different from file type presets -
they are complete project configurations that can be applied to new
or existing projects.
"""

import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from claudefig.preset_validator import PresetValidator

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

        # Ensure directory exists and has default presets
        self._ensure_presets_directory()
        self._ensure_default_preset()

    def _ensure_presets_directory(self) -> None:
        """Create ~/.claudefig/presets/ if it doesn't exist."""
        self.global_presets_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_default_preset(self) -> None:
        """Create default.toml preset and variants if they don't exist."""
        presets_to_create = {
            "default": self._create_default_preset_config,
            "minimal": self._create_minimal_preset_config,
            "full": self._create_full_preset_config,
            "backend": self._create_backend_preset_config,
            "frontend": self._create_frontend_preset_config,
        }

        for preset_name, config_func in presets_to_create.items():
            preset_path = self.global_presets_dir / f"{preset_name}.toml"
            if not preset_path.exists():
                config_data = config_func()
                with open(preset_path, "wb") as f:
                    tomli_w.dump(config_data, f)

    def _create_default_preset_config(self) -> dict:
        """Create the default preset configuration.

        Returns:
            Default preset configuration dict
        """
        return {
            "claudefig": {
                "version": "2.0",
                "schema_version": "2.0",
                "description": "Default Claude Code configuration with recommended settings",
            },
            "init": {"overwrite_existing": False},
            "files": [
                {
                    "id": "default-claude-md",
                    "type": "claude_md",
                    "preset": "claude_md:default",
                    "path": "CLAUDE.md",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "default-gitignore",
                    "type": "gitignore",
                    "preset": "gitignore:standard",
                    "path": ".gitignore",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "default-settings",
                    "type": "settings_json",
                    "preset": "settings_json:default",
                    "path": ".claude/settings.json",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "default-commands",
                    "type": "commands",
                    "preset": "commands:default",
                    "path": ".claude/commands/",
                    "enabled": True,
                    "variables": {},
                },
            ],
            "custom": {"template_dir": "", "presets_dir": ""},
        }

    def _create_minimal_preset_config(self) -> dict:
        """Create minimal preset configuration.

        Returns:
            Minimal preset configuration dict
        """
        return {
            "claudefig": {
                "version": "2.0",
                "schema_version": "2.0",
                "description": "Minimal Claude Code setup - just CLAUDE.md",
            },
            "init": {"overwrite_existing": False},
            "files": [
                {
                    "id": "minimal-claude-md",
                    "type": "claude_md",
                    "preset": "claude_md:minimal",
                    "path": "CLAUDE.md",
                    "enabled": True,
                    "variables": {},
                }
            ],
            "custom": {"template_dir": "", "presets_dir": ""},
        }

    def _create_full_preset_config(self) -> dict:
        """Create full preset configuration with all features.

        Returns:
            Full preset configuration dict
        """
        return {
            "claudefig": {
                "version": "2.0",
                "schema_version": "2.0",
                "description": "Full Claude Code setup with all features enabled",
            },
            "init": {"overwrite_existing": False},
            "files": [
                {
                    "id": "full-claude-md",
                    "type": "claude_md",
                    "preset": "claude_md:default",
                    "path": "CLAUDE.md",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "full-gitignore",
                    "type": "gitignore",
                    "preset": "gitignore:standard",
                    "path": ".gitignore",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "full-settings",
                    "type": "settings_json",
                    "preset": "settings_json:default",
                    "path": ".claude/settings.json",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "full-settings-local",
                    "type": "settings_local_json",
                    "preset": "settings_local_json:default",
                    "path": ".claude/settings.local.json",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "full-commands",
                    "type": "commands",
                    "preset": "commands:default",
                    "path": ".claude/commands/",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "full-agents",
                    "type": "agents",
                    "preset": "agents:default",
                    "path": ".claude/agents/",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "full-hooks",
                    "type": "hooks",
                    "preset": "hooks:default",
                    "path": ".claude/hooks/",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "full-output-styles",
                    "type": "output_styles",
                    "preset": "output_styles:default",
                    "path": ".claude/output-styles/",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "full-statusline",
                    "type": "statusline",
                    "preset": "statusline:default",
                    "path": ".claude/statusline.sh",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "full-mcp",
                    "type": "mcp",
                    "preset": "mcp:default",
                    "path": ".claude/mcp/",
                    "enabled": True,
                    "variables": {},
                },
            ],
            "custom": {"template_dir": "", "presets_dir": ""},
        }

    def _create_backend_preset_config(self) -> dict:
        """Create backend-focused preset configuration.

        Returns:
            Backend preset configuration dict
        """
        return {
            "claudefig": {
                "version": "2.0",
                "schema_version": "2.0",
                "description": "Backend development focused setup with API and database helpers",
            },
            "init": {"overwrite_existing": False},
            "files": [
                {
                    "id": "backend-claude-md",
                    "type": "claude_md",
                    "preset": "claude_md:backend",
                    "path": "CLAUDE.md",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "backend-gitignore",
                    "type": "gitignore",
                    "preset": "gitignore:standard",
                    "path": ".gitignore",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "backend-settings",
                    "type": "settings_json",
                    "preset": "settings_json:default",
                    "path": ".claude/settings.json",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "backend-commands",
                    "type": "commands",
                    "preset": "commands:default",
                    "path": ".claude/commands/",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "backend-agents",
                    "type": "agents",
                    "preset": "agents:default",
                    "path": ".claude/agents/",
                    "enabled": True,
                    "variables": {},
                },
            ],
            "custom": {"template_dir": "", "presets_dir": ""},
        }

    def _create_frontend_preset_config(self) -> dict:
        """Create frontend-focused preset configuration.

        Returns:
            Frontend preset configuration dict
        """
        return {
            "claudefig": {
                "version": "2.0",
                "schema_version": "2.0",
                "description": "Frontend development focused setup with UI/UX helpers",
            },
            "init": {"overwrite_existing": False},
            "files": [
                {
                    "id": "frontend-claude-md",
                    "type": "claude_md",
                    "preset": "claude_md:frontend",
                    "path": "CLAUDE.md",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "frontend-gitignore",
                    "type": "gitignore",
                    "preset": "gitignore:standard",
                    "path": ".gitignore",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "frontend-settings",
                    "type": "settings_json",
                    "preset": "settings_json:default",
                    "path": ".claude/settings.json",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "frontend-commands",
                    "type": "commands",
                    "preset": "commands:default",
                    "path": ".claude/commands/",
                    "enabled": True,
                    "variables": {},
                },
                {
                    "id": "frontend-output-styles",
                    "type": "output_styles",
                    "preset": "output_styles:default",
                    "path": ".claude/output-styles/",
                    "enabled": True,
                    "variables": {},
                },
            ],
            "custom": {"template_dir": "", "presets_dir": ""},
        }

    def list_global_presets(self, include_validation: bool = False) -> list[dict]:
        """List all global config preset templates.

        Args:
            include_validation: If True, include validation status for each preset

        Returns:
            List of dicts with: name, path, description, file_count, (optional) validation
        """
        presets = []
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
