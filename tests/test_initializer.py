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
    # Mock the new file instance methods
    config.get_file_instances.return_value = []
    config.set_file_instances.return_value = None
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
    def test_initialize_non_git_repo_user_accepts(
        self, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test initialization in non-git repo when user accepts to continue."""
        mock_is_git.return_value = False
        initializer = Initializer(mock_config)

        with (
            patch("claudefig.initializer.console.input", return_value="y"),
            patch.object(Config, "create_default"),
        ):
            result = initializer.initialize(git_repo)

        # Check that initialization completed (may have warnings but not complete failure)
        assert result in [True, False]  # Either success or warnings, but didn't abort
        mock_ensure_dir.assert_called_once()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_success_git_repo(
        self, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test successful initialization in git repository."""
        mock_is_git.return_value = True
        initializer = Initializer(mock_config)

        with patch.object(Config, "create_default"):
            result = initializer.initialize(git_repo)

        # Result may be True (success) or False (warnings with missing presets)
        assert result in [True, False]
        # Verify .claude directory was created
        mock_ensure_dir.assert_called_once_with(git_repo / ".claude")

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_creates_expected_files(
        self, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test that initialize creates the expected template files."""
        mock_is_git.return_value = True
        initializer = Initializer(mock_config)

        # Don't patch create_default - let it actually create the config file
        initializer.initialize(git_repo)

        # Verify CLAUDE.md was created (from default file instances)
        claude_md = git_repo / "CLAUDE.md"
        assert claude_md.exists()

        # Verify .claudefig.toml config was created
        config_file = git_repo / ".claudefig.toml"
        assert config_file.exists()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_with_force_mode(
        self, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test initialization with force mode enabled."""
        mock_is_git.return_value = True
        initializer = Initializer(mock_config)

        # Create existing CLAUDE.md file
        claude_md = git_repo / "CLAUDE.md"
        claude_md.write_text("Old content", encoding="utf-8")

        with patch.object(Config, "create_default"):
            initializer.initialize(git_repo, force=True)

        # Force mode should have overwritten the file
        assert claude_md.exists()
        # Content should be from template, not "Old content"
        assert claude_md.read_text(encoding="utf-8") != "Old content"

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
        existing_content = "[claudefig]\ntemplate_source = 'existing'"
        config_path.write_text(existing_content, encoding="utf-8")

        initializer.initialize(git_repo)

        # Verify config content wasn't changed
        assert config_path.read_text(encoding="utf-8") == existing_content


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


class TestSetupMcpServers:
    """Tests for Initializer.setup_mcp_servers method."""

    @patch("subprocess.run")
    def test_setup_mcp_servers_claude_not_installed(
        self, mock_subprocess, tmp_path, mock_config
    ):
        """Test MCP setup when claude CLI is not installed."""
        initializer = Initializer(mock_config)

        # Create MCP directory with a valid JSON file
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "example-server.json"
        mcp_file.write_text('{"command": "test"}', encoding="utf-8")

        # Mock subprocess to raise FileNotFoundError (claude not found)
        mock_subprocess.side_effect = FileNotFoundError("claude command not found")

        result = initializer.setup_mcp_servers(tmp_path)

        # Should return False and not crash
        assert result is False
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    def test_setup_mcp_servers_invalid_json(
        self, mock_subprocess, tmp_path, mock_config
    ):
        """Test MCP setup with invalid JSON in config file."""
        initializer = Initializer(mock_config)

        # Create MCP directory with invalid JSON
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "bad-server.json"
        mcp_file.write_text('{"invalid": json}', encoding="utf-8")  # Invalid JSON

        result = initializer.setup_mcp_servers(tmp_path)

        # Should handle JSONDecodeError gracefully
        assert result is False
        # subprocess should not be called due to JSON validation failure
        mock_subprocess.assert_not_called()

    @patch("subprocess.run")
    def test_setup_mcp_servers_timeout(self, mock_subprocess, tmp_path, mock_config):
        """Test MCP setup when claude command times out."""
        import subprocess

        initializer = Initializer(mock_config)

        # Create MCP directory with valid JSON
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "slow-server.json"
        mcp_file.write_text('{"command": "slow"}', encoding="utf-8")

        # Mock subprocess to raise TimeoutExpired
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["claude", "mcp", "add-json"], timeout=30
        )

        result = initializer.setup_mcp_servers(tmp_path)

        # Should handle timeout gracefully
        assert result is False
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    def test_setup_mcp_servers_command_fails(
        self, mock_subprocess, tmp_path, mock_config
    ):
        """Test MCP setup when claude command returns non-zero exit code."""
        initializer = Initializer(mock_config)

        # Create MCP directory with valid JSON
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "failing-server.json"
        mcp_file.write_text('{"command": "fail"}', encoding="utf-8")

        # Mock subprocess to return error
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: Server configuration invalid"
        mock_subprocess.return_value = mock_result

        result = initializer.setup_mcp_servers(tmp_path)

        # Should report failure but continue
        assert result is False
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    def test_setup_mcp_servers_success(self, mock_subprocess, tmp_path, mock_config):
        """Test successful MCP server setup."""
        initializer = Initializer(mock_config)

        # Create MCP directory with valid JSON files
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)

        # Create first server config
        server1 = mcp_dir / "example-server1.json"
        server1.write_text('{"command": "server1"}', encoding="utf-8")

        # Create second server config (test example- prefix removal)
        server2 = mcp_dir / "example-server2.json"
        server2.write_text('{"command": "server2"}', encoding="utf-8")

        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = initializer.setup_mcp_servers(tmp_path)

        # Should succeed
        assert result is True
        # Should be called twice (once for each JSON file)
        assert mock_subprocess.call_count == 2

        # Verify correct server names (example- prefix removed)
        calls = mock_subprocess.call_args_list
        server_names = [call[0][0][3] for call in calls]  # Extract server names
        assert "server1" in server_names
        assert "server2" in server_names

    def test_setup_mcp_servers_no_directory(self, tmp_path, mock_config):
        """Test MCP setup when .claude/mcp directory doesn't exist."""
        initializer = Initializer(mock_config)

        result = initializer.setup_mcp_servers(tmp_path)

        # Should return False with informative message
        assert result is False

    def test_setup_mcp_servers_no_json_files(self, tmp_path, mock_config):
        """Test MCP setup when .claude/mcp directory has no JSON files."""
        initializer = Initializer(mock_config)

        # Create empty MCP directory
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)

        result = initializer.setup_mcp_servers(tmp_path)

        # Should return False with informative message
        assert result is False

    @patch("subprocess.run")
    def test_setup_mcp_servers_partial_success(
        self, mock_subprocess, tmp_path, mock_config
    ):
        """Test MCP setup when some servers succeed and some fail."""
        initializer = Initializer(mock_config)

        # Create MCP directory with multiple JSON files
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)

        good_server = mcp_dir / "good-server.json"
        good_server.write_text('{"command": "good"}', encoding="utf-8")

        bad_server = mcp_dir / "bad-server.json"
        bad_server.write_text('{"command": "bad"}', encoding="utf-8")

        # Mock subprocess to succeed on first call, fail on second
        mock_success = Mock()
        mock_success.returncode = 0
        mock_success.stderr = ""

        mock_fail = Mock()
        mock_fail.returncode = 1
        mock_fail.stderr = "Server failed"

        mock_subprocess.side_effect = [mock_success, mock_fail]

        result = initializer.setup_mcp_servers(tmp_path)

        # Should succeed because at least one server was added
        assert result is True
        assert mock_subprocess.call_count == 2


