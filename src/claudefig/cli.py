"""CLI interface for claudefig."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from claudefig import __version__
from claudefig.error_messages import (
    ErrorMessages,
    format_cli_error,
    format_cli_warning,
)
from claudefig.exceptions import (
    BuiltInModificationError,
    ConfigFileExistsError,
    ConfigFileNotFoundError,
    FileOperationError,
    InitializationRollbackError,
    InstanceNotFoundError,
    InstanceValidationError,
    PresetExistsError,
    PresetNotFoundError,
    TemplateNotFoundError,
)
from claudefig.initializer import Initializer
from claudefig.logging_config import get_logger, setup_logging
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.repositories.preset_repository import TomlPresetRepository
from claudefig.services import config_service, file_instance_service
from claudefig.template_manager import FileTemplateManager

console = Console()
logger = get_logger("cli")


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="claudefig")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress informational output")
@click.pass_context
def main(ctx, verbose, quiet):
    """Universal config CLI tool for setting up Claude Code repositories.

    claudefig helps you initialize and manage Claude Code configurations
    with templates, settings, and best practices.

    Run without arguments to launch interactive mode.
    """
    import logging

    from claudefig.user_config import ensure_user_config

    # Setup logging based on verbosity flags
    if verbose and quiet:
        console.print(
            "[yellow]Warning: Cannot use --verbose and --quiet together. Using normal verbosity.[/yellow]"
        )
        console_level = logging.WARNING
    elif verbose:
        console_level = logging.DEBUG
    elif quiet:
        console_level = logging.ERROR
    else:
        console_level = logging.WARNING

    # Initialize logging
    setup_logging(
        console_level=console_level,
        file_level=logging.INFO,
        enable_file_logging=True,
    )

    logger.debug(f"claudefig v{__version__} starting")
    logger.debug(
        f"Verbosity: verbose={verbose}, quiet={quiet}, level={logging.getLevelName(console_level)}"
    )

    # Store flags in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    # Initialize user config on any command
    ensure_user_config(verbose=verbose)

    # If no subcommand provided, launch interactive mode
    if ctx.invoked_subcommand is None:
        ctx.invoke(interactive)


@main.command()
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path to initialize (default: current directory)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration files",
)
def init(path, force):
    """Initialize Claude Code configuration in a repository.

    Creates necessary files and directory structure for Claude Code integration:
    - .claude/ directory
    - CLAUDE.md configuration file
    - Optional settings.json
    - .claudefig.toml configuration
    """
    repo_path = Path(path).resolve()

    logger.info(f"Initializing Claude Code configuration in: {repo_path}")
    logger.debug(f"Force mode: {force}")

    console.print(
        f"[bold green]Initializing Claude Code configuration in:[/bold green] {repo_path}"
    )

    if force:
        console.print(
            "[yellow]Force mode enabled - will overwrite existing files[/yellow]"
        )

    try:
        initializer = Initializer()
        success = initializer.initialize(repo_path, force=force)

        if success:
            logger.info("Initialization completed successfully")
        else:
            logger.warning("Initialization completed with warnings")
            raise click.Abort()
    except FileOperationError as e:
        logger.error(f"File operation failed: {e}", exc_info=True)
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except InitializationRollbackError as e:
        logger.error(f"Initialization rolled back: {e}", exc_info=True)
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        console.print(
            format_cli_error(ErrorMessages.operation_failed("initialization", str(e)))
        )
        raise click.Abort() from e


@main.command()
def show():
    """Show current Claude Code configuration."""
    console.print("[bold blue]Current Configuration:[/bold blue]\n")

    try:
        config_path = config_service.find_config_path()

        if config_path:
            console.print(f"[green]Config file:[/green] {config_path}\n")
            repo = TomlConfigRepository(config_path)
        else:
            console.print("[yellow]No config file found (using defaults)[/yellow]\n")
            repo = TomlConfigRepository(Path.cwd() / ".claudefig.toml")

        config_data = config_service.load_config(repo)

        # Create a table to display config
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", width=30)
        table.add_column("Value", style="green")

        table.add_row(
            "Template Source",
            config_service.get_value(config_data, "claudefig.template_source"),
        )
        table.add_row(
            "Schema Version",
            str(config_service.get_value(config_data, "claudefig.schema_version")),
        )

        custom_dir = config_service.get_value(config_data, "custom.template_dir")
        if custom_dir:
            table.add_row("Custom Template Dir", custom_dir)

        console.print(table)

        # Show file instances summary
        console.print("\n[bold blue]File Instances:[/bold blue]\n")

        instances_data = config_service.get_file_instances(config_data)
        if instances_data:
            instances_dict, _ = file_instance_service.load_instances_from_config(
                instances_data
            )
            all_instances = file_instance_service.list_instances(instances_dict)

            # Count by type
            type_counts = {}
            for instance in all_instances:
                type_name = instance.type.display_name
                if type_name not in type_counts:
                    type_counts[type_name] = {"total": 0, "enabled": 0}
                type_counts[type_name]["total"] += 1
                if instance.enabled:
                    type_counts[type_name]["enabled"] += 1

            # Display summary
            summary_table = Table(show_header=True, header_style="bold magenta")
            summary_table.add_column("File Type", style="cyan")
            summary_table.add_column("Enabled", style="green")
            summary_table.add_column("Total", style="blue")

            for file_type, counts in sorted(type_counts.items()):
                summary_table.add_row(
                    file_type, str(counts["enabled"]), str(counts["total"])
                )

            console.print(summary_table)
            console.print(
                "\n[dim]Use 'claudefig files list' to see all file instances[/dim]"
            )
        else:
            console.print("[yellow]No file instances configured[/yellow]")
            console.print("[dim]Use 'claudefig files add' to add file instances[/dim]")

    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
    except Exception as e:
        console.print(
            format_cli_error(
                ErrorMessages.operation_failed("loading configuration", str(e))
            )
        )


@main.command()
@click.argument("template_name")
def add_template(template_name):
    """Add a new template to the repository.

    TEMPLATE_NAME: Name of the template to add
    """
    console.print(f"[bold green]Adding template:[/bold green] {template_name}")
    # TODO: Implement add-template logic
    console.print("[yellow]Implementation in progress...[/yellow]")


@main.command("list-templates")
def list_templates():
    """List all available templates."""
    console.print("[bold blue]Available Templates:[/bold blue]\n")

    try:
        # Find config and load it
        config_path = config_service.find_config_path()
        if config_path:
            config_repo = TomlConfigRepository(config_path)
            config_data = config_service.load_config(config_repo)
            custom_dir = config_service.get_value(config_data, "custom.template_dir")
        else:
            custom_dir = None

        template_manager = FileTemplateManager(Path(custom_dir) if custom_dir else None)

        templates = template_manager.list_templates()

        if not templates:
            console.print("[yellow]No templates found[/yellow]")
            return

        for template in templates:
            console.print(f"  • {template}")

    except Exception as e:
        console.print(
            format_cli_error(
                ErrorMessages.operation_failed("listing templates", str(e))
            )
        )


@main.group()
def config():
    """Manage claudefig configuration settings."""
    pass


@config.command("get")
@click.argument("key")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def config_get(key, path):
    """Get a configuration value.

    KEY: Configuration key in dot notation (e.g., claude.create_settings)
    """
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(repo)
        value = config_service.get_value(config_data, key)

        if value is None:
            console.print(f"[yellow]Key not found:[/yellow] {key}")
            console.print("[dim]Use 'claudefig config list' to see all settings[/dim]")
        else:
            console.print(f"[cyan]{key}:[/cyan] {value}")

    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Error getting config:[/red] {e}")
        raise click.Abort() from e


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def config_set(key, value, path):
    """Set a configuration value.

    KEY: Configuration key in dot notation (e.g., claude.create_settings)
    VALUE: Value to set (use 'true', 'false' for booleans)
    """
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        # Load or create config
        repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(repo)

        # Parse value
        parsed_value = value
        if value.lower() in ("true", "false"):
            parsed_value = value.lower() == "true"
        elif value.isdigit():
            parsed_value = int(value)

        # Set value
        config_service.set_value(config_data, key, parsed_value)

        # Save to config file
        config_service.save_config(config_data, repo)

        console.print(f"[green]+[/green] Set [cyan]{key}[/cyan] = {parsed_value}")
        console.print(f"[dim]Config saved to: {config_path}[/dim]")

    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Error setting config:[/red] {e}")
        raise click.Abort() from e


@config.command("set-init")
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
def config_set_init(overwrite, backup, path):
    """Manage initialization settings.

    Configure how claudefig behaves during file generation.
    """
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(repo)

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
        config_service.save_config(config_data, repo)

        console.print("\n[green]+[/green] Updated initialization settings:")
        for change in changes:
            console.print(f"  {change}")
        console.print(f"\n[dim]Config saved to: {config_path}[/dim]")

    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Error setting init config:[/red] {e}")
        raise click.Abort() from e


@config.command("list")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def config_list(path):
    """List all configuration settings and file instances."""
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(repo)

        if config_path and config_path.exists():
            console.print(f"[bold blue]Configuration from:[/bold blue] {config_path}\n")
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
                    console.print(f"  • {instance.id} ({status})")
                    console.print(f"      Path: {instance.path}")
                    console.print(f"      Preset: {instance.preset}")
            else:
                console.print("[yellow]No file instances configured[/yellow]")
        else:
            console.print("[yellow]No file instances configured[/yellow]")

        console.print("\n[dim]Use 'claudefig files list' for more details[/dim]")

    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Error listing config:[/red] {e}")
        raise click.Abort() from e


@main.group()
def files():
    """Manage file instances (files to be generated)."""
    pass


@files.command("list")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@click.option(
    "--type",
    "file_type",
    help="Filter by file type (e.g., claude_md, settings_json)",
)
@click.option(
    "--enabled-only",
    is_flag=True,
    help="Show only enabled instances",
)
def files_list(path, file_type, enabled_only):
    """List all configured file instances."""
    from claudefig.models import FileType

    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        # Load config
        repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(repo)

        # Load instances from config
        instances_data = config_service.get_file_instances(config_data)
        instances_dict, load_errors = file_instance_service.load_instances_from_config(
            instances_data
        )

        # Show load errors if any
        if load_errors:
            for error in load_errors:
                console.print(f"[yellow]Warning:[/yellow] {error}")

        # Filter by file type if provided
        filter_type = None
        if file_type:
            try:
                filter_type = FileType(file_type)
            except ValueError:
                valid_types = [ft.value for ft in FileType]
                console.print(
                    format_cli_error(
                        ErrorMessages.invalid_type("file type", file_type, valid_types)
                    )
                )
                raise click.Abort() from None

        # List instances with filters
        instances = file_instance_service.list_instances(
            instances_dict, filter_type, enabled_only
        )

        if not instances:
            console.print("[yellow]No file instances configured[/yellow]")
            console.print(
                "\nUse [cyan]claudefig files add[/cyan] to add a new file instance"
            )
            return

        # Display instances grouped by type
        console.print(f"\n[bold blue]File Instances[/bold blue] ({len(instances)})\n")

        current_type = None
        for instance in instances:
            if instance.type != current_type:
                current_type = instance.type
                console.print(f"\n[bold]{instance.type.display_name}[/bold]")

            status = "[green]+[/green]" if instance.enabled else "[dim]-[/dim]"
            console.print(f"  {status} {instance.id}")
            console.print(f"      Path: {instance.path}")
            console.print(f"      Preset: {instance.preset}")

    except Exception as e:
        console.print(
            format_cli_error(
                ErrorMessages.operation_failed("listing file instances", str(e))
            )
        )
        raise click.Abort() from e


@files.command("add")
@click.argument("file_type")
@click.option(
    "--preset",
    default="default",
    help="Preset name to use (default: default)",
)
@click.option(
    "--path-target",
    "path_target",
    help="Target path for the file (default: use file type default)",
)
@click.option(
    "--disabled",
    is_flag=True,
    help="Create instance as disabled",
)
@click.option(
    "--repo-path",
    "repo_path_arg",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def files_add(file_type, preset, path_target, disabled, repo_path_arg):
    """Add a new file instance.

    FILE_TYPE: Type of file (e.g., claude_md, settings_json)
    """
    from claudefig.models import FileInstance, FileType

    repo_path = Path(repo_path_arg).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        # Parse file type
        try:
            file_type_enum = FileType(file_type)
        except ValueError:
            console.print(f"[red]Invalid file type:[/red] {file_type}")
            console.print(f"Valid types: {', '.join([ft.value for ft in FileType])}")
            raise click.Abort() from None

        # Load config
        config_repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(config_repo)

        # Load existing instances
        instances_data = config_service.get_file_instances(config_data)
        instances_dict, load_errors = file_instance_service.load_instances_from_config(
            instances_data
        )

        # Show load errors if any
        if load_errors:
            for error in load_errors:
                console.print(f"[yellow]Warning:[/yellow] {error}")

        # Determine path
        if not path_target:
            path_target = file_type_enum.default_path

        # Generate instance ID
        instance_id = file_instance_service.generate_instance_id(
            file_type_enum, preset, path_target, instances_dict
        )

        # Build preset ID
        preset_id = f"{file_type_enum.value}:{preset}"

        # Create instance
        instance = FileInstance(
            id=instance_id,
            type=file_type_enum,
            preset=preset_id,
            path=path_target,
            enabled=not disabled,
            variables={},
        )

        # Validate and add
        preset_repo = TomlPresetRepository()
        result = file_instance_service.add_instance(
            instances_dict, instance, preset_repo, repo_path
        )

        if not result.valid:
            console.print("[red]Validation failed:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise click.Abort()

        if result.has_warnings:
            console.print("[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")

        # Save instances back to config
        updated_instances_data = file_instance_service.save_instances_to_config(
            instances_dict
        )
        config_service.set_file_instances(config_data, updated_instances_data)
        config_service.save_config(config_data, config_repo)

        console.print(
            f"\n[green]+[/green] Added file instance: [cyan]{instance.id}[/cyan]"
        )
        console.print(f"  Type: {instance.type.display_name}")
        console.print(f"  Preset: {instance.preset}")
        console.print(f"  Path: {instance.path}")
        console.print(f"  Enabled: {instance.enabled}")
        console.print(f"\n[dim]Config saved to: {config_path}[/dim]")

    except InstanceValidationError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        console.print(
            format_cli_error(
                ErrorMessages.operation_failed("adding file instance", str(e))
            )
        )
        raise click.Abort() from e


@files.command("remove")
@click.argument("instance_id")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def files_remove(instance_id, path):
    """Remove a file instance.

    INSTANCE_ID: ID of the instance to remove
    """
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        # Load config
        config_repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(config_repo)

        # Load instances
        instances_data = config_service.get_file_instances(config_data)
        instances_dict, _ = file_instance_service.load_instances_from_config(
            instances_data
        )

        # Remove instance
        if file_instance_service.remove_instance(instances_dict, instance_id):
            # Save instances back to config
            updated_instances_data = file_instance_service.save_instances_to_config(
                instances_dict
            )
            config_service.set_file_instances(config_data, updated_instances_data)
            config_service.save_config(config_data, config_repo)

            console.print(
                f"[green]+[/green] Removed file instance: [cyan]{instance_id}[/cyan]"
            )
            console.print(f"[dim]Config saved to: {config_path}[/dim]")
        else:
            console.print(
                format_cli_warning(
                    ErrorMessages.not_found("file instance", instance_id)
                )
            )

    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        console.print(
            format_cli_error(
                ErrorMessages.operation_failed("removing file instance", str(e))
            )
        )
        raise click.Abort() from e


@files.command("enable")
@click.argument("instance_id")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def files_enable(instance_id, path):
    """Enable a file instance.

    INSTANCE_ID: ID of the instance to enable
    """
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        # Load config
        config_repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(config_repo)

        # Load instances
        instances_data = config_service.get_file_instances(config_data)
        instances_dict, _ = file_instance_service.load_instances_from_config(
            instances_data
        )

        # Enable instance
        if file_instance_service.enable_instance(instances_dict, instance_id):
            # Save instances back to config
            updated_instances_data = file_instance_service.save_instances_to_config(
                instances_dict
            )
            config_service.set_file_instances(config_data, updated_instances_data)
            config_service.save_config(config_data, config_repo)

            console.print(
                f"[green]+[/green] Enabled file instance: [cyan]{instance_id}[/cyan]"
            )
            console.print(f"[dim]Config saved to: {config_path}[/dim]")
        else:
            console.print(
                format_cli_warning(
                    ErrorMessages.not_found("file instance", instance_id)
                )
            )

    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        console.print(
            format_cli_error(
                ErrorMessages.operation_failed("enabling file instance", str(e))
            )
        )
        raise click.Abort() from e


@files.command("disable")
@click.argument("instance_id")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def files_disable(instance_id, path):
    """Disable a file instance.

    INSTANCE_ID: ID of the instance to disable
    """
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        # Load config
        config_repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(config_repo)

        # Load instances
        instances_data = config_service.get_file_instances(config_data)
        instances_dict, _ = file_instance_service.load_instances_from_config(
            instances_data
        )

        # Disable instance
        if file_instance_service.disable_instance(instances_dict, instance_id):
            # Save instances back to config
            updated_instances_data = file_instance_service.save_instances_to_config(
                instances_dict
            )
            config_service.set_file_instances(config_data, updated_instances_data)
            config_service.save_config(config_data, config_repo)

            console.print(
                f"[green]+[/green] Disabled file instance: [cyan]{instance_id}[/cyan]"
            )
            console.print(f"[dim]Config saved to: {config_path}[/dim]")
        else:
            console.print(
                format_cli_warning(
                    ErrorMessages.not_found("file instance", instance_id)
                )
            )

    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        console.print(
            format_cli_error(
                ErrorMessages.operation_failed("disabling file instance", str(e))
            )
        )
        raise click.Abort() from e


@files.command("edit")
@click.argument("instance_id")
@click.option(
    "--preset",
    help="New preset to use (format: preset_name)",
)
@click.option(
    "--path-target",
    "path_target",
    help="New target path for the file",
)
@click.option(
    "--enable/--disable",
    default=None,
    help="Enable or disable the instance",
)
@click.option(
    "--repo-path",
    "repo_path_arg",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def files_edit(instance_id, preset, path_target, enable, repo_path_arg):
    """Edit an existing file instance.

    INSTANCE_ID: ID of the instance to edit
    """
    repo_path = Path(repo_path_arg).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        # Load config
        config_repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(config_repo)

        # Load instances
        instances_data = config_service.get_file_instances(config_data)
        instances_dict, _ = file_instance_service.load_instances_from_config(
            instances_data
        )

        # Get existing instance
        instance = file_instance_service.get_instance(instances_dict, instance_id)
        if not instance:
            console.print(
                format_cli_warning(
                    ErrorMessages.not_found("file instance", instance_id)
                )
            )
            raise click.Abort()

        # Track changes
        changes = []

        # Update preset if provided
        if preset:
            old_preset = instance.preset
            instance.preset = f"{instance.type.value}:{preset}"
            changes.append(f"preset: {old_preset} → {instance.preset}")

        # Update path if provided
        if path_target:
            old_path = instance.path
            instance.path = path_target
            changes.append(f"path: {old_path} → {instance.path}")

        # Update enabled state if provided
        if enable is not None:
            old_enabled = instance.enabled
            instance.enabled = enable
            status = "enabled" if enable else "disabled"
            old_status = "enabled" if old_enabled else "disabled"
            changes.append(f"status: {old_status} → {status}")

        if not changes:
            console.print("[yellow]No changes specified[/yellow]")
            console.print(
                "\n[dim]Use --preset, --path-target, or --enable/--disable to make changes[/dim]"
            )
            return

        # Validate changes
        preset_repo = TomlPresetRepository()
        result = file_instance_service.update_instance(
            instances_dict, instance, preset_repo, repo_path
        )

        if not result.valid:
            console.print("[red]Validation failed:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise click.Abort()

        if result.has_warnings:
            console.print("[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")

        # Save instances back to config
        updated_instances_data = file_instance_service.save_instances_to_config(
            instances_dict
        )
        config_service.set_file_instances(config_data, updated_instances_data)
        config_service.save_config(config_data, config_repo)

        console.print(
            f"\n[green]+[/green] Updated file instance: [cyan]{instance_id}[/cyan]"
        )
        for change in changes:
            console.print(f"  {change}")
        console.print(f"\n[dim]Config saved to: {config_path}[/dim]")

    except ConfigFileNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except InstanceNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        console.print(
            format_cli_error(
                ErrorMessages.operation_failed("editing file instance", str(e))
            )
        )
        raise click.Abort() from e


@main.group()
def presets():
    """Manage presets (templates for file types).

    Presets are reusable templates for different file types like CLAUDE.md,
    settings.json, commands, agents, etc. You can use built-in presets or
    create your own custom presets.

    Use 'claudefig presets --help' to see all available commands.
    """
    pass


@presets.command("list")
@click.option(
    "--type",
    "file_type",
    help="Filter by file type (e.g., claude_md, settings_json)",
)
def presets_list(file_type):
    """List available presets."""
    from claudefig.models import FileType
    from claudefig.preset_manager import PresetManager

    try:
        preset_manager = PresetManager()

        # Filter by file type if provided
        filter_type = None
        if file_type:
            try:
                filter_type = FileType(file_type)
            except ValueError:
                valid_types = [ft.value for ft in FileType]
                console.print(
                    format_cli_error(
                        ErrorMessages.invalid_type("file type", file_type, valid_types)
                    )
                )
                raise click.Abort() from None

        presets_list = preset_manager.list_presets(filter_type)

        if not presets_list:
            console.print("[yellow]No presets found[/yellow]")
            return

        console.print(
            f"\n[bold blue]Available Presets[/bold blue] ({len(presets_list)})\n"
        )

        # Group by file type
        current_type = None
        for preset in presets_list:
            if preset.type != current_type:
                current_type = preset.type
                console.print(f"\n[bold]{preset.type.display_name}[/bold]")

            source_badge = (
                "[cyan][built-in][/cyan]"
                if preset.source.value == "built-in"
                else f"[yellow][{preset.source.value}][/yellow]"
            )

            console.print(f"  - {preset.name} {source_badge}")
            console.print(f"      ID: {preset.id}")
            if preset.description:
                console.print(f"      {preset.description}")

    except Exception as e:
        console.print(
            format_cli_error(ErrorMessages.operation_failed("listing presets", str(e)))
        )
        raise click.Abort() from e


@presets.command("show")
@click.argument("preset_id")
def presets_show(preset_id):
    """Show detailed information about a preset.

    PRESET_ID: Preset ID in format "file_type:preset_name"
    """
    from claudefig.preset_manager import PresetManager

    try:
        preset_manager = PresetManager()
        preset = preset_manager.get_preset(preset_id)

        if not preset:
            console.print(
                format_cli_warning(ErrorMessages.not_found("preset", preset_id))
            )
            return

        console.print("\n[bold blue]Preset Details[/bold blue]\n")
        console.print(f"ID:          {preset.id}")
        console.print(f"Name:        {preset.name}")
        console.print(f"Type:        {preset.type.display_name}")
        console.print(f"Source:      {preset.source.value}")
        console.print(f"Description: {preset.description or 'N/A'}")

        if preset.tags:
            console.print(f"Tags:        {', '.join(preset.tags)}")

        if preset.template_path:
            console.print(f"Template:    {preset.template_path}")

        if preset.variables:
            console.print("\nVariables:")
            for key, value in preset.variables.items():
                console.print(f"  • {key}: {value}")

    except Exception as e:
        console.print(
            format_cli_error(ErrorMessages.operation_failed("showing preset", str(e)))
        )
        raise click.Abort() from e


@presets.command("open")
def presets_open():
    """Open the global presets directory in file explorer.

    Opens ~/.claudefig/presets/ in the system file manager.
    """
    import platform
    import subprocess

    from claudefig.user_config import get_user_config_dir

    presets_dir = get_user_config_dir() / "presets"

    # Ensure directory exists
    presets_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold blue]Opening presets directory:[/bold blue] {presets_dir}\n")

    try:
        system = platform.system()

        if system == "Windows":
            subprocess.run(["explorer", str(presets_dir)], check=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(presets_dir)], check=True)
        elif system == "Linux":
            # Try xdg-open first, fall back to alternatives
            try:
                subprocess.run(["xdg-open", str(presets_dir)], check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Try other common file managers
                for cmd in ["nautilus", "dolphin", "thunar", "nemo"]:
                    try:
                        subprocess.run([cmd, str(presets_dir)], check=True)
                        break
                    except FileNotFoundError:
                        continue
                else:
                    console.print(
                        "[yellow]Could not open file manager automatically[/yellow]"
                    )
                    console.print(f"\n[dim]Navigate to: {presets_dir}[/dim]")
                    return
        else:
            console.print(f"[yellow]Unsupported platform:[/yellow] {system}")
            console.print(f"\n[dim]Navigate to: {presets_dir}[/dim]")
            return

        console.print("[green]+[/green] Opened in file manager")

    except Exception as e:
        console.print(f"[red]Error opening directory:[/red] {e}")
        console.print(f"\n[dim]Navigate to: {presets_dir}[/dim]")


@presets.command("create")
@click.argument("preset_name")
@click.option(
    "--type",
    "file_type",
    required=True,
    help="File type for this preset (e.g., claude_md, settings_json)",
)
@click.option(
    "--description",
    default="",
    help="Description of the preset",
)
@click.option(
    "--template",
    "template_path",
    type=click.Path(exists=True),
    help="Path to template file",
)
@click.option(
    "--source",
    type=click.Choice(["user", "project"], case_sensitive=False),
    default="user",
    help="Where to store the preset (default: user)",
)
@click.option(
    "--tags",
    help="Comma-separated tags for the preset",
)
def presets_create(preset_name, file_type, description, template_path, source, tags):
    """Create a new custom preset.

    Create a new preset from scratch or from an existing template file.
    Presets can be stored at user level (~/.claudefig/presets/) or
    project level (.claudefig/presets/).

    PRESET_NAME: Name for the preset (e.g., "my_backend")

    Examples:

        # Create a simple preset
        claudefig presets create my_preset --type claude_md

        # Create from template file
        claudefig presets create backend --type claude_md --template my_template.md

        # Create with metadata
        claudefig presets create api --type claude_md --description "API docs" --tags "backend,api"
    """
    from claudefig.models import FileType, Preset, PresetSource
    from claudefig.preset_manager import PresetManager

    try:
        # Validate file type
        try:
            preset_type = FileType(file_type)
        except ValueError:
            valid_types = [ft.value for ft in FileType]
            console.print(
                format_cli_error(
                    ErrorMessages.invalid_type("file type", file_type, valid_types)
                )
            )
            raise click.Abort() from None

        # Parse source
        preset_source = (
            PresetSource.USER if source.lower() == "user" else PresetSource.PROJECT
        )

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Create preset ID
        preset_id = f"{preset_type.value}:{preset_name}"

        # Create Preset object
        preset = Preset(
            id=preset_id,
            type=preset_type,
            name=preset_name,
            description=description,
            source=preset_source,
            tags=tag_list,
            template_path=Path(template_path) if template_path else None,
        )

        # Create via preset manager
        preset_manager = PresetManager()
        preset_manager.add_preset(preset, preset_source)

        console.print(f"\n[green]+[/green] Created preset: [bold]{preset_id}[/bold]")
        console.print(f"  Type:        {preset_type.display_name}")
        console.print(f"  Source:      {preset_source.value}")
        if description:
            console.print(f"  Description: {description}")
        if template_path:
            console.print(f"  Template:    {template_path}")
        if tag_list:
            console.print(f"  Tags:        {', '.join(tag_list)}")

    except BuiltInModificationError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except PresetExistsError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except ValueError as e:
        # Catch validation errors (file type, etc.)
        console.print(
            format_cli_error(ErrorMessages.operation_failed("creating preset", str(e)))
        )
        raise click.Abort() from e
    except Exception as e:
        console.print(
            format_cli_error(ErrorMessages.operation_failed("creating preset", str(e)))
        )
        raise click.Abort() from e


@presets.command("delete")
@click.argument("preset_id")
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
def presets_delete(preset_id, force):
    """Delete a user or project preset.

    Deletes a custom preset from the user or project presets directory.
    Built-in presets cannot be deleted. You will be prompted for confirmation
    unless you use the --force flag.

    PRESET_ID: Preset ID in format "file_type:preset_name" (e.g., "claude_md:my_backend")

    Examples:

        # Delete with confirmation prompt
        claudefig presets delete claude_md:my_preset

        # Delete without confirmation
        claudefig presets delete claude_md:my_preset --force
    """
    from claudefig.preset_manager import PresetManager

    try:
        preset_manager = PresetManager()

        # Check if preset exists
        preset = preset_manager.get_preset(preset_id)
        if not preset:
            console.print(
                format_cli_warning(ErrorMessages.not_found("preset", preset_id))
            )
            return

        # Check if it's a built-in preset
        from claudefig.models import PresetSource

        if preset.source == PresetSource.BUILT_IN:
            console.print(format_cli_error("Cannot delete built-in presets"))
            raise click.Abort() from None

        # Confirmation prompt unless --force
        if not force:
            console.print("\n[yellow]About to delete preset:[/yellow]")
            console.print(f"  ID:     {preset.id}")
            console.print(f"  Name:   {preset.name}")
            console.print(f"  Type:   {preset.type.display_name}")
            console.print(f"  Source: {preset.source.value}")

            if not click.confirm("\nAre you sure you want to delete this preset?"):
                console.print("[dim]Cancelled[/dim]")
                return

        # Delete the preset
        preset_manager.delete_preset(preset_id)

        console.print(f"\n[green]+[/green] Deleted preset: [bold]{preset_id}[/bold]")

    except PresetNotFoundError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except BuiltInModificationError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except FileOperationError as e:
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except (FileNotFoundError, PermissionError, OSError) as e:
        # Catch any remaining OS-level errors (for backward compatibility)
        console.print(format_cli_error(f"Failed to delete preset: {e}"))
        raise click.Abort() from e
    except Exception as e:
        # Catch remaining unexpected errors
        console.print(
            format_cli_error(ErrorMessages.operation_failed("deleting preset", str(e)))
        )
        raise click.Abort() from e


@presets.command("edit")
@click.argument("preset_id")
def presets_edit(preset_id):
    """Edit a preset's TOML file in your default editor.

    Opens the preset's .toml configuration file in your system's default
    text editor (or $EDITOR if set). You can edit the preset's metadata,
    template content, and variables.

    PRESET_ID: Preset ID in format "file_type:preset_name" (e.g., "claude_md:my_backend")

    Examples:

        # Edit a user preset
        claudefig presets edit claude_md:my_preset

        # Edit and customize a preset
        claudefig presets edit settings_json:custom
    """
    import os
    import platform
    import subprocess

    from claudefig.preset_manager import PresetManager
    from claudefig.user_config import get_user_config_dir

    try:
        preset_manager = PresetManager()

        # Check if preset exists
        preset = preset_manager.get_preset(preset_id)
        if not preset:
            console.print(
                format_cli_warning(ErrorMessages.not_found("preset", preset_id))
            )
            return

        # Check if it's a built-in preset
        from claudefig.models import PresetSource

        if preset.source == PresetSource.BUILT_IN:
            console.print(format_cli_error("Cannot edit built-in presets"))
            raise click.Abort() from None

        # Determine preset file path
        if preset.source == PresetSource.USER:
            preset_dir = get_user_config_dir() / "presets"
        else:  # PROJECT
            preset_dir = Path.cwd() / ".claudefig" / "presets"

        preset_file = preset_dir / f"{preset_id.replace(':', '_')}.toml"

        if not preset_file.exists():
            console.print(format_cli_error(f"Preset file not found: {preset_file}"))
            raise click.Abort() from None

        console.print(f"[bold blue]Opening preset file:[/bold blue] {preset_file}\n")

        # Determine editor based on environment and platform
        editor = os.environ.get("EDITOR")

        if editor:
            # Use EDITOR environment variable
            subprocess.run([editor, str(preset_file)], check=True)
        else:
            # Fall back to platform defaults
            system = platform.system()
            if system == "Windows":
                subprocess.run(["notepad", str(preset_file)], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", "-t", str(preset_file)], check=True)
            else:  # Linux and others
                # Try common editors
                for cmd in ["nano", "vim", "vi", "gedit"]:
                    try:
                        subprocess.run([cmd, str(preset_file)], check=True)
                        break
                    except FileNotFoundError:
                        continue
                else:
                    console.print("[yellow]No suitable editor found[/yellow]")
                    console.print(f"\n[dim]Edit manually: {preset_file}[/dim]")
                    return

        console.print("[green]+[/green] Preset file edited")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error opening editor:[/red] {e}")
    except Exception as e:
        console.print(
            format_cli_error(ErrorMessages.operation_failed("editing preset", str(e)))
        )
        raise click.Abort() from e


@main.group()
def templates():
    """Manage global config templates (presets for entire project configs).

    Templates let you save and reuse complete project configurations across
    multiple projects. Save your current project setup as a template, then
    apply it to new projects for consistent configuration.

    Use 'claudefig templates --help' to see all available commands.
    """
    pass


@templates.command("list")
@click.option(
    "--validate",
    is_flag=True,
    help="Include validation status for each template",
)
def templates_list(validate):
    """List all global config templates."""
    from claudefig.config_template_manager import ConfigTemplateManager

    try:
        manager = ConfigTemplateManager()
        templates_list = manager.list_global_presets(include_validation=validate)

        if not templates_list:
            console.print("[yellow]No global templates found[/yellow]")
            console.print(
                f"\n[dim]Templates location: {manager.global_presets_dir}[/dim]"
            )
            return

        console.print(
            f"\n[bold blue]Global Config Templates[/bold blue] ({len(templates_list)})\n"
        )
        console.print(f"[dim]Location: {manager.global_presets_dir}[/dim]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", width=20)
        table.add_column("Description", style="white", width=40)
        table.add_column("Files", style="green", width=8)

        if validate:
            table.add_column("Valid", style="yellow", width=8)

        for template in templates_list:
            row = [
                template["name"],
                template.get("description", "N/A"),
                str(template.get("file_count", 0)),
            ]

            if validate and "validation" in template:
                valid = template["validation"].get("valid", False)
                row.append("[green]Yes[/green]" if valid else "[red]No[/red]")

            table.add_row(*row)

        console.print(table)
        console.print("\n[dim]Use 'claudefig templates show <name>' for details[/dim]")

    except Exception as e:
        console.print(f"[red]Error listing templates:[/red] {e}")
        raise click.Abort() from e


@templates.command("show")
@click.argument("template_name")
def templates_show(template_name):
    """Show details of a global config template.

    TEMPLATE_NAME: Name of the template to display
    """
    from claudefig.config_template_manager import ConfigTemplateManager

    try:
        manager = ConfigTemplateManager()

        # Get template config
        try:
            template_config = manager.get_preset_config(template_name)
        except FileNotFoundError:
            console.print(
                format_cli_warning(ErrorMessages.not_found("template", template_name))
            )
            console.print(
                "\n[dim]Use 'claudefig templates list' to see available templates[/dim]"
            )
            return

        # Get template metadata
        templates_list = manager.list_global_presets()
        template_info = next(
            (t for t in templates_list if t["name"] == template_name), None
        )

        console.print(f"\n[bold blue]Template: {template_name}[/bold blue]\n")

        if template_info:
            console.print(f"Description: {template_info.get('description', 'N/A')}")
            console.print(f"File Count:  {template_info.get('file_count', 0)}")

        console.print("\n[bold]File Instances:[/bold]\n")

        # Display file instances
        files = template_config.get_file_instances()
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

    except Exception as e:
        console.print(f"[red]Error showing template:[/red] {e}")
        raise click.Abort() from e


@templates.command("apply")
@click.argument("template_name")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Project path to apply template to (default: current directory)",
)
def templates_apply(template_name, path):
    """Apply a global template to a project.

    TEMPLATE_NAME: Name of the template to apply
    """
    from claudefig.config_template_manager import ConfigTemplateManager

    repo_path = Path(path).resolve()

    try:
        manager = ConfigTemplateManager()

        console.print(
            f"[bold green]Applying template '{template_name}' to:[/bold green] {repo_path}"
        )

        manager.apply_preset_to_project(template_name, target_path=repo_path)

        console.print(
            f"\n[green]+[/green] Template '{template_name}' applied successfully!"
        )
        console.print(f"[dim]Created: {repo_path / '.claudefig.toml'}[/dim]")

    except TemplateNotFoundError as e:
        console.print(f"[red]Template not found:[/red] {template_name}")
        console.print(
            "\n[dim]Use 'claudefig templates list' to see available templates[/dim]"
        )
        raise click.Abort() from e
    except ConfigFileExistsError as e:
        console.print(
            f"[red]Error:[/red] .claudefig.toml already exists in {repo_path}"
        )
        console.print(
            "[dim]Remove existing config or choose a different directory[/dim]"
        )
        raise click.Abort() from e
    except FileNotFoundError as e:
        # ConfigTemplateManager not yet migrated - catch for backward compatibility
        console.print(f"[red]Template not found:[/red] {template_name}")
        console.print(
            "\n[dim]Use 'claudefig templates list' to see available templates[/dim]"
        )
        raise click.Abort() from e
    except FileExistsError:
        # ConfigTemplateManager not yet migrated - catch for backward compatibility
        console.print(
            f"[red]Error:[/red] .claudefig.toml already exists in {repo_path}"
        )
        console.print(
            "[dim]Remove existing config or choose a different directory[/dim]"
        )
        raise click.Abort() from None
    except Exception as e:
        console.print(f"[red]Error applying template:[/red] {e}")
        raise click.Abort() from e


@templates.command("delete")
@click.argument("template_name")
@click.confirmation_option(prompt="Are you sure you want to delete this template?")
def templates_delete(template_name):
    """Delete a global config template.

    TEMPLATE_NAME: Name of the template to delete
    """
    from claudefig.config_template_manager import ConfigTemplateManager

    try:
        manager = ConfigTemplateManager()

        manager.delete_global_preset(template_name)

        console.print(
            f"[green]+[/green] Deleted template: [cyan]{template_name}[/cyan]"
        )

    except TemplateNotFoundError as e:
        console.print(f"[yellow]Template not found:[/yellow] {template_name}")
        raise click.Abort() from e
    except ValueError as e:
        # Catch validation errors (protected templates, etc.)
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except FileNotFoundError:
        # ConfigTemplateManager not yet migrated - catch for backward compatibility
        console.print(f"[yellow]Template not found:[/yellow] {template_name}")
        raise click.Abort() from None
    except Exception as e:
        console.print(f"[red]Error deleting template:[/red] {e}")
        raise click.Abort() from e


@templates.command("edit")
@click.argument("template_name")
def templates_edit(template_name):
    """Edit a global template's TOML file in your default editor.

    Opens the template's .toml configuration file in your system's default
    text editor (or $EDITOR if set). You can edit the template's metadata
    and file instance configurations.

    TEMPLATE_NAME: Name of the template to edit (e.g., "default", "my_fastapi_project")

    Examples:

        # Edit a template
        claudefig templates edit my_template

        # Edit and customize the default template
        claudefig templates edit default
    """
    import os
    import platform
    import subprocess

    from claudefig.config_template_manager import ConfigTemplateManager

    try:
        manager = ConfigTemplateManager()

        # Check if template exists
        template_file = manager.global_presets_dir / f"{template_name}.toml"

        if not template_file.exists():
            console.print(
                format_cli_warning(ErrorMessages.not_found("template", template_name))
            )
            console.print(
                "\n[dim]Use 'claudefig templates list' to see available templates[/dim]"
            )
            return

        # Check if it's a default template
        if template_name == "default":
            console.print(
                "[yellow]Warning: Editing default template - changes will affect new projects[/yellow]\n"
            )

        console.print(
            f"[bold blue]Opening template file:[/bold blue] {template_file}\n"
        )

        # Determine editor based on environment and platform
        editor = os.environ.get("EDITOR")

        if editor:
            # Use EDITOR environment variable
            subprocess.run([editor, str(template_file)], check=True)
        else:
            # Fall back to platform defaults
            system = platform.system()
            if system == "Windows":
                subprocess.run(["notepad", str(template_file)], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", "-t", str(template_file)], check=True)
            else:  # Linux and others
                # Try common editors
                for cmd in ["nano", "vim", "vi", "gedit"]:
                    try:
                        subprocess.run([cmd, str(template_file)], check=True)
                        break
                    except FileNotFoundError:
                        continue
                else:
                    console.print("[yellow]No suitable editor found[/yellow]")
                    console.print(f"\n[dim]Edit manually: {template_file}[/dim]")
                    return

        console.print("[green]+[/green] Template file edited")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error opening editor:[/red] {e}")
    except Exception as e:
        console.print(
            format_cli_error(ErrorMessages.operation_failed("editing template", str(e)))
        )
        raise click.Abort() from e


@templates.command("save")
@click.argument("template_name")
@click.option(
    "--description",
    default="",
    help="Description of the template",
)
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Project path to save config from (default: current directory)",
)
def templates_save(template_name, description, path):
    """Save current project config as a global template.

    TEMPLATE_NAME: Name for the new template
    """
    from claudefig.config_template_manager import ConfigTemplateManager

    repo_path = Path(path).resolve()

    try:
        # Ensure a config exists in the project
        config_path = repo_path / ".claudefig.toml"
        if not config_path.exists():
            console.print(
                format_cli_error(ErrorMessages.config_file_not_found(str(repo_path)))
            )
            console.print("[dim]Initialize a config first with 'claudefig init'[/dim]")
            raise click.Abort()

        manager = ConfigTemplateManager()

        # Temporarily change to project dir to read its config
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            manager.save_global_preset(template_name, description)
        finally:
            os.chdir(original_cwd)

        console.print(
            f"\n[green]+[/green] Saved template: [cyan]{template_name}[/cyan]"
        )
        console.print(
            f"[dim]Location: {manager.global_presets_dir / (template_name + '.toml')}[/dim]"
        )

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Error saving template:[/red] {e}")
        raise click.Abort() from e


@main.command("setup-mcp")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def setup_mcp(path):
    """Set up MCP servers from .claude/mcp/ directory.

    Runs 'claude mcp add-json' for each JSON file in .claude/mcp/
    """
    repo_path = Path(path).resolve()

    console.print(f"[bold green]Setting up MCP servers in:[/bold green] {repo_path}")

    try:
        initializer = Initializer()
        success = initializer.setup_mcp_servers(repo_path)

        if not success:
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error setting up MCP servers:[/red] {e}")
        raise click.Abort() from e


@main.command()
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing files",
)
def sync(path, force):
    """Regenerate files from current configuration.

    Reads .claudefig.toml and regenerates all enabled file instances.
    This is useful after modifying configuration or updating presets.
    """
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    logger.info(f"Synchronizing files in: {repo_path}")
    logger.debug(f"Force mode: {force}")

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        console.print(
            format_cli_error(ErrorMessages.config_file_not_found(str(repo_path)))
        )
        console.print(
            "[dim]Run 'claudefig init' to initialize configuration first[/dim]"
        )
        raise click.Abort()

    console.print(f"[bold green]Synchronizing files in:[/bold green] {repo_path}")

    if force:
        console.print(
            "[yellow]Force mode enabled - will overwrite existing files[/yellow]"
        )

    try:
        # Initialize with existing config
        initializer = Initializer(config_path=config_path)

        # Regenerate files
        success = initializer.initialize(repo_path, force=force)

        if success:
            logger.info("Files synchronized successfully")
            console.print("\n[green]+[/green] Files synchronized successfully")
        else:
            logger.warning("File synchronization completed with warnings")
            console.print("\n[yellow]![/yellow] Some files failed to synchronize")
            raise click.Abort()

    except FileOperationError as e:
        logger.error(f"File operation failed: {e}", exc_info=True)
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except InitializationRollbackError as e:
        logger.error(f"Synchronization rolled back: {e}", exc_info=True)
        console.print(format_cli_error(str(e)))
        raise click.Abort() from e
    except Exception as e:
        logger.error(f"Synchronization failed: {e}", exc_info=True)
        console.print(
            format_cli_error(
                ErrorMessages.operation_failed("synchronizing files", str(e))
            )
        )
        raise click.Abort() from e


@main.command()
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def validate(path):
    """Validate project configuration and file instances.

    Checks for errors and warnings in the current configuration.
    Shows health status similar to the TUI Overview screen.
    """
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    logger.info(f"Validating configuration in: {repo_path}")

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        console.print(
            format_cli_error(ErrorMessages.config_file_not_found(str(repo_path)))
        )
        console.print(
            "[dim]Run 'claudefig init' to initialize configuration first[/dim]"
        )
        raise click.Abort()

    console.print(f"[bold blue]Validating configuration in:[/bold blue] {repo_path}\n")

    try:
        # Load config
        config_repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(config_repo)

        # Load instances
        instances_data = config_service.get_file_instances(config_data)
        instances_dict, load_errors = file_instance_service.load_instances_from_config(
            instances_data
        )

        # Show load errors
        if load_errors:
            for error in load_errors:
                console.print(f"[red]Load error:[/red] {error}")

        # Get enabled instances
        enabled_instances = file_instance_service.list_instances(
            instances_dict, enabled_only=True
        )

        if not enabled_instances:
            logger.warning("No enabled file instances to validate")
            console.print("[yellow]No enabled file instances to validate[/yellow]")
            return

        logger.debug(f"Validating {len(enabled_instances)} enabled instance(s)")

        # Validate each instance
        total_errors = []
        total_warnings = []

        preset_repo = TomlPresetRepository()
        for instance in enabled_instances:
            result = file_instance_service.validate_instance(
                instance, instances_dict, preset_repo, repo_path, is_update=True
            )

            if result.has_errors:
                total_errors.extend(
                    [f"{instance.id}: {error}" for error in result.errors]
                )
                logger.debug(
                    f"Instance {instance.id} has {len(result.errors)} error(s)"
                )

            if result.has_warnings:
                total_warnings.extend(
                    [f"{instance.id}: {warning}" for warning in result.warnings]
                )
                logger.debug(
                    f"Instance {instance.id} has {len(result.warnings)} warning(s)"
                )

        # Display results
        if total_errors:
            logger.warning(f"Validation found {len(total_errors)} error(s)")
            console.print(f"[red]✗ Found {len(total_errors)} error(s):[/red]\n")
            for error in total_errors:
                console.print(f"  • {error}")
            console.print()

        if total_warnings:
            logger.info(f"Validation found {len(total_warnings)} warning(s)")
            console.print(
                f"[yellow]⚠ Found {len(total_warnings)} warning(s):[/yellow]\n"
            )
            for warning in total_warnings:
                console.print(f"  • {warning}")
            console.print()

        # Overall health
        if total_errors:
            logger.error("Validation failed with errors")
            console.print("[red]Health: ✗ Errors detected[/red]")
            raise click.Abort()
        elif total_warnings:
            logger.info("Validation passed with warnings")
            console.print("[yellow]Health: ⚠ Warnings detected[/yellow]")
        else:
            logger.info("Validation passed - all checks successful")
            console.print("[green]Health: ✓ All validations passed[/green]")

        console.print(
            f"\n[dim]Validated {len(enabled_instances)} enabled instance(s)[/dim]"
        )

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        console.print(
            format_cli_error(ErrorMessages.operation_failed("validation", str(e)))
        )
        raise click.Abort() from e


@main.command()
def interactive():
    """Launch interactive TUI mode."""
    try:
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()
        app.run()
    except ImportError as e:
        console.print(
            "[red]Error:[/red] Textual not installed. "
            "Run: pip install 'claudefig[tui]' or reinstall claudefig"
        )
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Error launching interactive mode:[/red] {e}")
        raise click.Abort() from e


if __name__ == "__main__":
    main()
