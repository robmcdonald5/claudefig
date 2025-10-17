"""Repository initialization logic for claudefig."""

import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console

from claudefig.config import Config
from claudefig.exceptions import InitializationRollbackError
from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import FileType
from claudefig.preset_manager import PresetManager
from claudefig.template_manager import FileTemplateManager
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
        self.template_manager = FileTemplateManager(
            Path(custom_dir) if custom_dir else None
        )
        self.preset_manager = PresetManager()
        self.instance_manager: Optional[FileInstanceManager] = None

        # Track created files/directories for rollback
        self._created_files: list[Path] = []
        self._created_dirs: list[Path] = []
        self._rollback_enabled: bool = True

    def _track_file(self, file_path: Path) -> None:
        """Track a created file for potential rollback.

        Args:
            file_path: Path to file that was created
        """
        if self._rollback_enabled and file_path not in self._created_files:
            self._created_files.append(file_path)

    def _track_directory(self, dir_path: Path) -> None:
        """Track a created directory for potential rollback.

        Args:
            dir_path: Path to directory that was created
        """
        if self._rollback_enabled and dir_path not in self._created_dirs:
            self._created_dirs.append(dir_path)

    def _rollback(self) -> None:
        """Rollback initialization by removing all created files and directories."""
        console.print("\n[yellow]Rolling back initialization...[/yellow]")

        # Remove files
        for file_path in reversed(self._created_files):
            try:
                if file_path.exists():
                    file_path.unlink()
                    console.print(f"[dim]Removed file: {file_path}[/dim]")
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Failed to remove {file_path}: {e}[/yellow]"
                )

        # Remove directories (in reverse order to handle nested directories)
        for dir_path in reversed(self._created_dirs):
            try:
                if (
                    dir_path.exists()
                    and dir_path.is_dir()
                    and not any(dir_path.iterdir())
                ):
                    # Only remove if empty
                    dir_path.rmdir()
                    console.print(f"[dim]Removed directory: {dir_path}[/dim]")
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Failed to remove {dir_path}: {e}[/yellow]"
                )

        console.print("[yellow]Rollback complete[/yellow]")

    def _clear_tracking(self) -> None:
        """Clear the rollback tracking lists."""
        self._created_files.clear()
        self._created_dirs.clear()

    def initialize(self, repo_path: Path, force: bool = False) -> bool:
        """Initialize Claude Code configuration in repository.

        Uses the file instance system to generate files based on configuration.

        Args:
            repo_path: Path to repository to initialize
            force: If True, overwrite existing files

        Returns:
            True if initialization successful, False otherwise.

        Raises:
            InitializationRollbackError: If initialization fails and rollback is triggered
        """
        # Clear any previous tracking
        self._clear_tracking()

        # Disable rollback in force mode (user explicitly wants to overwrite)
        self._rollback_enabled = not force

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

        # Wrap the actual initialization in try-except for rollback
        errors = []
        failed_files = []

        try:
            # Initialize FileInstanceManager
            self.instance_manager = FileInstanceManager(self.preset_manager, repo_path)

            # Load file instances from config
            instances_data = self.config.get_file_instances()

            if not instances_data:
                # No file instances configured - create default ones
                console.print(
                    "[yellow]No file instances configured, using defaults[/yellow]"
                )
                instances_data = self._create_default_instances()
                self.config.set_file_instances(instances_data)

            self.instance_manager.load_instances(instances_data)

            # Create .claude directory
            claude_dir = repo_path / ".claude"
            if not claude_dir.exists():
                ensure_directory(claude_dir)
                self._track_directory(claude_dir)
                console.print(f"[green]+[/green] Created directory: {claude_dir}")

            # Generate files from file instances
            success = True
            files_created = 0

            enabled_instances = self.instance_manager.list_instances(enabled_only=True)

            if not enabled_instances:
                console.print("[yellow]No enabled file instances to generate[/yellow]")
            else:
                console.print(
                    f"\n[bold blue]Generating {len(enabled_instances)} file(s)...[/bold blue]\n"
                )

                for instance in enabled_instances:
                    result = self._generate_file_from_instance(
                        instance, repo_path, force
                    )
                    if result:
                        files_created += 1
                    else:
                        failed_files.append(instance.path)
                        errors.append(f"Failed to generate {instance.path}")
                    success &= result

            # Create config file if it doesn't exist
            config_path = repo_path / ".claudefig.toml"
            if not config_path.exists():
                Config.create_default(config_path)
                self._track_file(config_path)
                console.print(f"\n[green]+[/green] Created config: {config_path}")
            else:
                console.print(f"\n[blue]i[/blue] Config already exists: {config_path}")

            # If we had critical failures and rollback is enabled, trigger rollback
            if (
                not success
                and self._rollback_enabled
                and len(failed_files) > len(enabled_instances) // 2
            ):
                # More than half failed - this is a critical failure
                raise InitializationRollbackError(failed_files, errors)

            # Summary
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  Files created: {files_created}")
            console.print(f"  Enabled instances: {len(enabled_instances)}")

            if success:
                console.print("\n[bold green]Initialization complete![/bold green]")
                console.print(
                    f"\nClaude Code configuration initialized in: {repo_path}"
                )
            else:
                console.print(
                    "\n[yellow]Initialization completed with warnings[/yellow]"
                )

            # Clear tracking on success
            self._clear_tracking()

            return success

        except InitializationRollbackError:
            # Rollback and re-raise
            self._rollback()
            raise

        except Exception as e:
            # Unexpected error - rollback if enabled
            error_msg = (
                f"Unexpected error during initialization: {type(e).__name__}: {e}"
            )
            errors.append(error_msg)
            console.print(f"[red]Error:[/red] {error_msg}")

            if self._rollback_enabled:
                self._rollback()
                raise InitializationRollbackError(failed_files, errors) from e

            return False

    def _create_default_instances(self) -> list[dict]:
        """Create default file instances when none are configured.

        Returns:
            List of default file instance dictionaries
        """
        from claudefig.models import FileInstance

        defaults = [
            FileInstance.create_default(FileType.CLAUDE_MD).to_dict(),
            FileInstance.create_default(FileType.GITIGNORE).to_dict(),
        ]

        return defaults

    def _generate_file_from_instance(
        self, instance, repo_path: Path, force: bool
    ) -> bool:
        """Generate a file from a file instance.

        Args:
            instance: FileInstance to generate
            repo_path: Repository root path
            force: Whether to overwrite existing files

        Returns:
            True if successful, False otherwise
        """
        # Check if this file type uses template directories
        if instance.type.template_directory:
            # Use template directory system (new approach for single-instance types)
            return self._generate_from_template_directory(instance, repo_path, force)

        # Otherwise, use preset system (existing approach)
        preset = self.preset_manager.get_preset(instance.preset)
        if not preset:
            console.print(
                f"[red]x[/red] Preset not found for instance '{instance.id}': {instance.preset}"
            )
            return False

        # Determine full path
        dest_path = repo_path / instance.path

        # Check if file/directory already exists
        if dest_path.exists() and not force and not instance.type.append_mode:
            console.print(
                f"[yellow]![/yellow] Already exists (use --force to overwrite): {dest_path}"
            )
            return False

        try:
            if instance.type.is_directory:
                # Handle directory-based file types (commands, agents, hooks, etc.)
                return self._generate_directory_from_instance(
                    instance, preset, dest_path, force
                )
            elif instance.type.append_mode:
                # Handle append mode (gitignore)
                return self._append_file_from_instance(instance, preset, dest_path)
            else:
                # Handle single file types
                return self._generate_single_file_from_instance(
                    instance, preset, dest_path
                )

        except Exception as e:
            console.print(f"[red]x[/red] Error generating {instance.path}: {e}")
            return False

    def _generate_from_template_directory(
        self, instance, repo_path: Path, force: bool
    ) -> bool:
        """Generate a file from GLOBAL template directory (new system for single-instance types).

        Reads templates from ~/.claudefig/{template_dir}/ (global user directory).

        Args:
            instance: FileInstance to generate
            repo_path: Repository root path
            force: Whether to overwrite existing files

        Returns:
            True if successful, False otherwise
        """
        template_dir = instance.type.template_directory
        extension = instance.type.template_file_extension

        if not template_dir or not extension:
            console.print(
                f"[red]x[/red] No template directory configured for {instance.type.value}"
            )
            return False

        # Build template path from GLOBAL ~/.claudefig/ directory
        global_claudefig = Path.home() / ".claudefig"
        template_name = instance.preset
        # Strip preset ID prefix if present (backwards compatibility)
        if ":" in template_name:
            template_name = template_name.split(":", 1)[1]

        template_path = global_claudefig / template_dir / f"{template_name}{extension}"

        if not template_path.exists():
            console.print(f"[red]x[/red] Template not found: {template_path}")
            console.print(
                f"[yellow]![/yellow] Expected template in global directory: {global_claudefig / template_dir}/"
            )
            return False

        # Determine destination path
        dest_path = repo_path / instance.path

        # Check if file already exists
        if dest_path.exists() and not force:
            console.print(
                f"[yellow]![/yellow] Already exists (use --force to overwrite): {dest_path}"
            )
            return False

        try:
            # Read template content
            content = template_path.read_text(encoding="utf-8")

            # Create parent directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            dest_path.write_text(content, encoding="utf-8")
            console.print(f"[green]+[/green] Created: {dest_path}")

            # Make statusline executable
            if instance.type == FileType.STATUSLINE:
                dest_path.chmod(0o755)

            return True

        except Exception as e:
            console.print(f"[red]x[/red] Error generating {instance.path}: {e}")
            return False

    def _generate_single_file_from_instance(
        self, instance, preset, dest_path: Path
    ) -> bool:
        """Generate a single file from an instance.

        Args:
            instance: FileInstance
            preset: Preset to use
            dest_path: Destination file path

        Returns:
            True if successful
        """
        # Get template content
        template_name = self.config.get("claudefig.template_source", "default")

        try:
            # Try to read template file
            content = self.template_manager.read_template_file(
                template_name, instance.path
            )
        except FileNotFoundError:
            # Fallback: Try preset-specific path
            try:
                # For CLAUDE.md, try different paths
                if instance.type == FileType.CLAUDE_MD:
                    content = self.template_manager.read_template_file(
                        template_name, "CLAUDE.md"
                    )
                elif instance.type == FileType.SETTINGS_JSON:
                    content = self.template_manager.read_template_file(
                        template_name, "claude/settings.json"
                    )
                elif instance.type == FileType.SETTINGS_LOCAL_JSON:
                    content = self.template_manager.read_template_file(
                        template_name, "claude/settings.local.json"
                    )
                elif instance.type == FileType.STATUSLINE:
                    content = self.template_manager.read_template_file(
                        template_name, "claude/statusline.sh"
                    )
                else:
                    console.print(
                        f"[yellow]![/yellow] No template found for {instance.type.value}"
                    )
                    return False
            except FileNotFoundError:
                console.print(
                    f"[yellow]![/yellow] Template file not found for {instance.type.value}"
                )
                return False

        # Create parent directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        dest_path.write_text(content, encoding="utf-8")
        self._track_file(dest_path)  # Track for rollback
        console.print(f"[green]+[/green] Created: {dest_path}")

        # Make statusline executable
        if instance.type == FileType.STATUSLINE:
            dest_path.chmod(0o755)

        return True

    def _append_file_from_instance(self, instance, preset, dest_path: Path) -> bool:
        """Append content to a file (for gitignore).

        Args:
            instance: FileInstance
            preset: Preset to use
            dest_path: Destination file path

        Returns:
            True if successful
        """
        template_name = self.config.get("claudefig.template_source", "default")

        try:
            # Read gitignore entries template
            entries = self.template_manager.read_template_file(
                template_name, "gitignore_entries.txt"
            )
            entries = entries.strip()

            # Check if .gitignore exists
            if dest_path.exists():
                existing_content = dest_path.read_text(encoding="utf-8")

                # Check if claudefig section already exists
                if (
                    "# claudefig" in existing_content
                    or ".claudefig.toml" in existing_content
                ):
                    console.print(
                        f"[blue]i[/blue] Already contains entries: {dest_path}"
                    )
                    return True

                # Append to existing
                separator = "\n\n" if existing_content.strip() else ""
                new_content = existing_content.rstrip() + separator + entries + "\n"
                dest_path.write_text(new_content, encoding="utf-8")
                # Don't track appends - file already existed
                console.print(f"[green]+[/green] Updated: {dest_path}")
            else:
                # Create new
                dest_path.write_text(entries + "\n", encoding="utf-8")
                self._track_file(dest_path)  # Track for rollback
                console.print(f"[green]+[/green] Created: {dest_path}")

            return True

        except FileNotFoundError:
            console.print("[yellow]![/yellow] Template not found for gitignore entries")
            return False

    def _generate_directory_from_instance(
        self, instance, preset, dest_path: Path, force: bool
    ) -> bool:
        """Generate a directory with template files from an instance.

        Args:
            instance: FileInstance
            preset: Preset to use
            dest_path: Destination directory path
            force: Whether to overwrite existing files

        Returns:
            True if successful
        """
        template_name = self.config.get("claudefig.template_source", "default")

        # Map file types to template paths
        template_dir_map = {
            FileType.COMMANDS: "claude/commands",
            FileType.AGENTS: "claude/agents",
            FileType.HOOKS: "claude/hooks",
            FileType.OUTPUT_STYLES: "claude/output-styles",
            FileType.MCP: "claude/mcp",
        }

        source_dir = template_dir_map.get(instance.type)
        if not source_dir:
            console.print(
                f"[yellow]![/yellow] No template directory for {instance.type.value}"
            )
            return False

        # Copy directory
        return self._copy_template_directory(
            template_name, source_dir, dest_path, force
        )

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
            self._track_file(dest_path)  # Track for rollback
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
                if (
                    "# claudefig" in existing_content
                    or ".claudefig.toml" in existing_content
                ):
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
                console.print(
                    "[green]+[/green] Created .gitignore with claudefig entries"
                )

            return True

        except FileNotFoundError:
            console.print("[yellow]![/yellow] gitignore_entries.txt template not found")
            return False
        except Exception as e:
            console.print(f"[red]x[/red] Error updating .gitignore: {e}")
            return False

    def setup_mcp_servers(self, repo_path: Path) -> bool:
        """Set up MCP servers from .claude/mcp/ directory.

        Runs 'claude mcp add-json' for each JSON file in .claude/mcp/

        Args:
            repo_path: Path to repository

        Returns:
            True if successful, False otherwise.
        """
        import json
        import subprocess

        mcp_dir = repo_path / ".claude" / "mcp"

        if not mcp_dir.exists():
            console.print("[yellow]![/yellow] No .claude/mcp/ directory found")
            return False

        # Find all JSON files
        json_files = list(mcp_dir.glob("*.json"))

        if not json_files:
            console.print(
                "[yellow]![/yellow] No MCP config files found in .claude/mcp/"
            )
            return False

        console.print("\n[bold blue]Setting up MCP servers...[/bold blue]")

        success_count = 0
        for json_file in json_files:
            # Extract server name from filename (remove example- prefix if present)
            server_name = json_file.stem
            if server_name.startswith("example-"):
                server_name = server_name.replace("example-", "")

            try:
                # Read JSON content
                with open(json_file, encoding="utf-8") as f:
                    json_content = f.read().strip()

                # Validate JSON
                json.loads(json_content)

                # Build claude mcp add-json command
                cmd = ["claude", "mcp", "add-json", server_name, json_content]

                console.print(
                    f"[dim]Running:[/dim] claude mcp add-json {server_name} ..."
                )

                # Run command
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    console.print(f"[green]+[/green] Added MCP server: {server_name}")
                    success_count += 1
                else:
                    console.print(
                        f"[yellow]![/yellow] Failed to add {server_name}: {result.stderr.strip()}"
                    )

            except json.JSONDecodeError as e:
                console.print(f"[red]x[/red] Invalid JSON in {json_file.name}: {e}")
            except subprocess.TimeoutExpired:
                console.print(f"[red]x[/red] Timeout adding {server_name}")
            except FileNotFoundError:
                console.print(
                    "[red]x[/red] 'claude' command not found. Make sure Claude Code is installed."
                )
                return False
            except Exception as e:
                console.print(f"[red]x[/red] Error adding {server_name}: {e}")

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
            content = self.template_manager.read_template_file(
                template_name, source_path
            )
            dest_path.write_text(content, encoding="utf-8")
            self._track_file(dest_path)  # Track for rollback
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

        try:
            # Get template source directory
            template_root = files("templates").joinpath(template_name)
            source_path = template_root.joinpath(source_dir)

            # Create destination directory
            if not dest_dir.exists():
                ensure_directory(dest_dir)
                self._track_directory(dest_dir)  # Track for rollback

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
                    self._track_file(dest_file)  # Track for rollback
                    copied_count += 1
                    console.print(f"[green]+[/green] Created file: {dest_file}")

            if copied_count > 0:
                console.print(
                    f"[green]+[/green] Created directory: {dest_dir} ({copied_count} files)"
                )
            return True

        except FileNotFoundError:
            console.print(
                f"[yellow]![/yellow] Template directory not found: {source_dir}"
            )
            return False
        except Exception as e:
            console.print(f"[red]x[/red] Error copying directory {source_dir}: {e}")
            return False
