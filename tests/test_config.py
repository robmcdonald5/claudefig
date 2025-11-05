"""Tests for Config class - focusing on error handling and edge cases."""

import os
import platform
from unittest.mock import patch

import pytest

from claudefig.config import Config
from claudefig.services import config_service


class TestConfigCorruption:
    """Tests for handling corrupted or malformed config files.

    With the new architecture, Config gracefully falls back to defaults
    when encountering malformed TOML files, which is the ideal behavior.
    """

    def test_load_malformed_toml_syntax(self, tmp_path):
        """Test loading config with TOML syntax errors falls back to defaults."""
        config_file = tmp_path / "claudefig.toml"
        # Write invalid TOML with syntax error
        config_file.write_text("[incomplete", encoding="utf-8")

        # Should fall back to defaults instead of crashing
        config = Config(config_path=config_file)

        # Should use default config values
        assert config.data == config_service.DEFAULT_CONFIG
        assert config.get("claudefig.version") is not None

    def test_load_malformed_toml_unclosed_table(self, tmp_path):
        """Test loading config with unclosed table falls back to defaults."""
        config_file = tmp_path / "claudefig.toml"
        # Unclosed table
        config_file.write_text(
            """[claudefig
            version = "2.0"
            """,
            encoding="utf-8",
        )

        # Should fall back to defaults instead of crashing
        config = Config(config_path=config_file)

        # Should use default config values
        assert config.data == config_service.DEFAULT_CONFIG

    def test_load_malformed_toml_invalid_value(self, tmp_path):
        """Test loading config with invalid value syntax falls back to defaults."""
        config_file = tmp_path / "claudefig.toml"
        # Invalid value (unquoted string)
        config_file.write_text(
            """[claudefig]
            version = 2.0
            template_source = invalid value without quotes
            """,
            encoding="utf-8",
        )

        # Should fall back to defaults instead of crashing
        config = Config(config_path=config_file)

        # Should use default config values
        assert config.data == config_service.DEFAULT_CONFIG

    def test_load_empty_file(self, tmp_path):
        """Test loading completely empty config file.

        CURRENT: Empty file loads as empty dict, no defaults merged
        IDEAL: Should merge with DEFAULT_CONFIG
        """
        config_file = tmp_path / "claudefig.toml"
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
        config_file = tmp_path / "claudefig.toml"
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
        config_file = tmp_path / "claudefig.toml"
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

    @pytest.mark.skipif(
        platform.system() in ["Windows", "Darwin"] or os.environ.get("CI") == "true",
        reason="File permission tests unreliable on Windows/macOS/CI - chmod doesn't prevent writes",
    )
    def test_save_permission_denied(self, tmp_path):
        """Test saving config when write permission is denied."""
        from claudefig.exceptions import FileWriteError

        config_file = tmp_path / "claudefig.toml"
        config = Config()

        # Create a read-only file
        config_file.write_text('[claudefig]\nversion = "2.0"', encoding="utf-8")
        config_file.chmod(0o444)  # Read-only

        # New architecture raises FileWriteError which wraps permission errors
        with pytest.raises((FileWriteError, PermissionError)):
            config.save(config_file)

        # Cleanup
        config_file.chmod(0o644)

    def test_save_to_nonexistent_directory(self, tmp_path):
        """Test saving config to directory that doesn't exist.

        New architecture automatically creates parent directories.
        """
        config = Config()
        config_file = tmp_path / "nonexistent" / "subdir" / "claudefig.toml"

        # Should automatically create parent directories and save successfully
        config.save(config_file)

        # Verify file was created
        assert config_file.exists()
        assert config_file.parent.exists()

    def test_save_disk_full(self, tmp_path):
        """Test saving config when disk is full."""
        from claudefig.exceptions import FileWriteError

        config = Config()
        config_file = tmp_path / "claudefig.toml"

        # Mock at the repository level since new architecture uses atomic writes
        with (
            patch(
                "claudefig.repositories.config_repository.TomlConfigRepository.save",
                side_effect=FileWriteError(
                    path=str(config_file),
                    reason="No space left on device",
                ),
            ),
            pytest.raises(FileWriteError),
        ):
            config.save(config_file)


