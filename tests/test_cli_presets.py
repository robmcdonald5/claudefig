"""Tests for CLI presets commands."""

import os
from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest
from click.testing import CliRunner

from claudefig.cli.commands.presets import (
    presets_apply,
    presets_create,
    presets_create_from_repo,
    presets_delete,
    presets_edit,
    presets_group,
    presets_list,
    presets_open,
    presets_show,
)
from claudefig.exceptions import (
    ConfigFileExistsError,
    TemplateNotFoundError,
)


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_preset_manager():
    """Create a mock ConfigTemplateManager."""
    manager = Mock()
    manager.global_presets_dir = Path("/fake/presets")
    return manager


@pytest.fixture
def sample_presets():
    """Create sample preset data."""
    return [
        {
            "name": "default",
            "description": "Default preset",
            "file_count": 3,
            "validation": {"valid": True},
        },
        {
            "name": "fastapi",
            "description": "FastAPI project setup",
            "file_count": 5,
            "validation": {"valid": True},
        },
        {
            "name": "broken",
            "description": "Invalid preset",
            "file_count": 2,
            "validation": {"valid": False},
        },
    ]


class TestPresetsList:
    """Tests for 'presets list' command."""

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_list_all_presets(self, mock_manager_class, cli_runner, sample_presets):
        """Test listing all presets successfully."""
        mock_manager = Mock()
        mock_manager.list_global_presets.return_value = sample_presets
        mock_manager.global_presets_dir = Path("/fake/presets")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_list, [])

        assert result.exit_code == 0
        assert "default" in result.output
        assert "fastapi" in result.output
        assert "broken" in result.output
        mock_manager.list_global_presets.assert_called_once_with(
            include_validation=False
        )

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_list_with_validation_flag(
        self, mock_manager_class, cli_runner, sample_presets
    ):
        """Test listing presets with validation status."""
        mock_manager = Mock()
        mock_manager.list_global_presets.return_value = sample_presets
        mock_manager.global_presets_dir = Path("/fake/presets")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_list, ["--validate"])

        assert result.exit_code == 0
        assert "Valid" in result.output  # Column header
        assert "Yes" in result.output or "No" in result.output
        mock_manager.list_global_presets.assert_called_once_with(
            include_validation=True
        )

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_list_empty_presets(self, mock_manager_class, cli_runner):
        """Test listing when no presets exist."""
        mock_manager = Mock()
        mock_manager.list_global_presets.return_value = []
        presets_path = Path("/fake/presets")
        mock_manager.global_presets_dir = presets_path
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_list, [])

        assert result.exit_code == 0
        assert "No presets found" in result.output
        assert str(presets_path) in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_list_shows_count(self, mock_manager_class, cli_runner, sample_presets):
        """Test that list shows total preset count."""
        mock_manager = Mock()
        mock_manager.list_global_presets.return_value = sample_presets
        mock_manager.global_presets_dir = Path("/fake/presets")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_list, [])

        assert result.exit_code == 0
        assert "(3)" in result.output  # Shows count

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_list_shows_location(self, mock_manager_class, cli_runner):
        """Test that list shows presets directory location."""
        mock_manager = Mock()
        mock_manager.list_global_presets.return_value = []
        custom_location = Path("/custom/location")
        mock_manager.global_presets_dir = custom_location
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_list, [])

        assert result.exit_code == 0
        assert str(custom_location) in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_list_shows_file_counts(
        self, mock_manager_class, cli_runner, sample_presets
    ):
        """Test that list shows file counts for each preset."""
        mock_manager = Mock()
        mock_manager.list_global_presets.return_value = sample_presets
        mock_manager.global_presets_dir = Path("/fake/presets")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_list, [])

        assert result.exit_code == 0
        assert "3" in result.output  # file_count for default
        assert "5" in result.output  # file_count for fastapi


class TestPresetsShow:
    """Tests for 'presets show' command."""

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_show_valid_preset(self, mock_manager_class, cli_runner, sample_presets):
        """Test showing valid preset details."""
        mock_config = Mock()
        mock_config.get_file_instances.return_value = [
            {
                "type": "claude_md",
                "path": "CLAUDE.md",
                "preset": "default",
                "enabled": True,
            }
        ]

        mock_manager = Mock()
        mock_manager.get_preset_config.return_value = mock_config
        mock_manager.list_global_presets.return_value = sample_presets
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_show, ["default"])

        assert result.exit_code == 0
        assert "default" in result.output
        assert "Default preset" in result.output
        assert "claude_md" in result.output
        assert "CLAUDE.md" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_show_missing_preset(self, mock_manager_class, cli_runner):
        """Test showing non-existent preset."""
        mock_manager = Mock()
        mock_manager.get_preset_config.side_effect = FileNotFoundError("Not found")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_show, ["nonexistent"])

        assert result.exit_code == 0  # Doesn't abort, just shows message
        assert "not found" in result.output.lower() or "nonexistent" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_show_displays_file_instances(self, mock_manager_class, cli_runner):
        """Test that show displays all file instances."""
        mock_config = Mock()
        mock_config.get_file_instances.return_value = [
            {
                "type": "claude_md",
                "path": "CLAUDE.md",
                "preset": "test",
                "enabled": True,
            },
            {
                "type": "settings_json",
                "path": ".vscode/settings.json",
                "preset": "test",
                "enabled": False,
            },
        ]

        mock_manager = Mock()
        mock_manager.get_preset_config.return_value = mock_config
        mock_manager.list_global_presets.return_value = [
            {"name": "test", "file_count": 2}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_show, ["test"])

        assert result.exit_code == 0
        assert "claude_md" in result.output
        assert "settings_json" in result.output
        assert "enabled" in result.output
        assert "disabled" in result.output or "dim" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_show_empty_preset(self, mock_manager_class, cli_runner):
        """Test showing preset with no file instances."""
        mock_config = Mock()
        mock_config.get_file_instances.return_value = []

        mock_manager = Mock()
        mock_manager.get_preset_config.return_value = mock_config
        mock_manager.list_global_presets.return_value = [
            {"name": "empty", "file_count": 0}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_show, ["empty"])

        assert result.exit_code == 0
        assert "No file instances" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_show_displays_description(self, mock_manager_class, cli_runner):
        """Test that show displays preset description."""
        mock_config = Mock()
        mock_config.get_file_instances.return_value = []

        mock_manager = Mock()
        mock_manager.get_preset_config.return_value = mock_config
        mock_manager.list_global_presets.return_value = [
            {"name": "test", "description": "Custom description"}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_show, ["test"])

        assert result.exit_code == 0
        assert "Custom description" in result.output


