"""Template rendering engine using Jinja2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment


class ComponentRenderer:
    """Renders component templates with Jinja2."""

    def __init__(self):
        """Initialize the component renderer."""
        # Create a base Jinja2 environment
        self.env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render_file(self, file_path: Path, variables: dict[str, Any]) -> str:
        """Render a component file with variables.

        Args:
            file_path: Path to the component content file.
            variables: Dictionary of variables to substitute.

        Returns:
            Rendered content as string.

        Raises:
            FileNotFoundError: If file doesn't exist.
            Exception: If rendering fails.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Component file not found: {file_path}")

        try:
            # Read the template content
            template_content = file_path.read_text(encoding="utf-8")

            # Create template and render
            template = self.env.from_string(template_content)
            rendered = template.render(**variables)

            return rendered

        except Exception as e:
            raise Exception(f"Error rendering {file_path}: {e}")

    def render_string(self, content: str, variables: dict[str, Any]) -> str:
        """Render a template string with variables.

        Args:
            content: Template content as string.
            variables: Dictionary of variables to substitute.

        Returns:
            Rendered content as string.
        """
        template = self.env.from_string(content)
        return template.render(**variables)

    def render_component_files(
        self, file_paths: list[Path], variables: dict[str, Any]
    ) -> str:
        """Render multiple component files and concatenate.

        Args:
            file_paths: List of paths to component content files.
            variables: Dictionary of variables to substitute.

        Returns:
            Concatenated rendered content.
        """
        rendered_parts = []

        for file_path in file_paths:
            try:
                rendered = self.render_file(file_path, variables)
                rendered_parts.append(rendered)
            except Exception as e:
                print(f"Warning: Skipping {file_path}: {e}")

        # Join with double newlines between components
        return "\n\n".join(rendered_parts)


class MarkdownComposer:
    """Composes markdown files from multiple component sections."""

    def __init__(self):
        """Initialize markdown composer."""
        self.sections: dict[str, dict[str, Any]] = {}

    def add_section(self, section_name: str, content: str, priority: int = 100):
        """Add or update a section.

        Args:
            section_name: Name of the section (e.g., "Python Coding Standards").
            content: Rendered content for this section.
            priority: Priority for ordering (lower = earlier).
        """
        # Store with priority for later sorting
        if section_name not in self.sections:
            self.sections[section_name] = {
                "content": content,
                "priority": priority,
            }
        else:
            # If section already exists, use lower priority (inserted earlier)
            existing_priority = self.sections[section_name]["priority"]
            if priority < existing_priority:
                self.sections[section_name] = {
                    "content": content,
                    "priority": priority,
                }

    def compose(self, include_toc: bool = False) -> str:
        """Compose all sections into a single markdown document.

        Args:
            include_toc: Whether to include a table of contents.

        Returns:
            Complete markdown document as string.
        """
        if not self.sections:
            return ""

        # Sort sections by priority
        sorted_sections = sorted(self.sections.items(), key=lambda x: x[1]["priority"])

        # Build the document
        parts = []

        # Optional TOC
        if include_toc:
            toc = self._generate_toc(sorted_sections)
            parts.append(toc)
            parts.append("---\n")

        # Add each section
        for section_name, section_data in sorted_sections:
            content = section_data["content"]
            parts.append(content)

        # Join with double newlines between sections
        return "\n\n".join(parts)

    def _generate_toc(self, sorted_sections: list) -> str:
        """Generate a table of contents.

        Args:
            sorted_sections: List of (section_name, section_data) tuples.

        Returns:
            Table of contents as markdown string.
        """
        toc_lines = ["# Table of Contents\n"]

        for section_name, _ in sorted_sections:
            # Convert section name to anchor link
            anchor = section_name.lower().replace(" ", "-")
            toc_lines.append(f"- [{section_name}](#{anchor})")

        return "\n".join(toc_lines)

    def get_section_content(self, section_name: str) -> str:
        """Get the content of a specific section.

        Args:
            section_name: Name of the section.

        Returns:
            Section content, or empty string if not found.
        """
        if section_name in self.sections:
            return self.sections[section_name]["content"]
        return ""

    def has_section(self, section_name: str) -> bool:
        """Check if a section exists.

        Args:
            section_name: Name of the section.

        Returns:
            True if section exists, False otherwise.
        """
        return section_name in self.sections

    def clear(self):
        """Clear all sections."""
        self.sections.clear()
