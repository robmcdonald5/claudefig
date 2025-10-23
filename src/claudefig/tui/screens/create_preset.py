"""Create preset modal screen."""

from textual.app import ComposeResult
from textual.widgets import Button, Input, Label

from claudefig.tui.base import BaseModalScreen


class CreatePresetScreen(BaseModalScreen):
    """Modal screen to create a new preset from current config."""

    def compose_title(self) -> str:
        """Return the modal title."""
        return ""

    def compose_content(self) -> ComposeResult:
        """Compose the modal content."""
        yield Label("Name:", classes="dialog-label")
        yield Input(placeholder="my-custom-preset", id="input-preset-name")
        yield Label("Description (optional):", classes="dialog-label")
        yield Input(
            placeholder="My custom configuration", id="input-preset-description"
        )

    def compose_actions(self) -> ComposeResult:
        """Compose the action buttons."""
        yield Button("Create", id="btn-create")
        yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-cancel":
            self.dismiss()
        elif event.button.id == "btn-create":
            name_input = self.query_one("#input-preset-name", Input)
            desc_input = self.query_one("#input-preset-description", Input)

            preset_name = name_input.value.strip()
            description = desc_input.value.strip()

            if not preset_name:
                self.notify("Preset name is required", severity="error")
                return

            self.dismiss(
                result={
                    "action": "create",
                    "name": preset_name,
                    "description": description,
                }
            )
