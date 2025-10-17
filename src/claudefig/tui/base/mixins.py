"""Mixins for common TUI screen functionality."""

from typing import TYPE_CHECKING, Optional

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button

if TYPE_CHECKING:
    from textual.app import App

    from claudefig.config import Config
    from claudefig.file_instance_manager import FileInstanceManager


class BackButtonMixin:
    """Mixin to add standard back button to config screens.

    Provides:
    - compose_back_button(): Yields a standard back button with footer container
    - handle_back_button(): Handles back button press, returns True if handled

    Usage:
        class MyScreen(Screen, BackButtonMixin):
            def compose(self) -> ComposeResult:
                # ... main content
                yield from self.compose_back_button()

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if self.handle_back_button(event):
                    return
                # ... other button handling
    """

    if TYPE_CHECKING:
        app: "App[object]"

    BACK_BUTTON_LABEL = "← Back to Config Menu"

    def compose_back_button(self, label: Optional[str] = None) -> ComposeResult:
        """Compose a standard back button in a footer container.

        Args:
            label: Optional custom label (defaults to BACK_BUTTON_LABEL)

        Yields:
            Container with back button
        """
        button_label = label or self.BACK_BUTTON_LABEL
        with Container(classes="screen-footer"):
            yield Button(button_label, id="btn-back")

    def handle_back_button(self, event: Button.Pressed) -> bool:
        """Handle back button press.

        Args:
            event: Button press event

        Returns:
            True if this was a back button press (handled), False otherwise
        """
        if event.button.id == "btn-back":
            self.app.pop_screen()
            return True
        return False


class FileInstanceMixin:
    """Mixin for screens that manage file instances.

    Provides:
    - sync_instances_to_config(): Sync instance manager state to config and save

    Requires the screen to have:
    - self.config: Config instance
    - self.instance_manager: FileInstanceManager instance

    Usage:
        class MyScreen(Screen, FileInstanceMixin):
            def __init__(self, config, instance_manager, **kwargs):
                super().__init__(**kwargs)
                self.config = config
                self.instance_manager = instance_manager

            def some_handler(self):
                # Modify instance manager
                self.instance_manager.add_instance(instance)
                # Sync to config and save
                self.sync_instances_to_config()
    """

    if TYPE_CHECKING:
        config: "Config"
        instance_manager: "FileInstanceManager"

    def sync_instances_to_config(self) -> None:
        """Sync instance manager state to config and save to disk.

        This method implements the critical 3-step state synchronization pattern
        documented in ARCHITECTURE.md:

        1. Modify instance_manager (already done by caller)
        2. Sync manager → config (done here)
        3. Sync config → disk (done here)

        Call this method after ANY modification to instance_manager:
        - add_instance()
        - update_instance()
        - remove_instance()
        - enable_instance()
        - disable_instance()

        Example:
            # Add an instance
            self.instance_manager.add_instance(new_instance)
            self.sync_instances_to_config()  # ← Call this!

            # Update an instance
            instance.enabled = False
            self.instance_manager.update_instance(instance)
            self.sync_instances_to_config()  # ← Call this!

        Raises:
            AttributeError: If screen doesn't have config or instance_manager
        """
        # Step 2: Sync manager → config
        self.config.set_file_instances(self.instance_manager.save_instances())

        # Step 3: Sync config → disk
        self.config.save()
