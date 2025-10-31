"""Component loading using Chain of Responsibility pattern.

Provides a clean, testable way to load components from multiple sources
with clear priority ordering.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from importlib.resources import files
from pathlib import Path

logger = logging.getLogger(__name__)


class ComponentLoader(ABC):
    """Base class for component loaders using Chain of Responsibility pattern.

    Each loader attempts to find a component. If unsuccessful, it delegates
    to the next loader in the chain.
    """

    def __init__(self, next_loader: ComponentLoader | None = None):
        """Initialize loader with optional next loader in chain.

        Args:
            next_loader: Next loader to try if this one fails.
        """
        self.next_loader = next_loader

    def load(self, preset: str, type: str, name: str) -> Path | None:
        """Attempt to load component, delegating to next loader if not found.

        Args:
            preset: Preset name (e.g., "default")
            type: Component type (e.g., "claude_md")
            name: Component name (e.g., "default")

        Returns:
            Path to component directory if found, None otherwise.
        """
        # Try this loader
        path = self.try_load(preset, type, name)
        if path is not None:
            logger.debug(
                f"Component {type}/{name} loaded from {self.__class__.__name__}"
            )
            return path

        # Delegate to next loader
        if self.next_loader:
            return self.next_loader.load(preset, type, name)

        return None

    @abstractmethod
    def try_load(self, preset: str, type: str, name: str) -> Path | None:
        """Attempt to load component from this loader's source.

        Args:
            preset: Preset name (e.g., "default")
            type: Component type (e.g., "claude_md")
            name: Component name (e.g., "default")

        Returns:
            Path to component directory if found, None otherwise.
        """
        pass


class PresetComponentLoader(ComponentLoader):
    """Loads components from preset-specific directory.

    Checks: src/presets/{preset}/components/{type}/{name}/
    """

    def try_load(self, preset: str, type: str, name: str) -> Path | None:
        """Try to load component from preset-specific directory.

        Args:
            preset: Preset name (e.g., "default")
            type: Component type (e.g., "claude_md")
            name: Component name (e.g., "default")

        Returns:
            Path to component if found, None otherwise.
        """
        try:
            preset_path = files("presets") / preset / "components" / type / name
            preset_path_obj = Path(str(preset_path))
            if preset_path_obj.exists():
                return preset_path_obj
        except (TypeError, FileNotFoundError, AttributeError, OSError) as e:
            logger.debug(f"Component {type}/{name} not found in preset '{preset}': {e}")

        return None


class GlobalComponentLoader(ComponentLoader):
    """Loads components from global component pool.

    Checks: ~/.claudefig/components/{type}/{name}/
    """

    def try_load(self, preset: str, type: str, name: str) -> Path | None:
        """Try to load component from global component pool.

        Args:
            preset: Preset name (not used, but required for interface)
            type: Component type (e.g., "claude_md")
            name: Component name (e.g., "default")

        Returns:
            Path to component if found, None otherwise.
        """
        try:
            from claudefig.user_config import get_components_dir

            global_path = get_components_dir() / type / name
            if global_path.exists():
                return global_path
        except (ImportError, OSError) as e:
            logger.debug(f"Could not access global component pool: {e}")

        return None


def create_component_loader_chain() -> ComponentLoader:
    """Create default component loader chain.

    Priority order:
    1. Preset-specific components (src/presets/{preset}/components/{type}/{name}/)
    2. Global component pool (~/.claudefig/components/{type}/{name}/)

    Returns:
        Head of the loader chain.
    """
    # Build chain in reverse order (last to first)
    global_loader = GlobalComponentLoader(next_loader=None)
    preset_loader = PresetComponentLoader(next_loader=global_loader)

    return preset_loader
