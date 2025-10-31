"""Preset details modal screen."""

from textual.app import ComposeResult
from textual.widgets import Button, Label

from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.exceptions import (
    FileReadError,
    PresetNotFoundError,
    TemplateNotFoundError,
)
from claudefig.tui.base import BaseModalScreen


class PresetDetailsScreen(BaseModalScreen):
    """Modal screen to view preset details."""

    def __init__(
        self, preset_name: str, config_template_manager: ConfigTemplateManager, **kwargs
    ) -> None:
        """Initialize preset details screen.

        Args:
            preset_name: Name of the preset to display
            config_template_manager: ConfigTemplateManager instance
        """
        super().__init__(**kwargs)
        self.preset_name = preset_name
        self.config_template_manager = config_template_manager

    def compose_title(self) -> str:
        """Return the modal title."""
        return f"Preset: {self.preset_name}"

    def compose_content(self) -> ComposeResult:
        """Compose the modal content."""
        try:
            # Load preset config
            preset_config = self.config_template_manager.get_preset_config(
                self.preset_name
            )
            preset_list = self.config_template_manager.list_global_presets()
            preset_info = next(
                (p for p in preset_list if p["name"] == self.preset_name), None
            )

            if preset_info:
                yield Label(
                    f"Description: {preset_info.get('description', 'N/A')}",
                    classes="dialog-text",
                )
                yield Label(
                    f"File Count: {preset_info.get('file_count', 0)}",
                    classes="dialog-text",
                )

            yield Label("\nFile Instances:", classes="dialog-section-title")

            files = preset_config.get_file_instances()
            if files:
                for file_inst in files:
                    yield Label(
                        f"  - {file_inst.get('type', '?')}: {file_inst.get('path', '?')} "
                        f"(preset: {file_inst.get('preset', '?')})",
                        classes="dialog-text",
                    )
            else:
                yield Label("  No file instances", classes="dialog-text")

        except PresetNotFoundError as e:
            yield Label(str(e), classes="dialog-error")
        except TemplateNotFoundError as e:
            yield Label(str(e), classes="dialog-error")
        except FileReadError as e:
            yield Label(str(e), classes="dialog-error")
        except FileNotFoundError as e:
            yield Label(f"Error loading preset: {e}", classes="dialog-error")
        except Exception as e:
            # Catch other unexpected errors
            yield Label(f"Error loading preset: {e}", classes="dialog-error")

    def compose_actions(self) -> ComposeResult:
        """Compose the action buttons."""
        yield Button("Use for Project", id="btn-use-preset", variant="primary")
        yield Button("Close", id="btn-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-close":
            self.dismiss()
        elif event.button.id == "btn-use-preset":
            self.dismiss(result={"action": "use", "preset_name": self.preset_name})
