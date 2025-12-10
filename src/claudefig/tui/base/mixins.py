"""Mixins for common TUI screen functionality.

Note: Platform and subprocess imports removed - now using claudefig.utils.platform

UI UPDATE PATTERNS - WHEN TO USE WHAT:
======================================

The TUI uses two main patterns for updating the UI:

1. REACTIVE ATTRIBUTES (Recommended for property changes):
   - Use for: Simple property updates (text, enabled state, visibility)
   - Benefits: Smooth updates, no widget rebuilding, efficient
   - Performance: Fast - only affected elements update
   - Example: FileInstanceItem updating path or enabled state

   Pattern:
   ```python
   from textual.reactive import reactive

   class MyWidget(Widget):
       my_value = reactive("default", init=False)

       def watch_my_value(self, new_value: str) -> None:
           '''Called automatically when my_value changes.'''
           label = self.query_one("#my-label", Static)
           label.update(new_value)

   # Later, update the reactive attribute:
   widget.my_value = "new value"  # Triggers watch_my_value()
   ```

2. REFRESH WITH RECOMPOSE (Use sparingly for structural changes):
   - Use for: Adding/removing widgets, major layout changes
   - Drawbacks: Expensive, rebuilds entire widget tree, loses focus
   - Performance: Slow - full screen recomposition
   - Example: FileInstancesScreen adding/removing instances

   Pattern:
   ```python
   def some_handler(self):
       # Modify data that affects compose()
       self.instances.append(new_instance)

       # Force full widget rebuild
       self.refresh(recompose=True)
   ```

DECISION TREE:
- Adding/removing widgets? → Use refresh(recompose=True)
- Changing widget properties? → Use reactive attributes
- Updating text content? → Use reactive attributes
- Changing enabled/disabled state? → Use reactive attributes
- Modifying CSS classes? → Direct manipulation (add_class/remove_class)

See FileInstanceItem.py for excellent reactive attribute examples.
See FileInstancesScreen._remove_instance() for recompose examples.
"""

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.events import DescendantFocus
from textual.widgets import Button

if TYPE_CHECKING:
    from typing import Any

    from textual.app import App

    from claudefig.repositories import AbstractConfigRepository


