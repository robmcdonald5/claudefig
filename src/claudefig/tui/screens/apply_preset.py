"""Apply preset modal screen."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label


class ApplyPresetScreen(Screen):
    """Modal screen to confirm applying a preset."""

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("backspace", "dismiss", "Cancel"),
        ("left", "focus_previous", "Focus previous"),
        ("right", "focus_next", "Focus next"),
    ]

    def __init__(self, preset_name: str, **kwargs) -> None:
        """Initialize apply preset screen.

        Args:
            preset_name: Name of preset to apply
        """
        super().__init__(**kwargs)
        self.preset_name = preset_name

    def compose(self) -> ComposeResult:
        """Compose the apply preset screen."""
        with Container(id="dialog-container"):
            yield Label("Apply Preset", classes="dialog-header")

            with VerticalScroll(id="dialog-content"):
                yield Label(
                    f"Apply preset '{self.preset_name}' to current directory?",
                    classes="dialog-text",
                )

                # Check if .claudefig.toml already exists
                config_path = Path.cwd() / ".claudefig.toml"
                if config_path.exists():
                    yield Label(
                        "\nWARNING: .claudefig.toml already exists in this directory!",
                        classes="dialog-warning",
                    )
                    yield Label(
                        "Applying this preset will overwrite the existing configuration.",
                        classes="dialog-warning",
                    )

            with Horizontal(classes="dialog-actions"):
                yield Button("Apply", id="btn-apply", variant="primary")
                yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-cancel":
            self.dismiss()
        elif event.button.id == "btn-apply":
            self.dismiss(result={"action": "apply", "preset_name": self.preset_name})

    def action_focus_previous(self) -> None:
        """Navigate focus to the previous focusable widget (left arrow)."""
        self.screen.focus_previous()

    def action_focus_next(self) -> None:
        """Navigate focus to the next focusable widget (right arrow)."""
        self.screen.focus_next()
