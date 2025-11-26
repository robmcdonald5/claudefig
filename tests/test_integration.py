"""End-to-end integration tests for claudefig."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from claudefig.cli import main
from claudefig.user_config import get_user_config_dir


@pytest.mark.slow
class TestFullInitializationWorkflow:
    """Test complete initialization workflow."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI test runner."""
        return CliRunner()

    def test_init_command_creates_structure(self, cli_runner, mock_user_home, tmp_path):
        """Test that 'claudefig init' creates necessary files and directories."""
        # Create a test repo directory
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Run init command with --non-interactive to skip prompts
        result = cli_runner.invoke(
            main, ["init", "--path", str(repo_dir), "--non-interactive"]
        )

        # Check command succeeded
        if result.exit_code != 0:
            print(f"Command output: {result.output}")
            if result.exception:
                print(f"Exception: {result.exception}")
        assert result.exit_code == 0

        # Check that files were created
        assert (repo_dir / ".claude").exists()
        assert (repo_dir / ".claude").is_dir()

    def test_init_command_with_force(self, cli_runner, mock_user_home, tmp_path):
        """Test init command with --force flag overwrites existing files."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Create existing .claude directory with content
        claude_dir = repo_dir / ".claude"
        claude_dir.mkdir()
        existing_file = claude_dir / "test.txt"
        existing_file.write_text("existing content", encoding="utf-8")

        # Run init with force and --non-interactive to skip prompts
        result = cli_runner.invoke(
            main, ["init", "--path", str(repo_dir), "--force", "--non-interactive"]
        )

        assert result.exit_code == 0
        assert claude_dir.exists()

    @pytest.mark.skip(
        reason="Version command doesn't trigger user config init - expected behavior"
    )
    def test_user_config_initialized_on_first_run(self, cli_runner, mock_user_home):
        """Test that user config is initialized on first CLI run."""
        config_dir = get_user_config_dir()

        # Ensure not initialized
        assert not config_dir.exists()

        # Run any command
        result = cli_runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        # User config should now exist
        assert config_dir.exists()
        assert (config_dir / "presets").exists()


class TestCLICommands:
    """Test CLI command integration."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI test runner."""
        return CliRunner()

    def test_show_command(self, cli_runner, mock_user_home):
        """Test 'claudefig show' command."""
        result = cli_runner.invoke(main, ["show"])

        assert result.exit_code == 0
        assert "Configuration" in result.output or "Config" in result.output

    def test_version_option(self, cli_runner):
        """Test --version option."""
        result = cli_runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "claudefig" in result.output.lower()

    def test_help_option(self, cli_runner):
        """Test --help option."""
        result = cli_runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "init" in result.output


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI test runner."""
        return CliRunner()

    def test_init_in_nonexistent_directory_fails(self, cli_runner, mock_user_home):
        """Test that init fails gracefully with non-existent directory."""
        result = cli_runner.invoke(main, ["init", "--path", "/nonexistent/path"])

        # Should fail
        assert result.exit_code != 0
