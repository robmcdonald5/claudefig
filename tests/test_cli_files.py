"""Tests for file management CLI commands."""

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
def mock_config_file(tmp_path):
    """Create a mock config file."""
    config_path = tmp_path / ".claudefig.toml"
    config_path.write_text(
        """
[claudefig]
version = "2.0"
schema_version = "2.0"

[[files]]
id = "test-claude-md"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true
variables = {}

[[files]]
id = "test-settings"
type = "settings_json"
preset = "settings_json:default"
path = ".claude/settings.json"
enabled = false
variables = {}
""",
        encoding="utf-8",
    )
    return config_path


class TestFilesList:
    """Tests for 'claudefig files list' command."""

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_list_all_files(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test listing all file instances."""
        # Setup mocks
        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = [
            {
                "id": "test-claude-md",
                "type": "claude_md",
                "preset": "claude_md:default",
                "path": "CLAUDE.md",
                "enabled": True,
            },
            {
                "id": "test-settings",
                "type": "settings_json",
                "preset": "settings_json:default",
                "path": ".claude/settings.json",
                "enabled": False,
            },
        ]
        mock_config_class.return_value = mock_cfg

        # Mock instances
        from claudefig.models import FileInstance, FileType

        mock_inst_mgr = Mock()
        mock_inst_mgr.list_instances.return_value = [
            FileInstance(
                id="test-claude-md",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            FileInstance(
                id="test-settings",
                type=FileType.SETTINGS_JSON,
                preset="settings_json:default",
                path=".claude/settings.json",
                enabled=False,
            ),
        ]
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(main, ["files", "list", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "File Instances" in result.output
        assert "test-claude-md" in result.output
        assert "test-settings" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_list_by_type(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test listing files filtered by type."""
        from claudefig.models import FileInstance, FileType

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.list_instances.return_value = [
            FileInstance(
                id="test-claude-md",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            )
        ]
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main, ["files", "list", "--path", str(tmp_path), "--type", "claude_md"]
        )

        assert result.exit_code == 0
        # Verify filter_type was passed to list_instances
        call_args = mock_inst_mgr.list_instances.call_args
        assert call_args[0][0] == FileType.CLAUDE_MD

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_list_enabled_only(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test listing only enabled file instances."""
        from claudefig.models import FileInstance, FileType

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.list_instances.return_value = [
            FileInstance(
                id="test-claude-md",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            )
        ]
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main, ["files", "list", "--path", str(tmp_path), "--enabled-only"]
        )

        assert result.exit_code == 0
        # Verify enabled_only flag was passed
        call_args = mock_inst_mgr.list_instances.call_args
        assert call_args[0][1] is True  # enabled_only parameter

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_list_empty(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test listing when no file instances exist."""
        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.list_instances.return_value = []
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(main, ["files", "list", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "No file instances configured" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_list_invalid_type(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test listing with invalid file type."""
        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        result = cli_runner.invoke(
            main, ["files", "list", "--path", str(tmp_path), "--type", "invalid_type"]
        )

        assert result.exit_code == 1
        assert "invalid_type" in result.output.lower()


class TestFilesAdd:
    """Tests for 'claudefig files add' command."""

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_add_valid_file(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test adding a valid file instance."""
        from claudefig.models import ValidationResult

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_cfg.save = Mock()
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.generate_instance_id.return_value = "claude-md-default"
        mock_inst_mgr.add_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            [
                "files",
                "add",
                "claude_md",
                "--preset",
                "default",
                "--repo-path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "Added file instance" in result.output
        assert "claude-md-default" in result.output or "claude_md" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_add_with_disabled_flag(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test adding a file instance with disabled flag."""
        from claudefig.models import ValidationResult

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_cfg.save = Mock()
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.generate_instance_id.return_value = "claude-md-default"
        mock_inst_mgr.add_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            [
                "files",
                "add",
                "claude_md",
                "--disabled",
                "--repo-path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        # Verify the instance was created with enabled=False
        add_call = mock_inst_mgr.add_instance.call_args[0][0]
        assert add_call.enabled is False

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_add_invalid_file_type(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test adding a file with invalid type."""
        result = cli_runner.invoke(
            main,
            ["files", "add", "invalid_type", "--repo-path", str(tmp_path)],
        )

        assert result.exit_code == 1
        assert "Invalid file type" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_add_validation_fails(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test adding a file that fails validation."""
        from claudefig.models import ValidationResult

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.generate_instance_id.return_value = "test-id"
        mock_inst_mgr.add_instance.return_value = ValidationResult(
            valid=False, errors=["Test error"], warnings=[]
        )
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            ["files", "add", "claude_md", "--repo-path", str(tmp_path)],
        )

        assert result.exit_code == 1
        assert "Validation failed" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_add_with_custom_path(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test adding a file with custom path."""
        from claudefig.models import ValidationResult

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_cfg.save = Mock()
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.generate_instance_id.return_value = "test-id"
        mock_inst_mgr.add_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            [
                "files",
                "add",
                "claude_md",
                "--path-target",
                "docs/CLAUDE.md",
                "--repo-path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        # Verify path was set correctly
        add_call = mock_inst_mgr.add_instance.call_args[0][0]
        assert add_call.path == "docs/CLAUDE.md"


class TestFilesRemove:
    """Tests for 'claudefig files remove' command."""

    @patch("claudefig.config.Config")
    def test_remove_existing_file(self, mock_config_class, cli_runner, tmp_path):
        """Test removing an existing file instance."""
        mock_cfg = Mock()
        mock_cfg.remove_file_instance.return_value = True
        mock_cfg.save = Mock()
        mock_config_class.return_value = mock_cfg

        result = cli_runner.invoke(
            main, ["files", "remove", "test-instance", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "Removed file instance" in result.output or "test-instance" in result.output

    @patch("claudefig.config.Config")
    def test_remove_nonexistent_file(self, mock_config_class, cli_runner, tmp_path):
        """Test removing a file instance that doesn't exist."""
        mock_cfg = Mock()
        mock_cfg.remove_file_instance.return_value = False
        mock_config_class.return_value = mock_cfg

        result = cli_runner.invoke(
            main, ["files", "remove", "nonexistent", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "nonexistent" in result.output


class TestFilesEnable:
    """Tests for 'claudefig files enable' command."""

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_enable_disabled_file(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test enabling a disabled file instance."""
        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_cfg.save = Mock()
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.enable_instance.return_value = True
        mock_inst_mgr.save_instances.return_value = []
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main, ["files", "enable", "test-instance", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "Enabled file instance" in result.output or "test-instance" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_enable_nonexistent_file(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test enabling a file that doesn't exist."""
        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.enable_instance.return_value = False
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main, ["files", "enable", "nonexistent", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "nonexistent" in result.output


class TestFilesDisable:
    """Tests for 'claudefig files disable' command."""

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_disable_enabled_file(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test disabling an enabled file instance."""
        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_cfg.save = Mock()
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.disable_instance.return_value = True
        mock_inst_mgr.save_instances.return_value = []
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main, ["files", "disable", "test-instance", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "Disabled file instance" in result.output or "test-instance" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_disable_nonexistent_file(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test disabling a file that doesn't exist."""
        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.disable_instance.return_value = False
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main, ["files", "disable", "nonexistent", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "nonexistent" in result.output


class TestFilesEdit:
    """Tests for 'claudefig files edit' command."""

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_edit_preset(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test editing a file instance's preset."""
        from claudefig.models import FileInstance, FileType, ValidationResult

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_cfg.save = Mock()
        mock_config_class.return_value = mock_cfg

        existing_instance = FileInstance(
            id="test-instance",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )

        mock_inst_mgr = Mock()
        mock_inst_mgr.get_instance.return_value = existing_instance
        mock_inst_mgr.update_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_inst_mgr.save_instances.return_value = []
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            [
                "files",
                "edit",
                "test-instance",
                "--preset",
                "minimal",
                "--repo-path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "Updated file instance" in result.output
        assert "preset" in result.output.lower() or "test-instance" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_edit_path(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test editing a file instance's path."""
        from claudefig.models import FileInstance, FileType, ValidationResult

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_cfg.save = Mock()
        mock_config_class.return_value = mock_cfg

        existing_instance = FileInstance(
            id="test-instance",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )

        mock_inst_mgr = Mock()
        mock_inst_mgr.get_instance.return_value = existing_instance
        mock_inst_mgr.update_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_inst_mgr.save_instances.return_value = []
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            [
                "files",
                "edit",
                "test-instance",
                "--path-target",
                "docs/CLAUDE.md",
                "--repo-path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "Updated file instance" in result.output
        assert "path" in result.output.lower()
        # Verify path was updated
        assert existing_instance.path == "docs/CLAUDE.md"

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_edit_enable_status(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test editing a file instance's enabled status."""
        from claudefig.models import FileInstance, FileType, ValidationResult

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_cfg.save = Mock()
        mock_config_class.return_value = mock_cfg

        existing_instance = FileInstance(
            id="test-instance",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )

        mock_inst_mgr = Mock()
        mock_inst_mgr.get_instance.return_value = existing_instance
        mock_inst_mgr.update_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_inst_mgr.save_instances.return_value = []
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            [
                "files",
                "edit",
                "test-instance",
                "--disable",
                "--repo-path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "Updated file instance" in result.output
        assert "status" in result.output.lower()
        # Verify enabled was updated
        assert existing_instance.enabled is False

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_edit_nonexistent_file(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test editing a file that doesn't exist."""
        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        mock_inst_mgr = Mock()
        mock_inst_mgr.get_instance.return_value = None
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            [
                "files",
                "edit",
                "nonexistent",
                "--preset",
                "minimal",
                "--repo-path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "nonexistent" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_edit_no_changes(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test editing without specifying any changes."""
        from claudefig.models import FileInstance, FileType

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        existing_instance = FileInstance(
            id="test-instance",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )

        mock_inst_mgr = Mock()
        mock_inst_mgr.get_instance.return_value = existing_instance
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            ["files", "edit", "test-instance", "--repo-path", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert "No changes specified" in result.output

    @patch("claudefig.file_instance_manager.FileInstanceManager")
    @patch("claudefig.preset_manager.PresetManager")
    @patch("claudefig.config.Config")
    def test_edit_validation_fails(
        self, mock_config_class, mock_preset_mgr_class, mock_inst_mgr_class, cli_runner, tmp_path
    ):
        """Test editing with validation failure."""
        from claudefig.models import FileInstance, FileType, ValidationResult

        mock_cfg = Mock()
        mock_cfg.get_file_instances.return_value = []
        mock_config_class.return_value = mock_cfg

        existing_instance = FileInstance(
            id="test-instance",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )

        mock_inst_mgr = Mock()
        mock_inst_mgr.get_instance.return_value = existing_instance
        mock_inst_mgr.update_instance.return_value = ValidationResult(
            valid=False, errors=["Invalid preset"], warnings=[]
        )
        mock_inst_mgr_class.return_value = mock_inst_mgr

        result = cli_runner.invoke(
            main,
            [
                "files",
                "edit",
                "test-instance",
                "--preset",
                "invalid",
                "--repo-path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 1
        assert "Validation failed" in result.output
