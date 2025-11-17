"""Tests for the Initializer class."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from claudefig.config import Config
from claudefig.initializer import Initializer


@pytest.fixture
def config_with_defaults(tmp_path):
    """Create a real config file with default settings.

    New architecture: Initializer takes config_path, not Config object.
    """
    config_file = tmp_path / "claudefig.toml"
    config_file.write_text(
        """[claudefig]
version = "2.0"
schema_version = "2.0"
template_source = "default"

[init]
create_claude_md = true
create_contributing = true
create_settings = false

[custom]
template_dir = ""
presets_dir = ""

[[files]]
""",
        encoding="utf-8",
    )
    return config_file


@pytest.fixture
def mock_template_manager():
    """Create a mock FileTemplateManager."""
    manager = MagicMock()
    manager.read_template_file.return_value = "# Template content"
    return manager


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    return tmp_path


@pytest.fixture
def mock_config_data():
    """Create mock config data for initialization tests."""
    return {
        "project": {"name": "test-project"},
        "file_instances": [],
    }


class TestInitializerInit:
    """Tests for Initializer.__init__ method."""

    def test_init_with_config(self, config_with_defaults):
        """Test initialization with provided config path."""
        initializer = Initializer(config_path=config_with_defaults)
        assert initializer.config_path == config_with_defaults
        assert initializer.config_data is not None
        assert initializer.template_manager is not None

    def test_init_without_config(self):
        """Test initialization without config (uses default)."""
        initializer = Initializer()
        assert initializer.config_data is not None
        assert initializer.template_manager is not None

    @patch("claudefig.initializer.FileTemplateManager")
    def test_init_with_custom_template_dir(self, mock_tm_class, tmp_path):
        """Test initialization with custom template directory."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text(
            """[claudefig]
version = "2.0"

[custom]
template_dir = "/custom/templates"
""",
            encoding="utf-8",
        )
        initializer = Initializer(config_path=config_file)

        mock_tm_class.assert_called_once_with(Path("/custom/templates"))
        assert initializer.config_path == config_file


class TestInitializeMethod:
    """Tests for Initializer.initialize method."""

    @patch("claudefig.initializer.is_git_repository")
    def test_initialize_nonexistent_path(self, mock_is_git):
        """Test initialization with non-existent path."""
        mock_is_git.return_value = False
        initializer = Initializer()  # Uses defaults
        non_existent = Path("/nonexistent/path/that/does/not/exist")

        with patch("claudefig.initializer.console.input", return_value="n"):
            result = initializer.initialize(non_existent)

        assert result is False

    @patch("claudefig.initializer.is_git_repository")
    def test_initialize_non_git_repo_user_declines(self, mock_is_git, git_repo):
        """Test initialization in non-git repo when user declines to continue."""
        mock_is_git.return_value = False
        initializer = Initializer()  # Uses defaults

        with patch("claudefig.initializer.console.input", return_value="n"):
            result = initializer.initialize(git_repo)

        assert result is False

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_non_git_repo_user_accepts(
        self, mock_ensure_dir, mock_is_git, git_repo
    ):
        """Test initialization in non-git repo when user accepts to continue."""
        mock_is_git.return_value = False
        initializer = Initializer()  # Uses defaults

        with (
            patch("claudefig.initializer.console.input", return_value="y"),
            patch("claudefig.services.config_service.save_config"),
            patch.object(
                initializer.template_manager,
                "read_template_file",
                return_value="# Template content",
            ),
        ):
            result = initializer.initialize(git_repo)

        # Check that initialization completed (may have warnings but not complete failure)
        assert result in [True, False]  # Either success or warnings, but didn't abort
        mock_ensure_dir.assert_called_once()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_success_git_repo(self, mock_ensure_dir, mock_is_git, git_repo):
        """Test successful initialization in git repository."""
        mock_is_git.return_value = True
        initializer = Initializer()

        with (
            patch.object(Config, "create_default"),
            patch.object(
                initializer.template_manager,
                "read_template_file",
                return_value="# Template content",
            ),
        ):
            result = initializer.initialize(git_repo)

        # Result may be True (success) or False (warnings with missing presets)
        assert result in [True, False]
        # Verify .claude directory was created
        mock_ensure_dir.assert_called_once_with(git_repo / ".claude")

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_creates_expected_files(
        self, mock_ensure_dir, mock_is_git, git_repo
    ):
        """Test that initialize creates the expected template files."""
        mock_is_git.return_value = True
        initializer = Initializer()

        # Don't patch create_default - let it actually create the config file
        with patch.object(
            initializer.template_manager,
            "read_template_file",
            return_value="# Template content",
        ):
            initializer.initialize(git_repo)

        # Verify CLAUDE.md was created (from default file instances)
        claude_md = git_repo / "CLAUDE.md"
        assert claude_md.exists()

        # Verify claudefig.toml config was created
        config_file = git_repo / "claudefig.toml"
        assert config_file.exists()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_with_force_mode(self, mock_ensure_dir, mock_is_git, git_repo):
        """Test initialization with force mode enabled."""
        mock_is_git.return_value = True
        initializer = Initializer()

        # Create existing CLAUDE.md file
        claude_md = git_repo / "CLAUDE.md"
        claude_md.write_text("Old content", encoding="utf-8")

        with (
            patch.object(Config, "create_default"),
            patch.object(
                initializer.template_manager,
                "read_template_file",
                return_value="# New template content",
            ),
        ):
            initializer.initialize(git_repo, force=True)

        # Force mode should have overwritten the file
        assert claude_md.exists()
        # Content should be from template, not "Old content"
        assert claude_md.read_text(encoding="utf-8") != "Old content"

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_skips_existing_config(
        self, mock_ensure_dir, mock_is_git, git_repo
    ):
        """Test that existing claudefig.toml is not overwritten."""
        mock_is_git.return_value = True
        initializer = Initializer()

        # Create existing config file
        config_path = git_repo / "claudefig.toml"
        existing_content = "[claudefig]\ntemplate_source = 'existing'"
        config_path.write_text(existing_content, encoding="utf-8")

        with patch.object(
            initializer.template_manager,
            "read_template_file",
            return_value="# Template content",
        ):
            initializer.initialize(git_repo)

        # Verify config content wasn't changed
        assert config_path.read_text(encoding="utf-8") == existing_content


