"""File instances screen for managing multi-instance file types."""

import contextlib
from pathlib import Path
from typing import Any

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.widgets import Button, Label, Select, TabbedContent, TabPane

from claudefig.error_messages import ErrorMessages
from claudefig.exceptions import (
    ConfigFileNotFoundError,
    FileOperationError,
    InstanceNotFoundError,
    InstanceValidationError,
)
from claudefig.models import FileInstance, FileType
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.repositories.preset_repository import TomlPresetRepository
from claudefig.services import config_service, file_instance_service
from claudefig.tui.base import BaseScreen, SystemUtilityMixin
from claudefig.tui.widgets.file_instance_item import FileInstanceItem
from claudefig.user_config import get_components_dir


class FileInstancesScreen(BaseScreen, SystemUtilityMixin):
    """Screen for managing multi-instance file types with tabs.

    Inherits standard navigation bindings from BaseScreen with ScrollNavigationMixin
    support for smart vertical/horizontal navigation.
    """

    # Class variables for state persistence across recompose
    _last_active_tab: str | None = None  # Tab ID e.g., "tab-claude_md"
    _last_focused_instance_id: str | None = None  # Instance ID for focused item
    _last_focused_widget_type: str = "select"  # "select", "button", or "instance"
    _last_focused_button_id: str | None = None  # For "Open Folder" button tracking

    def __init__(
        self,
        config_data: dict[str, Any],
        config_repo: TomlConfigRepository,
        instances_dict: dict[str, FileInstance],
        **kwargs,
    ) -> None:
        """Initialize file instances screen.

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

    def on_mount(self) -> None:
        """Called when the widget is mounted. Restore focus state after recompose."""
        self.call_after_refresh(self.restore_focus)

    def on_descendant_focus(self, event) -> None:
        """Track which widget has focus for restoration after recompose."""
        import contextlib

        focused = event.widget

        # Track active tab
        with contextlib.suppress(Exception):
            tabs = self.query_one("#file-instances-tabs", TabbedContent)
            FileInstancesScreen._last_active_tab = tabs.active

        # Track if Select dropdown is focused
        if isinstance(focused, Select):
            FileInstancesScreen._last_focused_widget_type = "select"

        # Track if a button is focused
        elif isinstance(focused, Button):
            if focused.id and focused.id.startswith("btn-open-components-"):
                # Open Folder button
                FileInstancesScreen._last_focused_widget_type = "button"
                FileInstancesScreen._last_focused_button_id = focused.id
            elif focused.id and any(
                focused.id.startswith(p)
                for p in ["edit-", "path-", "remove-", "toggle-"]
            ):
                # FileInstanceItem button - extract instance ID
                FileInstancesScreen._last_focused_widget_type = "instance"
                for prefix in ["edit-", "path-", "remove-", "toggle-"]:
                    if focused.id.startswith(prefix):
                        FileInstancesScreen._last_focused_instance_id = focused.id[
                            len(prefix) :
                        ]
                        break
            elif focused.id == "btn-back":
                FileInstancesScreen._last_focused_widget_type = "back"

    def restore_focus(self) -> None:
        """Restore focus to the last focused widget after recompose."""
        import contextlib

        try:
            # First restore the active tab
            if FileInstancesScreen._last_active_tab:
                with contextlib.suppress(Exception):
                    tabs = self.query_one("#file-instances-tabs", TabbedContent)
                    tabs.active = FileInstancesScreen._last_active_tab

            # Then restore focus based on widget type
            if FileInstancesScreen._last_focused_widget_type == "select":
                # Find and focus the select in the active tab
                if FileInstancesScreen._last_active_tab:
                    file_type_value = FileInstancesScreen._last_active_tab.replace(
                        "tab-", ""
                    )
                    select_id = f"select-add-{file_type_value}"
                    with contextlib.suppress(Exception):
                        select = self.query_one(f"#{select_id}", Select)
                        select.focus()
                        return

            elif FileInstancesScreen._last_focused_widget_type == "button":
                if FileInstancesScreen._last_focused_button_id:
                    with contextlib.suppress(Exception):
                        button = self.query_one(
                            f"#{FileInstancesScreen._last_focused_button_id}", Button
                        )
                        button.focus()
                        return

            elif FileInstancesScreen._last_focused_widget_type == "instance":
                if FileInstancesScreen._last_focused_instance_id:
                    # Try to find a button in the instance item
                    instance_id = FileInstancesScreen._last_focused_instance_id
                    for item in self.query(FileInstanceItem):
                        if item.instance_id == instance_id:
                            # Focus the first button in this item
                            buttons = list(item.query(Button))
                            if buttons:
                                buttons[0].focus()
                                return
                            break

            elif FileInstancesScreen._last_focused_widget_type == "back":
                with contextlib.suppress(Exception):
                    self.query_one("#btn-back", Button).focus()
                    return

            # Fallback: focus the back button
            with contextlib.suppress(Exception):
                self.query_one("#btn-back", Button).focus()

        except Exception:
            # Ultimate fallback
            with contextlib.suppress(Exception):
                self.query_one("#btn-back", Button).focus()

    def action_pop_screen(self) -> None:
        """Pop the current screen to return to config menu."""
        self.app.pop_screen()

    def on_key(self, event: Key) -> None:
        """Handle key events for Select navigation.

        Prevents up/down arrows from opening component Select dropdowns.
        Only Enter opens dropdowns, backspace/esc closes them.

        Args:
            event: The key event
        """
        focused = self.focused

        # If a component Select is focused, prevent up/down from opening the dropdown
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

    def compose_screen_content(self) -> ComposeResult:
        """Compose the file instances screen content."""
        # can_focus=False prevents the container from being in the focus chain
        # while still allowing it to be scrolled programmatically
        with VerticalScroll(id="file-instances-screen", can_focus=False):
            yield Label("FILE INSTANCES", classes="screen-title")

            yield Label(
                "Manage file instances and core configuration files.",
                classes="screen-description",
            )

            # Get all file types (both multi-instance and single-instance)
            all_file_types = [
                # Multi-instance types
                FileType.CLAUDE_MD,
                FileType.GITIGNORE,
                FileType.COMMANDS,
                FileType.AGENTS,
                FileType.HOOKS,
                FileType.OUTPUT_STYLES,
                FileType.MCP,
                FileType.PLUGINS,
                FileType.SKILLS,
                # Single-instance types
                FileType.SETTINGS_JSON,
                FileType.SETTINGS_LOCAL_JSON,
                FileType.STATUSLINE,
            ]

            # Create tabbed content
            with TabbedContent(id="file-instances-tabs"):
                for file_type in all_file_types:
                    with TabPane(file_type.display_name, id=f"tab-{file_type.value}"):
                        # Get instances for this file type
                        instances = file_instance_service.get_instances_by_type(
                            self.instances_dict, file_type
                        )

                        is_single_instance = not file_type.supports_multiple

                        # Component/Template selector
                        with Horizontal(classes="tab-actions"):
                            # Get available components from both global and preset sources
                            from claudefig.user_config import (
                                get_components_dir,
                                get_user_config_dir,
                            )

                            components = []

                            # Map file type to component directory (unified for all types)
                            type_dirs = {
                                FileType.CLAUDE_MD: "claude_md",
                                FileType.GITIGNORE: "gitignore",
                                FileType.COMMANDS: "commands",
                                FileType.AGENTS: "agents",
                                FileType.HOOKS: "hooks",
                                FileType.OUTPUT_STYLES: "output_styles",
                                FileType.MCP: "mcp",
                                FileType.PLUGINS: "plugins",
                                FileType.SKILLS: "skills",
                                FileType.SETTINGS_JSON: "settings_json",
                                FileType.SETTINGS_LOCAL_JSON: "settings_local_json",
                                FileType.STATUSLINE: "statusline",
                            }

                            type_dir_name = type_dirs.get(file_type, file_type.value)

                            # Scan global components: ~/.claudefig/components/{type}/
                            components_dir = get_components_dir()
                            global_type_dir = components_dir / type_dir_name

                            if global_type_dir.exists():
                                # All component types are folder-based (directories with files inside)
                                components.extend(
                                    [
                                        (f"{item.name} (g)", item, "global")
                                        for item in global_type_dir.iterdir()
                                        if item.is_dir()
                                    ]
                                )

                            # Scan preset components: ~/.claudefig/presets/default/components/{type}/
                            user_config_dir = get_user_config_dir()
                            default_preset_dir = user_config_dir / "presets" / "default"
                            preset_type_dir = (
                                default_preset_dir / "components" / type_dir_name
                            )

                            if preset_type_dir.exists():
                                # All component types are folder-based
                                components.extend(
                                    [
                                        (f"{item.name} (p)", item, "preset")
                                        for item in preset_type_dir.iterdir()
                                        if item.is_dir()
                                    ]
                                )

                            if components:
                                # Build options: (display_name, component_data)
                                # Store component data as JSON string: "name|source"
                                component_options = [
                                    (
                                        f"+ Add {display_name}",
                                        f"{path.stem if not path.is_dir() else path.name}|{source}",
                                    )
                                    for display_name, path, source in components
                                ]

                                yield Select(
                                    options=component_options,
                                    prompt=f"Select a {'template' if is_single_instance else 'component'} to add...",
                                    id=f"select-add-{file_type.value}",
                                    allow_blank=True,
                                    classes="component-select",
                                )
                            else:
                                # No components/templates available - show info message
                                yield Label(
                                    f"No {file_type.display_name} {'templates' if is_single_instance else 'components'} found.",
                                    classes="empty-message component-select",
                                )

                            # Always show button to open component/template directory
                            yield Button(
                                "Open Folder",
                                id=f"btn-open-components-{file_type.value}",
                                classes="component-folder-btn",
                            )

                        # Display instances
                        if instances:
                            # All types use FileInstanceItem now
                            # Single-instance types just have auto-replace logic when adding
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
        component_data = event.value

        # Ignore if blank/prompt selected or not a string
        if not component_data or not isinstance(component_data, str):
            return

        # Parse component data: "name|source"
        if "|" in component_data:
            component_name, source = component_data.split("|", 1)
        else:
            # Fallback for backward compatibility
            component_name = component_data
            source = "global"

        try:
            file_type = FileType(file_type_value)
            self._add_component_instance(file_type, component_name, source)

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

    def _add_component_instance(
        self, file_type: FileType, component_name: str, source: str = "global"
    ) -> None:
        """Load a component/template and add it as a file instance.

        For single-instance types, auto-replaces any existing instance.
        For multi-instance types, prevents duplicate components.

        Args:
            file_type: Type of file
            component_name: Name of the component/template to load
            source: Source of component - "global" or "preset"
        """
        try:
            is_single_instance = not file_type.supports_multiple

            if is_single_instance:
                # For single-instance types: auto-replace existing instance
                existing_instances = file_instance_service.get_instances_by_type(
                    self.instances_dict, file_type
                )
                for existing in existing_instances:
                    # Remove existing instance silently (auto-replace behavior)
                    file_instance_service.remove_instance(
                        self.instances_dict, existing.id
                    )
                    # Also remove the widget from the DOM
                    with contextlib.suppress(Exception):
                        for item in self.query(FileInstanceItem):
                            if item.instance_id == existing.id:
                                item.remove()
                                break
            else:
                # For multi-instance types: check if this component has already been added
                existing_instances = list(self.instances_dict.values())

                for existing in existing_instances:
                    # Skip if different type
                    if existing.type != file_type:
                        continue

                    # All types are folder-based now, check component_folder
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

            instance = None

            # Determine base components directory based on source
            if source == "preset":
                from claudefig.user_config import get_user_config_dir

                user_config_dir = get_user_config_dir()
                base_components_dir = (
                    user_config_dir / "presets" / "default" / "components"
                )
            else:
                base_components_dir = get_components_dir()

            type_dirs = {
                FileType.CLAUDE_MD: "claude_md",
                FileType.GITIGNORE: "gitignore",
                FileType.COMMANDS: "commands",
                FileType.AGENTS: "agents",
                FileType.HOOKS: "hooks",
                FileType.OUTPUT_STYLES: "output_styles",
                FileType.MCP: "mcp",
                FileType.PLUGINS: "plugins",
                FileType.SKILLS: "skills",
                FileType.SETTINGS_JSON: "settings_json",
                FileType.SETTINGS_LOCAL_JSON: "settings_local_json",
                FileType.STATUSLINE: "statusline",
            }

            type_dir = base_components_dir / type_dirs.get(file_type, file_type.value)

            # All component types are folder-based (no component.json needed!)
            component_folder = type_dir / component_name
            if component_folder.exists() and component_folder.is_dir():
                # Derive all metadata from folder structure
                instance = FileInstance(
                    id=f"{file_type.value}-{component_name}",
                    type=file_type,
                    preset=f"component:{component_name}",
                    path=file_type.default_path,  # Use default path from FileType
                    enabled=True,
                    variables={
                        "component_folder": str(component_folder),
                        "component_name": component_name,
                    },
                )

            if not instance:
                self.notify(
                    f"{'Template' if is_single_instance else 'Component'} '{component_name}' not found",
                    severity="error",
                )
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
            instance.id = file_instance_service.generate_instance_id(
                file_type, preset_name, instance.path, self.instances_dict
            )

            # Add instance with validation
            result = file_instance_service.add_instance(
                self.instances_dict,
                instance,
                self.preset_repo,
                self.config_repo.config_path.parent,
            )

            if result.valid:
                # Sync to config and save
                self.sync_instances_to_config()
                action = "Set" if is_single_instance else "Added"
                source = "template" if is_single_instance else "component"
                self.notify(
                    f"{action} {instance.type.display_name} from {source} '{component_name}'",
                    severity="information",
                )

                # Try to dynamically add the widget without recomposing
                try:
                    # Get the current tab pane for this file type
                    tab_id = f"tab-{file_type.value}"
                    tab_pane = self.query_one(f"#{tab_id}", TabPane)

                    # Try to find the instance-list container
                    instance_lists = tab_pane.query(".instance-list")
                    if instance_lists:
                        # Container exists, mount the new widget to it
                        container = instance_lists.first(Vertical)
                        container.mount(FileInstanceItem(instance=instance))
                    else:
                        # No container exists (was showing empty message)
                        # Remove the empty message labels and create container with widget
                        empty_messages = tab_pane.query(".empty-message")
                        for msg in empty_messages:
                            msg.remove()

                        # Create new container with the instance
                        container = Vertical(classes="instance-list")
                        tab_pane.mount(container)
                        container.mount(FileInstanceItem(instance=instance))

                except Exception:
                    # Track current state before fallback recompose
                    with contextlib.suppress(Exception):
                        tabs = self.query_one("#file-instances-tabs", TabbedContent)
                        FileInstancesScreen._last_active_tab = tabs.active
                    # If dynamic mounting fails, fallback to recompose
                    self.refresh(recompose=True)
            else:
                # Show validation errors
                error_msg = (
                    "\n".join(result.errors) if result.errors else "Validation failed"
                )
                self.notify(error_msg, severity="error")

        except InstanceValidationError as e:
            self.notify(str(e), severity="error")
        except ConfigFileNotFoundError as e:
            self.notify(str(e), severity="error")
        except FileOperationError as e:
            self.notify(str(e), severity="error")
        except Exception as e:
            # Catch any other unexpected errors
            self.notify(
                ErrorMessages.operation_failed("adding component", str(e)),
                severity="error",
            )

    def _open_component_file(self, instance_id: str) -> None:
        """Open the component file in the system editor.

        Args:
            instance_id: ID of the instance to edit
        """
        from claudefig.user_config import get_user_config_dir

        # Get the instance
        instance = file_instance_service.get_instance(self.instances_dict, instance_id)
        if not instance:
            self.notify(
                ErrorMessages.not_found("file instance", instance_id), severity="error"
            )
            return

        # Get component name from variables or extract from preset
        component_name = instance.variables.get("component_name")
        if not component_name and ":" in instance.preset:
            component_name = instance.preset.split(":")[-1]

        if not component_name:
            self.notify(
                f"Cannot determine component name from preset '{instance.preset}'",
                severity="error",
            )
            return

        # Get cached component folder, but verify it still exists
        component_folder = instance.variables.get("component_folder")
        folder_path = Path(component_folder) if component_folder else None

        # If no cached folder or cached folder doesn't exist, search for it
        if not folder_path or not folder_path.exists():
            # Search for component folder in multiple locations:
            # 1. Global components: ~/.claudefig/components/{type}/{name}
            # 2. Preset components: ~/.claudefig/presets/default/components/{type}/{name}
            possible_paths = [
                # Global components directory
                get_components_dir() / instance.type.value / component_name,
                # Default preset components directory
                get_user_config_dir()
                / "presets"
                / "default"
                / "components"
                / instance.type.value
                / component_name,
            ]

            # Find the first existing path
            folder_path = None
            for path in possible_paths:
                if path.exists() and path.is_dir():
                    folder_path = path
                    break

            if folder_path:
                # Update the instance to cache the correct path
                instance.variables = instance.variables or {}
                instance.variables["component_name"] = component_name
                instance.variables["component_folder"] = str(folder_path)
                file_instance_service.update_instance(
                    self.instances_dict,
                    instance,
                    self.preset_repo,
                    self.config_repo.config_path.parent,
                )
                self.sync_instances_to_config()
            else:
                # List searched paths in error message
                searched = ", ".join(str(p) for p in possible_paths)
                self.notify(
                    f"Component folder not found. Searched: {searched}",
                    severity="error",
                )
                return

        if not folder_path.is_dir():
            self.notify(
                f"Component folder is not a directory: {folder_path}",
                severity="error",
            )
            return

        # Find the file to open
        # For file-based types (claude_md, gitignore, etc.): use Path(instance.path).name
        # For directory-based types (commands, hooks, etc.): find the primary content file
        actual_filename = Path(instance.path).name
        file_to_open = folder_path / actual_filename

        # If direct filename match doesn't exist, find the primary content file
        # This handles directory-based component types where path ends with /
        if not file_to_open.exists() or not file_to_open.is_file():
            # Priority order for finding the primary file
            priority_extensions = [
                ".md",
                ".json",
                ".py",
                ".sh",
                ".txt",
                ".yaml",
                ".yml",
            ]
            priority_names = ["content", "README", "CLAUDE", "config", "example"]

            # Get all files in the folder (excluding hidden and __pycache__)
            content_files = [
                f
                for f in folder_path.iterdir()
                if f.is_file()
                and not f.name.startswith(".")
                and f.name != "component.toml"
                and "__pycache__" not in str(f)
            ]

            if not content_files:
                self.notify(
                    f"No content files found in component folder: {folder_path}",
                    severity="error",
                )
                return

            # Sort by priority: prefer known names, then by extension
            def sort_key(f: Path) -> tuple:
                name_priority = 99
                for i, name in enumerate(priority_names):
                    if name.lower() in f.stem.lower():
                        name_priority = i
                        break
                ext_priority = 99
                for i, ext in enumerate(priority_extensions):
                    if f.suffix.lower() == ext:
                        ext_priority = i
                        break
                return (name_priority, ext_priority, f.name)

            content_files.sort(key=sort_key)
            file_to_open = content_files[0]

        # Open file using SystemUtilityMixin method
        self.open_file_in_editor(file_to_open)

    def _show_file_path_selector(self, instance_id: str) -> None:
        """Open OS file picker to select path for file instances.

        Uses a thread worker to prevent blocking the TUI.

        Args:
            instance_id: ID of the instance to edit path for
        """
        # Get the instance
        instance = file_instance_service.get_instance(self.instances_dict, instance_id)
        if not instance:
            self.notify(
                ErrorMessages.not_found("file instance", instance_id), severity="error"
            )
            return

        # Prepare dialog parameters
        project_dir = self.config_repo.config_path.parent.resolve()
        default_filename = Path(instance.path).name

        # Set initial directory
        current_full_path = project_dir / instance.path
        if current_full_path.parent.exists():
            initial_dir = str(current_full_path.parent)
        else:
            initial_dir = str(project_dir)

        # Show loading indicator
        self.notify("Opening file selector...", severity="information", timeout=2)

        # Start the file dialog worker
        self._run_file_dialog(
            instance_id=instance_id,
            project_dir=str(project_dir),
            initial_dir=initial_dir,
            default_filename=default_filename,
            file_type_display_name=instance.type.display_name,
        )

    @work(thread=True, exclusive=True)
    def _run_file_dialog(
        self,
        instance_id: str,
        project_dir: str,
        initial_dir: str,
        default_filename: str,
        file_type_display_name: str,
    ) -> None:
        """Run tkinter file dialog in a separate thread.

        Args:
            instance_id: ID of the instance being edited
            project_dir: Project directory for relative path calculation
            initial_dir: Initial directory for the dialog
            default_filename: Default filename filter
            file_type_display_name: Display name for the file type
        """
        import tkinter as tk
        from tkinter import filedialog

        from textual.worker import get_current_worker

        # Check if worker was cancelled before starting
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        try:
            # Create a hidden tkinter root window
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            # Open file dialog
            selected_path = filedialog.askopenfilename(
                parent=root,
                title=f"Select or type location for {file_type_display_name}",
                initialdir=initial_dir,
                filetypes=[
                    (f"{default_filename}", default_filename),
                    ("All files", "*.*"),
                ],
            )

            # Clean up tkinter
            root.destroy()

            # Check cancellation again before processing
            if worker.is_cancelled:
                return

            if selected_path:
                # Safely call UI update from thread
                self.app.call_from_thread(
                    self._process_file_selection,
                    selected_path,
                    instance_id,
                    project_dir,
                )

        except Exception as e:
            # Safely notify error from thread
            self.app.call_from_thread(
                self.notify,
                ErrorMessages.operation_failed("selecting path", str(e)),
                "error",
            )

    def _process_file_selection(
        self, selected_path: str, instance_id: str, project_dir: str
    ) -> None:
        """Process a selected file path from the dialog.

        Args:
            selected_path: The path selected by the user
            instance_id: ID of the instance to update
            project_dir: Project directory for relative path calculation
        """
        try:
            instance = file_instance_service.get_instance(
                self.instances_dict, instance_id
            )
            if not instance:
                self.notify(
                    ErrorMessages.not_found("file instance", instance_id),
                    severity="error",
                )
                return

            project_dir_path = Path(project_dir)
            selected_path_obj = Path(selected_path)

            try:
                # Try to make it relative to project dir
                relative_path = selected_path_obj.relative_to(project_dir_path)
                new_path = str(relative_path)
            except ValueError:
                # If path is outside project, use absolute path
                new_path = str(selected_path_obj)

            # Update the instance path
            instance.path = new_path
            file_instance_service.update_instance(
                self.instances_dict,
                instance,
                self.preset_repo,
                self.config_repo.config_path.parent,
            )

            # Sync to config and save
            self.sync_instances_to_config()
            self.notify(
                f"Updated path for {instance.type.display_name} instance",
                severity="information",
            )

            # Update the widget's reactive attribute
            for item in self.query(FileInstanceItem):
                if item.instance_id == instance_id:
                    item.file_path = new_path
                    break

        except InstanceNotFoundError as e:
            self.notify(str(e), severity="error")
        except ConfigFileNotFoundError as e:
            self.notify(str(e), severity="error")
        except FileOperationError as e:
            self.notify(str(e), severity="error")
        except Exception as e:
            self.notify(
                ErrorMessages.operation_failed("updating path", str(e)),
                severity="error",
            )

    def _remove_instance(self, instance_id: str) -> None:
        """Remove a file instance.

        Args:
            instance_id: ID of the instance to remove
        """
        # Get the instance for display name
        instance = file_instance_service.get_instance(self.instances_dict, instance_id)
        if not instance:
            self.notify(
                ErrorMessages.not_found("file instance", instance_id), severity="error"
            )
            return

        # Remove from dict
        if file_instance_service.remove_instance(self.instances_dict, instance_id):
            # Sync to config and save
            self.sync_instances_to_config()
            self.notify(
                f"Removed {instance.type.display_name} instance", severity="information"
            )

            # Remove the widget directly from the DOM without recomposing
            try:
                for item in self.query(FileInstanceItem):
                    if item.instance_id == instance_id:
                        item.remove()
                        break
            except Exception:
                # Track current state before fallback recompose
                with contextlib.suppress(Exception):
                    tabs = self.query_one("#file-instances-tabs", TabbedContent)
                    FileInstancesScreen._last_active_tab = tabs.active
                # If dynamic removal fails, fallback to recompose
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
        instance = file_instance_service.get_instance(self.instances_dict, instance_id)
        if not instance:
            self.notify(
                ErrorMessages.not_found("file instance", instance_id), severity="error"
            )
            return

        # Toggle enabled status
        instance.enabled = not instance.enabled
        file_instance_service.update_instance(
            self.instances_dict,
            instance,
            self.preset_repo,
            self.config_repo.config_path.parent,
        )

        # Sync to config and save
        self.sync_instances_to_config()

        status = "enabled" if instance.enabled else "disabled"
        self.notify(
            f"{instance.type.display_name} instance {status}", severity="information"
        )

        # Update the widget's reactive attribute - triggers watch method for smooth update
        with contextlib.suppress(Exception):
            # Find the specific item by checking instance_id
            for item in self.query(FileInstanceItem):
                if item.instance_id == instance_id:
                    item.is_enabled = instance.enabled
                    break

    def _open_component_directory(self, file_type: FileType) -> None:
        """Open the component directory in the system file explorer.

        Args:
            file_type: File type to open component directory for
        """
        components_dir = get_components_dir()

        # Map file type to component directory (unified for all types)
        type_dirs = {
            FileType.CLAUDE_MD: "claude_md",
            FileType.GITIGNORE: "gitignore",
            FileType.COMMANDS: "commands",
            FileType.AGENTS: "agents",
            FileType.HOOKS: "hooks",
            FileType.OUTPUT_STYLES: "output_styles",
            FileType.MCP: "mcp",
            FileType.SETTINGS_JSON: "settings_json",
            FileType.SETTINGS_LOCAL_JSON: "settings_local_json",
            FileType.STATUSLINE: "statusline",
        }

        type_dir = components_dir / type_dirs.get(file_type, file_type.value)

        # Open folder using SystemUtilityMixin method
        self.open_folder_in_explorer(type_dir)
