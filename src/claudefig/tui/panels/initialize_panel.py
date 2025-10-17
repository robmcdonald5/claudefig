"""Initialize panel for project setup."""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Label, Select

from claudefig.config import Config
from claudefig.config_template_manager import ConfigTemplateManager


class InitializePanel(Container):
    """Initialize project panel with preset selection."""

    def __init__(self, config: Config, on_switch_to_presets, **kwargs) -> None:
        """Initialize panel.

        Args:
            config: Config instance
            on_switch_to_presets: Callback to switch to presets panel
        """
        super().__init__(**kwargs)
        self.config = config
        self.on_switch_to_presets_callback = on_switch_to_presets
        self.config_template_manager = ConfigTemplateManager()
        self.selected_preset: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Compose the initialize panel."""
        with VerticalScroll():
            yield Label("Initialize Claude Code Files", classes="panel-title")

            # Check if .claudefig.toml already exists
            config_path = Path.cwd() / ".claudefig.toml"
            if config_path.exists():
                yield Label(
                    "Configuration already exists!", classes="config-summary-title"
                )
                yield Label(
                    "Found .claudefig.toml in current directory.\n\n"
                    "Go to the 'Config' panel to manage your existing configuration, "
                    "or go to 'Presets' to apply a different preset (will overwrite).",
                    classes="panel-info",
                )
                with Horizontal(classes="button-row"):
                    yield Button("Go to Config", id="btn-go-config")
                    yield Button("Go to Presets", id="btn-go-presets")
                return

            yield Label(
                "Select a preset template to generate Claude Code files for this project.",
                classes="panel-info",
            )

            # Preset selection
            yield Label("Select Preset:", classes="config-summary-title")

            presets = self.config_template_manager.list_global_presets()
            if presets:
                preset_options = [
                    (preset["name"], preset["name"]) for preset in presets
                ]
                # Default to "default" preset
                default_preset = (
                    "default"
                    if any(p["name"] == "default" for p in presets)
                    else preset_options[0][1]
                )
                self.selected_preset = default_preset

                yield Select(
                    options=preset_options,
                    value=default_preset,
                    id="select-preset",
                    allow_blank=False,
                )

                # Preset preview
                yield Label("\nPreset Preview:", classes="config-summary-title")
                yield Label("", id="preset-preview-content", classes="config-summary")

            else:
                yield Label(
                    "No presets found! This shouldn't happen - the default preset should exist.",
                    classes="placeholder",
                )
                return

            # Action buttons
            with Horizontal(classes="button-row"):
                yield Button(
                    "Start Initialization", id="btn-start-init", variant="primary"
                )
                yield Button("Manage Presets", id="btn-manage-presets")

    def on_mount(self) -> None:
        """Update preview when mounted."""
        if self.selected_preset:
            self._update_preset_preview(self.selected_preset)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle preset selection change."""
        if event.select.id == "select-preset" and isinstance(event.value, str):
            # Ensure value is a string
            self.selected_preset = event.value
            self._update_preset_preview(event.value)

    def _update_preset_preview(self, preset_name: str) -> None:
        """Update the preset preview display.

        Args:
            preset_name: Name of preset to preview
        """
        try:
            # Load preset config
            preset_config = self.config_template_manager.get_preset_config(preset_name)
            preset_list = self.config_template_manager.list_global_presets()
            preset_info = next(
                (p for p in preset_list if p["name"] == preset_name), None
            )

            preview_lines = []

            if preset_info:
                preview_lines.append(
                    f"Description: {preset_info.get('description', 'N/A')}"
                )
                preview_lines.append(f"File Count: {preset_info.get('file_count', 0)}")

            # Show file instances that will be created
            files = preset_config.get_file_instances()
            if files:
                preview_lines.append("\nFiles that will be configured:")
                for file_inst in files:
                    file_type = file_inst.get("type", "?")
                    path = file_inst.get("path", "?")
                    enabled = file_inst.get("enabled", True)
                    status = "✓" if enabled else "✗"
                    preview_lines.append(f"  {status} {file_type}: {path}")
            else:
                preview_lines.append("\nNo file instances in this preset.")

            preview_content = "\n".join(preview_lines)

            # Update preview label
            try:
                preview_label = self.query_one("#preset-preview-content", Label)
                preview_label.update(preview_content)
            except Exception:
                pass

        except Exception as e:
            try:
                preview_label = self.query_one("#preset-preview-content", Label)
                preview_label.update(f"Error loading preset preview: {e}")
            except Exception:
                pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-manage-presets":
            self.on_switch_to_presets_callback()
            event.stop()
        elif event.button.id == "btn-go-config":
            # Switch to config panel
            from claudefig.tui.app import MainScreen

            if isinstance(self.app, MainScreen):
                self.app._activate_section("config")
            event.stop()
        elif event.button.id == "btn-go-presets":
            self.on_switch_to_presets_callback()
            event.stop()
        elif event.button.id == "btn-start-init":
            await self._start_initialization()
            event.stop()

    async def _start_initialization(self) -> None:
        """Start the initialization process."""
        if not self.selected_preset:
            self.app.notify("No preset selected", severity="error")
            return

        try:
            # Step 1: Apply preset (creates .claudefig.toml)
            self.app.notify(
                f"Applying preset '{self.selected_preset}'...", severity="information"
            )
            self.config_template_manager.apply_preset_to_project(self.selected_preset)

            # Step 2: Reload config after applying preset
            self.config = Config()

            # Step 3: Run initializer to generate files
            from claudefig.initializer import Initializer

            self.app.notify("Generating files...", severity="information")
            initializer = Initializer(self.config)

            # Generate files
            success = initializer.initialize(Path.cwd(), force=False)

            # Step 4: Show success summary
            if success:
                self.app.notify(
                    "Initialization complete! Files generated successfully.",
                    severity="information",
                    timeout=5,
                )
            else:
                self.app.notify(
                    "Initialization completed with warnings. Check logs for details.",
                    severity="warning",
                    timeout=5,
                )

            # Step 5: Switch to Config panel
            from claudefig.tui.app import MainScreen

            if isinstance(self.app, MainScreen):
                # Reload config in app
                self.app.config = Config()
                self.app._activate_section("config")

        except FileExistsError:
            self.app.notify(
                ".claudefig.toml already exists! Go to Presets panel to overwrite.",
                severity="error",
            )
        except Exception as e:
            self.app.notify(f"Initialization failed: {e}", severity="error")
