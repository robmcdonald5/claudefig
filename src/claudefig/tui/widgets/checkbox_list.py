"""Checkbox list widget for component selection using Textual's SelectionList."""

from rich.text import Text
from textual.binding import Binding
from textual.events import MouseScrollDown, MouseScrollUp
from textual.widgets import SelectionList
from textual.widgets.selection_list import Selection

from claudefig.models import DiscoveredComponent, FileType


class CheckboxList(SelectionList[str]):
    """List of checkboxes for component selection, grouped by type.

    Uses Textual's built-in SelectionList widget for proper layout and interaction.
    Includes priority Tab bindings and custom arrow key navigation that escapes
    focus to surrounding widgets when reaching list boundaries.
    """

    BINDINGS = [
        Binding("tab", "focus_next", "Next", priority=True),
        Binding("shift+tab", "focus_previous", "Previous", priority=True),
    ]

    def __init__(self, components: list[DiscoveredComponent], **kwargs) -> None:
        """Initialize checkbox list.

        Args:
            components: List of discovered components to display
        """
        # Store components for later retrieval
        self.components = components

        # Create mapping from component name to component object
        self._component_map: dict[str, DiscoveredComponent] = {
            c.name: c for c in components
        }

        # Build selections grouped by file type
        selections = self._build_selections(components)

        super().__init__(*selections, **kwargs)

    def _build_selections(
        self, components: list[DiscoveredComponent]
    ) -> list[Selection]:
        """Build Selection items grouped by file type.

        Args:
            components: List of discovered components

        Returns:
            List of Selection objects with styled prompts
        """
        if not components:
            return []

        # Group components by file type
        grouped: dict[FileType, list[DiscoveredComponent]] = {}
        for component in components:
            if component.type not in grouped:
                grouped[component.type] = []
            grouped[component.type].append(component)

        selections = []

        # Build selections for each group
        for file_type, group_components in grouped.items():
            # Add group header as a disabled selection (visual separator)
            header_text = Text(
                f"──── {file_type.display_name} ({len(group_components)}) ────",
                style="bold dim",
            )
            # Create a unique ID for the header that won't conflict with component names
            selections.append(
                Selection(header_text, f"__header_{file_type.value}__", disabled=True)
            )

            # Add each component in the group
            for component in group_components:
                # Create Rich Text with name (bold) and path (dim)
                prompt = Text()
                prompt.append(f"{component.name}", style="bold")
                prompt.append(" - ", style="dim")
                prompt.append(f"{component.relative_path}", style="dim italic")

                # Add warning indicator if duplicate
                if component.is_duplicate:
                    prompt.append(" ⚠", style="yellow")

                # All components start selected
                selections.append(Selection(prompt, component.name, initial_state=True))

        return selections

    def get_selected(self) -> list[DiscoveredComponent]:
        """Get list of selected components.

        Returns:
            List of selected DiscoveredComponent objects
        """
        # Get selected component names from SelectionList
        selected_names = self.selected

        # Map names back to DiscoveredComponent objects
        return [
            self._component_map[name]
            for name in selected_names
            if name in self._component_map
        ]

    def get_selected_count(self) -> int:
        """Get count of selected components.

        Returns:
            Number of selected components
        """
        # Filter out header selections (they have __ prefix)
        return len([s for s in self.selected if not s.startswith("__header_")])

    def get_unselected_count(self) -> int:
        """Get count of unselected components.

        Returns:
            Number of unselected components
        """
        return len(self.components) - self.get_selected_count()

    def select_all(self) -> "CheckboxList":
        """Select all components.

        Returns:
            Self for method chaining
        """
        for option in self._options:
            # Skip header options
            if option.id and not option.id.startswith("__header_"):
                self.select(option.id)
        return self

    def deselect_all(self) -> "CheckboxList":
        """Deselect all components.

        Returns:
            Self for method chaining
        """
        for option in self._options:
            # Skip header options
            if option.id and not option.id.startswith("__header_"):
                self.deselect(option.id)
        return self

    def action_focus_next(self) -> None:
        """Move focus to the next widget outside this SelectionList."""
        self.screen.focus_next()

    def action_focus_previous(self) -> None:
        """Move focus to the previous widget outside this SelectionList."""
        self.screen.focus_previous()

    def action_cursor_down(self) -> None:
        """Move cursor down within the list.

        Boundary handling is done by parent screen for navigation memory.
        """
        # Normal navigation within list
        super().action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up within the list.

        Stops at top without escaping to prevent focus on non-interactive widgets.
        """
        # Get enabled option indices
        enabled_indices = [i for i, opt in enumerate(self._options) if not opt.disabled]
        if not enabled_indices:
            return

        # Check if at first enabled option
        if self.highlighted == enabled_indices[0]:
            # At top boundary - stay in list
            return

        # Normal navigation within list
        super().action_cursor_up()

    def on_mouse_scroll_down(self, event: MouseScrollDown) -> None:
        """Handle mouse scroll down - prevent bubbling to parent scroll container.

        This stops scroll events from propagating to the parent VerticalScroll,
        keeping the list's internal scrolling isolated.
        """
        # Stop the event from bubbling to parent containers
        event.stop()

    def on_mouse_scroll_up(self, event: MouseScrollUp) -> None:
        """Handle mouse scroll up - prevent bubbling to parent scroll container.

        This stops scroll events from propagating to the parent VerticalScroll,
        keeping the list's internal scrolling isolated.
        """
        # Stop the event from bubbling to parent containers
        event.stop()
