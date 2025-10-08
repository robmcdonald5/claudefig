"""Configuration management for claudefig."""

import sys
from pathlib import Path
from typing import Any, Optional

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

import tomli_w


class Config:
    """Manages claudefig configuration."""

    DEFAULT_CONFIG = {
        "claudefig": {
            "version": "1.0",
            "template_source": "default",
        },
        "init": {
            "create_claude_md": True,
            "create_gitignore_entries": True,
            "overwrite_existing": False,
        },
        "claude": {
            # .claude/ directory features - all disabled by default
            "create_settings": False,
            "create_settings_local": False,
            "create_commands": False,
            "create_agents": False,
            "create_hooks": False,
            "create_output_styles": False,
            "create_statusline": False,
            "create_mcp": False,
        },
        "custom": {
            "template_dir": "",
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.

        Args:
            config_path: Path to config file. If None, searches for .claudefig.toml
                        in current directory and user home directory.
        """
        self.config_path = config_path or self._find_config()
        self.data = self._load_config()

    def _find_config(self) -> Optional[Path]:
        """Search for .claudefig.toml in current directory and home directory.

        Returns:
            Path to config file if found, None otherwise.
        """
        search_paths = [
            Path.cwd() / ".claudefig.toml",
            Path.home() / ".claudefig.toml",
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file or return defaults.

        Returns:
            Configuration dictionary.
        """
        if self.config_path and self.config_path.exists():
            with open(self.config_path, "rb") as f:
                return tomllib.load(f)

        return self.DEFAULT_CONFIG.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Configuration key in dot notation (e.g., "init.create_claude_md")
            default: Default value if key not found

        Returns:
            Configuration value or default.
        """
        keys = key.split(".")
        value = self.data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.

        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split(".")
        data = self.data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file.

        Args:
            path: Path to save config. If None, uses self.config_path or creates
                  .claudefig.toml in current directory.
        """
        save_path = path or self.config_path or Path.cwd() / ".claudefig.toml"

        with open(save_path, "wb") as f:
            tomli_w.dump(self.data, f)

        self.config_path = save_path

    @classmethod
    def create_default(cls, path: Path) -> "Config":
        """Create a new config file with default values.

        Args:
            path: Path where to create the config file

        Returns:
            Config instance with default values.
        """
        config = cls(config_path=None)
        config.data = cls.DEFAULT_CONFIG.copy()
        config.save(path)
        return config
