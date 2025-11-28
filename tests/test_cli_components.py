"""Tests for CLI components commands."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from claudefig.cli.commands.components import (
    _load_component_metadata,
    components_edit,
    components_group,
    components_list,
    components_open,
    components_show,
)


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_components_dir(tmp_path):
    """Create a mock components directory structure."""
    components_dir = tmp_path / "components"
    components_dir.mkdir()

    # Create sample components
    claude_md_dir = components_dir / "claude_md"
    claude_md_dir.mkdir()

    # Component 1: default
    default_comp = claude_md_dir / "default"
    default_comp.mkdir()
    (default_comp / "content.md").write_text("# Default Component")
    (default_comp / "component.toml").write_text(
        '[component]\nname = "default"\ntype = "claude_md"\ndescription = "Default component"\nversion = "1.0.0"'
    )

    # Component 2: test
    test_comp = claude_md_dir / "test"
    test_comp.mkdir()
    (test_comp / "content.md").write_text("# Test Component")

    return components_dir


@pytest.fixture
def sample_components():
    """Create sample component data."""
    return [
        {
            "name": "default",
            "type": "claude_md",
            "source": "global",
            "path": Path("/fake/path/claude_md/default"),
        },
        {
            "name": "test",
            "type": "claude_md",
            "source": "preset",
            "path": Path("/fake/path/preset/claude_md/test"),
        },
        {
            "name": "config",
            "type": "settings_json",
            "source": "global",
            "path": Path("/fake/path/settings_json/config"),
        },
    ]


class TestLoadComponentMetadata:
    """Tests for _load_component_metadata helper function."""

    def test_loads_valid_metadata(self, tmp_path):
        """Test loading valid component.toml metadata."""
        component_dir = tmp_path / "component"
        component_dir.mkdir()

        toml_content = """
[component]
name = "test-component"
type = "claude_md"
description = "Test description"
version = "1.0.0"

[metadata]
author = "Test Author"
tags = ["test", "example"]
"""
        (component_dir / "component.toml").write_text(toml_content)

        result = _load_component_metadata(component_dir)

        assert result is not None
        assert "component" in result
        assert result["component"]["name"] == "test-component"
        assert result["component"]["description"] == "Test description"
        assert "metadata" in result
        assert result["metadata"]["author"] == "Test Author"

    def test_returns_none_when_file_missing(self, tmp_path):
        """Test returns None when component.toml doesn't exist."""
        component_dir = tmp_path / "component"
        component_dir.mkdir()

        result = _load_component_metadata(component_dir)

        assert result is None

    def test_returns_none_on_invalid_toml(self, tmp_path):
        """Test returns None when TOML is invalid."""
        component_dir = tmp_path / "component"
        component_dir.mkdir()

        # Invalid TOML
        (component_dir / "component.toml").write_text("[invalid toml content {{{")

        result = _load_component_metadata(component_dir)

        assert result is None

    def test_returns_none_when_tomli_unavailable(self, tmp_path, monkeypatch):
        """Test returns None when tomli/tomllib not available."""
        component_dir = tmp_path / "component"
        component_dir.mkdir()
        (component_dir / "component.toml").write_text("[component]\nname = 'test'")

        # Mock tomllib as None (simulating Python < 3.11 without tomli)
        import claudefig.cli.commands.components as comp_module

        original_tomllib = comp_module.tomllib
        comp_module.tomllib = None

        try:
            result = _load_component_metadata(component_dir)
            assert result is None
        finally:
            comp_module.tomllib = original_tomllib

    def test_handles_empty_toml(self, tmp_path):
        """Test handles empty TOML file."""
        component_dir = tmp_path / "component"
        component_dir.mkdir()
        (component_dir / "component.toml").write_text("")

        result = _load_component_metadata(component_dir)

        # Empty TOML should parse successfully as empty dict
        assert result == {}

    def test_handles_minimal_metadata(self, tmp_path):
        """Test handles minimal metadata with only required fields."""
        component_dir = tmp_path / "component"
        component_dir.mkdir()
        (component_dir / "component.toml").write_text('[component]\nname = "minimal"')

        result = _load_component_metadata(component_dir)

        assert result is not None
        assert "component" in result
        assert result["component"]["name"] == "minimal"


