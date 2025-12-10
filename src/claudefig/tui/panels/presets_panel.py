"""Presets panel for managing global preset templates."""

import contextlib
from pathlib import Path
from typing import Any

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Label, Select
from textual.widgets._select import NoSelection

from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.exceptions import (
    ConfigFileExistsError,
    FileOperationError,
    PresetExistsError,
    PresetNotFoundError,
    TemplateNotFoundError,
)
from claudefig.services import config_service
from claudefig.tui.base import BaseNavigablePanel, SystemUtilityMixin
from claudefig.tui.screens import (
    ApplyPresetScreen,
    CreatePresetScreen,
    DeletePresetScreen,
)
from claudefig.tui.screens.create_preset_wizard import CreatePresetWizard


class PresetsPanel(BaseNavigablePanel, SystemUtilityMixin):
    """Panel for managing global preset templates with custom Select navigation.

    Inherits standard navigation bindings from BaseNavigablePanel but uses
    custom on_key() override to handle special navigation between Select
    dropdown and button row.
    """

    # Class variables for state persistence across panel instances
    _last_selected_preset: str | None = None
    _last_focused_widget_type: str = "select"  # "select" or "button"
    _last_focused_button_index: int = 0  # Which button (0-3) was last focused

    # Reactive attribute for tracking selected preset
    selected_preset: reactive[str | None] = reactive(None)

    def __init__(self, **kwargs) -> None:
        """Initialize presets panel."""
        super().__init__(**kwargs)
        self.config_template_manager = ConfigTemplateManager()
        self._presets_data: dict[str, dict[str, Any]] = {}  # Cache preset data by name

    def compose(self) -> ComposeResult:
        """Compose the presets panel."""
        # can_focus=False prevents the scroll container from being in the focus chain
        with VerticalScroll(can_focus=False):
            yield Label("Global Preset Templates", classes="panel-title")
            yield Label(
                f"Location: {self.config_template_manager.global_presets_dir}",
                classes="panel-subtitle",
            )

            # Load presets data
            presets = self.config_template_manager.list_global_presets()

            # Build Select options
            if not presets:
                yield Label("No presets found.", classes="placeholder")
                # Empty select (disabled)
                yield Select(
                    [(("No presets available", Select.BLANK))],
                    allow_blank=True,
                    id="preset-select",
                )
            else:
                # Cache preset data for later use
                self._presets_data = {p["name"]: p for p in presets}

                # Build options: (display_text, value)
                options = [
                    (
                        f"{p['name']} - {p.get('description', 'No description')}",
                        p["name"],
                    )
                    for p in presets
                ]

                # Determine initial value (will be fully restored in on_mount)
                initial_value: str | NoSelection = Select.BLANK
                if PresetsPanel._last_selected_preset in self._presets_data:
                    initial_value = PresetsPanel._last_selected_preset
                elif "default" in self._presets_data:
                    # Default to "default" preset if no previous selection
                    initial_value = "default"
                    PresetsPanel._last_selected_preset = "default"

                yield Select(
                    options,
                    prompt="Choose a preset...",
                    allow_blank=False,  # Changed to False to ensure a preset is always selected
                    value=initial_value,
                    id="preset-select",
                )

            # All buttons in a single row
            with Horizontal(classes="button-row"):
                yield Button(
                    "Apply to Project",
                    id="btn-apply-preset",
                    disabled=True,  # Disabled until preset selected
                )
                yield Button(
                    "🗑 Delete Preset",
                    id="btn-delete-preset",
                    disabled=True,  # Disabled until preset selected
                )
                yield Button("📁 Open Presets Folder", id="btn-open-folder")
                yield Button("Create from Config", id="btn-create-from-config")
                yield Button("Create from Repo", id="btn-create-from-repo")

    def on_mount(self) -> None:
        """Called when the widget is mounted.

        Restore the previously selected preset state and focus after all widgets are composed.
        """
        # Restore the selected preset reactive attribute
        # This must be done after mounting so the watch method can find the button
        if PresetsPanel._last_selected_preset in self._presets_data:
            self.selected_preset = PresetsPanel._last_selected_preset
        elif "default" in self._presets_data:
            # Default to "default" preset if no previous selection
            self.selected_preset = "default"
            PresetsPanel._last_selected_preset = "default"

        # Restore focus to the last focused widget
        self.restore_focus()

    def restore_focus(self) -> None:
        """Restore focus to the last focused widget (Select or button)."""
        try:
            if PresetsPanel._last_focused_widget_type == "select":
                # Restore focus to Select dropdown
                select = self.query_one("#preset-select", Select)
                select.focus()
            elif PresetsPanel._last_focused_widget_type == "button":
                # Restore focus to the last focused button
                button_row = self.query_one(".button-row")
                buttons = list(button_row.query("Button"))
                if buttons and 0 <= PresetsPanel._last_focused_button_index < len(
                    buttons
                ):
                    buttons[PresetsPanel._last_focused_button_index].focus()
                elif buttons:
                    # Fallback to first button
                    buttons[0].focus()
        except Exception:
            # Fallback to Select if restoration fails
            with contextlib.suppress(Exception):
                self.query_one("#preset-select", Select).focus()

    def on_descendant_focus(self, event) -> None:
        """Track which widget has focus for restoration later."""
        focused = event.widget

        # Track if Select is focused
        if isinstance(focused, Select):
            PresetsPanel._last_focused_widget_type = "select"

        # Track if a button in the button row is focused
        elif isinstance(focused, Button):
            with contextlib.suppress(Exception):
                button_row = self.query_one(".button-row")
                if focused.parent == button_row:
                    PresetsPanel._last_focused_widget_type = "button"
                    buttons = list(button_row.query("Button"))
                    with contextlib.suppress(ValueError):
                        PresetsPanel._last_focused_button_index = buttons.index(focused)

    def watch_selected_preset(
        self, _old_value: str | None, new_value: str | None
    ) -> None:
        """Watch method called when selected_preset changes.

        Enables/disables the Apply and Delete buttons based on selection state.
        """
        try:
            apply_button = self.query_one("#btn-apply-preset", Button)
            delete_button = self.query_one("#btn-delete-preset", Button)
        except Exception:
            # Buttons may not exist yet during recompose
            return

        if new_value and new_value in self._presets_data:
            # Enable Apply and Delete buttons when preset is selected
            apply_button.disabled = False
            delete_button.disabled = False
        else:
            # Disable Apply and Delete buttons when no preset selected
            apply_button.disabled = True
            delete_button.disabled = True

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle Select widget value changes."""
        # Update reactive attribute (this triggers watch method)
        if event.value == Select.BLANK:
            self.selected_preset = None
            PresetsPanel._last_selected_preset = None
        else:
            self.selected_preset = str(event.value)
            # Persist selection across panel navigation
            PresetsPanel._last_selected_preset = str(event.value)

    @work
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        import asyncio

        button_id = event.button.id
        if not button_id:
            return

        try:
            # Apply preset to project
            if button_id == "btn-apply-preset":
                if self.selected_preset:
                    self._apply_preset(self.selected_preset)

            # Delete preset
            elif button_id == "btn-delete-preset":
                if self.selected_preset:
                    await self._delete_preset(self.selected_preset)

            # Open presets folder in file explorer
            elif button_id == "btn-open-folder":
                self._open_presets_folder()

            # Create preset from config (Path 1)
            elif button_id == "btn-create-from-config":
                result = await self.app.push_screen_wait(CreatePresetScreen())
                if result and result.get("action") == "create":
                    await self._create_preset(
                        result.get("name"), result.get("description")
                    )

            # Create preset from discovered components (Path 2)
            elif button_id == "btn-create-from-repo":
                repo_path = Path.cwd()
                result = await self.app.push_screen_wait(CreatePresetWizard(repo_path))
                if result and result.get("action") == "created":
                    preset_name = result.get("preset_name")

                    # Store selection - on_mount will restore it after recompose
                    PresetsPanel._last_selected_preset = preset_name

                    # Refresh the panel to show new preset (on_mount handles selection)
                    self.refresh(recompose=True)

                    self.app.notify(
                        f"Switched to preset: {preset_name}", severity="information"
                    )

        except asyncio.CancelledError:
            # User cancelled the operation (pressed Escape) - this is normal
            pass

    def _open_presets_folder(self) -> None:
        """Open the presets folder in the system file explorer."""
        presets_path = Path(self.config_template_manager.global_presets_dir)

        # Open folder using SystemUtilityMixin method
        self.open_folder_in_explorer(presets_path)

    @work
    async def _apply_preset(self, preset_name: str) -> None:
        """Apply a preset to the current project."""
        import asyncio

        try:
            result = await self.app.push_screen_wait(ApplyPresetScreen(preset_name))

            if result and result.get("action") == "apply":
                try:
                    # User has confirmed via modal, so overwrite existing config
                    self.config_template_manager.apply_preset_to_project(
                        preset_name, overwrite=True
                    )
                    self.app.notify(
                        f"Applied preset '{preset_name}' successfully!",
                        severity="information",
                    )

                    # Reload config and switch to Config panel
                    # Import MainScreen to avoid circular import
                    from claudefig.tui.app import MainScreen

                    if isinstance(self.app, MainScreen):
                        self.app.config_data = config_service.load_config(
                            self.app.config_repo
                        )
                        self.app._activate_section("config")

                except ConfigFileExistsError as e:
                    self.app.notify(str(e), severity="error")
                except TemplateNotFoundError as e:
                    self.app.notify(str(e), severity="error")
                except PresetNotFoundError as e:
                    self.app.notify(str(e), severity="error")
                except Exception as e:
                    self.app.notify(f"Error applying preset: {e}", severity="error")
        except asyncio.CancelledError:
            # User cancelled the operation (pressed Escape) - this is normal
            pass

    async def _create_preset(self, name: str, description: str) -> None:
        """Create a new preset from current config."""
        try:
            # Validate that claudefig.toml exists in current directory
            config_path = Path.cwd() / "claudefig.toml"
            if not config_path.exists():
                self.app.notify(
                    "No Claudefig config detected. Please initialize Claudefig first (Initialize Project).",
                    severity="error",
                    timeout=5,
                )
                return

            self.config_template_manager.save_global_preset(name, description)
            self.app.notify(
                f"Created preset '{name}' successfully!", severity="information"
            )

            # Store selection - on_mount will restore it after recompose
            PresetsPanel._last_selected_preset = name

            # Refresh the panel to show new preset (on_mount handles selection)
            self.refresh(recompose=True)

            self.app.notify(f"Switched to preset: {name}", severity="information")

        except PresetExistsError as e:
            self.app.notify(str(e), severity="error")
        except ConfigFileExistsError as e:
            self.app.notify(str(e), severity="error")
        except FileOperationError as e:
            self.app.notify(str(e), severity="error")
        except ValueError as e:
            self.app.notify(str(e), severity="error")
        except FileNotFoundError as e:
            self.app.notify(str(e), severity="error")
        except Exception as e:
            self.app.notify(f"Error creating preset: {e}", severity="error")

    async def _delete_preset(self, preset_name: str) -> None:
        """Delete a preset after confirmation."""
        import asyncio

        try:
            # Show confirmation dialog
            result = await self.app.push_screen_wait(DeletePresetScreen(preset_name))

            if result and result.get("action") == "delete":
                try:
                    self.config_template_manager.delete_global_preset(preset_name)
                    self.app.notify(
                        f"Deleted preset '{preset_name}' successfully!",
                        severity="information",
                    )

                    # Clear the selection since the preset is gone
                    self.selected_preset = None
                    PresetsPanel._last_selected_preset = None

                    # Refresh the panel to remove deleted preset
                    self.refresh(recompose=True)

                except PresetNotFoundError as e:
                    self.app.notify(str(e), severity="error")
                except FileOperationError as e:
                    self.app.notify(str(e), severity="error")
                except FileNotFoundError as e:
                    self.app.notify(str(e), severity="error")
                except Exception as e:
                    self.app.notify(f"Error deleting preset: {e}", severity="error")

        except asyncio.CancelledError:
            # User cancelled the operation (pressed Escape) - this is normal
            pass

    def on_key(self, event) -> None:
        """Handle key events for custom navigation behavior with scroll support."""
        focused = self.screen.focused

        # Prevent Select from opening dropdown on arrow keys - use for navigation instead
        if isinstance(focused, Select):
            if event.key == "down":
                event.prevent_default()
                event.stop()
                # Move to the last focused button in the row
                with contextlib.suppress(Exception):
                    button_row = self.query_one(".button-row")
                    buttons = list(button_row.query("Button"))
                    if buttons and 0 <= PresetsPanel._last_focused_button_index < len(
                        buttons
                    ):
                        buttons[PresetsPanel._last_focused_button_index].focus()
                    elif buttons:
                        buttons[0].focus()
                return
            elif event.key == "up":
                # At the Select dropdown (top of panel) - scroll container to home
                with contextlib.suppress(Exception):
                    scroll_container = self.query_one(VerticalScroll)
                    scroll_container.scroll_home(animate=True)
                event.prevent_default()
                event.stop()
                return

        # When on any button, up arrow should go to Select
        if event.key == "up" and isinstance(focused, Button):
            # Check if this button is in the button-row
            with contextlib.suppress(Exception):
                button_row = self.query_one(".button-row")
                if focused.parent == button_row:
                    event.prevent_default()
                    event.stop()
                    # Remember which button we're leaving from
                    buttons = list(button_row.query("Button"))
                    with contextlib.suppress(ValueError):
                        PresetsPanel._last_focused_button_index = buttons.index(focused)
                    # Move to Select dropdown
                    select = self.query_one("#preset-select", Select)
                    select.focus()
                    return

        # When on any button in the button row, prevent down from wrapping
        # and scroll to reveal content below when at the last button
        if event.key == "down" and isinstance(focused, Button):
            with contextlib.suppress(Exception):
                button_row = self.query_one(".button-row")
                if focused.parent == button_row:
                    # At the bottom of the panel
                    buttons = list(button_row.query("Button"))
                    with contextlib.suppress(ValueError, Exception):
                        current_index = buttons.index(focused)
                        # If on the last button, scroll container to end
                        if current_index == len(buttons) - 1:
                            scroll_container = self.query_one(VerticalScroll)
                            scroll_container.scroll_end(animate=True)

                    # Prevent wrapping to main menu
                    event.prevent_default()
                    event.stop()
                    return
