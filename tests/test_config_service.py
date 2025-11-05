"""Tests for configuration service layer."""

from pathlib import Path
from unittest.mock import patch

from claudefig.repositories.config_repository import FakeConfigRepository
from claudefig.services import config_service


class TestFindConfigPath:
    """Test find_config_path() function."""

    def test_finds_config_in_current_directory(self, monkeypatch, tmp_path):
        """Test finding config in current directory."""
        config_file = tmp_path / "claudefig.toml"
        config_file.write_text("[claudefig]\nversion = '2.0'\n")

        monkeypatch.chdir(tmp_path)
        result = config_service.find_config_path()

        assert result is not None
        assert result == config_file

    def test_finds_config_in_home_directory(self, monkeypatch, tmp_path):
        """Test finding config in home directory when not in current."""
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        (home_dir / ".claudefig").mkdir()
        config_file = home_dir / ".claudefig" / "config.toml"
        config_file.write_text("[claudefig]\nversion = '2.0'\n")

        work_dir = tmp_path / "work"
        work_dir.mkdir()

        monkeypatch.setattr(Path, "home", lambda: home_dir)
        monkeypatch.chdir(work_dir)

        result = config_service.find_config_path()

        assert result is not None
        assert result == config_file

    def test_returns_none_when_no_config_found(self, monkeypatch, tmp_path):
        """Test returns None when no config exists."""
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        monkeypatch.setattr(Path, "home", lambda: home_dir)
        monkeypatch.chdir(work_dir)

        result = config_service.find_config_path()

        assert result is None

    def test_prioritizes_current_directory_over_home(self, monkeypatch, tmp_path):
        """Test current directory config has priority over home."""
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        (home_dir / ".claudefig").mkdir()
        home_config = home_dir / ".claudefig" / "config.toml"
        home_config.write_text("[claudefig]\nversion = '1.0'\n")

        work_dir = tmp_path / "work"
        work_dir.mkdir()
        work_config = work_dir / "claudefig.toml"
        work_config.write_text("[claudefig]\nversion = '2.0'\n")

        monkeypatch.setattr(Path, "home", lambda: home_dir)
        monkeypatch.chdir(work_dir)

        result = config_service.find_config_path()

        assert result == work_config


class TestLoadConfig:
    """Test load_config() function."""

    def test_returns_defaults_when_config_does_not_exist(self):
        """Test returns default config when file doesn't exist."""
        repo = FakeConfigRepository()

        result = config_service.load_config(repo)

        assert result == config_service.DEFAULT_CONFIG
        assert "claudefig" in result
        assert result["claudefig"]["version"] == "2.0"

    def test_loads_existing_config(self):
        """Test loads config when it exists."""
        data = {"claudefig": {"version": "2.0"}, "custom": {"key": "value"}}
        repo = FakeConfigRepository(data)

        result = config_service.load_config(repo)

        assert result == data
        assert result["custom"]["key"] == "value"

    def test_returns_defaults_on_load_error(self, monkeypatch):
        """Test returns defaults when load raises exception."""
        repo = FakeConfigRepository({"test": "data"})

        # Make load() raise an exception
        def raise_error():
            raise ValueError("Simulated load error")

        monkeypatch.setattr(repo, "load", raise_error)

        result = config_service.load_config(repo)

        assert result == config_service.DEFAULT_CONFIG


class TestSaveConfig:
    """Test save_config() function."""

    def test_saves_config_to_repository(self):
        """Test config is saved to repository."""
        repo = FakeConfigRepository()
        data = {"claudefig": {"version": "2.0"}, "test": "data"}

        config_service.save_config(data, repo)

        assert repo.exists()
        loaded = repo.load()
        assert loaded == data

    def test_overwrites_existing_config(self):
        """Test saves over existing config."""
        old_data = {"claudefig": {"version": "1.0"}}
        repo = FakeConfigRepository(old_data)

        new_data = {"claudefig": {"version": "2.0"}, "new": "field"}
        config_service.save_config(new_data, repo)

        loaded = repo.load()
        assert loaded == new_data
        assert "new" in loaded


