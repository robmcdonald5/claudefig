"""Preset card widget for displaying preset information."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label


class PresetCard(Container):
    """Display preset template info with actions."""

    def __init__(self, preset_name: str, preset_data: dict, **kwargs) -> None:
        """Initialize preset card.

        Args:
            preset_name: Name of the preset
            preset_data: Preset data dict with keys: description, file_count, path
        """
        super().__init__(**kwargs)
        self.preset_name = preset_name
        self.preset_data = preset_data

    def compose(self) -> ComposeResult:
        """Compose the preset card."""
        yield Label(self.preset_name, classes="preset-name")
        yield Label(self.preset_data.get("description", ""), classes="preset-description")
        yield Label(f"{self.preset_data.get('file_count', 0)} files", classes="preset-file-count")
        with Horizontal(classes="preset-actions"):
            yield Button("View Details", id=f"view-{self.preset_name}", classes="preset-button")
            yield Button("Use for Project", id=f"use-{self.preset_name}", classes="preset-button")
            if self.preset_name != "default":
                yield Button("Delete", id=f"delete-{self.preset_name}", classes="preset-button")
