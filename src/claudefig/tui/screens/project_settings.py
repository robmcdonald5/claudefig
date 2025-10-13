"""Project settings screen for editing config values."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static, Switch

from claudefig.config import Config


class ProjectSettingsScreen(Screen):
    """Screen for editing project configuration settings."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize project settings screen.

        Args:
            config: Configuration object
        """
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the project settings screen."""
        with Container(id="project-settings-screen"):
            yield Label("PROJECT SETTINGS", classes="screen-title")

            # Initialization settings
            with Vertical(classes="settings-section"):
                yield Label("Initialization Settings", classes="section-header")

                with Vertical(classes="setting-item"):
                    yield Label("Overwrite Existing Files:", classes="setting-label")
                    overwrite = self.config.get("init.overwrite_existing", False)
                    yield Switch(value=overwrite, id="switch-overwrite")
                    yield Static(
                        "Allow overwriting files that already exist during init",
                        classes="setting-description"
                    )

            # Custom paths settings
            with Vertical(classes="settings-section"):
                yield Label("Custom Paths", classes="section-header")

                with Vertical(classes="setting-item"):
                    yield Label("Template Directory:", classes="setting-label")
                    template_dir = self.config.get("custom.template_dir", "")
                    yield Input(
                        placeholder="Path to custom templates (optional)",
                        value=template_dir,
                        id="input-template-dir"
                    )

                with Vertical(classes="setting-item"):
                    yield Label("Presets Directory:", classes="setting-label")
                    presets_dir = self.config.get("custom.presets_dir", "")
                    yield Input(
                        placeholder="Path to custom presets (optional)",
                        value=presets_dir,
                        id="input-presets-dir"
                    )

            # Action buttons
            with Container(classes="screen-footer"):
                with Horizontal(classes="action-buttons"):
                    yield Button("Save Changes", id="btn-save", variant="primary")
                    yield Button("← Back", id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-save":
            self._save_settings()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch changes and auto-save."""
        if event.switch.id == "switch-overwrite":
            self.config.set("init.overwrite_existing", event.value)
            self.config.save()
            self.notify("Setting saved", severity="information")

    def _save_settings(self) -> None:
        """Save all settings to config."""
        try:
            # Get input values
            template_dir_input = self.query_one("#input-template-dir", Input)
            presets_dir_input = self.query_one("#input-presets-dir", Input)

            # Update config
            self.config.set("custom.template_dir", template_dir_input.value.strip())
            self.config.set("custom.presets_dir", presets_dir_input.value.strip())

            # Save
            self.config.save()

            self.notify("Settings saved successfully!", severity="information")
        except Exception as e:
            self.notify(f"Error saving settings: {e}", severity="error")
