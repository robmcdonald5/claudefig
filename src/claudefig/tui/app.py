"""Interactive TUI (Text User Interface) for claudefig."""

import contextlib
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Static

from claudefig import __version__
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.services import config_service
from claudefig.tui.panels import ContentPanel


class MainScreen(App):
    """Main claudefig TUI application with side-by-side layout."""

    TITLE = "claudefig"
    SUB_TITLE = f"v{__version__}"

    # Type hints for attributes accessed by child widgets
    config_data: dict[str, Any]
    config_repo: TomlConfigRepository

    # Load CSS from external files (split by feature)
    CSS_PATH = [
        Path(__file__).parent / "styles" / "base.tcss",
        Path(__file__).parent / "styles" / "panels.tcss",
        Path(__file__).parent / "styles" / "screens.tcss",
        Path(__file__).parent / "styles" / "widgets.tcss",
    ]

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        Binding("escape", "clear_selection", "Back", key_display="esc"),
        Binding("backspace", "clear_selection", "Back", show=False),
        Binding("left", "navigate_left", "Navigate Left", show=True),
        Binding("right", "navigate_right", "Navigate Right", show=True),
        Binding("up", "navigate_up", "Navigate Up", show=True),
        Binding("down", "navigate_down", "Navigate Down", show=True),
    ]

    active_button: reactive[str | None] = reactive(None)

    def __init__(self, **kwargs):
        """Initialize the app."""
        super().__init__(**kwargs)

        config_path = Path.cwd() / "claudefig.toml"

        self.config_repo = TomlConfigRepository(config_path)
        if config_path.exists():
            self.config_data = config_service.load_config(self.config_repo)
        else:
            self.config_data = config_service.DEFAULT_CONFIG.copy()

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Horizontal(id="main-container"):
            # Left panel - Menu
            # Wrap menu content in VerticalScroll to handle overflow when terminal is small
            # can_focus=False prevents the scroll container from being in the focus chain
            with (
                Vertical(id="menu-panel"),
                VerticalScroll(can_focus=False, id="menu-scroll"),
            ):
                yield Static("claudefig", id="title")
                yield Static(f"v{__version__}", id="version")

                with Container(id="menu-buttons"):
                    yield Button("Initialize Project", id="init")
                    yield Button("Presets", id="presets")
                    yield Button("Config", id="config")
                    yield Button("Exit", id="exit")

            # Right panel - Content
            yield ContentPanel(self.config_data, self.config_repo, id="content-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Set focus to first button on mount."""
        from claudefig.user_config import ensure_user_config

        # Initialize user config on first launch
        ensure_user_config(verbose=True)

        self.query_one("#init", Button).focus()

    def on_key(self, event: Key) -> None:
        """Handle key events for navigation.

        Explicitly handles up/down navigation when in the menu panel to prevent
        the VerticalScroll container from intercepting arrow keys and scrolling
        instead of navigating through buttons. Includes scroll-to-reveal logic
        for top/bottom boundaries.

        Args:
            event: The key event
        """
        focused = self.focused
        if not focused:
            return

        # Check if we're in the menu panel
        menu_panel = self.query_one("#menu-panel")
        if self._is_descendant_of(focused, menu_panel):
            # Get all menu buttons to check if we're at top/bottom
            menu_buttons_container = self.query_one("#menu-buttons")
            menu_buttons = [
                w for w in menu_buttons_container.query("Button") if w.focusable
            ]

            if not menu_buttons:
                return

            # In menu panel - handle navigation with scroll-to-reveal logic
            if event.key == "up":
                with contextlib.suppress(ValueError, Exception):
                    current_index = menu_buttons.index(focused)

                    # At the top - scroll container to home (absolute top)
                    if current_index == 0:
                        with contextlib.suppress(Exception):
                            scroll_container = menu_panel.query_one(VerticalScroll)
                            scroll_container.scroll_home(animate=True)
                        event.prevent_default()
                        event.stop()
                        return

                    # Otherwise navigate up normally
                    self.action_navigate_up()
                    event.prevent_default()
                    event.stop()
                    return
                # Fallback to normal navigation
                self.action_navigate_up()
                event.prevent_default()
                event.stop()
                return

            elif event.key == "down":
                with contextlib.suppress(ValueError, Exception):
                    current_index = menu_buttons.index(focused)
                    max_index = len(menu_buttons) - 1

                    # At the bottom - scroll container to end (absolute bottom)
                    if current_index == max_index:
                        with contextlib.suppress(Exception):
                            scroll_container = menu_panel.query_one(VerticalScroll)
                            scroll_container.scroll_end(animate=True)
                        event.prevent_default()
                        event.stop()
                        return

                    # Otherwise navigate down normally
                    self.action_navigate_down()
                    event.prevent_default()
                    event.stop()
                    return
                # Fallback to normal navigation
                self.action_navigate_down()
                event.prevent_default()
                event.stop()
                return

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
        # ConfigPanel handles its own focus restoration, so skip for config section
        if section_id != "config":
            self.set_timer(0.05, self._focus_first_in_content)

    def _focus_first_in_content(self) -> None:
        """Focus the first focusable widget in the content panel."""
        with contextlib.suppress(Exception):
            content_panel = self.query_one("#content-panel", ContentPanel)
            focusables = [
                w for w in content_panel.query("Button, Switch") if w.focusable
            ]
            if focusables:
                focusables[0].focus()

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
            with contextlib.suppress(Exception):
                self.query_one(f"#{previously_active}", Button).focus()
                previously_active = None  # Mark as handled
            if previously_active:  # Fallback if suppress didn't find button
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
        with contextlib.suppress(Exception):
            button_rows = self.query(".button-row")
            for button_row in button_rows:
                if self._is_descendant_of(focused, button_row):
                    # Navigate right within the horizontal button row
                    focusables = [w for w in button_row.query("Button") if w.focusable]
                    if len(focusables) > 1:
                        with contextlib.suppress(ValueError):
                            current_index = focusables.index(focused)
                            if current_index < len(focusables) - 1:
                                focusables[current_index + 1].focus()
                                return

        # Check if we're in the menu panel
        menu_panel = self.query_one("#menu-panel")
        if self._is_descendant_of(focused, menu_panel):
            # Only move to content panel if a section is already active
            if self.active_button:
                content_panel = self.query_one("#content-panel", ContentPanel)

                # ConfigPanel and PresetsPanel handle their own focus restoration
                if self.active_button == "config":
                    try:
                        from claudefig.tui.panels.config_panel import ConfigPanel

                        config_panel = content_panel.query_one(
                            "#config-panel", ConfigPanel
                        )
                        config_panel.restore_focus()
                    except Exception:
                        # Fallback if config panel not found
                        focusables = [
                            w for w in content_panel.query("Button") if w.focusable
                        ]
                        if focusables:
                            focusables[0].focus()
                elif self.active_button == "presets":
                    try:
                        from claudefig.tui.panels.presets_panel import PresetsPanel

                        presets_panel = content_panel.query_one(
                            "#presets-panel", PresetsPanel
                        )
                        presets_panel.restore_focus()
                    except Exception:
                        # Fallback if presets panel not found
                        focusables = [
                            w
                            for w in content_panel.query("Button, Select")
                            if w.focusable
                        ]
                        if focusables:
                            focusables[0].focus()
                else:
                    # For other panels, focus the first item
                    focusables = [
                        w for w in content_panel.query("Button, Switch") if w.focusable
                    ]
                    if focusables:
                        focusables[0].focus()
            # Don't activate section with right arrow - require Enter
            return

        # Check if we're in settings categories
        with contextlib.suppress(Exception):
            settings_categories = self.query_one("#settings-categories")
            if self._is_descendant_of(focused, settings_categories):
                # Move to settings content
                settings_content = self.query_one("#settings-content")
                focusables = [
                    w for w in settings_content.query("Switch") if w.focusable
                ]
                if focusables:
                    focusables[0].focus()

    def action_navigate_left(self) -> None:
        """Navigate left: content → menu, or settings → categories."""
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal button row (side-by-side buttons)
        with contextlib.suppress(Exception):
            button_rows = self.query(".button-row")
            for button_row in button_rows:
                if self._is_descendant_of(focused, button_row):
                    # Navigate left within the horizontal button row
                    focusables = [w for w in button_row.query("Button") if w.focusable]
                    if len(focusables) > 1:
                        with contextlib.suppress(ValueError):
                            current_index = focusables.index(focused)
                            if current_index > 0:
                                focusables[current_index - 1].focus()
                                return

        # Check if we're in settings content
        with contextlib.suppress(Exception):
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
            with contextlib.suppress(Exception):
                scope = self.query_one(f"#{scope_id}")
                if self._is_descendant_of(widget, scope) or widget == scope:
                    return scope

        # Fallback to content panel for other content
        with contextlib.suppress(Exception):
            content_panel = self.query_one("#content-panel")
            if self._is_descendant_of(widget, content_panel):
                return content_panel

        return None

    def action_navigate_up(self) -> None:
        """Navigate up within the current focus scope."""
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal button row - navigate up should exit to previous element
        with contextlib.suppress(Exception):
            button_rows = self.query(".button-row")
            for button_row in button_rows:
                if self._is_descendant_of(focused, button_row):
                    # Navigate up exits the button row to the previous focusable element
                    self.screen.focus_previous()
                    return

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

        # Check if we're in a horizontal button row - navigate down should exit to next element
        with contextlib.suppress(Exception):
            button_rows = self.query(".button-row")
            for button_row in button_rows:
                if self._is_descendant_of(focused, button_row):
                    # Navigate down exits the button row to the next focusable element
                    self.screen.focus_next()
                    return

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
