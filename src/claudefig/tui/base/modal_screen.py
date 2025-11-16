"""Base class for modal dialog screens."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Label

from claudefig.tui.base.mixins import ScrollNavigationMixin


class BaseModalScreen(Screen, ScrollNavigationMixin):
    """Base class for modal dialog screens with standard layout and navigation.

    Provides:
    - Smart scroll navigation via ScrollNavigationMixin:
      * Up/down arrows navigate vertically without wrapping
      * Button group treated as single unit for vertical navigation
      * Left/right arrows navigate horizontally between buttons (native Textual)
      * Dynamic scrollbar appears when content exceeds screen height
      * Auto-scroll to keep focused widget visible
    - Escape/backspace to dismiss

    To use this base class, inherit and override:
    - compose_title() -> str: Return the modal title (empty string for no title)
    - compose_content() -> ComposeResult: Yield content widgets
    - compose_actions() -> ComposeResult: Yield action button widgets
    - on_button_pressed(): Handle button press events

    Example:
        class MyModalScreen(BaseModalScreen):
            def compose_title(self) -> str:
                return "My Modal Title"

            def compose_content(self) -> ComposeResult:
                yield Label("My content")

            def compose_actions(self) -> ComposeResult:
                yield Button("OK", id="btn-ok")
                yield Button("Cancel", id="btn-cancel")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "btn-cancel":
                    self.dismiss()
                elif event.button.id == "btn-ok":
                    self.dismiss(result={"action": "ok"})
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", show=True),
        Binding("backspace", "dismiss", "Cancel", show=False),
        Binding("up", "focus_previous", "Navigate Up", show=True),
        Binding("down", "focus_next", "Navigate Down", show=True),
        Binding("left", "focus_horizontal_previous", "Navigate Left", show=True),
        Binding("right", "focus_horizontal_next", "Navigate Right", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Compose standard modal layout with footer for dynamic keybinding display.

        Subclasses should NOT override this method. Instead, override:
        - compose_title()
        - compose_content()
        - compose_actions()
        """
        # Everything inside VerticalScroll for proper scroll navigation with mixin
        with VerticalScroll(id="dialog-content", can_focus=False):
            # Header (only if title is provided)
            title = self.compose_title()
            if title:
                yield Label(title, classes="dialog-header")

            # Content area
            yield from self.compose_content()

            # Action buttons
            with Horizontal(classes="dialog-actions"):
                yield from self.compose_actions()

        # Footer displays modal-specific keybindings (Cancel, Navigate, etc.)
        yield Footer()

    def compose_title(self) -> str:
        """Return the modal title text.

        Override this method in subclasses.

        Returns:
            Modal title string
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement compose_title()"
        )

    def compose_content(self) -> ComposeResult:
        """Yield content widgets for the modal body.

        Override this method in subclasses.

        Yields:
            Content widgets
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement compose_content()"
        )

    def compose_actions(self) -> ComposeResult:
        """Yield action button widgets for the modal footer.

        Override this method in subclasses.

        Yields:
            Button widgets
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement compose_actions()"
        )

    async def action_dismiss(self, result: object = None) -> None:
        """Dismiss the modal without saving (escape/backspace keys)."""
        self.dismiss(result)

    def action_focus_horizontal_previous(self) -> None:
        """Navigate to previous focusable widget horizontally (left arrow).

        Only navigates if within a horizontal button group, preventing wrap-around.
        """
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal group
        horizontal_parent = self._get_horizontal_nav_parent(focused)
        if not horizontal_parent:
            return

        focus_chain = self.focus_chain
        current_index = focus_chain.index(focused) if focused in focus_chain else -1

        if current_index <= 0:
            return  # Already at first element, don't wrap

        # Get previous element
        prev_widget = focus_chain[current_index - 1]
        prev_parent = self._get_horizontal_nav_parent(prev_widget)

        # Only move if previous is in same horizontal group
        if prev_parent == horizontal_parent:
            prev_widget.focus()
            self._update_horizontal_focus_memory(prev_widget)

    def action_focus_horizontal_next(self) -> None:
        """Navigate to next focusable widget horizontally (right arrow).

        Only navigates if within a horizontal button group, preventing wrap-around.
        """
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal group
        horizontal_parent = self._get_horizontal_nav_parent(focused)
        if not horizontal_parent:
            return

        focus_chain = self.focus_chain
        current_index = focus_chain.index(focused) if focused in focus_chain else -1

        if current_index < 0 or current_index >= len(focus_chain) - 1:
            return  # Already at last element, don't wrap

        # Get next element
        next_widget = focus_chain[current_index + 1]
        next_parent = self._get_horizontal_nav_parent(next_widget)

        # Only move if next is in same horizontal group
        if next_parent == horizontal_parent:
            next_widget.focus()
            self._update_horizontal_focus_memory(next_widget)

    # Note: _get_horizontal_nav_parent is inherited from ScrollNavigationMixin
