"""Tests for main CLI commands (init, show, add-template, list-templates)."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from claudefig.cli import main


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a mock git repository."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    return tmp_path


class TestInit:
    """Tests for 'claudefig init' command."""

    @patch("claudefig.config.Config")
    @patch("claudefig.initializer.Initializer")
    def test_init_in_git_repo_success(
        self, mock_initializer_class, mock_config_class, cli_runner, tmp_path
    ):
        """Test successful initialization in a git repository."""
        # Mock Config
        mock_cfg = Mock()
        mock_config_class.return_value = mock_cfg

        # Mock successful initialization
        mock_initializer = Mock()
        mock_initializer.initialize.return_value = True
        mock_initializer_class.return_value = mock_initializer

        result = cli_runner.invoke(main, ["init", "--path", str(tmp_path)])

        # Test invokes CLI and shows initialization message
        assert (
            "Initializing Claude Code configuration" in result.output
            or "init" in result.output.lower()
        )

    @patch("claudefig.config.Config")
    @patch("claudefig.initializer.Initializer")
    def test_init_with_force_flag(
        self, mock_initializer_class, mock_config_class, cli_runner, tmp_path
    ):
        """Test initialization with force flag enabled."""
        # Mock Config
        mock_cfg = Mock()
        mock_config_class.return_value = mock_cfg

        mock_initializer = Mock()
        mock_initializer.initialize.return_value = True
        mock_initializer_class.return_value = mock_initializer

        result = cli_runner.invoke(main, ["init", "--path", str(tmp_path), "--force"])

        # Test includes force flag message or runs without error
        assert "Force mode enabled" in result.output or "Initializing" in result.output

    @patch("claudefig.config.Config")
    @patch("claudefig.initializer.Initializer")
    def test_init_with_warnings(
        self, mock_initializer_class, mock_config_class, cli_runner, tmp_path
    ):
        """Test initialization that completes with warnings."""
        # Mock Config
        mock_cfg = Mock()
        mock_config_class.return_value = mock_cfg

        # Initialize returns False to indicate warnings
        mock_initializer = Mock()
        mock_initializer.initialize.return_value = False
        mock_initializer_class.return_value = mock_initializer

        result = cli_runner.invoke(main, ["init", "--path", str(tmp_path)])

        # Should exit with abort due to warnings
        assert result.exit_code == 1

    @patch("claudefig.config.Config")
    @patch("claudefig.initializer.Initializer")
    def test_init_failure_with_exception(
        self, mock_initializer_class, mock_config_class, cli_runner, tmp_path
    ):
        """Test initialization failure with exception."""
        # Mock Config
        mock_cfg = Mock()
        mock_config_class.return_value = mock_cfg

        mock_initializer = Mock()
        mock_initializer.initialize.side_effect = RuntimeError("Init failed")
        mock_initializer_class.return_value = mock_initializer

        result = cli_runner.invoke(main, ["init", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_init_default_path_uses_current_directory(self, cli_runner, tmp_path):
        """Test that init without --path uses current directory."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create .git to simulate git repo
            (Path.cwd() / ".git").mkdir()

            with (
                patch("claudefig.config.Config") as mock_config_class,
                patch("claudefig.initializer.Initializer") as mock_init_class,
            ):
                mock_cfg = Mock()
                mock_config_class.return_value = mock_cfg

                mock_init = Mock()
                mock_init.initialize.return_value = True
                mock_init_class.return_value = mock_init

                result = cli_runner.invoke(main, ["init"])

                # Should attempt initialization
                assert "Initializing" in result.output or mock_init.initialize.called


class TestShow:
    """Tests for 'claudefig show' command."""

    def test_show_with_config_file(self, cli_runner, tmp_path):
        """Test show command when config file exists."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create a config file in the isolated filesystem
            config_path = Path.cwd() / "claudefig.toml"
            config_path.write_text(
                """
[claudefig]
version = "2.0"
schema_version = "2.0"
template_source = "default"

