"""Configuration service layer for business logic.

This module provides reusable business logic for configuration management,
separated from data access (repositories) and UI (CLI/TUI).

All functions accept a repository for dependency injection, enabling:
- Testing with FakeConfigRepository (no file I/O)
- Code reuse between CLI and TUI
- Swappable storage backends
"""

import copy
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from claudefig.models import ValidationResult
from claudefig.repositories import AbstractConfigRepository

# Schema version for claudefig configuration
SCHEMA_VERSION = "2.0"

# Default configuration structure
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

# Valid config keys with expected types for CLI validation
# Keys must match dot-notation used in get_value/set_value
VALID_CONFIG_KEYS: dict[str, type] = {
    "claudefig.version": str,
    "claudefig.schema_version": str,
    "claudefig.template_source": str,
    "init.overwrite_existing": bool,
    "init.create_backup": bool,
    "custom.template_dir": str,
    "custom.presets_dir": str,
}


def validate_config_key(key: str, value: Any) -> ValidationResult:
    """Validate a config key and value before setting.

    This ensures CLI users cannot set arbitrary keys that would corrupt
    the config file or cause unexpected behavior.

    Args:
        key: Dot-notation config key (e.g., "init.overwrite_existing")
        value: Value to set (already parsed to appropriate type)

    Returns:
        ValidationResult with any errors

    Example:
        >>> validate_config_key("init.overwrite_existing", True)
        ValidationResult(valid=True, errors=[], warnings=[])
        >>> validate_config_key("unknown.key", "value")
        ValidationResult(valid=False, errors=["Unknown config key: 'unknown.key'..."], ...)
    """
    result = ValidationResult(valid=True)

    if key not in VALID_CONFIG_KEYS:
        valid_keys = ", ".join(sorted(VALID_CONFIG_KEYS.keys()))
        result.add_error(f"Unknown config key: '{key}'. Valid keys: {valid_keys}")
        return result

    expected_type = VALID_CONFIG_KEYS[key]
    if not isinstance(value, expected_type):
        result.add_error(
            f"Invalid type for '{key}': expected {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )

    return result


def find_config_path() -> Path | None:
    """Search for claudefig.toml in current directory and home directory.

    Search order:
    1. Current working directory (claudefig.toml)
    2. User home directory (~/.claudefig/config.toml)

    Returns:
        Path to config file if found, None otherwise.
    """
    search_paths = [
        Path.cwd() / "claudefig.toml",
        Path.home() / ".claudefig" / "config.toml",
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def load_config(repo: AbstractConfigRepository) -> dict[str, Any]:
    """Load configuration from repository with fallback to defaults.

    Business logic:
    1. Check if config exists in repository
    2. Load from repository if exists
    3. Return defaults if not exists or on error
    4. Validate loaded config

    Args:
        repo: Configuration repository to load from.

    Returns:
        Configuration dictionary (either loaded or defaults).
    """
    if not repo.exists():
        return DEFAULT_CONFIG.copy()

    try:
        data = repo.load()
        return data
    except (OSError, ValueError, KeyError):
        # On any error, return defaults
        return DEFAULT_CONFIG.copy()


def save_config(data: dict[str, Any], repo: AbstractConfigRepository) -> None:
    """Save configuration to repository.

    Business logic:
    1. Validate config before saving (future)
    2. Create backup if config already exists (future)
    3. Save via repository

    Args:
        data: Configuration data to save.
        repo: Configuration repository to save to.

    Raises:
        IOError: If save operation fails.
        ValueError: If data is invalid.
    """
    # Future: Validate before saving
    # result = validate_config_schema(data)
    # if result.has_errors:
    #     raise ValueError(f"Invalid config: {result.errors}")

    repo.save(data)


def get_value(data: dict[str, Any], key: str, default: Any = None) -> Any:
    """Get configuration value by dot-notation key.

    Supports nested key access like "init.overwrite_existing".

    Args:
        data: Configuration data dictionary.
        key: Configuration key in dot notation (e.g., "init.create_backup").
        default: Default value if key not found.

    Returns:
        Configuration value or default if not found.

    Example:
        >>> config = {"init": {"overwrite": True}}
        >>> get_value(config, "init.overwrite")
        True
        >>> get_value(config, "init.missing", False)
        False
    """
    keys = key.split(".")
    value: Any = data

    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default

        if value is None:
            return default

    return value


def set_value(data: dict[str, Any], key: str, value: Any) -> None:
    """Set configuration value by dot-notation key.

    Creates nested dictionaries as needed.

    Args:
        data: Configuration data dictionary (modified in-place).
        key: Configuration key in dot notation.
        value: Value to set.

    Example:
        >>> config = {}
        >>> set_value(config, "init.overwrite", True)
        >>> config
        {'init': {'overwrite': True}}
    """
    keys = key.split(".")
    current = data

    # Navigate to parent, creating dicts as needed
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    # Set final value
    current[keys[-1]] = value


def get_file_instances(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Get file instances from configuration.

    Args:
        data: Configuration data dictionary.

    Returns:
        List of file instance dictionaries.
    """
    return cast(list[dict[str, Any]], data.get("files", []))


def set_file_instances(data: dict[str, Any], instances: list[dict[str, Any]]) -> None:
    """Set file instances in configuration.

    Args:
        data: Configuration data dictionary (modified in-place).
        instances: List of file instance dictionaries.
    """
    data["files"] = instances


def add_file_instance(data: dict[str, Any], instance: dict[str, Any]) -> None:
    """Add a file instance to configuration.

    Args:
        data: Configuration data dictionary (modified in-place).
        instance: File instance dictionary to add.
    """
    if "files" not in data:
        data["files"] = []
    data["files"].append(instance)


def remove_file_instance(data: dict[str, Any], instance_id: str) -> bool:
    """Remove a file instance from configuration.

    Args:
        data: Configuration data dictionary (modified in-place).
        instance_id: ID of instance to remove.

    Returns:
        True if removed, False if not found.
    """
    if "files" not in data:
        return False

    original_length = len(data["files"])
    data["files"] = [f for f in data["files"] if f.get("id") != instance_id]
    return len(data["files"]) < original_length


def create_default_config(repo: AbstractConfigRepository) -> dict[str, Any]:
    """Create a new config file with default values.

    Args:
        repo: Configuration repository to save to.

    Returns:
        Default configuration dictionary.
    """
    config_data = DEFAULT_CONFIG.copy()
    repo.save(config_data)
    return config_data


def validate_config_schema(data: dict[str, Any]) -> ValidationResult:
    """Validate the configuration schema.

    Validates:
    - Required sections exist (claudefig)
    - Schema version compatibility
    - Section types (dict, list, etc.)
    - Required fields in file instances
    - Field types (booleans, etc.)

    Args:
        data: Configuration data dictionary.

    Returns:
        ValidationResult with any errors or warnings.
    """
    result = ValidationResult(valid=True)

    # Validate that data is a dictionary
    if not isinstance(data, dict):
        result.add_error("Configuration must be a dictionary")
        return result

    # Validate required sections exist
    required_sections = ["claudefig"]
    for section in required_sections:
        if section not in data:
            result.add_error(f"Missing required section: '{section}'")

    # Validate claudefig section
    if "claudefig" in data:
        claudefig = data["claudefig"]
        if not isinstance(claudefig, dict):
            result.add_error("Section 'claudefig' must be a dictionary")
        else:
            # Check for required keys
            if "schema_version" not in claudefig:
                result.add_warning("Missing 'claudefig.schema_version' - using default")

            # Validate schema version
            schema_version = claudefig.get("schema_version")
            if schema_version and schema_version != SCHEMA_VERSION:
                result.add_warning(
                    f"Schema version mismatch: config has '{schema_version}', "
                    f"expected '{SCHEMA_VERSION}'"
                )

    # Validate init section (optional, but must be dict if present)
    if "init" in data:
        init = data["init"]
        if not isinstance(init, dict):
            result.add_error("Section 'init' must be a dictionary")
        else:
            # Validate known init keys have correct types
            if "overwrite_existing" in init and not isinstance(
                init["overwrite_existing"], bool
            ):
                result.add_error("'init.overwrite_existing' must be a boolean")

            if "create_backup" in init and not isinstance(init["create_backup"], bool):
                result.add_error("'init.create_backup' must be a boolean")

    # Validate files section (optional, but must be list if present)
    if "files" in data:
        files = data["files"]
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
    if "custom" in data:
        custom = data["custom"]
        if not isinstance(custom, dict):
            result.add_error("Section 'custom' must be a dictionary")

    return result


@lru_cache(maxsize=1)
def _get_config_singleton_cached(config_path: Path | None = None) -> dict[str, Any]:
    """Internal cached config loader.

    Args:
        config_path: Optional path to config file.

    Returns:
        Configuration dictionary (internal use only - do not modify).
    """
    from claudefig.repositories import TomlConfigRepository

    path = config_path or find_config_path() or Path.cwd() / "claudefig.toml"
    repo = TomlConfigRepository(path)
    return load_config(repo)


def get_config_singleton(config_path: Path | None = None) -> dict[str, Any]:
    """Get singleton configuration instance (cached).

    This is a convenience function for applications that want a global config.
    For better testability, prefer using load_config() with explicit repository.

    Args:
        config_path: Optional path to config file. If None, searches using find_config_path().

    Returns:
        Configuration dictionary (a deep copy to prevent cache pollution).

    Note:
        This function caches the result. Call reload_config_singleton()
        to force reload from disk.
    """
    # Return a deep copy to prevent callers from modifying the cached dict
    return copy.deepcopy(_get_config_singleton_cached(config_path))


def reload_config_singleton() -> dict[str, Any]:
    """Force reload of singleton configuration.

    Returns:
        Freshly loaded configuration dictionary.
    """
    _get_config_singleton_cached.cache_clear()
    return get_config_singleton()
