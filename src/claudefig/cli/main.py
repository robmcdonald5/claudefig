"""Main CLI commands for claudefig.

This module contains the main Click group and core commands that don't fit into
specific command groups (init, show, sync, validate, interactive, etc.).
"""

import logging
from pathlib import Path

import click
from rich.table import Table

from claudefig import __version__
from claudefig.error_messages import (
    ErrorMessages,
    format_cli_error,
)
from claudefig.exceptions import (
    ConfigFileNotFoundError,
    FileOperationError,
    InitializationRollbackError,
)
from claudefig.initializer import Initializer
from claudefig.logging_config import get_logger, setup_logging
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.repositories.preset_repository import TomlPresetRepository
from claudefig.services import config_service, file_instance_service

# Import shared console from parent
from . import console

logger = get_logger("cli.main")


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
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Skip interactive prompts (for scripting/testing)",
)
def init(path, force, non_interactive):
    """Initialize Claude Code configuration in a repository.

    Creates necessary files and directory structure for Claude Code integration:
    - .claude/ directory
    - CLAUDE.md configuration file
    - Optional settings.json
    - claudefig.toml configuration
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
        success = initializer.initialize(
            repo_path, force=force, skip_prompts=non_interactive
        )

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
            repo = TomlConfigRepository(Path.cwd() / "claudefig.toml")

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


@main.command("setup-mcp")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def setup_mcp(path):
    """Set up MCP servers from configuration files.

    Supports two configuration patterns:
    \b
    1. Standard .mcp.json in project root
    2. Multiple .json files in .claude/mcp/ directory

    Runs 'claude mcp add-json' for each server configuration.

    Transport types supported:
    \b
    - STDIO: Local command-line tools (npx packages)
    - HTTP: Remote cloud services (OAuth 2.1 or API keys)
    - SSE: Server-Sent Events (deprecated)

    Validates:
    \b
    - JSON syntax
    - Transport type requirements
    - Security best practices (warns about hardcoded credentials)

    See docs/ADDING_NEW_COMPONENTS.md and docs/MCP_SECURITY_GUIDE.md
    for detailed setup instructions and security guidelines.
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

    Reads claudefig.toml and regenerates all enabled file instances.
    This is useful after modifying configuration or updating presets.
    """
    repo_path = Path(path).resolve()
    config_path = repo_path / "claudefig.toml"

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
    config_path = repo_path / "claudefig.toml"

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
            console.print(f"[red]X Found {len(total_errors)} error(s):[/red]\n")
            for error in total_errors:
                console.print(f"  - {error}")
            console.print()

        if total_warnings:
            logger.info(f"Validation found {len(total_warnings)} warning(s)")
            console.print(
                f"[yellow]! Found {len(total_warnings)} warning(s):[/yellow]\n"
            )
            for warning in total_warnings:
                console.print(f"  - {warning}")
            console.print()

        # Overall health
        if total_errors:
            logger.error("Validation failed with errors")
            console.print("[red]Health: X Errors detected[/red]")
            raise click.Abort()
        elif total_warnings:
            logger.info("Validation passed with warnings")
            console.print("[yellow]Health: ! Warnings detected[/yellow]")
        else:
            logger.info("Validation passed - all checks successful")
            console.print("[green]Health: OK All validations passed[/green]")

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
