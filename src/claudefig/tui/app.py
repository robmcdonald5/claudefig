"""Interactive TUI (Text User Interface) for claudefig."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Static

from claudefig import __version__
from claudefig.config import Config
from claudefig.tui.panels import ContentPanel


class MainScreen(App):
    """Main claudefig TUI application with side-by-side layout."""

    TITLE = "claudefig"
    SUB_TITLE = f"v{__version__}"

    # Type hints for attributes accessed by child widgets
    config: Config

    # Load CSS from external file
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        Binding("escape", "clear_selection", "Back", key_display="esc"),
        Binding("backspace", "clear_selection", "Back", show=False),
        Binding("left", "navigate_left", "Nav Left", show=True),
        Binding("right", "navigate_right", "Nav Right", show=True),
        Binding("up", "navigate_up", "Nav Up", show=True),
        Binding("down", "navigate_down", "Nav Down", show=True),
    ]

    active_button: reactive[str | None] = reactive(None)

    def __init__(self, **kwargs):
        """Initialize the app."""
        super().__init__(**kwargs)
        self.config = Config()

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
                    yield Button("Presets", id="presets")
                    yield Button("Config", id="config")
                    yield Button("Exit", id="exit")

            # Right panel - Content
            yield ContentPanel(self.config, id="content-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Set focus to first button on mount."""
        from claudefig.user_config import ensure_user_config

        # Initialize user config on first launch
        ensure_user_config(verbose=True)

        self.query_one("#init", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if not button_id:
            return

        # Don't handle button presses from child panels
        if button_id.startswith(("cat-", "btn-", "switch-")):
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
        for button in self.query("#menu-buttons Button"):
            if button.id == section_id:
                button.add_class("active")
            else:
                button.remove_class("active")

        # Show content panel
        content_panel = self.query_one("#content-panel", ContentPanel)
        content_panel.show_section(section_id)
        content_panel.add_class("visible")

        # Auto-focus first item in the new content tree
        self.set_timer(0.05, self._focus_first_in_content)

    def _focus_first_in_content(self) -> None:
        """Focus the first focusable widget in the content panel."""
        try:
            content_panel = self.query_one("#content-panel", ContentPanel)
            focusables = [
                w for w in content_panel.query("Button, Switch") if w.focusable
            ]
            if focusables:
                focusables[0].focus()
        except Exception:
            pass

    def action_clear_selection(self) -> None:
        """Clear the active selection and hide content panel."""
        # Remember which button was active
        previously_active = self.active_button

        # Clear active button styling
        for button in self.query("#menu-buttons Button"):
            button.remove_class("active")

        self.active_button = None

        # FOCUS FIRST - set focus on target button
        if previously_active:
            try:
                self.query_one(f"#{previously_active}", Button).focus()
            except Exception:
                self.query_one("#init", Button).focus()
        else:
            self.query_one("#init", Button).focus()

        # CRITICAL: Use call_after_refresh to ensure focus has settled before removing widgets
        # Removing focused widgets causes Textual to temporarily focus Exit button
        self.call_after_refresh(self._clear_content_panel)

    def _clear_content_panel(self) -> None:
        """Clear content panel after focus has settled."""
        content_panel = self.query_one("#content-panel", ContentPanel)
        content_panel.clear()
        content_panel.remove_class("visible")

    def _is_descendant_of(self, widget, ancestor) -> bool:
        """Check if widget is a descendant of ancestor."""
        current = widget.parent
        while current is not None:
            if current == ancestor:
                return True
            current = current.parent
        return False

    def action_navigate_right(self) -> None:
        """Navigate right: menu → content (if section open), or categories → settings."""
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal button row (side-by-side buttons)
        try:
            button_rows = self.query(".button-row")
            for button_row in button_rows:
                if self._is_descendant_of(focused, button_row):
                    # Navigate right within the horizontal button row
                    focusables = [w for w in button_row.query("Button") if w.focusable]
                    if len(focusables) > 1:
                        try:
                            current_index = focusables.index(focused)
                            if current_index < len(focusables) - 1:
                                focusables[current_index + 1].focus()
                                return
                        except ValueError:
                            pass
        except Exception:
            pass

        # Check if we're in the menu panel
        menu_panel = self.query_one("#menu-panel")
        if self._is_descendant_of(focused, menu_panel):
            # Only move to content panel if a section is already active
            if self.active_button:
                content_panel = self.query_one("#content-panel", ContentPanel)
                # Try to focus the first focusable widget in content
                focusables = [
                    w for w in content_panel.query("Button, Switch") if w.focusable
                ]
                if focusables:
                    focusables[0].focus()
            # Don't activate section with right arrow - require Enter
            return

        # Check if we're in settings categories
        try:
            settings_categories = self.query_one("#settings-categories")
            if self._is_descendant_of(focused, settings_categories):
                # Move to settings content
                settings_content = self.query_one("#settings-content")
                focusables = [
                    w for w in settings_content.query("Switch") if w.focusable
                ]
                if focusables:
                    focusables[0].focus()
        except Exception:
            pass

    def action_navigate_left(self) -> None:
        """Navigate left: content → menu, or settings → categories."""
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal button row (side-by-side buttons)
        try:
            button_rows = self.query(".button-row")
            for button_row in button_rows:
                if self._is_descendant_of(focused, button_row):
                    # Navigate left within the horizontal button row
                    focusables = [w for w in button_row.query("Button") if w.focusable]
                    if len(focusables) > 1:
                        try:
                            current_index = focusables.index(focused)
                            if current_index > 0:
                                focusables[current_index - 1].focus()
                                return
                        except ValueError:
                            pass
        except Exception:
            pass

        # Check if we're in settings content
        try:
            settings_content = self.query_one("#settings-content")
            if self._is_descendant_of(focused, settings_content):
                # Move to settings categories
                settings_categories = self.query_one("#settings-categories")
                focusables = [
                    w for w in settings_categories.query("Button") if w.focusable
                ]
                if focusables:
                    focusables[0].focus()
                return
        except Exception:
            pass

        # Check if we're in content panel
        content_panel = self.query_one("#content-panel")
        if self._is_descendant_of(focused, content_panel) and self.active_button:
            # Move back to the active menu button
            menu_button = self.query_one(f"#{self.active_button}", Button)
            menu_button.focus()

    def _get_focus_scope(self, widget):
        """Get the container that defines the focus scope for a widget."""
        # Define scope containers (independent vertical navigation trees)
        scope_ids = [
            "menu-buttons",
            "settings-categories",
            "settings-content",
            "init-panel",
        ]

        for scope_id in scope_ids:
            try:
                scope = self.query_one(f"#{scope_id}")
                if self._is_descendant_of(widget, scope) or widget == scope:
                    return scope
            except Exception:
                continue

        # Fallback to content panel for other content
        try:
            content_panel = self.query_one("#content-panel")
            if self._is_descendant_of(widget, content_panel):
                return content_panel
        except Exception:
            pass

        return None

    def action_navigate_up(self) -> None:
        """Navigate up within the current focus scope."""
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal button row - don't navigate up/down within it
        try:
            button_rows = self.query(".button-row")
            for button_row in button_rows:
                if self._is_descendant_of(focused, button_row):
                    # In a horizontal layout, use left/right only
                    # Navigate up should exit the button row to previous element
                    return
        except Exception:
            pass

        scope = self._get_focus_scope(focused)
        if not scope:
            self.screen.focus_previous()
            return

        # Get all focusable widgets in this scope
        focusables = [w for w in scope.query("Button, Switch") if w.focusable]
        if not focusables:
            return

        try:
            current_index = focusables.index(focused)
            if current_index > 0:
                focusables[current_index - 1].focus()
        except ValueError:
            # Not in the list, focus first
            if focusables:
                focusables[0].focus()

    def action_navigate_down(self) -> None:
        """Navigate down within the current focus scope."""
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal button row - don't navigate up/down within it
        try:
            button_rows = self.query(".button-row")
            for button_row in button_rows:
                if self._is_descendant_of(focused, button_row):
                    # In a horizontal layout, use left/right only
                    # Navigate down should exit the button row to next element
                    return
        except Exception:
            pass

        scope = self._get_focus_scope(focused)
        if not scope:
            self.screen.focus_next()
            return

        # Get all focusable widgets in this scope
        focusables = [w for w in scope.query("Button, Switch") if w.focusable]
        if not focusables:
            return

        try:
            current_index = focusables.index(focused)
            if current_index < len(focusables) - 1:
                focusables[current_index + 1].focus()
        except ValueError:
            # Not in the list, focus first
            if focusables:
                focusables[0].focus()


class ClaudefigApp(MainScreen):
    """Alias for backward compatibility."""

    pass


if __name__ == "__main__":
    app = MainScreen()
    app.run()
