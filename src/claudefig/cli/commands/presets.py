"""Preset management commands.

This module contains commands for managing project presets
(list, create, delete, apply, show, open).
"""

import os
from pathlib import Path

import click
from rich.table import Table

from claudefig.cli.decorators import handle_errors
from claudefig.config_template_manager import ConfigTemplateManager
from claudefig.error_messages import ErrorMessages, format_cli_error, format_cli_warning
from claudefig.exceptions import (
    ConfigFileExistsError,
    TemplateNotFoundError,
)
from claudefig.logging_config import get_logger

# Import platform utilities
from claudefig.utils.platform import open_file_in_editor, open_folder_in_explorer

# Import shared console from parent
from .. import console

logger = get_logger("cli.presets")


@click.group(name="presets")
def presets_group():
    """Manage project presets (reusable project configurations).

    Presets let you save and reuse complete project configurations across
    multiple projects. Save your current project setup as a preset, then
    apply it to new projects for consistent configuration.

    Use 'claudefig presets --help' to see all available commands.
    """
    pass


@presets_group.command("list")
@click.option(
    "--validate",
    is_flag=True,
    help="Include validation status for each preset",
)
@handle_errors("listing presets")
def presets_list(validate):
    """List all available presets."""
    manager = ConfigTemplateManager()
    presets_list = manager.list_global_presets(include_validation=validate)

    if not presets_list:
        console.print("[yellow]No presets found[/yellow]")
        console.print(f"\n[dim]Presets location: {manager.global_presets_dir}[/dim]")
        return

    console.print(f"\n[bold blue]Available Presets[/bold blue] ({len(presets_list)})\n")
    console.print(f"[dim]Location: {manager.global_presets_dir}[/dim]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Description", style="white", width=40)
    table.add_column("Files", style="green", width=8)

    if validate:
        table.add_column("Valid", style="yellow", width=8)

    for preset in presets_list:
        row = [
            preset["name"],
            preset.get("description", "N/A"),
            str(preset.get("file_count", 0)),
        ]

        if validate and "validation" in preset:
            valid = preset["validation"].get("valid", False)
            row.append("[green]Yes[/green]" if valid else "[red]No[/red]")

        table.add_row(*row)

    console.print(table)
    console.print("\n[dim]Use 'claudefig presets show <name>' for details[/dim]")


@presets_group.command("show")
@click.argument("preset_name")
@handle_errors("showing preset")
def presets_show(preset_name):
    """Show details of a preset.

    PRESET_NAME: Name of the preset to display
    """
    manager = ConfigTemplateManager()

    # Get preset config
    try:
        preset_config = manager.get_preset_config(preset_name)
    except FileNotFoundError:
        console.print(
            format_cli_warning(ErrorMessages.not_found("preset", preset_name))
        )
        console.print(
            "\n[dim]Use 'claudefig presets list' to see available presets[/dim]"
        )
        return

    # Get preset metadata
    presets_list = manager.list_global_presets()
    preset_info = next((p for p in presets_list if p["name"] == preset_name), None)

    console.print(f"\n[bold blue]Preset: {preset_name}[/bold blue]\n")

    if preset_info:
        console.print(f"Description: {preset_info.get('description', 'N/A')}")
        console.print(f"File Count:  {preset_info.get('file_count', 0)}")

    console.print("\n[bold]File Instances:[/bold]\n")

    # Display file instances
    files = preset_config.get_file_instances()
    if files:
        for file_inst in files:
            file_type = file_inst.get("type", "?")
            path = file_inst.get("path", "?")
            preset = file_inst.get("preset", "?")
            enabled = file_inst.get("enabled", True)

            status = "[green]enabled[/green]" if enabled else "[dim]disabled[/dim]"
            console.print(f"  • {file_type}: {path} ({status})")
            console.print(f"      Preset: {preset}")
    else:
        console.print("  [dim]No file instances[/dim]")


@presets_group.command("apply")
@click.argument("preset_name")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Project path to apply preset to (default: current directory)",
)
@handle_errors(
    "applying preset",
    extra_handlers={
        TemplateNotFoundError: lambda e: (
            console.print(f"[red]Preset not found:[/red] {e}"),  # type: ignore[func-returns-value]
            console.print(
                "\n[dim]Use 'claudefig presets list' to see available presets[/dim]"
            ),  # type: ignore[func-returns-value]
        )[-1],
        FileNotFoundError: lambda e: (
            console.print(f"[red]Preset not found:[/red] {e}"),  # type: ignore[func-returns-value]
            console.print(
                "\n[dim]Use 'claudefig presets list' to see available presets[/dim]"
            ),  # type: ignore[func-returns-value]
        )[-1],
        ConfigFileExistsError: lambda e: (
            console.print(f"[red]Error:[/red] {e}"),  # type: ignore[func-returns-value]
            console.print(
                "[dim]Remove existing config or choose a different directory[/dim]"
            ),  # type: ignore[func-returns-value]
        )[-1],
        FileExistsError: lambda e: (
            console.print("[red]Error:[/red] claudefig.toml already exists"),  # type: ignore[func-returns-value]
            console.print(
                "[dim]Remove existing config or choose a different directory[/dim]"
            ),  # type: ignore[func-returns-value]
        )[-1],
    },
)
def presets_apply(preset_name, path):
    """Apply a preset to a project.

    PRESET_NAME: Name of the preset to apply
    """
    repo_path = Path(path).resolve()

    manager = ConfigTemplateManager()

    console.print(
        f"[bold green]Applying preset '{preset_name}' to:[/bold green] {repo_path}"
    )

    manager.apply_preset_to_project(preset_name, target_path=repo_path)

    console.print(f"\n[green]+[/green] Preset '{preset_name}' applied successfully!")
    console.print(f"[dim]Created: {repo_path / 'claudefig.toml'}[/dim]")


