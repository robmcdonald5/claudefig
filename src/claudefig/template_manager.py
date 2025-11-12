"""File template management for claudefig."""

import logging
from importlib.resources import files
from pathlib import Path

from claudefig.component_loaders import create_component_loader_chain

logger = logging.getLogger(__name__)


class FileTemplateManager:
    """Manages file templates for claudefig.

    This class handles templates for individual files (like CLAUDE.md, .gitignore, etc.),
    as opposed to ConfigTemplateManager which handles entire project configurations.
    """

    def __init__(self, custom_template_dir: Path | None = None):
        """Initialize template manager.

        Args:
            custom_template_dir: Optional path to custom template directory.
                               If None, uses built-in templates.
        """
        self.custom_template_dir = custom_template_dir

    def get_template_dir(self, template_name: str = "default") -> Path:
        """Get path to template directory.

        Args:
            template_name: Name of the template set to use

        Returns:
            Path to template directory.

        Raises:
            FileNotFoundError: If template directory not found.
        """
        # Check custom templates first
        if self.custom_template_dir:
            custom_path = self.custom_template_dir / template_name
            if custom_path.exists():
                return custom_path

        # Fall back to built-in templates
        try:
            # Use importlib.resources to access package data
            template_files = files("presets") / template_name
            return Path(str(template_files))
        except (TypeError, FileNotFoundError) as e:
            raise FileNotFoundError(
                f"Template '{template_name}' not found in built-in templates"
            ) from e

    def list_templates(self) -> list[str]:
        """List available templates.

        Returns:
            List of available template names.
        """
        templates = []

        # List built-in templates
        try:
            template_root = files("presets")
            template_path = Path(str(template_root))
            if template_path.exists() and template_path.is_dir():
                templates.extend(
                    [
                        d.name
                        for d in template_path.iterdir()
                        if d.is_dir() and not d.name.startswith("_")
                    ]
                )
        except (OSError, TypeError, AttributeError) as e:
            logger.debug(f"Could not list built-in templates: {e}")

        # List custom templates
        if self.custom_template_dir and self.custom_template_dir.exists():
            custom_templates = [
                d.name
                for d in self.custom_template_dir.iterdir()
                if d.is_dir() and not d.name.startswith("_")
            ]
            templates.extend([f"{t} (custom)" for t in custom_templates])

        return sorted(templates)

    def get_template_files(self, template_name: str = "default") -> list[Path]:
        """Get list of files in a template.

        Args:
            template_name: Name of the template set

        Returns:
            List of file paths in the template.
        """
        template_dir = self.get_template_dir(template_name)

        if not template_dir.exists():
            return []

        return [
            f
            for f in template_dir.iterdir()
            if f.is_file() and not f.name.startswith("_")
        ]

    def read_template_file(self, template_name: str, filename: str) -> str:
        """Read content of a template file.

        Args:
            template_name: Name of the template set
            filename: Name of the file to read (can include subdirectories)

        Returns:
            Content of the template file.

        Raises:
            FileNotFoundError: If template file not found.
        """
        template_dir = self.get_template_dir(template_name)
        file_path = template_dir / filename

        if file_path.exists():
            return file_path.read_text(encoding="utf-8")

        raise FileNotFoundError(
            f"Template file '{filename}' not found in '{template_name}'"
        )

    def get_component_path(self, preset: str, type: str, name: str) -> Path:
        """Get path to component directory using loader chain.

        Uses Chain of Responsibility pattern with priority order:
        1. Preset-specific components: src/presets/{preset}/components/{type}/{name}/
        2. Global component pool: ~/.claudefig/components/{type}/{name}/

        Args:
            preset: Preset name (e.g., "default")
            type: Component type (e.g., "claude_md")
            name: Component name (e.g., "default")

        Returns:
            Path to component directory

        Raises:
            FileNotFoundError: If component not found
        """
        loader = create_component_loader_chain()
        path = loader.load(preset, type, name)

        if path is None:
            raise FileNotFoundError(
                f"Component {type}/{name} not found in preset '{preset}' or global pool"
            )

        return path

    def list_components(self, preset: str, type: str | None = None) -> list[dict]:
        """List available components from preset and global pool.

        Shows components from preset-specific folder and global pool,
        with (p) and (g) suffixes to distinguish them.

        Args:
            preset: Current preset name
            type: Optional component type filter (e.g., "claude_md")

        Returns:
            List of dicts with component info:
            - name: Component name
            - type: Component type
            - source: 'preset' or 'global'
            - display_name: Name with suffix (e.g., "default (p)")
            - path: Full path to component
        """
        components = []

        # Collect preset-specific components
        try:
            preset_components_dir = files("presets") / preset / "components"
            preset_components_path = Path(str(preset_components_dir))

            if preset_components_path.exists():
                # If type specified, only scan that type
                if type:
                    type_dirs = (
                        [preset_components_path / type]
                        if (preset_components_path / type).exists()
                        else []
                    )
                else:
                    # Scan all type directories
                    type_dirs = [
                        d for d in preset_components_path.iterdir() if d.is_dir()
                    ]

                for type_dir in type_dirs:
                    comp_type = type_dir.name
                    for comp_dir in type_dir.iterdir():
                        if comp_dir.is_dir():
                            comp_name = comp_dir.name
                            components.append(
                                {
                                    "name": comp_name,
                                    "type": comp_type,
                                    "source": "preset",
                                    "display_name": self.get_component_display_name(
                                        comp_name, "preset"
                                    ),
                                    "path": comp_dir,
                                }
                            )
        except (TypeError, AttributeError, OSError) as e:
            logger.debug(f"Could not list preset components for '{preset}': {e}")

        # Collect global components
        try:
            from claudefig.user_config import get_components_dir

            global_components_dir = get_components_dir()

            if global_components_dir.exists():
                # If type specified, only scan that type
                if type:
                    type_dirs = (
                        [global_components_dir / type]
                        if (global_components_dir / type).exists()
                        else []
                    )
                else:
                    # Scan all type directories
                    type_dirs = [
                        d
                        for d in global_components_dir.iterdir()
                        if d.is_dir() and not d.name.startswith(".")
                    ]

                for type_dir in type_dirs:
                    comp_type = type_dir.name
                    for comp_dir in type_dir.iterdir():
                        if comp_dir.is_dir():
                            comp_name = comp_dir.name
                            components.append(
                                {
                                    "name": comp_name,
                                    "type": comp_type,
                                    "source": "global",
                                    "display_name": self.get_component_display_name(
                                        comp_name, "global"
                                    ),
                                    "path": comp_dir,
                                }
                            )
        except (ImportError, OSError) as e:
            logger.debug(f"Could not list global components: {e}")

        # Sort by type, then name
        components.sort(key=lambda c: (c["type"], c["name"]))

        return components

    def get_component_display_name(self, name: str, source: str) -> str:
        """Get display name with source suffix.

        Args:
            name: Component name
            source: 'preset' or 'global'

        Returns:
            Display name with suffix (e.g., "default (p)" or "custom (g)")
        """
        suffix = "(p)" if source == "preset" else "(g)"
        return f"{name} {suffix}"
