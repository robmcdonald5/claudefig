"""Concrete implementations of preset repositories."""

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from claudefig.exceptions import (
    BuiltInModificationError,
    FileOperationError,
    FileReadError,
    FileWriteError,
    InvalidPresetNameError,
    PresetExistsError,
    PresetNotFoundError,
    TemplateNotFoundError,
)
from claudefig.models import FileType, Preset, PresetSource
from claudefig.repositories.base import AbstractPresetRepository


class TomlPresetRepository(AbstractPresetRepository):
    """TOML-based preset repository supporting multi-source loading.

    This repository manages presets from three sources with priority:
    1. Built-in presets (programmatically defined)
    2. User presets (~/.claudefig/presets/)
    3. Project presets (.claudefig/presets/)

    Features:
    - Multi-source preset discovery
    - TOML persistence for user/project presets
    - Caching for performance
    - Circular dependency detection
    """

    def __init__(
        self,
        user_presets_dir: Path | None = None,
        project_presets_dir: Path | None = None,
    ):
        """Initialize repository with preset directories.

        Args:
            user_presets_dir: Path to user presets. Defaults to ~/.claudefig/presets/
            project_presets_dir: Path to project presets. Defaults to .claudefig/presets/
        """
        self.user_presets_dir = user_presets_dir or (
            Path.home() / ".claudefig" / "presets"
        )
        self.project_presets_dir = project_presets_dir or (
            Path.cwd() / ".claudefig" / "presets"
        )

        # Cache for loaded presets
        self._preset_cache: dict[str, Preset] = {}
        self._cache_loaded = False
        self._load_errors: list[str] = []  # Track errors during preset loading

    def list_presets(
        self, file_type: str | None = None, source: PresetSource | None = None
    ) -> list[Preset]:
        """List all available presets with optional filtering.

        Args:
            file_type: Filter by file type (e.g., "claude_md").
            source: Filter by preset source (BUILT_IN, USER, PROJECT).

        Returns:
            List of Preset objects matching filters, sorted by type and name.
        """
        self._ensure_cache_loaded()

        presets = list(self._preset_cache.values())

        # Apply filters
        if file_type:
            presets = [p for p in presets if p.type.value == file_type]
        if source:
            presets = [p for p in presets if p.source == source]

        # Sort by file type, then name
        presets.sort(key=lambda p: (p.type.value, p.name))

        return presets

    def get_preset(self, preset_id: str) -> Preset | None:
        """Retrieve a specific preset by ID.

        Args:
            preset_id: Preset identifier in format "file_type:preset_name".

        Returns:
            Preset object if found, None otherwise.

        Raises:
            InvalidPresetNameError: If preset ID contains dangerous characters.
        """
        self._validate_preset_id(preset_id)
        self._ensure_cache_loaded()
        return self._preset_cache.get(preset_id)

    def add_preset(self, preset: Preset, source: PresetSource) -> None:
        """Add a new preset to the specified source.

        Args:
            preset: Preset object to add.
            source: Target source (USER or PROJECT only).

        Raises:
            InvalidPresetNameError: If preset ID contains dangerous characters.
            BuiltInModificationError: If source is BUILT_IN.
            PresetExistsError: If preset already exists.
            FileWriteError: If write operation fails.
        """
        self._validate_preset_id(preset.id)

        if source == PresetSource.BUILT_IN:
            raise BuiltInModificationError("preset", "add")

        self._ensure_cache_loaded()

        if preset.id in self._preset_cache:
            raise PresetExistsError(preset.id)

        # Determine storage directory
        storage_dir = (
            self.user_presets_dir
            if source == PresetSource.USER
            else self.project_presets_dir
        )
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Save preset metadata to TOML
        preset_file = storage_dir / f"{preset.id.replace(':', '_')}.toml"
        try:
            with open(preset_file, "wb") as f:
                tomli_w.dump({"preset": preset.to_dict()}, f)
        except Exception as e:
            raise FileWriteError(str(preset_file), str(e)) from e

        # Update cache
        preset.source = source
        self._preset_cache[preset.id] = preset

    def update_preset(self, preset: Preset) -> None:
        """Update an existing preset.

        Args:
            preset: Updated preset object.

        Raises:
            InvalidPresetNameError: If preset ID contains dangerous characters.
            PresetNotFoundError: If preset doesn't exist.
            BuiltInModificationError: If trying to update a BUILT_IN preset.
            FileWriteError: If write operation fails.
        """
        self._validate_preset_id(preset.id)
        self._ensure_cache_loaded()

        if preset.id not in self._preset_cache:
            raise PresetNotFoundError(preset.id)

        existing = self._preset_cache[preset.id]
        if existing.source == PresetSource.BUILT_IN:
            raise BuiltInModificationError("preset", "update")

        # Determine storage directory
        storage_dir = (
            self.user_presets_dir
            if existing.source == PresetSource.USER
            else self.project_presets_dir
        )

        preset_file = storage_dir / f"{preset.id.replace(':', '_')}.toml"
        if not preset_file.exists():
            raise PresetNotFoundError(preset.id)

        # Save updated preset
        try:
            with open(preset_file, "wb") as f:
                tomli_w.dump({"preset": preset.to_dict()}, f)
        except Exception as e:
            raise FileWriteError(str(preset_file), str(e)) from e

        # Update cache
        self._preset_cache[preset.id] = preset

    def delete_preset(self, preset_id: str) -> None:
        """Delete a preset by ID.

        Args:
            preset_id: Preset identifier to delete.

        Raises:
            InvalidPresetNameError: If preset ID contains dangerous characters.
            PresetNotFoundError: If preset doesn't exist.
            BuiltInModificationError: If trying to delete a BUILT_IN preset.
            FileOperationError: If deletion fails.
        """
        self._validate_preset_id(preset_id)
        self._ensure_cache_loaded()

        preset = self._preset_cache.get(preset_id)
        if not preset:
            raise PresetNotFoundError(preset_id)

        if preset.source == PresetSource.BUILT_IN:
            raise BuiltInModificationError("preset", "delete")

        # Determine storage directory
        storage_dir = (
            self.user_presets_dir
            if preset.source == PresetSource.USER
            else self.project_presets_dir
        )

        preset_file = storage_dir / f"{preset_id.replace(':', '_')}.toml"
        if preset_file.exists():
            try:
                preset_file.unlink()
            except Exception as e:
                raise FileOperationError(
                    f"delete preset file {preset_file}", str(e)
                ) from e

        # Remove from cache
        del self._preset_cache[preset_id]

    def exists(self, preset_id: str) -> bool:
        """Check if a preset exists.

        Args:
            preset_id: Preset identifier to check.

        Returns:
            True if preset exists, False otherwise.
        """
        self._ensure_cache_loaded()
        return preset_id in self._preset_cache

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
        # If preset has explicit template_path, use it
        if preset.template_path and preset.template_path.exists():
            try:
                return preset.template_path.read_text(encoding="utf-8")
            except Exception as e:
                raise FileReadError(str(preset.template_path), str(e)) from e

        # Otherwise, resolve from preset source using component system
        component_path = self._resolve_component_path(preset)

        if not component_path or not component_path.exists():
            raise TemplateNotFoundError(
                preset.id,
                f"Component file not found for preset '{preset.id}' at {component_path}",
            )

        try:
            return component_path.read_text(encoding="utf-8")
        except Exception as e:
            raise FileReadError(str(component_path), str(e)) from e

    def _resolve_component_path(self, preset: Preset) -> Path | None:
        """Resolve the component file path for a preset.

        Args:
            preset: Preset to resolve component path for

        Returns:
            Path to component file, or None if not found
        """
        # Extract component name from preset ID (e.g., "gitignore:default" -> "default")
        component_name = preset.id.split(":")[-1] if ":" in preset.id else preset.name

        # Determine component file name based on file type
        file_name = self._get_component_filename(preset.type)

        if preset.source == PresetSource.BUILT_IN:
            return self._resolve_builtin_component(
                preset.type, component_name, file_name
            )
        elif preset.source == PresetSource.USER:
            return self._resolve_user_component(preset.type, component_name, file_name)
        elif preset.source == PresetSource.PROJECT:
            return self._resolve_project_component(
                preset.type, component_name, file_name
            )

        return None

    def _get_component_filename(self, file_type: FileType) -> str:
        """Get the expected filename for a component type.

        Args:
            file_type: Type of file/component

        Returns:
            Expected filename for that component type
        """
        filename_map = {
            FileType.CLAUDE_MD: "CLAUDE.md",
            FileType.GITIGNORE: ".gitignore",
            FileType.SETTINGS_JSON: "settings.json",
            FileType.SETTINGS_LOCAL_JSON: "settings.local.json",
            FileType.STATUSLINE: "statusline.sh",
            FileType.COMMANDS: "example.md",  # Commands are usually example files
            FileType.AGENTS: "example.md",
            FileType.HOOKS: "example.py",
            FileType.OUTPUT_STYLES: "example.md",
            FileType.MCP: "config.json",  # MCP servers use config.json
            FileType.PLUGINS: "plugin.json",
            FileType.SKILLS: "skill.md",
        }
        return filename_map.get(file_type, "template.txt")

    def _resolve_builtin_component(
        self, file_type: FileType, component_name: str, file_name: str
    ) -> Path | None:
        """Resolve component path from built-in presets.

        Args:
            file_type: Type of file/component
            component_name: Name of the component variant
            file_name: Expected filename

        Returns:
            Path to component file, or None if not found
        """
        from importlib.resources import files

        try:
            # Backward compatibility aliases
            alias_map = {
                (FileType.MCP, "default"): "stdio-local",
            }

            # Check if this is an aliased component
            alias_key = (file_type, component_name)
            if alias_key in alias_map:
                component_name = alias_map[alias_key]

            # Path: src/presets/default/components/{file_type}/{component_name}/{file_name}
            builtin_source = files("presets").joinpath("default")

            # Get the actual path
            if hasattr(builtin_source, "__fspath__"):
                source_path = Path(builtin_source)  # type: ignore[arg-type]
            else:
                # For Python 3.10+, extract path as string
                source_path = Path(str(builtin_source))

            component_path = (
                source_path
                / "components"
                / file_type.value
                / component_name
                / file_name
            )

            return component_path if component_path.exists() else None

        except (ImportError, AttributeError, FileNotFoundError, TypeError):
            return None

    def _resolve_user_component(
        self, file_type: FileType, component_name: str, file_name: str
    ) -> Path | None:
        """Resolve component path from user presets.

        Args:
            file_type: Type of file/component
            component_name: Name of the component variant
            file_name: Expected filename

        Returns:
            Path to component file, or None if not found
        """
        # Path: ~/.claudefig/presets/default/components/{file_type}/{component_name}/{file_name}
        component_path = (
            self.user_presets_dir
            / "default"
            / "components"
            / file_type.value
            / component_name
            / file_name
        )

        return component_path if component_path.exists() else None

    def _resolve_project_component(
        self, file_type: FileType, component_name: str, file_name: str
    ) -> Path | None:
        """Resolve component path from project presets.

        Args:
            file_type: Type of file/component
            component_name: Name of the component variant
            file_name: Expected filename

        Returns:
            Path to component file, or None if not found
        """
        # Path: .claudefig/presets/default/components/{file_type}/{component_name}/{file_name}
        component_path = (
            self.project_presets_dir
            / "default"
            / "components"
            / file_type.value
            / component_name
            / file_name
        )

        return component_path if component_path.exists() else None

    def clear_cache(self) -> None:
        """Clear the internal preset cache.

        Useful when presets have been modified externally and need to be reloaded.
        """
        self._preset_cache.clear()
        self._cache_loaded = False
        self._load_errors.clear()

    def get_load_errors(self) -> list[str]:
        """Get any errors that occurred during preset loading.

        Returns:
            List of error messages from preset loading failures.
        """
        self._ensure_cache_loaded()
        return self._load_errors.copy()

    def _ensure_cache_loaded(self) -> None:
        """Ensure presets are loaded into cache."""
        if not self._cache_loaded:
            self._load_all_presets()

    def _validate_preset_id(self, preset_id: str) -> None:
        """Validate preset ID doesn't contain path traversal characters.

        Args:
            preset_id: Preset identifier to validate.

        Raises:
            InvalidPresetNameError: If preset ID contains dangerous characters.
        """
        dangerous_patterns = ["/", "\\", "..", "\0"]
        if any(pattern in preset_id for pattern in dangerous_patterns):
            raise InvalidPresetNameError(
                preset_id,
                "Preset ID cannot contain path separators or traversal sequences",
            )

    def _load_all_presets(self) -> None:
        """Load presets from all sources into cache."""
        # Built-in presets are loaded first (lowest priority)
        # User presets can override built-in
        # Project presets can override user and built-in

        # Load built-in presets
        self._load_builtin_presets()

        # Load user presets
        if self.user_presets_dir.exists():
            self._load_from_directory(self.user_presets_dir, PresetSource.USER)

        # Load project presets (highest priority)
        if self.project_presets_dir.exists():
            self._load_from_directory(self.project_presets_dir, PresetSource.PROJECT)

        self._cache_loaded = True

    def _load_builtin_presets(self) -> None:
        """Load built-in presets from package data TOML file."""
        from importlib.resources import files

        try:
            builtin_file = files("presets").joinpath("builtin_presets.toml")
            with builtin_file.open("rb") as f:
                data = tomllib.load(f)

            for preset_data in data.get("presets", []):
                # Validate required keys
                required_keys = ["id", "type", "name"]
                if not all(key in preset_data for key in required_keys):
                    continue

                preset = Preset.from_dict(preset_data)
                preset.source = PresetSource.BUILT_IN
                self._preset_cache[preset.id] = preset

        except (ImportError, AttributeError, FileNotFoundError, TypeError) as e:
            self._load_errors.append(f"Failed to load built-in presets: {e}")

    def _load_from_directory(self, directory: Path, source: PresetSource) -> None:
        """Load all preset TOML files from a directory.

        Args:
            directory: Directory containing preset TOML files.
            source: Source to assign to loaded presets.
        """
        for preset_file in directory.glob("*.toml"):
            try:
                with open(preset_file, "rb") as f:
                    data = tomllib.load(f)

                # Skip files without a [preset] section (e.g., ConfigTemplateManager files)
                if "preset" not in data:
                    continue

                preset_data = data.get("preset", {})

                # Validate required keys before deserialization
                required_keys = ["id", "type", "name"]
                if not all(key in preset_data for key in required_keys):
                    error_msg = f"Missing required keys in {preset_file}"
                    self._load_errors.append(error_msg)
                    continue

                preset = Preset.from_dict(preset_data)
                preset.source = source

                # Add to cache (overwrites if already exists = priority)
                self._preset_cache[preset.id] = preset

            except OSError as e:
                # File system errors
                error_msg = f"Failed to read preset file {preset_file}: {e}"
                self._load_errors.append(error_msg)
            except (KeyError, ValueError, TypeError) as e:
                # Invalid preset data
                error_msg = f"Invalid preset data in {preset_file}: {e}"
                self._load_errors.append(error_msg)
            except Exception as e:
                # Unexpected errors
                error_msg = (
                    f"Unexpected error loading preset from {preset_file}: "
                    f"{type(e).__name__}: {e}"
                )
                self._load_errors.append(error_msg)


