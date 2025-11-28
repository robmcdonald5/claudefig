"""Configuration management commands.

This module contains commands for managing claudefig configuration settings
(get, set, show, reset, init).
"""

import click
from rich.table import Table

from claudefig.cli.decorators import handle_errors, with_config
from claudefig.logging_config import get_logger
from claudefig.services import config_service, file_instance_service

# Import shared console from parent
from .. import console

logger = get_logger("cli.config")


def parse_config_value(value: str) -> str | bool | int | float:
    """Parse a config value string to appropriate type.

    Handles:
    - Booleans: 'true', 'false' (case-insensitive)
    - Integers: '42', '-7'
    - Floats: '3.14', '-2.5'
    - Strings: everything else

    Args:
        value: String value from CLI input

    Returns:
        Parsed value as appropriate Python type
    """
    lower = value.lower()
    if lower in ("true", "false"):
        return lower == "true"

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


@click.group(name="config")
def config_group():
    """Manage claudefig configuration settings."""
    pass


@config_group.command("get")
@click.argument("key")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@with_config()
@handle_errors("getting config")
def config_get(key, path, config_data, config_repo):
    """Get a configuration value.

    KEY: Configuration key in dot notation (e.g., claude.create_settings)
    """
    value = config_service.get_value(config_data, key)

    if value is None:
        console.print(f"[yellow]Key not found:[/yellow] {key}")
        console.print("[dim]Use 'claudefig config list' to see all settings[/dim]")
    else:
        console.print(f"[cyan]{key}:[/cyan] {value}")


@config_group.command("set")
@click.argument("key")
@click.argument("value")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@with_config()
@handle_errors("setting config")
def config_set(key, value, path, config_data, config_repo):
    """Set a configuration value.

    KEY: Configuration key in dot notation (e.g., claude.create_settings)
    VALUE: Value to set (use 'true', 'false' for booleans)
    """
    # Parse value
    parsed_value = parse_config_value(value)

    # Validate key and type
    validation = config_service.validate_config_key(key, parsed_value)
    if not validation.valid:
        for error in validation.errors:
            console.print(f"[red]Error:[/red] {error}")
        raise click.Abort()

    # Set value
    config_service.set_value(config_data, key, parsed_value)

    # Save to config file
    config_service.save_config(config_data, config_repo)

    console.print(f"[green]+[/green] Set [cyan]{key}[/cyan] = {parsed_value}")
    console.print(f"[dim]Config saved to: {config_repo.get_path()}[/dim]")


@config_group.command("set-init")
@click.option(
    "--overwrite/--no-overwrite",
    default=None,
    help="Allow overwriting existing files during init",
)
@click.option(
    "--backup/--no-backup",
    default=None,
    help="Create backup files before overwriting",
)
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@with_config()
@handle_errors("setting init config")
def config_set_init(overwrite, backup, path, config_data, config_repo):
    """Manage initialization settings.

    Configure how claudefig behaves during file generation.
    """
    changes = []

    # Update overwrite setting
    if overwrite is not None:
        config_service.set_value(config_data, "init.overwrite_existing", overwrite)
        status = "enabled" if overwrite else "disabled"
        changes.append(f"overwrite_existing: {status}")

    # Update backup setting
    if backup is not None:
        config_service.set_value(config_data, "init.create_backup", backup)
        status = "enabled" if backup else "disabled"
        changes.append(f"create_backup: {status}")

    if not changes:
        # Show current settings
        console.print("[bold blue]Current initialization settings:[/bold blue]\n")
        console.print(
            f"Overwrite existing: {config_service.get_value(config_data, 'init.overwrite_existing', False)}"
        )
        console.print(
            f"Create backups:     {config_service.get_value(config_data, 'init.create_backup', True)}"
        )
        console.print(
            "\n[dim]Use --overwrite/--no-overwrite or --backup/--no-backup to change settings[/dim]"
        )
        return

    # Save changes
    config_service.save_config(config_data, config_repo)

    console.print("\n[green]+[/green] Updated initialization settings:")
    for change in changes:
        console.print(f"  {change}")
    console.print(f"\n[dim]Config saved to: {config_repo.get_path()}[/dim]")


