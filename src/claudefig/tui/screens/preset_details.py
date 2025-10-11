"""Preset details modal screen."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label

from claudefig.config_template_manager import ConfigTemplateManager


class PresetDetailsScreen(Screen):
    """Modal screen to view preset details."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("backspace", "dismiss", "Close"),
    ]

    def __init__(self, preset_name: str, config_template_manager: ConfigTemplateManager, **kwargs) -> None:
        """Initialize preset details screen.

        Args:
            preset_name: Name of the preset to display
            config_template_manager: ConfigTemplateManager instance
        """
        super().__init__(**kwargs)
        self.preset_name = preset_name
        self.config_template_manager = config_template_manager

    def compose(self) -> ComposeResult:
        """Compose the preset details screen."""
        try:
            # Load preset config
            preset_config = self.config_template_manager.get_preset_config(self.preset_name)
            preset_list = self.config_template_manager.list_global_presets()
            preset_info = next((p for p in preset_list if p["name"] == self.preset_name), None)

            with Container(id="dialog-container"):
                yield Label(f"Preset: {self.preset_name}", classes="dialog-header")

                with VerticalScroll(id="dialog-content"):
                    if preset_info:
                        yield Label(f"Description: {preset_info.get('description', 'N/A')}", classes="dialog-text")
                        yield Label(f"File Count: {preset_info.get('file_count', 0)}", classes="dialog-text")

                    yield Label("\nFile Instances:", classes="dialog-section-title")

                    files = preset_config.get_file_instances()
                    if files:
                        for file_inst in files:
                            yield Label(
                                f"  - {file_inst.get('type', '?')}: {file_inst.get('path', '?')} "
                                f"(preset: {file_inst.get('preset', '?')})",
                                classes="dialog-text"
                            )
                    else:
                        yield Label("  No file instances", classes="dialog-text")

                with Horizontal(classes="dialog-actions"):
                    yield Button("Use for Project", id="btn-use-preset", variant="primary")
                    yield Button("Close", id="btn-close")

        except Exception as e:
            yield Label(f"Error loading preset: {e}", classes="dialog-error")
            yield Button("Close", id="btn-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-close":
            self.dismiss()
        elif event.button.id == "btn-use-preset":
            self.dismiss(result={"action": "use", "preset_name": self.preset_name})