class FakePresetRepository(AbstractPresetRepository):
    """In-memory preset repository for testing.

    Stores presets in memory without filesystem access.
    Useful for fast, isolated unit tests.
    """

    def __init__(self, initial_presets: list[Preset] | None = None):
        """Initialize repository with optional initial presets.

        Args:
            initial_presets: List of presets to pre-populate. Defaults to empty.
        """
        self._presets: dict[str, Preset] = {}
        if initial_presets:
            for preset in initial_presets:
                self._presets[preset.id] = preset

    def list_presets(
        self, file_type: str | None = None, source: PresetSource | None = None
    ) -> list[Preset]:
        """List all available presets with optional filtering."""
        presets = list(self._presets.values())

        if file_type:
            presets = [p for p in presets if p.type.value == file_type]
        if source:
            presets = [p for p in presets if p.source == source]

        presets.sort(key=lambda p: (p.type.value, p.name))
        return presets

    def get_preset(self, preset_id: str) -> Preset | None:
        """Retrieve a specific preset by ID."""
        return self._presets.get(preset_id)

    def add_preset(self, preset: Preset, source: PresetSource) -> None:
        """Add a new preset to memory."""
        if source == PresetSource.BUILT_IN:
            raise BuiltInModificationError(preset.id, "add")

        if preset.id in self._presets:
            raise PresetExistsError(preset.id)

        preset.source = source
        self._presets[preset.id] = preset

    def update_preset(self, preset: Preset) -> None:
        """Update an existing preset in memory."""
        if preset.id not in self._presets:
            raise PresetNotFoundError(preset.id)

        existing = self._presets[preset.id]
        if existing.source == PresetSource.BUILT_IN:
            raise BuiltInModificationError(preset.id, "update")

        self._presets[preset.id] = preset

    def delete_preset(self, preset_id: str) -> None:
        """Delete a preset from memory."""
        if preset_id not in self._presets:
            raise PresetNotFoundError(preset_id)

        preset = self._presets[preset_id]
        if preset.source == PresetSource.BUILT_IN:
            raise BuiltInModificationError(preset_id, "delete")

        del self._presets[preset_id]

    def exists(self, preset_id: str) -> bool:
        """Check if a preset exists in memory."""
        return preset_id in self._presets

    def get_template_content(self, preset: Preset) -> str:
        """Return mock template content for testing."""
        return f"# Mock template for {preset.id}\n{{variable}}"

    def clear_cache(self) -> None:
        """Clear all presets from memory."""
        self._presets.clear()
