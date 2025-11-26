"""File instance management commands.

This module contains commands for managing file instances
(list, show, add, update, remove, reset).
"""

from pathlib import Path

import click

from claudefig.cli.decorators import handle_errors, with_config
from claudefig.cli.types import FILE_TYPE
from claudefig.error_messages import ErrorMessages, format_cli_error, format_cli_warning
from claudefig.logging_config import get_logger
from claudefig.models import FileType
from claudefig.repositories.preset_repository import TomlPresetRepository
from claudefig.services import config_service, file_instance_service

# Import shared console from parent
from .. import console

logger = get_logger("cli.files")


@click.group(name="files")
def files_group():
    """Manage file instances (files to be generated)."""
    pass


@files_group.command("list")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@click.option(
    "--type",
    "file_type",
    type=FILE_TYPE,
    help="Filter by file type (e.g., claude_md, settings_json)",
)
@click.option(
    "--enabled-only",
    is_flag=True,
    help="Show only enabled instances",
)
@with_config()
@handle_errors("listing file instances")
def files_list(
    path, file_type: FileType | None, enabled_only, config_data, config_repo
):
    """List all configured file instances."""

    # Load instances from config
    instances_data = config_service.get_file_instances(config_data)
    instances_dict, load_errors = file_instance_service.load_instances_from_config(
        instances_data
    )

    # Show load errors if any
    if load_errors:
        for error in load_errors:
            console.print(f"[yellow]Warning:[/yellow] {error}")

    # file_type is already validated by FILE_TYPE ParamType (or None if not provided)
    filter_type = file_type

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


@files_group.command("add")
@click.argument("file_type", type=FILE_TYPE)
@click.option(
    "--preset",
    default=None,
    help="Preset name to use",
)
@click.option(
    "--component",
    default=None,
    help="Component name to use (alternative to --preset)",
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
@with_config(path_param="repo_path_arg")
@handle_errors("adding file instance")
def files_add(
    file_type: FileType,
    preset,
    component,
    path_target,
    disabled,
    repo_path_arg,
    config_data,
    config_repo,
):
    """Add a new file instance.

    FILE_TYPE: Type of file (e.g., claude_md, settings_json)

    Use --preset to specify a preset name, or --component to specify a component name.
    If neither is provided, defaults to 'default'.
    """
    from claudefig.models import FileInstance
    from claudefig.template_manager import FileTemplateManager

    # Validate preset and component options
    if preset and component:
        console.print(format_cli_error("Cannot specify both --preset and --component"))
        raise click.Abort()

    # Determine which name to use
    if component:
        preset_name = component
    elif preset:
        preset_name = preset
    else:
        preset_name = "default"

    # file_type is already validated by FILE_TYPE ParamType
    file_type_enum = file_type

    # If component was specified, verify it exists
    if component:
        manager = FileTemplateManager()
        components = manager.list_components("default", type=file_type_enum.value)
        component_exists = any(
            c["name"] == component and c["type"] == file_type_enum.value
            for c in components
        )

        if not component_exists:
            console.print(
                format_cli_error(
                    f"Component '{component}' not found for type '{file_type_enum.value}'"
                )
            )
            console.print(
                f"\n[dim]Use 'claudefig components list {file_type_enum.value}' to see available components[/dim]"
            )
            raise click.Abort()

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
        file_type_enum, preset_name, path_target, instances_dict
    )

    # Build preset ID
    preset_id = f"{file_type_enum.value}:{preset_name}"

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
    repo_path = Path(repo_path_arg).resolve()
    preset_repo = TomlPresetRepository()
    result = file_instance_service.add_instance(
        instances_dict, instance, preset_repo, repo_path
    )

    if not result.valid:
        console.print("[red]Validation failed:[/red]")
        for error in result.errors:
            console.print(f"  - {error}")
        raise click.Abort()

    if result.has_warnings:
        console.print("[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  - {warning}")

    # Save instances back to config
    updated_instances_data = file_instance_service.save_instances_to_config(
        instances_dict
    )
    config_service.set_file_instances(config_data, updated_instances_data)
    config_service.save_config(config_data, config_repo)

    console.print(f"\n[green]+[/green] Added file instance: [cyan]{instance.id}[/cyan]")
    console.print(f"  Type: {instance.type.display_name}")
    console.print(f"  Preset: {instance.preset}")
    console.print(f"  Path: {instance.path}")
    console.print(f"  Enabled: {instance.enabled}")
    console.print(f"\n[dim]Config saved to: {config_repo.get_path()}[/dim]")


