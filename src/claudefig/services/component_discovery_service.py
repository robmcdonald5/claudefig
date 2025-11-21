"""Component discovery service for scanning repositories.

This service scans a repository for Claude Code components and builds
a list of discovered components that can be used to create presets.
"""

import time
from collections import defaultdict
from pathlib import Path

from claudefig.models import (
    ComponentDiscoveryResult,
    DiscoveredComponent,
    FileType,
)

# File type patterns for component discovery
# Maps FileType to list of glob patterns for scanning
FILE_TYPE_PATTERNS: dict[FileType, dict] = {
    FileType.CLAUDE_MD: {
        "patterns": ["**/CLAUDE.md"],
        "duplicate_sensitive": True,
    },
    FileType.GITIGNORE: {
        "patterns": ["**/.gitignore"],
        "duplicate_sensitive": True,
    },
    FileType.SETTINGS_JSON: {
        "patterns": ["**/settings.json"],
        "duplicate_sensitive": True,
    },
    FileType.SETTINGS_LOCAL_JSON: {
        "patterns": ["**/settings.local.json"],
        "duplicate_sensitive": True,
    },
    FileType.STATUSLINE: {
        "patterns": ["**/statusline.sh"],
        "duplicate_sensitive": True,
    },
    FileType.COMMANDS: {
        "patterns": [".claude/commands/**/*.md"],
        "duplicate_sensitive": False,
    },
    FileType.AGENTS: {
        "patterns": [".claude/agents/**/*.md"],
        "duplicate_sensitive": False,
    },
    FileType.HOOKS: {
        "patterns": [".claude/hooks/**/*.py"],
        "duplicate_sensitive": False,
    },
    FileType.OUTPUT_STYLES: {
        "patterns": [".claude/output-styles/**/*.md"],
        "duplicate_sensitive": False,
    },
    FileType.MCP: {
        "patterns": [".claude/mcp/**/*.json", "**/.mcp.json"],
        "duplicate_sensitive": False,
    },
    FileType.PLUGINS: {
        "patterns": [".claude/plugins/**/plugin.json"],
        "duplicate_sensitive": False,
    },
    FileType.SKILLS: {
        "patterns": [".claude/skills/**/skill.md"],
        "duplicate_sensitive": False,
    },
}


