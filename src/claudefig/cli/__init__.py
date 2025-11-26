"""CLI entry point for claudefig.

This module serves as the main entry point for the claudefig CLI.
It imports the main Click group and registers all command subgroups.
"""

from rich.console import Console

# Shared console for all CLI modules
console = Console()

# Import main group
# Import command groups
from .commands import components, config, files, presets  # noqa: E402
from .main import main  # noqa: E402

# Register command groups with main
main.add_command(components.components_group)  # type: ignore[has-type]
main.add_command(config.config_group)  # type: ignore[has-type]
main.add_command(files.files_group)  # type: ignore[has-type]
main.add_command(presets.presets_group)  # type: ignore[has-type]

__all__ = ["main", "console"]
