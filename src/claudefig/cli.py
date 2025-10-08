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
    ensure_user_config(verbose=True)

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
        table.add_row("Update .gitignore", str(config.get("init.create_gitignore_entries")))

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
        cfg = Config(config_path=config_path if config_path.exists() else None)
        value = cfg.get(key)

        if value is None:
            console.print(f"[yellow]Key not found:[/yellow] {key}")
            console.print("[dim]Use 'claudefig config list' to see all settings[/dim]")
        else:
            console.print(f"[cyan]{key}:[/cyan] {value}")

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
        cfg = Config(config_path=config_path if config_path.exists() else None)

        # Parse value
        parsed_value = value
        if value.lower() in ("true", "false"):
            parsed_value = value.lower() == "true"
        elif value.isdigit():
            parsed_value = int(value)

        # Set value
        cfg.set(key, parsed_value)

        # Save to config file
        cfg.save(config_path)

        console.print(f"[green]+[/green] Set [cyan]{key}[/cyan] = {parsed_value}")
        console.print(f"[dim]Config saved to: {config_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Error setting config:[/red] {e}")
        raise click.Abort() from e


@config.command("list")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
def config_list(path):
    """List all configuration settings."""
    repo_path = Path(path).resolve()
    config_path = repo_path / ".claudefig.toml"

    try:
        cfg = Config(config_path=config_path if config_path.exists() else None)

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
        table.add_row("  version", str(cfg.get("claudefig.version")))
        table.add_row("  template_source", cfg.get("claudefig.template_source"))

        # Init section
        table.add_row("[bold]Init[/bold]", "")
        table.add_row("  create_claude_md", str(cfg.get("init.create_claude_md")))
        table.add_row(
            "  create_gitignore_entries", str(cfg.get("init.create_gitignore_entries"))
        )

        # Claude section
        table.add_row("[bold]Claude Directory[/bold]", "")
        table.add_row("  create_settings", str(cfg.get("claude.create_settings")))
        table.add_row(
            "  create_settings_local", str(cfg.get("claude.create_settings_local"))
        )
        table.add_row("  create_commands", str(cfg.get("claude.create_commands")))
        table.add_row("  create_agents", str(cfg.get("claude.create_agents")))
        table.add_row("  create_hooks", str(cfg.get("claude.create_hooks")))
        table.add_row(
            "  create_output_styles", str(cfg.get("claude.create_output_styles"))
        )
        table.add_row("  create_statusline", str(cfg.get("claude.create_statusline")))
        table.add_row("  create_mcp", str(cfg.get("claude.create_mcp")))

        # Custom section
        custom_dir = cfg.get("custom.template_dir")
        if custom_dir:
            table.add_row("[bold]Custom[/bold]", "")
            table.add_row("  template_dir", custom_dir)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing config:[/red] {e}")
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

    console.print(
        f"[bold green]Setting up MCP servers in:[/bold green] {repo_path}"
    )

    try:
        config = Config()
        initializer = Initializer(config)
        success = initializer.setup_mcp_servers(repo_path)

        if not success:
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error setting up MCP servers:[/red] {e}")
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
