"""File instances screen for managing multi-instance file types."""

from pathlib import Path
from typing import Any

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
                        instances = file_instance_service.get_instances_by_type(
                            self.instances_dict, file_type
                        )

                        # Component selector
                        with Horizontal(classes="tab-actions"):
                            # Get available components for this file type
                            from claudefig.user_config import get_components_dir

                            components_dir = get_components_dir()
                            # Map file type to component directory
                            type_dirs = {
                                FileType.CLAUDE_MD: "claude_md",
                                FileType.GITIGNORE: "gitignore",
                                FileType.COMMANDS: "commands",
                                FileType.AGENTS: "agents",
                                FileType.HOOKS: "hooks",
                                FileType.OUTPUT_STYLES: "output_styles",
                                FileType.MCP: "mcp",
                                FileType.SETTINGS_JSON: "settings_json",
                            }

                            type_dir = components_dir / type_dirs.get(
                                file_type, file_type.value
                            )
                            components = []

                            if type_dir.exists():
                                # For folder-based components (CLAUDE_MD, GITIGNORE)
                                if file_type in (
                                    FileType.CLAUDE_MD,
                                    FileType.GITIGNORE,
                                ):
                                    components = [
                                        (item.name, item)
                                        for item in type_dir.iterdir()
                                        if item.is_dir()
                                    ]
                                else:
                                    # For JSON-based components
                                    components = [
                                        (item.stem, item)
                                        for item in type_dir.glob("*.json")
                                    ]

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
            existing_instances = list(self.instances_dict.values())

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
            import json

            from claudefig.user_config import get_components_dir

            components_dir = get_components_dir()
            type_dirs = {
                FileType.CLAUDE_MD: "claude_md",
                FileType.GITIGNORE: "gitignore",
                FileType.COMMANDS: "commands",
                FileType.AGENTS: "agents",
                FileType.HOOKS: "hooks",
                FileType.OUTPUT_STYLES: "output_styles",
                FileType.MCP: "mcp",
                FileType.SETTINGS_JSON: "settings_json",
            }

            type_dir = components_dir / type_dirs.get(file_type, file_type.value)
            instance = None

            # For folder-based components
            if file_type in (FileType.CLAUDE_MD, FileType.GITIGNORE):
                component_folder = type_dir / component_name
                if component_folder.exists() and component_folder.is_dir():
                    metadata_file = component_folder / "component.json"
                    if metadata_file.exists():
                        component_data = json.loads(
                            metadata_file.read_text(encoding="utf-8")
                        )
                        instance = FileInstance(
                            id=f"{file_type.value}-{component_name}",
                            type=file_type,
                            preset=f"component:{component_name}",
                            path=component_data.get("path", file_type.default_path),
                            enabled=True,
                            variables={
                                "component_folder": str(component_folder),
                                "component_name": component_name,
                            },
                        )
            else:
                # For JSON-based components
                component_file = type_dir / f"{component_name}.json"
                if component_file.exists():
                    component_data = json.loads(
                        component_file.read_text(encoding="utf-8")
                    )
                    instance = FileInstance(
                        id=f"{file_type.value}-{component_name}",
                        type=file_type,
                        preset=f"component:{component_name}",
                        path=component_data.get("path", file_type.default_path),
                        enabled=True,
                        variables={"component_name": component_name},
                    )

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
        # Get the instance
        instance = file_instance_service.get_instance(self.instances_dict, instance_id)
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
                    file_instance_service.update_instance(
                        self.instances_dict,
                        instance,
                        self.preset_repo,
                        self.config_repo.config_path.parent,
                    )
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
        instance = file_instance_service.get_instance(self.instances_dict, instance_id)
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
            project_dir = self.config_repo.config_path.parent.resolve()

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
                selected_path_obj = Path(selected_path)
                try:
                    # Try to make it relative to project dir
                    relative_path = selected_path_obj.relative_to(project_dir)
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

                # Update the widget's reactive attribute - triggers watch method for smooth update
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
            # Catch any other unexpected errors (e.g., tkinter issues)
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
