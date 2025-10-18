"""User-level configuration and directory management."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

console = Console()


def get_user_config_dir() -> Path:
    """Get user-level config directory (cross-platform).

    Returns:
        Path to ~/.claudefig/ directory.
    """
    return Path.home() / ".claudefig"


def get_template_dir() -> Path:
    """Get user-level template directory.

    Returns:
        Path to ~/.claudefig/templates/ directory.
    """
    return get_user_config_dir() / "templates"


def get_cache_dir() -> Path:
    """Get user-level cache directory.

    Returns:
        Path to ~/.claudefig/cache/ directory.
    """
    return get_user_config_dir() / "cache"


def get_components_dir() -> Path:
    """Get user-level components directory.

    Returns:
        Path to ~/.claudefig/components/ directory.
    """
    return get_user_config_dir() / "components"


def get_user_config_file() -> Path:
    """Get user-level config file path.

    Returns:
        Path to ~/.claudefig/config.toml file.
    """
    return get_user_config_dir() / "config.toml"


def is_initialized() -> bool:
    """Check if user-level claudefig directory is initialized.

    Returns:
        True if ~/.claudefig/ exists and has basic structure, False otherwise.
    """
    config_dir = get_user_config_dir()
    return (
        config_dir.exists()
        and (config_dir / "presets").exists()
        and (config_dir / "components").exists()
    )


def ensure_user_config(verbose: bool = True) -> Path:
    """Create ~/.claudefig/ if it doesn't exist (lazy initialization).

    Args:
        verbose: Whether to print initialization messages.

    Returns:
        Path to user config directory.
    """
    config_dir = get_user_config_dir()

    if not is_initialized():
        if verbose:
            console.print(
                "[green]First run detected - initializing claudefig...[/green]"
            )
        initialize_user_directory(config_dir, verbose=verbose)

    return config_dir


def initialize_user_directory(config_dir: Path, verbose: bool = True) -> None:
    """Set up default directory structure.

    Args:
        config_dir: Path to user config directory to initialize.
        verbose: Whether to print progress messages.
    """
    try:
        # Create directory structure
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "presets").mkdir(parents=True, exist_ok=True)
        (config_dir / "templates").mkdir(parents=True, exist_ok=True)
        (config_dir / "cache").mkdir(parents=True, exist_ok=True)

        # Create components directory with subdirectories for each file type
        components_dir = config_dir / "components"
        components_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for each file type component
        component_types = [
            "claude_md",
            "gitignore",
            "commands",
            "agents",
            "hooks",
            "output_styles",
            "mcp",
        ]
        for component_type in component_types:
            (components_dir / component_type).mkdir(parents=True, exist_ok=True)

        if verbose:
            console.print(f"[green]+[/green] Created directory: {config_dir}")

        # Create default user config file
        create_default_user_config(config_dir / "config.toml", verbose=verbose)

        if verbose:
            console.print(
                "\n[bold green]User configuration initialized successfully![/bold green]"
            )
            console.print(f"Location: {config_dir}")

    except Exception as e:
        console.print(f"[red]Error initializing user directory:[/red] {e}")
        raise


def create_default_user_config(config_path: Path, verbose: bool = True) -> None:
    """Create default user-level config file.

    Args:
        config_path: Path to config.toml file to create.
        verbose: Whether to print progress messages.
    """
    if config_path.exists():
        return

    default_config = """# claudefig user-level configuration

[user]
# Default template to use when initializing projects
default_template = "default"

# Whether to use interactive mode by default
prefer_interactive = true

[ui]
# Theme for TUI (dark, light, auto)
theme = "auto"

# Show hints and tips
show_hints = true
"""

    try:
        config_path.write_text(default_config, encoding="utf-8")
        if verbose:
            console.print(f"[green]+[/green] Created config: {config_path}")
    except Exception as e:
        console.print(f"[red]Error creating user config:[/red] {e}")
        raise


def reset_user_config(force: bool = False) -> bool:
    """Reset user-level configuration (dangerous operation).

    Args:
        force: If True, don't prompt for confirmation.

    Returns:
        True if reset was successful, False if cancelled.
    """
    config_dir = get_user_config_dir()

    if not config_dir.exists():
        console.print("[yellow]No user configuration to reset[/yellow]")
        return False

    if not force:
        console.print(
            f"[yellow]Warning:[/yellow] This will delete {config_dir} and all custom configuration!"
        )
        response = console.input("Are you sure? Type 'yes' to confirm: ")
        if response.lower() != "yes":
            console.print("[yellow]Reset cancelled[/yellow]")
            return False

    try:
        shutil.rmtree(config_dir)
        console.print("[green]User configuration reset successfully[/green]")
        console.print("Run claudefig again to reinitialize with defaults")
        return True
    except Exception as e:
        console.print(f"[red]Error resetting configuration:[/red] {e}")
        return False
