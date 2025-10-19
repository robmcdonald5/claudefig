"""File instances screen for managing multi-instance file types."""

import platform
import subprocess
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import DescendantFocus, Key
from textual.screen import Screen
from textual.widgets import Button, Label, Select, TabbedContent, TabPane

from claudefig.config import Config
from claudefig.error_messages import ErrorMessages
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileType
from claudefig.preset_manager import PresetManager
from claudefig.tui.base import BackButtonMixin, FileInstanceMixin
from claudefig.tui.widgets.file_instance_item import FileInstanceItem
from claudefig.user_config import get_components_dir


class FileInstancesScreen(Screen, BackButtonMixin, FileInstanceMixin):
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

        Args:
            event: The key event
        """
        focused = self.focused

        # If a component Select is focused
        if isinstance(focused, Select) and focused.id and focused.id.startswith("select-add-"):
            # Prevent up/down from opening the dropdown
            if event.key in ("up", "down") and not focused.expanded:
                # Don't let Select handle it - let it bubble for navigation
                event.prevent_default()
                # Manually trigger navigation
                if event.key == "up":
                    self.action_focus_previous()
                else:
                    self.action_focus_next()
                event.stop()

    def action_focus_previous(self) -> None:
        """Override up arrow navigation to prevent wrapping.

        Handles focus movement when pressing up arrow:
        - If at the first focusable element, stay there (no wrap)
        - Otherwise, move focus to previous element normally
        """
        # Use this screen's actual focus_chain instead of building our own list
        # This ensures we're using the same order Textual uses for navigation
        focus_chain = self.focus_chain

        if not focus_chain:
            return

        focused = self.focused
        if focused is None:
            # No focus, focus the first element in chain
            focus_chain[0].focus()
            return

        if focused not in focus_chain:
            # Focused widget not in chain, shouldn't happen but handle gracefully
            return

        current_index = focus_chain.index(focused)

        # At the absolute first element - don't wrap
        if current_index == 0:
            # Scroll to the top to reveal title labels
            try:
                # Get the title label and scroll it into view (at the top)
                title_label = self.query("Label.screen-title").first()
                if title_label:
                    title_label.scroll_visible(top=True, animate=False)
            except Exception:
                pass
            return

        # Normal navigation - focus previous element in chain
        # Textual will automatically scroll to keep it visible
        focus_chain[current_index - 1].focus()

    def action_focus_next(self) -> None:
        """Override down arrow navigation to prevent wrapping.

        Handles focus movement when pressing down arrow:
        - If at the last focusable element, stay there (no wrap)
        - Otherwise, move focus to next element normally
        """
        # Use this screen's actual focus_chain instead of building our own list
        # This ensures we're using the same order Textual uses for navigation
        focus_chain = self.focus_chain

        if not focus_chain:
            return

        focused = self.focused
        if focused is None:
            # No focus, focus the first element in chain
            focus_chain[0].focus()
            return

        if focused not in focus_chain:
            # Focused widget not in chain, shouldn't happen but handle gracefully
            return

        current_index = focus_chain.index(focused)

        # At the bottom of the tree (last element, typically the Back button)
        # Don't wrap, but scroll viewport if there's content below
        if current_index == len(focus_chain) - 1:
            # Scroll to ensure the last element (and any content below) is visible
            try:
                # Scroll the current focused widget to bottom to reveal content below
                focused.scroll_visible(top=False, animate=False)
            except Exception:
                pass
            return

        # Normal navigation - focus next element in chain
        # Textual will automatically scroll to keep it visible
        focus_chain[current_index + 1].focus()

    def on_descendant_focus(self, event: DescendantFocus) -> None:
        """Ensure focused widgets are scrolled into view.

        Args:
            event: The focus event containing the focused widget
        """
        # Scroll the VerticalScroll container to keep focused widget visible
        # This ensures proper scrolling within the container
        try:
            scroll_container = self.query_one("#file-instances-screen", VerticalScroll)
            scroll_container.scroll_to_widget(event.widget, animate=False)
        except Exception:
            pass

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
                            components = self.instance_manager.list_components(file_type)

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

    def _add_component_instance(
        self, file_type: FileType, component_name: str
    ) -> None:
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
                self.notify(
                    f"Component '{component_name}' not found", severity="error"
                )
                return

            # Generate new ID for this project
            preset_name = instance.preset.split(":")[-1] if ":" in instance.preset else instance.preset
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
                # Refresh screen to show updated data
                self.refresh(recompose=True)
            else:
                # Show validation errors
                error_msg = "\n".join(result.errors) if result.errors else "Validation failed"
                self.notify(error_msg, severity="error")

        except Exception as e:
            self.notify(
                ErrorMessages.operation_failed("adding component", str(e)),
                severity="error",
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
            self.notify(
                ErrorMessages.not_found("file instance", instance_id), severity="error"
            )
            return

        def handle_result(result: Optional[dict]) -> None:
            """Handle dialog result."""
            if result and result.get("action") == "save":
                updated_instance = result["instance"]
                try:
                    self.instance_manager.update_instance(updated_instance)
                    # Sync to config and save
                    self.sync_instances_to_config()
                    self.notify(
                        f"Updated {updated_instance.type.display_name} instance",
                        severity="information",
                    )
                    # Refresh screen to show updated data
                    self.refresh(recompose=True)
                except Exception as e:
                    self.notify(
                        ErrorMessages.operation_failed("updating instance", str(e)),
                        severity="error",
                    )

        self.app.push_screen(
            FileInstanceEditScreen(
                instance_manager=self.instance_manager,
                preset_manager=self.preset_manager,
                instance=instance,
            ),
            callback=handle_result,
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
            # Refresh screen to show updated data
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

        # Refresh screen to show updated data
        self.refresh(recompose=True)

    def _open_component_directory(self, file_type: FileType) -> None:
        """Open the component directory in the system file explorer.

        Args:
            file_type: File type to open component directory for
        """
        try:
            components_dir = get_components_dir()
            type_dir = components_dir / file_type.value

            # Ensure directory exists
            type_dir.mkdir(parents=True, exist_ok=True)

            # Open in file explorer based on platform
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", str(type_dir)], check=False)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(type_dir)], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", str(type_dir)], check=False)

            self.notify(
                f"Opened component folder: {type_dir}", severity="information"
            )

        except Exception as e:
            self.notify(
                f"Failed to open component folder: {e}", severity="error"
            )
