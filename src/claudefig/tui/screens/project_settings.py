"""Initialization settings screen for editing init behavior."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.widgets import Button, Label, Static, Switch

from claudefig.models import FileInstance
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.services import config_service
from claudefig.tui.base import BaseScreen


class ProjectSettingsScreen(BaseScreen):
    """Screen for editing initialization settings.

    Inherits standard navigation bindings from BaseScreen with ScrollNavigationMixin
    support for smart vertical/horizontal navigation.
    """

    def __init__(
        self,
        config_data: dict[str, Any],
        config_repo: TomlConfigRepository,
        instances_dict: dict[str, FileInstance],
        **kwargs,
    ) -> None:
        """Initialize initialization settings screen.

        Args:
            config_data: Configuration dictionary
            config_repo: Configuration repository for saving
            instances_dict: Dictionary of file instances (id -> FileInstance)
        """
        super().__init__(**kwargs)
        self.config_data = config_data
        self.config_repo = config_repo
        self.instances_dict = instances_dict

    def compose_screen_content(self) -> ComposeResult:
        """Compose the initialization settings screen content."""
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
                    overwrite = config_service.get_value(
                        self.config_data, "init.overwrite_existing", False
                    )
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
                    backup = config_service.get_value(
                        self.config_data, "init.create_backup", True
                    )
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

    def on_key(self, event: Key) -> None:
        """Handle key events for navigation.

        Explicitly calls navigation actions to ensure proper scrolling behavior
        when Switch widgets are present.

        Args:
            event: The key event
        """
        # Explicitly handle up/down navigation to ensure ScrollNavigationMixin
        # methods are called directly for proper scroll behavior
        if event.key == "up":
            self.action_focus_previous()
            event.prevent_default()
            event.stop()
        elif event.key == "down":
            self.action_focus_next()
            event.prevent_default()
            event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        # Check if back button was pressed and return early if handled
        if self.handle_back_button(event):
            return

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch changes and auto-save."""
        if event.switch.id == "switch-overwrite":
            # Save overwrite setting
            config_service.set_value(
                self.config_data, "init.overwrite_existing", event.value
            )
            config_service.save_config(self.config_data, self.config_repo)

            # Enable/disable backup switch based on overwrite
            backup_switch = self.query_one("#switch-backup", Switch)
            backup_switch.disabled = not event.value

            self.notify("Setting saved", severity="information")

        elif event.switch.id == "switch-backup":
            # Save backup setting
            config_service.set_value(
                self.config_data, "init.create_backup", event.value
            )
            config_service.save_config(self.config_data, self.config_repo)
            self.notify("Setting saved", severity="information")