class TestComponentsList:
    """Tests for 'components list' command."""

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_list_all_components(
        self, mock_get_dir, mock_manager_class, cli_runner, sample_components
    ):
        """Test listing all components without filter."""
        mock_get_dir.return_value = Path("/fake/components")
        mock_manager = Mock()
        mock_manager.list_components.return_value = sample_components
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_list, [])

        assert result.exit_code == 0
        assert "default" in result.output
        assert "test" in result.output
        assert "config" in result.output
        mock_manager.list_components.assert_called_once()

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_list_filtered_by_type(self, mock_get_dir, mock_manager_class, cli_runner):
        """Test listing components filtered by file type."""
        mock_get_dir.return_value = Path("/fake/components")
        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {
                "name": "default",
                "type": "claude_md",
                "source": "global",
                "path": Path("/fake/path"),
            }
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_list, ["claude_md"])

        assert result.exit_code == 0
        assert "default" in result.output
        mock_manager.list_components.assert_called_once_with(
            "default", type="claude_md"
        )

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_list_by_preset(self, mock_get_dir, mock_manager_class, cli_runner):
        """Test listing components for specific preset."""
        mock_get_dir.return_value = Path("/fake/components")
        mock_manager = Mock()
        mock_manager.list_components.return_value = []
        mock_manager_class.return_value = mock_manager

        cli_runner.invoke(components_list, ["--preset", "custom-preset"])

        mock_manager.list_components.assert_called_once_with("custom-preset", type=None)

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_list_empty_results(self, mock_get_dir, mock_manager_class, cli_runner):
        """Test listing when no components found."""
        components_path = Path("/fake/components")
        mock_get_dir.return_value = components_path
        mock_manager = Mock()
        mock_manager.list_components.return_value = []
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_list, [])

        assert result.exit_code == 0
        assert "No components found" in result.output
        assert str(components_path) in result.output

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_list_invalid_file_type(self, mock_manager_class, cli_runner):
        """Test listing with invalid file type."""
        result = cli_runner.invoke(components_list, ["invalid_type"])

        # Click returns exit code 2 for UsageError (bad parameter)
        assert result.exit_code == 2
        assert "Invalid file type" in result.output
        # Should show valid types
        assert "claude_md" in result.output or "Valid types" in result.output

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_list_groups_by_type(self, mock_get_dir, mock_manager_class, cli_runner):
        """Test that components are grouped by type in output."""
        mock_get_dir.return_value = Path("/fake/components")
        components = [
            {
                "name": "comp1",
                "type": "claude_md",
                "source": "global",
                "path": Path("/fake1"),
            },
            {
                "name": "comp2",
                "type": "claude_md",
                "source": "global",
                "path": Path("/fake2"),
            },
            {
                "name": "comp3",
                "type": "settings_json",
                "source": "global",
                "path": Path("/fake3"),
            },
        ]
        mock_manager = Mock()
        mock_manager.list_components.return_value = components
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_list, [])

        assert result.exit_code == 0
        # Should show type headers
        output = result.output
        assert "Claude" in output or "Settings" in output  # Type display names

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_list_shows_source_labels(
        self, mock_get_dir, mock_manager_class, cli_runner
    ):
        """Test that list shows global vs preset source labels."""
        mock_get_dir.return_value = Path("/fake/components")
        components = [
            {
                "name": "global_comp",
                "type": "claude_md",
                "source": "global",
                "path": Path("/fake1"),
            },
            {
                "name": "preset_comp",
                "type": "claude_md",
                "source": "preset",
                "path": Path("/fake2"),
            },
        ]
        mock_manager = Mock()
        mock_manager.list_components.return_value = components
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_list, [])

        assert result.exit_code == 0
        assert "global_comp" in result.output
        assert "preset_comp" in result.output
        # Should contain source indicators
        assert "(global)" in result.output or "(preset)" in result.output

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components.get_components_dir")
    @patch("claudefig.cli.commands.components._load_component_metadata")
    def test_list_shows_descriptions(
        self, mock_load_meta, mock_get_dir, mock_manager_class, cli_runner
    ):
        """Test that list shows component descriptions when available."""
        mock_get_dir.return_value = Path("/fake/components")
        mock_load_meta.return_value = {
            "component": {"description": "Test component description"}
        }

        components = [
            {
                "name": "described",
                "type": "claude_md",
                "source": "global",
                "path": Path("/fake"),
            },
        ]
        mock_manager = Mock()
        mock_manager.list_components.return_value = components
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_list, [])

        assert result.exit_code == 0
        assert "Test component description" in result.output

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_list_empty_with_type_filter(
        self, mock_get_dir, mock_manager_class, cli_runner
    ):
        """Test listing empty results with type filter shows specific message."""
        mock_get_dir.return_value = Path("/fake/components")
        mock_manager = Mock()
        mock_manager.list_components.return_value = []
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_list, ["claude_md"])

        assert result.exit_code == 0
        assert "No claude_md components found" in result.output