class BackButtonMixin:
    """Mixin to add standard back button to config screens.

    Provides:
    - compose_back_button(): Yields a standard back button with footer container
    - handle_back_button(): Handles back button press, returns True if handled

    Usage:
        class MyScreen(Screen, BackButtonMixin):
            def compose(self) -> ComposeResult:
                # ... main content
                yield from self.compose_back_button()  # type: ignore[misc]

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if self.handle_back_button(event):
                    return
                # ... other button handling
    """

    if TYPE_CHECKING:
        app: "App[object]"

    BACK_BUTTON_LABEL = "← Back to Config Menu"

    def compose_back_button(self, label: str | None = None) -> ComposeResult:
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
    - sync_instances_to_config(): Sync instances dict to config and save

    Requires the screen to have:
    - self.config_data: dict[str, Any] - Configuration data dictionary
    - self.config_repo: AbstractConfigRepository - Repository for saving
    - self.instances_dict: dict[str, FileInstance] - File instances by ID

    Usage:
        class MyScreen(Screen, FileInstanceMixin):
            def __init__(self, config_data, config_repo, instances_dict, **kwargs):
                super().__init__(**kwargs)
                self.config_data = config_data
                self.config_repo = config_repo
                self.instances_dict = instances_dict

            def some_handler(self):
                # Modify instances_dict
                self.instances_dict[instance_id] = instance
                # Sync to config and save
                self.sync_instances_to_config()
    """

    if TYPE_CHECKING:
        from claudefig.models import FileInstance

        config_data: dict[str, Any]
        config_repo: "AbstractConfigRepository"
        instances_dict: dict[str, "FileInstance"]

    def sync_instances_to_config(self) -> None:
        """Sync instances dict to config data and save to disk.

        This method implements the critical 3-step state synchronization pattern
        for the new architecture:

        1. Modify instances_dict (already done by caller)
        2. Sync instances_dict → config_data (done here)
        3. Sync config_data → disk via repository (done here)

        Call this method after ANY modification to instances_dict:
        - Adding an instance: instances_dict[id] = instance
        - Updating an instance: instances_dict[id] = updated_instance
        - Removing an instance: del instances_dict[id]
        - Enabling/disabling: instances_dict[id].enabled = True/False

        Example:
            # Add an instance
            self.instances_dict[new_instance.id] = new_instance
            self.sync_instances_to_config()  # ← Call this!

            # Update an instance
            instance = self.instances_dict[instance_id]
            instance.enabled = False
            self.instances_dict[instance_id] = instance
            self.sync_instances_to_config()  # ← Call this!

            # Remove an instance
            del self.instances_dict[instance_id]
            self.sync_instances_to_config()  # ← Call this!

        Raises:
            AttributeError: If screen doesn't have required attributes
        """
        from claudefig.services import file_instance_service

        # Step 2: Sync instances_dict → config_data
        instances_list = file_instance_service.save_instances_to_config(
            self.instances_dict
        )
        self.config_data["files"] = instances_list

        # Step 3: Sync config_data → disk via repository
        self.config_repo.save(self.config_data)


class ScrollNavigationMixin:
    """Mixin providing smooth scroll navigation for screens with VerticalScroll containers.

    Provides:
    - Smart up/down arrow navigation that doesn't wrap at boundaries
    - Smart left/right arrow navigation within horizontal groups
    - Automatic scrolling to reveal title when at top
    - Automatic scrolling to reveal content when at bottom
    - Horizontal group navigation support (skips siblings in horizontal containers)
    - Focus memory for horizontal groups (remembers last focused button)
    - Auto-scroll focused widgets into view

    Requires:
    - Screen must use a VerticalScroll container with an id attribute
    - Screen must have up/down arrow bindings that call action_focus_previous/action_focus_next
    - Optional: left/right arrow bindings that call action_focus_left/action_focus_right

    Usage:
        class MyScreen(Screen, ScrollNavigationMixin):
            BINDINGS = [
                ("up", "focus_previous", "Focus Previous"),
                ("down", "focus_next", "Focus Next"),
                ("left", "focus_left", "Focus Left"),
                ("right", "focus_right", "Focus Right"),
            ]

            def compose(self) -> ComposeResult:
                with VerticalScroll(id="my-screen", can_focus=False):
                    yield Label("TITLE", classes="screen-title")
                    # ... content
    """

    # These attributes/methods are expected to be provided by the Screen class
    # that this mixin is used with.
    if TYPE_CHECKING:
        from typing import Any

        focused: Any  # Provided by Screen
        focus_chain: Any  # Provided by Screen

    def _ensure_focus_memory_initialized(self):
        """Ensure the focus memory dict exists (lazy initialization).

        This is needed because the mixin's __init__ may not be called
        depending on the inheritance chain of the using class.
        """
        if not hasattr(self, "_horizontal_group_focus_memory"):
            self._horizontal_group_focus_memory = {}

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
            # Check if it's a Horizontal navigation group we care about
            if (
                isinstance(current, Horizontal)
                and hasattr(current, "classes")
                and (
                    "tab-actions" in current.classes
                    or "instance-actions" in current.classes
                    or "dialog-actions" in current.classes
                    or "wizard-actions" in current.classes
                )
            ):
                return current
            current = current.parent

        return None

    def _update_horizontal_focus_memory(self, widget):
        """Update focus memory for a widget's horizontal group.

        Args:
            widget: The widget that was focused
        """
        self._ensure_focus_memory_initialized()
        horizontal_parent = self._get_horizontal_nav_parent(widget)
        if horizontal_parent:
            # Use id() to get unique identifier for the parent container
            self._horizontal_group_focus_memory[id(horizontal_parent)] = widget

    def _get_remembered_focus_in_group(self, horizontal_parent):
        """Get the last focused widget in a horizontal group.

        Args:
            horizontal_parent: The horizontal container

        Returns:
            The last focused widget in this group, or None if no memory
        """
        self._ensure_focus_memory_initialized()
        return self._horizontal_group_focus_memory.get(id(horizontal_parent))

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
            with contextlib.suppress(Exception):
                # Get the title label and scroll it into view (at the top)
                title_label = self.query("Label.screen-title").first()  # type: ignore[attr-defined]
                if title_label:
                    title_label.scroll_visible(top=True, animate=True)
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
            with contextlib.suppress(Exception):
                title_label = self.query("Label.screen-title").first()  # type: ignore[attr-defined]
                if title_label:
                    title_label.scroll_visible(top=True, animate=True)
            return

        # If the target widget is in a horizontal group, use focus memory if available
        target_widget = focus_chain[target_index]
        target_horizontal_parent = self._get_horizontal_nav_parent(target_widget)

        if target_horizontal_parent:
            # Check if we have a remembered focus in this group
            remembered_widget = self._get_remembered_focus_in_group(
                target_horizontal_parent
            )

            if remembered_widget and remembered_widget in focus_chain:
                # Use the remembered widget
                target_widget = remembered_widget
            else:
                # No memory, find the first widget in this horizontal group
                first_in_group_index = target_index
                while first_in_group_index > 0:
                    prev_widget = focus_chain[first_in_group_index - 1]
                    prev_horizontal_parent = self._get_horizontal_nav_parent(
                        prev_widget
                    )

                    # Stop if previous widget is not in the same horizontal group
                    if prev_horizontal_parent != target_horizontal_parent:
                        break

                    first_in_group_index -= 1

                target_widget = focus_chain[first_in_group_index]

        # Focus the target element and update memory
        target_widget.focus()
        self._update_horizontal_focus_memory(target_widget)

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
            # Scroll the current focused widget to bottom to reveal content below
            with contextlib.suppress(Exception):
                focused.scroll_visible(top=False, animate=True)
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
            with contextlib.suppress(Exception):
                focused.scroll_visible(top=False, animate=True)
            return

        # If the target widget is in a horizontal group, use focus memory if available
        target_widget = focus_chain[target_index]
        target_horizontal_parent = self._get_horizontal_nav_parent(target_widget)

        if target_horizontal_parent:
            # Check if we have a remembered focus in this group
            remembered_widget = self._get_remembered_focus_in_group(
                target_horizontal_parent
            )

            if remembered_widget and remembered_widget in focus_chain:
                # Use the remembered widget
                target_widget = remembered_widget
            # Otherwise just use the first widget in the group (target_widget is already set)

        # Focus the target element and update memory
        target_widget.focus()
        self._update_horizontal_focus_memory(target_widget)

    def on_descendant_focus(self, event: DescendantFocus) -> None:
        """Ensure focused widgets are scrolled into view.

        Args:
            event: The focus event containing the focused widget
        """
        # Update focus memory if this widget is in a horizontal group
        self._update_horizontal_focus_memory(event.widget)

        # Scroll the VerticalScroll container to keep focused widget visible
        # This ensures proper scrolling within the container
        with contextlib.suppress(Exception):
            # Find the first VerticalScroll container in this screen
            scroll_container = self.query_one(VerticalScroll)  # type: ignore[attr-defined]
            scroll_container.scroll_to_widget(event.widget, animate=True)

    # =========================================================================
    # Boundary Navigation Helpers
    # These methods help panels/screens handle navigation at focus chain edges
    # =========================================================================

    def _scroll_to_top_boundary(
        self, scroll_container_selector: str = "VerticalScroll"
    ) -> bool:
        """Scroll container to top when at navigation boundary.

        Use this when the user presses up at the first focusable element
        to scroll and reveal content above (like title labels).

        Args:
            scroll_container_selector: CSS selector for the scroll container

        Returns:
            True if scroll was triggered, False otherwise
        """
        try:
            scroll_container = self.query_one(scroll_container_selector)  # type: ignore[attr-defined]
            scroll_container.scroll_home(animate=True)
            return True
        except Exception:
            return False

    def _scroll_to_bottom_boundary(
        self, scroll_container_selector: str = "VerticalScroll"
    ) -> bool:
        """Scroll container to bottom when at navigation boundary.

        Use this when the user presses down at the last focusable element
        to scroll and reveal any content below.

        Args:
            scroll_container_selector: CSS selector for the scroll container

        Returns:
            True if scroll was triggered, False otherwise
        """
        try:
            scroll_container = self.query_one(scroll_container_selector)  # type: ignore[attr-defined]
            scroll_container.scroll_end(animate=True)
            return True
        except Exception:
            return False

    def handle_boundary_navigation(
        self,
        event,
        focusables: list,
        current_index: int,
        scroll_container_selector: str = "VerticalScroll",
    ) -> bool:
        """Handle navigation at focus chain boundaries with scroll behavior.

        This helper method consolidates the common pattern of:
        - At top (index 0) + up key: Scroll to top, prevent default
        - At bottom (max index) + down key: Scroll to bottom, prevent default

        Use this in on_key() handlers to simplify boundary navigation logic.

        Args:
            event: The key event (must have key, prevent_default, stop attributes)
            focusables: List of focusable widgets in the current scope
            current_index: Current position in the focusables list
            scroll_container_selector: CSS selector for scroll container

        Returns:
            True if boundary was handled (event should be stopped), False otherwise

        Example:
            def on_key(self, event: Key) -> None:
                focused = self.screen.focused
                buttons = [w for w in self.query("Button") if w.focusable]

                if focused in buttons:
                    current_index = buttons.index(focused)
                    if self.handle_boundary_navigation(event, buttons, current_index):
                        return  # Boundary handled

                # ... other key handling
        """
        if not focusables:
            return False

        max_index = len(focusables) - 1

        if event.key == "up" and current_index == 0:
            # At top - scroll to reveal content above
            self._scroll_to_top_boundary(scroll_container_selector)
            event.prevent_default()
            event.stop()
            return True

        elif event.key == "down" and current_index == max_index:
            # At bottom - scroll to reveal content below
            self._scroll_to_bottom_boundary(scroll_container_selector)
            event.prevent_default()
            event.stop()
            return True

        return False

    def action_focus_left(self) -> None:
        """Navigate left within a horizontal group.

        Handles focus movement when pressing left arrow:
        - Only works if current widget is in a horizontal navigation group
        - Moves focus to the previous focusable widget in the group
        - Does not wrap - stays on first element if already there
        - Does not navigate if not in a horizontal group
        """
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal group
        horizontal_parent = self._get_horizontal_nav_parent(focused)
        if not horizontal_parent:
            # Not in a horizontal group, do nothing
            return

        # Get all focusable widgets in this horizontal container

        focusable_widgets = [
            widget
            for widget in horizontal_parent.query("Select, Button")
            if widget.can_focus and widget.display and not widget.disabled
        ]

        if len(focusable_widgets) <= 1:
            # Only one or zero widgets, nothing to navigate to
            return

        try:
            current_index = focusable_widgets.index(focused)
        except ValueError:
            # Current widget not in list
            return

        # Navigate left (previous widget)
        new_index = current_index - 1
        if new_index >= 0:
            focusable_widgets[new_index].focus()
            self._update_horizontal_focus_memory(focusable_widgets[new_index])

    def action_focus_right(self) -> None:
        """Navigate right within a horizontal group.

        Handles focus movement when pressing right arrow:
        - Only works if current widget is in a horizontal navigation group
        - Moves focus to the next focusable widget in the group
        - Does not wrap - stays on last element if already there
        - Does not navigate if not in a horizontal group
        """
        focused = self.focused
        if not focused:
            return

        # Check if we're in a horizontal group
        horizontal_parent = self._get_horizontal_nav_parent(focused)
        if not horizontal_parent:
            # Not in a horizontal group, do nothing
            return

        # Get all focusable widgets in this horizontal container

        focusable_widgets = [
            widget
            for widget in horizontal_parent.query("Select, Button")
            if widget.can_focus and widget.display and not widget.disabled
        ]

        if len(focusable_widgets) <= 1:
            # Only one or zero widgets, nothing to navigate to
            return

        try:
            current_index = focusable_widgets.index(focused)
        except ValueError:
            # Current widget not in list
            return

        # Navigate right (next widget)
        new_index = current_index + 1
        if new_index < len(focusable_widgets):
            focusable_widgets[new_index].focus()
            self._update_horizontal_focus_memory(focusable_widgets[new_index])


class SystemUtilityMixin:
    """Mixin providing platform-specific system operations.

    Provides cross-platform methods for:
    - Opening files in system editor
    - Opening folders in system file explorer

    Usage:
        class MyScreen(Screen, SystemUtilityMixin):
            def some_handler(self):
                self.open_file_in_editor(Path("/path/to/file.txt"))
                self.open_folder_in_explorer(Path("/path/to/folder"))

    Note: These methods handle platform detection (Windows, macOS, Linux)
    automatically and use appropriate system commands.
    """

    if TYPE_CHECKING:
        from textual.app import App

        app: "App[object]"

    def open_file_in_editor(self, file_path: Path | str) -> bool:
        """Open a file in the system's default editor.

        Args:
            file_path: Path to the file to open

        Returns:
            True if successful, False otherwise

        Note:
            This method automatically:
            - Validates file exists
            - Detects platform (Windows/macOS/Linux)
            - Uses appropriate system command
            - Shows notification to user
        """
        from claudefig.utils.platform import open_file_in_editor as platform_open_file

        try:
            platform_open_file(file_path)
            self.notify(  # type: ignore[attr-defined]
                "Opened file in editor",
                severity="information",
            )
            return True

        except FileNotFoundError as e:
            self.notify(  # type: ignore[attr-defined]
                str(e),
                severity="error",
            )
            return False
        except ValueError as e:
            self.notify(  # type: ignore[attr-defined]
                str(e),
                severity="error",
            )
            return False
        except (RuntimeError, Exception) as e:
            # Catch subprocess and other unexpected errors
            self.notify(  # type: ignore[attr-defined]
                f"Failed to open file: {e}",
                severity="error",
            )
            return False

    def open_folder_in_explorer(self, folder_path: Path | str) -> bool:
        """Open a folder in the system's file explorer.

        Args:
            folder_path: Path to the folder to open

        Returns:
            True if successful, False otherwise

        Note:
            This method automatically:
            - Creates folder if it doesn't exist
            - Detects platform (Windows/macOS/Linux)
            - Uses appropriate system command
            - Shows notification to user
        """
        from claudefig.utils.platform import (
            open_folder_in_explorer as platform_open_folder,
        )

        try:
            platform_open_folder(folder_path, create_if_missing=True)
            self.notify(  # type: ignore[attr-defined]
                f"Opened folder: {folder_path}",
                severity="information",
            )
            return True

        except FileNotFoundError as e:
            self.notify(  # type: ignore[attr-defined]
                str(e),
                severity="error",
            )
            return False
        except (OSError, RuntimeError, Exception) as e:
            # Catch subprocess and other unexpected errors
            self.notify(  # type: ignore[attr-defined]
                f"Failed to open folder: {e}",
                severity="error",
            )
            return False