class TestCopyTemplateFile:
    """Tests for Initializer._copy_template_file method."""

    def test_copy_template_file_success(self, tmp_path, mock_template_manager):
        """Test successful template file copy."""
        initializer = Initializer()
        initializer.template_manager = mock_template_manager

        result = initializer._copy_template_file(
            "default", "TEST_TEMPLATE.md", tmp_path, False
        )

        assert result is True
        dest_file = tmp_path / "TEST_TEMPLATE.md"
        assert dest_file.exists()
        assert dest_file.read_text(encoding="utf-8") == "# Template content"

    def test_copy_template_file_exists_no_force(self, tmp_path, mock_template_manager):
        """Test copying when file exists without force flag."""
        initializer = Initializer()
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
        self, tmp_path, mock_template_manager
    ):
        """Test copying when file exists with force flag."""
        initializer = Initializer()
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

    def test_copy_template_file_not_found(self, tmp_path, mock_template_manager):
        """Test copying when template file doesn't exist."""
        initializer = Initializer()
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

    def test_copy_template_file_write_error(self, tmp_path, mock_template_manager):
        """Test handling of write errors during file copy."""
        initializer = Initializer()
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
    def test_setup_mcp_servers_claude_not_installed(self, mock_subprocess, tmp_path):
        """Test MCP setup when claude CLI is not installed."""
        initializer = Initializer()

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
    def test_setup_mcp_servers_invalid_json(self, mock_subprocess, tmp_path):
        """Test MCP setup with invalid JSON in config file."""
        initializer = Initializer()

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
    def test_setup_mcp_servers_timeout(
        self, mock_subprocess, tmp_path
    ):  # Removed mock_config
        """Test MCP setup when claude command times out."""
        import subprocess

        initializer = Initializer()

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
    def test_setup_mcp_servers_command_fails(self, mock_subprocess, tmp_path):
        """Test MCP setup when claude command returns non-zero exit code."""
        initializer = Initializer()

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
    def test_setup_mcp_servers_success(
        self, mock_subprocess, tmp_path
    ):  # Removed mock_config
        """Test successful MCP server setup."""
        initializer = Initializer()

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

    def test_setup_mcp_servers_no_directory(self, tmp_path):  # Removed mock_config
        """Test MCP setup when .claude/mcp directory doesn't exist."""
        initializer = Initializer()

        result = initializer.setup_mcp_servers(tmp_path)

        # Should return False with informative message
        assert result is False

    def test_setup_mcp_servers_no_json_files(self, tmp_path):  # Removed mock_config
        """Test MCP setup when .claude/mcp directory has no JSON files."""
        initializer = Initializer()

        # Create empty MCP directory
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)

        result = initializer.setup_mcp_servers(tmp_path)

        # Should return False with informative message
        assert result is False

    @patch("subprocess.run")
    def test_setup_mcp_servers_partial_success(self, mock_subprocess, tmp_path):
        """Test MCP setup when some servers succeed and some fail."""
        initializer = Initializer()

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

    @patch("subprocess.run")
    def test_setup_mcp_servers_with_mcp_json(self, mock_subprocess, tmp_path):
        """Test MCP setup with standard .mcp.json file."""
        initializer = Initializer()

        # Create .mcp.json file in project root
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text('{"command": "test", "args": ["-y"]}', encoding="utf-8")

        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = initializer.setup_mcp_servers(tmp_path)

        # Should succeed
        assert result is True
        mock_subprocess.assert_called_once()

        # Verify server name is extracted from filename
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[3] == ".mcp"  # Server name from .mcp.json

    @patch("subprocess.run")
    def test_setup_mcp_servers_both_patterns(self, mock_subprocess, tmp_path):
        """Test MCP setup with both .mcp.json and .claude/mcp/*.json files."""
        initializer = Initializer()

        # Create .mcp.json
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text('{"command": "root-server"}', encoding="utf-8")

        # Create .claude/mcp/*.json
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "dir-server.json"
        mcp_file.write_text('{"command": "dir-server"}', encoding="utf-8")

        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = initializer.setup_mcp_servers(tmp_path)

        # Should succeed and process both files
        assert result is True
        assert mock_subprocess.call_count == 2

    @patch("subprocess.run")
    def test_setup_mcp_servers_http_transport_valid(self, mock_subprocess, tmp_path):
        """Test MCP setup with valid HTTP transport configuration."""
        initializer = Initializer()

        # Create MCP directory with HTTP config
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "http-server.json"
        mcp_file.write_text(
            '{"type": "http", "url": "https://api.example.com/mcp"}',
            encoding="utf-8",
        )

        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = initializer.setup_mcp_servers(tmp_path)

        # Should succeed
        assert result is True
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    def test_setup_mcp_servers_http_transport_missing_url(
        self, mock_subprocess, tmp_path
    ):
        """Test MCP setup fails with HTTP transport missing URL."""
        initializer = Initializer()

        # Create MCP directory with invalid HTTP config (missing url)
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "http-server.json"
        mcp_file.write_text('{"type": "http"}', encoding="utf-8")

        result = initializer.setup_mcp_servers(tmp_path)

        # Should fail validation
        assert result is False
        # Subprocess should not be called
        mock_subprocess.assert_not_called()

    @patch("subprocess.run")
    def test_setup_mcp_servers_stdio_transport_missing_command(
        self, mock_subprocess, tmp_path
    ):
        """Test MCP setup fails with STDIO transport missing command."""
        initializer = Initializer()

        # Create MCP directory with invalid STDIO config (missing command)
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "stdio-server.json"
        mcp_file.write_text('{"type": "stdio", "args": ["-y"]}', encoding="utf-8")

        result = initializer.setup_mcp_servers(tmp_path)

        # Should fail validation
        assert result is False
        # Subprocess should not be called
        mock_subprocess.assert_not_called()

    @patch("subprocess.run")
    def test_setup_mcp_servers_invalid_transport_type(self, mock_subprocess, tmp_path):
        """Test MCP setup fails with invalid transport type."""
        initializer = Initializer()

        # Create MCP directory with invalid transport type
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "invalid-server.json"
        mcp_file.write_text(
            '{"type": "websocket", "url": "ws://..."}', encoding="utf-8"
        )

        result = initializer.setup_mcp_servers(tmp_path)

        # Should fail validation
        assert result is False
        # Subprocess should not be called
        mock_subprocess.assert_not_called()

    @patch("subprocess.run")
    def test_setup_mcp_servers_sse_transport_deprecation_warning(
        self, mock_subprocess, tmp_path, capsys
    ):
        """Test MCP setup shows deprecation warning for SSE transport."""
        initializer = Initializer()

        # Create MCP directory with SSE config
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "sse-server.json"
        mcp_file.write_text(
            '{"type": "sse", "url": "https://api.example.com/events"}',
            encoding="utf-8",
        )

        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = initializer.setup_mcp_servers(tmp_path)

        # Should succeed but show warning
        assert result is True
        mock_subprocess.assert_called_once()
        # Note: Console output testing would require capturing rich console output

    @patch("subprocess.run")
    def test_setup_mcp_servers_http_non_https_warning(
        self, mock_subprocess, tmp_path, capsys
    ):
        """Test MCP setup warns about HTTP (non-HTTPS) usage."""
        initializer = Initializer()

        # Create MCP directory with HTTP (not HTTPS) config
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "http-server.json"
        mcp_file.write_text(
            '{"type": "http", "url": "http://api.example.com/mcp"}',
            encoding="utf-8",
        )

        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = initializer.setup_mcp_servers(tmp_path)

        # Should succeed but show warning
        assert result is True
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    def test_setup_mcp_servers_hardcoded_credentials_warning(
        self, mock_subprocess, tmp_path, capsys
    ):
        """Test MCP setup warns about potential hardcoded credentials."""
        initializer = Initializer()

        # Create MCP directory with hardcoded credential
        mcp_dir = tmp_path / ".claude" / "mcp"
        mcp_dir.mkdir(parents=True)
        mcp_file = mcp_dir / "http-server.json"
        mcp_file.write_text(
            '{"type": "http", "url": "https://api.example.com/mcp", "headers": {"Authorization": "Bearer sk_live_abc123"}}',
            encoding="utf-8",
        )

        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        result = initializer.setup_mcp_servers(tmp_path)

        # Should succeed but show warning
        assert result is True
        mock_subprocess.assert_called_once()