@files_group.command("remove")
@click.argument("instance_id")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@with_config()
@handle_errors("removing file instance")
def files_remove(instance_id, path, config_data, config_repo):
    """Remove a file instance.

    INSTANCE_ID: ID of the instance to remove
    """
    # Load instances
    instances_data = config_service.get_file_instances(config_data)
    instances_dict, _ = file_instance_service.load_instances_from_config(instances_data)

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
        console.print(f"[dim]Config saved to: {config_repo.get_path()}[/dim]")
    else:
        console.print(
            format_cli_warning(ErrorMessages.not_found("file instance", instance_id))
        )


@files_group.command("enable")
@click.argument("instance_id")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@with_config()
@handle_errors("enabling file instance")
def files_enable(instance_id, path, config_data, config_repo):
    """Enable a file instance.

    INSTANCE_ID: ID of the instance to enable
    """
    # Load instances
    instances_data = config_service.get_file_instances(config_data)
    instances_dict, _ = file_instance_service.load_instances_from_config(instances_data)

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
        console.print(f"[dim]Config saved to: {config_repo.get_path()}[/dim]")
    else:
        console.print(
            format_cli_warning(ErrorMessages.not_found("file instance", instance_id))
        )


@files_group.command("disable")
@click.argument("instance_id")
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Repository path (default: current directory)",
)
@with_config()
@handle_errors("disabling file instance")
def files_disable(instance_id, path, config_data, config_repo):
    """Disable a file instance.

    INSTANCE_ID: ID of the instance to disable
    """
    # Load instances
    instances_data = config_service.get_file_instances(config_data)
    instances_dict, _ = file_instance_service.load_instances_from_config(instances_data)

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
        console.print(f"[dim]Config saved to: {config_repo.get_path()}[/dim]")
    else:
        console.print(
            format_cli_warning(ErrorMessages.not_found("file instance", instance_id))
        )


@files_group.command("edit")
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
@with_config(path_param="repo_path_arg")
@handle_errors("editing file instance")
def files_edit(
    instance_id, preset, path_target, enable, repo_path_arg, config_data, config_repo
):
    """Edit an existing file instance.

    INSTANCE_ID: ID of the instance to edit
    """
    repo_path = Path(repo_path_arg).resolve()

    # Load instances
    instances_data = config_service.get_file_instances(config_data)
    instances_dict, _ = file_instance_service.load_instances_from_config(instances_data)

    # Get existing instance
    instance = file_instance_service.get_instance(instances_dict, instance_id)
    if not instance:
        console.print(
            format_cli_warning(ErrorMessages.not_found("file instance", instance_id))
        )
        raise click.Abort()

    # Track changes
    changes = []

    # Update preset if provided
    if preset:
        old_preset = instance.preset
        instance.preset = f"{instance.type.value}:{preset}"
        changes.append(f"preset: {old_preset} -> {instance.preset}")

    # Update path if provided
    if path_target:
        old_path = instance.path
        instance.path = path_target
        changes.append(f"path: {old_path} -> {instance.path}")

    # Update enabled state if provided
    if enable is not None:
        old_enabled = instance.enabled
        instance.enabled = enable
        status = "enabled" if enable else "disabled"
        old_status = "enabled" if old_enabled else "disabled"
        changes.append(f"status: {old_status} -> {status}")

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
            console.print(f"  - {error}")
        raise click.Abort()

    if result.has_warnings:
        console.print("[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  - {warning}")

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
    console.print(f"\n[dim]Config saved to: {config_repo.get_path()}[/dim]")
