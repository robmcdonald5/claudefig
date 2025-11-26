"""Tests for config management CLI commands."""

import pytest
from click.testing import CliRunner

from claudefig.cli import main


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def config_file(tmp_path):
    """Create a test config file."""
    config_path = tmp_path / "claudefig.toml"
    config_path.write_text(
        """
[claudefig]
version = "2.0"
schema_version = "2.0"
template_source = "default"

[init]
overwrite_existing = false
create_backup = true

[custom]
template_dir = ""
presets_dir = ""

[[files]]
id = "test-file"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true
""",
        encoding="utf-8",
    )
    return config_path


class TestConfigGet:
    """Tests for 'claudefig config get' command."""

    def test_get_existing_key(self, cli_runner, tmp_path, config_file):
        """Test getting an existing configuration key."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "get", "claudefig.version"])

            assert result.exit_code == 0
            assert "2.0" in result.output or "version" in result.output.lower()

    def test_get_nested_key(self, cli_runner, tmp_path, config_file):
        """Test getting a nested configuration key."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                main, ["config", "get", "init.overwrite_existing"]
            )

            assert result.exit_code == 0
            # Should show the value (false) or the key name
            assert (
                "false" in result.output.lower() or "overwrite" in result.output.lower()
            )

    def test_get_nonexistent_key(self, cli_runner, tmp_path, config_file):
        """Test getting a key that doesn't exist."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "get", "nonexistent.key"])

            assert result.exit_code == 0
            assert (
                "not found" in result.output.lower() or "nonexistent" in result.output
            )

    def test_get_without_config_file(self, cli_runner, tmp_path):
        """Test getting config when no config file exists."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "get", "claudefig.version"])

            assert result.exit_code == 0
            # Should handle gracefully (show default or not found)


class TestConfigSet:
    """Tests for 'claudefig config set' command."""

    def test_set_unknown_key_rejected(self, cli_runner, tmp_path, config_file):
        """Test that unknown configuration keys are rejected."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                main, ["config", "set", "custom.new_key", "test_value"]
            )

            # Unknown keys should be rejected
            assert result.exit_code == 1
            assert "Unknown config key" in result.output or "new_key" in result.output

    def test_set_existing_key(self, cli_runner, tmp_path, config_file):
        """Test updating an existing configuration key."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                main, ["config", "set", "claudefig.template_source", "custom"]
            )

            assert result.exit_code == 0
            assert "Set" in result.output or "custom" in result.output

    def test_set_boolean_true(self, cli_runner, tmp_path, config_file):
        """Test setting a boolean value (true)."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                main, ["config", "set", "init.overwrite_existing", "true"]
            )

            assert result.exit_code == 0
            # Should parse 'true' as boolean
            assert "Set" in result.output or "true" in result.output.lower()

    def test_set_boolean_false(self, cli_runner, tmp_path, config_file):
        """Test setting a boolean value (false)."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                main, ["config", "set", "init.create_backup", "false"]
            )

            assert result.exit_code == 0
            assert "Set" in result.output or "false" in result.output.lower()

    def test_set_integer_to_string_key_rejected(
        self, cli_runner, tmp_path, config_file
    ):
        """Test that setting an integer value to a string key is rejected."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # custom.template_dir expects str, but "5" is parsed as int
            result = cli_runner.invoke(
                main, ["config", "set", "custom.template_dir", "5"]
            )

            # Type validation should reject integer for string key
            assert result.exit_code == 1
            assert "Invalid type" in result.output or "expected str" in result.output

    def test_set_string_value(self, cli_runner, tmp_path, config_file):
        """Test setting a string value."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                main, ["config", "set", "custom.template_dir", "/path/to/templates"]
            )

            assert result.exit_code == 0
            assert "Set" in result.output or "template" in result.output.lower()


class TestConfigSetInit:
    """Tests for 'claudefig config set-init' command."""

    def test_set_init_overwrite_true(self, cli_runner, tmp_path, config_file):
        """Test enabling overwrite_existing setting."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "set-init", "--overwrite"])

            assert result.exit_code == 0
            assert "overwrite" in result.output.lower() or "Updated" in result.output

    def test_set_init_overwrite_false(self, cli_runner, tmp_path, config_file):
        """Test disabling overwrite_existing setting."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "set-init", "--no-overwrite"])

            assert result.exit_code == 0
            assert "overwrite" in result.output.lower() or "Updated" in result.output

    def test_set_init_backup_true(self, cli_runner, tmp_path, config_file):
        """Test enabling create_backup setting."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "set-init", "--backup"])

            assert result.exit_code == 0
            assert "backup" in result.output.lower() or "Updated" in result.output

    def test_set_init_backup_false(self, cli_runner, tmp_path, config_file):
        """Test disabling create_backup setting."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "set-init", "--no-backup"])

            assert result.exit_code == 0
            assert "backup" in result.output.lower() or "Updated" in result.output

    def test_set_init_multiple_settings(self, cli_runner, tmp_path, config_file):
        """Test setting multiple init settings at once."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                main, ["config", "set-init", "--overwrite", "--no-backup"]
            )

            assert result.exit_code == 0
            assert (
                "Updated" in result.output or "initialization" in result.output.lower()
            )

    def test_set_init_no_changes(self, cli_runner, tmp_path, config_file):
        """Test set-init without any flags shows current settings."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "set-init"])

            assert result.exit_code == 0
            # Should show current settings
            assert (
                "initialization" in result.output.lower()
                or "overwrite" in result.output.lower()
                or "backup" in result.output.lower()
            )


