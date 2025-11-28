"""Component management commands.

This module contains commands for discovering and managing components
(list, show, open, edit).
"""

import sys
from pathlib import Path

import click

from claudefig.cli.decorators import handle_errors
from claudefig.cli.handlers import handle_editor_error
from claudefig.cli.types import FILE_TYPE
from claudefig.error_messages import ErrorMessages, format_cli_error, format_cli_warning
from claudefig.logging_config import get_logger
from claudefig.models import FileType
from claudefig.template_manager import FileTemplateManager
from claudefig.user_config import get_components_dir

# Import platform utilities
from claudefig.utils.platform import open_file_in_editor, open_folder_in_explorer

# Import shared console from parent
from .. import console

# Handle tomli import for Python < 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

logger = get_logger("cli.components")


def _load_component_metadata(component_path: Path) -> dict | None:
    """Load component metadata from component.toml file.

    Args:
        component_path: Path to component directory

    Returns:
        Component metadata dict or None if not found/invalid
    """
    if tomllib is None:
        logger.warning("tomli not available, cannot read component metadata")
        return None

    metadata_file = component_path / "component.toml"
    if not metadata_file.exists():
        return None

    try:
        with open(metadata_file, "rb") as f:
            result: dict = tomllib.load(f)
            return result
    except Exception as e:
        logger.debug(f"Failed to load component metadata from {metadata_file}: {e}")
        return None


@click.group(name="components")
def components_group():
    """Discover and manage components.

    Components are reusable content templates that can be added to file instances.
    Components can be global (available to all projects) or preset-specific.
    """
    pass


@components_group.command("list")
@click.argument("file_type", required=False, type=FILE_TYPE)
@click.option(
    "--preset",
    default="default",
    help="Preset to search for components (default: default)",
)
@handle_errors("listing components")
def components_list(file_type: FileType | None, preset):
    """List available components.

    FILE_TYPE: Optional file type filter (e.g., claude_md, settings_json).
               If not provided, lists components for all types.

    Examples:

        claudefig components list claude_md

        claudefig components list --preset my-preset
    """
    # file_type is already validated by FILE_TYPE ParamType
    file_type_str = file_type.value if file_type else None

    manager = FileTemplateManager()
    components = manager.list_components(preset, type=file_type_str)

    if not components:
        if file_type_str:
            console.print(f"[yellow]No {file_type_str} components found[/yellow]")
        else:
            console.print("[yellow]No components found[/yellow]")

        console.print(
            f"\n[dim]Global components location: {get_components_dir()}[/dim]"
        )
        return

    # Group components by type
    by_type: dict[str, list] = {}
    for comp in components:
        comp_type = comp["type"]
        if comp_type not in by_type:
            by_type[comp_type] = []
        by_type[comp_type].append(comp)

    # Display header
    if file_type_str:
        console.print(
            f"\n[bold blue]Available Components - {file_type_str}[/bold blue] ({len(components)})\n"
        )
    else:
        console.print(
            f"\n[bold blue]Available Components[/bold blue] ({len(components)})\n"
        )

    # Display components grouped by type
    for comp_type, comps in sorted(by_type.items()):
        # Pretty type name
        try:
            ft = FileType(comp_type)
            type_display = ft.name.replace("_", " ").title()
        except ValueError:
            type_display = comp_type

        console.print(f"[bold cyan]{type_display}[/bold cyan]\n")

        for comp in sorted(comps, key=lambda c: (c["source"], c["name"])):
            source_label = (
                "[cyan](preset)[/cyan]"
                if comp["source"] == "preset"
                else "[green](global)[/green]"
            )
            comp_name = comp["name"]

            # Try to load metadata for description
            metadata = _load_component_metadata(comp["path"])
            description = ""
            if metadata and "component" in metadata:
                description = metadata["component"].get("description", "")

            if description:
                console.print(f"  - [bold]{comp_name}[/bold] {source_label}")
                console.print(f"    [dim]{description}[/dim]")
            else:
                console.print(f"  - [bold]{comp_name}[/bold] {source_label}")

        console.print()

    console.print(f"[dim]Global: {get_components_dir()}[/dim]")
    console.print(
        "\n[dim]Use 'claudefig components show <type> <name>' for details[/dim]"
    )


