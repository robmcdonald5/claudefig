"""CLI interface for claudefig."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from claudefig import __version__
from claudefig.config import Config
from claudefig.initializer import Initializer
from claudefig.template_manager import TemplateManager

console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="claudefig")
@click.pass_context
def main(ctx):
    """Universal config CLI tool for setting up Claude Code repositories.

    claudefig helps you initialize and manage Claude Code configurations
    with templates, settings, and best practices.

    Run without arguments to launch interactive mode.
    """
    from claudefig.user_config import ensure_user_config

    # Initialize user config on any command
    ensure_user_config(verbose=False)

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

    console.print(
        f"[bold green]Initializing Claude Code configuration in:[/bold green] {repo_path}"
    )

    if force:
        console.print(
            "[yellow]Force mode enabled - will overwrite existing files[/yellow]"
        )

    try:
        config = Config()
        initializer = Initializer(config)
        success = initializer.initialize(repo_path, force=force)

        if not success:
            raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error during initialization:[/red] {e}")
        raise click.Abort() from e


@main.command()
def show():
    """Show current Claude Code configuration."""
    console.print("[bold blue]Current Configuration:[/bold blue]\n")

    try:
        config = Config()

        if config.config_path:
            console.print(f"[green]Config file:[/green] {config.config_path}\n")
        else:
            console.print("[yellow]No config file found (using defaults)[/yellow]\n")

        # Create a table to display config
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", width=30)
        table.add_column("Value", style="green")

        table.add_row("Template Source", config.get("claudefig.template_source"))
        table.add_row("Create CLAUDE.md", str(config.get("init.create_claude_md")))
        table.add_row("Create Settings", str(config.get("init.create_settings")))

        custom_dir = config.get("custom.template_dir")
        if custom_dir:
            table.add_row("Custom Template Dir", custom_dir)

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {e}")


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
        config = Config()
        custom_dir = config.get("custom.template_dir")
        template_manager = TemplateManager(Path(custom_dir) if custom_dir else None)

        templates = template_manager.list_templates()

        if not templates:
            console.print("[yellow]No templates found[/yellow]")
            return

        for template in templates:
            console.print(f"  • {template}")

    except Exception as e:
        console.print(f"[red]Error listing templates:[/red] {e}")


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
