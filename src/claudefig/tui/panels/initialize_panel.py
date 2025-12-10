"""Initialize panel for project setup."""

import contextlib
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.events import Key
from textual.widgets import Button, Label

from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.exceptions import (
    ConfigFileExistsError,
    FileOperationError,
    InitializationRollbackError,
)
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.services import config_service
from claudefig.tui.base import BaseHorizontalNavigablePanel


class InitializePanel(BaseHorizontalNavigablePanel):
    """Initialize project panel with horizontal-only navigation.

    Inherits from BaseHorizontalNavigablePanel which provides horizontal-only
    navigation for the button row. Vertical navigation is automatically disabled.
    """

    def __init__(
        self,
        config_data: dict[str, Any],
        config_repo: TomlConfigRepository,
        on_switch_to_presets,
        **kwargs,
    ) -> None:
        """Initialize panel.

        Args:
            config_data: Configuration data dictionary
            config_repo: Configuration repository
            on_switch_to_presets: Callback to switch to presets panel
        """
        super().__init__(**kwargs)
        self.config_data = config_data
        self.config_repo = config_repo
        self.on_switch_to_presets_callback = on_switch_to_presets
        self.config_template_manager = ConfigTemplateManager()

    def compose(self) -> ComposeResult:
        """Compose the initialize panel."""
        with VerticalScroll(can_focus=False):
            yield Label("Initialize Claude Code Files", classes="panel-title")

            # Check if claudefig.toml already exists
            config_path = Path.cwd() / "claudefig.toml"

            # IMPORTANT: Each Label must be ≤35 chars to avoid Textual layout bug
            # that causes menu-buttons border to stretch beyond bounds.
            # NOTE: Emojis count as 2+ terminal cells, avoid them!
            # See DEBUG_UI_BORDER_BUG.md for details.
            if config_path.exists():
                yield Label(
                    "WARNING: Config file exists", classes="panel-info"
                )  # 29 chars
                yield Label(
                    "Re-init may override files", classes="panel-info"
                )  # 27 chars
                yield Label(
                    "Use Presets/Config to change", classes="panel-info"
                )  # 32 chars
            else:
                yield Label("No config file found", classes="panel-info")  # 20 chars
                yield Label("Will use default preset", classes="panel-info")  # 25 chars
                yield Label(
                    "Use Presets to apply different", classes="panel-info"
                )  # 35 chars

            # Unified action buttons (same in both states)
            with Horizontal(classes="button-row"):
                yield Button("Initialize", id="btn-initialize")
                yield Button("Manage Presets", id="btn-manage-presets")
                yield Button("Manage Config", id="btn-manage-config")

    def on_key(self, event: Key) -> None:
        """Handle key events for navigation with scroll support.

        Explicitly handles up/down navigation to prevent the VerticalScroll
        container from intercepting arrow keys and provides scroll-to-reveal
        logic at boundaries.

        Args:
            event: The key event
        """
        focused = self.screen.focused
        if not focused:
            return

        # Get all buttons in the button row
        with contextlib.suppress(Exception):
            button_row = self.query_one(".button-row")
            buttons = [w for w in button_row.query("Button") if w.focusable]

            if not buttons or focused not in buttons:
                # Not in our button row, let normal handling continue
                return

            current_index = buttons.index(focused)

            if event.key == "up":
                # At the first button - scroll container to home (absolute top)
                if current_index == 0 or current_index == -1:
                    with contextlib.suppress(Exception):
                        scroll_container = self.query_one(VerticalScroll)
                        scroll_container.scroll_home(animate=True)
                        event.prevent_default()
                        event.stop()
                return

            elif event.key == "down":
                # At the last button - scroll container to end (absolute bottom)
                if current_index == len(buttons) - 1:
                    with contextlib.suppress(Exception):
                        scroll_container = self.query_one(VerticalScroll)
                        scroll_container.scroll_end(animate=True)
                        event.prevent_default()
                        event.stop()
                return

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
        from claudefig.initializer import Initializer
        from claudefig.tui.app import MainScreen
        from claudefig.tui.panels.content_panel import ContentPanel

        config_path = Path.cwd() / "claudefig.toml"

        try:
            # Step 1: If no config exists, apply default preset first
            if not config_path.exists():
                self.app.notify("Applying default preset...", severity="information")
                self.config_template_manager.apply_preset_to_project("default")
                # Reload config after applying preset
                self.config_data = config_service.load_config(self.config_repo)

            # Step 2: Run initializer to generate files
            self.app.notify("Generating files...", severity="information")
            initializer = Initializer(self.config_repo.get_path())

            # Generate files (skip_prompts=True for TUI non-interactive mode)
            success = initializer.initialize(Path.cwd(), force=False, skip_prompts=True)

            # Step 3: Reload config everywhere
            if isinstance(self.app, MainScreen):
                # Reload config in app
                self.app.config_data = config_service.load_config(self.app.config_repo)
                # Reload config in content panel so all panels get fresh config
                content_panel = self.app.query_one("#content-panel", ContentPanel)
                content_panel.config_data = self.app.config_data
                # Update local config reference
                self.config_data = self.app.config_data

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
            self.app.notify(
                "claudefig.toml already exists! Go to Presets panel to overwrite.",
                severity="error",
            )
        except Exception as e:
            self.app.notify(f"Initialization failed: {e}", severity="error")
