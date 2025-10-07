"""Tests for the Initializer class."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from claudefig.config import Config
from claudefig.initializer import Initializer


@pytest.fixture
def mock_config():
    """Create a mock Config object with default settings."""
    config = Mock(spec=Config)
    config.get.side_effect = lambda key, default=None: {
        "claudefig.template_source": "default",
        "init.create_claude_md": True,
        "init.create_contributing": True,
        "init.create_settings": False,
        "custom.template_dir": None,
    }.get(key, default)
    return config


@pytest.fixture
def mock_template_manager():
    """Create a mock TemplateManager."""
    manager = MagicMock()
    manager.read_template_file.return_value = "# Template content"
    return manager


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    return tmp_path


class TestInitializerInit:
    """Tests for Initializer.__init__ method."""

    def test_init_with_config(self, mock_config):
        """Test initialization with provided config."""
        initializer = Initializer(mock_config)
        assert initializer.config is mock_config
        assert initializer.template_manager is not None

    def test_init_without_config(self):
        """Test initialization without config (uses default)."""
        initializer = Initializer()
        assert isinstance(initializer.config, Config)
        assert initializer.template_manager is not None

    @patch("claudefig.initializer.TemplateManager")
    def test_init_with_custom_template_dir(self, mock_tm_class):
        """Test initialization with custom template directory."""
        config = Mock(spec=Config)
        config.get.side_effect = lambda key, default=None: {
            "custom.template_dir": "/custom/templates"
        }.get(key, default)
        initializer = Initializer(config)

        mock_tm_class.assert_called_once_with(Path("/custom/templates"))
        assert initializer.config is config


class TestInitializeMethod:
    """Tests for Initializer.initialize method."""

    @patch("claudefig.initializer.is_git_repository")
    def test_initialize_nonexistent_path(self, mock_is_git, mock_config):
        """Test initialization with non-existent path."""
        mock_is_git.return_value = False
        initializer = Initializer(mock_config)
        non_existent = Path("/nonexistent/path/that/does/not/exist")

        with patch("claudefig.initializer.console.input", return_value="n"):
            result = initializer.initialize(non_existent)

        assert result is False

    @patch("claudefig.initializer.is_git_repository")
    def test_initialize_non_git_repo_user_declines(
        self, mock_is_git, git_repo, mock_config
    ):
        """Test initialization in non-git repo when user declines to continue."""
        mock_is_git.return_value = False
        initializer = Initializer(mock_config)

        with patch("claudefig.initializer.console.input", return_value="n"):
            result = initializer.initialize(git_repo)

        assert result is False

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    @patch.object(Initializer, "_copy_template_file")
    def test_initialize_non_git_repo_user_accepts(
        self, mock_copy, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test initialization in non-git repo when user accepts to continue."""
        mock_is_git.return_value = False
        mock_copy.return_value = True
        initializer = Initializer(mock_config)

        with patch("claudefig.initializer.console.input", return_value="y"):
            with patch.object(Config, "create_default"):
                result = initializer.initialize(git_repo)

        assert result is True
        mock_ensure_dir.assert_called_once()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    @patch.object(Initializer, "_copy_template_file")
    def test_initialize_success_git_repo(
        self, mock_copy, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test successful initialization in git repository."""
        mock_is_git.return_value = True
        mock_copy.return_value = True
        initializer = Initializer(mock_config)

        with patch.object(Config, "create_default"):
            result = initializer.initialize(git_repo)

        assert result is True
        # Verify .claude directory was created
        mock_ensure_dir.assert_called_once_with(git_repo / ".claude")

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    @patch.object(Initializer, "_copy_template_file")
    def test_initialize_creates_expected_files(
        self, mock_copy, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test that initialize creates the expected template files."""
        mock_is_git.return_value = True
        mock_copy.return_value = True
        initializer = Initializer(mock_config)

        with patch.object(Config, "create_default"):
            initializer.initialize(git_repo)

        # Verify template files were copied
        expected_calls = [
            ("default", "CLAUDE.md", git_repo, False),
            ("default", "CONTRIBUTING.md", git_repo, False),
        ]
        actual_calls = [call[0] for call in mock_copy.call_args_list]
        assert actual_calls == expected_calls

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    @patch.object(Initializer, "_copy_template_file")
    def test_initialize_with_force_mode(
        self, mock_copy, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test initialization with force mode enabled."""
        mock_is_git.return_value = True
        mock_copy.return_value = True
        initializer = Initializer(mock_config)

        with patch.object(Config, "create_default"):
            result = initializer.initialize(git_repo, force=True)

        assert result is True
        # Verify force=True was passed to _copy_template_file
        for call in mock_copy.call_args_list:
            assert call[0][3] is True  # force parameter is 4th argument

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_skips_existing_config(
        self, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test that existing .claudefig.toml is not overwritten."""
        mock_is_git.return_value = True
        initializer = Initializer(mock_config)

        # Create existing config file
        config_path = git_repo / ".claudefig.toml"
        config_path.write_text("[claudefig]\ntemplate_source = 'existing'")

        with patch.object(Initializer, "_copy_template_file", return_value=True):
            initializer.initialize(git_repo)

        # Verify config content wasn't changed
        assert config_path.read_text() == "[claudefig]\ntemplate_source = 'existing'"


class TestCopyTemplateFile:
    """Tests for Initializer._copy_template_file method."""

    def test_copy_template_file_success(
        self, tmp_path, mock_config, mock_template_manager
    ):
        """Test successful template file copy."""
        initializer = Initializer(mock_config)
        initializer.template_manager = mock_template_manager

        result = initializer._copy_template_file(
            "default", "TEST_TEMPLATE.md", tmp_path, False
        )

        assert result is True
        dest_file = tmp_path / "TEST_TEMPLATE.md"
        assert dest_file.exists()
        assert dest_file.read_text(encoding="utf-8") == "# Template content"

    def test_copy_template_file_exists_no_force(
        self, tmp_path, mock_config, mock_template_manager
    ):
        """Test copying when file exists without force flag."""
        initializer = Initializer(mock_config)
        initializer.template_manager = mock_template_manager

        existing_file = tmp_path / "TEST_TEMPLATE.md"
        existing_file.write_text("Old existing content", encoding="utf-8")

        result = initializer._copy_template_file(
            "default", "TEST_TEMPLATE.md", tmp_path, False
        )

        assert result is False
        dest_file = tmp_path / "TEST_TEMPLATE.md"
        assert dest_file.read_text(encoding="utf-8") == "Old existing content"
        mock_template_manager.read_template_file.assert_not_called()

    def test_copy_template_file_exists_with_force(
        self, tmp_path, mock_config, mock_template_manager
    ):
        """Test copying when file exists with force flag."""
        initializer = Initializer(mock_config)
        initializer.template_manager = mock_template_manager

        existing_file = tmp_path / "TEST_TEMPLATE.md"
        existing_file.write_text("Old existing content", encoding="utf-8")

        result = initializer._copy_template_file(
            "default", "TEST_TEMPLATE.md", tmp_path, True
        )

        assert result is True
        dest_file = tmp_path / "TEST_TEMPLATE.md"
        assert dest_file.read_text(encoding="utf-8") == "# Template content"
        mock_template_manager.read_template_file.assert_called_once_with(
            "default", "TEST_TEMPLATE.md"
        )

    def test_copy_template_file_not_found(
        self, tmp_path, mock_config, mock_template_manager
    ):
        """Test copying when template file doesn't exist."""
        initializer = Initializer(mock_config)
        initializer.template_manager = mock_template_manager

        mock_template_manager.read_template_file.side_effect = FileNotFoundError()

        result = initializer._copy_template_file(
            "default", "NON_EXISTENT.md", tmp_path, False
        )

        assert result is False
        dest_file = tmp_path / "NON_EXISTENT.md"
        assert not dest_file.exists()
        mock_template_manager.read_template_file.assert_called_once_with(
            "default", "NON_EXISTENT.md"
        )

    def test_copy_template_file_write_error(
        self, tmp_path, mock_config, mock_template_manager
    ):
        """Test handling of write errors during file copy."""
        initializer = Initializer(mock_config)
        initializer.template_manager = mock_template_manager

        with patch.object(
            Path, "write_text", side_effect=PermissionError("Permission denied")
        ):
            result = initializer._copy_template_file(
                "default", "UNWRITABLE_FILE.md", tmp_path, False
            )

        assert result is False
        dest_file = tmp_path / "UNWRITABLE_FILE.md"
        assert not dest_file.exists()
        mock_template_manager.read_template_file.assert_called_once_with(
            "default", "UNWRITABLE_FILE.md"
        )
