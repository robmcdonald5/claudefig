"""File instances screen for managing multi-instance file types."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Button, Label, Select, TabbedContent, TabPane

from claudefig.config import Config
from claudefig.error_messages import ErrorMessages
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileType
from claudefig.preset_manager import PresetManager
from claudefig.tui.base import (
    BackButtonMixin,
    FileInstanceMixin,
    ScrollNavigationMixin,
    SystemUtilityMixin,
)
from claudefig.tui.widgets.file_instance_item import FileInstanceItem
from claudefig.user_config import get_components_dir


class FileInstancesScreen(
    Screen,
    BackButtonMixin,
    FileInstanceMixin,
    ScrollNavigationMixin,
    SystemUtilityMixin,
):
    """Screen for managing multi-instance file types with tabs."""

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

    def on_key(self, event: Key) -> None:
        """Handle key events for Select navigation.

        Prevents up/down arrows from opening component Select dropdowns.
        Only Enter opens dropdowns, backspace/esc closes them.
        Adds left/right navigation for horizontal button groups.

        Args:
            event: The key event
        """
        focused = self.focused

        # If a component Select is focused and prevent up/down from opening the dropdown
        if (
            isinstance(focused, Select)
            and focused.id
            and focused.id.startswith("select-add-")
            and event.key in ("up", "down")
            and not focused.expanded
        ):
            # Don't let Select handle it - let it bubble for navigation
            event.prevent_default()
            # Manually trigger navigation
            if event.key == "up":
                self.action_focus_previous()
            else:
                self.action_focus_next()
            event.stop()

        # Handle left/right navigation for horizontal groups
        if (
            event.key in ("left", "right")
            and focused
            and self._handle_horizontal_navigation(event.key, focused)
        ):
            event.prevent_default()
            event.stop()

    def _handle_horizontal_navigation(self, key: str, focused) -> bool:
        """Handle left/right navigation within horizontal groups.

        Supports navigation in:
        1. Tab actions (Select dropdown <-> Open Folder button)
        2. Instance actions (Edit <-> Remove <-> Toggle buttons per instance)

        Args:
            key: Either "left" or "right"
            focused: The currently focused widget

        Returns:
            True if navigation was handled, False otherwise
        """
        from textual.containers import Horizontal

        # Find the horizontal parent container
        horizontal_parent = None
        current = focused.parent

        # Walk up the tree to find a Horizontal container
        while current:
            # Check if it's a Horizontal navigation group we care about
            if isinstance(current, Horizontal) and hasattr(current, "classes") and (
                "tab-actions" in current.classes
                or "instance-actions" in current.classes
            ):
                horizontal_parent = current
                break
            current = current.parent

        if not horizontal_parent:
            return False

        # Get all focusable widgets in this horizontal container
        focusable_widgets = [
            widget
            for widget in horizontal_parent.query("Select, Button")
            if widget.can_focus and widget.display and not widget.disabled
        ]

        if len(focusable_widgets) <= 1:
            return False

        try:
            current_index = focusable_widgets.index(focused)
        except ValueError:
            return False

        # Navigate left or right
        if key == "left":
            new_index = current_index - 1
            if new_index >= 0:
                focusable_widgets[new_index].focus()
                return True
        elif key == "right":
            new_index = current_index + 1
            if new_index < len(focusable_widgets):
                focusable_widgets[new_index].focus()
                return True

        return False

    def compose(self) -> ComposeResult:
        """Compose the file instances screen."""
        # can_focus=False prevents the container from being in the focus chain
        # while still allowing it to be scrolled programmatically
        with VerticalScroll(id="file-instances-screen", can_focus=False):
            yield Label("FILE INSTANCES", classes="screen-title")

            yield Label(
                "Multi-instance files that can have multiple configurations per project.",
                classes="screen-description",
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
                            inst
                            for inst in self.instance_manager.list_instances()
                            if inst.type == file_type
                        ]

                        # Component selector
                        with Horizontal(classes="tab-actions"):
                            # Get available components for this file type
                            components = self.instance_manager.list_components(
                                file_type
                            )

                            if components:
                                # Build options: (display_name, component_name)
                                component_options = [
                                    (f"+ Add {name}", name) for name, _ in components
                                ]

                                yield Select(
                                    options=component_options,
                                    prompt="Select a component to add...",
                                    id=f"select-add-{file_type.value}",
                                    allow_blank=True,
                                    classes="component-select",
                                )
                            else:
                                # No components available - show info message
                                yield Label(
                                    f"No {file_type.display_name} components found.",
                                    classes="empty-message component-select",
                                )

                            # Always show button to open component directory
                            yield Button(
                                "Open Folder",
                                id=f"btn-open-components-{file_type.value}",
                                classes="component-folder-btn",
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
                                classes="empty-message",
                            )

            # Back button
            yield from self.compose_back_button()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle component selection."""
        select_id = event.select.id
        if not select_id or not select_id.startswith("select-add-"):
            return

        # Extract file type from select id
        file_type_value = select_id.replace("select-add-", "")
        component_name = event.value

        # Ignore if blank/prompt selected or not a string
        if not component_name or not isinstance(component_name, str):
            return

        try:
            file_type = FileType(file_type_value)
            self._add_component_instance(file_type, component_name)

            # Reset select back to prompt
            event.select.value = Select.BLANK

        except ValueError:
            valid_types = [ft.value for ft in FileType]
            self.notify(
                ErrorMessages.invalid_type("file type", file_type_value, valid_types),
                severity="error",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        # Handle back button first
        if self.handle_back_button(event):
            return

        button_id = event.button.id
        if not button_id:
            return

        if button_id.startswith("btn-open-components-"):
            # Open component directory in system file explorer
            file_type_value = button_id.replace("btn-open-components-", "")
            try:
                file_type = FileType(file_type_value)
                self._open_component_directory(file_type)
            except ValueError:
                self.notify(f"Invalid file type: {file_type_value}", severity="error")
        elif button_id.startswith("edit-"):
            # Open component file in system editor
            instance_id = button_id.replace("edit-", "")
            self._open_component_file(instance_id)
        elif button_id.startswith("path-"):
            # Show file path selector
            instance_id = button_id.replace("path-", "")
            self._show_file_path_selector(instance_id)
        elif button_id.startswith("remove-"):
            # Remove instance
            instance_id = button_id.replace("remove-", "")
            self._remove_instance(instance_id)
        elif button_id.startswith("toggle-"):
            # Toggle instance enabled/disabled
            instance_id = button_id.replace("toggle-", "")
            self._toggle_instance(instance_id)

    def _add_component_instance(self, file_type: FileType, component_name: str) -> None:
        """Load a component and add it as a file instance.

        Args:
            file_type: Type of file
            component_name: Name of the component to load
        """
        try:
            # Check if this component has already been added
            existing_instances = self.instance_manager.list_instances()

            for existing in existing_instances:
                # Skip if different type
                if existing.type != file_type:
                    continue

                # For CLAUDE.md and .gitignore (folder-based), check folder name
                if file_type in (FileType.CLAUDE_MD, FileType.GITIGNORE):
                    component_folder = existing.variables.get("component_folder", "")
                    if component_folder:
                        # Extract the component folder name from the path
                        folder_name = Path(component_folder).name
                        if folder_name == component_name:
                            self.notify(
                                f"Component '{component_name}' has already been added",
                                severity="warning",
                            )
                            return
                else:
                    # For other types, check component file name (stem without extension)
                    component_file = existing.variables.get("component_file", "")
                    if component_file:
                        file_stem = Path(component_file).stem
                        if file_stem == component_name:
                            self.notify(
                                f"Component '{component_name}' has already been added",
                                severity="warning",
                            )
                            return

            # Load component from library
            instance = self.instance_manager.load_component(file_type, component_name)

            if not instance:
                self.notify(f"Component '{component_name}' not found", severity="error")
                return

            # Store the component name in variables for later reference
            # This is needed to reconstruct paths if component_folder gets lost
            instance.variables = instance.variables or {}
            instance.variables["component_name"] = component_name

            # Generate new ID for this project
            preset_name = (
                instance.preset.split(":")[-1]
                if ":" in instance.preset
                else instance.preset
            )
            instance.id = self.instance_manager.generate_instance_id(
                file_type, preset_name, instance.path
            )

            # Add instance
            result = self.instance_manager.add_instance(instance)

            if result.valid:
                # Sync to config and save
                self.sync_instances_to_config()
                self.notify(
                    f"Added {instance.type.display_name} from component '{component_name}'",
                    severity="information",
                )
                # Refresh screen to add the new widget
                # Note: We still need refresh(recompose=True) here because we're adding a new widget
                self.refresh(recompose=True)
            else:
                # Show validation errors
                error_msg = (
                    "\n".join(result.errors) if result.errors else "Validation failed"
                )
                self.notify(error_msg, severity="error")

        except Exception as e:
            self.notify(
                ErrorMessages.operation_failed("adding component", str(e)),
                severity="error",
            )

    def _open_component_file(self, instance_id: str) -> None:
        """Open the component file in the system editor.

        Args:
            instance_id: ID of the instance to edit
        """
        # Get the instance
        instance = self.instance_manager.get_instance(instance_id)
        if not instance:
            self.notify(
                ErrorMessages.not_found("file instance", instance_id), severity="error"
            )
            return

        # Determine the file to open based on component type
        file_to_open = None

        if instance.type in (FileType.CLAUDE_MD, FileType.GITIGNORE):
            # For folder-based components, find the actual file in the folder
            component_folder = instance.variables.get("component_folder")

            # If component_folder is missing, try to find it from component_name variable
            if not component_folder:
                component_name = instance.variables.get("component_name")

                # If component_name is also missing, try to extract from preset
                # Preset format: "claude_md:default" or "gitignore:standard"
                if not component_name and ":" in instance.preset:
                    component_name = instance.preset.split(":")[-1]

                if component_name:
                    # Reconstruct the component folder path
                    components_dir = get_components_dir()
                    type_dir = components_dir / instance.type.value
                    component_folder = str(type_dir / component_name)
                    # Update the instance to cache both values for next time
                    instance.variables = instance.variables or {}
                    instance.variables["component_name"] = component_name
                    instance.variables["component_folder"] = component_folder
                    self.instance_manager.update_instance(instance)
                    self.sync_instances_to_config()
                else:
                    self.notify(
                        f"Cannot determine component folder - no component_name or component_folder in variables, and cannot extract from preset '{instance.preset}'. Available: {list(instance.variables.keys())}",
                        severity="error",
                    )
                    return

            folder_path = Path(component_folder)
            if not folder_path.exists():
                self.notify(
                    f"Component folder does not exist: {folder_path}",
                    severity="error",
                )
                return

            if not folder_path.is_dir():
                self.notify(
                    f"Component folder is not a directory: {folder_path}",
                    severity="error",
                )
                return

            # Find the actual CLAUDE.md or .gitignore file in the folder
            actual_filename = Path(instance.path).name
            file_to_open = folder_path / actual_filename

            if not file_to_open.exists():
                self.notify(
                    f"Component file does not exist: {file_to_open}",
                    severity="error",
                )
                return
        else:
            # For other types, use component_file
            component_file = instance.variables.get("component_file")
            if not component_file:
                self.notify(
                    f"No component file found in variables. Available: {list(instance.variables.keys())}",
                    severity="error",
                )
                return

            file_to_open = Path(component_file)

            if not file_to_open.exists():
                self.notify(
                    f"Component file does not exist: {file_to_open}",
                    severity="error",
                )
                return

        # Open file using SystemUtilityMixin method
        self.open_file_in_editor(file_to_open)

    def _show_file_path_selector(self, instance_id: str) -> None:
        """Open OS file picker to select path for CLAUDE.md or .gitignore instances.

        Args:
            instance_id: ID of the instance to edit path for
        """
        import tkinter as tk
        from tkinter import filedialog

        # Get the instance
        instance = self.instance_manager.get_instance(instance_id)
        if not instance:
            self.notify(
                ErrorMessages.not_found("file instance", instance_id), severity="error"
            )
            return

        try:
            # Create a hidden tkinter root window
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            root.attributes("-topmost", True)  # Bring dialog to front

            # Get the project directory as the initial directory
            # The project directory is the parent of the config file
            if self.config.config_path:
                project_dir = self.config.config_path.parent.resolve()
            else:
                # Fallback to current working directory if no config path
                project_dir = Path.cwd()

            # Determine the filename based on file type
            default_filename = Path(instance.path).name

            # Set initial directory to the directory containing the current path
            current_full_path = project_dir / instance.path
            if current_full_path.parent.exists():
                initial_dir = str(current_full_path.parent)
            else:
                initial_dir = str(project_dir)

            # Open file dialog - use askopenfilename to avoid overwrite warnings
            # since we're just selecting a path, not actually writing to the file
            # Users can select existing file OR type a new path
            selected_path = filedialog.askopenfilename(
                parent=root,
                title=f"Select or type location for {instance.type.display_name}",
                initialdir=initial_dir,
                filetypes=[
                    (f"{default_filename}", default_filename),
                    ("All files", "*.*"),
                ],
            )

            # Clean up tkinter
            root.destroy()

            if selected_path:
                # Convert to path relative to project directory
                selected_path = Path(selected_path)
                try:
                    # Try to make it relative to project dir
                    relative_path = selected_path.relative_to(project_dir)
                    new_path = str(relative_path)
                except ValueError:
                    # If path is outside project, use absolute path
                    new_path = str(selected_path)

                # Update the instance path
                instance.path = new_path
                self.instance_manager.update_instance(instance)

                # Sync to config and save
                self.sync_instances_to_config()
                self.notify(
                    f"Updated path for {instance.type.display_name} instance",
                    severity="information",
                )

                # Update the widget's reactive attribute - triggers watch method for smooth update
                for item in self.query(FileInstanceItem):
                    if item.instance_id == instance_id:
                        item.file_path = new_path
                        break

        except Exception as e:
            self.notify(
                ErrorMessages.operation_failed("selecting path", str(e)),
                severity="error",
            )

    def _remove_instance(self, instance_id: str) -> None:
        """Remove a file instance.

        Args:
            instance_id: ID of the instance to remove
        """
        # Get the instance for display name
        instance = self.instance_manager.get_instance(instance_id)
        if not instance:
            self.notify(
                ErrorMessages.not_found("file instance", instance_id), severity="error"
            )
            return

        # Remove from manager
        if self.instance_manager.remove_instance(instance_id):
            # Sync to config and save
            self.sync_instances_to_config()
            self.notify(
                f"Removed {instance.type.display_name} instance", severity="information"
            )
            # Refresh screen to remove the widget - this is necessary for removal
            # Note: We still need refresh(recompose=True) here because we're removing a widget
            self.refresh(recompose=True)
        else:
            self.notify(
                ErrorMessages.failed_to_perform("remove", "file instance", instance_id),
                severity="error",
            )

    def _toggle_instance(self, instance_id: str) -> None:
        """Toggle an instance's enabled status.

        Args:
            instance_id: ID of the instance to toggle
        """
        instance = self.instance_manager.get_instance(instance_id)
        if not instance:
            self.notify(
                ErrorMessages.not_found("file instance", instance_id), severity="error"
            )
            return

        # Toggle enabled status
        instance.enabled = not instance.enabled
        self.instance_manager.update_instance(instance)

        # Sync to config and save
        self.sync_instances_to_config()

        status = "enabled" if instance.enabled else "disabled"
        self.notify(
            f"{instance.type.display_name} instance {status}", severity="information"
        )

        # Update the widget's reactive attribute - triggers watch method for smooth update
        try:
            # Find the specific item by checking instance_id
            for item in self.query(FileInstanceItem):
                if item.instance_id == instance_id:
                    item.is_enabled = instance.enabled
                    break
        except Exception:
            # Widget not found, ignore
            pass

    def _open_component_directory(self, file_type: FileType) -> None:
        """Open the component directory in the system file explorer.

        Args:
            file_type: File type to open component directory for
        """
        components_dir = get_components_dir()
        type_dir = components_dir / file_type.value

        # Open folder using SystemUtilityMixin method
        self.open_folder_in_explorer(type_dir)
