"""Tests for CLI template commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from claudefig.cli import main


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


class TestTemplatesList:
    """Tests for 'claudefig templates list' command."""

    def test_list_templates_basic(self, cli_runner):
        """Test listing templates shows built-in templates."""
        result = cli_runner.invoke(main, ["templates", "list"])

        assert result.exit_code == 0
        assert "Global Config Templates" in result.output
        # Should have the 5 default templates
        assert "default" in result.output
        assert "minimal" in result.output
        assert "full" in result.output
        assert "backend" in result.output
        assert "frontend" in result.output

    def test_list_templates_with_validation(self, cli_runner):
        """Test listing templates with validation flag."""
        result = cli_runner.invoke(main, ["templates", "list", "--validate"])

        assert result.exit_code == 0
        assert "Valid" in result.output  # Validation column header


class TestTemplatesShow:
    """Tests for 'claudefig templates show' command."""

    def test_show_existing_template(self, cli_runner):
        """Test showing an existing template."""
        result = cli_runner.invoke(main, ["templates", "show", "minimal"])

        assert result.exit_code == 0
        assert "Template: minimal" in result.output
        assert "Minimal Claude Code setup" in result.output
        assert "File Count:" in result.output

    def test_show_nonexistent_template(self, cli_runner):
        """Test showing a template that doesn't exist."""
        result = cli_runner.invoke(main, ["templates", "show", "nonexistent"])

        assert result.exit_code == 0
        assert "Template not found" in result.output


class TestTemplatesApply:
    """Tests for 'claudefig templates apply' command."""

    def test_apply_template_to_project(self, cli_runner):
        """Test applying a template to a project directory."""
        with cli_runner.isolated_filesystem():
            project_dir = Path("test_project")
            project_dir.mkdir()

            result = cli_runner.invoke(
                main, ["templates", "apply", "minimal", "--path", str(project_dir)]
            )

            assert result.exit_code == 0
            assert "applied successfully" in result.output
            assert (project_dir / ".claudefig.toml").exists()

    def test_apply_template_existing_config(self, cli_runner):
        """Test applying template when config already exists."""
        with cli_runner.isolated_filesystem():
            project_dir = Path("test_project")
            project_dir.mkdir()

            # Create existing config
            config_file = project_dir / ".claudefig.toml"
            config_file.write_text("existing", encoding="utf-8")

            result = cli_runner.invoke(
                main, ["templates", "apply", "minimal", "--path", str(project_dir)]
            )

            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_apply_nonexistent_template(self, cli_runner):
        """Test applying a template that doesn't exist."""
        with cli_runner.isolated_filesystem():
            project_dir = Path("test_project")
            project_dir.mkdir()

            result = cli_runner.invoke(
                main, ["templates", "apply", "nonexistent", "--path", str(project_dir)]
            )

            assert result.exit_code == 1
            assert "Template not found" in result.output


class TestTemplatesDelete:
    """Tests for 'claudefig templates delete' command."""

    def test_delete_default_template_error(self, cli_runner):
        """Test that deleting 'default' template raises error."""
        result = cli_runner.invoke(
            main, ["templates", "delete", "default"], input="y\n"
        )

        assert result.exit_code == 1
        assert "Cannot delete default preset" in result.output

    def test_delete_nonexistent_template(self, cli_runner):
        """Test deleting a template that doesn't exist."""
        result = cli_runner.invoke(
            main, ["templates", "delete", "nonexistent"], input="y\n"
        )

        assert result.exit_code == 1
        assert "Template not found" in result.output


class TestTemplatesSave:
    """Tests for 'claudefig templates save' command."""

    def test_save_template_no_config(self, cli_runner):
        """Test saving template when no config exists in project."""
        with cli_runner.isolated_filesystem():
            project_dir = Path("test_project")
            project_dir.mkdir()

            result = cli_runner.invoke(
                main,
                [
                    "templates",
                    "save",
                    "my_template",
                    "--path",
                    str(project_dir),
                ],
            )

            assert result.exit_code == 1
            assert "No .claudefig.toml found" in result.output