class TestGetValue:
    """Test get_value() function."""

    def test_gets_top_level_value(self):
        """Test getting top-level configuration value."""
        data = {"key": "value"}

        result = config_service.get_value(data, "key")

        assert result == "value"

    def test_gets_nested_value_with_dot_notation(self):
        """Test getting nested value using dot notation."""
        data = {"init": {"overwrite_existing": True}}

        result = config_service.get_value(data, "init.overwrite_existing")

        assert result is True

    def test_gets_deeply_nested_value(self):
        """Test getting deeply nested value."""
        data = {"a": {"b": {"c": {"d": "deep"}}}}

        result = config_service.get_value(data, "a.b.c.d")

        assert result == "deep"

    def test_returns_default_for_missing_key(self):
        """Test returns default when key doesn't exist."""
        data = {"key": "value"}

        result = config_service.get_value(data, "missing", "default")

        assert result == "default"

    def test_returns_default_for_missing_nested_key(self):
        """Test returns default for missing nested key."""
        data = {"init": {}}

        result = config_service.get_value(data, "init.missing", False)

        assert result is False

    def test_returns_none_by_default_for_missing_key(self):
        """Test returns None when no default provided."""
        data = {}

        result = config_service.get_value(data, "missing")

        assert result is None

    def test_returns_default_when_intermediate_key_not_dict(self):
        """Test returns default when path traverses non-dict."""
        data = {"key": "string_value"}

        result = config_service.get_value(data, "key.nested", "default")

        assert result == "default"


class TestSetValue:
    """Test set_value() function."""

    def test_sets_top_level_value(self):
        """Test setting top-level value."""
        data = {}

        config_service.set_value(data, "key", "value")

        assert data["key"] == "value"

    def test_sets_nested_value_with_dot_notation(self):
        """Test setting nested value using dot notation."""
        data = {}

        config_service.set_value(data, "init.overwrite_existing", True)

        assert data["init"]["overwrite_existing"] is True

    def test_sets_deeply_nested_value(self):
        """Test setting deeply nested value."""
        data = {}

        config_service.set_value(data, "a.b.c.d", "deep")

        assert data["a"]["b"]["c"]["d"] == "deep"

    def test_creates_intermediate_dictionaries(self):
        """Test creates intermediate dicts as needed."""
        data = {}

        config_service.set_value(data, "a.b.c", "value")

        assert isinstance(data["a"], dict)
        assert isinstance(data["a"]["b"], dict)
        assert data["a"]["b"]["c"] == "value"

    def test_overwrites_existing_value(self):
        """Test overwrites existing value."""
        data = {"key": "old"}

        config_service.set_value(data, "key", "new")

        assert data["key"] == "new"

    def test_updates_nested_value(self):
        """Test updates nested value in existing structure."""
        data = {"init": {"overwrite_existing": False}}

        config_service.set_value(data, "init.overwrite_existing", True)

        assert data["init"]["overwrite_existing"] is True


class TestGetFileInstances:
    """Test get_file_instances() function."""

    def test_gets_file_instances_list(self):
        """Test gets file instances from config."""
        instances = [{"id": "1", "type": "claude_md"}]
        data = {"files": instances}

        result = config_service.get_file_instances(data)

        assert result == instances

    def test_returns_empty_list_when_no_files_key(self):
        """Test returns empty list when files key missing."""
        data = {}

        result = config_service.get_file_instances(data)

        assert result == []

    def test_returns_empty_list_when_files_is_empty(self):
        """Test returns empty list when files is empty."""
        data = {"files": []}

        result = config_service.get_file_instances(data)

        assert result == []


class TestSetFileInstances:
    """Test set_file_instances() function."""

    def test_sets_file_instances_list(self):
        """Test sets file instances in config."""
        data = {}
        instances = [{"id": "1", "type": "claude_md"}]

        config_service.set_file_instances(data, instances)

        assert data["files"] == instances

    def test_overwrites_existing_instances(self):
        """Test overwrites existing file instances."""
        data = {"files": [{"id": "old"}]}
        instances = [{"id": "new"}]

        config_service.set_file_instances(data, instances)

        assert data["files"] == instances
        assert len(data["files"]) == 1


class TestAddFileInstance:
    """Test add_file_instance() function."""

    def test_adds_instance_to_existing_list(self):
        """Test adds instance to existing files list."""
        data = {"files": [{"id": "1"}]}
        instance = {"id": "2", "type": "gitignore"}

        config_service.add_file_instance(data, instance)

        assert len(data["files"]) == 2
        assert data["files"][1] == instance

    def test_creates_files_list_if_missing(self):
        """Test creates files list if not present."""
        data = {}
        instance = {"id": "1", "type": "claude_md"}

        config_service.add_file_instance(data, instance)

        assert "files" in data
        assert len(data["files"]) == 1
        assert data["files"][0] == instance

    def test_appends_to_end_of_list(self):
        """Test new instance is appended to end."""
        data = {"files": [{"id": "1"}, {"id": "2"}]}
        instance = {"id": "3"}

        config_service.add_file_instance(data, instance)

        assert data["files"][-1] == instance


