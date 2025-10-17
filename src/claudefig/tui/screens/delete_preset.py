"""Delete preset modal screen."""

from textual.app import ComposeResult
from textual.widgets import Button, Label

from claudefig.tui.base import BaseModalScreen


class DeletePresetScreen(BaseModalScreen):
    """Modal screen to confirm deleting a preset."""

    def __init__(self, preset_name: str, **kwargs) -> None:
        """Initialize delete preset screen.

        Args:
            preset_name: Name of preset to delete
        """
        super().__init__(**kwargs)
        self.preset_name = preset_name

    def compose_title(self) -> str:
        """Return the modal title."""
        return "Delete Preset"

    def compose_content(self) -> ComposeResult:
        """Compose the modal content."""
        yield Label(
            f"Are you sure you want to delete preset '{self.preset_name}'?",
            classes="dialog-text",
        )
        yield Label(
            "\nWARNING: This action cannot be undone!",
            classes="dialog-warning",
        )
        yield Label(
            "The preset file will be permanently removed from ~/.claudefig/presets/",
            classes="dialog-warning",
        )

    def compose_actions(self) -> ComposeResult:
        """Compose the action buttons."""
        yield Button("Delete", id="btn-delete", variant="error")
        yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-cancel":
            self.dismiss()
        elif event.button.id == "btn-delete":
            self.dismiss(result={"action": "delete", "preset_name": self.preset_name})