class TestComponentsShow:
    """Tests for 'components show' command."""

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components._load_component_metadata")
    def test_show_valid_component(
        self, mock_load_meta, mock_manager_class, cli_runner, tmp_path
    ):
        """Test showing valid component details."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        (comp_path / "content.md").write_text("# Test")

        mock_load_meta.return_value = {
            "component": {
                "name": "test",
                "description": "Test component",
                "version": "1.0.0",
            }
        }

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "global", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_show, ["claude_md", "test"])

        assert result.exit_code == 0
        assert "Component Details" in result.output
        assert "test" in result.output
        assert "Test component" in result.output
        assert "1.0.0" in result.output

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components._load_component_metadata")
    def test_show_with_metadata(
        self, mock_load_meta, mock_manager_class, cli_runner, tmp_path
    ):
        """Test showing component with full metadata."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        (comp_path / "content.md").write_text("# Test", encoding="utf-8")

        mock_load_meta.return_value = {
            "component": {
                "name": "test",
                "description": "Test description",
                "version": "2.0.0",
            },
            "metadata": {
                "author": "Test Author",
                "tags": ["test", "example"],
            },
            "dependencies": {
                "requires": ["dep1", "dep2"],
                "recommends": ["opt1"],
            },
        }

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "global", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_show, ["claude_md", "test"])

        assert result.exit_code == 0
        assert "Test Author" in result.output
        assert "test, example" in result.output or "test" in result.output
        assert "dep1" in result.output
        assert "opt1" in result.output

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_show_missing_component(self, mock_manager_class, cli_runner):
        """Test showing non-existent component."""
        mock_manager = Mock()
        mock_manager.list_components.return_value = []
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_show, ["claude_md", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "nonexistent" in result.output

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_show_invalid_file_type(self, mock_manager_class, cli_runner):
        """Test showing component with invalid file type."""
        result = cli_runner.invoke(components_show, ["invalid_type", "test"])

        # Click returns exit code 2 for UsageError (bad parameter)
        assert result.exit_code == 2
        assert "Invalid file type" in result.output

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components._load_component_metadata")
    def test_show_without_metadata_file(
        self, mock_load_meta, mock_manager_class, cli_runner, tmp_path
    ):
        """Test showing component without component.toml."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        (comp_path / "content.md").write_text("# Test")
        (comp_path / "other.txt").write_text("Other file")

        mock_load_meta.return_value = None

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "global", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_show, ["claude_md", "test"])

        assert result.exit_code == 0
        # Should still show files
        assert "content.md" in result.output
        assert "other.txt" in result.output

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components._load_component_metadata")
    def test_show_displays_file_sizes(
        self, mock_load_meta, mock_manager_class, cli_runner, tmp_path
    ):
        """Test that show displays file sizes."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        # Create a file with known size
        (comp_path / "content.md").write_text("# Test Content\n" * 100)

        mock_load_meta.return_value = {"component": {"name": "test"}}

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "global", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_show, ["claude_md", "test"])

        assert result.exit_code == 0
        assert "content.md" in result.output
        assert "KB" in result.output  # Should show size in KB

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    @patch("claudefig.cli.commands.components._load_component_metadata")
    def test_show_preset_component(
        self, mock_load_meta, mock_manager_class, cli_runner, tmp_path
    ):
        """Test showing preset-specific component."""
        comp_path = tmp_path / "preset_component"
        comp_path.mkdir()
        (comp_path / "content.md").write_text("# Preset")

        mock_load_meta.return_value = {"component": {"name": "preset_comp"}}

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {
                "name": "preset_comp",
                "type": "claude_md",
                "source": "preset",
                "path": comp_path,
            }
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            components_show, ["claude_md", "preset_comp", "--preset", "custom"]
        )

        assert result.exit_code == 0
        assert "Preset-specific" in result.output or "preset" in result.output.lower()


