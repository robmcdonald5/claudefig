"""File instance item widget for displaying file instance information."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Static

from claudefig.models import FileInstance, FileType


class FileInstanceItem(Container):
    """Display file instance with edit actions using reactive attributes."""

    # Reactive attributes - automatically trigger watch methods when changed
    # init=False prevents watch methods from being called during __init__
    is_enabled = reactive(True, init=False)
    file_path = reactive("", init=False)
    component_name = reactive("", init=False)

    def __init__(self, instance: FileInstance, **kwargs) -> None:
        """Initialize file instance item.

        Args:
            instance: FileInstance object
        """
        super().__init__(**kwargs)
        # Store non-reactive data
        self.instance_id = instance.id
        self.instance_type = instance.type

        # Store initial values to set after mounting
        self._initial_enabled = instance.enabled
        self._initial_path = instance.path
        self._initial_component_name = instance.get_component_name()

    def compose(self) -> ComposeResult:
        """Compose the file instance item."""
        # Use Static widgets with IDs so we can update them in watch methods
        yield Static(id="path-label", classes="instance-path")
        yield Static(id="component-label", classes="instance-component")
        yield Static(id="status-label", classes="instance-status")

        with Horizontal(classes="instance-actions"):
            yield Button(
                "Edit", id=f"edit-{self.instance_id}", classes="instance-button"
            )
            yield Button(
                "Remove", id=f"remove-{self.instance_id}", classes="instance-button"
            )
            yield Button(
                "Toggle", id=f"toggle-{self.instance_id}", classes="instance-button"
            )
            # Add Path button for CLAUDE.md and .gitignore
            if self.instance_type in (FileType.CLAUDE_MD, FileType.GITIGNORE):
                yield Button(
                    "Path", id=f"path-{self.instance_id}", classes="instance-button"
                )

    def on_mount(self) -> None:
        """Called when widget is mounted - set initial reactive values.

        Now that compose() has been called and widgets exist, we can safely
        set reactive attributes which will trigger watch methods.
        """
        # Use set_reactive to set ALL values without triggering watchers first
        # This ensures all reactive attributes have correct values before any watcher runs
        self.set_reactive(FileInstanceItem.component_name, self._initial_component_name)
        self.set_reactive(FileInstanceItem.file_path, self._initial_path)
        self.set_reactive(FileInstanceItem.is_enabled, self._initial_enabled)

        # Now manually trigger watchers in the correct order
        # All reactive attributes are set, so watchers can access correct values
        self.watch_component_name(self._initial_component_name)
        self.watch_file_path(self._initial_path)
        self.watch_is_enabled(self._initial_enabled)

        # Force a final update to ensure path label has correct text and CSS
        # This guarantees the UI is in sync with reactive state
        self._update_path_label()

    def watch_is_enabled(self, new_value: bool) -> None:
        """Called automatically when is_enabled changes.

        Args:
            new_value: New enabled state
        """
        # Update status label
        status_label = self.query_one("#status-label", Static)
        status_text = "+ Enabled" if new_value else "- Disabled"
        status_label.update(status_text)

        # Update CSS classes
        if new_value:
            status_label.remove_class("instance-disabled")
            status_label.add_class("instance-enabled")
        else:
            status_label.remove_class("instance-enabled")
            status_label.add_class("instance-disabled")

        # Update path label to show/hide disabled indicator
        self._update_path_label()

    def watch_file_path(self, new_value: str) -> None:
        """Called automatically when file_path changes.

        Args:
            new_value: New file path
        """
        self._update_path_label()

    def watch_component_name(self, new_value: str) -> None:
        """Called automatically when component_name changes.

        Args:
            new_value: New component name
        """
        component_label = self.query_one("#component-label", Static)
        component_label.update(f"Component: {new_value}")

    def _update_path_label(self) -> None:
        """Update the path label with current path and disabled indicator."""
        path_label = self.query_one("#path-label", Static)
        path_suffix = " [disabled]" if not self.is_enabled else ""
        path_label.update(f"Path: {self.file_path}{path_suffix}")

        # Update CSS classes
        if self.is_enabled:
            path_label.remove_class("instance-disabled")
        else:
            path_label.add_class("instance-disabled")