class TestConfigGet:
    """Tests for Config.get() method edge cases."""

    def test_get_nested_missing_key(self, tmp_path):
        """Test getting nested key that doesn't exist."""
        config_file = tmp_path / "claudefig.toml"
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


class TestConfigSet:
    """Tests for Config.set() method."""

    def test_set_top_level_key(self):
        """Test setting a top-level key."""
        config = Config()

        config.set("new_key", "new_value")

        assert config.data["new_key"] == "new_value"

    def test_set_nested_key(self):
        """Test setting a nested key."""
        config = Config()

        config.set("level1.level2.level3", "deep_value")

        assert config.data["level1"]["level2"]["level3"] == "deep_value"

    def test_set_creates_missing_parent_keys(self):
        """Test that set() creates missing intermediate keys."""
        config = Config()

        # Set a deeply nested key - all parents should be created
        config.set("a.b.c.d.e", "value")

        # Verify all levels were created
        assert "a" in config.data
        assert "b" in config.data["a"]
        assert "c" in config.data["a"]["b"]
        assert "d" in config.data["a"]["b"]["c"]
        assert "e" in config.data["a"]["b"]["c"]["d"]
        assert config.data["a"]["b"]["c"]["d"]["e"] == "value"

    def test_set_overwrites_existing_value(self):
        """Test that set() overwrites existing values."""
        config = Config()
        config.data = {"existing": "old_value"}

        config.set("existing", "new_value")

        assert config.data["existing"] == "new_value"

    def test_set_nested_in_existing_structure(self):
        """Test setting nested value in existing structure."""
        config = Config()
        config.data = {"level1": {"existing": "value"}}

        config.set("level1.new_key", "new_value")

        assert config.data["level1"]["existing"] == "value"
        assert config.data["level1"]["new_key"] == "new_value"

    def test_set_with_different_data_types(self):
        """Test setting values of different types."""
        config = Config()

        config.set("string_key", "string_value")
        config.set("int_key", 42)
        config.set("bool_key", True)
        config.set("list_key", [1, 2, 3])
        config.set("dict_key", {"nested": "dict"})

        assert config.data["string_key"] == "string_value"
        assert config.data["int_key"] == 42
        assert config.data["bool_key"] is True
        assert config.data["list_key"] == [1, 2, 3]
        assert config.data["dict_key"] == {"nested": "dict"}


class TestConfigRemoveFileInstance:
    """Tests for Config.remove_file_instance() method."""

    def test_remove_existing_instance(self):
        """Test removing an existing file instance."""
        config = Config()
        config.data = {
            "files": [
                {"id": "instance1", "path": "file1.md"},
                {"id": "instance2", "path": "file2.md"},
                {"id": "instance3", "path": "file3.md"},
            ]
        }

        result = config.remove_file_instance("instance2")

        assert result is True
        assert len(config.data["files"]) == 2
        assert config.data["files"][0]["id"] == "instance1"
        assert config.data["files"][1]["id"] == "instance3"
        # instance2 should be gone
        assert not any(f["id"] == "instance2" for f in config.data["files"])

    def test_remove_nonexistent_instance_returns_false(self):
        """Test removing non-existent instance returns False."""
        config = Config()
        config.data = {
            "files": [
                {"id": "instance1", "path": "file1.md"},
            ]
        }

        result = config.remove_file_instance("nonexistent")

        assert result is False
        # Original data should be unchanged
        assert len(config.data["files"]) == 1
        assert config.data["files"][0]["id"] == "instance1"

    def test_remove_when_no_files_key(self):
        """Test removing instance when 'files' key doesn't exist."""
        config = Config()
        config.data = {}

        result = config.remove_file_instance("any_id")

        assert result is False
        # Should not create 'files' key
        assert "files" not in config.data

    def test_remove_from_empty_files_array(self):
        """Test removing from empty files array."""
        config = Config()
        config.data = {"files": []}

        result = config.remove_file_instance("any_id")

        assert result is False
        # Array should still be empty
        assert config.data["files"] == []

    def test_remove_first_instance(self):
        """Test removing the first instance in the list."""
        config = Config()
        config.data = {
            "files": [
                {"id": "first", "path": "file1.md"},
                {"id": "second", "path": "file2.md"},
            ]
        }

        result = config.remove_file_instance("first")

        assert result is True
        assert len(config.data["files"]) == 1
        assert config.data["files"][0]["id"] == "second"

    def test_remove_last_instance(self):
        """Test removing the last instance in the list."""
        config = Config()
        config.data = {
            "files": [
                {"id": "first", "path": "file1.md"},
                {"id": "last", "path": "file2.md"},
            ]
        }

        result = config.remove_file_instance("last")

        assert result is True
        assert len(config.data["files"]) == 1
        assert config.data["files"][0]["id"] == "first"

    def test_remove_only_instance(self):
        """Test removing the only instance in the list."""
        config = Config()
        config.data = {
            "files": [
                {"id": "only", "path": "file.md"},
            ]
        }

        result = config.remove_file_instance("only")

        assert result is True
        assert config.data["files"] == []


