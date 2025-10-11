"""File type section widget for grouping file instances by type."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Label

from claudefig.models import FileInstance, FileType
from claudefig.tui.widgets.file_instance_item import FileInstanceItem


class FileTypeSection(Container):
    """Group file instances by type."""

    def __init__(
        self, file_type: FileType, instances: list[FileInstance], **kwargs
    ) -> None:
        """Initialize file type section.

        Args:
            file_type: FileType enum value
            instances: List of FileInstance objects for this type
        """
        super().__init__(**kwargs)
        self.file_type = file_type
        self.instances = instances

    def compose(self) -> ComposeResult:
        """Compose the file type section."""
        yield Label(
            f"{self.file_type.display_name} ({len(self.instances)} instances)",
            classes="section-header",
        )

        for instance in self.instances:
            yield FileInstanceItem(instance, classes="instance-item")

        yield Button(
            f"+ Add {self.file_type.display_name} Instance",
            id=f"add-{self.file_type.value}",
            classes="add-instance-button",
        )
