"""High-level component composition orchestrator."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from claudefig.component import ComponentLoader
from claudefig.renderer import ComponentRenderer, MarkdownComposer

console = Console()


class ComponentComposer:
    """Orchestrates the entire component → file generation workflow."""

    def __init__(self, component_base_dir: Path):
        """Initialize the component composer.

        Args:
            component_base_dir: Base directory containing components (e.g., ~/.claudefig/components/).
        """
        self.loader = ComponentLoader(component_base_dir)
        self.renderer = ComponentRenderer()

    def compose_claude_md(
        self,
        component_paths: List[str],
        variables: Optional[Dict[str, Any]] = None,
        include_toc: bool = False,
    ) -> str:
        """Compose CLAUDE.md from selected components.

        Args:
            component_paths: List of component paths to include (e.g., ["languages/python"]).
            variables: Dictionary of variables to pass to component templates.
            include_toc: Whether to include a table of contents.

        Returns:
            Composed CLAUDE.md content as string.

        Raises:
            ValueError: If component dependencies cannot be resolved or conflicts exist.
        """
        if variables is None:
            variables = {}

        # Step 1: Resolve dependencies
        try:
            resolved_components = self.loader.resolve_dependencies(component_paths)
        except ValueError as e:
            console.print(f"[red]Error resolving dependencies:[/red] {e}")
            raise

        if not resolved_components:
            console.print("[yellow]No components selected[/yellow]")
            return ""

        # Step 2: Render each component and add to composer
        composer = MarkdownComposer()

        for component in resolved_components:
            # Get component variables (merge defaults with provided variables)
            component_vars = self._merge_variables(component.variables, variables)

            # Render all CLAUDE.md files for this component
            file_paths = component.get_file_paths("claude_md")
            if file_paths:
                try:
                    rendered_content = self.renderer.render_component_files(
                        file_paths, component_vars
                    )

                    # Add to composer with section name and priority
                    composer.add_section(
                        component.section, rendered_content, component.priority
                    )

                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Failed to render {component.name}:[/yellow] {e}"
                    )

        # Step 3: Compose final document
        return composer.compose(include_toc=include_toc)

    def compose_settings_json(
        self,
        component_paths: List[str],
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Compose .claude/settings.json from selected components.

        Args:
            component_paths: List of component paths to include.
            variables: Dictionary of variables to pass to component templates.

        Returns:
            Composed settings.json content as string.
        """
        if variables is None:
            variables = {}

        try:
            resolved_components = self.loader.resolve_dependencies(component_paths)
        except ValueError as e:
            console.print(f"[red]Error resolving dependencies:[/red] {e}")
            raise

        # Collect all settings file content
        all_content = []

        for component in resolved_components:
            component_vars = self._merge_variables(component.variables, variables)
            file_paths = component.get_file_paths("settings")

            if file_paths:
                try:
                    rendered = self.renderer.render_component_files(
                        file_paths, component_vars
                    )
                    all_content.append(rendered)
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Failed to render settings for {component.name}:[/yellow] {e}"
                    )

        # Join all settings content
        return "\n".join(all_content) if all_content else "{}"

    def compose_contributing_md(
        self,
        component_paths: List[str],
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Compose CONTRIBUTING.md from selected components.

        Args:
            component_paths: List of component paths to include.
            variables: Dictionary of variables to pass to component templates.

        Returns:
            Composed CONTRIBUTING.md content as string.
        """
        if variables is None:
            variables = {}

        try:
            resolved_components = self.loader.resolve_dependencies(component_paths)
        except ValueError as e:
            console.print(f"[red]Error resolving dependencies:[/red] {e}")
            raise

        # Use MarkdownComposer for sections
        composer = MarkdownComposer()

        for component in resolved_components:
            component_vars = self._merge_variables(component.variables, variables)
            file_paths = component.get_file_paths("contributing")

            if file_paths:
                try:
                    rendered = self.renderer.render_component_files(
                        file_paths, component_vars
                    )
                    composer.add_section(
                        component.section, rendered, component.priority
                    )
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Failed to render CONTRIBUTING for {component.name}:[/yellow] {e}"
                    )

        return composer.compose(include_toc=False)

    def _merge_variables(
        self, component_variables: Dict[str, Any], provided_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge component default variables with provided variables.

        Args:
            component_variables: Default variables from component.toml.
            provided_variables: Variables provided by user.

        Returns:
            Merged variable dictionary.
        """
        merged = {}

        # Start with component defaults
        for key, config in component_variables.items():
            if isinstance(config, dict) and "default" in config:
                merged[key] = config["default"]
            else:
                merged[key] = config

        # Override with provided variables
        merged.update(provided_variables)

        return merged

    def get_available_components(self, category: Optional[str] = None) -> List[str]:
        """Get list of available components.

        Args:
            category: Optional category to filter by.

        Returns:
            List of component paths.
        """
        return self.loader.list_components(category)

    def get_component_details(self, component_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a component.

        Args:
            component_path: Path to component (e.g., "languages/python").

        Returns:
            Dictionary with component details, or None if not found.
        """
        return self.loader.get_component_info(component_path)

    def validate_components(self, component_paths: List[str]) -> tuple[bool, str]:
        """Validate that components can be resolved without errors.

        Args:
            component_paths: List of component paths to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            self.loader.resolve_dependencies(component_paths)
            return True, ""
        except ValueError as e:
            return False, str(e)
