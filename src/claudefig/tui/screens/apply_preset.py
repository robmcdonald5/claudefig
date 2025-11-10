"""Apply preset modal screen."""

from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Button, Label

from claudefig.tui.base import BaseModalScreen


class ApplyPresetScreen(BaseModalScreen):
    """Modal screen to confirm applying a preset."""

    def __init__(self, preset_name: str, **kwargs) -> None:
        """Initialize apply preset screen.

        Args:
            preset_name: Name of preset to apply
        """
        super().__init__(**kwargs)
        self.preset_name = preset_name

    def compose_title(self) -> str:
        """Return the modal title."""
        return "Apply Preset"

    def compose_content(self) -> ComposeResult:
        """Compose the modal content."""
        yield Label(
            f"Apply preset '{self.preset_name}' to current directory?",
            classes="dialog-text",
        )

        # Check if claudefig.toml already exists
        config_path = Path.cwd() / "claudefig.toml"
        if config_path.exists():
            yield Label(
                "\nWARNING: claudefig.toml already exists in this directory!",
                classes="dialog-warning",
            )
            yield Label(
                "Applying this preset will overwrite the existing configuration.",
                classes="dialog-warning",
            )

    def compose_actions(self) -> ComposeResult:
        """Compose the action buttons."""
        yield Button("Apply", id="btn-apply")
        yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-cancel":
            self.dismiss()
        elif event.button.id == "btn-apply":
            self.dismiss(result={"action": "apply", "preset_name": self.preset_name})
