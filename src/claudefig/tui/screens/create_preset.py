"""Create preset modal screen."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label


class CreatePresetScreen(Screen):
    """Modal screen to create a new preset from current config."""

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("backspace", "dismiss", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the create preset screen."""
        with Container(id="dialog-container"):
            yield Label("Create New Preset", classes="dialog-header")

            with VerticalScroll(id="dialog-content"):
                yield Label("Preset Name:", classes="dialog-label")
                yield Input(placeholder="my-custom-preset", id="input-preset-name")

                yield Label("\nDescription (optional):", classes="dialog-label")
                yield Input(placeholder="My custom configuration", id="input-preset-description")

            with Horizontal(classes="dialog-actions"):
                yield Button("Create", id="btn-create", variant="primary")
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

            self.dismiss(result={
                "action": "create",
                "name": preset_name,
                "description": description
            })
