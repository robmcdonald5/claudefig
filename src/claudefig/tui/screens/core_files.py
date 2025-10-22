"""Core files screen for managing single-instance file types."""

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label

from claudefig.config import Config
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileType
from claudefig.preset_manager import PresetManager
from claudefig.tui.base import BackButtonMixin, FileInstanceMixin, ScrollNavigationMixin
from claudefig.tui.widgets.compact_single_instance import CompactSingleInstanceControl


class CoreFilesScreen(Screen, BackButtonMixin, FileInstanceMixin, ScrollNavigationMixin):
    """Screen for managing single-instance core files."""

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("backspace", "pop_screen", "Back"),
        ("up", "focus_previous", "Focus Previous"),
        ("down", "focus_next", "Focus Next"),
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
        # can_focus=False prevents the container from being in the focus chain
        # while still allowing it to be scrolled programmatically
        with VerticalScroll(id="core-files-screen", can_focus=False):
            yield Label("CORE FILES", classes="screen-title")

            yield Label(
                "Single-instance files that can only have one configuration per project.",
                classes="screen-description",
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
                        inst
                        for inst in self.instance_manager.list_instances()
                        if inst.type == file_type
                    ]
                    instance = instances[0] if instances else None

                    # Add compact control
                    yield CompactSingleInstanceControl(
                        file_type=file_type,
                        instance=instance,
                        preset_manager=self.preset_manager,
                    )

            # Back button
            yield from self.compose_back_button()

    def action_pop_screen(self) -> None:
        """Pop the current screen to return to config menu."""
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        # Check if back button was pressed and return early if handled
        if self.handle_back_button(event):
            return

    def on_compact_single_instance_control_toggle_changed(
        self, event: CompactSingleInstanceControl.ToggleChanged
    ) -> None:
        """Handle toggle changes - create or disable instance."""
        file_type = event.file_type
        enabled = event.enabled

        # Find existing instance
        instances = [
            inst
            for inst in self.instance_manager.list_instances()
            if inst.type == file_type
        ]
        instance = instances[0] if instances else None

        if enabled and not instance:
            # Create new instance with default template
            # For template directory types, use "default" as the template name
            # For other types, use the first available preset
            from claudefig.models import FileInstance

            if file_type.template_directory:
                # Use simple template name
                default_template = "default"
            else:
                # Use preset system
                presets = self.preset_manager.list_presets(file_type=file_type)
                default_template = presets[0].id if presets else "default"

            new_instance = FileInstance(
                id=f"{file_type.value}-default",
                type=file_type,
                preset=default_template,
                path=file_type.default_path,
                enabled=True,
            )
            self.instance_manager.add_instance(new_instance)

            # Sync to config and save
            self.sync_instances_to_config()
        elif instance:
            # Update enabled status
            instance.enabled = enabled
            self.instance_manager.update_instance(instance)

            # Sync to config and save
            self.sync_instances_to_config()

    def on_compact_single_instance_control_preset_changed(
        self, event: CompactSingleInstanceControl.PresetChanged
    ) -> None:
        """Handle preset selection changes."""
        file_type = event.file_type
        preset_id = event.preset_id

        # Find existing instance
        instances = [
            inst
            for inst in self.instance_manager.list_instances()
            if inst.type == file_type
        ]
        instance = instances[0] if instances else None

        if instance:
            # Update preset
            instance.preset = preset_id
            self.instance_manager.update_instance(instance)

            # Sync to config and save
            self.sync_instances_to_config()
