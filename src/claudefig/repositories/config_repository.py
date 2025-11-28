"""Concrete implementations of configuration repositories."""

import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, cast

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

import tomli_w

from claudefig.exceptions import (
    ConfigFileNotFoundError,
    FileOperationError,
    FileWriteError,
)
from claudefig.repositories.base import AbstractConfigRepository
from claudefig.utils.paths import validate_not_symlink


class TomlConfigRepository(AbstractConfigRepository):
    """TOML-based configuration repository.

    Stores configuration data in TOML format with atomic writes and
    backup support. This is the primary storage mechanism for claudefig.

    Features:
    - Atomic writes (temp file + rename)
    - Automatic backup creation
    - Schema version tracking
    - Error recovery
    """

    def __init__(self, config_path: Path):
        """Initialize repository with config file path.

        Args:
            config_path: Path to TOML configuration file.
        """
        self.config_path = config_path.resolve()

    def load(self) -> dict[str, Any]:
        """Load configuration from TOML file.

        Returns:
            Configuration data as nested dictionary.

        Raises:
            ConfigFileNotFoundError: If configuration file doesn't exist.
            ValueError: If TOML is malformed or cannot be parsed.
        """
        if not self.exists():
            raise ConfigFileNotFoundError(str(self.config_path))

        try:
            with open(self.config_path, "rb") as f:
                return cast(dict[str, Any], tomllib.load(f))
        except tomllib.TOMLDecodeError as e:
            raise ValueError(
                f"Invalid TOML in config file {self.config_path}: {e}"
            ) from e

    def save(self, data: dict[str, Any]) -> None:
        """Save configuration to TOML file atomically.

        Uses atomic write pattern (temp file + rename) to prevent corruption
        on crashes or interruptions.

        Args:
            data: Configuration data to persist.

        Raises:
            FileWriteError: If write operation fails.
            ValueError: If data cannot be serialized to TOML.
        """
        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: temp file + rename
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=self.config_path.parent,
                delete=False,
                suffix=".tmp",
            ) as tmp:
                tmp_path = Path(tmp.name)
                tomli_w.dump(data, tmp)

            # Atomic rename (POSIX guarantees atomicity)
            tmp_path.replace(self.config_path)

        except Exception as e:
            # Clean up temp file on error
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
            raise FileWriteError(str(self.config_path), str(e)) from e

    def exists(self) -> bool:
        """Check if configuration file exists.

        Returns:
            True if configuration file exists, False otherwise.
        """
        return self.config_path.exists()

    def get_path(self) -> Path:
        """Get the path to the configuration file.

        Returns:
            Path to the TOML configuration file.
        """
        return self.config_path

    def backup(self, backup_path: Path | None = None) -> Path:
        """Create a backup of the current configuration.

        Args:
            backup_path: Optional path for backup. If None, creates timestamped
                        backup in same directory as config file.

        Returns:
            Path to the created backup file.

        Raises:
            ConfigFileNotFoundError: If no configuration exists to backup.
            FileOperationError: If backup creation fails.
        """
        if not self.exists():
            raise ConfigFileNotFoundError(str(self.config_path))

        if backup_path is None:
            # Generate timestamped backup name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_path.with_suffix(f".{timestamp}.bak")

        try:
            # Security: Reject symlinks
            validate_not_symlink(self.config_path, context="config backup source")
            shutil.copy2(self.config_path, backup_path)
            return backup_path
        except Exception as e:
            raise FileOperationError(f"create backup at {backup_path}", str(e)) from e

    def delete(self) -> None:
        """Delete the configuration file.

        Raises:
            ConfigFileNotFoundError: If configuration doesn't exist.
            FileOperationError: If deletion fails.
        """
        if not self.exists():
            raise ConfigFileNotFoundError(str(self.config_path))

        try:
            self.config_path.unlink()
        except Exception as e:
            raise FileOperationError(f"delete config {self.config_path}", str(e)) from e


class FakeConfigRepository(AbstractConfigRepository):
    """In-memory configuration repository for testing.

    Stores configuration data in memory, simulating file I/O without
    actual filesystem access. Useful for fast, isolated unit tests.

    Example:
        >>> repo = FakeConfigRepository({"version": "1.0"})
        >>> data = repo.load()
        >>> data["version"] = "2.0"
        >>> repo.save(data)
        >>> assert repo.load()["version"] == "2.0"
    """

    def __init__(self, initial_data: dict[str, Any] | None = None):
        """Initialize repository with optional initial data.

        Args:
            initial_data: Initial configuration data. Defaults to empty dict.
        """
        self._data: dict[str, Any] | None = (
            initial_data.copy() if initial_data else None
        )
        self._path = Path("/fake/config.toml")  # Virtual path for testing
        self._backups: list[dict[str, Any]] = []  # Track backups for testing

    def load(self) -> dict[str, Any]:
        """Load configuration from memory.

        Returns:
            Copy of configuration data.

        Raises:
            ConfigFileNotFoundError: If no data has been stored yet.
        """
        if self._data is None:
            raise ConfigFileNotFoundError(str(self._path))

        return self._data.copy()

    def save(self, data: dict[str, Any]) -> None:
        """Save configuration to memory.

        Args:
            data: Configuration data to store.
        """
        self._data = data.copy()

    def exists(self) -> bool:
        """Check if configuration exists in memory.

        Returns:
            True if data has been stored, False otherwise.
        """
        return self._data is not None

    def get_path(self) -> Path:
        """Get the virtual path to the configuration.

        Returns:
            Virtual path (not a real file).
        """
        return self._path

    def backup(self, backup_path: Path | None = None) -> Path:
        """Create a backup in memory.

        Args:
            backup_path: Ignored for fake repository.

        Returns:
            Virtual path to backup.

        Raises:
            ConfigFileNotFoundError: If no data exists to backup.
        """
        if not self.exists():
            raise ConfigFileNotFoundError(str(self._path))

        # Store backup in memory
        self._backups.append(self._data.copy())  # type: ignore

        # Return virtual path
        backup_path = self._path.with_suffix(f".{len(self._backups)}.bak")
        return backup_path

    def delete(self) -> None:
        """Delete the configuration from memory.

        Raises:
            ConfigFileNotFoundError: If no configuration exists.
        """
        if not self.exists():
            raise ConfigFileNotFoundError(str(self._path))

        self._data = None

    def get_backups(self) -> list[dict[str, Any]]:
        """Get all backups (testing utility).

        Returns:
            List of backed up configuration data.
        """
        return self._backups.copy()

    def restore_backup(self, index: int = -1) -> None:
        """Restore from a backup (testing utility).

        Args:
            index: Index of backup to restore. Defaults to most recent (-1).

        Raises:
            ConfigFileNotFoundError: If no backups available.
        """
        if not self._backups:
            raise ConfigFileNotFoundError(str(self._path))

        self._data = self._backups[index].copy()
