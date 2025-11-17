"""Base classes for navigable panels and screens with consistent navigation bindings.

This module provides base classes that establish standard navigation patterns
across the TUI. Panels and screens can inherit from these bases and selectively
override behavior while maintaining consistent tooltip descriptions and key bindings.

Architecture:
    - BaseNavigablePanel: Standard 4-directional navigation for panels
    - BaseHorizontalNavigablePanel: Horizontal-only navigation (up/down disabled)
    - BaseScreen: Standard navigation for full screens with ScrollNavigationMixin

Usage:
    # Standard panel navigation
    class MyPanel(BaseNavigablePanel):
        # Inherits all navigation - just works!
        pass

    # Custom panel navigation
    class GridPanel(BaseNavigablePanel):
        # Override specific actions for custom behavior
        def action_navigate_up(self) -> None:
            self._custom_grid_navigation(-1, 0)

    # Horizontal-only panel navigation
    class ButtonRowPanel(BaseHorizontalNavigablePanel):
        # Up/down automatically disabled and hidden
        pass

    # Standard screen navigation
    class MyScreen(BaseScreen):
        # Inherits navigation with ScrollNavigationMixin support
        pass
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer

from claudefig.tui.base.mixins import BackButtonMixin, ScrollNavigationMixin


class BaseNavigablePanel(Container):
    """Base class for panels with standard 4-directional navigation.

    Provides consistent navigation bindings and tooltip descriptions across
    all panels. Child classes can selectively override action methods to
    customize navigation behavior while keeping consistent descriptions.

    Default Behavior:
        - Up/Down: Navigate vertically through focus chain
        - Left/Right: Navigate horizontally through focus chain
        - All directions shown in footer tooltips

    Customization:
        Override any action_navigate_* method to customize behavior:

        class CustomPanel(BaseNavigablePanel):
            def action_navigate_up(self) -> None:
                # Custom logic here
                pass

    The BINDINGS attribute uses Textual's Binding objects with show=True
    to ensure tooltips are displayed. Child classes can override BINDINGS
    to change visibility or behavior.
    """

    BINDINGS = [
        Binding("up", "navigate_up", "Navigate Up", show=True),
        Binding("down", "navigate_down", "Navigate Down", show=True),
        Binding("left", "navigate_left", "Navigate Left", show=True),
        Binding("right", "navigate_right", "Navigate Right", show=True),
    ]

    def action_navigate_up(self) -> None:
        """Navigate up through the focus chain.

        Default implementation moves to previous focusable widget.
        Override this method in subclasses for custom vertical navigation.
        """
        self.screen.focus_previous()

    def action_navigate_down(self) -> None:
        """Navigate down through the focus chain.

        Default implementation moves to next focusable widget.
        Override this method in subclasses for custom vertical navigation.
        """
        self.screen.focus_next()

    # Note: action_navigate_left/right are NOT implemented here by design.
    # Horizontal navigation often needs to bubble up to parent screens
    # (e.g., MainScreen) for complex navigation logic like escaping back
    # to the main menu. Panels that need custom horizontal navigation
    # (like ConfigPanel's 2D grid) should implement these methods explicitly.


class BaseHorizontalNavigablePanel(BaseNavigablePanel):
    """Base class for panels with horizontal-only navigation.

    Use this for panels that only support left/right navigation, such as
    horizontal button rows where up/down navigation should be disabled.

    Behavior:
        - Up/Down: Disabled (no-op) and hidden from footer tooltips
        - Left/Right: Navigate horizontally through focus chain
        - Consistent with BaseNavigablePanel descriptions

    Example:
        class InitializePanel(BaseHorizontalNavigablePanel):
            # Up/down automatically disabled
            # Only left/right navigation active
            pass
    """

    BINDINGS = [
        Binding("up", "navigate_up", "", show=False),  # Disabled & hidden
        Binding("down", "navigate_down", "", show=False),  # Disabled & hidden
        Binding("left", "navigate_left", "Navigate Left", show=True),
        Binding("right", "navigate_right", "Navigate Right", show=True),
    ]

    def action_navigate_up(self) -> None:
        """No-op for vertical navigation (disabled in horizontal-only panels)."""
        pass

    def action_navigate_down(self) -> None:
        """No-op for vertical navigation (disabled in horizontal-only panels)."""
        pass


class BaseScreen(Screen, BackButtonMixin, ScrollNavigationMixin):
    """Base class for full screens with standard navigation and scroll support.

    Provides consistent navigation bindings for all detail screens with
    ScrollNavigationMixin support for smart vertical/horizontal navigation.
    All screens automatically get back button functionality via BackButtonMixin.

    Features:
        - Escape/Backspace: Pop screen (go back)
        - Up/Down: Navigate vertically with smart scrolling (no wrap)
        - Left/Right: Navigate horizontally within button groups
        - ScrollNavigationMixin: Auto-scroll focused widgets into view
        - BackButtonMixin: Standard back button behavior

    Default Behavior:
        - escape/backspace call action_pop_screen() which dismisses the screen
        - Navigation uses ScrollNavigationMixin's focus_previous/next/left/right
        - Consistent "Navigate Up/Down/Left/Right" tooltip descriptions

    Customization:
        Override action_pop_screen() for custom back behavior:

        class CustomScreen(BaseScreen):
            def action_pop_screen(self) -> None:
                # Save state before popping
                self.save_changes()
                self.dismiss()

    Note:
        Screens that need special escape handling (like OverviewScreen with
        collapsible sections) can override BINDINGS to use a custom action.
    """

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", show=True),
        Binding("backspace", "pop_screen", "Back", show=False),
        Binding("up", "focus_previous", "Navigate Up", show=True),
        Binding("down", "focus_next", "Navigate Down", show=True),
        Binding("left", "focus_left", "Navigate Left", show=True),
        Binding("right", "focus_right", "Navigate Right", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Compose screen with footer for dynamic keybinding display.

        Child classes should override compose_screen_content() instead of compose()
        to ensure the footer is always included and displays screen-specific bindings.
        """
        yield from self.compose_screen_content()
        yield Footer()

    def compose_screen_content(self) -> ComposeResult:
        """Compose all screen widgets.

        Override this method in child classes instead of compose() to ensure
        the footer displays properly. This allows the base class to handle
        footer composition while child classes define the complete screen layout.

        Yields:
            All widgets and containers that make up the screen.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement compose_screen_content()"
        )

    def action_pop_screen(self) -> None:
        """Pop this screen from the stack (go back).

        Default implementation dismisses the screen. Override this method
        to add custom behavior before popping (e.g., save validation).
        """
        self.dismiss()