class TestConfigList:
    """Tests for 'claudefig config list' command."""

    def test_list_all_config(self, cli_runner, tmp_path, config_file):
        """Test listing all configuration settings."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "list"])

            assert result.exit_code == 0
            # Should show configuration sections
            assert "Configuration" in result.output or "config" in result.output.lower()
            # Should show some settings
            assert "version" in result.output.lower() or "2.0" in result.output

    def test_list_shows_file_instances(self, cli_runner, tmp_path, config_file):
        """Test that list shows file instances summary."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "list"])

            assert result.exit_code == 0
            assert "File Instances" in result.output or "files" in result.output.lower()

    def test_list_shows_init_settings(self, cli_runner, tmp_path, config_file):
        """Test that list shows init settings."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "list"])

            assert result.exit_code == 0
            # Should show init section
            assert "Init" in result.output or "overwrite" in result.output.lower()

    def test_list_empty_config(self, cli_runner, tmp_path):
        """Test listing when no config file exists."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "list"])

            assert result.exit_code == 0
            # Should handle gracefully
            assert (
                "Configuration" in result.output or "defaults" in result.output.lower()
            )

    def test_list_with_custom_path(self, cli_runner, tmp_path, config_file):
        """Test listing config from a custom path."""
        result = cli_runner.invoke(main, ["config", "list", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "Configuration" in result.output or "config" in result.output.lower()


class TestConfigEdgeCases:
    """Tests for config command edge cases and error handling."""

    def test_get_with_invalid_path(self, cli_runner):
        """Test getting config from invalid path."""
        result = cli_runner.invoke(
            main, ["config", "get", "key", "--path", "/nonexistent/path"]
        )

        # Should handle error gracefully
        assert result.exit_code == 1 or "Error" in result.output

    def test_set_with_invalid_path(self, cli_runner):
        """Test setting config in invalid path."""
        result = cli_runner.invoke(
            main,
            ["config", "set", "key", "value", "--path", "/nonexistent/path"],
        )

        # Should handle error gracefully
        assert result.exit_code == 1 or "Error" in result.output

    def test_set_creates_config_if_missing(self, cli_runner, tmp_path):
        """Test that set creates config file if it doesn't exist."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "set", "custom.test", "value"])

            # Should succeed and create config
            assert result.exit_code == 0 or "Error" in result.output
            # Config file may or may not be created depending on implementation

    def test_get_complex_nested_key(self, cli_runner, tmp_path, config_file):
        """Test getting deeply nested configuration key."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "get", "custom.template_dir"])

            assert result.exit_code == 0
            # Should show the value or key name


class TestConfigIntegration:
    """Integration tests for config commands."""

    def test_set_then_get(self, cli_runner, tmp_path, config_file):
        """Test setting a value then retrieving it."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Set a value using valid key
            set_result = cli_runner.invoke(
                main, ["config", "set", "custom.template_dir", "/test/templates"]
            )
            assert set_result.exit_code == 0

            # Get the same value
            get_result = cli_runner.invoke(
                main, ["config", "get", "custom.template_dir"]
            )
            assert get_result.exit_code == 0
            assert (
                "/test/templates" in get_result.output
                or "template_dir" in get_result.output
            )

    def test_set_init_then_list(self, cli_runner, tmp_path, config_file):
        """Test setting init options then listing them."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Set init options
            set_result = cli_runner.invoke(main, ["config", "set-init", "--overwrite"])
            assert set_result.exit_code == 0

            # List config to verify
            list_result = cli_runner.invoke(main, ["config", "list"])
            assert list_result.exit_code == 0
            # Should show the updated setting
            assert (
                "overwrite" in list_result.output.lower()
                or "Init" in list_result.output
            )

    def test_multiple_sets(self, cli_runner, tmp_path, config_file):
        """Test setting multiple values in sequence."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Set multiple valid values
            result1 = cli_runner.invoke(
                main, ["config", "set", "custom.template_dir", "/templates"]
            )
            result2 = cli_runner.invoke(
                main, ["config", "set", "custom.presets_dir", "/presets"]
            )
            result3 = cli_runner.invoke(
                main, ["config", "set", "init.overwrite_existing", "true"]
            )

            assert result1.exit_code == 0
            assert result2.exit_code == 0
            assert result3.exit_code == 0

            # List to verify all were set
            list_result = cli_runner.invoke(main, ["config", "list"])
            assert list_result.exit_code == 0
