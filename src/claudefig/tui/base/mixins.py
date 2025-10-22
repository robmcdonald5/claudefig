"""Mixins for common TUI screen functionality."""

from typing import TYPE_CHECKING, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.events import DescendantFocus
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


class ScrollNavigationMixin:
    """Mixin providing smooth scroll navigation for screens with VerticalScroll containers.

    Provides:
    - Smart up/down arrow navigation that doesn't wrap at boundaries
    - Automatic scrolling to reveal title when at top
    - Automatic scrolling to reveal content when at bottom
    - Horizontal group navigation support (skips siblings in horizontal containers)
    - Auto-scroll focused widgets into view

    Requires:
    - Screen must use a VerticalScroll container with an id attribute
    - Screen must have up/down arrow bindings that call action_focus_previous/action_focus_next

    Usage:
        class MyScreen(Screen, ScrollNavigationMixin):
            BINDINGS = [
                ("up", "focus_previous", "Focus Previous"),
                ("down", "focus_next", "Focus Next"),
            ]

            def compose(self) -> ComposeResult:
                with VerticalScroll(id="my-screen", can_focus=False):
                    yield Label("TITLE", classes="screen-title")
                    # ... content
    """

    # These attributes/methods are expected to be provided by the Screen class
    # that this mixin is used with. We declare them here for type checking only.
    if TYPE_CHECKING:
        from typing import Any

        focused: Any  # Provided by Screen
        focus_chain: Any  # Provided by Screen

        def query(self, selector: str) -> Any: ...  # Provided by DOMNode
        def query_one(self, selector: Any, expect_type: Any = None) -> Any: ...  # Provided by DOMNode

    def _get_horizontal_nav_parent(self, widget):
        """Get the horizontal navigation parent for a widget, if any.

        Args:
            widget: The widget to check

        Returns:
            The Horizontal parent container if widget is in a navigation group,
            None otherwise
        """
        current = widget.parent

        # Walk up the tree to find a Horizontal container
        while current:
            if isinstance(current, Horizontal):
                # Check if it's a navigation group we care about
                if hasattr(current, "classes") and (
                    "tab-actions" in current.classes
                    or "instance-actions" in current.classes
                ):
                    return current
            current = current.parent

        return None

    def action_focus_previous(self) -> None:
        """Override up arrow navigation to prevent wrapping.

        Handles focus movement when pressing up arrow:
        - If at the first focusable element, stay there (no wrap)
        - Skips siblings within horizontal groups
        - Otherwise, move focus to previous element normally
        """
        # Use this screen's actual focus_chain instead of building our own list
        # This ensures we're using the same order Textual uses for navigation
        focus_chain = self.focus_chain

        if not focus_chain:
            return

        focused = self.focused
        if focused is None:
            # No focus, focus the first element in chain
            focus_chain[0].focus()
            return

        if focused not in focus_chain:
            # Focused widget not in chain, shouldn't happen but handle gracefully
            return

        current_index = focus_chain.index(focused)

        # At the absolute first element - don't wrap
        if current_index == 0:
            # Scroll to the top to reveal title labels
            try:
                # Get the title label and scroll it into view (at the top)
                title_label = self.query("Label.screen-title").first()
                if title_label:
                    title_label.scroll_visible(top=True, animate=False)
            except Exception:
                pass
            return

        # Find the target index, skipping siblings in horizontal groups
        target_index = current_index - 1

        # Check if current widget is in a horizontal group
        horizontal_parent = self._get_horizontal_nav_parent(focused)

        if horizontal_parent:
            # Skip all siblings in this horizontal group
            while target_index >= 0:
                candidate = focus_chain[target_index]
                candidate_parent = self._get_horizontal_nav_parent(candidate)

                # Stop if we found a widget not in the same horizontal group
                if candidate_parent != horizontal_parent:
                    break

                target_index -= 1

        # Ensure we don't go below 0
        if target_index < 0:
            # Already at top, scroll to reveal title
            try:
                title_label = self.query("Label.screen-title").first()
                if title_label:
                    title_label.scroll_visible(top=True, animate=False)
            except Exception:
                pass
            return

        # If the target widget is in a horizontal group, find the FIRST widget in that group
        target_widget = focus_chain[target_index]
        target_horizontal_parent = self._get_horizontal_nav_parent(target_widget)

        if target_horizontal_parent:
            # Walk backwards to find the first widget in this horizontal group
            first_in_group_index = target_index
            while first_in_group_index > 0:
                prev_widget = focus_chain[first_in_group_index - 1]
                prev_horizontal_parent = self._get_horizontal_nav_parent(prev_widget)

                # Stop if previous widget is not in the same horizontal group
                if prev_horizontal_parent != target_horizontal_parent:
                    break

                first_in_group_index -= 1

            target_index = first_in_group_index

        # Focus the target element
        focus_chain[target_index].focus()

    def action_focus_next(self) -> None:
        """Override down arrow navigation to prevent wrapping.

        Handles focus movement when pressing down arrow:
        - If at the last focusable element, stay there (no wrap)
        - Skips siblings within horizontal groups
        - Otherwise, move focus to next element normally
        """
        # Use this screen's actual focus_chain instead of building our own list
        # This ensures we're using the same order Textual uses for navigation
        focus_chain = self.focus_chain

        if not focus_chain:
            return

        focused = self.focused
        if focused is None:
            # No focus, focus the first element in chain
            focus_chain[0].focus()
            return

        if focused not in focus_chain:
            # Focused widget not in chain, shouldn't happen but handle gracefully
            return

        current_index = focus_chain.index(focused)
        max_index = len(focus_chain) - 1

        # At the bottom of the tree (last element, typically the Back button)
        # Don't wrap, but scroll viewport if there's content below
        if current_index == max_index:
            # Scroll to ensure the last element (and any content below) is visible
            try:
                # Scroll the current focused widget to bottom to reveal content below
                focused.scroll_visible(top=False, animate=False)
            except Exception:
                pass
            return

        # Find the target index, skipping siblings in horizontal groups
        target_index = current_index + 1

        # Check if current widget is in a horizontal group
        horizontal_parent = self._get_horizontal_nav_parent(focused)

        if horizontal_parent:
            # Skip all siblings in this horizontal group
            while target_index <= max_index:
                candidate = focus_chain[target_index]
                candidate_parent = self._get_horizontal_nav_parent(candidate)

                # Stop if we found a widget not in the same horizontal group
                if candidate_parent != horizontal_parent:
                    break

                target_index += 1

        # Ensure we don't exceed max
        if target_index > max_index:
            # Already at bottom, scroll to reveal content below
            try:
                focused.scroll_visible(top=False, animate=False)
            except Exception:
                pass
            return

        # If the target widget is in a horizontal group, we're already on the first one
        # (because focus_chain is in DOM order, left-to-right, top-to-bottom)
        # So no adjustment needed for down navigation

        # Focus the target element
        focus_chain[target_index].focus()

    def on_descendant_focus(self, event: DescendantFocus) -> None:
        """Ensure focused widgets are scrolled into view.

        Args:
            event: The focus event containing the focused widget
        """
        # Scroll the VerticalScroll container to keep focused widget visible
        # This ensures proper scrolling within the container
        try:
            # Find the first VerticalScroll container in this screen
            scroll_container = self.query_one(VerticalScroll)
            scroll_container.scroll_to_widget(event.widget, animate=False)
        except Exception:
            pass