class TestComponentsOpen:
    """Tests for 'components open' command."""

    @patch("claudefig.cli.commands.components.open_folder_in_explorer")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_open_global_directory(
        self, mock_get_dir, mock_open_folder, cli_runner, tmp_path
    ):
        """Test opening global components directory."""
        mock_get_dir.return_value = tmp_path / "components"

        result = cli_runner.invoke(components_open, [])

        assert result.exit_code == 0
        mock_open_folder.assert_called_once()
        assert "Opening components directory" in result.output

    @patch("claudefig.cli.commands.components.open_folder_in_explorer")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_open_specific_type(
        self, mock_get_dir, mock_open_folder, cli_runner, tmp_path
    ):
        """Test opening specific file type directory."""
        components_dir = tmp_path / "components"
        mock_get_dir.return_value = components_dir

        result = cli_runner.invoke(components_open, ["claude_md"])

        assert result.exit_code == 0
        # Should open claude_md subdirectory
        call_arg = mock_open_folder.call_args[0][0]
        assert call_arg.name == "claude_md"
        assert call_arg.parent == components_dir

    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_open_creates_directory(self, mock_get_dir, cli_runner, tmp_path):
        """Test that open creates directory if it doesn't exist."""
        components_dir = tmp_path / "components"
        mock_get_dir.return_value = components_dir

        with patch("claudefig.cli.commands.components.open_folder_in_explorer"):
            result = cli_runner.invoke(components_open, ["settings_json"])

        assert result.exit_code == 0
        # Directory should be created
        assert (components_dir / "settings_json").exists()

    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_open_invalid_type(self, mock_get_dir, cli_runner, tmp_path):
        """Test opening with invalid file type."""
        mock_get_dir.return_value = tmp_path / "components"

        result = cli_runner.invoke(components_open, ["invalid_type"])

        # Click returns exit code 2 for UsageError (bad parameter)
        assert result.exit_code == 2
        assert "Invalid file type" in result.output

    @patch("claudefig.cli.commands.components.open_folder_in_explorer")
    @patch("claudefig.cli.commands.components.get_components_dir")
    def test_open_handles_error(
        self, mock_get_dir, mock_open_folder, cli_runner, tmp_path
    ):
        """Test handling error when file manager can't open."""
        mock_get_dir.return_value = tmp_path / "components"
        mock_open_folder.side_effect = RuntimeError("Cannot open")

        result = cli_runner.invoke(components_open, [])

        assert result.exit_code == 0  # Should not fail
        assert (
            "Could not open file manager" in result.output
            or "Cannot open" in result.output
        )


