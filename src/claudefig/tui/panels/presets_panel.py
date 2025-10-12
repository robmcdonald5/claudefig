"""Presets panel for managing global preset templates."""

import os
import platform
import subprocess
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Label, Select

from claudefig.config import Config
from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.tui.screens import (
    ApplyPresetScreen,
    CreatePresetScreen,
)


class PresetsPanel(Container):
    """Panel for managing global preset templates."""

    # Class variable for state persistence across panel instances
    _last_selected_preset: str | None = None

    # Reactive attribute for tracking selected preset
    selected_preset: reactive[str | None] = reactive(None)

    def __init__(self, **kwargs) -> None:
        """Initialize presets panel."""
        super().__init__(**kwargs)
        self.config_template_manager = ConfigTemplateManager()
        self._presets_data = {}  # Cache preset data by name
        self._last_focused_button_index = 0  # Track which button was last focused

    def compose(self) -> ComposeResult:
        """Compose the presets panel."""
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
                (f"{p['name']} - {p.get('description', 'No description')}", p["name"])
                for p in presets
            ]

            # Determine initial value (will be fully restored in on_mount)
            initial_value = Select.BLANK
            if PresetsPanel._last_selected_preset in self._presets_data:
                initial_value = PresetsPanel._last_selected_preset

            yield Select(
                options,
                prompt="Choose a preset...",
                allow_blank=True,
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
            yield Button("📁 Open Presets Folder", id="btn-open-folder")
            yield Button("+ Create New Preset", id="btn-create-preset")

    def on_mount(self) -> None:
        """Called when the widget is mounted.

        Restore the previously selected preset state after all widgets are composed.
        """
        # Restore the selected preset reactive attribute
        # This must be done after mounting so the watch method can find the button
        if PresetsPanel._last_selected_preset in self._presets_data:
            self.selected_preset = PresetsPanel._last_selected_preset

    def watch_selected_preset(
        self, _old_value: str | None, new_value: str | None
    ) -> None:
        """Watch method called when selected_preset changes.

        Enables/disables the Apply button based on selection state.
        """
        apply_button = self.query_one("#btn-apply-preset", Button)

        if new_value and new_value in self._presets_data:
            # Enable Apply button when preset is selected
            apply_button.disabled = False
        else:
            # Disable Apply button when no preset selected
            apply_button.disabled = True

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

            # Open presets folder in file explorer
            elif button_id == "btn-open-folder":
                self._open_presets_folder()

            # Create new preset
            elif button_id == "btn-create-preset":
                result = await self.app.push_screen_wait(CreatePresetScreen())
                if result and result.get("action") == "create":
                    await self._create_preset(
                        result.get("name"), result.get("description")
                    )

        except asyncio.CancelledError:
            # User cancelled the operation (pressed Escape) - this is normal
            pass

    def _open_presets_folder(self) -> None:
        """Open the presets folder in the system file explorer."""
        presets_path = Path(self.config_template_manager.global_presets_dir)

        # Ensure the directory exists
        if not presets_path.exists():
            self.app.notify(
                f"Presets folder does not exist: {presets_path}",
                severity="warning",
            )
            return

        try:
            system = platform.system()

            if system == "Windows":
                # Windows: use os.startfile
                os.startfile(str(presets_path))
            elif system == "Darwin":
                # macOS: use 'open' command
                subprocess.call(["open", str(presets_path)])
            else:
                # Linux: use 'xdg-open' command
                subprocess.call(["xdg-open", str(presets_path)])

            self.app.notify(
                "Opened presets folder in file explorer",
                severity="information",
            )
        except Exception as e:
            self.app.notify(
                f"Error opening folder: {e}",
                severity="error",
            )

    @work
    async def _apply_preset(self, preset_name: str) -> None:
        """Apply a preset to the current project."""
        import asyncio

        try:
            result = await self.app.push_screen_wait(ApplyPresetScreen(preset_name))

            if result and result.get("action") == "apply":
                try:
                    self.config_template_manager.apply_preset_to_project(preset_name)
                    self.app.notify(
                        f"Applied preset '{preset_name}' successfully!",
                        severity="information",
                    )

                    # Reload config and switch to Config panel
                    # Import MainScreen to avoid circular import
                    from claudefig.tui.app import MainScreen

                    if isinstance(self.app, MainScreen):
                        self.app.config = Config()
                        self.app._activate_section("config")

                except FileExistsError:
                    self.app.notify(".claudefig.toml already exists!", severity="error")
                except Exception as e:
                    self.app.notify(f"Error applying preset: {e}", severity="error")
        except asyncio.CancelledError:
            # User cancelled the operation (pressed Escape) - this is normal
            pass

    async def _create_preset(self, name: str, description: str) -> None:
        """Create a new preset from current config."""
        try:
            self.config_template_manager.save_global_preset(name, description)
            self.app.notify(
                f"Created preset '{name}' successfully!", severity="information"
            )

            # Refresh the panel to show new preset
            self.refresh(recompose=True)

        except ValueError as e:
            self.app.notify(str(e), severity="error")
        except FileNotFoundError as e:
            self.app.notify(str(e), severity="error")
        except Exception as e:
            self.app.notify(f"Error creating preset: {e}", severity="error")

    def on_key(self, event) -> None:
        """Handle key events for custom navigation behavior."""
        focused = self.screen.focused

        # Prevent Select from opening dropdown on arrow keys - use for navigation instead
        if isinstance(focused, Select):
            if event.key == "down":
                event.prevent_default()
                event.stop()
                # Move to the last focused button in the row
                try:
                    button_row = self.query_one(".button-row")
                    buttons = list(button_row.query("Button"))
                    if buttons and 0 <= self._last_focused_button_index < len(buttons):
                        buttons[self._last_focused_button_index].focus()
                    elif buttons:
                        buttons[0].focus()
                except Exception:
                    pass
                return
            elif event.key == "up":
                # Prevent up arrow from opening dropdown
                event.prevent_default()
                event.stop()
                return

        # When on any button, up arrow should go to Select
        if event.key == "up" and isinstance(focused, Button):
            # Check if this button is in the button-row
            try:
                button_row = self.query_one(".button-row")
                if focused.parent == button_row:
                    event.prevent_default()
                    event.stop()
                    # Remember which button we're leaving from
                    buttons = list(button_row.query("Button"))
                    try:
                        self._last_focused_button_index = buttons.index(focused)
                    except ValueError:
                        self._last_focused_button_index = 0
                    # Move to Select dropdown
                    select = self.query_one("#preset-select", Select)
                    select.focus()
                    return
            except Exception:
                pass
