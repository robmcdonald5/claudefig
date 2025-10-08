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

        # .claude/ directory features
        self._setup_claude_directory(claude_dir, template_name, force)

        # Update .gitignore with claudefig entries
        if self.config.get("init.create_gitignore_entries", True):
            success &= self._update_gitignore(repo_path, template_name)

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

    def _update_gitignore(self, repo_path: Path, template_name: str) -> bool:
        """Add or update .gitignore with claudefig entries.

        Args:
            repo_path: Path to repository
            template_name: Name of template set to use for gitignore entries

        Returns:
            True if successful, False otherwise.
        """
        gitignore_path = repo_path / ".gitignore"

        try:
            # Read the gitignore entries template
            entries = self.template_manager.read_template_file(
                template_name, "gitignore_entries.txt"
            )
            entries = entries.strip()

            # Check if .gitignore exists
            if gitignore_path.exists():
                # Read existing content
                existing_content = gitignore_path.read_text(encoding="utf-8")

                # Check if claudefig section already exists
                if "# claudefig" in existing_content or ".claudefig.toml" in existing_content:
                    console.print(
                        "[blue]i[/blue] .gitignore already contains claudefig entries"
                    )
                    return True

                # Append to existing gitignore
                # Ensure there's a blank line before our section
                separator = "\n\n" if existing_content.strip() else ""
                new_content = existing_content.rstrip() + separator + entries + "\n"

                gitignore_path.write_text(new_content, encoding="utf-8")
                console.print(
                    "[green]+[/green] Updated .gitignore with claudefig entries"
                )
            else:
                # Create new .gitignore
                gitignore_path.write_text(entries + "\n", encoding="utf-8")
                console.print("[green]+[/green] Created .gitignore with claudefig entries")

            return True

        except FileNotFoundError:
            console.print(
                "[yellow]![/yellow] gitignore_entries.txt template not found"
            )
            return False
        except Exception as e:
            console.print(f"[red]x[/red] Error updating .gitignore: {e}")
            return False

    def _setup_claude_directory(
        self, claude_dir: Path, template_name: str, force: bool
    ) -> None:
        """Set up .claude/ directory with optional features.

        Args:
            claude_dir: Path to .claude directory
            template_name: Name of template set
            force: If True, overwrite existing files
        """
        # settings.json - team shared config
        if self.config.get("claude.create_settings", False):
            self._copy_claude_template_file(
                template_name, "settings.json", claude_dir, force
            )

        # settings.local.json - personal project config
        if self.config.get("claude.create_settings_local", False):
            self._copy_claude_template_file(
                template_name, "settings.local.json", claude_dir, force
            )

        # commands/ - custom slash commands
        if self.config.get("claude.create_commands", False):
            self._copy_template_directory(
                template_name, "claude/commands", claude_dir / "commands", force
            )

        # agents/ - custom sub-agents
        if self.config.get("claude.create_agents", False):
            self._copy_template_directory(
                template_name, "claude/agents", claude_dir / "agents", force
            )

        # hooks/ - custom hooks
        if self.config.get("claude.create_hooks", False):
            self._copy_template_directory(
                template_name, "claude/hooks", claude_dir / "hooks", force
            )

        # output-styles/ - custom output styles
        if self.config.get("claude.create_output_styles", False):
            self._copy_template_directory(
                template_name,
                "claude/output-styles",
                claude_dir / "output-styles",
                force,
            )

        # statusline.sh - custom status line
        if self.config.get("claude.create_statusline", False):
            self._copy_claude_template_file(
                template_name, "statusline.sh", claude_dir, force
            )
            # Make statusline.sh executable
            statusline_path = claude_dir / "statusline.sh"
            if statusline_path.exists():
                statusline_path.chmod(0o755)

        # mcp/ - MCP server configs
        if self.config.get("claude.create_mcp", False):
            self._copy_template_directory(
                template_name, "claude/mcp", claude_dir / "mcp", force
            )

    def setup_mcp_servers(self, repo_path: Path) -> bool:
        """Set up MCP servers from .claude/mcp/ directory.

        Runs 'claude mcp add-json' for each JSON file in .claude/mcp/

        Args:
            repo_path: Path to repository

        Returns:
            True if successful, False otherwise.
        """
        import subprocess
        import json

        mcp_dir = repo_path / ".claude" / "mcp"

        if not mcp_dir.exists():
            console.print("[yellow]![/yellow] No .claude/mcp/ directory found")
            return False

        # Find all JSON files
        json_files = list(mcp_dir.glob("*.json"))

        if not json_files:
            console.print("[yellow]![/yellow] No MCP config files found in .claude/mcp/")
            return False

        console.print(f"\n[bold blue]Setting up MCP servers...[/bold blue]")

        success_count = 0
        for json_file in json_files:
            # Extract server name from filename (remove example- prefix if present)
            server_name = json_file.stem
            if server_name.startswith("example-"):
                server_name = server_name.replace("example-", "")

            try:
                # Read JSON content
                with open(json_file, "r", encoding="utf-8") as f:
                    json_content = f.read().strip()

                # Validate JSON
                json.loads(json_content)

                # Build claude mcp add-json command
                cmd = ["claude", "mcp", "add-json", server_name, json_content]

                console.print(
                    f"[dim]Running:[/dim] claude mcp add-json {server_name} ..."
                )

                # Run command
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    console.print(
                        f"[green]+[/green] Added MCP server: {server_name}"
                    )
                    success_count += 1
                else:
                    console.print(
                        f"[yellow]![/yellow] Failed to add {server_name}: {result.stderr.strip()}"
                    )

            except json.JSONDecodeError as e:
                console.print(
                    f"[red]x[/red] Invalid JSON in {json_file.name}: {e}"
                )
            except subprocess.TimeoutExpired:
                console.print(
                    f"[red]x[/red] Timeout adding {server_name}"
                )
            except FileNotFoundError:
                console.print(
                    "[red]x[/red] 'claude' command not found. Make sure Claude Code is installed."
                )
                return False
            except Exception as e:
                console.print(
                    f"[red]x[/red] Error adding {server_name}: {e}"
                )

        if success_count > 0:
            console.print(
                f"\n[bold green]Added {success_count} MCP server(s)[/bold green]"
            )
            return True
        else:
            console.print("\n[yellow]No MCP servers were added[/yellow]")
            return False

    def _copy_claude_template_file(
        self, template_name: str, filename: str, dest_dir: Path, force: bool
    ) -> bool:
        """Copy a file from claude/ template subdirectory to destination.

        Args:
            template_name: Name of template set
            filename: Name of file in claude/ subdirectory
            dest_dir: Destination directory (.claude/)
            force: If True, overwrite existing files

        Returns:
            True if successful, False otherwise.
        """
        from pathlib import Path as PathLib

        # Source is claude/filename in template
        source_path = f"claude/{filename}"
        # Destination is dest_dir/filename (not dest_dir/claude/filename)
        dest_path = dest_dir / filename

        # Check if file already exists
        if dest_path.exists() and not force:
            console.print(
                f"[yellow]![/yellow] File already exists (use --force to overwrite): {dest_path}"
            )
            return False

        try:
            content = self.template_manager.read_template_file(template_name, source_path)
            dest_path.write_text(content, encoding="utf-8")
            console.print(f"[green]+[/green] Created file: {dest_path}")
            return True
        except FileNotFoundError:
            console.print(f"[yellow]![/yellow] Template file not found: {source_path}")
            return False
        except Exception as e:
            console.print(f"[red]x[/red] Error creating {filename}: {e}")
            return False

    def _copy_template_directory(
        self, template_name: str, source_dir: str, dest_dir: Path, force: bool
    ) -> bool:
        """Copy a template directory to destination.

        Args:
            template_name: Name of template set
            source_dir: Source directory path relative to template
            dest_dir: Destination directory path
            force: If True, overwrite existing files

        Returns:
            True if successful, False otherwise.
        """
        from importlib.resources import files
        import shutil

        try:
            # Get template source directory
            template_root = files("templates").joinpath(template_name)
            source_path = template_root.joinpath(source_dir)

            # Create destination directory
            ensure_directory(dest_dir)

            # Copy all files from source to destination
            copied_count = 0
            for item in source_path.iterdir():
                if item.is_file():
                    dest_file = dest_dir / item.name
                    if dest_file.exists() and not force:
                        console.print(
                            f"[yellow]![/yellow] File already exists (use --force to overwrite): {dest_file}"
                        )
                        continue

                    shutil.copy2(str(item), dest_file)
                    copied_count += 1
                    console.print(f"[green]+[/green] Created file: {dest_file}")

            if copied_count > 0:
                console.print(
                    f"[green]+[/green] Created directory: {dest_dir} ({copied_count} files)"
                )
            return True

        except FileNotFoundError:
            console.print(f"[yellow]![/yellow] Template directory not found: {source_dir}")
            return False
        except Exception as e:
            console.print(f"[red]x[/red] Error copying directory {source_dir}: {e}")
            return False