class TestRemoveFileInstance:
    """Test remove_file_instance() function."""

    def test_removes_instance_by_id(self):
        """Test removes instance matching ID."""
        data = {"files": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}

        result = config_service.remove_file_instance(data, "2")

        assert result is True
        assert len(data["files"]) == 2
        assert all(f["id"] != "2" for f in data["files"])

    def test_returns_false_when_id_not_found(self):
        """Test returns False when ID doesn't exist."""
        data = {"files": [{"id": "1"}]}

        result = config_service.remove_file_instance(data, "999")

        assert result is False
        assert len(data["files"]) == 1

    def test_returns_false_when_no_files_key(self):
        """Test returns False when files key missing."""
        data = {}

        result = config_service.remove_file_instance(data, "1")

        assert result is False

    def test_removes_only_matching_instance(self):
        """Test only removes instance with exact ID match."""
        data = {"files": [{"id": "1"}, {"id": "2"}, {"id": "1"}]}

        result = config_service.remove_file_instance(data, "2")

        assert result is True
        assert len(data["files"]) == 2
        assert all(f["id"] == "1" for f in data["files"])


class TestCreateDefaultConfig:
    """Test create_default_config() function."""

    def test_creates_and_saves_default_config(self):
        """Test creates default config and saves to repo."""
        repo = FakeConfigRepository()

        result = config_service.create_default_config(repo)

        assert result == config_service.DEFAULT_CONFIG
        assert repo.exists()

    def test_saved_config_matches_returned_config(self):
        """Test saved and returned config are the same."""
        repo = FakeConfigRepository()

        result = config_service.create_default_config(repo)
        loaded = repo.load()

        assert loaded == result

    def test_default_config_has_required_structure(self):
        """Test default config has expected structure."""
        repo = FakeConfigRepository()

        result = config_service.create_default_config(repo)

        assert "claudefig" in result
        assert "init" in result
        assert "files" in result
        assert result["claudefig"]["schema_version"] == "2.0"


