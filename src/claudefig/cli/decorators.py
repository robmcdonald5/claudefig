"""Decorators for reducing CLI boilerplate.

This module provides reusable decorators that eliminate repetitive patterns
in CLI commands, such as config loading, error handling, and validation.
"""

import functools
from collections.abc import Callable
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from claudefig.error_messages import ErrorMessages, format_cli_error
from claudefig.exceptions import ConfigFileNotFoundError
from claudefig.logging_config import get_logger
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.services import config_service
from claudefig.utils.paths import is_git_repository

console = Console()
logger = get_logger("cli.decorators")


def _normalize_config_path(path: str | Path | None) -> Path:
    """Normalize path to absolute claudefig.toml path.

    Args:
        path: Path to normalize (can be str, Path, or None)

    Returns:
        Absolute path to claudefig.toml file
    """
    if path is None:
        path = Path.cwd()

    if isinstance(path, str):
        path = Path(path)

    # If directory, append claudefig.toml
    if path.is_dir():
        path = path / "claudefig.toml"

    return path.resolve()


def with_config(
    path_param: str = "path",
    config_name: str = "config_data",
    repo_name: str = "config_repo",
):
    """Decorator that automatically loads config and injects it into the command.

    This eliminates the repeated pattern of:
        repo = TomlConfigRepository(config_path)
        config_data = config_service.load_config(repo)

    The config_service.load_config() automatically returns defaults if the file
    doesn't exist, so missing configs are handled gracefully.

    Args:
        path_param: Name of the Click parameter containing the config path (default: "path")
        config_name: Name to use for injected config_data parameter (default: "config_data")
        repo_name: Name to use for injected config_repo parameter (default: "config_repo")

    Usage:
        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config(path_param="path")
        def my_command(path, config_data, config_repo):
            # config_data and config_repo are automatically loaded
            # config_data contains defaults if file doesn't exist
            value = config_service.get_value(config_data, "some.key")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract and normalize the path
            config_path = _normalize_config_path(kwargs.get(path_param, "."))

            # Create repository
            repo = TomlConfigRepository(config_path)

            # Load config (service returns defaults if file doesn't exist)
            config_data = config_service.load_config(repo)

            # Inject config into kwargs
            kwargs[config_name] = config_data
            kwargs[repo_name] = repo

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def handle_errors(
    operation_name: str, extra_handlers: dict[type, Callable] | None = None
):
    """Decorator that wraps command in standardized error handling.

    This eliminates the repeated pattern of:
        try:
            # command logic
        except SpecificException as e:
            console.print(format_cli_error(str(e)))
            raise click.Abort() from e
        except Exception as e:
            console.print(format_cli_error(...))
            raise click.Abort() from e

    Args:
        operation_name: Name of the operation for error messages (e.g., "adding file instance")
        extra_handlers: Optional dict mapping exception types to handler functions.
                       Handler functions receive the exception and should print error messages.
                       If handler returns True, error handling stops (no click.Abort).
                       If handler returns False or None, default behavior continues.

    Usage:
        @click.command()
        @handle_errors("adding file instance")
        def add_file(file_type, path):
            # If any exception occurs, automatically formatted and aborted
            instance = create_instance(file_type, path)
            save_instance(instance)

    Example with custom handlers:
        @click.command()
        @handle_errors(
            "deleting preset",
            extra_handlers={
                PresetNotFoundError: lambda e: console.print(f"[yellow]{e}[/yellow]"),
                BuiltInModificationError: lambda e: console.print(f"[red]{e}[/red]"),
            }
        )
        def delete_preset(name):
            # Custom error messages for specific exceptions
            preset_manager.delete(name)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except ConfigFileNotFoundError as e:
                logger.error(f"{operation_name} failed: {e}", exc_info=True)
                console.print(format_cli_error(str(e)))
                raise click.Abort() from e
            except Exception as e:
                # Check for custom handlers
                if extra_handlers:
                    exception_type = type(e)
                    if exception_type in extra_handlers:
                        handler = extra_handlers[exception_type]
                        result = handler(e)
                        if result:  # Handler handled it completely
                            return  # Don't abort - handler dealt with it
                        # If handler returned False/None, continue to default handling

                # Default error handling
                logger.error(f"{operation_name} failed: {e}", exc_info=True)
                console.print(
                    format_cli_error(
                        ErrorMessages.operation_failed(operation_name, str(e))
                    )
                )
                raise click.Abort() from e

        return wrapper

    return decorator


def require_git_repo(path_param: str = "path"):
    """Decorator that ensures command is run within a git repository.

    Args:
        path_param: Name of the Click parameter containing the directory path (default: "path")

    Usage:
        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @require_git_repo(path_param="path")
        def git_command(path):
            # Guaranteed to be in a git repo
            # perform git operations
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract the path from kwargs
            repo_path = kwargs.get(path_param, Path.cwd())
            if isinstance(repo_path, str):
                repo_path = Path(repo_path)

            # Check if directory is a git repository
            if not is_git_repository(repo_path):
                console.print(
                    format_cli_error(
                        "Not a git repository. Initialize git first with 'git init'"
                    )
                )
                raise click.Abort()

            return func(*args, **kwargs)

        return wrapper

    return decorator


def with_config_optional(
    path_param: str = "path",
    config_name: str = "config_data",
    repo_name: str = "config_repo",
    default_message: str | None = None,
):
    """Decorator that loads config if available, or uses defaults with optional message.

    Similar to @with_config but doesn't fail if config is missing - uses defaults instead.

    Args:
        path_param: Name of the Click parameter containing the config path (default: "path")
        config_name: Name to use for injected config_data parameter (default: "config_data")
        repo_name: Name to use for injected config_repo parameter (default: "repo_name")
        default_message: Optional message to display when using defaults

    Usage:
        @click.command()
        @with_config_optional(default_message="Using default configuration")
        def show_config(path, config_data, config_repo):
            # config_data contains defaults if no config file exists
            # config_repo is still available for saving
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract and normalize the path
            config_path = _normalize_config_path(kwargs.get(path_param))

            # Create repository
            repo = TomlConfigRepository(config_path)

            # Load config (uses defaults if missing)
            config_data = config_service.load_config(repo)

            # Display message if using defaults and config doesn't exist
            if not repo.exists() and default_message:
                console.print(f"[yellow]{default_message}[/yellow]")

            # Inject config into kwargs
            kwargs[config_name] = config_data
            kwargs[repo_name] = repo

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator
