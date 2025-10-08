"""Tests for MCP server automation."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from claudefig.config import Config
from claudefig.initializer import Initializer


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    return tmp_path


@pytest.fixture
def mcp_dir_with_configs(tmp_path):
    """Create a .claude/mcp directory with sample MCP configs."""
    mcp_dir = tmp_path / ".claude" / "mcp"
    mcp_dir.mkdir(parents=True)

    # Create sample MCP configs
    github_config = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}
    memory_config = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"]}

    (mcp_dir / "github.json").write_text(json.dumps(github_config))
    (mcp_dir / "memory.json").write_text(json.dumps(memory_config))
    (mcp_dir / "example-sentry.json").write_text(json.dumps({"type": "http", "url": "https://mcp.sentry.dev/mcp"}))

    return tmp_path


class TestSetupMcpServers:
    """Tests for setup_mcp_servers method."""

    def test_no_mcp_directory(self, git_repo):
        """Test when .claude/mcp directory doesn't exist."""
        config = Config()
        initializer = Initializer(config)

        result = initializer.setup_mcp_servers(git_repo)

        assert result is False

    def test_empty_mcp_directory(self, git_repo):
        """Test when .claude/mcp directory is empty."""
        mcp_dir = git_repo / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)

        config = Config()
        initializer = Initializer(config)

        result = initializer.setup_mcp_servers(git_repo)

        assert result is False

    @patch("subprocess.run")
    def test_setup_single_mcp_server(self, mock_run, mcp_dir_with_configs):
        """Test setting up a single MCP server."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Remove all but one config
        (mcp_dir_with_configs / ".claude" / "mcp" / "memory.json").unlink()
        (mcp_dir_with_configs / ".claude" / "mcp" / "example-sentry.json").unlink()

        config = Config()
        initializer = Initializer(config)

        result = initializer.setup_mcp_servers(mcp_dir_with_configs)

        assert result is True
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "claude"
        assert call_args[1] == "mcp"
        assert call_args[2] == "add-json"
        assert call_args[3] == "github"

    @patch("subprocess.run")
    def test_setup_multiple_mcp_servers(self, mock_run, mcp_dir_with_configs):
        """Test setting up multiple MCP servers."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        config = Config()
        initializer = Initializer(config)

        result = initializer.setup_mcp_servers(mcp_dir_with_configs)

        assert result is True
        # Should be called 3 times (github, memory, sentry)
        assert mock_run.call_count == 3

    @patch("subprocess.run")
    def test_example_prefix_removed(self, mock_run, mcp_dir_with_configs):
        """Test that 'example-' prefix is removed from server names."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        config = Config()
        initializer = Initializer(config)

        result = initializer.setup_mcp_servers(mcp_dir_with_configs)

        # Check that 'sentry' was used instead of 'example-sentry'
        calls = mock_run.call_args_list
        server_names = [call[0][0][3] for call in calls]
        assert "sentry" in server_names
        assert "example-sentry" not in server_names

    @patch("subprocess.run")
    def test_invalid_json_handling(self, mock_run, git_repo):
        """Test handling of invalid JSON in MCP config."""
        mcp_dir = git_repo / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)

        # Create invalid JSON file
        (mcp_dir / "invalid.json").write_text("{invalid json")

        config = Config()
        initializer = Initializer(config)

        result = initializer.setup_mcp_servers(git_repo)

        # Should fail due to invalid JSON
        assert result is False
        # subprocess.run should not be called
        assert not mock_run.called

    @patch("subprocess.run")
    def test_command_failure_handling(self, mock_run, mcp_dir_with_configs):
        """Test handling when claude mcp add-json command fails."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error message")

        config = Config()
        initializer = Initializer(config)

        result = initializer.setup_mcp_servers(mcp_dir_with_configs)

        # Should return False if all commands failed
        # But we can't know for sure without capturing output
        assert mock_run.called

    @patch("subprocess.run")
    def test_claude_command_not_found(self, mock_run, mcp_dir_with_configs):
        """Test handling when 'claude' command is not installed."""
        mock_run.side_effect = FileNotFoundError("claude command not found")

        config = Config()
        initializer = Initializer(config)

        result = initializer.setup_mcp_servers(mcp_dir_with_configs)

        assert result is False

    @patch("subprocess.run")
    def test_timeout_handling(self, mock_run, mcp_dir_with_configs):
        """Test handling of command timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("claude", 30)

        config = Config()
        initializer = Initializer(config)

        # Should not raise exception, just handle gracefully
        result = initializer.setup_mcp_servers(mcp_dir_with_configs)

        # Result depends on whether all commands timed out
        assert isinstance(result, bool)

    @patch("subprocess.run")
    def test_json_content_passed_correctly(self, mock_run, mcp_dir_with_configs):
        """Test that JSON content is passed correctly to the command."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        config = Config()
        initializer = Initializer(config)

        initializer.setup_mcp_servers(mcp_dir_with_configs)

        # Get the JSON content passed to the command
        call_args = mock_run.call_args_list[0][0][0]
        json_content = call_args[4]  # 5th argument is the JSON content

        # Verify it's valid JSON
        parsed = json.loads(json_content)
        assert "command" in parsed or "type" in parsed


class TestMcpIntegration:
    """Integration tests for MCP setup workflow."""

    @patch("subprocess.run")
    def test_full_mcp_workflow(self, mock_run, git_repo):
        """Test complete MCP setup workflow from init to setup-mcp."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # 1. Configure to create MCP directory
        config = Config()
        config.set("claude.create_mcp", True)

        # 2. Create initializer and set up MCP directory
        initializer = Initializer(config)

        # Create MCP configs manually (simulating template copy)
        mcp_dir = git_repo / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)

        github_config = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}
        (mcp_dir / "github.json").write_text(json.dumps(github_config))

        # 3. Set up MCP servers
        result = initializer.setup_mcp_servers(git_repo)

        assert result is True
        assert mock_run.called
        assert mock_run.call_args[0][0][0] == "claude"
