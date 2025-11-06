"""CLI entry point for claudefig.

This module serves as the main entry point for the claudefig CLI.
It imports the main Click group and registers all command subgroups.
"""

from rich.console import Console

# Shared console for all CLI modules
console = Console()

# Import main group
from .main import main  # noqa: E402

# Import command groups
from .commands import config, files, presets  # noqa: E402

# Register command groups with main
main.add_command(config.config_group)
main.add_command(files.files_group)
main.add_command(presets.presets_group)

__all__ = ["main", "console"]
