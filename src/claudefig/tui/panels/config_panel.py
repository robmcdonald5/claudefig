"""Config panel - main menu for configuration options."""

import contextlib
from typing import Any

from textual.app import ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.events import Key
from textual.widgets import Button, Label

from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.services import config_service
from claudefig.tui.base import BaseNavigablePanel
from claudefig.tui.screens import (
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
        "btn-file-instances": (1, 0),
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

    def compose(self) -> ComposeResult:
        """Compose the config menu panel."""
        # can_focus=False prevents the scroll container from being in the focus chain
        with VerticalScroll(can_focus=False):
            # Check if config exists
            if not self.config_repo.exists():
                yield Label(
                    "No claudefig.toml found in current directory.\n\n"
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
                    "File Instances\nManage all file configurations",
                    id="btn-file-instances",
                    classes="config-menu-button",
                )

    def on_mount(self) -> None:
        """Restore focus to the last focused button."""
        self.restore_focus()

    def restore_focus(self) -> None:
        """Restore focus to the last focused button."""
        with contextlib.suppress(Exception):
            last_button = self.query_one(f"#{ConfigPanel._last_focused_button}", Button)
            last_button.focus()
            return
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

        # Vertical: Stop at edges (no wrapping) and scroll to boundaries
        if row_delta < 0 and row == 0:
            # Already at top row - scroll container to home (absolute top)
            with contextlib.suppress(Exception):
                scroll_container = self.query_one(VerticalScroll)
                scroll_container.scroll_home(animate=True)
            return
        if row_delta > 0 and row == 1:
            # Already at bottom row (row 1) - scroll container to end (absolute bottom)
            with contextlib.suppress(Exception):
                scroll_container = self.query_one(VerticalScroll)
                scroll_container.scroll_end(animate=True)
            return

        # Horizontal: Escape to main menu when navigating left from leftmost column
        if col_delta < 0 and col == 0:
            # Moving left from leftmost column - go to Config button in main menu
            with contextlib.suppress(Exception):
                config_button = self.app.query_one("#config", Button)
                config_button.focus()
                return

        # Horizontal: Stay at right edge when navigating right from rightmost position
        # Row 0 has buttons at col 0 and 1 (rightmost is col 1)
        # Row 1 has button only at col 0 (rightmost is col 0)
        if col_delta > 0 and ((row == 0 and col == 1) or (row == 1 and col == 0)):
            # Already at rightmost position for this row - do nothing
            return

        # Focus the new button within the grid
        new_button_id = self.POSITION_TO_BUTTON.get((new_row, new_col))
        if new_button_id:
            with contextlib.suppress(Exception):
                new_button = self.query_one(f"#{new_button_id}", Button)
                new_button.focus()
                # Track this as the last focused button
                ConfigPanel._last_focused_button = new_button_id

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

    def on_key(self, event: Key) -> None:
        """Handle key events for navigation with scroll support.

        Explicitly handles up/down navigation to prevent the VerticalScroll
        container from intercepting arrow keys and to ensure our custom 2D
        grid navigation runs properly.

        Args:
            event: The key event
        """
        focused = self.screen.focused
        if not focused or not isinstance(focused, Button):
            return

        # Check if we're in the config grid
        button_id = focused.id
        if button_id not in self.GRID_POSITIONS:
            return

        # In config grid - explicitly call our navigation actions
        # to prevent VerticalScroll from handling the keys
        if event.key == "up":
            self.action_navigate_up()
            event.prevent_default()
            event.stop()
        elif event.key == "down":
            self.action_navigate_down()
            event.prevent_default()
            event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses and navigate to screens."""
        from claudefig.services import config_service, file_instance_service

        button_id = event.button.id

        # Track this button as the last focused for when we return
        if button_id in self.GRID_POSITIONS:
            ConfigPanel._last_focused_button = button_id

        # Load instances_dict for screens
        instances_data = config_service.get_file_instances(self.config_data)
        instances_dict, _ = file_instance_service.load_instances_from_config(
            instances_data
        )

        if button_id == "btn-overview":
            self.app.push_screen(
                OverviewScreen(
                    config_data=self.config_data,
                    config_repo=self.config_repo,
                    instances_dict=instances_dict,
                )
            )
        elif button_id == "btn-settings":
            self.app.push_screen(
                ProjectSettingsScreen(
                    config_data=self.config_data,
                    config_repo=self.config_repo,
                    instances_dict=instances_dict,
                )
            )
        elif button_id == "btn-file-instances":
            self.app.push_screen(
                FileInstancesScreen(
                    config_data=self.config_data,
                    config_repo=self.config_repo,
                    instances_dict=instances_dict,
                )
            )
