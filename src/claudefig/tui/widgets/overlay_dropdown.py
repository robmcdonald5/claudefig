"""Overlay dropdown widget that doesn't affect document flow."""

import contextlib

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.widgets import Static


class DropdownContent(Container):
    """Content container that overlays above other elements."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent content from being focusable - focus should stay on header
        self.can_focus = False


class DropdownHeader(Static):
    """Clickable header for the dropdown."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_focus = True


class OverlayDropdown(Widget):
    """A dropdown widget that overlays content without affecting page layout.

    Uses Textual's overlay: screen pattern (same as official Select widget).

    Attributes:
        title: The dropdown title text
        expanded: Whether the dropdown is currently expanded
    """

    BINDINGS = [
        ("enter", "toggle_dropdown", "Toggle"),
    ]

    DEFAULT_CSS = """
    OverlayDropdown {
        width: 100%;
        height: 3;  /* Only header height - content overlays */
        margin-bottom: 1;
    }

    DropdownHeader {
        width: 100%;
        height: 3;
        padding: 0 1;
        background: $panel;
        border: round $primary-lighten-1;
        text-style: bold;
        color: $accent;
    }

    DropdownHeader:hover {
        background: $primary;
    }

    DropdownHeader:focus {
        background: $primary;
        border: round $accent;
    }

    /* THE MAGIC: overlay: screen removes widget from document flow */
    OverlayDropdown > DropdownContent {
        overlay: screen;          /* Renders on separate layer above all content */
        constrain: none inside;   /* Auto-repositions to stay within screen bounds */
        display: none;            /* Hidden by default */
        width: 100%;
        height: auto;
        max-height: 20;           /* Scrollable after 20 lines */
        background: $surface;
        border: round $primary-lighten-1;
        padding: 1;
    }

    /* Show overlay when expanded */
    OverlayDropdown.-expanded > DropdownContent {
        display: block;
    }

    DropdownContent > VerticalScroll {
        width: 100%;
        height: auto;
        max-height: 18;
        padding: 1;
        overflow-y: auto;
        scrollbar-size: 1 1;
        scrollbar-background: $panel;
        scrollbar-color: $primary;
    }

    DropdownContent Static {
        margin: 0 0 0 1;
    }
    """

    title: reactive[str] = reactive("")
    expanded: var[bool] = var(False, init=False)  # Use var for proper reactivity

    def __init__(
        self,
        title: str = "",
        *,
        expanded: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the overlay dropdown.

        Args:
            title: The dropdown title
            expanded: Initial expanded state
            name: The name of the widget
            id: The ID of the widget in the DOM
            classes: The CSS classes for the widget
        """
        super().__init__(name=name, id=id, classes=classes)
        self.title = title
        # Don't set expanded here - let watch_expanded handle it after mount

    def compose(self) -> ComposeResult:
        """Compose the dropdown widget."""
        # Header (always visible, fixed height)
        yield DropdownHeader(self._format_title())

        # Content (overlay, initially hidden via CSS)
        content = DropdownContent()
        content.can_focus = False  # Prevent focus on content
        with content:
            scroll = VerticalScroll()
            scroll.can_focus = False  # Prevent focus on scroll
            with scroll:
                # Content will be added by caller via set_content()
                pass
        yield content

    def _format_title(self) -> str:
        """Format the title with expansion indicator.

        Returns:
            Formatted title string
        """
        indicator = "▾" if self.expanded else "▸"
        return f"{indicator} {self.title}"

    def watch_expanded(self, expanded: bool) -> None:
        """React to expanded state changes.

        This follows the official Select widget pattern:
        - Use set_class() to toggle CSS visibility
        - Update header text

        Args:
            expanded: New expanded state
        """
        # Toggle CSS class to show/hide overlay
        self.set_class(expanded, "-expanded")

        # Update header text
        with contextlib.suppress(Exception):
            header = self.query_one(DropdownHeader)
            header.update(self._format_title())

    def on_click(self, event) -> None:
        """Handle click events to toggle dropdown.

        Args:
            event: The click event
        """
        self.toggle()
        event.stop()

    def action_toggle_dropdown(self) -> None:
        """Action to toggle dropdown (called by Enter key binding)."""
        self.toggle()

    def toggle(self) -> None:
        """Toggle the dropdown expanded state."""
        self.expanded = not self.expanded

    def collapse(self) -> None:
        """Collapse the dropdown."""
        self.expanded = False

    def expand_dropdown(self) -> None:
        """Expand the dropdown."""
        self.expanded = True

    def set_content(self, *widgets: Widget) -> None:
        """Set the content of the dropdown.

        Args:
            widgets: Widgets to display in the dropdown content
        """
        content = self.query_one(DropdownContent)
        scroll = content.query_one(VerticalScroll)

        # Clear existing content
        scroll.remove_children()

        # Add new content and ensure they can't receive focus
        for widget in widgets:
            widget.can_focus = False
        scroll.mount(*widgets)
