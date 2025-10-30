"""Preset definition loader service.

Handles loading preset definitions from .claudefig.toml files
across different locations (library, user, project).
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from claudefig.models import PresetDefinition
from claudefig.user_config import get_user_config_dir


class PresetDefinitionLoader:
    """Load preset definitions from .claudefig.toml files.

    Supports loading from three locations with priority:
    1. Project (.claudefig/presets/)
    2. User (~/.claudefig/presets/)
    3. Library (src/presets/)
    """

    def __init__(
        self,
        library_presets_path: Path | None = None,
        user_presets_path: Path | None = None,
        project_presets_path: Path | None = None,
    ):
        """Initialize preset loader.

        Args:
            library_presets_path: Path to library presets (src/presets/)
            user_presets_path: Path to user presets (~/.claudefig/presets/)
            project_presets_path: Path to project presets (.claudefig/presets/)
        """
        # Set library path (from package)
        if library_presets_path:
            self.library_presets_path = library_presets_path
        else:
            # Use importlib.resources to access built-in presets
            try:
                presets_root = files("presets")
                self.library_presets_path = Path(str(presets_root))
            except (TypeError, FileNotFoundError, AttributeError, OSError):
                self.library_presets_path = None

        # Set user and project paths
        self.user_presets_path = user_presets_path or (
            get_user_config_dir() / "presets"
        )
        self.project_presets_path = project_presets_path

        # Cache for loaded presets
        self._cache: dict[str, PresetDefinition] = {}

    def _load_from_path(
        self,
        preset_name: str,
        base_path: Path | None,
        location_name: str,
    ) -> PresetDefinition:
        """Load preset from a specific base path.

        Args:
            preset_name: Name of preset to load
            base_path: Base directory containing preset subdirectories
            location_name: Human-readable name for error messages (e.g., "Library", "User")

        Returns:
            PresetDefinition instance

        Raises:
            FileNotFoundError: If base path or preset not found
        """
        if not base_path or not base_path.exists():
            raise FileNotFoundError(f"{location_name} presets path not found")

        preset_path = base_path / preset_name / ".claudefig.toml"
        if not preset_path.exists():
            raise FileNotFoundError(
                f"Preset '{preset_name}' not found in {location_name.lower()} presets"
            )

        return PresetDefinition.from_toml(preset_path)

    def load_from_library(self, preset_name: str) -> PresetDefinition:
        """Load preset definition from library (src/presets/{name}/.claudefig.toml).

        Args:
            preset_name: Name of preset to load

        Returns:
            PresetDefinition instance

        Raises:
            FileNotFoundError: If preset not found in library
        """
        return self._load_from_path(preset_name, self.library_presets_path, "Library")

    def load_from_user(self, preset_name: str) -> PresetDefinition:
        """Load preset from user directory (~/.claudefig/presets/{name}/.claudefig.toml).

        Args:
            preset_name: Name of preset to load

        Returns:
            PresetDefinition instance

        Raises:
            FileNotFoundError: If preset not found in user directory
        """
        return self._load_from_path(preset_name, self.user_presets_path, "User")

    def load_from_project(self, preset_name: str) -> PresetDefinition:
        """Load preset from project (.claudefig/presets/{name}/.claudefig.toml).

        Args:
            preset_name: Name of preset to load

        Returns:
            PresetDefinition instance

        Raises:
            FileNotFoundError: If preset not found in project
        """
        return self._load_from_path(preset_name, self.project_presets_path, "Project")

    def load_preset(self, preset_name: str, use_cache: bool = True) -> PresetDefinition:
        """Load preset with priority: project > user > library.

        Args:
            preset_name: Name of preset to load
            use_cache: Whether to use cached preset if available

        Returns:
            PresetDefinition instance

        Raises:
            FileNotFoundError: If preset not found in any location
        """
        # Check cache first
        if use_cache and preset_name in self._cache:
            return self._cache[preset_name]

        # Try locations in priority order
        loaders = [
            ("Project", self.load_from_project, self.project_presets_path),
            ("User", self.load_from_user, self.user_presets_path),
            ("Library", self.load_from_library, self.library_presets_path),
        ]

        errors = []
        for location_name, loader_func, required_path in loaders:
            # Skip if path is not configured/doesn't exist
            if required_path is None:
                continue

            try:
                preset = loader_func(preset_name)
                self._cache[preset_name] = preset
                return preset
            except FileNotFoundError as e:
                errors.append(f"{location_name}: {e}")

        # Not found in any location
        error_details = "\n  ".join(errors)
        raise FileNotFoundError(
            f"Preset '{preset_name}' not found in any location:\n  {error_details}"
        )

    def _scan_presets_dir(self, path: Path | None) -> set[str]:
        """Scan directory for preset subdirectories.

        Args:
            path: Directory to scan for presets

        Returns:
            Set of preset names found in directory
        """
        if not path or not path.exists():
            return set()

        presets = set()
        try:
            for item in path.iterdir():
                if item.is_dir() and (item / ".claudefig.toml").exists():
                    presets.add(item.name)
        except (OSError, PermissionError):
            pass

        return presets

    def list_available_presets(self) -> list[str]:
        """List all available preset names from all locations.

        Returns:
            Sorted list of unique preset names
        """
        presets = set()
        presets.update(self._scan_presets_dir(self.library_presets_path))
        presets.update(self._scan_presets_dir(self.user_presets_path))
        presets.update(self._scan_presets_dir(self.project_presets_path))
        return sorted(presets)
