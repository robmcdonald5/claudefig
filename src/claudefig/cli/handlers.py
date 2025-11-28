"""Shared error handlers for CLI commands.

This module provides reusable error handler functions for the
@handle_errors decorator's extra_handlers parameter.

These replace the tuple-based lambda pattern (code smell) with
proper named functions for maintainability and clarity.
"""

from rich.console import Console

from claudefig.exceptions import ConfigFileExistsError, TemplateNotFoundError

console = Console()


# =============================================================================
# Preset-related handlers
# =============================================================================


def handle_template_not_found(e: TemplateNotFoundError) -> None:
    """Handle TemplateNotFoundError for preset operations.

    Args:
        e: The TemplateNotFoundError exception
    """
    console.print(f"[red]Preset not found:[/red] {e}")
    console.print("\n[dim]Use 'claudefig presets list' to see available presets[/dim]")


def handle_preset_not_found(e: FileNotFoundError) -> None:
    """Handle FileNotFoundError for preset operations.

    Args:
        e: The FileNotFoundError exception
    """
    console.print(f"[red]Preset not found:[/red] {e}")
    console.print("\n[dim]Use 'claudefig presets list' to see available presets[/dim]")


def handle_config_file_exists(e: ConfigFileExistsError) -> None:
    """Handle ConfigFileExistsError when applying presets.

    Args:
        e: The ConfigFileExistsError exception
    """
    console.print(f"[red]Error:[/red] {e}")
    console.print("[dim]Remove existing config or choose a different directory[/dim]")


def handle_file_exists_error(e: FileExistsError) -> None:
    """Handle FileExistsError when config already exists.

    Args:
        e: The FileExistsError exception
    """
    console.print("[red]Error:[/red] claudefig.toml already exists")
    console.print("[dim]Remove existing config or choose a different directory[/dim]")


def handle_preset_value_error(e: ValueError) -> None:
    """Handle ValueError for preset operations.

    Args:
        e: The ValueError exception
    """
    console.print(f"[red]Error:[/red] {e}")


def handle_preset_file_not_found(e: FileNotFoundError) -> None:
    """Handle FileNotFoundError for preset creation (no config found).

    Args:
        e: The FileNotFoundError exception
    """
    console.print(f"[red]Error:[/red] {e}")


def handle_preset_delete_not_found(e: TemplateNotFoundError) -> None:
    """Handle TemplateNotFoundError during preset deletion (warning style).

    Args:
        e: The TemplateNotFoundError exception
    """
    console.print(f"[yellow]Preset not found:[/yellow] {e}")


def handle_preset_delete_file_not_found(e: FileNotFoundError) -> None:
    """Handle FileNotFoundError during preset deletion.

    Args:
        e: The FileNotFoundError exception
    """
    console.print("[yellow]Preset not found[/yellow]")


# =============================================================================
# Editor-related handlers
# =============================================================================


def handle_editor_error(e: RuntimeError) -> None:
    """Handle RuntimeError when opening editor fails.

    Args:
        e: The RuntimeError exception
    """
    console.print(f"[red]Error opening editor:[/red] {e}")
