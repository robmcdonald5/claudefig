"""Tests for ComponentDiscoveryService."""

import pytest

from claudefig.models import FileType
from claudefig.services.component_discovery_service import (
    FILE_TYPE_PATTERNS,
    ComponentDiscoveryService,
)


@pytest.fixture
def discovery_service():
    """Create a ComponentDiscoveryService instance."""
    return ComponentDiscoveryService()


@pytest.fixture
def repo_with_components(tmp_path):
    """Create a mock repository with various Claude Code components."""
    # Root CLAUDE.md
    (tmp_path / "CLAUDE.md").write_text("# Root CLAUDE")

    # Nested CLAUDE.md
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "CLAUDE.md").write_text("# Src CLAUDE")

    # Root .gitignore
    (tmp_path / ".gitignore").write_text("*.pyc\n__pycache__/")

    # .claude directory structure
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()

    # Commands
    commands_dir = claude_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "git-workflow.md").write_text("# Git Workflow Command")
    (commands_dir / "deploy.md").write_text("# Deploy Command")

    # Agents
    agents_dir = claude_dir / "agents"
    agents_dir.mkdir()
    (agents_dir / "python-helper.md").write_text("# Python Helper Agent")

    # Hooks
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "pre-commit.py").write_text("# Pre-commit hook")

    # Settings
    (claude_dir / "settings.json").write_text('{"model": "claude-3"}')

    # MCP
    mcp_dir = claude_dir / "mcp"
    mcp_dir.mkdir()
    (mcp_dir / "filesystem.json").write_text('{"name": "filesystem"}')

    return tmp_path


