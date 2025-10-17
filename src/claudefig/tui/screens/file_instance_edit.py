"""File instance edit modal screen."""

from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, Select, Switch

from claudefig.error_messages import ErrorMessages
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileInstance, FileType
from claudefig.preset_manager import PresetManager
from claudefig.tui.base import BaseModalScreen


class FileInstanceEditScreen(BaseModalScreen):
    """Modal screen to add or edit a file instance."""

    def __init__(
        self,
        instance_manager: FileInstanceManager,
        preset_manager: PresetManager,
        instance: FileInstance | None = None,
        file_type: FileType | None = None,
        **kwargs,
    ) -> None:
        """Initialize file instance edit screen.

        Args:
            instance_manager: FileInstanceManager for validation
            preset_manager: PresetManager for loading available presets
            instance: Existing FileInstance to edit (None for new)
            file_type: Pre-selected file type (for Add button)
        """
        super().__init__(**kwargs)
        self.instance_manager = instance_manager
        self.preset_manager = preset_manager
        self.instance = instance
        self.file_type = file_type or (instance.type if instance else None)
        self.is_edit_mode = instance is not None
        self.validation_errors: list[str] = []
        self.validation_warnings: list[str] = []

    def compose_title(self) -> str:
        """Return the modal title."""
        return "Edit File Instance" if self.is_edit_mode else "Add File Instance"

    def compose_content(self) -> ComposeResult:
        """Compose the modal content."""
        # File Type dropdown
        yield Label("File Type:", classes="dialog-label")
        file_type_options = [(ft.display_name, ft.value) for ft in FileType]
        selected_type = (
            self.file_type.value if self.file_type else file_type_options[0][1]
        )
        yield Select(
            options=file_type_options,
            value=selected_type,
            id="select-file-type",
            allow_blank=False,
        )

        # Preset dropdown (will be populated based on file type)
        yield Label("\nPreset:", classes="dialog-label")
        preset_options = self._get_preset_options_for_type(
            self.file_type or FileType.CLAUDE_MD
        )
        selected_preset = (
            self.instance.preset
            if self.instance
            else (preset_options[0][1] if preset_options else "")
        )
        yield Select(
            options=preset_options,
            value=selected_preset,
            id="select-preset",
            allow_blank=False,
        )

        # Path input (conditional based on path_customizable)
        yield Label("\nPath:", classes="dialog-label")

        # Determine default path
        if self.instance:
            default_path = self.instance.path
        elif self.file_type:
            default_path = self.file_type.default_path
        else:
            default_path = ""

        # Check if path is customizable
        is_path_customizable = (
            self.file_type.path_customizable if self.file_type else True
        )

        if is_path_customizable:
            # Show editable input for CLAUDE.md and .gitignore
            yield Input(
                placeholder="e.g., CLAUDE.md or docs/CLAUDE.md",
                value=default_path,
                id="input-path",
            )
        else:
            # Show read-only label for fixed location/directory types
            yield Label(
                f"  {default_path} (fixed location)",
                classes="dialog-text setting-description",
            )
            # Keep a hidden input to maintain form logic
            yield Input(
                value=default_path,
                id="input-path",
                classes="hidden",
            )

        # Add helper text for special behaviors
        if self.file_type:
            if self.file_type.append_mode:
                yield Label(
                    "ℹ️  This file will be appended to if it already exists",
                    classes="dialog-text setting-description",
                )
            if self.file_type.is_directory:
                yield Label(
                    f"ℹ️  Files will be created in {self.file_type.default_path}",
                    classes="dialog-text setting-description",
                )

        # Enabled checkbox
        yield Label("\nEnabled:", classes="dialog-label")
        enabled_value = self.instance.enabled if self.instance else True
        yield Switch(value=enabled_value, id="switch-enabled")

        # Validation feedback area
        yield Label("", id="validation-feedback", classes="dialog-text")

    def compose_actions(self) -> ComposeResult:
        """Compose the action buttons."""
        save_text = "Save" if self.is_edit_mode else "Add"
        yield Button(save_text, id="btn-save", variant="primary")
        yield Button("Cancel", id="btn-cancel")

    def _get_preset_options_for_type(
        self, file_type: FileType
    ) -> list[tuple[str, str]]:
        """Get available presets for a specific file type.

        Args:
            file_type: FileType to filter presets for

        Returns:
            List of (display_name, preset_id) tuples
        """
        try:
            all_presets = self.preset_manager.list_presets(file_type)
            if not all_presets:
                # Fallback to default preset
                return [(f"{file_type.value}:default", f"{file_type.value}:default")]

            return [
                (f"{preset.name} ({preset.source.value})", preset.id)
                for preset in all_presets
            ]
        except Exception:
            # Fallback
            return [(f"{file_type.value}:default", f"{file_type.value}:default")]

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select dropdown changes."""
        if event.select.id == "select-file-type":
            # Update preset dropdown when file type changes
            try:
                new_file_type = FileType(event.value)
                preset_select = self.query_one("#select-preset", Select)

                # Update preset options
                new_preset_options = self._get_preset_options_for_type(new_file_type)
                preset_select.set_options(new_preset_options)

                # Update path placeholder
                path_input = self.query_one("#input-path", Input)
                old_default = self.file_type.default_path if self.file_type else ""
                if not path_input.value or path_input.value == old_default:
                    path_input.value = new_file_type.default_path

                self.file_type = new_file_type

                # Revalidate
                self._validate_current_inputs()

            except Exception as e:
                self.notify(ErrorMessages.operation_failed("updating file type", str(e)), severity="error")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for real-time validation."""
        if event.input.id == "input-path":
            self._validate_current_inputs()

    def _validate_current_inputs(self) -> None:
        """Validate current form inputs and display feedback."""
        try:
            # Get current values
            file_type_select = self.query_one("#select-file-type", Select)
            preset_select = self.query_one("#select-preset", Select)
            path_input = self.query_one("#input-path", Input)
            enabled_switch = self.query_one("#switch-enabled", Switch)

            file_type = FileType(file_type_select.value)
            preset_id_value = preset_select.value
            path = path_input.value
            enabled = enabled_switch.value

            # Ensure preset_id is a string
            if not isinstance(preset_id_value, str):
                return
            preset_id = preset_id_value

            # Generate instance ID
            preset_name = preset_id.split(":")[-1] if ":" in preset_id else preset_id
            if self.is_edit_mode and self.instance:
                instance_id = self.instance.id
            else:
                instance_id = self.instance_manager.generate_instance_id(
                    file_type, preset_name, path
                )

            # Create temporary instance for validation
            temp_instance = FileInstance(
                id=instance_id,
                type=file_type,
                preset=preset_id,
                path=path,
                enabled=enabled,
            )

            # Validate
            result = self.instance_manager.validate_instance(
                temp_instance, is_update=self.is_edit_mode
            )

            self.validation_errors = result.errors
            self.validation_warnings = result.warnings

            # Update feedback label
            feedback_label = self.query_one("#validation-feedback", Label)
            if result.errors:
                feedback_label.update("\n".join([f"❌ {err}" for err in result.errors]))
                feedback_label.styles.color = "red"
            elif result.warnings:
                feedback_label.update(
                    "\n".join([f"⚠️  {warn}" for warn in result.warnings])
                )
                feedback_label.styles.color = "yellow"
            else:
                feedback_label.update("✓ Validation passed")
                feedback_label.styles.color = "green"

        except Exception as e:
            feedback_label = self.query_one("#validation-feedback", Label)
            feedback_label.update(f"❌ Validation error: {e}")
            feedback_label.styles.color = "red"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-cancel":
            self.dismiss()
        elif event.button.id == "btn-save":
            self._save_instance()

    def _save_instance(self) -> None:
        """Save the file instance and dismiss."""
        try:
            # Get current values
            file_type_select = self.query_one("#select-file-type", Select)
            preset_select = self.query_one("#select-preset", Select)
            path_input = self.query_one("#input-path", Input)
            enabled_switch = self.query_one("#switch-enabled", Switch)

            file_type = FileType(file_type_select.value)
            preset_id_value = preset_select.value
            path = path_input.value.strip()
            enabled = enabled_switch.value

            # Ensure preset_id is a string
            if not isinstance(preset_id_value, str):
                self.notify(ErrorMessages.empty_value("preset selection"), severity="error")
                return
            preset_id = preset_id_value

            # Validate path not empty
            if not path:
                self.notify(ErrorMessages.empty_value("path"), severity="error")
                return

            # Generate instance ID
            preset_name = preset_id.split(":")[-1] if ":" in preset_id else preset_id
            if self.is_edit_mode and self.instance:
                instance_id = self.instance.id
            else:
                instance_id = self.instance_manager.generate_instance_id(
                    file_type, preset_name, path
                )

            # Create file instance
            instance = FileInstance(
                id=instance_id,
                type=file_type,
                preset=preset_id,
                path=path,
                enabled=enabled,
                variables=self.instance.variables if self.instance else {},
            )

            # Final validation
            result = self.instance_manager.validate_instance(
                instance, is_update=self.is_edit_mode
            )

            if result.has_errors:
                # Show errors
                error_msg = "\n".join(result.errors)
                self.notify(ErrorMessages.validation_failed(error_msg), severity="error")
                return

            # Dismiss with result
            self.dismiss(
                result={
                    "action": "save",
                    "instance": instance,
                    "is_edit": self.is_edit_mode,
                }
            )

        except Exception as e:
            self.notify(ErrorMessages.operation_failed("saving instance", str(e)), severity="error")
