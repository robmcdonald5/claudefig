"""Project overview screen showing stats and quick actions."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from claudefig.config import Config
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileInstance, FileType
from claudefig.tui.base import BackButtonMixin
from claudefig.tui.widgets import OverlayDropdown


class OverviewScreen(Screen, BackButtonMixin):
    """Screen displaying project overview with stats and quick actions."""

    BINDINGS = [
        ("escape", "collapse_or_back", "Collapse/Back"),
        ("backspace", "collapse_or_back", "Collapse/Back"),
    ]

    def __init__(
        self,
        config: Config,
        instance_manager: FileInstanceManager,
        **kwargs,
    ) -> None:
        """Initialize overview screen.

        Args:
            config: Configuration object
            instance_manager: FileInstanceManager for stats
        """
        super().__init__(**kwargs)
        self.config = config
        self.instance_manager = instance_manager

    def compose(self) -> ComposeResult:
        """Compose the overview screen."""
        with Container(id="overview-screen"):
            # Title
            yield Label("PROJECT OVERVIEW", classes="screen-title")

            # Config info - single compact line
            config_path = str(self.config.config_path)
            # Shorten path if too long
            if len(config_path) > 50:
                config_path = "..." + config_path[-47:]

            schema_version = self.config.get('claudefig.schema_version', 'unknown')

            yield Static(
                f"Config: {config_path} | Schema: {schema_version}",
                classes="overview-info-line"
            )

            # SECTION 1: Health Status - OVERLAY DROPDOWN
            status, errors, warnings = self._calculate_health()
            status_text = self._format_health_status(status, errors, warnings)

            yield OverlayDropdown(
                title=f"STATUS: {status_text.split(':')[1].strip()}",
                expanded=False,
                id="status-dropdown"
            )

            # SECTION 2: Files - OVERLAY DROPDOWN
            instances = self.instance_manager.list_instances()
            total = len(instances)
            enabled = sum(1 for i in instances if i.enabled)
            disabled = total - enabled

            yield OverlayDropdown(
                title=f"FILES IN CONFIG ({total} total, {enabled} enabled, {disabled} disabled)",
                expanded=False,
                id="files-dropdown"
            )

            # SECTION 3: Settings - OVERLAY DROPDOWN
            yield OverlayDropdown(
                title="INITIALIZATION SETTINGS",
                expanded=False,
                id="settings-dropdown"
            )

            # Back button
            yield from self.compose_back_button()

    def on_mount(self) -> None:
        """Called when screen is mounted - populate dropdown content."""
        # Populate STATUS dropdown
        status, errors, warnings = self._calculate_health()
        status_dropdown = self.query_one("#status-dropdown", OverlayDropdown)
        status_content = []

        if errors:
            status_content.append(Static("Errors:", classes="overview-section-header error"))
            for error in errors:
                status_content.append(Static(f"  ✗ {error}", classes="overview-error-item"))

        if warnings:
            if errors:
                status_content.append(Static(""))  # Spacer
            status_content.append(Static("Warnings:", classes="overview-section-header warning"))
            for warning in warnings:
                status_content.append(Static(f"  ⚠ {warning}", classes="overview-warning-item"))

        if not errors and not warnings:
            status_content.append(Static("✓ All enabled file instances are valid", classes="overview-healthy-item"))

        status_dropdown.set_content(*status_content)

        # Populate FILES dropdown
        instances = self.instance_manager.list_instances()
        files_dropdown = self.query_one("#files-dropdown", OverlayDropdown)
        files_content = []

        if len(instances) == 0:
            files_content.append(Static("No file instances configured", classes="file-disabled"))
        else:
            for instance in sorted(instances, key=self._file_sort_key):
                icon = "✓" if instance.enabled else "-"
                suffix = " (disabled)" if not instance.enabled else ""
                css_class = "file-enabled" if instance.enabled else "file-disabled"
                files_content.append(Static(f"{icon} {instance.path}{suffix}", classes=css_class))

        files_dropdown.set_content(*files_content)

        # Populate SETTINGS dropdown
        overwrite = "Yes" if self.config.get('init.overwrite_existing') else "No"
        backup = "Yes" if self.config.get('init.create_backup', True) else "No"

        settings_dropdown = self.query_one("#settings-dropdown", OverlayDropdown)
        settings_dropdown.set_content(
            Static(f"• Overwrite existing files: {overwrite}"),  # type: ignore[arg-type]
            Static(f"• Create backup files: {backup}")  # type: ignore[arg-type]
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        self.handle_back_button(event)

    def on_click(self, event) -> None:
        """Handle clicks on the screen - close other dropdowns when one opens."""
        # Walk up to find if a dropdown was clicked
        current = event.widget
        while current:
            if isinstance(current, OverlayDropdown):
                # Schedule closing other dropdowns after this click completes
                self.call_after_refresh(self._close_other_dropdowns, current)
                break
            current = current.parent

    def on_key(self, event) -> None:
        """Handle key presses - close other dropdowns when one is toggled with Enter."""
        if event.key == "enter":
            focused = self.app.focused
            current = focused
            while current:
                if isinstance(current, OverlayDropdown):
                    # Schedule closing other dropdowns after Enter is processed
                    self.call_after_refresh(self._close_other_dropdowns, current)
                    break
                current = current.parent

    def _close_other_dropdowns(self, keep_open: OverlayDropdown) -> None:
        """Close all dropdowns except the specified one.

        Args:
            keep_open: The dropdown to keep open (if expanded)
        """
        for dropdown in self.query(OverlayDropdown):
            if dropdown != keep_open and dropdown.expanded:
                dropdown.collapse()

    def action_collapse_or_back(self) -> None:
        """Collapse focused dropdown section or go back if none focused."""
        # Get the currently focused widget
        focused = self.app.focused

        # Check if focus is within an OverlayDropdown
        if focused:
            # Walk up the DOM tree to find an OverlayDropdown
            current = focused
            while current:
                if isinstance(current, OverlayDropdown):
                    # If expanded, collapse it
                    if current.expanded:
                        current.collapse()
                        return
                    break
                current = current.parent

        # If no dropdown to collapse, go back
        self.app.pop_screen()

    def _calculate_health(self) -> tuple[str, list[str], list[str]]:
        """Validate all instances and return health status.

        Returns:
            Tuple of (status, errors, warnings) where status is 'healthy', 'warning', or 'error'
        """
        all_errors = []
        all_warnings = []

        for instance in self.instance_manager.list_instances():
            # Only validate enabled instances
            if instance.enabled:
                result = self.instance_manager.validate_instance(instance, is_update=True)
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)

        if all_errors:
            return ("error", all_errors, all_warnings)
        elif all_warnings:
            return ("warning", all_errors, all_warnings)
        else:
            return ("healthy", all_errors, all_warnings)

    def _format_health_status(self, status: str, errors: list[str], warnings: list[str]) -> str:
        """Format health status message.

        Args:
            status: Health status ('healthy', 'warning', or 'error')
            errors: List of error messages
            warnings: List of warning messages

        Returns:
            Formatted status string
        """
        instances = self.instance_manager.list_instances()
        total = len(instances)
        enabled = sum(1 for i in instances if i.enabled)

        if status == "healthy":
            return f"STATUS: ✓ Healthy - {enabled} enabled instance{'s' if enabled != 1 else ''}, all valid"
        elif status == "warning":
            return f"STATUS: ⚠ Warning - {len(warnings)} warning(s) found"
        else:
            return f"STATUS: ✗ Error - {len(errors)} error(s), {len(warnings)} warning(s)"

    def _file_sort_key(self, instance: FileInstance) -> tuple:
        """Sort files logically: enabled first, then by type priority, then path.

        Args:
            instance: File instance to generate sort key for

        Returns:
            Sort key tuple
        """
        # Type priority (core files first)
        type_priority = {
            FileType.CLAUDE_MD: 0,
            FileType.SETTINGS_JSON: 1,
            FileType.SETTINGS_LOCAL_JSON: 2,
            FileType.GITIGNORE: 3,
            FileType.COMMANDS: 4,
            FileType.AGENTS: 5,
            FileType.HOOKS: 6,
            FileType.MCP: 7,
            FileType.OUTPUT_STYLES: 8,
            FileType.STATUSLINE: 9,
        }

        return (
            0 if instance.enabled else 1,  # Enabled first
            type_priority.get(instance.type, 99),  # Then by type
            instance.path  # Then alphabetically
        )
