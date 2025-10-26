"""Config panel - main menu for configuration options."""

import contextlib
from typing import Any

from textual.app import ComposeResult
from textual.containers import Grid
from textual.widgets import Button, Label

from claudefig.preset_manager import PresetManager
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.services import config_service
from claudefig.tui.base import BaseNavigablePanel
from claudefig.tui.screens import (
    CoreFilesScreen,
    FileInstancesScreen,
    OverviewScreen,
    ProjectSettingsScreen,
)


class ConfigPanel(BaseNavigablePanel):
    """Main configuration menu panel with custom 2D grid navigation.

    Inherits standard navigation bindings from BaseNavigablePanel but overrides
    all action_navigate_* methods to implement custom 2x2 grid navigation logic.
    """

    # Class variable for state persistence across panel instances
    _last_focused_button: str = "btn-overview"

    # 2D grid navigation map (button_id -> (row, col))
    GRID_POSITIONS = {
        "btn-overview": (0, 0),
        "btn-settings": (0, 1),
        "btn-core-files": (1, 0),
        "btn-file-instances": (1, 1),
    }

    # Reverse map (row, col) -> button_id
    POSITION_TO_BUTTON = {v: k for k, v in GRID_POSITIONS.items()}

    def __init__(
        self, config_data: dict[str, Any], config_repo: TomlConfigRepository, **kwargs
    ) -> None:
        """Initialize config panel.

        Args:
            config_data: Configuration data dictionary
            config_repo: Configuration repository
        """
        super().__init__(**kwargs)
        self.config_data = config_data
        self.config_repo = config_repo
        self.preset_manager = PresetManager()

    def compose(self) -> ComposeResult:
        """Compose the config menu panel."""
        # Check if config exists
        if not self.config_repo.exists():
            yield Label(
                "No .claudefig.toml found in current directory.\n\n"
                "Go to 'Presets' panel and use a preset to create a config.",
                classes="placeholder",
            )
            return

        # Load file instances
        instances_data = config_service.get_file_instances(self.config_data)
        if instances_data:
            from claudefig.services import file_instance_service

            instances_dict, _ = file_instance_service.load_instances_from_config(
                instances_data
            )
            instances_list = list(instances_dict.values())
        else:
            instances_list = []

        # Header
        yield Label("Configuration Menu", classes="panel-title")

        # Summary info
        enabled_count = sum(1 for i in instances_list if i.enabled)
        total_count = len(instances_list)
        config_path_str = str(self.config_repo.get_path())
        if len(config_path_str) > 60:
            config_path_str = "..." + config_path_str[-57:]
        yield Label(
            f"{config_path_str} | {total_count} instances ({enabled_count} enabled)",
            classes="panel-subtitle",
        )

        # Menu buttons in grid
        with Grid(id="config-menu-grid"):
            yield Button(
                "Project Overview\nStats & quick actions",
                id="btn-overview",
                classes="config-menu-button",
            )
            yield Button(
                "Initialization Settings\nFile generation behavior",
                id="btn-settings",
                classes="config-menu-button",
            )
            yield Button(
                "Core Files\nSingle-instance files",
                id="btn-core-files",
                classes="config-menu-button",
            )
            yield Button(
                "File Instances\nMulti-instance files",
                id="btn-file-instances",
                classes="config-menu-button",
            )

    def on_mount(self) -> None:
        """Restore focus to the last focused button."""
        self.restore_focus()

    def restore_focus(self) -> None:
        """Restore focus to the last focused button."""
        try:
            last_button = self.query_one(f"#{ConfigPanel._last_focused_button}", Button)
            last_button.focus()
        except Exception:
            # Fallback to first button if last focused doesn't exist
            with contextlib.suppress(Exception):
                self.query_one("#btn-overview", Button).focus()

    def _navigate_grid(self, row_delta: int, col_delta: int) -> None:
        """Navigate in the grid by moving in a direction.

        Args:
            row_delta: Change in row (-1 for up, 1 for down)
            col_delta: Change in column (-1 for left, 1 for right)
        """
        # Get currently focused widget
        focused = self.app.focused
        if not focused or not isinstance(focused, Button):
            return

        button_id = focused.id
        if button_id not in self.GRID_POSITIONS:
            return

        # Get current position
        row, col = self.GRID_POSITIONS[button_id]

        # Calculate new position
        new_row = row + row_delta
        new_col = col + col_delta

        # Vertical: Stop at edges (no wrapping)
        if row_delta < 0 and row == 0:
            # Already at top row - do nothing
            return
        if row_delta > 0 and row == 1:
            # Already at bottom row (row 1) - do nothing
            return

        # Horizontal: Escape to main menu when navigating left from leftmost column
        if col_delta < 0 and col == 0:
            # Moving left from leftmost column - go to Config button in main menu
            try:
                config_button = self.app.query_one("#config", Button)
                config_button.focus()
                return
            except Exception:
                pass  # Config button not found

        # Horizontal: Stay at right edge when navigating right from rightmost column
        if col_delta > 0 and col == 1:
            # Already at rightmost column - do nothing
            return

        # Focus the new button within the grid
        new_button_id = self.POSITION_TO_BUTTON.get((new_row, new_col))
        if new_button_id:
            try:
                new_button = self.query_one(f"#{new_button_id}", Button)
                new_button.focus()
                # Track this as the last focused button
                ConfigPanel._last_focused_button = new_button_id
            except Exception:
                pass  # Button not found

    def action_navigate_up(self) -> None:
        """Navigate up in the grid."""
        self._navigate_grid(-1, 0)

    def action_navigate_down(self) -> None:
        """Navigate down in the grid."""
        self._navigate_grid(1, 0)

    def action_navigate_left(self) -> None:
        """Navigate left in the grid."""
        self._navigate_grid(0, -1)

    def action_navigate_right(self) -> None:
        """Navigate right in the grid."""
        self._navigate_grid(0, 1)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses and navigate to screens."""
        from claudefig.services import config_service, file_instance_service

        button_id = event.button.id

        # Track this button as the last focused for when we return
        if button_id in self.GRID_POSITIONS:
            ConfigPanel._last_focused_button = button_id

        # Load instances_dict for migrated screens
        instances_data = config_service.get_file_instances(self.config_data)
        instances_dict, _ = file_instance_service.load_instances_from_config(
            instances_data
        )

        if button_id == "btn-overview":
            # OverviewScreen has been migrated - uses new architecture
            self.app.push_screen(
                OverviewScreen(
                    config_data=self.config_data,
                    config_repo=self.config_repo,
                    instances_dict=instances_dict,
                )
            )
        elif button_id == "btn-settings":
            # ProjectSettingsScreen has been migrated - uses new architecture
            self.app.push_screen(
                ProjectSettingsScreen(
                    config_data=self.config_data,
                    config_repo=self.config_repo,
                    instances_dict=instances_dict,
                )
            )
        elif button_id == "btn-core-files":
            # CoreFilesScreen has been migrated - uses new architecture
            self.app.push_screen(
                CoreFilesScreen(
                    config_data=self.config_data,
                    config_repo=self.config_repo,
                    instances_dict=instances_dict,
                )
            )
        elif button_id == "btn-file-instances":
            # FileInstancesScreen has been migrated - uses new architecture
            self.app.push_screen(
                FileInstancesScreen(
                    config_data=self.config_data,
                    config_repo=self.config_repo,
                    instances_dict=instances_dict,
                )
            )
