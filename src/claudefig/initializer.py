"""Repository initialization logic for claudefig."""

from pathlib import Path
from typing import Optional

from rich.console import Console

from claudefig.config import Config
from claudefig.template_manager import TemplateManager
from claudefig.utils import ensure_directory, is_git_repository

console = Console()


class Initializer:
    """Handles repository initialization."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the Initializer.

        Args:
            config: Configuration instance. If None, loads default config.
        """
        self.config = config or Config()
        custom_dir = self.config.get("custom.template_dir")
        self.template_manager = TemplateManager(
            Path(custom_dir) if custom_dir else None
        )

    def initialize(self, repo_path: Path, force: bool = False) -> bool:
        """Initialize Claude Code configuration in repository.

        Args:
            repo_path: Path to repository to initialize
            force: If True, overwrite existing files

        Returns:
            True if initialization successful, False otherwise.
        """
        try:
            repo_path = repo_path.resolve()
        except (OSError, RuntimeError) as e:
            console.print(f"[red]Error:[/red] Cannot resolve path: {e}")
            return False

        # Check if it's a git repository
        if not is_git_repository(repo_path):
            console.print(
                f"[yellow]Warning:[/yellow] {repo_path} is not a git repository"
            )
            proceed = console.input("Continue anyway? [y/N]: ")
            if proceed.lower() != "y":
                console.print("[yellow]Initialization cancelled[/yellow]")
                return False

        # Create .claude directory
        claude_dir = repo_path / ".claude"
        ensure_directory(claude_dir)
        console.print(f"[green]+[/green] Created directory: {claude_dir}")

        # Get template source
        template_name = self.config.get("claudefig.template_source", "default")

        # Copy template files based on config
        success = True

        if self.config.get("init.create_claude_md", True):
            success &= self._copy_template_file(
                template_name, "CLAUDE.md", repo_path, force
            )

        if self.config.get("init.create_contributing", True):
            success &= self._copy_template_file(
                template_name, "CONTRIBUTING.md", repo_path, force
            )

        if self.config.get("init.create_settings", False):
            success &= self._copy_template_file(
                template_name, "settings.json", claude_dir, force
            )

        # Create config file if it doesn't exist
        config_path = repo_path / ".claudefig.toml"
        if not config_path.exists():
            Config.create_default(config_path)
            console.print(f"[green]+[/green] Created config: {config_path}")
        else:
            console.print(f"[blue]i[/blue] Config already exists: {config_path}")

        if success:
            console.print("\n[bold green]Initialization complete![/bold green]")
            console.print(f"\nClaude Code configuration initialized in: {repo_path}")
        else:
            console.print("\n[yellow]Initialization completed with warnings[/yellow]")

        return success

    def _copy_template_file(
        self, template_name: str, filename: str, dest_dir: Path, force: bool
    ) -> bool:
        """Copy a template file to destination.

        Args:
            template_name: Name of template set
            filename: Name of file to copy
            dest_dir: Destination directory
            force: If True, overwrite existing files

        Returns:
            True if successful, False otherwise.
        """
        dest_path = dest_dir / filename

        # Check if file already exists
        if dest_path.exists() and not force:
            console.print(
                f"[yellow]![/yellow] File already exists (use --force to overwrite): {dest_path}"
            )
            return False

        try:
            content = self.template_manager.read_template_file(template_name, filename)
            dest_path.write_text(content, encoding="utf-8")
            console.print(f"[green]+[/green] Created file: {dest_path}")
            return True
        except FileNotFoundError:
            console.print(f"[yellow]![/yellow] Template file not found: {filename}")
            return False
        except Exception as e:
            console.print(f"[red]x[/red] Error creating {filename}: {e}")
            return False
