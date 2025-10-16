"""File instances screen for managing multi-instance file types."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, TabbedContent, TabPane

from claudefig.config import Config
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileType
from claudefig.preset_manager import PresetManager
from claudefig.tui.base import BackButtonMixin, FileInstanceMixin
from claudefig.tui.widgets.file_instance_item import FileInstanceItem


class FileInstancesScreen(Screen, BackButtonMixin, FileInstanceMixin):
    """Screen for managing multi-instance file types with tabs."""

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("backspace", "pop_screen", "Back"),
    ]

    def __init__(
        self,
        config: Config,
        instance_manager: FileInstanceManager,
        preset_manager: PresetManager,
        **kwargs,
    ) -> None:
        """Initialize file instances screen.

        Args:
            config: Configuration object
            instance_manager: FileInstanceManager for CRUD operations
            preset_manager: PresetManager for preset info
        """
        super().__init__(**kwargs)
        self.config = config
        self.instance_manager = instance_manager
        self.preset_manager = preset_manager

    def action_pop_screen(self) -> None:
        """Pop the current screen to return to config menu."""
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        """Compose the file instances screen."""
        with Container(id="file-instances-screen"):
            yield Label("FILE INSTANCES", classes="screen-title")

            yield Label(
                "Multi-instance files that can have multiple configurations per project.",
                classes="screen-description"
            )

            # Get multi-instance file types
            multi_instance_types = [
                FileType.CLAUDE_MD,
                FileType.GITIGNORE,
                FileType.COMMANDS,
                FileType.AGENTS,
                FileType.HOOKS,
                FileType.OUTPUT_STYLES,
                FileType.MCP,
            ]

            # Create tabbed content
            with TabbedContent(id="file-instances-tabs"):
                for file_type in multi_instance_types:
                    with TabPane(file_type.display_name, id=f"tab-{file_type.value}"):
                        # Get instances for this file type
                        instances = [
                            inst for inst in self.instance_manager.list_instances()
                            if inst.type == file_type
                        ]

                        # Action buttons
                        with Horizontal(classes="tab-actions"):
                            yield Button(
                                f"+ Add {file_type.display_name}",
                                id=f"btn-add-{file_type.value}",
                                variant="primary"
                            )

                        # Display instances
                        if instances:
                            with Vertical(classes="instance-list"):
                                for instance in instances:
                                    yield FileInstanceItem(
                                        instance=instance,
                                    )
                        else:
                            yield Label(
                                f"No {file_type.display_name} instances configured.",
                                classes="empty-message"
                            )

            # Back button
            yield from self.compose_back_button()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        # Handle back button first
        if self.handle_back_button(event):
            return

        button_id = event.button.id
        if not button_id:
            return

        if button_id.startswith("btn-add-"):
            # Extract file type from button id
            file_type_value = button_id.replace("btn-add-", "")
            try:
                file_type = FileType(file_type_value)
                self._show_add_instance_dialog(file_type)
            except ValueError:
                self.notify(f"Unknown file type: {file_type_value}", severity="error")
        elif button_id.startswith("edit-"):
            # Edit instance
            instance_id = button_id.replace("edit-", "")
            self._show_edit_instance_dialog(instance_id)
        elif button_id.startswith("remove-"):
            # Remove instance
            instance_id = button_id.replace("remove-", "")
            self._remove_instance(instance_id)
        elif button_id.startswith("toggle-"):
            # Toggle instance enabled/disabled
            instance_id = button_id.replace("toggle-", "")
            self._toggle_instance(instance_id)

    def _show_add_instance_dialog(self, file_type: FileType) -> None:
        """Show the add instance dialog for a file type.

        Args:
            file_type: Type of file to add
        """
        from claudefig.tui.screens.file_instance_edit import FileInstanceEditScreen

        def handle_result(result: dict | None) -> None:
            """Handle dialog result."""
            if result and result.get("action") == "save":
                instance = result["instance"]
                try:
                    self.instance_manager.add_instance(instance)
                    # Sync to config and save
                    self.sync_instances_to_config()
                    self.notify(f"Added {instance.type.display_name} instance", severity="information")
                    # Refresh screen to show updated data
                    self.refresh(recompose=True)
                except Exception as e:
                    self.notify(f"Error adding instance: {e}", severity="error")

        self.app.push_screen(
            FileInstanceEditScreen(
                instance_manager=self.instance_manager,
                preset_manager=self.preset_manager,
                file_type=file_type,
            ),
            callback=handle_result
        )

    def _show_edit_instance_dialog(self, instance_id: str) -> None:
        """Show the edit instance dialog for an existing instance.

        Args:
            instance_id: ID of the instance to edit
        """
        from claudefig.tui.screens.file_instance_edit import FileInstanceEditScreen

        # Get the instance
        instance = self.instance_manager.get_instance(instance_id)
        if not instance:
            self.notify(f"Instance not found: {instance_id}", severity="error")
            return

        def handle_result(result: dict | None) -> None:
            """Handle dialog result."""
            if result and result.get("action") == "save":
                updated_instance = result["instance"]
                try:
                    self.instance_manager.update_instance(updated_instance)
                    # Sync to config and save
                    self.sync_instances_to_config()
                    self.notify(f"Updated {updated_instance.type.display_name} instance", severity="information")
                    # Refresh screen to show updated data
                    self.refresh(recompose=True)
                except Exception as e:
                    self.notify(f"Error updating instance: {e}", severity="error")

        self.app.push_screen(
            FileInstanceEditScreen(
                instance_manager=self.instance_manager,
                preset_manager=self.preset_manager,
                instance=instance,
            ),
            callback=handle_result
        )

    def _remove_instance(self, instance_id: str) -> None:
        """Remove a file instance.

        Args:
            instance_id: ID of the instance to remove
        """
        # Get the instance for display name
        instance = self.instance_manager.get_instance(instance_id)
        if not instance:
            self.notify(f"Instance not found: {instance_id}", severity="error")
            return

        # Remove from manager
        if self.instance_manager.remove_instance(instance_id):
            # Sync to config and save
            self.sync_instances_to_config()
            self.notify(f"Removed {instance.type.display_name} instance", severity="information")
            # Refresh screen to show updated data
            self.refresh(recompose=True)
        else:
            self.notify(f"Failed to remove instance: {instance_id}", severity="error")

    def _toggle_instance(self, instance_id: str) -> None:
        """Toggle an instance's enabled status.

        Args:
            instance_id: ID of the instance to toggle
        """
        instance = self.instance_manager.get_instance(instance_id)
        if not instance:
            self.notify(f"Instance not found: {instance_id}", severity="error")
            return

        # Toggle enabled status
        instance.enabled = not instance.enabled
        self.instance_manager.update_instance(instance)

        # Sync to config and save
        self.sync_instances_to_config()

        status = "enabled" if instance.enabled else "disabled"
        self.notify(f"{instance.type.display_name} instance {status}", severity="information")

        # Refresh screen to show updated data
        self.refresh(recompose=True)
