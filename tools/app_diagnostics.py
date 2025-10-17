"""
Diagnostic version of MainScreen for debugging hover flash issue.

Usage:
    1. Run: python tools/app_diagnostics.py
    2. Navigate to a section (Presets or Config)
    3. Press escape/backspace
    4. Check the terminal output for event sequence
    5. Look for which widget received Enter event and when
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Static

from claudefig import __version__
from claudefig.config import Config
from claudefig.tui.panels import ContentPanel


def log_event(message: str):
    """Log event with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)


class DiagnosticButton(Button):
    """Button with event logging."""

    def on_enter(self, event: events.Enter) -> None:
        """Log Enter event."""
        log_event(f"  ENTER: Button#{self.id}")

    def on_leave(self, event: events.Leave) -> None:
        """Log Leave event."""
        log_event(f"  LEAVE: Button#{self.id}")

    def on_focus(self, event: events.Focus) -> None:
        """Log Focus event."""
        log_event(f"  FOCUS: Button#{self.id}")

    def on_blur(self, event: events.Blur) -> None:
        """Log Blur event."""
        log_event(f"  BLUR: Button#{self.id}")


class MainScreenDiagnostic(App):
    """Diagnostic version of MainScreen."""

    TITLE = "claudefig [DIAGNOSTIC MODE]"
    SUB_TITLE = f"v{__version__}"

    config: Config
    CSS_PATH = Path(__file__).parent.parent / "src" / "claudefig" / "tui" / "styles.tcss"

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
        log_event("=" * 60)
        log_event("DIAGNOSTIC MODE ENABLED")
        log_event("Watch for Enter/Leave/Focus/Blur events")
        log_event("=" * 60)

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Horizontal(id="main-container"):
            with Vertical(id="menu-panel"):
                yield Static("claudefig", id="title")
                yield Static(f"v{__version__} [DIAG]", id="version")

                with Container(id="menu-buttons"):
                    yield DiagnosticButton("Initialize Project", id="init")
                    yield DiagnosticButton("Presets", id="presets")
                    yield DiagnosticButton("Config", id="config")
                    yield DiagnosticButton("Exit", id="exit")

            yield ContentPanel(self.config, id="content-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Set focus to first button on mount."""
        from claudefig.user_config import ensure_user_config
        ensure_user_config(verbose=True)
        log_event("APP MOUNTED - focusing init button")
        self.query_one("#init", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if not button_id:
            return

        if button_id.startswith(("cat-", "btn-", "switch-")):
            return

        if button_id == "exit":
            self.exit()
            return

        log_event(f"BUTTON PRESSED: {button_id}")
        self._activate_section(button_id)

    def _activate_section(self, section_id: str) -> None:
        """Activate a section and update UI accordingly."""
        log_event(f"ACTIVATE SECTION: {section_id}")
        self.active_button = section_id

        for button in self.query("#menu-buttons Button"):
            if button.id == section_id:
                button.add_class("active")
            else:
                button.remove_class("active")

        content_panel = self.query_one("#content-panel", ContentPanel)
        content_panel.show_section(section_id)
        content_panel.add_class("visible")

        self.set_timer(0.05, self._focus_first_in_content)

    def _focus_first_in_content(self) -> None:
        """Focus the first focusable widget in the content panel."""
        log_event("  Attempting to focus first content widget")
        try:
            content_panel = self.query_one("#content-panel", ContentPanel)
            focusables = [
                w for w in content_panel.query("Button, Switch") if w.focusable
            ]
            if focusables:
                focusables[0].focus()
                log_event(f"  Focused: {focusables[0]}")
        except Exception as e:
            log_event(f"  Failed to focus: {e}")

    def action_clear_selection(self) -> None:
        """Clear the active selection and hide content panel."""
        log_event("")
        log_event("=" * 60)
        log_event("ACTION: CLEAR_SELECTION (escape/backspace pressed)")
        log_event("=" * 60)

        previously_active = self.active_button
        log_event(f"Previously active button: {previously_active}")

        # Step 1: Remove active class
        log_event("Step 1: Removing 'active' class from all buttons")
        for button in self.query("#menu-buttons Button"):
            button.remove_class("active")

        self.active_button = None

        # Step 2: Set focus FIRST
        log_event("Step 2: Setting focus to previously active button")
        if previously_active:
            try:
                target = self.query_one(f"#{previously_active}", Button)
                log_event(f"  Focusing: Button#{previously_active}")
                target.focus()
                log_event(f"  Focus set on: {target}")
            except Exception as e:
                log_event(f"  Exception: {e}, falling back to init")
                self.query_one("#init", Button).focus()
        else:
            log_event("  No previously active button, focusing init")
            self.query_one("#init", Button).focus()

        # Step 3: Hide content panel
        log_event("Step 3: Hiding content panel")
        content_panel = self.query_one("#content-panel", ContentPanel)
        log_event("  Calling content_panel.clear()")
        content_panel.clear()
        log_event("  Removing 'visible' class")
        content_panel.remove_class("visible")
        log_event("  Content panel hidden")

        log_event("")
        log_event("WATCHING FOR HOVER FLASH...")
        log_event("(Look for unexpected ENTER event above)")
        log_event("=" * 60)

    def _is_descendant_of(self, widget, ancestor) -> bool:
        """Check if widget is a descendant of ancestor."""
        current = widget.parent
        while current is not None:
            if current == ancestor:
                return True
            current = current.parent
        return False

    # Navigation methods omitted for brevity - using default Textual behavior


if __name__ == "__main__":
    app = MainScreenDiagnostic()
    app.run()
