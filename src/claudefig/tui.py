"""Interactive TUI (Text User Interface) for claudefig."""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from claudefig import __version__


class MainMenuScreen(Screen):
    """Main menu screen with navigation options."""

    CSS = """
    MainMenuScreen {
        align: left top;
    }

    #title {
        text-style: bold;
        color: $accent;
        margin-bottom: 0;
        margin-top: 1;
        margin-left: 2;
    }

    #version {
        color: $text-muted;
        margin-bottom: 1;
        margin-left: 2;
    }

    Container {
        width: 40;
        height: auto;
        border: round $primary;
        padding: 1;
        margin-left: 2;
        margin-top: 0;
    }

    Button {
        width: 100%;
        margin: 0;
        min-height: 1;
        padding: 0 1;
    }

    /* Consistent focus styling for all buttons */
    Button:focus {
        text-style: bold;
    }

    Button.-active {
        background: $panel;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
        ("up", "app.focus_previous", "Focus Previous"),
        ("down", "app.focus_next", "Focus Next"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main menu screen."""
        yield Header()
        with Container():
            yield Static("claudefig", id="title")
            yield Static(f"v{__version__}", id="version")
            yield Button("Initialize Project", id="init")
            yield Button("Manage Components", id="components")
            yield Button("View Configuration", id="config")
            yield Button("Settings", id="settings")
            yield Button("Exit", id="exit")
        yield Footer()

    def on_mount(self) -> None:
        """Set focus to first button on mount."""
        self.query_one("#init", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "init":
            self.app.push_screen("init")
        elif button_id == "components":
            self.app.push_screen("components")
        elif button_id == "config":
            self.app.push_screen("config")
        elif button_id == "settings":
            self.app.push_screen("settings")
        elif button_id == "exit":
            self.app.exit()


class InitProjectScreen(Screen):
    """Screen for initializing a new project."""

    CSS = """
    InitProjectScreen {
        align: left top;
    }

    Container {
        width: 60;
        height: auto;
        border: round $primary;
        padding: 1;
        margin-left: 2;
        margin-top: 1;
    }

    #screen-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #placeholder {
        height: 6;
        color: $text-muted;
        margin-bottom: 1;
    }

    Button {
        width: 100%;
        margin-top: 0;
        min-height: 1;
        padding: 0 1;
    }

    Button:focus {
        text-style: bold;
    }
    """

    BINDINGS = [
        ("escape", "back", "Back"),
        ("backspace", "back", "Back"),
        ("up", "app.focus_previous", "Focus Previous"),
        ("down", "app.focus_next", "Focus Next"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the init project screen."""
        yield Header()
        with Container():
            yield Static("Initialize Project", id="screen-title")
            yield Static(
                "Interactive project initialization wizard\n(Coming soon)",
                id="placeholder",
            )
            yield Button("Back to Main Menu", id="back")
        yield Footer()

    def on_mount(self) -> None:
        """Set focus to back button on mount."""
        self.query_one("#back", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back":
            self.app.pop_screen()

    def action_back(self) -> None:
        """Navigate back to main menu."""
        self.app.pop_screen()


class ComponentsScreen(Screen):
    """Screen for managing components."""

    CSS = """
    ComponentsScreen {
        align: left top;
    }

    Container {
        width: 60;
        height: auto;
        border: round $primary;
        padding: 1;
        margin-left: 2;
        margin-top: 1;
    }

    #screen-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #placeholder {
        height: 6;
        color: $text-muted;
        margin-bottom: 1;
    }

    Button {
        width: 100%;
        margin-top: 0;
        min-height: 1;
        padding: 0 1;
    }

    Button:focus {
        text-style: bold;
    }
    """

    BINDINGS = [
        ("escape", "back", "Back"),
        ("backspace", "back", "Back"),
        ("up", "app.focus_previous", "Focus Previous"),
        ("down", "app.focus_next", "Focus Next"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the components management screen."""
        yield Header()
        with Container():
            yield Static("Manage Components", id="screen-title")
            yield Static(
                "View, add, and remove components\n(Coming soon)", id="placeholder"
            )
            yield Button("Back to Main Menu", id="back")
        yield Footer()

    def on_mount(self) -> None:
        """Set focus to back button on mount."""
        self.query_one("#back", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back":
            self.app.pop_screen()

    def action_back(self) -> None:
        """Navigate back to main menu."""
        self.app.pop_screen()


class ConfigScreen(Screen):
    """Screen for viewing configuration."""

    CSS = """
    ConfigScreen {
        align: left top;
    }

    Container {
        width: 60;
        height: auto;
        border: round $primary;
        padding: 1;
        margin-left: 2;
        margin-top: 1;
    }

    #screen-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #placeholder {
        height: 6;
        color: $text-muted;
        margin-bottom: 1;
    }

    Button {
        width: 100%;
        margin-top: 0;
        min-height: 1;
        padding: 0 1;
    }

    Button:focus {
        text-style: bold;
    }
    """

    BINDINGS = [
        ("escape", "back", "Back"),
        ("backspace", "back", "Back"),
        ("up", "app.focus_previous", "Focus Previous"),
        ("down", "app.focus_next", "Focus Next"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the configuration viewer screen."""
        yield Header()
        with Container():
            yield Static("View Configuration", id="screen-title")
            yield Static(
                "Display current claudefig configuration\n(Coming soon)",
                id="placeholder",
            )
            yield Button("Back to Main Menu", id="back")
        yield Footer()

    def on_mount(self) -> None:
        """Set focus to back button on mount."""
        self.query_one("#back", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back":
            self.app.pop_screen()

    def action_back(self) -> None:
        """Navigate back to main menu."""
        self.app.pop_screen()


class SettingsScreen(Screen):
    """Screen for application settings."""

    CSS = """
    SettingsScreen {
        align: left top;
    }

    Container {
        width: 60;
        height: auto;
        border: round $primary;
        padding: 1;
        margin-left: 2;
        margin-top: 1;
    }

    #screen-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #placeholder {
        height: 6;
        color: $text-muted;
        margin-bottom: 1;
    }

    Button {
        width: 100%;
        margin-top: 0;
        min-height: 1;
        padding: 0 1;
    }

    Button:focus {
        text-style: bold;
    }
    """

    BINDINGS = [
        ("escape", "back", "Back"),
        ("backspace", "back", "Back"),
        ("up", "app.focus_previous", "Focus Previous"),
        ("down", "app.focus_next", "Focus Next"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        yield Header()
        with Container():
            yield Static("Settings", id="screen-title")
            yield Static(
                "Configure claudefig preferences\n(Coming soon)", id="placeholder"
            )
            yield Button("Back to Main Menu", id="back")
        yield Footer()

    def on_mount(self) -> None:
        """Set focus to back button on mount."""
        self.query_one("#back", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back":
            self.app.pop_screen()

    def action_back(self) -> None:
        """Navigate back to main menu."""
        self.app.pop_screen()


class ClaudefigApp(App):
    """Main claudefig TUI application."""

    TITLE = "claudefig"
    SUB_TITLE = f"v{__version__}"

    SCREENS = {
        "main": MainMenuScreen,
        "init": InitProjectScreen,
        "components": ComponentsScreen,
        "config": ConfigScreen,
        "settings": SettingsScreen,
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Initialize the application on mount."""
        self.push_screen("main")


if __name__ == "__main__":
    app = ClaudefigApp()
    app.run()
