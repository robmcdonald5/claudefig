"""Multi-step wizard for creating presets from discovered components."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Button, Input, Label, Static

from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.models import ComponentDiscoveryResult, DiscoveredComponent
from claudefig.services.component_discovery_service import ComponentDiscoveryService
from claudefig.services.validation_service import validate_not_empty
from claudefig.tui.base import BaseScreen
from claudefig.tui.widgets import CheckboxList


class CreatePresetWizard(BaseScreen):
    """Multi-step wizard for creating presets from discovered components.

    Step 1: Preset name and description input
    Step 2: Component discovery and selection (final step - creates preset)
    """

    current_step = reactive(1, init=False)

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

        # Store initial step
        self._initial_step = 1

        # Remember last focused button for navigation memory
        self._last_button_index: int = 0

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
            indicator.update(f"Step {new_step} of 2")
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

            # Note: No refresh needed - mount() automatically updates the display
        except Exception as e:
            self.notify(f"Error building step {new_step}: {e}", severity="error")

    def _focus_step1_input(self) -> None:
        """Focus the preset name input in step 1."""
        try:
            name_input = self.query_one("#input-preset-name", Input)
            name_input.focus()
        except Exception:
            pass

    def compose_screen_content(self) -> ComposeResult:
        """Compose the wizard screen content."""
        with VerticalScroll(id="wizard-screen", can_focus=False):
            yield Label("CREATE PRESET FROM REPOSITORY", classes="screen-title")
            yield Label(
                "Discover and select Claude Code components to include in your preset",
                classes="screen-description",
            )
            yield Static(
                "Step 1 of 2", id="step-indicator", classes="wizard-step-indicator"
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
        """Build Step 2: Component selection.

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

        # Checkbox list for component selection
        container.mount(
            Label(
                "Select components to include (all selected by default):",
                classes="wizard-label",
            )
        )
        container.mount(
            CheckboxList(
                components=self.discovery_result.components,
                id="component-checklist",
            )
        )

        # Actions
        actions = Horizontal(classes="wizard-actions")
        container.mount(actions)
        actions.mount(Button("← Back", id="btn-back"))
        actions.mount(Button("Create Preset", id="btn-create"))

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

        elif event.button.id == "btn-create":
            # Get selected components from checkbox list
            try:
                checklist = self.query_one("#component-checklist", CheckboxList)
                self.selected_components = checklist.get_selected()
            except Exception:
                # If checklist doesn't exist, use all components
                if self.discovery_result:
                    self.selected_components = self.discovery_result.components
                else:
                    self.selected_components = []

            # Create the preset
            self._create_preset()

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

    def on_key(self, event: Key) -> None:
        """Handle key events for navigation.

        Allows Tab to move between SelectionList and buttons (standard behavior).
        Handles up/down arrow navigation between CheckboxList and buttons with memory.

        Args:
            event: The key event
        """
        focused = self.focused

        # Handle CheckboxList navigation to buttons
        if event.key == "down":
            try:
                from claudefig.tui.widgets import CheckboxList

                checklist = self.query_one("#component-checklist", CheckboxList)
                if focused == checklist:
                    # Check if at last enabled option
                    enabled_indices = [
                        i
                        for i, opt in enumerate(checklist._options)
                        if not opt.disabled
                    ]
                    if enabled_indices and checklist.highlighted == enabled_indices[-1]:
                        # At boundary - go to remembered button
                        try:
                            actions = self.query_one(".wizard-actions")
                            buttons = list(actions.query(Button))
                            if buttons:
                                # Focus the remembered button (default to first)
                                button_index = min(
                                    self._last_button_index, len(buttons) - 1
                                )
                                buttons[button_index].focus()
                                event.prevent_default()
                                event.stop()
                                return
                        except Exception:
                            pass
            except Exception:
                pass

        # Handle button navigation
        if isinstance(focused, Button):
            try:
                actions = self.query_one(".wizard-actions")
                if focused.parent == actions:
                    buttons = list(actions.query(Button))
                    try:
                        current_index = buttons.index(focused)

                        # Up arrow on ANY button -> go back to CheckboxList
                        if event.key == "up":
                            # Remember which button we were on
                            self._last_button_index = current_index
                            try:
                                from claudefig.tui.widgets import CheckboxList

                                checklist = self.query_one(
                                    "#component-checklist", CheckboxList
                                )
                                checklist.focus()
                                event.prevent_default()
                                event.stop()
                                return
                            except Exception:
                                pass

                        # Down arrow on last button -> prevent wrapping
                        elif event.key == "down" and current_index == len(buttons) - 1:
                            event.prevent_default()
                            event.stop()
                            return
                    except (ValueError, Exception):
                        pass
            except Exception:
                pass