@presets_group.command("create")
@click.argument("preset_name")
@click.option(
    "--description",
    default="",
    help="Description of the preset",
)
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Project path to save config from (default: current directory)",
)
@handle_errors(
    "creating preset",
    extra_handlers={
        ValueError: lambda e: console.print(f"[red]Error:[/red] {e}"),
        FileNotFoundError: lambda e: console.print(f"[red]Error:[/red] {e}"),
    },
)
def presets_create(preset_name, description, path):
    """Save current project config as a preset.

    PRESET_NAME: Name for the new preset
    """
    repo_path = Path(path).resolve()

    # Ensure a config exists in the project
    config_path = repo_path / "claudefig.toml"
    if not config_path.exists():
        console.print(
            format_cli_error(ErrorMessages.config_file_not_found(str(repo_path)))
        )
        console.print("[dim]Initialize a config first with 'claudefig init'[/dim]")
        raise click.Abort()

    manager = ConfigTemplateManager()

    # Temporarily change to project dir to read its config
    original_cwd = os.getcwd()
    try:
        os.chdir(repo_path)
        manager.save_global_preset(preset_name, description)
    finally:
        os.chdir(original_cwd)

    console.print(f"\n[green]+[/green] Created preset: [cyan]{preset_name}[/cyan]")
    console.print(
        f"[dim]Location: {manager.global_presets_dir / preset_name / 'claudefig.toml'}[/dim]"
    )


@presets_group.command("delete")
@click.argument("preset_name")
@click.confirmation_option(prompt="Are you sure you want to delete this preset?")
@handle_errors(
    "deleting preset",
    extra_handlers={
        TemplateNotFoundError: lambda e: console.print(
            f"[yellow]Preset not found:[/yellow] {e}"
        ),
        ValueError: lambda e: console.print(f"[red]Error:[/red] {e}"),
        FileNotFoundError: lambda e: console.print("[yellow]Preset not found[/yellow]"),
    },
)
def presets_delete(preset_name):
    """Delete a preset.

    PRESET_NAME: Name of the preset to delete
    """
    manager = ConfigTemplateManager()

    manager.delete_global_preset(preset_name)

    console.print(f"[green]+[/green] Deleted preset: [cyan]{preset_name}[/cyan]")


@presets_group.command("edit")
@click.argument("preset_name")
@handle_errors(
    "editing preset",
    extra_handlers={
        RuntimeError: lambda e: console.print(f"[red]Error opening editor:[/red] {e}"),
    },
)
def presets_edit(preset_name):
    """Edit a preset's TOML file in your default editor.

    Opens the preset's .toml configuration file in your system's default
    text editor (or $EDITOR if set). You can edit the preset's metadata
    and file instance configurations.

    PRESET_NAME: Name of the preset to edit (e.g., "default", "my_fastapi_project")

    Examples:

        # Edit a preset
        claudefig presets edit my_preset

        # Edit and customize the default preset
        claudefig presets edit default
    """
    manager = ConfigTemplateManager()

    # Check if preset exists (directory-based structure)
    preset_dir = manager.global_presets_dir / preset_name
    preset_file = preset_dir / "claudefig.toml"

    if not preset_dir.exists() or not preset_file.exists():
        console.print(
            format_cli_warning(ErrorMessages.not_found("preset", preset_name))
        )
        console.print(
            "\n[dim]Use 'claudefig presets list' to see available presets[/dim]"
        )
        return

    # Check if it's a default preset
    if preset_name == "default":
        console.print(
            "[yellow]Warning: Editing default preset - changes will affect new projects[/yellow]\n"
        )

    console.print(f"[bold blue]Opening preset file:[/bold blue] {preset_file}\n")

    console.print(f"[dim]Opening {preset_file} in editor...[/dim]")

    open_file_in_editor(preset_file)

    console.print("[green]+[/green] Preset file edited")


@presets_group.command("open")
@handle_errors("opening presets directory")
def presets_open():
    """Open the presets directory in file explorer.

    Opens ~/.claudefig/presets/ in the system file manager.
    """
    manager = ConfigTemplateManager()
    presets_dir = manager.global_presets_dir

    # Ensure directory exists
    presets_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold blue]Opening presets directory:[/bold blue] {presets_dir}\n")

    try:
        open_folder_in_explorer(presets_dir)
        console.print("[green]+[/green] Opened in file manager")
    except RuntimeError:
        console.print("[yellow]Could not open file manager automatically[/yellow]")
        console.print(f"\n[dim]Navigate to: {presets_dir}[/dim]")
