"""Template management for claudefig."""

from importlib.resources import files
from pathlib import Path
from typing import Optional


class TemplateManager:
    """Manages templates for claudefig."""

    def __init__(self, custom_template_dir: Optional[Path] = None):
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
            template_files = files("templates") / template_name
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
            template_root = files("templates")
            template_path = Path(str(template_root))
            if template_path.exists() and template_path.is_dir():
                templates.extend(
                    [
                        d.name
                        for d in template_path.iterdir()
                        if d.is_dir() and not d.name.startswith("_")
                    ]
                )
        except Exception:
            pass

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
            filename: Name of the file to read

        Returns:
            Content of the template file.

        Raises:
            FileNotFoundError: If template file not found.
        """
        template_dir = self.get_template_dir(template_name)
        file_path = template_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Template file '{filename}' not found in '{template_name}'"
            )

        return file_path.read_text(encoding="utf-8")
