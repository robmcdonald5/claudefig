"""Initialization settings screen for editing init behavior."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, Static, Switch

from claudefig.config import Config
from claudefig.tui.base import BackButtonMixin, ScrollNavigationMixin


class ProjectSettingsScreen(Screen, BackButtonMixin, ScrollNavigationMixin):
    """Screen for editing initialization settings."""

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("backspace", "pop_screen", "Back"),
        ("up", "focus_previous", "Focus Previous"),
        ("down", "focus_next", "Focus Next"),
        ("left", "focus_left", "Focus Left"),
        ("right", "focus_right", "Focus Right"),
    ]

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize initialization settings screen.

        Args:
            config: Configuration object
        """
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the initialization settings screen."""
        # can_focus=False prevents the container from being in the focus chain
        # while still allowing it to be scrolled programmatically
        with VerticalScroll(id="project-settings-screen", can_focus=False):
            yield Label("INITIALIZATION SETTINGS", classes="screen-title")

            yield Label(
                "Configure how claudefig initializes and generates files in your project.",
                classes="screen-description",
            )

            # Compact settings list (matching Core Files style)
            with Vertical(classes="init-settings-list"):
                # Overwrite setting - compact row
                with Horizontal(classes="init-setting-row"):
                    overwrite = self.config.get("init.overwrite_existing", False)
                    yield Switch(value=overwrite, id="switch-overwrite")
                    with Vertical(classes="init-setting-info"):
                        yield Label(
                            "Overwrite Existing Files", classes="init-setting-label"
                        )
                        yield Static(
                            "Allow initialization to overwrite files that already exist",
                            classes="init-setting-desc",
                        )

                # Backup setting - compact row (disabled when overwrite is off)
                with Horizontal(classes="init-setting-row"):
                    backup = self.config.get("init.create_backup", True)
                    yield Switch(
                        value=backup, id="switch-backup", disabled=not overwrite
                    )
                    with Vertical(classes="init-setting-info"):
                        yield Label("Create Backup Files", classes="init-setting-label")
                        yield Static(
                            "Save original files as .bak before overwriting",
                            classes="init-setting-desc",
                        )

            # Action buttons (matching Core Files style)
            yield from self.compose_back_button()

    def action_pop_screen(self) -> None:
        """Pop the current screen to return to config menu."""
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        # Check if back button was pressed and return early if handled
        if self.handle_back_button(event):
            return

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch changes and auto-save."""
        if event.switch.id == "switch-overwrite":
            # Save overwrite setting
            self.config.set("init.overwrite_existing", event.value)
            self.config.save()

            # Enable/disable backup switch based on overwrite
            backup_switch = self.query_one("#switch-backup", Switch)
            backup_switch.disabled = not event.value

            self.notify("Setting saved", severity="information")

        elif event.switch.id == "switch-backup":
            # Save backup setting
            self.config.set("init.create_backup", event.value)
            self.config.save()
            self.notify("Setting saved", severity="information")