class TestValidateConfigSchema:
    """Test validate_config_schema() function."""

    def test_validates_minimal_valid_config(self):
        """Test validates minimal valid config."""
        data = {"claudefig": {"schema_version": "2.0"}}

        result = config_service.validate_config_schema(data)

        assert result.valid
        assert not result.has_errors

    def test_rejects_non_dict_config(self):
        """Test rejects config that isn't a dictionary."""
        result = config_service.validate_config_schema("not a dict")  # type: ignore[arg-type]

        assert not result.valid
        assert result.has_errors
        assert "must be a dictionary" in result.errors[0]

    def test_requires_claudefig_section(self):
        """Test requires claudefig section."""
        data = {"init": {}}

        result = config_service.validate_config_schema(data)

        assert not result.valid
        assert any("claudefig" in err for err in result.errors)

    def test_claudefig_section_must_be_dict(self):
        """Test claudefig section must be dictionary."""
        data = {"claudefig": "not a dict"}

        result = config_service.validate_config_schema(data)

        assert not result.valid
        assert any("must be a dictionary" in err for err in result.errors)

    def test_warns_on_missing_schema_version(self):
        """Test warns when schema_version missing."""
        data = {"claudefig": {}}

        result = config_service.validate_config_schema(data)

        assert result.valid  # Warning, not error
        assert result.has_warnings
        assert any("schema_version" in warn for warn in result.warnings)

    def test_warns_on_schema_version_mismatch(self):
        """Test warns when schema version doesn't match."""
        data = {"claudefig": {"schema_version": "1.0"}}

        result = config_service.validate_config_schema(data)

        assert result.valid
        assert result.has_warnings
        assert any("mismatch" in warn for warn in result.warnings)

    def test_validates_init_section_must_be_dict(self):
        """Test init section must be dictionary."""
        data = {"claudefig": {"schema_version": "2.0"}, "init": "not a dict"}

        result = config_service.validate_config_schema(data)

        assert not result.valid
        assert any("init" in err and "dictionary" in err for err in result.errors)

    def test_validates_init_overwrite_existing_is_bool(self):
        """Test init.overwrite_existing must be boolean."""
        data = {
            "claudefig": {"schema_version": "2.0"},
            "init": {"overwrite_existing": "not a bool"},
        }

        result = config_service.validate_config_schema(data)

        assert not result.valid
        assert any(
            "overwrite_existing" in err and "boolean" in err for err in result.errors
        )

    def test_validates_init_create_backup_is_bool(self):
        """Test init.create_backup must be boolean."""
        data = {
            "claudefig": {"schema_version": "2.0"},
            "init": {"create_backup": "not a bool"},
        }

        result = config_service.validate_config_schema(data)

        assert not result.valid
        assert any("create_backup" in err and "boolean" in err for err in result.errors)

    def test_validates_files_section_must_be_list(self):
        """Test files section must be list."""
        data = {"claudefig": {"schema_version": "2.0"}, "files": "not a list"}

        result = config_service.validate_config_schema(data)

        assert not result.valid
        assert any("files" in err and "list" in err for err in result.errors)

    def test_validates_file_instances_must_be_dicts(self):
        """Test each file instance must be dictionary."""
        data = {
            "claudefig": {"schema_version": "2.0"},
            "files": ["not a dict"],
        }

        result = config_service.validate_config_schema(data)

        assert not result.valid
        assert any("dictionary" in err for err in result.errors)

    def test_validates_file_instance_required_fields(self):
        """Test file instances have required fields."""
        data = {
            "claudefig": {"schema_version": "2.0"},
            "files": [{"id": "test"}],  # Missing type, preset, path
        }

        result = config_service.validate_config_schema(data)

        assert not result.valid
        assert any("type" in err for err in result.errors)
        assert any("preset" in err for err in result.errors)
        assert any("path" in err for err in result.errors)

    def test_validates_custom_section_must_be_dict(self):
        """Test custom section must be dictionary."""
        data = {"claudefig": {"schema_version": "2.0"}, "custom": "not a dict"}

        result = config_service.validate_config_schema(data)

        assert not result.valid
        assert any("custom" in err and "dictionary" in err for err in result.errors)

    def test_validates_complete_valid_config(self):
        """Test validates complete valid configuration."""
        data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "init": {"overwrite_existing": False, "create_backup": True},
            "files": [
                {
                    "id": "1",
                    "type": "claude_md",
                    "preset": "default",
                    "path": "CLAUDE.md",
                }
            ],
            "custom": {"template_dir": "/templates"},
        }

        result = config_service.validate_config_schema(data)

        assert result.valid
        assert not result.has_errors


class TestConfigSingleton:
    """Test get_config_singleton() and reload_config_singleton()."""

    def test_get_config_singleton_returns_config(self, tmp_path):
        """Test singleton returns configuration."""
        config_file = tmp_path / "test.toml"

        # Clear cache first
        config_service._get_config_singleton_cached.cache_clear()

        result = config_service.get_config_singleton(config_file)

        assert isinstance(result, dict)
        assert "claudefig" in result

    def test_singleton_caches_result(self, tmp_path):
        """Test singleton caches result but returns deep copies."""
        config_file = tmp_path / "test.toml"

        config_service._get_config_singleton_cached.cache_clear()

        result1 = config_service.get_config_singleton(config_file)
        result2 = config_service.get_config_singleton(config_file)

        # Results are equal but not same object (deep copy protection)
        assert result1 == result2
        assert result1 is not result2

        # Verify cache is working (only 1 miss, subsequent calls are hits)
        cache_info = config_service._get_config_singleton_cached.cache_info()
        assert cache_info.hits >= 1  # At least one cache hit

    @patch("claudefig.services.config_service.find_config_path")
    def test_reload_config_singleton_clears_cache(self, mock_find_config, tmp_path):
        """Test reload clears cache and returns fresh config."""
        config_file = tmp_path / "test.toml"
        # Mock find_config_path to return our test file path
        mock_find_config.return_value = config_file

        config_service._get_config_singleton_cached.cache_clear()

        result1 = config_service.get_config_singleton(config_file)
        result2 = config_service.reload_config_singleton()

        # Different instances (deep copy + cache cleared)
        assert result1 is not result2
        # Same content (both defaults)
        assert result1 == result2
