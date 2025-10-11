"""Content panel for orchestrating dynamic panel display."""

from textual.containers import Container

from claudefig.config import Config
from claudefig.tui.panels.config_panel import ConfigPanel
from claudefig.tui.panels.initialize_panel import InitializePanel
from claudefig.tui.panels.presets_panel import PresetsPanel


class ContentPanel(Container):
    """Dynamic content panel that displays based on selection."""

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize the content panel."""
        super().__init__(**kwargs)
        self.config = config
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
                InitializePanel(self.config, self._switch_to_presets, id="init-panel")
            )
        elif section == "presets":
            self.mount(PresetsPanel(id="presets-panel"))
        elif section == "config":
            self.mount(ConfigPanel(self.config, id="config-panel"))

        self.display = True

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
        self.display = False
