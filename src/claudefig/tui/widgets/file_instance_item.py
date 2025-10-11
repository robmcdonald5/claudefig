"""File instance item widget for displaying file instance information."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label

from claudefig.models import FileInstance


class FileInstanceItem(Container):
    """Display file instance with edit actions."""

    def __init__(self, instance: FileInstance, **kwargs) -> None:
        """Initialize file instance item.

        Args:
            instance: FileInstance object
        """
        super().__init__(**kwargs)
        self.instance = instance

    def compose(self) -> ComposeResult:
        """Compose the file instance item."""
        yield Label(f"Path: {self.instance.path}", classes="instance-path")
        yield Label(f"Preset: {self.instance.preset}", classes="instance-preset")

        status_text = "+ Enabled" if self.instance.enabled else "- Disabled"
        status_class = "instance-enabled" if self.instance.enabled else "instance-disabled"
        yield Label(status_text, classes=f"instance-status {status_class}")

        with Horizontal(classes="instance-actions"):
            yield Button("Edit", id=f"edit-{self.instance.id}", classes="instance-button")
            yield Button("Remove", id=f"remove-{self.instance.id}", classes="instance-button")
            yield Button("Toggle", id=f"toggle-{self.instance.id}", classes="instance-button")