class TestComponentsEdit:
    """Tests for 'components edit' command."""

    @patch("claudefig.cli.commands.components.open_file_in_editor")
    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_edit_finds_primary_file(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test editing component finds primary content file."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        content_file = comp_path / "content.md"
        content_file.write_text("# Test")

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "global", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_edit, ["claude_md", "test"])

        assert result.exit_code == 0
        mock_open_editor.assert_called_once_with(content_file)
        assert "Opening component file" in result.output

    @patch("claudefig.cli.commands.components.open_file_in_editor")
    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_edit_missing_component(
        self, mock_manager_class, mock_open_editor, cli_runner
    ):
        """Test editing non-existent component."""
        mock_manager = Mock()
        mock_manager.list_components.return_value = []
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_edit, ["claude_md", "missing"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "missing" in result.output
        mock_open_editor.assert_not_called()

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_edit_no_content_files(self, mock_manager_class, cli_runner, tmp_path):
        """Test editing component with no editable files."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        # Only a .toml file, no content
        (comp_path / "component.toml").write_text("")

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "global", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_edit, ["claude_md", "test"])

        assert result.exit_code == 1
        assert "No editable content file found" in result.output

    @patch("claudefig.cli.commands.components.open_file_in_editor")
    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_edit_preset_warning(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test editing preset-specific component shows warning."""
        comp_path = tmp_path / "preset_component"
        comp_path.mkdir()
        (comp_path / "content.md").write_text("# Preset")

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {
                "name": "preset_comp",
                "type": "claude_md",
                "source": "preset",
                "path": comp_path,
            }
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_edit, ["claude_md", "preset_comp"])

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "preset" in result.output.lower()

    @patch("claudefig.cli.commands.components.open_file_in_editor")
    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_edit_prefers_content_md(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test edit prefers content.md over other files."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        (comp_path / "README.md").write_text("# README")
        content_file = comp_path / "content.md"
        content_file.write_text("# Content")
        (comp_path / "other.txt").write_text("Other")

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "global", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_edit, ["claude_md", "test"])

        assert result.exit_code == 0
        # Should prefer content.md
        mock_open_editor.assert_called_once_with(content_file)

    @patch("claudefig.cli.commands.components.open_file_in_editor")
    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_edit_fallback_to_first_file(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test edit falls back to first non-.toml file if no known content files."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        (comp_path / "component.toml").write_text("")
        first_file = comp_path / "some_file.txt"
        first_file.write_text("Content")

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "global", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(components_edit, ["claude_md", "test"])

        assert result.exit_code == 0
        # Should use first non-.toml file
        call_arg = mock_open_editor.call_args[0][0]
        assert call_arg.name == "some_file.txt"

    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_edit_invalid_file_type(self, mock_manager_class, cli_runner):
        """Test editing with invalid file type."""
        result = cli_runner.invoke(components_edit, ["invalid_type", "test"])

        # Click returns exit code 2 for UsageError (bad parameter)
        assert result.exit_code == 2
        assert "Invalid file type" in result.output

    @patch("claudefig.cli.commands.components.open_file_in_editor")
    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_edit_with_custom_preset(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test editing component from custom preset."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        (comp_path / "content.md").write_text("# Test")

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "preset", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(
            components_edit, ["claude_md", "test", "--preset", "custom"]
        )

        assert result.exit_code == 0
        mock_manager.list_components.assert_called_once_with("custom", type="claude_md")

    @patch("claudefig.cli.commands.components.open_file_in_editor")
    @patch("claudefig.cli.commands.components.FileTemplateManager")
    def test_edit_handles_editor_error(
        self, mock_manager_class, mock_open_editor, cli_runner, tmp_path
    ):
        """Test handling error when editor can't open."""
        comp_path = tmp_path / "test_component"
        comp_path.mkdir()
        (comp_path / "content.md").write_text("# Test")

        mock_manager = Mock()
        mock_manager.list_components.return_value = [
            {"name": "test", "type": "claude_md", "source": "global", "path": comp_path}
        ]
        mock_manager_class.return_value = mock_manager

        mock_open_editor.side_effect = RuntimeError("Editor not found")

        result = cli_runner.invoke(components_edit, ["claude_md", "test"])

        # Should handle the error gracefully (decorator should catch it)
        assert (
            "Error opening editor" in result.output
            or "Editor not found" in result.output
        )


class TestComponentsGroupIntegration:
    """Integration tests for the components command group."""

    def test_components_group_exists(self):
        """Test that components group is properly registered."""
        assert components_group.name == "components"
        assert components_group.help is not None

    def test_components_group_has_all_commands(self):
        """Test that all commands are registered in the group."""
        command_names = [cmd.name for cmd in components_group.commands.values()]

        assert "list" in command_names
        assert "show" in command_names
        assert "open" in command_names
        assert "edit" in command_names

    def test_list_command_has_correct_params(self):
        """Test list command has correct parameters."""
        list_cmd = components_group.commands["list"]
        param_names = [p.name for p in list_cmd.params]

        assert "file_type" in param_names
        assert "preset" in param_names

    def test_show_command_has_correct_params(self):
        """Test show command has correct parameters."""
        show_cmd = components_group.commands["show"]
        param_names = [p.name for p in show_cmd.params]

        assert "file_type" in param_names
        assert "component_name" in param_names
        assert "preset" in param_names

    def test_edit_command_has_correct_params(self):
        """Test edit command has correct parameters."""
        edit_cmd = components_group.commands["edit"]
        param_names = [p.name for p in edit_cmd.params]

        assert "file_type" in param_names
        assert "component_name" in param_names
        assert "preset" in param_names