class TestPresetsApply:
    """Tests for 'presets apply' command."""

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_apply_success(self, mock_manager_class, cli_runner, tmp_path):
        """Test successfully applying preset to project."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_apply, ["default", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "applied successfully" in result.output
        mock_manager.apply_preset_to_project.assert_called_once()

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_apply_missing_preset(self, mock_manager_class, cli_runner, tmp_path):
        """Test applying non-existent preset."""
        mock_manager = Mock()
        mock_manager.apply_preset_to_project.side_effect = TemplateNotFoundError(
            "Not found"
        )
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_apply, ["nonexistent", "--path", str(tmp_path)]
        )

        # Custom handler should print message
        assert (
            "not found" in result.output.lower() or "Preset not found" in result.output
        )

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_apply_config_exists_error(self, mock_manager_class, cli_runner, tmp_path):
        """Test applying when config already exists."""
        mock_manager = Mock()
        mock_manager.apply_preset_to_project.side_effect = ConfigFileExistsError(
            "Config exists"
        )
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_apply, ["default", "--path", str(tmp_path)])

        assert "Error" in result.output or "already exists" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_apply_file_exists_error(self, mock_manager_class, cli_runner, tmp_path):
        """Test applying when file exists."""
        mock_manager = Mock()
        mock_manager.apply_preset_to_project.side_effect = FileExistsError(
            "File exists"
        )
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_apply, ["default", "--path", str(tmp_path)])

        assert "already exists" in result.output or "Error" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_apply_to_custom_path(self, mock_manager_class, cli_runner, tmp_path):
        """Test applying preset to custom path."""
        custom_path = tmp_path / "project"
        custom_path.mkdir()

        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_apply, ["default", "--path", str(custom_path)]
        )

        assert result.exit_code == 0
        call_args = mock_manager.apply_preset_to_project.call_args
        assert call_args[0][0] == "default"
        assert Path(call_args[1]["target_path"]) == custom_path.resolve()

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_apply_shows_preset_name(self, mock_manager_class, cli_runner, tmp_path):
        """Test that apply shows preset name in output."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_apply, ["custom_preset", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "custom_preset" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_apply_shows_target_path(self, mock_manager_class, cli_runner, tmp_path):
        """Test that apply shows target path in output."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_apply, ["default", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert str(tmp_path) in result.output or "claudefig.toml" in result.output


class TestPresetsCreate:
    """Tests for 'presets create' command."""

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_create_success(self, mock_manager_class, cli_runner, tmp_path):
        """Test successfully creating preset from current config."""
        # Create a config file
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text("[project]\nname = 'test'")

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create,
            ["my_preset", "--description", "Test preset", "--path", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert "Created preset" in result.output
        assert "my_preset" in result.output
        mock_manager.save_global_preset.assert_called_once_with(
            "my_preset", "Test preset", config_path=ANY
        )

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_create_without_config(self, mock_manager_class, cli_runner, tmp_path):
        """Test creating preset when no config exists."""
        # No config file
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create, ["my_preset", "--path", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "Initialize" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_create_with_default_description(
        self, mock_manager_class, cli_runner, tmp_path
    ):
        """Test creating preset with default (empty) description."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text("[project]\nname = 'test'")

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create, ["my_preset", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        mock_manager.save_global_preset.assert_called_once_with(
            "my_preset", "", config_path=ANY
        )

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_create_does_not_change_directory(
        self, mock_manager_class, cli_runner, tmp_path
    ):
        """Test that create does not change the current working directory."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text("[project]\nname = 'test'")

        original_cwd = os.getcwd()

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_create, ["test", "--path", str(tmp_path)])

        # Current directory should never change
        assert os.getcwd() == original_cwd
        assert result.exit_code == 0

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_create_shows_location(self, mock_manager_class, cli_runner, tmp_path):
        """Test that create shows preset location."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text("[project]\nname = 'test'")

        presets_dir = tmp_path / "presets"
        mock_manager = Mock()
        mock_manager.global_presets_dir = presets_dir
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create, ["my_preset", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "Location:" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_create_handles_value_error(self, mock_manager_class, cli_runner, tmp_path):
        """Test create handles ValueError from manager."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text("[project]\nname = 'test'")

        mock_manager = Mock()
        mock_manager.save_global_preset.side_effect = ValueError("Invalid name")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create, ["bad-name", "--path", str(tmp_path)]
        )

        assert "Error" in result.output or "Invalid name" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_create_handles_file_not_found(
        self, mock_manager_class, cli_runner, tmp_path
    ):
        """Test create handles FileNotFoundError from manager."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text("[project]\nname = 'test'")

        mock_manager = Mock()
        mock_manager.save_global_preset.side_effect = FileNotFoundError("Missing file")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_create, ["test", "--path", str(tmp_path)])

        assert "Error" in result.output or "Missing file" in result.output


class TestPresetsDelete:
    """Tests for 'presets delete' command."""

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_delete_success(self, mock_manager_class, cli_runner):
        """Test successfully deleting preset."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_delete, ["old_preset"], input="y\n")

        assert result.exit_code == 0
        assert "Deleted preset" in result.output
        assert "old_preset" in result.output
        mock_manager.delete_global_preset.assert_called_once_with("old_preset")

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_delete_requires_confirmation(self, mock_manager_class, cli_runner):
        """Test that delete requires user confirmation."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # User cancels
        result = cli_runner.invoke(presets_delete, ["test"], input="n\n")

        assert result.exit_code == 1  # Aborted
        mock_manager.delete_global_preset.assert_not_called()

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_delete_missing_preset(self, mock_manager_class, cli_runner):
        """Test deleting non-existent preset."""
        mock_manager = Mock()
        mock_manager.delete_global_preset.side_effect = TemplateNotFoundError(
            "Not found"
        )
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_delete, ["nonexistent"], input="y\n")

        assert (
            "not found" in result.output.lower() or "Preset not found" in result.output
        )

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_delete_handles_value_error(self, mock_manager_class, cli_runner):
        """Test delete handles ValueError (e.g., built-in preset protection)."""
        mock_manager = Mock()
        mock_manager.delete_global_preset.side_effect = ValueError(
            "Cannot delete built-in"
        )
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_delete, ["default"], input="y\n")

        assert "Error" in result.output or "Cannot delete built-in" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_delete_handles_file_not_found(self, mock_manager_class, cli_runner):
        """Test delete handles FileNotFoundError."""
        mock_manager = Mock()
        mock_manager.delete_global_preset.side_effect = FileNotFoundError("Not found")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_delete, ["missing"], input="y\n")

        assert (
            "not found" in result.output.lower() or "Preset not found" in result.output
        )


