"""Tests for .claude/ directory feature generation."""

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
def mock_template_manager():
    """Create a mock TemplateManager that returns test content."""
    manager = MagicMock()
    manager.read_template_file.return_value = "# Test content"
    return manager


class TestClaudeDirectorySetup:
    """Tests for _setup_claude_directory method."""

    def test_no_features_enabled(self, git_repo, mock_template_manager):
        """Test that nothing is created when all features are disabled."""
        config = Config()
        config.data["claude"] = {
            "create_settings": False,
            "create_settings_local": False,
            "create_commands": False,
            "create_agents": False,
            "create_hooks": False,
            "create_output_styles": False,
            "create_statusline": False,
            "create_mcp": False,
        }

        initializer = Initializer(config)
        initializer.template_manager = mock_template_manager

        claude_dir = git_repo / ".claude"
        claude_dir.mkdir()

        initializer._setup_claude_directory(claude_dir, "default", force=False)

        # Verify no files were created (only the directory exists)
        assert claude_dir.exists()
        assert len(list(claude_dir.iterdir())) == 0

    def test_create_settings_json(self, git_repo, mock_template_manager):
        """Test creating settings.json."""
        config = Config()
        config.data["claude"] = {"create_settings": True}

        initializer = Initializer(config)
        initializer.template_manager = mock_template_manager

        claude_dir = git_repo / ".claude"
        claude_dir.mkdir()

        initializer._setup_claude_directory(claude_dir, "default", force=False)

        settings_file = claude_dir / "settings.json"
        assert settings_file.exists()
        assert settings_file.read_text() == "# Test content"

    def test_create_settings_local_json(self, git_repo, mock_template_manager):
        """Test creating settings.local.json."""
        config = Config()
        config.data["claude"] = {"create_settings_local": True}

        initializer = Initializer(config)
        initializer.template_manager = mock_template_manager

        claude_dir = git_repo / ".claude"
        claude_dir.mkdir()

        initializer._setup_claude_directory(claude_dir, "default", force=False)

        settings_local_file = claude_dir / "settings.local.json"
        assert settings_local_file.exists()

    @patch("claudefig.initializer.Initializer._copy_template_directory")
    def test_create_commands_directory(
        self, mock_copy_dir, git_repo, mock_template_manager
    ):
        """Test creating commands directory."""
        config = Config()
        config.data["claude"] = {"create_commands": True}

        initializer = Initializer(config)
        initializer.template_manager = mock_template_manager

        claude_dir = git_repo / ".claude"
        claude_dir.mkdir()

        initializer._setup_claude_directory(claude_dir, "default", force=False)

        # Verify _copy_template_directory was called for commands
        assert mock_copy_dir.called
        args = mock_copy_dir.call_args_list[0][0]
        assert "claude/commands" in args

    @patch("claudefig.initializer.Initializer._copy_template_directory")
    def test_create_agents_directory(
        self, mock_copy_dir, git_repo, mock_template_manager
    ):
        """Test creating agents directory."""
        config = Config()
        config.data["claude"] = {"create_agents": True}

        initializer = Initializer(config)
        initializer.template_manager = mock_template_manager

        claude_dir = git_repo / ".claude"
        claude_dir.mkdir()

        initializer._setup_claude_directory(claude_dir, "default", force=False)

        # Verify _copy_template_directory was called for agents
        assert mock_copy_dir.called
        args = mock_copy_dir.call_args_list[0][0]
        assert "claude/agents" in args

    def test_create_statusline_executable(self, git_repo, mock_template_manager):
        """Test creating statusline.sh and making it executable."""
        import sys

        config = Config()
        config.data["claude"] = {"create_statusline": True}

        initializer = Initializer(config)
        initializer.template_manager = mock_template_manager

        claude_dir = git_repo / ".claude"
        claude_dir.mkdir()

        initializer._setup_claude_directory(claude_dir, "default", force=False)

        statusline_file = claude_dir / "statusline.sh"
        assert statusline_file.exists()

        # Check if file is executable (only on Unix systems)
        if sys.platform != "win32":
            import stat

            st = statusline_file.stat()
            assert st.st_mode & stat.S_IXUSR  # User execute permission

    def test_multiple_features_enabled(self, git_repo, mock_template_manager):
        """Test creating multiple features at once."""
        config = Config()
        config.data["claude"] = {
            "create_settings": True,
            "create_settings_local": True,
            "create_statusline": True,
        }

        initializer = Initializer(config)
        initializer.template_manager = mock_template_manager

        claude_dir = git_repo / ".claude"
        claude_dir.mkdir()

        initializer._setup_claude_directory(claude_dir, "default", force=False)

        # Verify all files were created
        assert (claude_dir / "settings.json").exists()
        assert (claude_dir / "settings.local.json").exists()
        assert (claude_dir / "statusline.sh").exists()


class TestCopyTemplateDirectory:
    """Tests for _copy_template_directory method."""

    @patch("importlib.resources.files")
    def test_copy_directory_not_found(self, mock_files, git_repo):
        """Test handling of non-existent template directory."""
        # Make template_root.joinpath() raise FileNotFoundError
        mock_template_root = MagicMock()
        mock_template_root.joinpath.side_effect = FileNotFoundError
        mock_files.return_value.joinpath.return_value = mock_template_root

        config = Config()
        initializer = Initializer(config)

        dest_dir = git_repo / "commands"
        result = initializer._copy_template_directory(
            "default", "claude/commands", dest_dir, force=False
        )

        assert result is False
