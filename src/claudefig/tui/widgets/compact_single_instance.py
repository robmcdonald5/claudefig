"""Compact single instance control for inline display."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Select, Static, Switch

from claudefig.models import FileInstance, FileType
from claudefig.preset_manager import PresetManager


class CompactSingleInstanceControl(Horizontal):
    """Compact one-line control for single-instance file types.

    Shows: [Switch] File Type Name [Preset Dropdown]
    """

    # Container itself should not be focusable
    can_focus = False

    def __init__(
        self,
        file_type: FileType,
        instance: Optional[FileInstance],
        preset_manager: PresetManager,
        **kwargs,
    ) -> None:
        """Initialize compact single instance control.

        Args:
            file_type: The single-instance file type
            instance: Existing instance or None if not configured
            preset_manager: PresetManager for fetching available presets
        """
        super().__init__(**kwargs)
        self.file_type = file_type
        self.instance = instance
        self.preset_manager = preset_manager

    def _get_template_options(self) -> list[tuple[str, str]]:
        """Get available template options for this file type.

        Returns:
            List of (display_name, template_value) tuples
        """
        # Check if this file type uses template directories
        template_dir = self.file_type.template_directory
        extension = self.file_type.template_file_extension

        if template_dir and extension:
            # Scan the GLOBAL template directory (~/.claudefig/)
            global_claudefig = Path.home() / ".claudefig"
            template_path = global_claudefig / template_dir

            if not template_path.exists():
                return [("No templates available (directory not found)", "")]

            # Find all files with the correct extension
            template_files = sorted(template_path.glob(f"*{extension}"))

            if not template_files:
                return [(f"No {extension} templates found", "")]

            # Create options: display name = filename without extension, value = full filename
            options = []
            for template_file in template_files:
                name_without_ext = template_file.stem
                display_name = name_without_ext.replace("_", " ").title()
                options.append((display_name, name_without_ext))

            return options
        else:
            # Fall back to preset manager for other file types
            presets = self.preset_manager.list_presets(file_type=self.file_type)
            if not presets:
                return [("No presets available", "")]
            return [(f"{p.source.value}: {p.name}", p.id) for p in presets]

    def compose(self) -> ComposeResult:
        """Compose the compact control."""
        # Switch for enable/disable
        is_enabled = self.instance.enabled if self.instance else False
        yield Switch(
            value=is_enabled,
            id="switch-" + self.file_type.value,
            classes="compact-switch",
        )

        # File type name (not focusable)
        name_label = Static(
            f"{self.file_type.display_name}",
            classes="compact-instance-name",
        )
        name_label.can_focus = False
        yield name_label

        # Get available template options (from directories or preset manager)
        options = self._get_template_options()

        # Current selected template/preset
        # Extract just the name part if it's a full preset ID (backwards compatibility)
        current_value = ""
        if self.instance and self.instance.preset:
            preset_value = self.instance.preset
            # If it's a preset ID format (type:name), extract the name
            if ":" in preset_value:
                current_value = preset_value.split(":", 1)[1]
            else:
                current_value = preset_value
        elif options:
            current_value = options[0][1]

        # Validate that current_value is in the options list
        # If not, default to the first option
        if options:
            option_values = [opt[1] for opt in options]
            if current_value not in option_values:
                current_value = options[0][1]

        # Select dropdown for preset selection
        yield Select(
            options=options,
            value=current_value,
            id="preset-" + self.file_type.value,
            classes="compact-preset-select",
            disabled=not is_enabled,  # Disabled when switch is off
            allow_blank=False,
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch toggle."""
        # Enable/disable the Select dropdown
        select = self.query_one(f"#preset-{self.file_type.value}", Select)
        select.disabled = not event.value

        # Post message for parent screen to handle instance creation/deletion
        self.post_message(self.ToggleChanged(self.file_type, event.value))

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle preset selection."""
        if event.value:
            # Post message for parent screen to handle preset change
            self.post_message(self.PresetChanged(self.file_type, str(event.value)))

    def on_mount(self) -> None:
        """After mounting, make Select only focusable via left/right."""
        select = self.query_one(f"#preset-{self.file_type.value}", Select)
        # Prevent Select from being focused via tab/up/down
        select.can_focus = False

    def on_key(self, event) -> None:
        """Handle key presses for custom navigation."""
        switch = self.query_one(f"#switch-{self.file_type.value}", Switch)
        select = self.query_one(f"#preset-{self.file_type.value}", Select)

        focused = self.app.focused

        # Left/Right navigation within the row
        if event.key == "left":
            if focused == select:
                # Move from dropdown to switch
                select.can_focus = False
                switch.focus()
                event.prevent_default()
                event.stop()
        elif event.key == "right":
            if focused == switch and not select.disabled:
                # Move from switch to dropdown (only if enabled)
                select.can_focus = True
                select.focus()
                event.prevent_default()
                event.stop()

        # Up/Down navigation - only between switches, never to dropdowns
        elif event.key in ("up", "down"):
            # Get all switches in the screen
            all_switches = list(self.screen.query(Switch))

            if (
                focused in (switch, select)
                and switch in all_switches
                and len(all_switches) > 0
            ):
                # Make sure dropdown is not focusable
                select.can_focus = False

                current_idx = all_switches.index(switch)

                if event.key == "down":
                    # If on last switch, allow navigation to escape to other elements (like buttons)
                    if current_idx == len(all_switches) - 1:
                        # Don't intercept - let normal navigation continue
                        return
                    # Move to next switch
                    next_idx = current_idx + 1
                    all_switches[next_idx].focus()
                else:
                    # If on first switch, allow navigation to escape upwards
                    if current_idx == 0:
                        # Don't intercept - let normal navigation continue
                        return
                    # Move to previous switch
                    prev_idx = current_idx - 1
                    all_switches[prev_idx].focus()

                event.prevent_default()
                event.stop()

    # Custom messages for communication with parent screen
    class ToggleChanged(Message):
        """Posted when the switch is toggled."""

        def __init__(self, file_type: FileType, enabled: bool):
            super().__init__()
            self.file_type = file_type
            self.enabled = enabled

    class PresetChanged(Message):
        """Posted when a preset is selected."""

        def __init__(self, file_type: FileType, preset_id: str):
            super().__init__()
            self.file_type = file_type
            self.preset_id = preset_id