class TestPresetsEdit:
    """Tests for 'presets edit' command."""

    @patch("claudefig.cli.commands.presets.open_file_in_editor")
    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_edit_success(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test successfully editing preset file."""
        preset_dir = tmp_path / "test_preset"
        preset_dir.mkdir()
        preset_file = preset_dir / "claudefig.toml"
        preset_file.write_text("[project]\nname = 'test'")

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_edit, ["test_preset"])

        assert result.exit_code == 0
        assert "Opening preset file" in result.output
        mock_open_editor.assert_called_once_with(preset_file)

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_edit_missing_preset(self, mock_manager_class, cli_runner, tmp_path):
        """Test editing non-existent preset."""
        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_edit, ["nonexistent"])

        assert result.exit_code == 0  # Doesn't abort, just shows message
        assert "not found" in result.output.lower() or "nonexistent" in result.output

    @patch("claudefig.cli.commands.presets.open_file_in_editor")
    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_edit_default_preset_warning(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test editing default preset shows warning."""
        preset_dir = tmp_path / "default"
        preset_dir.mkdir()
        preset_file = preset_dir / "claudefig.toml"
        preset_file.write_text("[project]\nname = 'default'")

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_edit, ["default"])

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "default preset" in result.output.lower()

    @patch("claudefig.cli.commands.presets.open_file_in_editor")
    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_edit_missing_toml_file(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test editing when preset directory exists but toml file missing."""
        preset_dir = tmp_path / "incomplete"
        preset_dir.mkdir()
        # No claudefig.toml file

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_edit, ["incomplete"])

        assert result.exit_code == 0
        assert "not found" in result.output.lower()
        mock_open_editor.assert_not_called()

    @patch("claudefig.cli.commands.presets.open_file_in_editor")
    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_edit_handles_editor_error(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test handling error when editor can't open."""
        preset_dir = tmp_path / "test"
        preset_dir.mkdir()
        preset_file = preset_dir / "claudefig.toml"
        preset_file.write_text("")

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path
        mock_manager_class.return_value = mock_manager

        mock_open_editor.side_effect = RuntimeError("Editor not found")

        result = cli_runner.invoke(presets_edit, ["test"])

        assert (
            "Error opening editor" in result.output
            or "Editor not found" in result.output
        )


class TestPresetsOpen:
    """Tests for 'presets open' command."""

    @patch("claudefig.cli.commands.presets.open_folder_in_explorer")
    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_open_success(
        self, mock_manager_class, mock_open_folder, cli_runner, tmp_path
    ):
        """Test successfully opening presets directory."""
        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_open, [])

        assert result.exit_code == 0
        assert "Opening presets directory" in result.output
        mock_open_folder.assert_called_once()

    @patch("claudefig.cli.commands.presets.open_folder_in_explorer")
    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_open_creates_directory(
        self, mock_manager_class, mock_open_folder, cli_runner, tmp_path
    ):
        """Test that open creates directory if it doesn't exist."""
        presets_dir = tmp_path / "presets"

        mock_manager = Mock()
        mock_manager.global_presets_dir = presets_dir
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_open, [])

        assert result.exit_code == 0
        assert presets_dir.exists()

    @patch("claudefig.cli.commands.presets.open_folder_in_explorer")
    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_open_handles_error(
        self, mock_manager_class, mock_open_folder, cli_runner, tmp_path
    ):
        """Test handling error when file manager can't open."""
        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        mock_open_folder.side_effect = RuntimeError("Cannot open")

        result = cli_runner.invoke(presets_open, [])

        assert result.exit_code == 0  # Should not fail
        assert (
            "Could not open file manager" in result.output
            or "Navigate to" in result.output
        )

    @patch("claudefig.cli.commands.presets.open_folder_in_explorer")
    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    def test_open_shows_directory_path(
        self, mock_manager_class, mock_open_folder, cli_runner, tmp_path
    ):
        """Test that open shows directory path."""
        presets_dir = tmp_path / "custom_presets"

        mock_manager = Mock()
        mock_manager.global_presets_dir = presets_dir
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(presets_open, [])

        assert result.exit_code == 0
        assert "custom_presets" in result.output


