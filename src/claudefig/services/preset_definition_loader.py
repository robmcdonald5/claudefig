"""Preset definition loader service.

Handles loading preset definitions from claudefig.toml files
across different locations (library, user, project).

This module uses a functional design with explicit parameters.
Cache can be passed explicitly or a module-level default is used.
"""

from __future__ import annotations

import contextlib
from importlib.resources import files
from pathlib import Path

from claudefig.models import PresetDefinition
from claudefig.user_config import get_user_config_dir

# Module-level cache (used when no explicit cache is passed)
_default_cache: dict[str, PresetDefinition] = {}


def get_library_presets_path() -> Path | None:
    """Get the path to built-in library presets.

    Returns:
        Path to library presets, or None if not available.
    """
    try:
        presets_root = files("presets")
        return Path(str(presets_root))
    except (TypeError, FileNotFoundError, AttributeError, OSError):
        return None


def get_user_presets_path() -> Path:
    """Get the path to user presets directory.

    Returns:
        Path to user presets (~/.claudefig/presets/).
    """
    return get_user_config_dir() / "presets"


def _load_from_path(
    preset_name: str,
    base_path: Path | None,
    location_name: str,
) -> PresetDefinition:
    """Load preset from a specific base path.

    Args:
        preset_name: Name of preset to load.
        base_path: Base directory containing preset subdirectories.
        location_name: Human-readable name for error messages.

    Returns:
        PresetDefinition instance.

    Raises:
        FileNotFoundError: If base path or preset not found.
    """
    if not base_path or not base_path.exists():
        raise FileNotFoundError(f"{location_name} presets path not found")

    preset_path = base_path / preset_name / "claudefig.toml"
    if not preset_path.exists():
        raise FileNotFoundError(
            f"Preset '{preset_name}' not found in {location_name.lower()} presets"
        )

    return PresetDefinition.from_toml(preset_path)


def load_from_library(
    preset_name: str,
    library_path: Path | None = None,
) -> PresetDefinition:
    """Load preset definition from library (src/presets/{name}/claudefig.toml).

    Args:
        preset_name: Name of preset to load.
        library_path: Optional custom library path. Defaults to package presets.

    Returns:
        PresetDefinition instance.

    Raises:
        FileNotFoundError: If preset not found in library.
    """
    path = library_path if library_path is not None else get_library_presets_path()
    return _load_from_path(preset_name, path, "Library")


def load_from_user(
    preset_name: str,
    user_path: Path | None = None,
) -> PresetDefinition:
    """Load preset from user directory (~/.claudefig/presets/{name}/claudefig.toml).

    Args:
        preset_name: Name of preset to load.
        user_path: Optional custom user path. Defaults to ~/.claudefig/presets/.

    Returns:
        PresetDefinition instance.

    Raises:
        FileNotFoundError: If preset not found in user directory.
    """
    path = user_path if user_path is not None else get_user_presets_path()
    return _load_from_path(preset_name, path, "User")


def load_from_project(
    preset_name: str,
    project_path: Path | None = None,
) -> PresetDefinition:
    """Load preset from project (.claudefig/presets/{name}/claudefig.toml).

    Args:
        preset_name: Name of preset to load.
        project_path: Path to project presets directory.

    Returns:
        PresetDefinition instance.

    Raises:
        FileNotFoundError: If preset not found in project or project_path is None.
    """
    return _load_from_path(preset_name, project_path, "Project")


def load_preset(
    preset_name: str,
    *,
    project_path: Path | None = None,
    user_path: Path | None = None,
    library_path: Path | None = None,
    use_cache: bool = True,
    cache: dict[str, PresetDefinition] | None = None,
) -> PresetDefinition:
    """Load preset with priority: project > user > library.

    Args:
        preset_name: Name of preset to load.
        project_path: Optional project presets path.
        user_path: Optional user presets path (defaults to ~/.claudefig/presets/).
        library_path: Optional library presets path (defaults to package presets).
        use_cache: Whether to use cached preset if available.
        cache: Optional explicit cache dict. If None, uses module-level cache.

    Returns:
        PresetDefinition instance.

    Raises:
        FileNotFoundError: If preset not found in any location.
    """
    # Use explicit cache or module default
    active_cache = cache if cache is not None else _default_cache

    # Check cache first
    if use_cache and preset_name in active_cache:
        return active_cache[preset_name]

    # Resolve paths with defaults
    resolved_user_path = user_path if user_path is not None else get_user_presets_path()
    resolved_library_path = (
        library_path if library_path is not None else get_library_presets_path()
    )

    # Try locations in priority order
    loaders: list[tuple[str, Path | None]] = [
        ("Project", project_path),
        ("User", resolved_user_path),
        ("Library", resolved_library_path),
    ]

    errors = []
    for location_name, path in loaders:
        # Skip if path is not configured/doesn't exist
        if path is None:
            continue

        try:
            preset = _load_from_path(preset_name, path, location_name)
            active_cache[preset_name] = preset
            return preset
        except FileNotFoundError as e:
            errors.append(f"{location_name}: {e}")

    # Not found in any location
    error_details = "\n  ".join(errors)
    raise FileNotFoundError(
        f"Preset '{preset_name}' not found in any location:\n  {error_details}"
    )