[[files]]
id = "test-file"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true
""",
                encoding="utf-8",
            )

            result = cli_runner.invoke(main, ["show"])

            assert result.exit_code == 0
            assert "Current Configuration" in result.output
            assert "claudefig.toml" in result.output or "Config file" in result.output

    @patch("claudefig.services.config_service.find_config_path")
    def test_show_without_config_file(self, mock_find_config, cli_runner, tmp_path):
        """Test show command when no config file exists."""
        # Mock find_config_path to return None, preventing fallback to user home config
        mock_find_config.return_value = None

        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["show"])

            assert result.exit_code == 0
            assert "Current Configuration" in result.output
            assert "No config file found" in result.output

    def test_show_displays_file_instances(self, cli_runner, tmp_path):
        """Test that show command displays file instance summary."""
        config_path = tmp_path / "claudefig.toml"
        config_path.write_text(
            """
[claudefig]
version = "2.0"
schema_version = "2.0"

[[files]]
id = "claude-default"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true

[[files]]
id = "settings-default"
type = "settings_json"
preset = "settings_json:default"
path = ".claude/settings.json"
enabled = false
""",
            encoding="utf-8",
        )

        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["show"])

            assert result.exit_code == 0
            assert "File Instances" in result.output

    def test_show_with_exception(self, cli_runner, tmp_path):
        """Test show command error handling with invalid TOML."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create invalid TOML config
            config_path = Path.cwd() / "claudefig.toml"
            config_path.write_text("invalid toml {", encoding="utf-8")

            result = cli_runner.invoke(main, ["show"])

            # With new architecture, invalid TOML falls back to defaults (resilient behavior)
            assert result.exit_code == 0
            assert "Current Configuration" in result.output
            # Should still show config file was found (check for config section)
            assert "Config file:" in result.output or "Schema Version" in result.output
            # Should show default values (fallback behavior)
            assert "Schema Version" in result.output
            assert "2.0" in result.output


class TestMainGroup:
    """Tests for main command group behavior."""

    def test_main_without_subcommand_launches_interactive(self, cli_runner):
        """Test that running claudefig without subcommand launches interactive mode."""
        with patch("claudefig.tui.ClaudefigApp") as mock_app_class:
            mock_app = Mock()
            mock_app_class.return_value = mock_app

            cli_runner.invoke(main, [])

            # Should have attempted to launch TUI
            mock_app.run.assert_called_once()

    def test_main_version_option(self, cli_runner):
        """Test --version flag displays version."""
        result = cli_runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "claudefig" in result.output

    def test_main_with_verbose_flag(self, cli_runner, tmp_path):
        """Test that --verbose flag is processed."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            (Path.cwd() / ".git").mkdir()

            with (
                patch("claudefig.config.Config") as mock_config_class,
                patch("claudefig.initializer.Initializer") as mock_init_class,
            ):
                mock_cfg = Mock()
                mock_config_class.return_value = mock_cfg

                mock_init = Mock()
                mock_init.initialize.return_value = True
                mock_init_class.return_value = mock_init

                result = cli_runner.invoke(main, ["--verbose", "init"])

                # Should process verbose flag
                assert "init" in result.output.lower() or mock_init.initialize.called

    def test_main_with_quiet_flag(self, cli_runner, tmp_path):
        """Test that --quiet flag is processed."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            (Path.cwd() / ".git").mkdir()

            with (
                patch("claudefig.config.Config") as mock_config_class,
                patch("claudefig.initializer.Initializer") as mock_init_class,
            ):
                mock_cfg = Mock()
                mock_config_class.return_value = mock_cfg

                mock_init = Mock()
                mock_init.initialize.return_value = True
                mock_init_class.return_value = mock_init

                result = cli_runner.invoke(main, ["--quiet", "init"])

                # Should process quiet flag
                assert mock_init.initialize.called or "init" in result.output.lower()

    def test_main_with_verbose_and_quiet_shows_warning(self, cli_runner, tmp_path):
        """Test that using both --verbose and --quiet shows warning."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            (Path.cwd() / ".git").mkdir()

            with patch("claudefig.initializer.Initializer") as mock_init_class:
                mock_init = Mock()
                mock_init.initialize.return_value = True
                mock_init_class.return_value = mock_init

                result = cli_runner.invoke(main, ["--verbose", "--quiet", "init"])

                # Should warn about conflicting flags
                assert (
                    "Warning" in result.output or "cannot use" in result.output.lower()
                )
