"""Core files screen for managing single-instance file types."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label

from claudefig.config import Config
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileType
from claudefig.preset_manager import PresetManager
from claudefig.tui.widgets.compact_single_instance import CompactSingleInstanceControl


class CoreFilesScreen(Screen):
    """Screen for managing single-instance core files."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(
        self,
        config: Config,
        instance_manager: FileInstanceManager,
        preset_manager: PresetManager,
        **kwargs,
    ) -> None:
        """Initialize core files screen.

        Args:
            config: Configuration object
            instance_manager: FileInstanceManager for CRUD operations
            preset_manager: PresetManager for preset info
        """
        super().__init__(**kwargs)
        self.config = config
        self.instance_manager = instance_manager
        self.preset_manager = preset_manager

    def compose(self) -> ComposeResult:
        """Compose the core files screen."""
        with Container(id="core-files-screen"):
            yield Label("CORE FILES", classes="screen-title")

            yield Label(
                "Single-instance files that can only have one configuration per project.",
                classes="screen-description"
            )

            # Get single-instance file types
            single_instance_types = [
                FileType.SETTINGS_JSON,
                FileType.SETTINGS_LOCAL_JSON,
                FileType.STATUSLINE,
            ]

            # Display controls for each single-instance type
            with Vertical(classes="core-files-list"):
                for file_type in single_instance_types:
                    # Find existing instance for this file type
                    instances = [
                        inst for inst in self.instance_manager.list_instances()
                        if inst.type == file_type
                    ]
                    instance = instances[0] if instances else None

                    # Add compact control
                    yield CompactSingleInstanceControl(
                        file_type=file_type,
                        instance=instance,
                    )

            # Back button
            with Container(classes="screen-footer"):
                yield Button("← Back to Config Menu", id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