def _scan_presets_dir(path: Path | None) -> set[str]:
    """Scan directory for preset subdirectories.

    Args:
        path: Directory to scan for presets.

    Returns:
        Set of preset names found in directory.
    """
    if not path or not path.exists():
        return set()

    presets = set()
    with contextlib.suppress(OSError, PermissionError):
        for item in path.iterdir():
            if item.is_dir() and (item / "claudefig.toml").exists():
                presets.add(item.name)

    return presets


def list_available_presets(
    *,
    project_path: Path | None = None,
    user_path: Path | None = None,
    library_path: Path | None = None,
) -> list[str]:
    """List all available preset names from all locations.

    Args:
        project_path: Optional project presets path.
        user_path: Optional user presets path (defaults to ~/.claudefig/presets/).
        library_path: Optional library presets path (defaults to package presets).

    Returns:
        Sorted list of unique preset names.
    """
    # Resolve paths with defaults
    resolved_user_path = user_path if user_path is not None else get_user_presets_path()
    resolved_library_path = (
        library_path if library_path is not None else get_library_presets_path()
    )

    presets: set[str] = set()
    presets.update(_scan_presets_dir(resolved_library_path))
    presets.update(_scan_presets_dir(resolved_user_path))
    presets.update(_scan_presets_dir(project_path))
    return sorted(presets)


def clear_cache(cache: dict[str, PresetDefinition] | None = None) -> None:
    """Clear the preset definition cache.

    Args:
        cache: Optional explicit cache to clear. If None, clears module-level cache.
    """
    if cache is None:
        _default_cache.clear()
    else:
        cache.clear()


# Backward compatibility: Keep class available but deprecated
class PresetDefinitionLoader:
    """Load preset definitions from claudefig.toml files.

    .. deprecated::
        Use the functional API instead (load_preset, list_available_presets, etc.).
        This class is provided for backward compatibility only.
    """

    def __init__(
        self,
        library_presets_path: Path | None = None,
        user_presets_path: Path | None = None,
        project_presets_path: Path | None = None,
    ):
        """Initialize preset loader."""
        self.library_presets_path = (
            library_presets_path
            if library_presets_path is not None
            else get_library_presets_path()
        )
        self.user_presets_path = (
            user_presets_path
            if user_presets_path is not None
            else get_user_presets_path()
        )
        self.project_presets_path = project_presets_path
        self._cache: dict[str, PresetDefinition] = {}

    def load_from_library(self, preset_name: str) -> PresetDefinition:
        """Load preset from library."""
        return load_from_library(preset_name, self.library_presets_path)

    def load_from_user(self, preset_name: str) -> PresetDefinition:
        """Load preset from user directory."""
        return load_from_user(preset_name, self.user_presets_path)

    def load_from_project(self, preset_name: str) -> PresetDefinition:
        """Load preset from project."""
        return load_from_project(preset_name, self.project_presets_path)

    def load_preset(self, preset_name: str, use_cache: bool = True) -> PresetDefinition:
        """Load preset with priority order."""
        return load_preset(
            preset_name,
            project_path=self.project_presets_path,
            user_path=self.user_presets_path,
            library_path=self.library_presets_path,
            use_cache=use_cache,
            cache=self._cache,
        )

    def list_available_presets(self) -> list[str]:
        """List all available preset names."""
        return list_available_presets(
            project_path=self.project_presets_path,
            user_path=self.user_presets_path,
            library_path=self.library_presets_path,
        )