@config_group.command("list")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@with_config()
@handle_errors("listing config")
def config_list(path, config_data, config_repo):
    """List all configuration settings and file instances."""
    if config_repo.exists():
        console.print(
            f"[bold blue]Configuration from:[/bold blue] {config_repo.get_path()}\n"
        )
    else:
        console.print(
            "[bold blue]Configuration:[/bold blue] [dim](using defaults)[/dim]\n"
        )

    # Display config in organized sections
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan", width=35)
    table.add_column("Value", style="green")

    # Claudefig section
    table.add_row("[bold]Claudefig[/bold]", "")
    table.add_row(
        "  version", str(config_service.get_value(config_data, "claudefig.version"))
    )
    table.add_row(
        "  schema_version",
        str(config_service.get_value(config_data, "claudefig.schema_version")),
    )
    table.add_row(
        "  template_source",
        config_service.get_value(config_data, "claudefig.template_source"),
    )

    # Init section
    table.add_row("[bold]Init[/bold]", "")
    table.add_row(
        "  overwrite_existing",
        str(config_service.get_value(config_data, "init.overwrite_existing")),
    )

    # Custom section
    custom_dir = config_service.get_value(config_data, "custom.template_dir")
    presets_dir = config_service.get_value(config_data, "custom.presets_dir")
    if custom_dir or presets_dir:
        table.add_row("[bold]Custom[/bold]", "")
        if custom_dir:
            table.add_row("  template_dir", custom_dir)
        if presets_dir:
            table.add_row("  presets_dir", presets_dir)

    console.print(table)

    # Display file instances
    console.print("\n[bold blue]File Instances:[/bold blue]\n")

    instances_data = config_service.get_file_instances(config_data)
    if instances_data:
        instances_dict, _ = file_instance_service.load_instances_from_config(
            instances_data
        )
        all_instances = file_instance_service.list_instances(instances_dict)

        if all_instances:
            # Group by file type
            current_type = None
            for instance in all_instances:
                if instance.type != current_type:
                    current_type = instance.type
                    console.print(f"\n[bold]{instance.type.display_name}[/bold]")

                status = (
                    "[green]enabled[/green]"
                    if instance.enabled
                    else "[dim]disabled[/dim]"
                )
                console.print(f"  - {instance.id} ({status})")
                console.print(f"      Path: {instance.path}")
                console.print(f"      Preset: {instance.preset}")
        else:
            console.print("[yellow]No file instances configured[/yellow]")
    else:
        console.print("[yellow]No file instances configured[/yellow]")

    console.print("\n[dim]Use 'claudefig files list' for more details[/dim]")


@config_group.command("repair")
@handle_errors("repairing config")
def config_repair():
    """Repair the user configuration directory.

    This command ensures the ~/.claudefig directory is functional by:

    \b
    - Creating any missing directories in the folder structure
    - Creating the config.toml file if missing
    - Restoring the default preset from the library if missing/incomplete

    This is a non-destructive operation - it only creates missing items
    and does not modify or overwrite existing files.
    """
    from claudefig.user_config import repair_user_config

    success = repair_user_config(verbose=True)

    if not success:
        raise click.ClickException("Repair completed with errors")


@config_group.command("reset")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
@handle_errors("resetting config")
def config_reset(yes):
    """Reset the user configuration to factory defaults.

    This command deletes the entire ~/.claudefig directory and all custom
    configuration, presets, and components. After reset, run any claudefig
    command to reinitialize with defaults.

    \b
    WARNING: This operation cannot be undone!
    """
    from claudefig.user_config import get_user_config_dir, reset_user_config

    config_dir = get_user_config_dir()

    if not config_dir.exists():
        console.print("[yellow]No user configuration to reset[/yellow]")
        return

    if not yes:
        console.print(
            f"[bold red]Warning:[/bold red] This will delete [cyan]{config_dir}[/cyan] "
            "and all custom configuration!\n"
        )
        if not click.confirm("Are you sure you want to reset?", default=False):
            console.print("[yellow]Reset cancelled[/yellow]")
            return

    success = reset_user_config(force=True)

    if not success:
        raise click.ClickException("Reset failed")
