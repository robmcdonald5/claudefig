"""User-level configuration and directory management."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

console = Console()


def get_user_config_dir() -> Path:
    """Get user-level config directory.

    Uses ~/.claudefig/ on all platforms:
    - Windows: C:\\Users\\{user}\\.claudefig\\
    - macOS: ~/.claudefig/
    - Linux: ~/.claudefig/

    Returns:
        Path to user config directory.
    """
    return Path.home() / ".claudefig"


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


def is_initialized(auto_heal: bool = True) -> bool:
    """Check if user-level claudefig directory is properly initialized.

    Validates existence of all critical directories and files, and optionally
    performs auto-healing to repair missing structure.

    Args:
        auto_heal: If True, automatically repair missing directories and files.

    Returns:
        True if all critical structure exists or was repaired, False otherwise.
    """
    from claudefig.services.structure_validator import (
        validate_preset_integrity,
        validate_user_directory,
    )

    config_dir = get_user_config_dir()

    # Check main directory
    if not config_dir.exists():
        if auto_heal:
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                return False
        else:
            return False

    # Validate and optionally repair directory structure
    validation_result = validate_user_directory(
        config_dir, auto_heal=auto_heal, verbose=False
    )

    # Check critical files
    if not (config_dir / "config.toml").exists() and not auto_heal:
        # Config file missing but will be created by ensure_user_config
        return False

    # Validate default preset integrity
    default_preset_dir = config_dir / "presets" / "default"
    if default_preset_dir.exists():
        preset_validation = validate_preset_integrity(default_preset_dir, verbose=False)
        if not preset_validation.is_valid and not auto_heal:
            # Preset exists but is incomplete
            return False
            # If auto-heal is on, it will be repaired by _copy_default_preset_to_user

    # Return true if structure is valid or was successfully repaired
    return validation_result.is_valid or (auto_heal and not validation_result.errors)


def ensure_user_config(verbose: bool = True) -> Path:
    """Create ~/.claudefig/ if it doesn't exist (lazy initialization).

    Performs auto-healing if structure is incomplete or damaged.

    Args:
        verbose: Whether to print initialization messages.

    Returns:
        Path to user config directory.
    """
    from claudefig.services.structure_validator import validate_user_directory

    config_dir = get_user_config_dir()

    # Check if initialization is needed (with auto-heal disabled for detection)
    was_initialized = is_initialized(auto_heal=False)

    if not was_initialized:
        # First run or structure is missing
        if verbose:
            if not config_dir.exists():
                console.print(
                    "[green]First run detected - initializing claudefig...[/green]"
                )
            else:
                console.print("[yellow]Repairing user configuration...[/yellow]")

        # Initialize with auto-heal enabled
        initialize_user_directory(config_dir, verbose=verbose)
    else:
        # Already initialized, but run validation with auto-heal for safety
        validation_result = validate_user_directory(
            config_dir, auto_heal=True, verbose=verbose
        )

        # Check if presets need to be populated (auto-heal for presets)
        presets_dir = config_dir / "presets"
        if presets_dir.exists():
            # Check if default preset exists and is complete
            from claudefig.services.structure_validator import validate_preset_integrity

            default_preset_dir = presets_dir / "default"
            if not default_preset_dir.exists():
                # Default preset missing entirely - copy it
                if verbose:
                    console.print(
                        "[yellow]Default preset missing, restoring...[/yellow]"
                    )
                _copy_default_preset_to_user(presets_dir, verbose=verbose)
            else:
                # Check integrity of existing preset
                preset_validation = validate_preset_integrity(
                    default_preset_dir, verbose=False
                )
                if not preset_validation.is_valid:
                    # Preset exists but is incomplete - re-copy
                    if verbose:
                        console.print(
                            "[yellow]Default preset incomplete, repairing...[/yellow]"
                        )
                    _copy_default_preset_to_user(presets_dir, verbose=verbose)

        # Report any repairs that were made
        if validation_result.was_repaired and verbose:
            console.print("[green]✓[/green] Configuration repaired successfully")

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
            "settings_json",
            "settings_local_json",
            "statusline",
        ]
        for component_type in component_types:
            (components_dir / component_type).mkdir(parents=True, exist_ok=True)

        if verbose:
            console.print(f"[green]+[/green] Created directory: {config_dir}")

        # Create default user config file
        create_default_user_config(config_dir / "config.toml", verbose=verbose)

        # Populate presets directory with library presets
        _ensure_presets_populated(config_dir / "presets", verbose=verbose)

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


def _ensure_presets_populated(presets_dir: Path, verbose: bool = True) -> None:
    """Populate presets directory with library presets if empty.

    Args:
        presets_dir: Path to presets directory.
        verbose: Whether to print progress messages.
    """
    try:
        # Copy the default preset from built-in library to user directory
        _copy_default_preset_to_user(presets_dir, verbose=verbose)

    except Exception as e:
        # Non-fatal - presets will be created on first use
        if verbose:
            console.print(f"[yellow]Warning:[/yellow] Could not populate presets: {e}")


def _copy_default_preset_to_user(presets_dir: Path, verbose: bool = True) -> None:
    """Copy the default preset from built-in library to user directory.

    Args:
        presets_dir: Path to user presets directory.
        verbose: Whether to print progress messages.
    """
    from importlib.resources import files

    from claudefig.services.structure_validator import validate_preset_integrity

    # Destination: ~/.claudefig/presets/default/
    dest_dir = presets_dir / "default"

    # Check if preset already exists and is complete
    if dest_dir.exists():
        # Validate integrity instead of just checking for .claudefig.toml
        validation_result = validate_preset_integrity(dest_dir, verbose=False)
        if validation_result.is_valid:
            if verbose:
                console.print(
                    f"[blue]i[/blue] Default preset already exists: {dest_dir}"
                )
            return
        else:
            # Preset exists but is incomplete
            if verbose:
                console.print(
                    "[yellow]Warning:[/yellow] Default preset incomplete, re-copying..."
                )

    try:
        # Source: src/presets/default/
        builtin_source = files("claudefig").joinpath("../presets/default")

        # Get the actual path (resolve traversable to Path)
        if hasattr(builtin_source, "__fspath__"):
            source_path = Path(builtin_source)  # type: ignore[arg-type]
        else:
            # For Python 3.10+, extract path as string
            source_path = Path(str(builtin_source))

        if not source_path.exists():
            if verbose:
                console.print(
                    f"[yellow]Warning:[/yellow] Built-in preset not found at {source_path}"
                )
            return

        # Copy the entire default preset directory
        shutil.copytree(source_path, dest_dir, dirs_exist_ok=True)

        if verbose:
            console.print(f"[green]+[/green] Copied default preset to {dest_dir}")

        # Verify the copy was successful
        validation_result = validate_preset_integrity(dest_dir, verbose=False)
        if validation_result.is_valid:
            if verbose:
                # Count components for feedback
                import sys

                if sys.version_info >= (3, 11):
                    import tomllib
                else:
                    import tomli as tomllib

                try:
                    with open(dest_dir / ".claudefig.toml", "rb") as f:
                        config = tomllib.load(f)
                    components = config.get("components", {})
                    total_variants = sum(
                        len(c.get("variants", []))
                        for c in components.values()
                        if isinstance(c, dict)
                    )
                    console.print(
                        f"[green]✓[/green] Verified preset integrity ({total_variants} components)"
                    )
                except Exception:
                    pass  # Silent fail on verification feedback
        else:
            # Copy succeeded but validation failed
            if verbose:
                console.print(
                    "[yellow]Warning:[/yellow] Preset copied but validation failed"
                )
                for error in validation_result.errors:
                    console.print(f"  - {error}")

    except Exception as e:
        if verbose:
            console.print(
                f"[yellow]Warning:[/yellow] Could not copy default preset: {e}"
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
