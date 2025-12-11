"""Multi-step wizard for creating presets from discovered components."""

import contextlib
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Button, Checkbox, Input, Label, Static

from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.models import ComponentDiscoveryResult, DiscoveredComponent, FileType
from claudefig.services.component_discovery_service import ComponentDiscoveryService
from claudefig.services.validation_service import validate_not_empty
from claudefig.tui.base import BaseScreen


class CreatePresetWizard(BaseScreen):
    """Multi-step wizard for creating presets from discovered components.

    Step 1: Preset name and description input
    Step 2: Component discovery and selection (final step - creates preset)
    """

    TOTAL_STEPS = 2

    current_step = reactive(1, init=False)
    # Track selected count for display
    selected_count = reactive(0, init=False)

    def __init__(self, repo_path: Path, **kwargs) -> None:
        """Initialize the preset creation wizard.

        Args:
            repo_path: Path to the repository to scan for components
        """
        super().__init__(**kwargs)
        self.repo_path = repo_path
        self.preset_name: str = ""
        self.preset_description: str = ""
        self.discovery_result: ComponentDiscoveryResult | None = None
        self.selected_components: list[DiscoveredComponent] = []
        # Use unique key combining name and relative path to avoid collisions
        self.component_checkboxes: dict[str, Checkbox] = {}

        # Store initial step
        self._initial_step = 1

        # Navigation memory for button focus
        self._last_button_id: str = "btn-back"

        # Initialize flag for step watcher (M4 fix)
        self._initialized = False

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        # Build initial step after refresh to ensure widgets are ready
        self.call_after_refresh(self._initialize_step1)

    def _initialize_step1(self) -> None:
        """Initialize step 1 content after mount."""
        # Set initialized flag so watcher won't skip future step changes
        self._initialized = True

        try:
            content = self.query_one("#wizard-content", Vertical)
            content.remove_children()
            self._build_step1(content)

            # Auto-focus the preset name input after refresh
            self.call_after_refresh(self._focus_step1_input)
        except Exception as e:
            # Log the error for debugging
            self.notify(f"Error initializing wizard: {e}", severity="error")

    def watch_current_step(self, new_step: int) -> None:
        """Rebuild UI when step changes.

        Args:
            new_step: The new step number
        """
        # Update step indicator
        try:
            indicator = self.query_one("#step-indicator", Static)
            indicator.update(f"Step {new_step} of {self.TOTAL_STEPS}")
        except Exception as e:
            # Widget might not exist yet during initialization
            self.notify(f"Error updating step indicator: {e}", severity="error")
            return

        # Rebuild content (but not during initial mount)
        if not hasattr(self, "_initialized"):
            return

        try:
            content = self.query_one("#wizard-content", Vertical)
            content.remove_children()

            if new_step == 1:
                self._build_step1(content)
                # Auto-focus the preset name input when navigating to step 1
                self.call_after_refresh(self._focus_step1_input)
            elif new_step == 2:
                self._build_step2(content)
                # Auto-focus the first button when navigating to step 2
                self.call_after_refresh(self._focus_step2_button)

            # Note: No refresh needed - mount() automatically updates the display
        except Exception as e:
            self.notify(f"Error building step {new_step}: {e}", severity="error")

    def _focus_step1_input(self) -> None:
        """Focus the preset name input in step 1."""
        try:
            name_input = self.query_one("#input-preset-name", Input)
            name_input.focus()
        except Exception as e:
            self.log.warning(f"Could not focus input: {e}")

    def _focus_step2_button(self) -> None:
        """Focus the first button in step 2."""
        try:
            btn = self.query_one("#btn-back", Button)
            btn.focus()
        except Exception as e:
            self.log.warning(f"Could not focus button: {e}")

    def compose_screen_content(self) -> ComposeResult:
        """Compose the wizard screen content."""
        with VerticalScroll(id="wizard-screen", can_focus=False):
            yield Label("CREATE PRESET FROM REPOSITORY", classes="screen-title")
            yield Label(
                "Discover and select Claude Code components to include in your preset",
                classes="screen-description",
            )
            yield Static(
                f"Step 1 of {self.TOTAL_STEPS}",
                id="step-indicator",
                classes="wizard-step-indicator",
            )

            # Dynamic content area
            yield Vertical(id="wizard-content", classes="wizard-content")

    def _build_step1(self, container: Vertical) -> None:
        """Build Step 1: Preset name and description.

        Args:
            container: Container to mount widgets into
        """
        container.mount(Label("Preset Name:", classes="wizard-label"))
        container.mount(
            Input(
                placeholder="my-custom-preset",
                id="input-preset-name",
                value=self.preset_name,
            )
        )

        container.mount(Label("Description (optional):", classes="wizard-label"))
        container.mount(
            Input(
                placeholder="Describe your preset",
                id="input-preset-description",
                value=self.preset_description,
            )
        )

        # Actions - mount container first, then add buttons
        actions = Horizontal(classes="wizard-actions")
        container.mount(actions)
        actions.mount(Button("← Back", id="btn-back"))
        actions.mount(Button("Discover Components →", id="btn-discover"))

    def _build_step2(self, container: Vertical) -> None:
        """Build Step 2: Component selection with checkboxes.

        Args:
            container: Container to mount widgets into
        """
        # Run discovery if not already done
        if self.discovery_result is None:
            discovery_service = ComponentDiscoveryService()
            try:
                self.discovery_result = discovery_service.discover_components(
                    self.repo_path
                )
            except Exception as e:
                container.mount(
                    Label(
                        f"Error scanning repository: {e}",
                        classes="wizard-error",
                    )
                )
                actions = Horizontal(classes="wizard-actions")
                container.mount(actions)
                actions.mount(Button("← Back", id="btn-back"))
                return

        # Check if any components found
        if self.discovery_result.total_found == 0:
            container.mount(
                Label(
                    "No usable components detected in repository",
                    classes="wizard-error",
                )
            )
            container.mount(
                Static(
                    "The scanner looked for CLAUDE.md files, .claude/ directory contents, "
                    ".gitignore files, MCP configurations, and more.",
                    classes="wizard-help-text",
                )
            )
            actions = Horizontal(classes="wizard-actions")
            container.mount(actions)
            actions.mount(Button("← Back", id="btn-back"))
            return

        # Show discovered components count
        container.mount(
            Label(
                f"Found {self.discovery_result.total_found} components",
                classes="wizard-status-success",
            )
        )
        container.mount(
            Static(
                f"Scan completed in {self.discovery_result.scan_time_ms:.1f}ms",
                classes="wizard-help-text",
            )
        )

        # Show warnings if any
        if self.discovery_result.has_warnings:
            container.mount(Label("⚠ Warnings:", classes="wizard-warning-header"))
            for warning in self.discovery_result.warnings:
                container.mount(Static(f"• {warning}", classes="wizard-warning-text"))

        # Component selection section with count display
        total_components = self.discovery_result.total_found
        container.mount(
            Label(
                "Select/deselect components you want in the preset:",
                classes="wizard-label",
            )
        )
        # Selection count label (will be updated dynamically)
        container.mount(
            Static(
                f"Selected: {total_components} of {total_components}",
                id="selection-count",
                classes="wizard-help-text",
            )
        )

        # Add action buttons in a single row
        action_buttons = Horizontal(classes="dialog-actions")
        container.mount(action_buttons)
        action_buttons.mount(Button("← Back", id="btn-back"))
        action_buttons.mount(Button("Select All", id="btn-select-all"))
        action_buttons.mount(Button("Clear All", id="btn-clear-all"))
        action_buttons.mount(Button("Create Preset", id="btn-create"))

        # Clear existing checkboxes
        self.component_checkboxes.clear()

        # Group components by file type
        grouped: dict[FileType, list[DiscoveredComponent]] = {}
        for component in self.discovery_result.components:
            if component.type not in grouped:
                grouped[component.type] = []
            grouped[component.type].append(component)

        # Build checkboxes for each group directly on the page
        for file_type, group_components in grouped.items():
            # Add group header
            container.mount(
                Static(
                    f"──── {file_type.display_name} ({len(group_components)}) ────",
                    classes="component-group-header",
                )
            )

            # Add checkbox for each component
            for idx, component in enumerate(group_components):
                # Create checkbox label
                label = f"{component.name} - {component.relative_path}"
                if component.is_duplicate:
                    label += " ⚠"

                # Create safe ID (only letters, numbers, underscores, hyphens)
                safe_id = f"chk-{file_type.value}-{idx}"

                # Create checkbox (default to checked)
                checkbox = Checkbox(label, value=True, id=safe_id)
                # Use unique key combining name and path to avoid collisions (M5 fix)
                checkbox_key = f"{component.name}:{component.relative_path}"
                self.component_checkboxes[checkbox_key] = checkbox
                container.mount(checkbox)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button pressed event
        """
        if event.button.id == "btn-back":
            if self.current_step == 1:
                # Exit wizard
                self.dismiss()
            else:
                # Go to previous step
                self.current_step -= 1

        elif event.button.id == "btn-discover":
            # Validate name before proceeding
            name_input = self.query_one("#input-preset-name", Input)
            desc_input = self.query_one("#input-preset-description", Input)

            preset_name = name_input.value.strip()

            # Validate preset name
            validation_result = validate_not_empty(preset_name, "Preset name")
            if validation_result.has_errors:
                self.notify(validation_result.errors[0], severity="error")
                return

            # Store values and proceed
            self.preset_name = preset_name
            self.preset_description = desc_input.value.strip()
            self.current_step = 2

        elif event.button.id == "btn-select-all":
            self._select_all()

        elif event.button.id == "btn-clear-all":
            self._clear_all()

        elif event.button.id == "btn-create":
            # Get selected components from checkboxes
            self._gather_selected_components()
            # Create the preset with selected components
            self._create_preset()

    def _gather_selected_components(self) -> None:
        """Gather selected components from checkboxes."""
        if not self.discovery_result:
            return

        self.selected_components = []
        for component in self.discovery_result.components:
            # Use unique key matching the one used when creating checkboxes
            checkbox_key = f"{component.name}:{component.relative_path}"
            if checkbox_key in self.component_checkboxes:
                checkbox = self.component_checkboxes[checkbox_key]
                if checkbox.value:
                    self.selected_components.append(component)

    def on_key(self, event: Key) -> None:
        """Handle key events for Step 2 navigation.

        Navigation rules:
        - Left/Right: Navigate horizontally between buttons (no wrap)
        - Up/Down: Navigate vertically between checkboxes (no wrap)
        - Up from first checkbox: Go to remembered button and scroll to top
        - Down from buttons: Go to first checkbox
        - Memory: Remember which button was last focused
        """
        # Only apply custom nav on step 2
        if self.current_step != 2:
            return

        focused = self.focused
        if focused is None:
            return

        # Get buttons and checkboxes
        try:
            dialog_actions = self.query_one(".dialog-actions", Horizontal)
            buttons = list(dialog_actions.query(Button))
            checkboxes = list(self.component_checkboxes.values())
            scroll_container = self.query_one("#wizard-screen", VerticalScroll)
        except Exception:
            return

        # Handle button navigation
        if isinstance(focused, Button) and focused in buttons:
            button_idx = buttons.index(focused)

            if event.key == "left":
                # Move left, no wrap
                if button_idx > 0:
                    buttons[button_idx - 1].focus()
                    self._last_button_id = buttons[button_idx - 1].id or "btn-back"
                    event.prevent_default()
                    event.stop()
                # else: at first button, do nothing (no wrap)

            elif event.key == "right":
                # Move right, no wrap
                if button_idx < len(buttons) - 1:
                    buttons[button_idx + 1].focus()
                    self._last_button_id = buttons[button_idx + 1].id or "btn-back"
                    event.prevent_default()
                    event.stop()
                # else: at last button, do nothing (no wrap)

            elif event.key == "down":
                # Go to first checkbox
                if checkboxes:
                    self._last_button_id = focused.id or "btn-back"
                    checkboxes[0].focus()
                    # Smooth scroll to show the checkbox
                    checkboxes[0].scroll_visible(animate=False)
                    event.prevent_default()
                    event.stop()

            elif event.key == "up":
                # Scroll up when at buttons
                scroll_container.scroll_home(animate=False)
                event.prevent_default()
                event.stop()

        # Handle checkbox navigation
        elif isinstance(focused, Checkbox) and focused in checkboxes:
            checkbox_idx = checkboxes.index(focused)

            if event.key == "up":
                if checkbox_idx > 0:
                    # Move to previous checkbox
                    prev_checkbox = checkboxes[checkbox_idx - 1]
                    prev_checkbox.focus()
                    prev_checkbox.scroll_visible(animate=False)
                else:
                    # At first checkbox - go to remembered button and scroll to top
                    focused_button = False
                    with contextlib.suppress(Exception):
                        btn = self.query_one(f"#{self._last_button_id}", Button)
                        btn.focus()
                        focused_button = True
                    if not focused_button and buttons:
                        buttons[0].focus()
                    # Scroll to top of screen
                    scroll_container.scroll_home(animate=False)
                event.prevent_default()
                event.stop()

            elif event.key == "down":
                if checkbox_idx < len(checkboxes) - 1:
                    # Move to next checkbox
                    next_checkbox = checkboxes[checkbox_idx + 1]
                    next_checkbox.focus()
                    next_checkbox.scroll_visible(animate=False)
                # else: at last checkbox, no wrap - do nothing
                event.prevent_default()
                event.stop()

            elif event.key in ("left", "right"):
                # No horizontal nav on checkboxes - let default behavior handle
                pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes to update selection count."""
        self._update_selection_count()

    def _update_selection_count(self) -> None:
        """Update the selection count display."""
        if not self.discovery_result:
            return
        selected = sum(1 for cb in self.component_checkboxes.values() if cb.value)
        total = self.discovery_result.total_found
        with contextlib.suppress(Exception):
            count_label = self.query_one("#selection-count", Static)
            count_label.update(f"Selected: {selected} of {total}")

    def _select_all(self) -> None:
        """Select all checkboxes."""
        for checkbox in self.component_checkboxes.values():
            checkbox.value = True
        self._update_selection_count()

    def _clear_all(self) -> None:
        """Clear all checkboxes."""
        for checkbox in self.component_checkboxes.values():
            checkbox.value = False
        self._update_selection_count()

    def on_unmount(self) -> None:
        """Clean up widget references to prevent memory leaks."""
        self.component_checkboxes.clear()
        self.selected_components.clear()

    def _create_preset(self) -> None:
        """Create preset from selected components."""
        if not self.selected_components:
            self.notify("No components selected", severity="error")
            return

        try:
            # Create preset using ConfigTemplateManager
            template_manager = ConfigTemplateManager()
            template_manager.create_preset_from_discovery(
                preset_name=self.preset_name,
                description=self.preset_description,
                components=self.selected_components,
            )

            self.notify(
                f"Preset '{self.preset_name}' created successfully!",
                severity="information",
            )
            self.dismiss(
                result={
                    "action": "created",
                    "preset_name": self.preset_name,
                }
            )

        except ValueError as e:
            self.notify(f"Error creating preset: {e}", severity="error")
        except Exception as e:
            self.notify(
                f"Unexpected error creating preset: {e}",
                severity="error",
            )