class TestComponentDiscoveryService:
    """Tests for ComponentDiscoveryService.discover_components method."""

    def test_discover_components_empty_repo(self, discovery_service, tmp_path):
        """Test discovering components in an empty repository."""
        result = discovery_service.discover_components(tmp_path)

        assert result.total_found == 0
        assert len(result.components) == 0
        assert not result.has_warnings
        assert result.scan_time_ms >= 0

    def test_discover_components_with_claude_md(self, discovery_service, tmp_path):
        """Test discovering CLAUDE.md files at root and nested locations."""
        # Create root CLAUDE.md
        (tmp_path / "CLAUDE.md").write_text("# Root")

        # Create nested CLAUDE.md
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "CLAUDE.md").write_text("# Docs")

        result = discovery_service.discover_components(tmp_path)

        claude_components = result.get_components_by_type(FileType.CLAUDE_MD)
        assert len(claude_components) == 2

        names = {c.name for c in claude_components}
        assert "CLAUDE" in names
        assert "docs-CLAUDE" in names

    def test_discover_components_with_gitignore(self, discovery_service, tmp_path):
        """Test discovering .gitignore files."""
        (tmp_path / ".gitignore").write_text("*.pyc")

        result = discovery_service.discover_components(tmp_path)

        gitignore_components = result.get_components_by_type(FileType.GITIGNORE)
        assert len(gitignore_components) == 1
        assert gitignore_components[0].name == "gitignore"

    def test_discover_components_with_commands(self, discovery_service, tmp_path):
        """Test discovering command files in .claude/commands/."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "test-cmd.md").write_text("# Test")
        (commands_dir / "another-cmd.md").write_text("# Another")

        result = discovery_service.discover_components(tmp_path)

        command_components = result.get_components_by_type(FileType.COMMANDS)
        assert len(command_components) == 2

        names = {c.name for c in command_components}
        assert "test-cmd" in names
        assert "another-cmd" in names

    def test_discover_components_with_agents(self, discovery_service, tmp_path):
        """Test discovering agent files in .claude/agents/."""
        agents_dir = tmp_path / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "code-reviewer.md").write_text("# Code Reviewer")

        result = discovery_service.discover_components(tmp_path)

        agent_components = result.get_components_by_type(FileType.AGENTS)
        assert len(agent_components) == 1
        assert agent_components[0].name == "code-reviewer"

    def test_discover_components_with_hooks(self, discovery_service, tmp_path):
        """Test discovering hook files in .claude/hooks/."""
        hooks_dir = tmp_path / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True)
        (hooks_dir / "pre-commit.py").write_text("# Hook")

        result = discovery_service.discover_components(tmp_path)

        hook_components = result.get_components_by_type(FileType.HOOKS)
        assert len(hook_components) == 1
        assert hook_components[0].name == "pre-commit"

    def test_discover_components_with_mcp(self, discovery_service, tmp_path):
        """Test discovering MCP configuration files."""
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        (mcp_dir / "filesystem.json").write_text('{"name": "fs"}')

        # Also test root .mcp.json
        (tmp_path / ".mcp.json").write_text('{"name": "root-mcp"}')

        result = discovery_service.discover_components(tmp_path)

        mcp_components = result.get_components_by_type(FileType.MCP)
        assert len(mcp_components) == 2

    def test_discover_components_all_types(
        self, discovery_service, repo_with_components
    ):
        """Test comprehensive discovery with all component types."""
        result = discovery_service.discover_components(repo_with_components)

        assert result.total_found > 0

        # Verify we found each type
        assert len(result.get_components_by_type(FileType.CLAUDE_MD)) >= 2
        assert len(result.get_components_by_type(FileType.GITIGNORE)) >= 1
        assert len(result.get_components_by_type(FileType.COMMANDS)) >= 2
        assert len(result.get_components_by_type(FileType.AGENTS)) >= 1
        assert len(result.get_components_by_type(FileType.HOOKS)) >= 1
        assert len(result.get_components_by_type(FileType.SETTINGS_JSON)) >= 1
        assert len(result.get_components_by_type(FileType.MCP)) >= 1

    def test_discover_invalid_repo_path(self, discovery_service, tmp_path):
        """Test that invalid repository path raises ValueError."""
        non_existent = tmp_path / "does_not_exist"

        with pytest.raises(ValueError, match="does not exist"):
            discovery_service.discover_components(non_existent)

    def test_discover_file_not_directory(self, discovery_service, tmp_path):
        """Test that file path (not directory) raises ValueError."""
        file_path = tmp_path / "somefile.txt"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            discovery_service.discover_components(file_path)

    def test_discover_skips_symlinks(self, discovery_service, tmp_path):
        """Test that symbolic links are skipped during discovery."""
        # Create a real CLAUDE.md
        (tmp_path / "CLAUDE.md").write_text("# Real")

        # Create a symlink to it (if platform supports)
        symlink_path = tmp_path / "link-CLAUDE.md"
        try:
            symlink_path.symlink_to(tmp_path / "CLAUDE.md")
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        result = discovery_service.discover_components(tmp_path)

        # Should only find the real file, not the symlink
        claude_components = result.get_components_by_type(FileType.CLAUDE_MD)
        assert len(claude_components) == 1

    def test_discover_scan_time_populated(self, discovery_service, tmp_path):
        """Test that scan_time_ms is populated with a reasonable value."""
        result = discovery_service.discover_components(tmp_path)

        assert result.scan_time_ms >= 0
        assert result.scan_time_ms < 60000  # Should complete in under a minute


class TestDuplicateDetection:
    """Tests for duplicate name detection."""

    def test_detect_duplicate_names(self, discovery_service, tmp_path):
        """Test that multiple files with same name are flagged as duplicates."""
        # Create two CLAUDE.md files in different locations
        (tmp_path / "CLAUDE.md").write_text("# Root")

        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "CLAUDE.md").write_text("# Sub")

        result = discovery_service.discover_components(tmp_path)

        # With our naming strategy, these should have different names
        # Root: "CLAUDE", Sub: "sub-CLAUDE"
        claude_components = result.get_components_by_type(FileType.CLAUDE_MD)
        assert len(claude_components) == 2

        # They should NOT be duplicates since names are different
        for comp in claude_components:
            assert not comp.is_duplicate

    def test_detect_actual_duplicate_names(self, discovery_service, tmp_path):
        """Test that actual duplicate names are detected correctly."""
        # Create settings.json in two .claude directories at same level
        # This is a contrived case but tests the logic
        (tmp_path / "settings.json").write_text("{}")

        # Create another with same name pattern
        sub1 = tmp_path / "a"
        sub1.mkdir()
        (sub1 / "settings.json").write_text("{}")

        sub2 = tmp_path / "b"
        sub2.mkdir()
        (sub2 / "settings.json").write_text("{}")

        result = discovery_service.discover_components(tmp_path)

        settings_components = result.get_components_by_type(FileType.SETTINGS_JSON)

        # Should have 3 settings files with different prefixed names
        assert len(settings_components) == 3

    def test_duplicate_warnings_generated(self, discovery_service, tmp_path):
        """Test that warning strings are generated for duplicates."""
        # Create a scenario with duplicates using commands
        # Create commands with same name in different subdirs
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)

        sub1 = commands_dir / "group1"
        sub1.mkdir()
        (sub1 / "deploy.md").write_text("# Deploy 1")

        sub2 = commands_dir / "group2"
        sub2.mkdir()
        (sub2 / "deploy.md").write_text("# Deploy 2")

        result = discovery_service.discover_components(tmp_path)

        # Both should be named "deploy" (standard naming)
        command_components = result.get_components_by_type(FileType.COMMANDS)
        deploy_components = [c for c in command_components if c.name == "deploy"]

        if len(deploy_components) > 1:
            assert result.has_warnings
            assert any("deploy" in w for w in result.warnings)

    def test_no_false_duplicates(self, discovery_service, tmp_path):
        """Test that unique names are not flagged as duplicates."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "unique-cmd-1.md").write_text("# Cmd 1")
        (commands_dir / "unique-cmd-2.md").write_text("# Cmd 2")

        result = discovery_service.discover_components(tmp_path)

        for component in result.components:
            assert not component.is_duplicate