class ComponentDiscoveryService:
    """Service for discovering Claude Code components in a repository.

    Scans a repository using pathlib.rglob() to find all Claude Code
    components based on file patterns and naming conventions.
    """

    def _glob_pattern(self, repo_path: Path, pattern: str):
        """Execute a glob pattern correctly handling ** patterns.

        Handles three cases:
        1. Pattern starts with ** (e.g., "**/CLAUDE.md") - use rglob from repo root
        2. Pattern has prefix before ** (e.g., ".claude/commands/**/*.md") -
           navigate to prefix dir, then use rglob for the rest
        3. No ** in pattern - use regular glob

        Args:
            repo_path: Repository root path
            pattern: Glob pattern to match

        Returns:
            Iterator of matching paths
        """
        if "**" not in pattern:
            # No recursive pattern - use regular glob
            return repo_path.glob(pattern)

        # Split pattern at first **
        if pattern.startswith("**"):
            # Pattern starts with ** - use rglob from repo root
            # e.g., "**/CLAUDE.md" -> rglob("CLAUDE.md")
            # e.g., "**/.gitignore" -> rglob(".gitignore")
            suffix = pattern[3:] if pattern.startswith("**/") else pattern[2:]
            return repo_path.rglob(suffix)
        else:
            # Pattern has a prefix directory before **
            # e.g., ".claude/commands/**/*.md"
            # Split into prefix and suffix at **
            parts = pattern.split("**", 1)
            prefix = parts[0].rstrip("/")  # e.g., ".claude/commands"
            suffix = parts[1].lstrip("/")  # e.g., "*.md"

            # Check if prefix directory exists
            prefix_path = repo_path / prefix
            if not prefix_path.exists() or not prefix_path.is_dir():
                return iter([])  # Return empty iterator

            # Use rglob from the prefix directory
            return prefix_path.rglob(suffix)

    def discover_components(self, repo_path: Path) -> ComponentDiscoveryResult:
        """Discover all Claude Code components in a repository.

        Scans the repository for all supported file types and returns
        a result containing discovered components, warnings, and metrics.

        Args:
            repo_path: Path to the repository root to scan

        Returns:
            ComponentDiscoveryResult with all discovered components

        Raises:
            ValueError: If repo_path doesn't exist or isn't a directory
        """
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        if not repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")

        start_time = time.time()
        discovered: list[DiscoveredComponent] = []
        warnings: list[str] = []

        # Scan for each file type
        for file_type, config in FILE_TYPE_PATTERNS.items():
            for pattern in config["patterns"]:
                try:
                    matches = self._glob_pattern(repo_path, pattern)

                    for file_path in matches:
                        # Skip symbolic links to avoid loops and duplicate discoveries
                        if file_path.is_symlink():
                            continue
                        # Only process files, not directories
                        if file_path.is_file():
                            component = self._create_discovered_component(
                                file_path=file_path,
                                file_type=file_type,
                                repo_root=repo_path,
                                is_duplicate_sensitive=config["duplicate_sensitive"],
                            )
                            if component:
                                discovered.append(component)
                except (OSError, PermissionError) as e:
                    # Log the error but continue scanning
                    warnings.append(f"Error scanning pattern '{pattern}': {e}")
                    continue

        # Detect duplicate names and add to warnings
        duplicate_warnings = self._detect_duplicate_names(discovered)
        warnings.extend(duplicate_warnings)

        scan_time_ms = (time.time() - start_time) * 1000

        return ComponentDiscoveryResult(
            components=discovered,
            total_found=len(discovered),
            warnings=warnings,
            scan_time_ms=scan_time_ms,
        )

    def _create_discovered_component(
        self,
        file_path: Path,
        file_type: FileType,
        repo_root: Path,
        is_duplicate_sensitive: bool,
    ) -> DiscoveredComponent | None:
        """Create a DiscoveredComponent from a file path.

        Args:
            file_path: Absolute path to the discovered file
            file_type: Type of component
            repo_root: Root of the repository
            is_duplicate_sensitive: Whether this type uses folder-based naming

        Returns:
            DiscoveredComponent or None if component should be skipped
        """
        try:
            relative_path = file_path.relative_to(repo_root)
        except ValueError:
            # File is not within repo_root
            return None

        # Generate component name using naming strategy
        if is_duplicate_sensitive:
            name = self._generate_name_duplicate_sensitive(
                file_path=file_path,
                repo_root=repo_root,
                file_type=file_type,
            )
        else:
            name = self._generate_name_standard(file_path)

        # Get parent folder name
        parent_folder = file_path.parent.name if file_path.parent != repo_root else "."

        return DiscoveredComponent(
            name=name,
            type=file_type,
            path=file_path,
            relative_path=relative_path,
            parent_folder=parent_folder,
            is_duplicate=False,  # Will be updated by duplicate detection
            duplicate_paths=[],
        )

    def _generate_name_duplicate_sensitive(
        self, file_path: Path, repo_root: Path, file_type: FileType
    ) -> str:
        """Generate component name for duplicate-sensitive file types.

        Duplicate-sensitive types (CLAUDE.md, .gitignore, settings, statusline)
        use folder-based naming to avoid conflicts.

        Examples:
            /repo/CLAUDE.md → "CLAUDE"
            /repo/src/CLAUDE.md → "src-CLAUDE"
            /repo/docs/api/CLAUDE.md → "api-CLAUDE"
            /repo/.gitignore → "gitignore"
            /repo/src/.gitignore → "src-gitignore"

        Args:
            file_path: Absolute path to the file
            repo_root: Root of the repository
            file_type: Type of component

        Returns:
            Component name string
        """
        relative = file_path.relative_to(repo_root)
        parent = relative.parent

        # Determine base name from file type
        if file_type == FileType.CLAUDE_MD:
            base_name = "CLAUDE"
        elif file_type == FileType.GITIGNORE:
            base_name = "gitignore"
        elif file_type == FileType.SETTINGS_JSON:
            base_name = "settings"
        elif file_type == FileType.SETTINGS_LOCAL_JSON:
            base_name = "settings-local"
        elif file_type == FileType.STATUSLINE:
            base_name = "statusline"
        else:
            base_name = file_path.stem

        # Root-level file - just use base name
        if parent == Path("."):
            return base_name

        # Subdirectory file - use immediate parent + base name
        folder_name = parent.name
        return f"{folder_name}-{base_name}"

    def _generate_name_standard(self, file_path: Path) -> str:
        """Generate component name for non-duplicate file types.

        Non-duplicate types (commands, agents, hooks, etc.) use the
        filename without extension as the component name.

        Examples:
            .claude/commands/git-workflow.md → "git-workflow"
            .claude/agents/python-helper.md → "python-helper"
            .claude/mcp/filesystem.json → "filesystem"

        Args:
            file_path: Absolute path to the file

        Returns:
            Component name string
        """
        return file_path.stem

    def _detect_duplicate_names(
        self, components: list[DiscoveredComponent]
    ) -> list[str]:
        """Detect and flag duplicate component names.

        Updates the is_duplicate flag and duplicate_paths list for
        components with duplicate names.

        Args:
            components: List of discovered components to check

        Returns:
            List of warning messages for duplicate names
        """
        warnings: list[str] = []

        # Group components by name
        name_groups: dict[str, list[DiscoveredComponent]] = defaultdict(list)
        for component in components:
            name_groups[component.name].append(component)

        # Check for duplicates
        for name, group in name_groups.items():
            if len(group) > 1:
                # Found duplicates
                paths = [c.path for c in group]
                warning = (
                    f"Duplicate component name '{name}' found in {len(group)} locations: "
                    f"{', '.join(str(p) for p in paths)}"
                )
                warnings.append(warning)

                # Update each component in the duplicate group
                for component in group:
                    component.is_duplicate = True
                    component.duplicate_paths = [
                        p for p in paths if p != component.path
                    ]

        return warnings
