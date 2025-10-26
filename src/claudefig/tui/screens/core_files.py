"""Core files screen for managing single-instance file types."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.events import Key
from textual.widgets import Button, Label

from claudefig.models import FileInstance, FileType
from claudefig.preset_manager import PresetManager
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.repositories.preset_repository import TomlPresetRepository
from claudefig.services import config_service, file_instance_service
from claudefig.tui.base import BaseScreen
from claudefig.tui.widgets.compact_single_instance import CompactSingleInstanceControl


class CoreFilesScreen(BaseScreen):
    """Screen for managing single-instance core files.

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
        """Initialize core files screen.

        Args:
            config_data: Configuration dictionary
            config_repo: Configuration repository for saving
            instances_dict: Dictionary of file instances (id -> FileInstance)
        """
        super().__init__(**kwargs)
        self.config_data = config_data
        self.config_repo = config_repo
        self.instances_dict = instances_dict
        self.preset_repo = TomlPresetRepository()
        self.preset_manager = PresetManager()  # For CompactSingleInstanceControl

    def sync_instances_to_config(self) -> None:
        """Sync instances dict to config and save to disk.

        This implements the state synchronization pattern:
        1. Modify instances_dict (done by caller)
        2. Sync instances → config (done here)
        3. Sync config → disk (done here)
        """
        # Save instances to config format
        instances_data = file_instance_service.save_instances_to_config(
            self.instances_dict
        )
        config_service.set_file_instances(self.config_data, instances_data)

        # Save config to disk
        config_service.save_config(self.config_data, self.config_repo)

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
                    instances = file_instance_service.get_instances_by_type(
                        self.instances_dict, file_type
                    )
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

    def on_key(self, event: Key) -> None:
        """Handle key events for navigation.

        Explicitly calls navigation actions to ensure proper scrolling behavior
        when CompactSingleInstanceControl widgets are present.

        Args:
            event: The key event
        """
        # Explicitly handle up/down navigation to ensure ScrollNavigationMixin
        # methods are called directly, bypassing any widget-level key handlers
        # that might interfere with proper scroll behavior
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

    def on_compact_single_instance_control_toggle_changed(
        self, event: CompactSingleInstanceControl.ToggleChanged
    ) -> None:
        """Handle toggle changes - create or disable instance."""
        file_type = event.file_type
        enabled = event.enabled

        # Find existing instance
        instances = file_instance_service.get_instances_by_type(
            self.instances_dict, file_type
        )
        instance = instances[0] if instances else None

        if enabled and not instance:
            # Create new instance with default template
            # For template directory types, use "default" as the template name
            # For other types, use the first available preset
            if file_type.template_directory:
                # Use simple template name
                default_template = "default"
            else:
                # Use preset system
                presets = self.preset_repo.list_presets(file_type=file_type.value)
                default_template = presets[0].id if presets else "default"

            new_instance = FileInstance(
                id=f"{file_type.value}-default",
                type=file_type,
                preset=default_template,
                path=file_type.default_path,
                enabled=True,
            )
            file_instance_service.add_instance(
                self.instances_dict,
                new_instance,
                self.preset_repo,
                self.config_repo.config_path.parent,
            )

            # Sync to config and save
            self.sync_instances_to_config()
        elif instance:
            # Update enabled status
            instance.enabled = enabled
            file_instance_service.update_instance(
                self.instances_dict,
                instance,
                self.preset_repo,
                self.config_repo.config_path.parent,
            )

            # Sync to config and save
            self.sync_instances_to_config()

    def on_compact_single_instance_control_preset_changed(
        self, event: CompactSingleInstanceControl.PresetChanged
    ) -> None:
        """Handle preset selection changes."""
        file_type = event.file_type
        preset_id = event.preset_id

        # Find existing instance
        instances = file_instance_service.get_instances_by_type(
            self.instances_dict, file_type
        )
        instance = instances[0] if instances else None

        if instance:
            # Update preset
            instance.preset = preset_id
            file_instance_service.update_instance(
                self.instances_dict,
                instance,
                self.preset_repo,
                self.config_repo.config_path.parent,
            )

            # Sync to config and save
            self.sync_instances_to_config()
