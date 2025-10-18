"""Save component modal screen."""

from textual.app import ComposeResult
from textual.widgets import Button, Input, Label

from claudefig.tui.base import BaseModalScreen


class SaveComponentScreen(BaseModalScreen):
    """Modal screen to save a file instance as a reusable component."""

    def compose_title(self) -> str:
        """Return the modal title."""
        return "Save as Component"

    def compose_content(self) -> ComposeResult:
        """Compose the modal content."""
        yield Label("Component Name:", classes="dialog-label")
        yield Label(
            "Save this file instance to your component library for reuse across projects.",
            classes="dialog-text setting-description",
        )
        yield Input(
            placeholder="e.g., python-backend, react-frontend",
            id="input-component-name",
        )

    def compose_actions(self) -> ComposeResult:
        """Compose the action buttons."""
        yield Button("Save", id="btn-save", variant="primary")
        yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-cancel":
            self.dismiss()
        elif event.button.id == "btn-save":
            name_input = self.query_one("#input-component-name", Input)
            component_name = name_input.value.strip()

            if not component_name:
                self.notify("Component name is required", severity="error")
                return

            # Validate component name (alphanumeric, dashes, underscores)
            if not all(c.isalnum() or c in ("-", "_") for c in component_name):
                self.notify(
                    "Component name can only contain letters, numbers, dashes, and underscores",
                    severity="error",
                )
                return

            self.dismiss(result={"action": "save", "name": component_name})
