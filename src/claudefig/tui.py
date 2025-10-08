"""Interactive TUI (Text User Interface) for claudefig."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Static

from claudefig import __version__


class ContentPanel(Static):
    """Dynamic content panel that displays based on selection."""

    def __init__(self, **kwargs) -> None:
        """Initialize the content panel."""
        super().__init__(**kwargs)
        self.current_section: str | None = None

    def show_section(self, section: str) -> None:
        """Display content for the specified section."""
        self.current_section = section

        content_map = {
            "init": ("Initialize Project", "Interactive project initialization wizard\n(Coming soon)"),
            "components": ("Manage Components", "View, add, and remove components\n(Coming soon)"),
            "config": ("View Configuration", "Display current claudefig configuration\n(Coming soon)"),
            "settings": ("Settings", "Configure claudefig preferences\n(Coming soon)"),
        }

        if section in content_map:
            title, description = content_map[section]
            self.update(f"[bold cyan]{title}[/]\n\n[dim]{description}[/]")
            self.display = True
        else:
            self.update("")
            self.display = False

    def clear(self) -> None:
        """Clear the content panel."""
        self.current_section = None
        self.update("")
        self.display = False


class MainScreen(App):
    """Main claudefig TUI application with side-by-side layout."""

    TITLE = "claudefig"
    SUB_TITLE = f"v{__version__}"

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #menu-panel {
        width: 40;
        height: 100%;
        padding: 1 2;
    }

    #title {
        text-style: bold;
        color: $accent;
        margin-bottom: 0;
        margin-top: 1;
    }

    #version {
        color: $text-muted;
        margin-bottom: 2;
    }

    #menu-buttons {
        width: 100%;
        height: auto;
        border: round $primary;
        padding: 1;
    }

    Button {
        width: 100%;
        margin: 0;
        min-height: 1;
        padding: 0 1;
        background: $panel;
    }

    Button:focus {
        text-style: bold;
        border: solid $accent;
    }

    Button.active {
        background: $accent;
        color: $text;
        text-style: bold;
    }

    Button.active:focus {
        background: $accent;
        color: $text;
        text-style: bold;
        border: solid $accent;
    }

    #content-panel {
        width: 1fr;
        height: 100%;
        border-left: solid $primary;
        padding: 2 4;
        display: none;
    }

    #content-panel.visible {
        display: block;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        Binding("escape", "clear_selection", "Back", key_display="esc/←"),
        Binding("backspace", "clear_selection", "Back", show=False),
        ("up", "focus_previous", "Focus Previous"),
        ("down", "focus_next", "Focus Next"),
    ]

    active_button: reactive[str | None] = reactive(None)

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Horizontal(id="main-container"):
            # Left panel - Menu
            with Vertical(id="menu-panel"):
                yield Static("claudefig", id="title")
                yield Static(f"v{__version__}", id="version")

                with Container(id="menu-buttons"):
                    yield Button("Initialize Project", id="init")
                    yield Button("Manage Components", id="components")
                    yield Button("View Configuration", id="config")
                    yield Button("Settings", id="settings")
                    yield Button("Exit", id="exit")

            # Right panel - Content
            yield ContentPanel(id="content-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Set focus to first button on mount."""
        self.query_one("#init", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if not button_id:
            return

        if button_id == "exit":
            self.exit()
            return

        # Activate the section
        self._activate_section(button_id)

    def _activate_section(self, section_id: str) -> None:
        """Activate a section and update UI accordingly."""
        # Update active button state
        self.active_button = section_id

        # Update button styling
        for button in self.query(Button):
            if button.id == section_id:
                button.add_class("active")
            else:
                button.remove_class("active")

        # Show content panel
        content_panel = self.query_one(ContentPanel)
        content_panel.show_section(section_id)
        content_panel.add_class("visible")

    def action_clear_selection(self) -> None:
        """Clear the active selection and hide content panel."""
        # Clear active button styling
        for button in self.query(Button):
            button.remove_class("active")

        # Hide content panel
        content_panel = self.query_one(ContentPanel)
        content_panel.clear()
        content_panel.remove_class("visible")

        self.active_button = None

        # Refocus the first button
        self.query_one("#init", Button).focus()


class ClaudefigApp(MainScreen):
    """Alias for backward compatibility."""
    pass


if __name__ == "__main__":
    app = MainScreen()
    app.run()