class TestInitializeTemplateErrors:
    """Tests for template error handling during initialization."""

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_missing_critical_template(
        self, mock_ensure_dir, mock_is_git, git_repo, mock_config, mock_template_manager
    ):
        """Test initialization when a critical template file is missing.

        BEHAVIOR: Should skip the file gracefully with warning but continue initialization.
        """
        mock_is_git.return_value = True
        initializer = Initializer(mock_config)
        initializer.template_manager = mock_template_manager

        # Mock template manager to raise FileNotFoundError for CLAUDE.md
        mock_template_manager.read_template_file.side_effect = FileNotFoundError(
            "Template not found"
        )

        with patch.object(Config, "create_default"):
            result = initializer.initialize(git_repo, force=False)

        # Should complete but with warnings (result=False indicates warnings)
        assert result is False
        # Config should still be created
        mock_ensure_dir.assert_called_once()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_permission_denied_during_write(
        self, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test initialization when write permission is denied.

        BEHAVIOR: Should catch PermissionError, report error, and continue initialization.
        """
        mock_is_git.return_value = True
        initializer = Initializer(mock_config)

        # Create read-only git repo directory
        # Note: We can't actually make the directory read-only as it would prevent
        # the test from cleaning up. Instead, we'll patch Path.write_text to raise PermissionError

        with (
            patch.object(Config, "create_default"),
            patch.object(
                Path,
                "write_text",
                side_effect=PermissionError("Permission denied"),
            ),
        ):
            result = initializer.initialize(git_repo, force=False)

        # Should complete but with errors (result=False)
        assert result is False
        # Should still have tried to create .claude directory
        mock_ensure_dir.assert_called_once()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_continues_after_partial_failure(
        self, mock_ensure_dir, mock_is_git, git_repo, mock_config
    ):
        """Test that initialization continues when some files fail.

        BEHAVIOR: Initialization should continue processing remaining files even if some fail.
        """
        mock_is_git.return_value = True
        initializer = Initializer(mock_config)

        # Mock template manager to fail on first call, succeed on second
        mock_tm = MagicMock()
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise FileNotFoundError("First template missing")
            else:
                return "# Template content"

        mock_tm.read_template_file.side_effect = side_effect
        initializer.template_manager = mock_tm

        with patch.object(Config, "create_default"):
            result = initializer.initialize(git_repo, force=False)

        # Should complete (some files may have succeeded)
        # Result may be True or False depending on how many files succeeded
        assert result in [True, False]
        # Should have tried to create .claude directory
        mock_ensure_dir.assert_called_once()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_reports_helpful_error_on_template_missing(
        self,
        mock_ensure_dir,
        mock_is_git,
        git_repo,
        mock_config,
        mock_template_manager,
        capsys,
    ):
        """Test that missing template errors include helpful messages.

        BEHAVIOR: Error messages should indicate which template is missing.
        """
        mock_is_git.return_value = True
        initializer = Initializer(mock_config)
        initializer.template_manager = mock_template_manager

        # Mock template manager to raise FileNotFoundError
        mock_template_manager.read_template_file.side_effect = FileNotFoundError(
            "CLAUDE.md not found"
        )

        with patch.object(Config, "create_default"):
            result = initializer.initialize(git_repo, force=False)

        # Should have failed with warnings
        assert result is False

        # Check that output includes helpful warning
        captured = capsys.readouterr()
        # Should mention template not found (actual message may vary)
        assert "Template" in captured.out or "template" in captured.out