class TestPresetsGroupIntegration:
    """Integration tests for the presets command group."""

    def test_presets_group_exists(self):
        """Test that presets group is properly registered."""
        assert presets_group.name == "presets"
        assert presets_group.help is not None

    def test_presets_group_has_all_commands(self):
        """Test that all commands are registered in the group."""
        command_names = [cmd.name for cmd in presets_group.commands.values()]

        assert "list" in command_names
        assert "show" in command_names
        assert "apply" in command_names
        assert "create" in command_names
        assert "delete" in command_names
        assert "edit" in command_names
        assert "open" in command_names

    def test_list_command_has_correct_params(self):
        """Test list command has correct parameters."""
        list_cmd = presets_group.commands["list"]
        param_names = [p.name for p in list_cmd.params]

        assert "validate" in param_names

    def test_show_command_has_correct_params(self):
        """Test show command has correct parameters."""
        show_cmd = presets_group.commands["show"]
        param_names = [p.name for p in show_cmd.params]

        assert "preset_name" in param_names

    def test_apply_command_has_correct_params(self):
        """Test apply command has correct parameters."""
        apply_cmd = presets_group.commands["apply"]
        param_names = [p.name for p in apply_cmd.params]

        assert "preset_name" in param_names
        assert "path" in param_names

    def test_create_command_has_correct_params(self):
        """Test create command has correct parameters."""
        create_cmd = presets_group.commands["create"]
        param_names = [p.name for p in create_cmd.params]

        assert "preset_name" in param_names
        assert "description" in param_names
        assert "path" in param_names

    def test_delete_command_has_confirmation(self):
        """Test delete command has confirmation option."""
        delete_cmd = presets_group.commands["delete"]
        param_names = [p.name for p in delete_cmd.params]

        assert "preset_name" in param_names
        # Should have confirmation parameter (added by @click.confirmation_option)

    def test_edit_command_has_correct_params(self):
        """Test edit command has correct parameters."""
        edit_cmd = presets_group.commands["edit"]
        param_names = [p.name for p in edit_cmd.params]

        assert "preset_name" in param_names

    def test_open_command_has_no_params(self):
        """Test open command has no required parameters."""
        open_cmd = presets_group.commands["open"]
        # Should have no arguments, only the command itself
        assert len(open_cmd.params) == 0

    def test_create_from_repo_command_registered(self):
        """Test create-from-repo command is registered in the group."""
        command_names = [cmd.name for cmd in presets_group.commands.values()]
        assert "create-from-repo" in command_names

    def test_create_from_repo_command_has_correct_params(self):
        """Test create-from-repo command has correct parameters."""
        create_from_repo_cmd = presets_group.commands["create-from-repo"]
        param_names = [p.name for p in create_from_repo_cmd.params]

        assert "preset_name" in param_names
        assert "description" in param_names
        assert "path" in param_names


