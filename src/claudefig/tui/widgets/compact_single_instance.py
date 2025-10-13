"""Compact single instance control for inline display."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static, Switch

from claudefig.models import FileInstance, FileType


class CompactSingleInstanceControl(Horizontal):
    """Compact one-line control for single-instance file types.

    Shows: [Switch] File Type Name [Configure Button]
    """

    def __init__(
        self,
        file_type: FileType,
        instance: FileInstance | None,
        **kwargs,
    ) -> None:
        """Initialize compact single instance control.

        Args:
            file_type: The single-instance file type
            instance: Existing instance or None if not configured
        """
        super().__init__(**kwargs)
        self.file_type = file_type
        self.instance = instance

    def compose(self) -> ComposeResult:
        """Compose the compact control."""
        # Switch for enable/disable
        yield Switch(
            value=self.instance.enabled if self.instance else False,
            id=f"switch-{self.file_type.value}",
        )

        # File type name with status
        status = ""
        if self.instance:
            status = " ✓" if self.instance.enabled else " (disabled)"

        yield Static(
            f"{self.file_type.display_name}{status}",
            classes="compact-instance-name",
        )

        # Configure button
        configure_enabled = self.instance and self.instance.enabled
        yield Button(
            "Configure",
            id=f"configure-{self.file_type.value}",
            disabled=not configure_enabled,
            classes="compact-configure-btn",
        )
