"""Presets panel for managing global preset templates."""

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Label

from claudefig.config import Config
from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.tui.screens import (
    ApplyPresetScreen,
    CreatePresetScreen,
    PresetDetailsScreen,
)
from claudefig.tui.widgets import PresetCard


class PresetsPanel(Container):
    """Panel for managing global preset templates."""

    def __init__(self, **kwargs) -> None:
        """Initialize presets panel."""
        super().__init__(**kwargs)
        self.config_template_manager = ConfigTemplateManager()

    def compose(self) -> ComposeResult:
        """Compose the presets panel."""
        yield Label("Global Preset Templates", classes="panel-title")

        with VerticalScroll():
            yield Label(
                f"Location: {self.config_template_manager.global_presets_dir}",
                classes="panel-subtitle",
            )

            # Load and display presets
            presets = self.config_template_manager.list_global_presets()

            if not presets:
                yield Label("No presets found.", classes="placeholder")
            else:
                for preset in presets:
                    yield PresetCard(preset["name"], preset, classes="preset-card")

            # Footer button
            with Horizontal(classes="button-row"):
                yield Button(
                    "+ Create New Preset from Current Config", id="btn-create-preset"
                )

    @work
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        import asyncio

        button_id = event.button.id
        if not button_id:
            return

        try:
            # View Details
            if button_id.startswith("view-"):
                preset_name = button_id.replace("view-", "")
                result = await self.app.push_screen_wait(
                    PresetDetailsScreen(preset_name, self.config_template_manager)
                )
                if result and result.get("action") == "use":
                    self._apply_preset(result.get("preset_name"))

            # Use for Project
            elif button_id.startswith("use-"):
                preset_name = button_id.replace("use-", "")
                self._apply_preset(preset_name)

            # Delete
            elif button_id.startswith("delete-"):
                preset_name = button_id.replace("delete-", "")
                await self._delete_preset(preset_name)

            # Create New Preset
            elif button_id == "btn-create-preset":
                result = await self.app.push_screen_wait(CreatePresetScreen())
                if result and result.get("action") == "create":
                    await self._create_preset(
                        result.get("name"), result.get("description")
                    )
        except asyncio.CancelledError:
            # User cancelled the operation (pressed Escape) - this is normal
            pass

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

    async def _delete_preset(self, preset_name: str) -> None:
        """Delete a preset."""
        try:
            self.config_template_manager.delete_global_preset(preset_name)
            self.app.notify(f"Deleted preset '{preset_name}'", severity="information")

            # Refresh the panel
            self.refresh(recompose=True)

        except ValueError as e:
            self.app.notify(str(e), severity="error")
        except Exception as e:
            self.app.notify(f"Error deleting preset: {e}", severity="error")

    async def _create_preset(self, name: str, description: str) -> None:
        """Create a new preset from current config."""
        try:
            self.config_template_manager.save_global_preset(name, description)
            self.app.notify(
                f"Created preset '{name}' successfully!", severity="information"
            )

            # Refresh the panel
            self.refresh(recompose=True)

        except ValueError as e:
            self.app.notify(str(e), severity="error")
        except FileNotFoundError as e:
            self.app.notify(str(e), severity="error")
        except Exception as e:
            self.app.notify(f"Error creating preset: {e}", severity="error")
