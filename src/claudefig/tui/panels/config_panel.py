"""Config panel for editing project configuration."""

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Label

from claudefig.config import Config
from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileInstance, FileType
from claudefig.preset_manager import PresetManager
from claudefig.tui.screens import CreatePresetScreen, FileInstanceEditScreen
from claudefig.tui.widgets import FileTypeSection


class ConfigPanel(Container):
    """Panel for editing current project's .claudefig.toml."""

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize config panel.

        Args:
            config: Config object for current project
        """
        super().__init__(**kwargs)
        self.config = config
        self.preset_manager = PresetManager()
        self.config_template_manager = ConfigTemplateManager()
        self.instance_manager = FileInstanceManager(self.preset_manager)

    def compose(self) -> ComposeResult:
        """Compose the config panel."""
        yield Label("Project Configuration", classes="panel-title")

        # Check if config exists
        if not self.config.config_path or not self.config.config_path.exists():
            yield Label(
                "No .claudefig.toml found in current directory.\n\n"
                "Go to 'Presets' panel and use a preset to create a config.",
                classes="placeholder",
            )
            return

        with VerticalScroll():
            yield Label(f"Path: {self.config.config_path}", classes="panel-subtitle")

            # Load file instances
            instances_data = self.config.get_file_instances()
            if instances_data:
                self.instance_manager.load_instances(instances_data)

                # Group by file type
                instances_by_type: dict[FileType, list[FileInstance]] = {}
                for instance in self.instance_manager.list_instances():
                    if instance.type not in instances_by_type:
                        instances_by_type[instance.type] = []
                    instances_by_type[instance.type].append(instance)

                # Display sections
                enabled_count = sum(
                    1 for i in self.instance_manager.list_instances() if i.enabled
                )
                total_count = len(self.instance_manager.list_instances())
                yield Label(
                    f"Summary: {total_count} file instances ({enabled_count} enabled, {total_count - enabled_count} disabled)",
                    classes="config-summary-title",
                )

                for file_type in sorted(
                    instances_by_type.keys(), key=lambda ft: ft.value
                ):
                    yield FileTypeSection(
                        file_type,
                        instances_by_type[file_type],
                        classes="file-type-section",
                    )
            else:
                yield Label("No file instances configured.", classes="placeholder")

            # Footer button
            with Horizontal(classes="button-row"):
                yield Button(
                    "Save Current Config as New Preset", id="btn-save-as-preset"
                )

    @work
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        import asyncio

        button_id = event.button.id
        if not button_id:
            return

        try:
            # Toggle instance
            if button_id.startswith("toggle-"):
                instance_id = button_id.replace("toggle-", "")
                await self._toggle_instance(instance_id)

            # Remove instance
            elif button_id.startswith("remove-"):
                instance_id = button_id.replace("remove-", "")
                await self._remove_instance(instance_id)

            # Edit instance
            elif button_id.startswith("edit-"):
                instance_id = button_id.replace("edit-", "")
                self._edit_instance(instance_id)

            # Add instance
            elif button_id.startswith("add-"):
                file_type_str = button_id.replace("add-", "")
                self._add_instance(file_type_str)

            # Save as preset
            elif button_id == "btn-save-as-preset":
                result = await self.app.push_screen_wait(CreatePresetScreen())
                if result and result.get("action") == "create":
                    await self._save_as_preset(
                        result.get("name"), result.get("description")
                    )
        except asyncio.CancelledError:
            # User cancelled the operation (pressed Escape) - this is normal
            pass

    async def _toggle_instance(self, instance_id: str) -> None:
        """Toggle instance enabled/disabled."""
        try:
            instance = self.instance_manager.get_instance(instance_id)
            if instance:
                instance.enabled = not instance.enabled
                self.instance_manager.update_instance(instance)

                # Save to config
                instances_data = [
                    inst.to_dict() for inst in self.instance_manager.list_instances()
                ]
                self.config.set_file_instances(instances_data)
                self.config.save()

                status = "enabled" if instance.enabled else "disabled"
                self.app.notify(f"Instance {status}", severity="information")

                # Refresh panel
                self.refresh(recompose=True)

        except Exception as e:
            self.app.notify(f"Error toggling instance: {e}", severity="error")

    async def _remove_instance(self, instance_id: str) -> None:
        """Remove an instance from config."""
        try:
            self.instance_manager.remove_instance(instance_id)

            # Save to config
            instances_data = [
                inst.to_dict() for inst in self.instance_manager.list_instances()
            ]
            self.config.set_file_instances(instances_data)
            self.config.save()

            self.app.notify("Instance removed", severity="information")

            # Refresh panel
            self.refresh(recompose=True)

        except Exception as e:
            self.app.notify(f"Error removing instance: {e}", severity="error")

    async def _save_as_preset(self, name: str, description: str) -> None:
        """Save current config as new preset."""
        try:
            self.config_template_manager.save_global_preset(name, description)
            self.app.notify(f"Saved config as preset '{name}'", severity="information")

        except Exception as e:
            self.app.notify(f"Error saving preset: {e}", severity="error")

    @work
    async def _edit_instance(self, instance_id: str) -> None:
        """Open edit dialog for an existing file instance."""
        import asyncio

        try:
            instance = self.instance_manager.get_instance(instance_id)
            if not instance:
                self.app.notify(f"Instance '{instance_id}' not found", severity="error")
                return

            # Open edit screen
            result = await self.app.push_screen_wait(
                FileInstanceEditScreen(
                    self.instance_manager, self.preset_manager, instance=instance
                )
            )

            if result and result.get("action") == "save":
                updated_instance = result.get("instance")

                # Update instance
                self.instance_manager.update_instance(updated_instance)

                # Save to config
                instances_data = [
                    inst.to_dict() for inst in self.instance_manager.list_instances()
                ]
                self.config.set_file_instances(instances_data)
                self.config.save()

                self.app.notify("Instance updated successfully", severity="information")

                # Refresh panel
                self.refresh(recompose=True)

        except asyncio.CancelledError:
            # User cancelled the operation (pressed Escape) - this is normal
            pass
        except Exception as e:
            self.app.notify(f"Error editing instance: {e}", severity="error")

    @work
    async def _add_instance(self, file_type_str: str) -> None:
        """Open add dialog for a new file instance."""
        import asyncio

        try:
            # Parse file type
            file_type = FileType(file_type_str)

            # Open add screen
            result = await self.app.push_screen_wait(
                FileInstanceEditScreen(
                    self.instance_manager,
                    self.preset_manager,
                    instance=None,
                    file_type=file_type,
                )
            )

            if result and result.get("action") == "save":
                new_instance = result.get("instance")

                # Add instance
                validation_result = self.instance_manager.add_instance(new_instance)

                if not validation_result.valid:
                    error_msg = "\n".join(validation_result.errors)
                    self.app.notify(
                        f"Failed to add instance:\n{error_msg}", severity="error"
                    )
                    return

                # Save to config
                instances_data = [
                    inst.to_dict() for inst in self.instance_manager.list_instances()
                ]
                self.config.set_file_instances(instances_data)
                self.config.save()

                self.app.notify("Instance added successfully", severity="information")

                # Refresh panel
                self.refresh(recompose=True)

        except asyncio.CancelledError:
            # User cancelled the operation (pressed Escape) - this is normal
            pass
        except Exception as e:
            self.app.notify(f"Error adding instance: {e}", severity="error")