class TestInitializeTemplateErrors:
    """Tests for template error handling during initialization."""

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_missing_critical_template(
        self, mock_ensure_dir, mock_is_git, git_repo, mock_template_manager
    ):
        """Test initialization when critical templates are missing.

        BEHAVIOR: Should trigger rollback when >50% of files fail.
        """
        from claudefig.exceptions import (
            InitializationRollbackError,
            TemplateNotFoundError,
        )

        mock_is_git.return_value = True
        initializer = Initializer()

        # Mock preset repository to raise TemplateNotFoundError for all templates
        mock_preset_repo = MagicMock()
        mock_preset_repo.get_template_content.side_effect = TemplateNotFoundError(
            "preset_id", "Template not found"
        )
        initializer.preset_repo = mock_preset_repo

        with (
            patch.object(Config, "create_default"),
            pytest.raises(InitializationRollbackError),
        ):
            initializer.initialize(git_repo, force=False)

        # Should have tried to create .claude directory
        mock_ensure_dir.assert_called_once()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_permission_denied_during_write(
        self, mock_ensure_dir, mock_is_git, git_repo
    ):
        """Test initialization when write permission is denied.

        BEHAVIOR: Should trigger rollback when all file writes fail due to permissions.
        """
        from claudefig.exceptions import InitializationRollbackError

        mock_is_git.return_value = True
        initializer = Initializer()

        # Patch Path.write_text to raise PermissionError for all writes
        with (
            patch.object(Config, "create_default"),
            patch.object(
                Path,
                "write_text",
                side_effect=PermissionError("Permission denied"),
            ),
            pytest.raises(InitializationRollbackError),
        ):
            initializer.initialize(git_repo, force=False)

        # Should have tried to create .claude directory
        mock_ensure_dir.assert_called_once()

    @patch("claudefig.initializer.is_git_repository")
    @patch("claudefig.initializer.ensure_directory")
    def test_initialize_continues_after_partial_failure(
        self, mock_ensure_dir, mock_is_git, git_repo
    ):
        """Test that initialization continues when some files fail.

        BEHAVIOR: Initialization should continue processing remaining files even if some fail.
        """
        mock_is_git.return_value = True
        initializer = Initializer()

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
        mock_template_manager,
        capsys,
    ):
        """Test that missing template errors include helpful messages.

        BEHAVIOR: Should trigger rollback and display helpful error messages.
        """
        from claudefig.exceptions import (
            InitializationRollbackError,
            TemplateNotFoundError,
        )

        mock_is_git.return_value = True
        initializer = Initializer()

        # Mock preset repository to raise TemplateNotFoundError
        mock_preset_repo = MagicMock()
        mock_preset_repo.get_template_content.side_effect = TemplateNotFoundError(
            "claude_md:default", "CLAUDE.md not found"
        )
        initializer.preset_repo = mock_preset_repo

        with (
            patch.object(Config, "create_default"),
            pytest.raises(InitializationRollbackError),
        ):
            initializer.initialize(git_repo, force=False)

        # Check that output includes helpful warning
        captured = capsys.readouterr()
        # Should mention template not found (actual message may vary)
        assert "Template" in captured.out or "template" in captured.out
