"""File instances screen for managing multi-instance file types."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, TabbedContent, TabPane

from claudefig.config import Config
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileType
from claudefig.preset_manager import PresetManager
from claudefig.tui.widgets.file_instance_item import FileInstanceItem


class FileInstancesScreen(Screen):
    """Screen for managing multi-instance file types with tabs."""

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
            with Container(classes="screen-footer"):
                yield Button("← Back to Config Menu", id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id and event.button.id.startswith("btn-add-"):
            # Extract file type from button id
            file_type_value = event.button.id.replace("btn-add-", "")
            try:
                file_type = FileType(file_type_value)
                self._show_add_instance_dialog(file_type)
            except ValueError:
                self.notify(f"Unknown file type: {file_type_value}", severity="error")

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
                    self.config.add_file_instance(instance.to_dict())
                    self.config.save()
                    self.notify(f"Added {instance.type.display_name} instance", severity="information")
                    # Refresh screen
                    self.app.pop_screen()
                    self.app.push_screen(
                        FileInstancesScreen(
                            config=self.config,
                            instance_manager=self.instance_manager,
                            preset_manager=self.preset_manager,
                        )
                    )
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
