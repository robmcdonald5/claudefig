"""Configuration management for claudefig."""

import sys
from pathlib import Path
from typing import Any, Optional

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

import tomli_w

from claudefig.models import ValidationResult


class Config:
    """Manages claudefig configuration."""

    SCHEMA_VERSION = "2.0"

    DEFAULT_CONFIG = {
        "claudefig": {
            "version": "2.0",
            "schema_version": "2.0",
        },
        "init": {
            "overwrite_existing": False,
        },
        "files": [],  # File instances
        "custom": {
            "template_dir": "",
            "presets_dir": "",
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
        self.schema_version = self.get("claudefig.schema_version", "2.0")
        self._validation_result: Optional[ValidationResult] = None

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

    def get_file_instances(self) -> list[dict[str, Any]]:
        """Get file instances from config.

        Returns:
            List of file instance dictionaries
        """
        return self.data.get("files", [])

    def set_file_instances(self, instances: list[dict[str, Any]]) -> None:
        """Set file instances in config.

        Args:
            instances: List of file instance dictionaries
        """
        if "files" not in self.data:
            self.data["files"] = []
        self.data["files"] = instances

    def add_file_instance(self, instance: dict[str, Any]) -> None:
        """Add a file instance to config.

        Args:
            instance: File instance dictionary
        """
        if "files" not in self.data:
            self.data["files"] = []
        self.data["files"].append(instance)

    def remove_file_instance(self, instance_id: str) -> bool:
        """Remove a file instance from config.

        Args:
            instance_id: ID of instance to remove

        Returns:
            True if removed, False if not found
        """
        if "files" not in self.data:
            return False

        original_length = len(self.data["files"])
        self.data["files"] = [
            f for f in self.data["files"] if f.get("id") != instance_id
        ]
        return len(self.data["files"]) < original_length

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
        config.schema_version = "2.0"
        config.save(path)
        return config

    def get_validation_result(self) -> ValidationResult:
        """Get cached validation result, or run validation if not cached.

        Returns:
            ValidationResult from schema validation
        """
        if self._validation_result is None:
            self._validation_result = self.validate_schema()
        return self._validation_result

    def validate_schema(self) -> ValidationResult:
        """Validate the configuration schema.

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(valid=True)

        # Validate that data is a dictionary
        if not isinstance(self.data, dict):
            result.add_error("Configuration must be a dictionary")
            return result

        # Validate required sections exist
        required_sections = ["claudefig"]
        for section in required_sections:
            if section not in self.data:
                result.add_error(f"Missing required section: '{section}'")

        # Validate claudefig section
        if "claudefig" in self.data:
            claudefig = self.data["claudefig"]
            if not isinstance(claudefig, dict):
                result.add_error("Section 'claudefig' must be a dictionary")
            else:
                # Check for required keys
                if "schema_version" not in claudefig:
                    result.add_warning("Missing 'claudefig.schema_version' - using default")

                # Validate schema version
                schema_version = claudefig.get("schema_version")
                if schema_version and schema_version != self.SCHEMA_VERSION:
                    result.add_warning(
                        f"Schema version mismatch: config has '{schema_version}', "
                        f"expected '{self.SCHEMA_VERSION}'"
                    )

        # Validate init section (optional, but must be dict if present)
        if "init" in self.data:
            init = self.data["init"]
            if not isinstance(init, dict):
                result.add_error("Section 'init' must be a dictionary")
            else:
                # Validate known init keys have correct types
                if "overwrite_existing" in init and not isinstance(
                    init["overwrite_existing"], bool
                ):
                    result.add_error("'init.overwrite_existing' must be a boolean")

                if "create_backup" in init and not isinstance(
                    init["create_backup"], bool
                ):
                    result.add_error("'init.create_backup' must be a boolean")

        # Validate files section (optional, but must be list if present)
        if "files" in self.data:
            files = self.data["files"]
            if not isinstance(files, list):
                result.add_error("Section 'files' must be a list")
            else:
                # Validate each file instance has required fields
                for i, file_inst in enumerate(files):
                    if not isinstance(file_inst, dict):
                        result.add_error(f"File instance at index {i} must be a dictionary")
                        continue

                    required_fields = ["id", "type", "preset", "path"]
                    for field in required_fields:
                        if field not in file_inst:
                            result.add_error(
                                f"File instance at index {i} missing required field: '{field}'"
                            )

        # Validate custom section (optional, but must be dict if present)
        if "custom" in self.data:
            custom = self.data["custom"]
            if not isinstance(custom, dict):
                result.add_error("Section 'custom' must be a dictionary")

        return result
