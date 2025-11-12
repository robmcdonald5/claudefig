"""Configuration management for claudefig.

This module provides the Config class, which is a compatibility wrapper
around config_service. It delegates all operations to the service layer
to ensure TUI and CLI use identical business logic.

For new code, prefer using config_service directly with TomlConfigRepository.
"""

from pathlib import Path
from typing import Any

from claudefig.models import ValidationResult
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.services import config_service


class Config:
    """Configuration manager - delegates to config_service.

    This is a compatibility wrapper that provides the old Config API
    while delegating to the new service layer. This ensures TUI and CLI
    use identical business logic for config operations.

    For new code, prefer using config_service directly:
        repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(repo)
        value = config_service.get_value(config_data, "some.key")
    """

    SCHEMA_VERSION = "2.0"
    DEFAULT_CONFIG = config_service.DEFAULT_CONFIG  # Delegate to service

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration.

        Args:
            config_path: Path to config file. If None, searches for claudefig.toml
                        in current directory and user home directory.
        """
        # Find config path
        if config_path is None:
            config_path = config_service.find_config_path()

        self.config_path = config_path
        self._repo: TomlConfigRepository | None

        # Load config data using service layer
        if self.config_path and self.config_path.exists():
            self._repo = TomlConfigRepository(self.config_path)
            self.data = config_service.load_config(self._repo)
        else:
            self._repo = None
            self.data = config_service.DEFAULT_CONFIG.copy()

        self.schema_version = config_service.get_value(
            self.data, "claudefig.schema_version", "2.0"
        )
        self._validation_result: ValidationResult | None = None

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Delegates to config_service.get_value() to ensure identical behavior
        between TUI (using this method) and CLI (using config_service directly).

        Args:
            key: Configuration key in dot notation (e.g., "init.create_claude_md")
            default: Default value if key not found

        Returns:
            Configuration value or default.
        """
        return config_service.get_value(self.data, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.

        Delegates to config_service.set_value() to ensure identical behavior
        between TUI (using this method) and CLI (using config_service directly).

        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        config_service.set_value(self.data, key, value)

    def save(self, path: Path | None = None) -> None:
        """Save configuration to file.

        Delegates to config_service.save_config() to ensure identical behavior
        between TUI (using this method) and CLI (using config_service directly).

        Args:
            path: Path to save config. If None, uses self.config_path or creates
                  claudefig.toml in current directory.
        """
        save_path = path or self.config_path or Path.cwd() / "claudefig.toml"

        # Create repository for save location
        save_repo = TomlConfigRepository(save_path)

        # Delegate to service layer
        config_service.save_config(self.data, save_repo)

        # Update our state
        self.config_path = save_path
        self._repo = save_repo

    def get_file_instances(self) -> list[dict[str, Any]]:
        """Get file instances from config.

        Delegates to config_service.get_file_instances() to ensure identical
        behavior between TUI and CLI.

        Returns:
            List of file instance dictionaries
        """
        return config_service.get_file_instances(self.data)

    def set_file_instances(self, instances: list[dict[str, Any]]) -> None:
        """Set file instances in config.

        Delegates to config_service.set_file_instances() to ensure identical
        behavior between TUI and CLI.

        Args:
            instances: List of file instance dictionaries
        """
        config_service.set_file_instances(self.data, instances)

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

        Delegates to config_service to ensure identical behavior
        between TUI and CLI.

        Args:
            path: Path where to create the config file

        Returns:
            Config instance with default values.
        """
        # Create default config using service layer
        default_config = config_service.DEFAULT_CONFIG.copy()
        repo = TomlConfigRepository(path)
        config_service.save_config(default_config, repo)

        # Return Config wrapper
        return cls(config_path=path)

    def get_validation_result(self) -> ValidationResult:
        """Get cached validation result, or run validation if not cached.

        Delegates to config_service.validate_config_schema() to ensure
        identical validation logic between TUI and CLI.

        Returns:
            ValidationResult from schema validation
        """
        if self._validation_result is None:
            self._validation_result = config_service.validate_config_schema(self.data)

        return self._validation_result

    def validate_schema(self) -> ValidationResult:
        """Validate configuration schema.

        Alias for get_validation_result() for backward compatibility.

        Returns:
            ValidationResult from schema validation
        """
        return self.get_validation_result()

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return self.data.copy()
