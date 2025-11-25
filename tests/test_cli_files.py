"""Tests for file management CLI commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from claudefig.cli import main
from claudefig.models import FileType
from tests.factories import FileInstanceFactory


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_config_file(tmp_path):
    """Create a mock config file."""
    config_path = tmp_path / "claudefig.toml"
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

    @patch("claudefig.services.file_instance_service.list_instances")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_list_all_files(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_list_instances,
        cli_runner,
        tmp_path,
    ):
        """Test listing all file instances."""

        # Mock config loading
        mock_load_config.return_value = {
            "claudefig": {"version": "2.0"},
            "files": [
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
            ],
        }

        mock_get_file_instances.return_value = mock_load_config.return_value["files"]

        # Mock instance loading
        claude_instance = FileInstanceFactory(id="test-claude-md")
        settings_instance = FileInstanceFactory.disabled(
            id="test-settings",
            type=FileType.SETTINGS_JSON,
            preset="settings_json:default",
            path=".claude/settings.json",
        )
        mock_load_instances.return_value = (
            {"test-claude-md": claude_instance, "test-settings": settings_instance},
            [],
        )
        mock_list_instances.return_value = [claude_instance, settings_instance]

        result = cli_runner.invoke(main, ["files", "list", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "File Instances" in result.output
        assert "test-claude-md" in result.output
        assert "test-settings" in result.output

    @patch("claudefig.services.file_instance_service.list_instances")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_list_by_type(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_list_instances,
        cli_runner,
        tmp_path,
    ):
        """Test listing files filtered by type."""

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []

        # Mock instance loading
        claude_instance = FileInstanceFactory(id="test-claude-md")
        mock_load_instances.return_value = ({"test-claude-md": claude_instance}, [])
        mock_list_instances.return_value = [claude_instance]

        result = cli_runner.invoke(
            main, ["files", "list", "--path", str(tmp_path), "--type", "claude_md"]
        )

        assert result.exit_code == 0
        # Verify filter_type was passed to list_instances
        call_args = mock_list_instances.call_args
        assert call_args[0][1] == FileType.CLAUDE_MD  # Second arg is filter_type

    @patch("claudefig.services.file_instance_service.list_instances")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_list_enabled_only(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_list_instances,
        cli_runner,
        tmp_path,
    ):
        """Test listing only enabled file instances."""

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []

        # Mock instance loading
        claude_instance = FileInstanceFactory(id="test-claude-md")
        mock_load_instances.return_value = ({"test-claude-md": claude_instance}, [])
        mock_list_instances.return_value = [claude_instance]

        result = cli_runner.invoke(
            main, ["files", "list", "--path", str(tmp_path), "--enabled-only"]
        )

        assert result.exit_code == 0
        # Verify enabled_only flag was passed
        call_args = mock_list_instances.call_args
        assert call_args[0][2] is True  # Third arg is enabled_only parameter

    @patch("claudefig.services.file_instance_service.list_instances")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_list_empty(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_list_instances,
        cli_runner,
        tmp_path,
    ):
        """Test listing when no file instances exist."""
        # Mock config loading with no instances
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])
        mock_list_instances.return_value = []

        result = cli_runner.invoke(main, ["files", "list", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "No file instances configured" in result.output

    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_list_invalid_type(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        cli_runner,
        tmp_path,
    ):
        """Test listing with invalid file type."""
        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        result = cli_runner.invoke(
            main, ["files", "list", "--path", str(tmp_path), "--type", "invalid_type"]
        )

        # Click returns exit code 2 for UsageError (bad parameter)
        assert result.exit_code == 2
        assert "invalid_type" in result.output.lower()


class TestFilesAdd:
    """Tests for 'claudefig files add' command."""

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.add_instance")
    @patch("claudefig.services.file_instance_service.generate_instance_id")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_add_valid_file(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_generate_id,
        mock_add_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test adding a valid file instance."""
        from claudefig.models import ValidationResult

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock instance creation
        mock_generate_id.return_value = "claude-md-default"
        mock_add_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_save_instances.return_value = []

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

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.add_instance")
    @patch("claudefig.services.file_instance_service.generate_instance_id")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_add_with_disabled_flag(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_generate_id,
        mock_add_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test adding a file instance with disabled flag."""
        from claudefig.models import ValidationResult

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock instance creation
        mock_generate_id.return_value = "claude-md-default"
        mock_add_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_save_instances.return_value = []

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
        add_call = mock_add_instance.call_args[0][1]  # Second arg is FileInstance
        assert add_call.enabled is False

    def test_add_invalid_file_type(
        self,
        cli_runner,
        tmp_path,
    ):
        """Test adding a file with invalid type."""
        result = cli_runner.invoke(
            main,
            ["files", "add", "invalid_type", "--repo-path", str(tmp_path)],
        )

        # Click returns exit code 2 for UsageError (bad parameter)
        assert result.exit_code == 2
        assert "Invalid file type" in result.output

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.add_instance")
    @patch("claudefig.services.file_instance_service.generate_instance_id")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_add_validation_fails(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_generate_id,
        mock_add_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test adding a file that fails validation."""
        from claudefig.models import ValidationResult

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock validation failure
        mock_generate_id.return_value = "test-id"
        mock_add_instance.return_value = ValidationResult(
            valid=False, errors=["Test error"], warnings=[]
        )

        result = cli_runner.invoke(
            main,
            ["files", "add", "claude_md", "--repo-path", str(tmp_path)],
        )

        assert result.exit_code == 1
        assert "Validation failed" in result.output

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.add_instance")
    @patch("claudefig.services.file_instance_service.generate_instance_id")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_add_with_custom_path(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_generate_id,
        mock_add_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test adding a file with custom path."""
        from claudefig.models import ValidationResult

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock instance creation
        mock_generate_id.return_value = "test-id"
        mock_add_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_save_instances.return_value = []

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
        add_call = mock_add_instance.call_args[0][1]  # Second arg is FileInstance
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
        assert (
            "Removed file instance" in result.output or "test-instance" in result.output
        )

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

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.enable_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_enable_disabled_file(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_enable_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test enabling a disabled file instance."""
        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock enable operation
        mock_enable_instance.return_value = True
        mock_save_instances.return_value = []

        result = cli_runner.invoke(
            main, ["files", "enable", "test-instance", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert (
            "Enabled file instance" in result.output or "test-instance" in result.output
        )

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.enable_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_enable_nonexistent_file(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_enable_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test enabling a file that doesn't exist."""
        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock enable failure (instance not found)
        mock_enable_instance.return_value = False

        result = cli_runner.invoke(
            main, ["files", "enable", "nonexistent", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "nonexistent" in result.output


class TestFilesDisable:
    """Tests for 'claudefig files disable' command."""

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.disable_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_disable_enabled_file(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_disable_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test disabling an enabled file instance."""
        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock disable operation
        mock_disable_instance.return_value = True
        mock_save_instances.return_value = []

        result = cli_runner.invoke(
            main, ["files", "disable", "test-instance", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert (
            "Disabled file instance" in result.output
            or "test-instance" in result.output
        )

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.disable_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_disable_nonexistent_file(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_disable_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test disabling a file that doesn't exist."""
        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock disable failure (instance not found)
        mock_disable_instance.return_value = False

        result = cli_runner.invoke(
            main, ["files", "disable", "nonexistent", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "nonexistent" in result.output


class TestFilesEdit:
    """Tests for 'claudefig files edit' command."""

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.update_instance")
    @patch("claudefig.services.file_instance_service.get_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_edit_preset(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_get_instance,
        mock_update_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test editing a file instance's preset."""
        from claudefig.models import ValidationResult

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock instance retrieval
        existing_instance = FileInstanceFactory(id="test-instance")
        mock_get_instance.return_value = existing_instance

        # Mock update operation
        mock_update_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_save_instances.return_value = []

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

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.update_instance")
    @patch("claudefig.services.file_instance_service.get_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_edit_path(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_get_instance,
        mock_update_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test editing a file instance's path."""
        from claudefig.models import ValidationResult

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock instance retrieval
        existing_instance = FileInstanceFactory(id="test-instance")
        mock_get_instance.return_value = existing_instance

        # Mock update operation
        mock_update_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_save_instances.return_value = []

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

    @patch("claudefig.services.config_service.save_config")
    @patch("claudefig.services.config_service.set_file_instances")
    @patch("claudefig.services.file_instance_service.save_instances_to_config")
    @patch("claudefig.services.file_instance_service.update_instance")
    @patch("claudefig.services.file_instance_service.get_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_edit_enable_status(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_get_instance,
        mock_update_instance,
        mock_save_instances,
        mock_set_file_instances,
        mock_save_config,
        cli_runner,
        tmp_path,
    ):
        """Test editing a file instance's enabled status."""
        from claudefig.models import ValidationResult

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock instance retrieval
        existing_instance = FileInstanceFactory(id="test-instance")
        mock_get_instance.return_value = existing_instance

        # Mock update operation
        mock_update_instance.return_value = ValidationResult(
            valid=True, errors=[], warnings=[]
        )
        mock_save_instances.return_value = []

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

    @patch("claudefig.services.file_instance_service.get_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_edit_nonexistent_file(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_get_instance,
        cli_runner,
        tmp_path,
    ):
        """Test editing a file that doesn't exist."""
        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock instance not found
        mock_get_instance.return_value = None

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

    @patch("claudefig.services.file_instance_service.get_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_edit_no_changes(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_get_instance,
        cli_runner,
        tmp_path,
    ):
        """Test editing without specifying any changes."""

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock instance retrieval
        existing_instance = FileInstanceFactory(id="test-instance")
        mock_get_instance.return_value = existing_instance

        result = cli_runner.invoke(
            main,
            ["files", "edit", "test-instance", "--repo-path", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert "No changes specified" in result.output

    @patch("claudefig.services.file_instance_service.update_instance")
    @patch("claudefig.services.file_instance_service.get_instance")
    @patch("claudefig.services.file_instance_service.load_instances_from_config")
    @patch("claudefig.services.config_service.get_file_instances")
    @patch("claudefig.services.config_service.load_config")
    def test_edit_validation_fails(
        self,
        mock_load_config,
        mock_get_file_instances,
        mock_load_instances,
        mock_get_instance,
        mock_update_instance,
        cli_runner,
        tmp_path,
    ):
        """Test editing with validation failure."""
        from claudefig.models import ValidationResult

        # Mock config loading
        mock_load_config.return_value = {"claudefig": {"version": "2.0"}, "files": []}
        mock_get_file_instances.return_value = []
        mock_load_instances.return_value = ({}, [])

        # Mock instance retrieval
        existing_instance = FileInstanceFactory(id="test-instance")
        mock_get_instance.return_value = existing_instance

        # Mock validation failure
        mock_update_instance.return_value = ValidationResult(
            valid=False, errors=["Invalid preset"], warnings=[]
        )

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
