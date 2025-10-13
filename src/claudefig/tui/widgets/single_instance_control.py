"""Single instance control widget for file types that allow only one instance."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label, Static, Switch

from claudefig.models import FileInstance, FileType
from claudefig.preset_manager import PresetManager


class SingleInstanceControl(Container):
    """Control for single-instance file types (settings.json, etc).

    Displays a toggle switch, status label, fixed location info, and configure button
    for file types that only allow one instance per project.
    """

    def __init__(
        self,
        file_type: FileType,
        instance: FileInstance | None,
        preset_manager: PresetManager,
        **kwargs,
    ) -> None:
        """Initialize single instance control.

        Args:
            file_type: The single-instance file type
            instance: Existing instance or None if not configured
            preset_manager: For loading available presets
        """
        super().__init__(**kwargs)
        self.file_type = file_type
        self.instance = instance
        self.preset_manager = preset_manager

    def compose(self) -> ComposeResult:
        """Compose the single instance control."""
        # Header with file type name
        yield Label(self.file_type.display_name, classes="section-header")

        # Enable/Disable switch
        with Horizontal(classes="setting-row"):
            yield Switch(
                value=self.instance.enabled if self.instance else False,
                id=f"switch-{self.file_type.value}",
            )
            yield Static(
                f"Enable {self.file_type.display_name}",
                classes="setting-description",
            )

        # Status label
        status = self._get_status_text()
        status_class = "instance-enabled" if (self.instance and self.instance.enabled) else "instance-disabled"
        yield Label(f"Status: {status}", classes=f"setting-sublabel {status_class}")

        # Fixed location (read-only)
        yield Label(
            f"Location: {self.file_type.default_path}",
            classes="setting-description",
        )

        # Configure button (opens edit dialog)
        # Only enabled when instance exists and is enabled
        configure_enabled = self.instance and self.instance.enabled
        yield Button(
            "Configure",
            id=f"configure-{self.file_type.value}",
            disabled=not configure_enabled,
        )

    def _get_status_text(self) -> str:
        """Get status text for the current instance state.

        Returns:
            Status string: "Not Configured", "Enabled", or "Disabled"
        """
        if not self.instance:
            return "Not Configured"
        return "Enabled" if self.instance.enabled else "Disabled"