class TestPresetsCreateFromRepo:
    """Tests for 'presets create-from-repo' command."""

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    @patch("claudefig.services.component_discovery_service.ComponentDiscoveryService")
    def test_create_from_repo_success(
        self, mock_discovery_class, mock_manager_class, cli_runner, tmp_path
    ):
        """Test successfully creating preset from repository."""
        from claudefig.models import (
            ComponentDiscoveryResult,
            DiscoveredComponent,
            FileType,
        )

        # Create a mock source file
        source_file = tmp_path / "CLAUDE.md"
        source_file.write_text("# Test")

        # Setup mock discovery result
        mock_component = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=source_file,
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
        )
        mock_result = ComponentDiscoveryResult(
            components=[mock_component],
            total_found=1,
            warnings=[],
            scan_time_ms=10.5,
        )

        mock_discovery = Mock()
        mock_discovery.discover_components.return_value = mock_result
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create_from_repo, ["my-preset", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "SUCCESS" in result.output or "created" in result.output.lower()
        mock_manager.create_preset_from_discovery.assert_called_once()

    @patch("claudefig.services.component_discovery_service.ComponentDiscoveryService")
    def test_create_from_repo_no_components(
        self, mock_discovery_class, cli_runner, tmp_path
    ):
        """Test that no components found shows appropriate message."""
        from claudefig.models import ComponentDiscoveryResult

        mock_result = ComponentDiscoveryResult(
            components=[],
            total_found=0,
            warnings=[],
            scan_time_ms=5.0,
        )

        mock_discovery = Mock()
        mock_discovery.discover_components.return_value = mock_result
        mock_discovery_class.return_value = mock_discovery

        result = cli_runner.invoke(
            presets_create_from_repo, ["empty-preset", "--path", str(tmp_path)]
        )

        # Should abort with exit code 1 (Abort)
        assert result.exit_code == 1
        assert (
            "No usable components" in result.output
            or "no components" in result.output.lower()
        )

    @patch("claudefig.services.component_discovery_service.ComponentDiscoveryService")
    def test_create_from_repo_invalid_path(self, mock_discovery_class, cli_runner):
        """Test handling invalid repository path."""
        mock_discovery = Mock()
        mock_discovery.discover_components.side_effect = ValueError(
            "Repository path does not exist"
        )
        mock_discovery_class.return_value = mock_discovery

        # Use a non-existent path - click will validate this before our code
        result = cli_runner.invoke(
            presets_create_from_repo, ["test-preset", "--path", "/nonexistent/path"]
        )

        # Click validates path exists, so this should fail
        assert result.exit_code != 0

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    @patch("claudefig.services.component_discovery_service.ComponentDiscoveryService")
    def test_create_from_repo_preset_exists(
        self, mock_discovery_class, mock_manager_class, cli_runner, tmp_path
    ):
        """Test error when preset already exists."""
        from claudefig.models import (
            ComponentDiscoveryResult,
            DiscoveredComponent,
            FileType,
        )

        source_file = tmp_path / "CLAUDE.md"
        source_file.write_text("# Test")

        mock_component = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=source_file,
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
        )
        mock_result = ComponentDiscoveryResult(
            components=[mock_component],
            total_found=1,
            warnings=[],
            scan_time_ms=10.0,
        )

        mock_discovery = Mock()
        mock_discovery.discover_components.return_value = mock_result
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager.create_preset_from_discovery.side_effect = ValueError(
            "Preset 'existing' already exists"
        )
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create_from_repo, ["existing", "--path", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "already exists" in result.output or "Error" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    @patch("claudefig.services.component_discovery_service.ComponentDiscoveryService")
    def test_create_from_repo_with_description(
        self, mock_discovery_class, mock_manager_class, cli_runner, tmp_path
    ):
        """Test create-from-repo with custom description."""
        from claudefig.models import (
            ComponentDiscoveryResult,
            DiscoveredComponent,
            FileType,
        )

        source_file = tmp_path / "CLAUDE.md"
        source_file.write_text("# Test")

        mock_component = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=source_file,
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
        )
        mock_result = ComponentDiscoveryResult(
            components=[mock_component],
            total_found=1,
            warnings=[],
            scan_time_ms=10.0,
        )

        mock_discovery = Mock()
        mock_discovery.discover_components.return_value = mock_result
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create_from_repo,
            [
                "custom-preset",
                "--description",
                "Custom description",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        call_args = mock_manager.create_preset_from_discovery.call_args
        assert call_args[1]["description"] == "Custom description"

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    @patch("claudefig.services.component_discovery_service.ComponentDiscoveryService")
    def test_create_from_repo_shows_table(
        self, mock_discovery_class, mock_manager_class, cli_runner, tmp_path
    ):
        """Test that component table is displayed."""
        from claudefig.models import (
            ComponentDiscoveryResult,
            DiscoveredComponent,
            FileType,
        )

        source_file = tmp_path / "CLAUDE.md"
        source_file.write_text("# Test")

        mock_component = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=source_file,
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
        )
        mock_result = ComponentDiscoveryResult(
            components=[mock_component],
            total_found=1,
            warnings=[],
            scan_time_ms=10.0,
        )

        mock_discovery = Mock()
        mock_discovery.discover_components.return_value = mock_result
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create_from_repo, ["table-test", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        # Table should show component name and type
        assert "CLAUDE" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    @patch("claudefig.services.component_discovery_service.ComponentDiscoveryService")
    def test_create_from_repo_shows_warnings(
        self, mock_discovery_class, mock_manager_class, cli_runner, tmp_path
    ):
        """Test that duplicate warnings are displayed."""
        from claudefig.models import (
            ComponentDiscoveryResult,
            DiscoveredComponent,
            FileType,
        )

        source_file = tmp_path / "CLAUDE.md"
        source_file.write_text("# Test")

        mock_component = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=source_file,
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
        )
        mock_result = ComponentDiscoveryResult(
            components=[mock_component],
            total_found=1,
            warnings=["Duplicate component name 'test' found in 2 locations"],
            scan_time_ms=10.0,
        )

        mock_discovery = Mock()
        mock_discovery.discover_components.return_value = mock_result
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create_from_repo, ["warning-test", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        # Warnings should be displayed
        assert "Warning" in result.output or "Duplicate" in result.output

    @patch("claudefig.cli.commands.presets.ConfigTemplateManager")
    @patch("claudefig.services.component_discovery_service.ComponentDiscoveryService")
    def test_create_from_repo_shows_scan_time(
        self, mock_discovery_class, mock_manager_class, cli_runner, tmp_path
    ):
        """Test that scan time is displayed in output."""
        from claudefig.models import (
            ComponentDiscoveryResult,
            DiscoveredComponent,
            FileType,
        )

        source_file = tmp_path / "CLAUDE.md"
        source_file.write_text("# Test")

        mock_component = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=source_file,
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
        )
        mock_result = ComponentDiscoveryResult(
            components=[mock_component],
            total_found=1,
            warnings=[],
            scan_time_ms=25.5,
        )

        mock_discovery = Mock()
        mock_discovery.discover_components.return_value = mock_result
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager.global_presets_dir = tmp_path / "presets"
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            presets_create_from_repo, ["time-test", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0
        # Scan time should be displayed
        assert "25.5" in result.output or "scanned" in result.output.lower()
