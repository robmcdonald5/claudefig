"""Project overview screen showing stats and quick actions."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from claudefig.config import Config
from claudefig.file_instance_manager import FileInstanceManager


class OverviewScreen(Screen):
    """Screen displaying project overview with stats and quick actions."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(
        self,
        config: Config,
        instance_manager: FileInstanceManager,
        **kwargs,
    ) -> None:
        """Initialize overview screen.

        Args:
            config: Configuration object
            instance_manager: FileInstanceManager for stats
        """
        super().__init__(**kwargs)
        self.config = config
        self.instance_manager = instance_manager

    def compose(self) -> ComposeResult:
        """Compose the overview screen."""
        with Container(id="overview-screen"):
            yield Label("PROJECT OVERVIEW", classes="screen-title")

            # Stats section
            with Vertical(classes="overview-section"):
                yield Label("Configuration", classes="section-header")

                with Vertical(classes="stats-container"):
                    yield Static(
                        f"Config Path: {self.config.config_path}",
                        classes="stat-line"
                    )
                    yield Static(
                        f"Schema Version: {self.config.get('claudefig.schema_version', 'unknown')}",
                        classes="stat-line"
                    )

            # Instance stats section
            with Vertical(classes="overview-section"):
                yield Label("File Instances", classes="section-header")

                instances = self.instance_manager.list_instances()
                total = len(instances)
                enabled = sum(1 for i in instances if i.enabled)
                disabled = total - enabled

                with Vertical(classes="stats-container"):
                    yield Static(f"Total Instances: {total}", classes="stat-line")
                    yield Static(f"Enabled: {enabled}", classes="stat-line")
                    yield Static(f"Disabled: {disabled}", classes="stat-line")

            # Quick actions section
            with Vertical(classes="overview-section"):
                yield Label("Quick Actions", classes="section-header")

                with Horizontal(classes="action-buttons"):
                    yield Button("Initialize Project", id="btn-initialize", variant="primary")
                    yield Button("View All Instances", id="btn-view-instances")

            # Back button
            with Container(classes="screen-footer"):
                yield Button("← Back to Config Menu", id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-initialize":
            # TODO: Trigger initialization
            self.notify("Initialize project feature coming soon!", severity="information")
        elif event.button.id == "btn-view-instances":
            # Navigate to File Instances screen
            from claudefig.tui.screens.file_instances import FileInstancesScreen
            from claudefig.preset_manager import PresetManager

            preset_manager = PresetManager()
            self.app.push_screen(
                FileInstancesScreen(
                    config=self.config,
                    instance_manager=self.instance_manager,
                    preset_manager=preset_manager,
                )
            )
