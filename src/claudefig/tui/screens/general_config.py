"""General config editor screen."""

import contextlib
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, Static

from claudefig.exceptions import ConfigFileNotFoundError, FileWriteError
from claudefig.models import FileInstance
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.services import config_service
from claudefig.services.validation_service import validate_not_empty
from claudefig.tui.base import BaseScreen


class GeneralConfigScreen(BaseScreen):
    """Screen for editing general configuration settings.

    Inherits standard navigation bindings from BaseScreen with ScrollNavigationMixin
    support for smart vertical/horizontal navigation.

    Note: Previously had a bug where BINDINGS referenced non-existent action_go_back().
    Now correctly inherits action_pop_screen() from BaseScreen.
    """

    def __init__(
        self,
        config_data: dict[str, Any],
        config_repo: TomlConfigRepository,
        instances_dict: dict[str, FileInstance],
        **kwargs,
    ) -> None:
        """Initialize the general config screen.

        Args:
            config_data: Configuration dictionary
            config_repo: Configuration repository for saving
            instances_dict: Dictionary of file instances (id -> FileInstance)
        """
        super().__init__(**kwargs)
        self.config_data = config_data
        self.config_repo = config_repo
        self.instances_dict = instances_dict

    def compose_screen_content(self) -> ComposeResult:
        """Compose the general config editor content."""
        # can_focus=False prevents the container from being in the focus chain
        # while still allowing it to be scrolled programmatically
        with VerticalScroll(id="general-config-screen", can_focus=False):
            yield Label("General Configuration", classes="screen-title")
            yield Label("Edit any configuration setting", classes="screen-subtitle")
            # Current config display
            yield Label("Current Settings", classes="section-title")
            yield Static(
                self._format_config(), id="config-display", classes="config-display"
            )

            # Config editor
            yield Label("\nEdit Configuration", classes="section-title")
            yield Label(
                "Use dot notation for keys (e.g., 'init.overwrite_existing')",
                classes="help-text",
            )

            with Horizontal(classes="input-row"):
                yield Label("Key:", classes="input-label")
                yield Input(placeholder="e.g., init.overwrite_existing", id="key-input")

            with Horizontal(classes="input-row"):
                yield Label("Value:", classes="input-label")
                yield Input(placeholder="e.g., true", id="value-input")

            yield Label(
                "Tip: Use 'true'/'false' for booleans, numbers without quotes",
                classes="help-text",
            )

            with Horizontal(classes="button-row"):
                yield Button("Set Value", id="btn-set", variant="primary")
                yield Button("Refresh Display", id="btn-refresh")

            # Back button
            yield from self.compose_back_button()

    def _format_config(self) -> str:
        """Format config data for display.

        Returns:
            Formatted config string (excluding file instances)
        """
        lines = []

        def format_dict(d: dict, prefix: str = "") -> None:
            """Recursively format dictionary."""
            for key, value in sorted(d.items()):
                full_key = f"{prefix}.{key}" if prefix else key

                # Skip files array - it has its own screen
                if key == "files":
                    lines.append(f"{full_key}: <{len(value)} file instances>")
                    continue

                if isinstance(value, dict):
                    format_dict(value, full_key)
                elif isinstance(value, list):
                    lines.append(f"{full_key}: {value}")
                else:
                    lines.append(f"{full_key}: {value}")

        if self.config_data:
            format_dict(self.config_data)
            return "\n".join(lines)
        else:
            return "No configuration loaded"

    def _parse_value(self, value_str: str) -> str | bool | int | float:
        """Parse value string into appropriate type.

        Args:
            value_str: String value to parse

        Returns:
            Parsed value (string, bool, int, or float)
        """
        # Parse booleans
        if value_str.lower() in ("true", "false"):
            return value_str.lower() == "true"

        # Parse numbers
        with contextlib.suppress(ValueError):
            if "." in value_str:
                return float(value_str)
            return int(value_str)

        # Return as string
        return value_str

    @on(Button.Pressed, "#btn-set")
    def handle_set(self) -> None:
        """Handle Set Value button press."""
        key_input = self.query_one("#key-input", Input)
        value_input = self.query_one("#value-input", Input)

        key = key_input.value.strip()
        value_str = value_input.value.strip()

        # Validate inputs using centralized validation
        key_validation = validate_not_empty(key, "Key")
        if key_validation.has_errors:
            self.app.notify(key_validation.errors[0], severity="warning")
            return

        value_validation = validate_not_empty(value_str, "Value")
        if value_validation.has_errors:
            self.app.notify(value_validation.errors[0], severity="warning")
            return

        try:
            # Parse value
            parsed_value = self._parse_value(value_str)

            # Set in config
            config_service.set_value(self.config_data, key, parsed_value)

            # Save to file
            config_service.save_config(self.config_data, self.config_repo)

            self.app.notify(
                f"Set {key} = {parsed_value}",
                severity="information",
            )

            # Refresh display
            config_display = self.query_one("#config-display", Static)
            config_display.update(self._format_config())

            # Clear inputs
            key_input.value = ""
            value_input.value = ""

        except ConfigFileNotFoundError as e:
            self.app.notify(str(e), severity="error")
        except FileWriteError as e:
            self.app.notify(str(e), severity="error")
        except Exception as e:
            # Catch other unexpected errors (e.g., parsing errors)
            self.app.notify(f"Error setting config: {e}", severity="error")

    @on(Button.Pressed, "#btn-refresh")
    def handle_refresh(self) -> None:
        """Handle Refresh Display button press."""
        # Reload config from disk
        if self.config_repo.config_path.exists():
            self.config_data = config_service.load_config(self.config_repo)

        # Refresh display
        config_display = self.query_one("#config-display", Static)
        config_display.update(self._format_config())

        self.app.notify("Configuration refreshed", severity="information")
