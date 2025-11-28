"""Abstract base classes for repository interfaces.

This module defines the contracts for data access layers, enabling
dependency inversion and testability through abstract interfaces.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from claudefig.models import Preset, PresetSource


class AbstractConfigRepository(ABC):
    """Abstract repository for configuration persistence.

    This interface defines the contract for storing and retrieving
    configuration data, abstracting away the underlying storage mechanism
    (TOML files, JSON, databases, etc.).

    Benefits:
    - Enables testing with FakeConfigRepository (no filesystem I/O)
    - Allows swapping storage backends without changing business logic
    - Follows Dependency Inversion Principle (depend on abstraction)
    """

    @abstractmethod
    def load(self) -> dict[str, Any]:
        """Load configuration data from storage.

        Returns:
            Configuration data as nested dictionary.

        Raises:
            ConfigFileNotFoundError: If configuration doesn't exist.
            ValueError: If configuration is malformed or invalid.
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, data: dict[str, Any]) -> None:
        """Save configuration data to storage.

        Args:
            data: Configuration data to persist.

        Raises:
            FileWriteError: If write operation fails.
            ValueError: If data cannot be serialized.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self) -> bool:
        """Check if configuration exists in storage.

        Returns:
            True if configuration exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def get_path(self) -> Path:
        """Get the path to the configuration storage.

        Returns:
            Path to the configuration file or directory.
        """
        raise NotImplementedError

    @abstractmethod
    def backup(self, backup_path: Path | None = None) -> Path:
        """Create a backup of the current configuration.

        Args:
            backup_path: Optional path for backup. If None, generate timestamped backup.

        Returns:
            Path to the created backup file.

        Raises:
            ConfigFileNotFoundError: If no configuration exists to backup.
            FileOperationError: If backup creation fails.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self) -> None:
        """Delete the configuration from storage.

        Raises:
            ConfigFileNotFoundError: If configuration doesn't exist.
            FileOperationError: If deletion fails.
        """
        raise NotImplementedError


class AbstractPresetRepository(ABC):
    """Abstract repository for preset persistence.

    This interface defines the contract for managing preset data across
    multiple sources (built-in, user, project) with consistent CRUD operations.

    The preset system supports three sources with priority:
    1. Project presets (.claude/presets/) - Highest priority
    2. User presets (~/.claudefig/presets/) - Medium priority
    3. Built-in presets (package data) - Lowest priority
    """

    @abstractmethod
    def list_presets(
        self, file_type: str | None = None, source: PresetSource | None = None
    ) -> list[Preset]:
        """List all available presets with optional filtering.

        Args:
            file_type: Filter by file type (e.g., "claude_md", "settings_json").
            source: Filter by preset source (BUILT_IN, USER, PROJECT).

        Returns:
            List of Preset objects matching filters.
        """
        raise NotImplementedError

    @abstractmethod
    def get_preset(self, preset_id: str) -> Preset | None:
        """Retrieve a specific preset by ID.

        Args:
            preset_id: Preset identifier in format "file_type:preset_name".

        Returns:
            Preset object if found, None otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def add_preset(self, preset: Preset, source: PresetSource) -> None:
        """Add a new preset to the specified source.

        Args:
            preset: Preset object to add.
            source: Target source (USER or PROJECT only, not BUILT_IN).

        Raises:
            BuiltInModificationError: If source is BUILT_IN.
            PresetExistsError: If preset already exists.
            FileWriteError: If write operation fails.
        """
        raise NotImplementedError

    @abstractmethod
    def update_preset(self, preset: Preset) -> None:
        """Update an existing preset.

        Args:
            preset: Updated preset object.

        Raises:
            PresetNotFoundError: If preset doesn't exist.
            BuiltInModificationError: If trying to update a BUILT_IN preset.
            FileWriteError: If write operation fails.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_preset(self, preset_id: str) -> None:
        """Delete a preset by ID.

        Args:
            preset_id: Preset identifier to delete.

        Raises:
            PresetNotFoundError: If preset doesn't exist.
            BuiltInModificationError: If trying to delete a BUILT_IN preset.
            FileOperationError: If deletion fails.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, preset_id: str) -> bool:
        """Check if a preset exists.

        Args:
            preset_id: Preset identifier to check.

        Returns:
            True if preset exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def get_template_content(self, preset: Preset) -> str:
        """Load the template file content for a preset.

        Args:
            preset: Preset object with template_path.

        Returns:
            Template content as string.

        Raises:
            TemplateNotFoundError: If template file doesn't exist.
            FileReadError: If read operation fails.
        """
        raise NotImplementedError

    @abstractmethod
    def clear_cache(self) -> None:
        """Clear any internal caches.

        Useful when presets have been modified externally and need to be reloaded.
        """
        raise NotImplementedError
