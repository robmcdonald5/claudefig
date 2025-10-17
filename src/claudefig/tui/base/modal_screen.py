"""Base class for modal dialog screens."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Label


class BaseModalScreen(Screen):
    """Base class for modal dialog screens with standard layout and navigation.

    Provides:
    - Standard BINDINGS for escape/backspace/left/right navigation
    - Standard modal layout (container > header > content > actions)
    - Standard navigation actions (focus_previous/focus_next)

    To use this base class, inherit and override:
    - compose_title() -> str: Return the modal title
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
                yield Button("OK", id="btn-ok", variant="primary")
                yield Button("Cancel", id="btn-cancel")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "btn-cancel":
                    self.dismiss()
                elif event.button.id == "btn-ok":
                    self.dismiss(result={"action": "ok"})
    """

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("backspace", "dismiss", "Cancel"),
        ("left", "focus_previous", "Focus previous"),
        ("right", "focus_next", "Focus next"),
    ]

    def compose(self) -> ComposeResult:
        """Compose standard modal layout.

        Subclasses should NOT override this method. Instead, override:
        - compose_title()
        - compose_content()
        - compose_actions()
        """
        with Container(id="dialog-container"):
            # Header
            yield Label(self.compose_title(), classes="dialog-header")

            # Content area (scrollable)
            with VerticalScroll(id="dialog-content"):
                yield from self.compose_content()

            # Action buttons
            with Horizontal(classes="dialog-actions"):
                yield from self.compose_actions()

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

    def action_focus_previous(self) -> None:
        """Navigate focus to the previous focusable widget (left arrow)."""
        self.screen.focus_previous()

    def action_focus_next(self) -> None:
        """Navigate focus to the next focusable widget (right arrow)."""
        self.screen.focus_next()
