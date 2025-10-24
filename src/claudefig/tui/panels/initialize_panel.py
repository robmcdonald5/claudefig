"""Initialize panel for project setup."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Label

from claudefig.config import Config
from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.exceptions import (
    ConfigFileExistsError,
    FileOperationError,
    InitializationRollbackError,
)


class InitializePanel(Container):
    """Initialize project panel."""

    # Disable up/down navigation - only left/right for horizontal button row
    BINDINGS = [
        ("up", "ignore_up", ""),
        ("down", "ignore_down", ""),
    ]

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

    def compose(self) -> ComposeResult:
        """Compose the initialize panel."""
        with VerticalScroll():
            yield Label("Initialize Claude Code Files", classes="panel-title")

            # Check if .claudefig.toml already exists
            config_path = Path.cwd() / ".claudefig.toml"

            if config_path.exists():
                # Show warning if config exists
                yield Label(
                    "⚠️  Warning: A .claudefig.toml file already exists in this directory.\n\n"
                    "Initializing again will generate files based on your current configuration settings. "
                    "This may override existing files.\n\n"
                    "To change presets or settings, use the 'Manage Presets' or 'Manage Config' buttons below.",
                    classes="panel-info",
                )
            else:
                # Show info if no config exists
                yield Label(
                    "No .claudefig.toml file found in this directory.\n\n"
                    "Initialization will use the default preset to create your configuration and generate files.\n\n"
                    "To use a different preset, click 'Manage Presets' below to apply one before initializing.",
                    classes="panel-info",
                )

            # Unified action buttons (same in both states)
            with Horizontal(classes="button-row"):
                yield Button("Initialize", id="btn-initialize")
                yield Button("Manage Presets", id="btn-manage-presets")
                yield Button("Manage Config", id="btn-manage-config")

    def action_ignore_up(self) -> None:
        """Ignore up navigation - no vertical elements on this page."""
        pass

    def action_ignore_down(self) -> None:
        """Ignore down navigation - no vertical elements on this page."""
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-manage-presets":
            self.on_switch_to_presets_callback()
            event.stop()
        elif event.button.id == "btn-manage-config":
            # Switch to config panel
            from claudefig.tui.app import MainScreen

            if isinstance(self.app, MainScreen):
                self.app._activate_section("config")
            event.stop()
        elif event.button.id == "btn-initialize":
            await self._start_initialization()
            event.stop()

    async def _start_initialization(self) -> None:
        """Start the initialization process."""
        from claudefig.exceptions import InitializationRollbackError
        from claudefig.initializer import Initializer
        from claudefig.tui.app import MainScreen
        from claudefig.tui.panels.content_panel import ContentPanel

        config_path = Path.cwd() / ".claudefig.toml"

        try:
            # Step 1: If no config exists, apply default preset first
            if not config_path.exists():
                self.app.notify("Applying default preset...", severity="information")
                self.config_template_manager.apply_preset_to_project("default")
                # Reload config after applying preset
                self.config = Config()

            # Step 2: Run initializer to generate files
            self.app.notify("Generating files...", severity="information")
            initializer = Initializer(self.config)

            # Generate files (skip_prompts=True for TUI non-interactive mode)
            success = initializer.initialize(Path.cwd(), force=False, skip_prompts=True)

            # Step 3: Reload config everywhere
            if isinstance(self.app, MainScreen):
                # Reload config in app
                self.app.config = Config()
                # Reload config in content panel so all panels get fresh config
                content_panel = self.app.query_one("#content-panel", ContentPanel)
                content_panel.config = self.app.config
                # Update local config reference
                self.config = self.app.config

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

        except InitializationRollbackError as e:
            # Initialization was rolled back due to errors
            error_details = e.details.get("errors", [])
            error_msg = "Initialization failed:\n" + "\n".join(
                f"  - {err}" for err in error_details
            )
            self.app.notify(
                error_msg,
                severity="error",
                timeout=10,
            )
        except FileOperationError as e:
            self.app.notify(str(e), severity="error")
        except ConfigFileExistsError as e:
            self.app.notify(str(e), severity="error")
        except FileExistsError:
            # Fallback for non-migrated code - backward compatibility
            self.app.notify(
                ".claudefig.toml already exists! Go to Presets panel to overwrite.",
                severity="error",
            )
        except Exception as e:
            self.app.notify(f"Initialization failed: {e}", severity="error")
