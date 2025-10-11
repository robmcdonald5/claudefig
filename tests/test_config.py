"""Tests for Config class - focusing on error handling and edge cases."""

from unittest.mock import patch

import pytest

from claudefig.config import Config


class TestConfigCorruption:
    """Tests for handling corrupted or malformed config files.

    NOTE: These tests document CURRENT behavior. Config currently raises
    TOMLDecodeError for malformed files instead of handling gracefully.
    This is a known issue that should be fixed in the future.
    """

    def test_load_malformed_toml_syntax(self, tmp_path):
        """Test loading config with TOML syntax errors.

        CURRENT: Raises TOMLDecodeError
        IDEAL: Should fall back to defaults with warning
        """
        import sys
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        config_file = tmp_path / ".claudefig.toml"
        # Write invalid TOML with syntax error
        config_file.write_text("[incomplete", encoding="utf-8")

        # Currently raises TOMLDecodeError - this documents the issue
        with pytest.raises(tomllib.TOMLDecodeError):
            Config(config_path=config_file)

    def test_load_malformed_toml_unclosed_table(self, tmp_path):
        """Test loading config with unclosed table.

        CURRENT: Raises TOMLDecodeError
        IDEAL: Should fall back to defaults with warning
        """
        import sys
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        config_file = tmp_path / ".claudefig.toml"
        # Unclosed table
        config_file.write_text(
            """[claudefig
            version = "2.0"
            """,
            encoding="utf-8",
        )

        with pytest.raises(tomllib.TOMLDecodeError):
            Config(config_path=config_file)

    def test_load_malformed_toml_invalid_value(self, tmp_path):
        """Test loading config with invalid value syntax.

        CURRENT: Raises TOMLDecodeError
        IDEAL: Should fall back to defaults with warning
        """
        import sys
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        config_file = tmp_path / ".claudefig.toml"
        # Invalid value (unquoted string)
        config_file.write_text(
            """[claudefig]
            version = 2.0
            template_source = invalid value without quotes
            """,
            encoding="utf-8",
        )

        with pytest.raises(tomllib.TOMLDecodeError):
            Config(config_path=config_file)

    def test_load_empty_file(self, tmp_path):
        """Test loading completely empty config file.

        CURRENT: Empty file loads as empty dict, no defaults merged
        IDEAL: Should merge with DEFAULT_CONFIG
        """
        config_file = tmp_path / ".claudefig.toml"
        config_file.write_text("", encoding="utf-8")

        config = Config(config_path=config_file)

        # Currently returns None for missing keys (should use default parameter)
        assert config.get("claudefig.version", "2.0") == "2.0"
        assert config.get("claudefig.template_source", "built-in") == "built-in"

    def test_load_missing_claudefig_section(self, tmp_path):
        """Test loading config missing [claudefig] section.

        CURRENT: Only loads what's in file, doesn't merge defaults
        IDEAL: Should merge missing sections from DEFAULT_CONFIG
        """
        config_file = tmp_path / ".claudefig.toml"
        config_file.write_text(
            """[custom]
            some_key = "value"
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)

        # Need to provide default since file doesn't have [claudefig]
        assert config.get("claudefig.version", "2.0") == "2.0"
        # Custom section is preserved
        assert config.get("custom.some_key") == "value"

    def test_load_wrong_data_types(self, tmp_path):
        """Test loading config with wrong data types."""
        config_file = tmp_path / ".claudefig.toml"
        config_file.write_text(
            """[claudefig]
            version = ["2.0"]  # Should be string, not array
            schema_version = 2.0  # Should be string, not float
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)

        # Should handle gracefully
        # Config loads TOML as-is, values may be wrong type but shouldn't crash
        result = config.get("claudefig.version")
        assert result is not None  # At minimum, should return something


class TestConfigSaveErrors:
    """Tests for error handling during config save operations."""

    def test_save_permission_denied(self, tmp_path):
        """Test saving config when write permission is denied."""
        config_file = tmp_path / ".claudefig.toml"
        config = Config()

        # Create a read-only file
        config_file.write_text("[claudefig]\nversion = \"2.0\"", encoding="utf-8")
        config_file.chmod(0o444)  # Read-only

        # Attempt to save should raise PermissionError
        with pytest.raises(PermissionError):
            config.save(config_file)

        # Cleanup
        config_file.chmod(0o644)

    def test_save_to_nonexistent_directory(self, tmp_path):
        """Test saving config to directory that doesn't exist."""
        config = Config()
        config_file = tmp_path / "nonexistent" / "subdir" / ".claudefig.toml"

        # Should raise FileNotFoundError or similar
        with pytest.raises((FileNotFoundError, OSError)):
            config.save(config_file)

    def test_save_disk_full(self, tmp_path):
        """Test saving config when disk is full."""
        import sys
        if sys.version_info >= (3, 11):
            pass
        else:
            pass

        config = Config()
        config_file = tmp_path / ".claudefig.toml"

        # We can't easily simulate disk full, but we can test the code path
        # by mocking at a lower level
        with (
            patch("builtins.open", side_effect=OSError("No space left on device")),
            pytest.raises(OSError),
        ):
            config.save(config_file)


class TestConfigGet:
    """Tests for Config.get() method edge cases."""

    def test_get_nested_missing_key(self, tmp_path):
        """Test getting nested key that doesn't exist."""
        config_file = tmp_path / ".claudefig.toml"
        config_file.write_text(
            """[claudefig]
            version = "2.0"
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)

        # Getting missing nested key with default
        result = config.get("claudefig.nonexistent.deep.key", "default_value")
        assert result == "default_value"

    def test_get_with_none_default(self):
        """Test get() with None as default value."""
        config = Config()

        result = config.get("nonexistent.key", None)
        assert result is None

    def test_get_empty_string_key(self):
        """Test get() with empty string as key."""
        config = Config()

        result = config.get("", "default")
        assert result == "default"


class TestConfigFileInstances:
    """Tests for file instance operations with error handling."""

    def test_get_file_instances_corrupted_array(self, tmp_path):
        """Test getting file instances when [[files]] is corrupted."""
        config_file = tmp_path / ".claudefig.toml"
        config_file.write_text(
            """[claudefig]
            version = "2.0"

            [[files]]
            # Missing required fields
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)

        # Should return the corrupted data (validation happens elsewhere)
        instances = config.get_file_instances()
        assert isinstance(instances, list)

    def test_add_file_instance_to_corrupted_config(self, tmp_path):
        """Test adding file instance to corrupted config.

        CURRENT: Config fails to load if TOML is malformed
        This test shows that we can't add to a corrupted config
        """
        import sys
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        config_file = tmp_path / ".claudefig.toml"
        config_file.write_text("[incomplete", encoding="utf-8")

        # Config load fails with corrupted TOML
        with pytest.raises(tomllib.TOMLDecodeError):
            Config(config_path=config_file)

    def test_add_file_instance_to_valid_config(self, tmp_path):
        """Test adding file instance to a valid (but minimal) config."""
        config_file = tmp_path / ".claudefig.toml"
        # Valid but minimal TOML
        config_file.write_text(
            """[claudefig]
            version = "2.0"
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)

        instance = {
            "id": "test",
            "type": "claude_md",
            "preset": "claude_md:default",
            "path": "CLAUDE.md",
            "enabled": True,
        }

        config.add_file_instance(instance)

        # Should have the instance now
        instances = config.get_file_instances()
        assert len(instances) == 1
        assert instances[0]["id"] == "test"
