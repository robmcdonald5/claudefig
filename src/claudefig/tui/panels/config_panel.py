"""Config panel - main menu for configuration options."""

from textual.app import ComposeResult
from textual.containers import Container, Grid
from textual.widgets import Button, Label

from claudefig.config import Config
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.preset_manager import PresetManager
from claudefig.tui.screens import (
    CoreFilesScreen,
    FileInstancesScreen,
    GeneralConfigScreen,
    OverviewScreen,
    ProjectSettingsScreen,
)


class ConfigPanel(Container):
    """Main configuration menu panel."""

    # Bindings for 2D grid navigation
    BINDINGS = [
        ("up", "navigate_up", "Navigate up"),
        ("down", "navigate_down", "Navigate down"),
        ("left", "navigate_left", "Navigate left"),
        ("right", "navigate_right", "Navigate right"),
    ]

    # 2D grid navigation map (button_id -> (row, col))
    GRID_POSITIONS = {
        "btn-overview": (0, 0),
        "btn-settings": (0, 1),
        "btn-core-files": (1, 0),
        "btn-file-instances": (1, 1),
        "btn-general-config": (2, 0),
    }

    # Reverse map (row, col) -> button_id
    POSITION_TO_BUTTON = {v: k for k, v in GRID_POSITIONS.items()}

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize config panel.

        Args:
            config: Config object for current project
        """
        super().__init__(**kwargs)
        self.config = config
        self.preset_manager = PresetManager()
        self.instance_manager = FileInstanceManager(self.preset_manager)

    def compose(self) -> ComposeResult:
        """Compose the config menu panel."""
        # Check if config exists
        if not self.config.config_path or not self.config.config_path.exists():
            yield Label(
                "No .claudefig.toml found in current directory.\n\n"
                "Go to 'Presets' panel and use a preset to create a config.",
                classes="placeholder",
            )
            return

        # Load file instances
        instances_data = self.config.get_file_instances()
        if instances_data:
            self.instance_manager.load_instances(instances_data)

        # Header
        yield Label("Configuration Menu", classes="panel-title")

        # Summary info
        enabled_count = sum(
            1 for i in self.instance_manager.list_instances() if i.enabled
        )
        total_count = len(self.instance_manager.list_instances())
        config_path_str = str(self.config.config_path)
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
            yield Button(
                "General Config\nEdit any config setting",
                id="btn-general-config",
                classes="config-menu-button",
            )

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
        if row_delta > 0 and row == 2:
            # Already at bottom row (row 2) - do nothing
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
        button_id = event.button.id

        if button_id == "btn-overview":
            self.app.push_screen(
                OverviewScreen(
                    config=self.config,
                    instance_manager=self.instance_manager,
                )
            )
        elif button_id == "btn-settings":
            self.app.push_screen(ProjectSettingsScreen(config=self.config))
        elif button_id == "btn-core-files":
            self.app.push_screen(
                CoreFilesScreen(
                    config=self.config,
                    instance_manager=self.instance_manager,
                    preset_manager=self.preset_manager,
                )
            )
        elif button_id == "btn-file-instances":
            self.app.push_screen(
                FileInstancesScreen(
                    config=self.config,
                    instance_manager=self.instance_manager,
                    preset_manager=self.preset_manager,
                )
            )
        elif button_id == "btn-general-config":
            self.app.push_screen(GeneralConfigScreen(config=self.config))
