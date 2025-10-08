"""Tests for config CLI commands."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from claudefig.cli import config_get, config_list, config_set
from claudefig.config import Config


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory with a config file."""
    config_path = tmp_path / ".claudefig.toml"
    config = Config()
    config.save(config_path)
    return tmp_path


class TestConfigGet:
    """Tests for 'claudefig config get' command."""

    def test_get_existing_key(self, runner, temp_config_dir):
        """Test getting an existing configuration key."""
        result = runner.invoke(
            config_get, ["claudefig.version", "--path", str(temp_config_dir)]
        )
        assert result.exit_code == 0
        assert "1.0" in result.output

    def test_get_nonexistent_key(self, runner, temp_config_dir):
        """Test getting a non-existent key."""
        result = runner.invoke(
            config_get, ["nonexistent.key", "--path", str(temp_config_dir)]
        )
        assert result.exit_code == 0
        assert "Key not found" in result.output

    def test_get_nested_key(self, runner, temp_config_dir):
        """Test getting a nested configuration key."""
        result = runner.invoke(
            config_get, ["claude.create_settings", "--path", str(temp_config_dir)]
        )
        assert result.exit_code == 0
        assert "False" in result.output


class TestConfigSet:
    """Tests for 'claudefig config set' command."""

    def test_set_boolean_true(self, runner, temp_config_dir):
        """Test setting a boolean value to true."""
        result = runner.invoke(
            config_set,
            ["claude.create_settings", "true", "--path", str(temp_config_dir)],
        )
        assert result.exit_code == 0
        assert "Set claude.create_settings = True" in result.output

        # Verify the value was saved
        config = Config(config_path=temp_config_dir / ".claudefig.toml")
        assert config.get("claude.create_settings") is True

    def test_set_boolean_false(self, runner, temp_config_dir):
        """Test setting a boolean value to false."""
        result = runner.invoke(
            config_set,
            ["init.create_claude_md", "false", "--path", str(temp_config_dir)],
        )
        assert result.exit_code == 0
        assert "Set init.create_claude_md = False" in result.output

        # Verify the value was saved
        config = Config(config_path=temp_config_dir / ".claudefig.toml")
        assert config.get("init.create_claude_md") is False

    def test_set_string_value(self, runner, temp_config_dir):
        """Test setting a string value."""
        result = runner.invoke(
            config_set,
            ["claudefig.template_source", "custom", "--path", str(temp_config_dir)],
        )
        assert result.exit_code == 0
        assert "Set claudefig.template_source = custom" in result.output

        # Verify the value was saved
        config = Config(config_path=temp_config_dir / ".claudefig.toml")
        assert config.get("claudefig.template_source") == "custom"

    def test_set_integer_value(self, runner, temp_config_dir):
        """Test setting an integer value."""
        result = runner.invoke(
            config_set,
            ["custom.some_number", "42", "--path", str(temp_config_dir)],
        )
        assert result.exit_code == 0
        assert "Set custom.some_number = 42" in result.output

        # Verify the value was saved
        config = Config(config_path=temp_config_dir / ".claudefig.toml")
        assert config.get("custom.some_number") == 42

    def test_set_creates_config_if_missing(self, runner, tmp_path):
        """Test that set creates config file if it doesn't exist."""
        result = runner.invoke(
            config_set, ["claude.create_hooks", "true", "--path", str(tmp_path)]
        )
        assert result.exit_code == 0

        # Verify config file was created
        config_path = tmp_path / ".claudefig.toml"
        assert config_path.exists()


class TestConfigList:
    """Tests for 'claudefig config list' command."""

    def test_list_default_config(self, runner, temp_config_dir):
        """Test listing configuration with default values."""
        result = runner.invoke(config_list, ["--path", str(temp_config_dir)])
        assert result.exit_code == 0

        # Check for key sections
        assert "Claudefig" in result.output
        assert "Init" in result.output
        assert "Claude Directory" in result.output

        # Check for specific values
        assert "version" in result.output
        assert "template_source" in result.output
        assert "create_settings" in result.output

    def test_list_with_custom_values(self, runner, temp_config_dir):
        """Test listing configuration after setting custom values."""
        # Set some custom values
        config = Config(config_path=temp_config_dir / ".claudefig.toml")
        config.set("claude.create_commands", True)
        config.set("claude.create_hooks", True)
        config.save()

        result = runner.invoke(config_list, ["--path", str(temp_config_dir)])
        assert result.exit_code == 0
        assert "True" in result.output

    def test_list_shows_config_path(self, runner, temp_config_dir):
        """Test that list shows the config file path."""
        result = runner.invoke(config_list, ["--path", str(temp_config_dir)])
        assert result.exit_code == 0
        assert ".claudefig.toml" in result.output

    def test_list_without_config_shows_defaults(self, runner, tmp_path):
        """Test listing when no config file exists."""
        result = runner.invoke(config_list, ["--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "using defaults" in result.output