@components_group.command("show")
@click.argument("file_type", type=FILE_TYPE)
@click.argument("component_name")
@click.option(
    "--preset",
    default="default",
    help="Preset to search for components (default: default)",
)
@handle_errors("showing component")
def components_show(file_type: FileType, component_name, preset):
    """Show detailed information about a component.

    FILE_TYPE: Component type (e.g., claude_md, settings_json)
    COMPONENT_NAME: Name of the component

    Examples:

        claudefig components show claude_md default

        claudefig components show claude_md fastapi --preset my-preset
    """
    # file_type is already validated by FILE_TYPE ParamType
    file_type_str = file_type.value

    manager = FileTemplateManager()
    components = manager.list_components(preset, type=file_type_str)

    # Find the specific component
    component = next(
        (
            c
            for c in components
            if c["name"] == component_name and c["type"] == file_type_str
        ),
        None,
    )

    if not component:
        console.print(
            format_cli_warning(
                ErrorMessages.not_found(
                    "component", f"{file_type_str}/{component_name}"
                )
            )
        )
        console.print(
            f"\n[dim]Use 'claudefig components list {file_type_str}' to see available components[/dim]"
        )
        raise click.Abort()

    # Load metadata
    metadata = _load_component_metadata(component["path"])

    # Display component details
    console.print("\n[bold blue]Component Details[/bold blue]\n")

    source_display = "Preset-specific" if component["source"] == "preset" else "Global"
    console.print(f"[bold]Name:[/bold]        {component_name}")
    console.print(f"[bold]Type:[/bold]        {file_type_str}")
    console.print(f"[bold]Source:[/bold]      {source_display}")
    console.print(f"[bold]Path:[/bold]        {component['path']}")

    if metadata and "component" in metadata:
        comp_meta = metadata["component"]

        if "description" in comp_meta:
            console.print(f"[bold]Description:[/bold] {comp_meta['description']}")

        if "version" in comp_meta:
            console.print(f"[bold]Version:[/bold]     {comp_meta['version']}")

        # Show metadata section if present
        if "metadata" in metadata:
            meta_section = metadata["metadata"]
            if "author" in meta_section:
                console.print(f"[bold]Author:[/bold]      {meta_section['author']}")
            if "tags" in meta_section and meta_section["tags"]:
                tags_str = ", ".join(meta_section["tags"])
                console.print(f"[bold]Tags:[/bold]        {tags_str}")

        # Show dependencies if present
        if "dependencies" in metadata:
            deps = metadata["dependencies"]
            if deps.get("requires"):
                console.print("\n[bold]Requires:[/bold]")
                for req in deps["requires"]:
                    console.print(f"  - {req}")

            if deps.get("recommends"):
                console.print("\n[bold]Recommends:[/bold]")
                for rec in deps["recommends"]:
                    console.print(f"  - {rec}")

        # Show files
        console.print("\n[bold]Files:[/bold]")
        comp_path = component["path"]
        for file in comp_path.iterdir():
            if file.is_file() and not file.name.startswith("."):
                size = file.stat().st_size
                size_kb = size / 1024
                console.print(f"  - {file.name} ({size_kb:.1f} KB)")

    else:
        # No metadata file, just list files
        console.print("\n[bold]Files:[/bold]")
        comp_path = component["path"]
        for file in comp_path.iterdir():
            if file.is_file():
                console.print(f"  - {file.name}")


@components_group.command("open")
@click.argument("file_type", required=False, type=FILE_TYPE)
@handle_errors("opening components directory")
def components_open(file_type: FileType | None):
    """Open the components directory in file explorer.

    FILE_TYPE: Optional file type to open specific type folder

    Examples:

        # Open global components directory
        claudefig components open

        # Open claude_md components folder
        claudefig components open claude_md
    """
    components_dir = get_components_dir()

    # file_type is already validated by FILE_TYPE ParamType
    if file_type:
        target_dir = components_dir / file_type.value
        target_dir.mkdir(parents=True, exist_ok=True)
    else:
        target_dir = components_dir
        target_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        f"[bold blue]Opening components directory:[/bold blue] {target_dir}\n"
    )

    try:
        open_folder_in_explorer(target_dir)
        console.print("[green]+[/green] Opened in file manager")
    except RuntimeError:
        console.print("[yellow]Could not open file manager automatically[/yellow]")
        console.print(f"\n[dim]Navigate to: {target_dir}[/dim]")


@components_group.command("edit")
@click.argument("file_type", type=FILE_TYPE)
@click.argument("component_name")
@click.option(
    "--preset",
    default="default",
    help="Preset to search for components (default: default)",
)
@handle_errors(
    "editing component",
    extra_handlers={
        RuntimeError: handle_editor_error,
    },
)
def components_edit(file_type: FileType, component_name, preset):
    """Edit a component's primary content file in your default editor.

    FILE_TYPE: Component type (e.g., claude_md, settings_json)
    COMPONENT_NAME: Name of the component

    Examples:

        claudefig components edit claude_md default

        claudefig components edit claude_md fastapi
    """
    # file_type is already validated by FILE_TYPE ParamType
    file_type_str = file_type.value

    manager = FileTemplateManager()
    components = manager.list_components(preset, type=file_type_str)

    # Find the specific component
    component = next(
        (
            c
            for c in components
            if c["name"] == component_name and c["type"] == file_type_str
        ),
        None,
    )

    if not component:
        console.print(
            format_cli_warning(
                ErrorMessages.not_found(
                    "component", f"{file_type_str}/{component_name}"
                )
            )
        )
        console.print(
            f"\n[dim]Use 'claudefig components list {file_type_str}' to see available components[/dim]"
        )
        raise click.Abort()

    comp_path = component["path"]

    # Find the primary content file (usually content.md or similar)
    content_files = [
        "content.md",
        "CLAUDE.md",
        "README.md",
        "template.md",
        "content.txt",
    ]

    target_file = None
    for filename in content_files:
        candidate = comp_path / filename
        if candidate.exists():
            target_file = candidate
            break

    # If no known content file, just pick the first non-.toml file
    if not target_file:
        for file in comp_path.iterdir():
            if (
                file.is_file()
                and file.suffix != ".toml"
                and not file.name.startswith(".")
            ):
                target_file = file
                break

    if not target_file:
        console.print(
            format_cli_error(
                f"No editable content file found in component directory: {comp_path}"
            )
        )
        raise click.Abort()

    console.print(f"[bold blue]Opening component file:[/bold blue] {target_file}\n")

    if component["source"] == "preset":
        console.print("[yellow]Warning: Editing preset-specific component[/yellow]\n")

    console.print(f"[dim]Opening {target_file} in editor...[/dim]")

    open_file_in_editor(target_file)

    console.print("[green]+[/green] Component file edited")