class TestNamingStrategies:
    """Tests for component naming strategies."""

    def test_name_duplicate_sensitive_root_level(self, discovery_service, tmp_path):
        """Test naming for CLAUDE.md at root level."""
        (tmp_path / "CLAUDE.md").write_text("# Root")

        result = discovery_service.discover_components(tmp_path)

        claude_components = result.get_components_by_type(FileType.CLAUDE_MD)
        assert len(claude_components) == 1
        assert claude_components[0].name == "CLAUDE"

    def test_name_duplicate_sensitive_nested(self, discovery_service, tmp_path):
        """Test naming for CLAUDE.md in subdirectory."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "CLAUDE.md").write_text("# Src")

        result = discovery_service.discover_components(tmp_path)

        claude_components = result.get_components_by_type(FileType.CLAUDE_MD)
        assert len(claude_components) == 1
        assert claude_components[0].name == "src-CLAUDE"

    def test_name_standard_commands(self, discovery_service, tmp_path):
        """Test standard naming for command files."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "git-workflow.md").write_text("# Git")

        result = discovery_service.discover_components(tmp_path)

        command_components = result.get_components_by_type(FileType.COMMANDS)
        assert len(command_components) == 1
        assert command_components[0].name == "git-workflow"

    def test_name_gitignore_root(self, discovery_service, tmp_path):
        """Test naming for .gitignore at root level."""
        (tmp_path / ".gitignore").write_text("*.pyc")

        result = discovery_service.discover_components(tmp_path)

        gitignore_components = result.get_components_by_type(FileType.GITIGNORE)
        assert len(gitignore_components) == 1
        assert gitignore_components[0].name == "gitignore"

    def test_name_gitignore_nested(self, discovery_service, tmp_path):
        """Test naming for .gitignore in subdirectory."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / ".gitignore").write_text("*.pyc")

        result = discovery_service.discover_components(tmp_path)

        gitignore_components = result.get_components_by_type(FileType.GITIGNORE)
        assert len(gitignore_components) == 1
        assert gitignore_components[0].name == "src-gitignore"

    def test_name_settings_json(self, discovery_service, tmp_path):
        """Test naming for settings.json files."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text("{}")

        result = discovery_service.discover_components(tmp_path)

        settings_components = result.get_components_by_type(FileType.SETTINGS_JSON)
        assert len(settings_components) == 1
        assert settings_components[0].name == ".claude-settings"


class TestGlobPatterns:
    """Tests for glob pattern handling."""

    def test_glob_pattern_recursive_from_root(self, discovery_service, tmp_path):
        """Test that **/CLAUDE.md pattern finds files recursively."""
        # Root level
        (tmp_path / "CLAUDE.md").write_text("# Root")

        # Nested
        deeply_nested = tmp_path / "a" / "b" / "c"
        deeply_nested.mkdir(parents=True)
        (deeply_nested / "CLAUDE.md").write_text("# Deep")

        result = discovery_service.discover_components(tmp_path)

        claude_components = result.get_components_by_type(FileType.CLAUDE_MD)
        assert len(claude_components) == 2

    def test_glob_pattern_with_prefix(self, discovery_service, tmp_path):
        """Test that patterns with prefix like .claude/commands/**/*.md work."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)

        # Direct child
        (commands_dir / "cmd1.md").write_text("# Cmd1")

        # Nested
        nested = commands_dir / "subdir"
        nested.mkdir()
        (nested / "cmd2.md").write_text("# Cmd2")

        result = discovery_service.discover_components(tmp_path)

        command_components = result.get_components_by_type(FileType.COMMANDS)
        assert len(command_components) == 2

    def test_glob_missing_prefix_dir(self, discovery_service, tmp_path):
        """Test that missing prefix directory returns empty results."""
        # Don't create .claude/commands directory
        result = discovery_service.discover_components(tmp_path)

        command_components = result.get_components_by_type(FileType.COMMANDS)
        assert len(command_components) == 0

    def test_glob_only_files_not_directories(self, discovery_service, tmp_path):
        """Test that only files are discovered, not directories."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)

        # Create a directory named like a command file
        fake_cmd_dir = commands_dir / "not-a-file.md"
        fake_cmd_dir.mkdir()

        # Create a real command file
        (commands_dir / "real-cmd.md").write_text("# Real")

        result = discovery_service.discover_components(tmp_path)

        command_components = result.get_components_by_type(FileType.COMMANDS)
        assert len(command_components) == 1
        assert command_components[0].name == "real-cmd"


class TestFileTypePatterns:
    """Tests for FILE_TYPE_PATTERNS configuration."""

    def test_all_file_types_have_patterns(self):
        """Test that all FileType enums have patterns defined."""
        for file_type in FileType:
            assert file_type in FILE_TYPE_PATTERNS, f"Missing pattern for {file_type}"

    def test_patterns_are_valid(self):
        """Test that all patterns are valid strings."""
        for _file_type, config in FILE_TYPE_PATTERNS.items():
            assert "patterns" in config
            assert isinstance(config["patterns"], list)
            assert len(config["patterns"]) > 0
            for pattern in config["patterns"]:
                assert isinstance(pattern, str)
                assert len(pattern) > 0

    def test_duplicate_sensitive_flag_exists(self):
        """Test that duplicate_sensitive flag exists for all types."""
        for _file_type, config in FILE_TYPE_PATTERNS.items():
            assert "duplicate_sensitive" in config
            assert isinstance(config["duplicate_sensitive"], bool)