class TestConfigFileInstances:
    """Tests for file instance operations with error handling."""

    def test_get_file_instances_corrupted_array(self, tmp_path):
        """Test getting file instances when [[files]] is corrupted."""
        config_file = tmp_path / "claudefig.toml"
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

        New architecture gracefully falls back to defaults when TOML is malformed,
        so we can add instances to the recovered config.
        """
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text("[incomplete", encoding="utf-8")

        # Config should load with default values (graceful fallback)
        config = Config(config_path=config_file)

        # Should have default structure
        assert config.data is not None

        # Can add file instances to the recovered config
        test_instance = {
            "id": "test-1",
            "type": "claude_md",
            "preset": "claude_md:default",
            "path": "CLAUDE.md",
            "enabled": True,
        }
        config.add_file_instance(test_instance)

        # Verify it was added
        instances = config.get_file_instances()
        assert len(instances) == 1
        assert instances[0]["id"] == "test-1"

    def test_add_file_instance_to_valid_config(self, tmp_path):
        """Test adding file instance to a valid (but minimal) config."""
        config_file = tmp_path / "claudefig.toml"
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


class TestConfigValidation:
    """Tests for Config.validate_schema() method."""

    def test_validate_schema_valid_config(self, tmp_path):
        """Test validation passes for valid configuration."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text(
            """[claudefig]
            version = "2.0"
            schema_version = "2.0"

            [init]
            overwrite_existing = false
            create_backup = true

            [[files]]
            id = "test"
            type = "claude_md"
            preset = "claude_md:default"
            path = "CLAUDE.md"
            enabled = true

            [custom]
            template_dir = ""
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)
        result = config.validate_schema()

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_schema_missing_required_section(self, tmp_path):
        """Test validation catches missing required [claudefig] section."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text(
            """[custom]
            some_key = "value"
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)
        result = config.validate_schema()

        assert result.valid is False
        assert any("Missing required section: 'claudefig'" in e for e in result.errors)

    def test_validate_schema_claudefig_not_dict(self, tmp_path):
        """Test validation catches claudefig section as non-dict."""
        config = Config()
        config.data = {"claudefig": "not a dict"}

        result = config.validate_schema()

        assert result.valid is False
        assert any(
            "Section 'claudefig' must be a dictionary" in e for e in result.errors
        )

    def test_validate_schema_missing_schema_version(self, tmp_path):
        """Test validation warns about missing schema_version."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text(
            """[claudefig]
            version = "2.0"
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)
        result = config.validate_schema()

        # Should be valid but have warning
        assert result.valid is True
        assert any("Missing 'claudefig.schema_version'" in w for w in result.warnings)

    def test_validate_schema_version_mismatch(self, tmp_path):
        """Test validation warns about schema version mismatch."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text(
            """[claudefig]
            version = "2.0"
            schema_version = "1.0"
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)
        result = config.validate_schema()

        assert result.valid is True
        assert any("Schema version mismatch" in w for w in result.warnings)

    def test_validate_schema_init_section_not_dict(self):
        """Test validation catches [init] section as non-dict."""
        config = Config()
        config.data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "init": "not a dict",
        }

        result = config.validate_schema()

        assert result.valid is False
        assert any("Section 'init' must be a dictionary" in e for e in result.errors)

    def test_validate_schema_init_overwrite_not_bool(self):
        """Test validation catches init.overwrite_existing as non-boolean."""
        config = Config()
        config.data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "init": {"overwrite_existing": "not a bool"},
        }

        result = config.validate_schema()

        assert result.valid is False
        assert any(
            "'init.overwrite_existing' must be a boolean" in e for e in result.errors
        )

    def test_validate_schema_init_create_backup_not_bool(self):
        """Test validation catches init.create_backup as non-boolean."""
        config = Config()
        config.data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "init": {"create_backup": 123},
        }

        result = config.validate_schema()

        assert result.valid is False
        assert any("'init.create_backup' must be a boolean" in e for e in result.errors)

    def test_validate_schema_files_not_list(self):
        """Test validation catches [[files]] as non-list."""
        config = Config()
        config.data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "files": "not a list",
        }

        result = config.validate_schema()

        assert result.valid is False
        assert any("Section 'files' must be a list" in e for e in result.errors)

    def test_validate_schema_file_instance_not_dict(self):
        """Test validation catches file instance as non-dict."""
        config = Config()
        config.data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "files": ["not a dict", {"id": "valid"}],
        }

        result = config.validate_schema()

        assert result.valid is False
        assert any(
            "File instance at index 0 must be a dictionary" in e for e in result.errors
        )

    def test_validate_schema_file_instance_missing_fields(self):
        """Test validation catches missing required fields in file instance."""
        config = Config()
        config.data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "files": [
                {"id": "test1"},  # Missing type, preset, path
                {
                    "id": "test2",
                    "type": "claude_md",
                    "preset": "claude_md:default",
                    "path": "CLAUDE.md",
                },  # Complete
            ],
        }

        result = config.validate_schema()

        assert result.valid is False
        # Should have errors for missing fields
        assert any("missing required field: 'type'" in e for e in result.errors)
        assert any("missing required field: 'preset'" in e for e in result.errors)
        assert any("missing required field: 'path'" in e for e in result.errors)

    def test_validate_schema_custom_section_not_dict(self):
        """Test validation catches [custom] section as non-dict."""
        config = Config()
        config.data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "custom": ["not", "a", "dict"],
        }

        result = config.validate_schema()

        assert result.valid is False
        assert any("Section 'custom' must be a dictionary" in e for e in result.errors)

    def test_validate_schema_data_not_dict(self):
        """Test validation catches config.data as non-dict."""
        config = Config()
        config.data = "not a dictionary"  # type: ignore[assignment]

        result = config.validate_schema()

        assert result.valid is False
        assert any("Configuration must be a dictionary" in e for e in result.errors)

    def test_get_validation_result_caches_result(self, tmp_path):
        """Test that get_validation_result caches the validation result."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text(
            """[claudefig]
            version = "2.0"
            schema_version = "2.0"
            """,
            encoding="utf-8",
        )

        config = Config(config_path=config_file)

        # First call should validate and cache
        result1 = config.get_validation_result()
        # Second call should return cached result
        result2 = config.get_validation_result()

        assert result1 is result2  # Same object
        assert result1.valid is True

    def test_validate_schema_multiple_errors(self):
        """Test validation collects multiple errors."""
        config = Config()
        config.data = {
            # Missing claudefig section
            "init": "not a dict",  # Wrong type
            "files": "not a list",  # Wrong type
            "custom": 123,  # Wrong type
        }

        result = config.validate_schema()

        assert result.valid is False
        # Should have multiple errors
        assert len(result.errors) >= 4
        assert any("Missing required section" in e for e in result.errors)
        assert any("'init' must be a dictionary" in e for e in result.errors)
        assert any("'files' must be a list" in e for e in result.errors)
        assert any("'custom' must be a dictionary" in e for e in result.errors)
