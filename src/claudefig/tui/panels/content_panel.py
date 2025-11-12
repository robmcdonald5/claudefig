"""Content panel for orchestrating dynamic panel display."""

from typing import Any

from textual.containers import Container

from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.tui.panels.config_panel import ConfigPanel
from claudefig.tui.panels.initialize_panel import InitializePanel
from claudefig.tui.panels.presets_panel import PresetsPanel


class ContentPanel(Container):
    """Dynamic content panel that displays based on selection."""

    # Type hints for attributes accessed by child widgets
    config_data: dict[str, Any]
    config_repo: TomlConfigRepository

    def __init__(
        self, config_data: dict[str, Any], config_repo: TomlConfigRepository, **kwargs
    ) -> None:
        """Initialize the content panel."""
        super().__init__(**kwargs)
        self.config_data = config_data
        self.config_repo = config_repo
        self.current_section: str | None = None

    def show_section(self, section: str) -> None:
        """Display content for the specified section."""
        # Don't remount if we're already showing this section
        if self.current_section == section and self.children:
            return

        self.current_section = section

        # Remove all children widgets to avoid ID conflicts
        for child in list(self.children):
            child.remove()

        # Mount appropriate panel
        if section == "init":
            self.mount(
                InitializePanel(
                    self.config_data,
                    self.config_repo,
                    self._switch_to_presets,
                    id="init-panel",
                )
            )
        elif section == "presets":
            self.mount(PresetsPanel(id="presets-panel"))
        elif section == "config":
            self.mount(
                ConfigPanel(self.config_data, self.config_repo, id="config-panel")
            )

    def _switch_to_presets(self) -> None:
        """Switch to presets section."""
        # This will be called from InitializePanel
        from claudefig.tui.app import MainScreen

        main_app = self.app
        if isinstance(main_app, MainScreen):
            main_app._activate_section("presets")

    def clear(self) -> None:
        """Clear the content panel."""
        self.current_section = None
        self.remove_children()
