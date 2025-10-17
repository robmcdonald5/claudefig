"""General config editor screen."""

from pathlib import Path
from typing import Union

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from claudefig.config import Config
from claudefig.tui.base import BackButtonMixin


class GeneralConfigScreen(Screen, BackButtonMixin):
    """Screen for editing general configuration settings."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("backspace", "go_back", "Back"),
    ]

    config: reactive[Config] = reactive(lambda: Config())

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize the general config screen.

        Args:
            config: Config instance to edit
        """
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the general config editor."""
        yield Label("General Configuration", classes="screen-title")
        yield Label("Edit any configuration setting", classes="screen-subtitle")

        with VerticalScroll(classes="content-area"):
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

        if self.config and self.config.data:
            format_dict(self.config.data)
            return "\n".join(lines)
        else:
            return "No configuration loaded"

    def _parse_value(self, value_str: str) -> Union[str, bool, int, float]:
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
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # Return as string
        return value_str

    @on(Button.Pressed, "#btn-set")
    def handle_set(self) -> None:
        """Handle Set Value button press."""
        key_input = self.query_one("#key-input", Input)
        value_input = self.query_one("#value-input", Input)

        key = key_input.value.strip()
        value_str = value_input.value.strip()

        if not key:
            self.app.notify("Please enter a key", severity="warning")
            return

        if not value_str:
            self.app.notify("Please enter a value", severity="warning")
            return

        try:
            # Parse value
            parsed_value = self._parse_value(value_str)

            # Set in config
            self.config.set(key, parsed_value)

            # Save to file
            if self.config.config_path:
                self.config.save(self.config.config_path)
            else:
                # Save to current directory
                config_path = Path.cwd() / ".claudefig.toml"
                self.config.save(config_path)

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

        except Exception as e:
            self.app.notify(f"Error setting config: {e}", severity="error")

    @on(Button.Pressed, "#btn-refresh")
    def handle_refresh(self) -> None:
        """Handle Refresh Display button press."""
        # Reload config from disk
        if self.config.config_path and self.config.config_path.exists():
            self.config = Config(config_path=self.config.config_path)
        else:
            self.config = Config()

        # Refresh display
        config_display = self.query_one("#config-display", Static)
        config_display.update(self._format_config())

        self.app.notify("Configuration refreshed", severity="information")
