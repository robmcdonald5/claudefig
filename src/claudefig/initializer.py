"""Repository initialization logic for claudefig."""

import shutil
from pathlib import Path

from rich.console import Console

from claudefig.exceptions import FileOperationError, InitializationRollbackError
from claudefig.models import FileInstance, FileType
from claudefig.preset_manager import PresetManager
from claudefig.repositories.config_repository import TomlConfigRepository
from claudefig.repositories.preset_repository import TomlPresetRepository
from claudefig.services import config_service, file_instance_service
from claudefig.template_manager import FileTemplateManager
from claudefig.utils.paths import (
    ensure_directory,
    is_git_repository,
    validate_not_symlink,
)
from claudefig.utils.platform import is_windows

console = Console()


class Initializer:
    """Handles repository initialization."""

    def __init__(self, config_path: Path | None = None):
        """Initialize the Initializer.

        Args:
            config_path: Path to config file. If None, finds or uses default.
        """
        # Initialize repositories
        if config_path is None:
            found_path = config_service.find_config_path()
            config_path = found_path or (Path.cwd() / "claudefig.toml")

        self.config_path = config_path
        self.config_repo = TomlConfigRepository(config_path)
        self.config_data = config_service.load_config(self.config_repo)

        # Initialize services/managers
        custom_dir = config_service.get_value(self.config_data, "custom.template_dir")
        self.template_manager = FileTemplateManager(
            Path(custom_dir) if custom_dir else None
        )
        self.preset_manager = PresetManager()
        self.preset_repo = TomlPresetRepository()

        # Instance tracking
        self.instances_dict: dict[str, FileInstance] = {}

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

    def initialize(
        self, repo_path: Path, force: bool = False, skip_prompts: bool = False
    ) -> bool:
        """Initialize Claude Code configuration in repository.

        Uses the file instance system to generate files based on configuration.

        Args:
            repo_path: Path to repository to initialize
            force: If True, overwrite existing files
            skip_prompts: If True, skip interactive prompts (for TUI/non-interactive use)

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
            raise FileOperationError(f"resolve path {repo_path}", str(e)) from e

        # Check if it's a git repository
        if not is_git_repository(repo_path) and not skip_prompts:
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
            # Load file instances from config
            instances_data = config_service.get_file_instances(self.config_data)

            if not instances_data:
                # No file instances configured - create default ones
                console.print(
                    "[yellow]No file instances configured, using defaults[/yellow]"
                )
                instances_data = self._create_default_instances()
                config_service.set_file_instances(self.config_data, instances_data)

            # Load instances into dictionary
            self.instances_dict, load_errors = (
                file_instance_service.load_instances_from_config(instances_data)
            )

            # Show load errors if any
            if load_errors:
                for error in load_errors:
                    console.print(f"[yellow]Warning:[/yellow] {error}")

            # Create .claude directory
            claude_dir = repo_path / ".claude"
            if not claude_dir.exists():
                ensure_directory(claude_dir)
                self._track_directory(claude_dir)
                console.print(f"[green]+[/green] Created directory: {claude_dir}")

            # Generate files from file instances
            success = True
            files_created = 0

            enabled_instances = file_instance_service.list_instances(
                self.instances_dict, enabled_only=True
            )

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
            config_path = repo_path / "claudefig.toml"
            if not config_path.exists():
                # Create default config
                default_config = config_service.DEFAULT_CONFIG.copy()
                config_repo = TomlConfigRepository(config_path)
                config_service.save_config(default_config, config_repo)
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

            # Auto-setup MCP servers if any MCP instances were enabled
            self._auto_setup_mcp_servers(repo_path, enabled_instances)

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
        # Use preset/component system for all file types
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
            console.print(f"[blue]i[/blue] Already exists (skipped): {dest_path}")
            return True  # Treat existing files as success (skip)

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
        try:
            # Get content from preset using component system
            content = self.preset_repo.get_template_content(preset)

            # Create parent directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            dest_path.write_text(content, encoding="utf-8")
            self._track_file(dest_path)  # Track for rollback
            console.print(f"[green]+[/green] Created: {dest_path}")

            # Make statusline executable (Unix only)
            if instance.type == FileType.STATUSLINE and not is_windows():
                dest_path.chmod(0o755)

            return True

        except Exception as e:
            console.print(f"[red]x[/red] Error generating {instance.path}: {e}")
            return False

    def _append_file_from_instance(self, instance, preset, dest_path: Path) -> bool:
        """Append content to a file (for gitignore).

        Args:
            instance: FileInstance
            preset: Preset to use
            dest_path: Destination file path

        Returns:
            True if successful
        """
        try:
            # Get entries from preset using component system
            entries = self.preset_repo.get_template_content(preset)
            entries = entries.strip()

            # Check if .gitignore exists
            if dest_path.exists():
                existing_content = dest_path.read_text(encoding="utf-8")

                # Check if claudefig section already exists
                if (
                    "# claudefig" in existing_content
                    or "claudefig.toml" in existing_content
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

        except Exception as e:
            console.print(f"[red]x[/red] Error reading preset template: {e}")
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
        # Use component system to get source folder
        # Extract component name from preset (e.g., "commands:default" -> "default")
        component_name = preset.id.split(":")[-1] if ":" in preset.id else preset.name

        # Get component folder from preset repository
        from importlib.resources import files

        try:
            # Path: src/presets/default/components/{file_type}/{component_name}/
            builtin_source = files("presets").joinpath("default")

            # Get the actual path
            if hasattr(builtin_source, "__fspath__"):
                source_path = Path(builtin_source)  # type: ignore[arg-type]
            else:
                # For Python 3.10+, extract path as string
                source_path = Path(str(builtin_source))

            component_folder = (
                source_path / "components" / instance.type.value / component_name
            )

            if not component_folder.exists() or not component_folder.is_dir():
                console.print(
                    f"[yellow]![/yellow] Component folder not found: {component_folder}"
                )
                return False

            # Create destination directory
            if not dest_path.exists():
                dest_path.mkdir(parents=True, exist_ok=True)
                self._track_directory(dest_path)

            # Copy all files from component folder to destination
            copied_count = 0
            for item in component_folder.iterdir():
                if item.is_file():
                    # Security: Reject symlinks
                    validate_not_symlink(item, context="component file")

                    dest_file = dest_path / item.name
                    if dest_file.exists() and not force:
                        console.print(
                            f"[blue]i[/blue] Already exists (skipped): {dest_file}"
                        )
                        continue

                    shutil.copy2(str(item), dest_file)
                    self._track_file(dest_file)
                    copied_count += 1
                    console.print(f"[green]+[/green] Created: {dest_file}")

            if copied_count > 0:
                console.print(
                    f"[green]+[/green] Created directory: {dest_path} ({copied_count} files)"
                )
            return True

        except Exception as e:
            console.print(f"[red]x[/red] Error generating directory: {e}")
            return False

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
                    or "claudefig.toml" in existing_content
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
        """Set up MCP servers from .mcp.json or .claude/mcp/ directory.

        Supports two configuration patterns:
        1. Standard .mcp.json file in project root (checked first)
        2. Multiple JSON files in .claude/mcp/ directory

        Runs 'claude mcp add-json' for each server configuration found.

        Args:
            repo_path: Path to repository

        Returns:
            True if successful, False otherwise.
        """
        import json
        import subprocess

        json_files = []
        config_sources = []

        # Check for standard .mcp.json first
        mcp_json = repo_path / ".mcp.json"
        if mcp_json.exists():
            json_files.append(mcp_json)
            config_sources.append(".mcp.json (standard)")

        # Check for .claude/mcp/*.json files
        mcp_dir = repo_path / ".claude" / "mcp"
        if mcp_dir.exists():
            dir_json_files = list(mcp_dir.glob("*.json"))
            json_files.extend(dir_json_files)
            if dir_json_files:
                config_sources.append(f".claude/mcp/ ({len(dir_json_files)} files)")

        if not json_files:
            console.print(
                "[yellow]![/yellow] No MCP configuration found. "
                "Expected .mcp.json or .claude/mcp/*.json"
            )
            return False

        console.print("\n[bold blue]Setting up MCP servers...[/bold blue]")
        if config_sources:
            console.print(f"[dim]Sources:[/dim] {', '.join(config_sources)}")

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

                # Validate JSON structure before subprocess execution
                config = self._validate_mcp_json_schema(json_content, json_file.name)

                # Validate transport type if present
                self._validate_mcp_transport(config, json_file.name)

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
            except ValueError as e:
                console.print(
                    f"[red]x[/red] Configuration error in {json_file.name}: {e}"
                )
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

    def _validate_mcp_json_schema(self, json_content: str, filename: str) -> dict:
        """Validate MCP config JSON structure before subprocess execution.

        Args:
            json_content: Raw JSON string from file
            filename: Source filename for error messages

        Returns:
            Parsed config dict if valid

        Raises:
            json.JSONDecodeError: If JSON is malformed
            ValueError: If JSON structure is invalid
        """
        import json

        config = json.loads(json_content)

        # MCP config must be a JSON object
        if not isinstance(config, dict):
            raise ValueError(
                f"MCP config must be a JSON object, got {type(config).__name__}"
            )

        return config

    def _validate_mcp_transport(self, config: dict, filename: str) -> None:
        """Validate MCP transport configuration.

        Args:
            config: Parsed JSON configuration
            filename: Name of config file (for error messages)

        Raises:
            ValueError: If transport configuration is invalid
        """
        # If no transport type specified, assume STDIO (backward compatibility)
        if "type" not in config and "transport" not in config:
            return

        transport_type = config.get("type") or config.get("transport", {}).get("type")

        if not transport_type:
            return

        # Validate transport type
        valid_transports = ["stdio", "http", "sse"]
        if transport_type not in valid_transports:
            raise ValueError(
                f"Invalid transport type '{transport_type}'. "
                f"Must be one of: {', '.join(valid_transports)}"
            )

        # Transport-specific validation
        if transport_type == "http":
            if "url" not in config:
                raise ValueError(
                    "HTTP transport requires 'url' field. "
                    'Example: "url": "${MCP_SERVICE_URL}"'
                )

            # Warn about common security issues
            url = config.get("url", "")
            if url.startswith("http://") and not url.startswith("http://localhost"):
                console.print(
                    f"[yellow]Warning:[/yellow] {filename} uses HTTP (not HTTPS). "
                    "Consider using HTTPS for production."
                )

            # Check for hardcoded credentials (common mistake)
            headers = config.get("headers", {})
            for key, value in headers.items():
                if (
                    isinstance(value, str)
                    and not value.startswith("${")
                    and any(
                        sensitive in key.lower()
                        for sensitive in ["auth", "token", "key", "secret"]
                    )
                ):
                    console.print(
                        f"[yellow]Warning:[/yellow] {filename} may contain hardcoded "
                        f"credentials in header '{key}'. Use environment variables: "
                        '"${VAR_NAME}"'
                    )

        elif transport_type == "stdio":
            if "command" not in config:
                raise ValueError(
                    "STDIO transport requires 'command' field. "
                    'Example: "command": "npx"'
                )

        elif transport_type == "sse":
            console.print(
                "[yellow]Info:[/yellow] SSE transport is deprecated. "
                "Consider using HTTP transport instead."
            )

    def _auto_setup_mcp_servers(self, repo_path: Path, enabled_instances: list) -> None:
        """Automatically setup MCP servers if MCP instances are enabled.

        Called during initialization to register MCP servers with Claude Code.
        Non-fatal - warnings are shown but initialization continues on failure.

        Args:
            repo_path: Path to repository
            enabled_instances: List of enabled FileInstance objects
        """
        from .models import FileType

        # Check if any MCP instances are enabled
        has_mcp = any(instance.type == FileType.MCP for instance in enabled_instances)

        if not has_mcp:
            return

        # Check if MCP configs exist
        mcp_json = repo_path / ".mcp.json"
        mcp_dir = repo_path / ".claude" / "mcp"

        has_configs = mcp_json.exists() or (
            mcp_dir.exists() and list(mcp_dir.glob("*.json"))
        )

        if not has_configs:
            # No configs yet - user will add them later
            return

        # Attempt to setup MCP servers
        console.print("\n[bold blue]Setting up MCP servers...[/bold blue]")

        try:
            success = self.setup_mcp_servers(repo_path)
            if not success:
                console.print(
                    "[yellow]Note:[/yellow] MCP servers not registered. "
                    "You can run 'claudefig setup-mcp' later to register them."
                )
        except Exception as e:
            # Non-fatal - just warn the user
            console.print(
                f"[yellow]Warning:[/yellow] Could not auto-setup MCP servers: {e}"
            )
            console.print(
                "[dim]You can manually setup MCP servers by running:[/dim] "
                "claudefig setup-mcp"
            )

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
        source_path = Path("claude") / filename
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
                template_name, str(source_path)
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
            template_root = files("presets").joinpath(template_name)
            source_path = template_root.joinpath(source_dir)

            # Create destination directory
            if not dest_dir.exists():
                ensure_directory(dest_dir)
                self._track_directory(dest_dir)  # Track for rollback

            # Copy all files from source to destination
            copied_count = 0
            for item in source_path.iterdir():
                if item.is_file():
                    # Security: Reject symlinks
                    item_path = Path(str(item))
                    validate_not_symlink(item_path, context="template file")

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
