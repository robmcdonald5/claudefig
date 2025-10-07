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


def get_component_dir() -> Path:
    """Get user-level component library directory.

    Returns:
        Path to ~/.claudefig/components/ directory.
    """
    return get_user_config_dir() / "components"


def get_template_dir() -> Path:
    """Get user-level template directory.

    Returns:
        Path to ~/.claudefig/templates/ directory.
    """
    return get_user_config_dir() / "templates"


def get_cache_dir() -> Path:
    """Get user-level cache directory for downloaded components.

    Returns:
        Path to ~/.claudefig/cache/ directory.
    """
    return get_user_config_dir() / "cache"


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
    return config_dir.exists() and (config_dir / "components").exists()


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


def initialize_user_directory(config_dir: Path, verbose: bool = True):
    """Set up default directory structure and components.

    Args:
        config_dir: Path to user config directory to initialize.
        verbose: Whether to print progress messages.
    """
    try:
        # Create directory structure
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "components" / "general").mkdir(parents=True, exist_ok=True)
        (config_dir / "components" / "languages").mkdir(parents=True, exist_ok=True)
        (config_dir / "components" / "frameworks").mkdir(parents=True, exist_ok=True)
        (config_dir / "components" / "tools").mkdir(parents=True, exist_ok=True)
        (config_dir / "components" / "domains").mkdir(parents=True, exist_ok=True)
        (config_dir / "templates").mkdir(parents=True, exist_ok=True)
        (config_dir / "cache").mkdir(parents=True, exist_ok=True)

        if verbose:
            console.print(f"[green]+[/green] Created directory: {config_dir}")

        # Create default user config file
        create_default_user_config(config_dir / "config.toml", verbose=verbose)

        # Copy default components from package data
        copy_default_components(config_dir, verbose=verbose)

        if verbose:
            console.print(
                "\n[bold green]User configuration initialized successfully![/bold green]"
            )
            console.print(f"Location: {config_dir}")

    except Exception as e:
        console.print(f"[red]Error initializing user directory:[/red] {e}")
        raise


def create_default_user_config(config_path: Path, verbose: bool = True):
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

[components]
# Auto-update components on init
auto_update = false

# Component sources (for future remote component support)
sources = []

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


def copy_default_components(config_dir: Path, verbose: bool = True):
    """Copy bundled default components to user directory.

    Args:
        config_dir: Path to user config directory.
        verbose: Whether to print progress messages.
    """
    from importlib.resources import files

    try:
        # Get the default components from package data
        source = files("claudefig_data").joinpath("default_components")
        dest = config_dir / "components"

        # Copy each category directory
        for category in ["general", "languages", "frameworks"]:
            category_source = source.joinpath(category)
            category_dest = dest / category

            # Check if source category exists and has content
            try:
                # List components in this category
                for component_dir in category_source.iterdir():
                    if component_dir.is_dir():
                        component_name = component_dir.name
                        component_dest = category_dest / component_name

                        # Copy the entire component directory
                        shutil.copytree(
                            str(component_dir),
                            component_dest,
                            dirs_exist_ok=True
                        )

                        if verbose:
                            console.print(
                                f"[green]+[/green] Installed component: {category}/{component_name}"
                            )
            except (AttributeError, FileNotFoundError):
                # Category doesn't exist or is empty, skip it
                if verbose:
                    console.print(
                        f"[yellow]![/yellow] No default components found for {category}"
                    )

    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not copy default components:[/yellow] {e}"
        )


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
            f"[yellow]Warning:[/yellow] This will delete {config_dir} and all custom components!"
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
