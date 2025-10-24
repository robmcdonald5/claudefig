"""Tests for config repository implementations."""

import tempfile
from pathlib import Path

import pytest
import tomli_w

from claudefig.exceptions import (
    ConfigFileNotFoundError,
)
from claudefig.repositories.config_repository import (
    FakeConfigRepository,
    TomlConfigRepository,
)


class TestTomlConfigRepository:
    """Test TomlConfigRepository implementation."""

    def test_init_stores_config_path(self):
        """Test that initialization stores the config path."""
        config_path = Path("/tmp/config.toml")
        repo = TomlConfigRepository(config_path)

        assert repo.config_path == config_path.resolve()

    def test_exists_returns_false_for_missing_file(self):
        """Test exists() returns False when config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.toml"
            repo = TomlConfigRepository(config_path)

            assert not repo.exists()

    def test_exists_returns_true_for_existing_file(self):
        """Test exists() returns True when config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("[claudefig]\nversion = '1.0'\n")
            repo = TomlConfigRepository(config_path)

            assert repo.exists()

    def test_get_path_returns_config_path(self):
        """Test get_path() returns the config path."""
        config_path = Path("/tmp/config.toml")
        repo = TomlConfigRepository(config_path)

        assert repo.get_path() == config_path.resolve()

    def test_load_valid_config(self):
        """Test loading a valid TOML config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            data = {"claudefig": {"version": "1.0"}, "custom": {"key": "value"}}
            with open(config_path, "wb") as f:
                tomli_w.dump(data, f)

            repo = TomlConfigRepository(config_path)
            result = repo.load()

            assert result == data
            assert result["claudefig"]["version"] == "1.0"
            assert result["custom"]["key"] == "value"

    def test_load_missing_file_raises_error(self):
        """Test loading missing config raises ConfigFileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.toml"
            repo = TomlConfigRepository(config_path)

            with pytest.raises(ConfigFileNotFoundError) as exc_info:
                repo.load()

            # Check filename is in error (handles Windows short vs long path names)
            assert "nonexistent.toml" in str(exc_info.value)

    def test_load_malformed_toml_raises_error(self):
        """Test loading malformed TOML raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("invalid toml {{{ content")

            repo = TomlConfigRepository(config_path)

            with pytest.raises(ValueError) as exc_info:
                repo.load()

            assert "Invalid TOML" in str(exc_info.value)

    def test_save_creates_new_file(self):
        """Test saving creates a new config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            repo = TomlConfigRepository(config_path)

            data = {"claudefig": {"version": "1.0"}}
            repo.save(data)

            assert config_path.exists()
            loaded = repo.load()
            assert loaded == data

    def test_save_overwrites_existing_file(self):
        """Test saving overwrites existing config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            repo = TomlConfigRepository(config_path)

            # Save initial data
            data1 = {"key": "value1"}
            repo.save(data1)

            # Overwrite with new data
            data2 = {"key": "value2"}
            repo.save(data2)

            loaded = repo.load()
            assert loaded == data2

    def test_save_creates_parent_directories(self):
        """Test save creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "nested" / "config.toml"
            repo = TomlConfigRepository(config_path)

            data = {"test": "data"}
            repo.save(data)

            assert config_path.exists()
            assert config_path.parent.exists()

    def test_save_atomic_write_pattern(self):
        """Test save uses atomic write (temp file + rename)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            repo = TomlConfigRepository(config_path)

            data = {"test": "data"}
            repo.save(data)

            # Verify no .tmp files left behind
            tmp_files = list(Path(tmpdir).glob("*.tmp"))
            assert len(tmp_files) == 0

    def test_backup_creates_timestamped_file(self):
        """Test backup creates a timestamped backup file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            repo = TomlConfigRepository(config_path)

            # Create initial config
            data = {"test": "data"}
            repo.save(data)

            # Create backup
            backup_path = repo.backup()

            # Verify backup exists
            assert backup_path.exists()
            assert backup_path.suffix == ".bak"
            assert backup_path.stem.startswith("config.")

            # Verify backup content matches original
            backup_repo = TomlConfigRepository(backup_path)
            backup_data = backup_repo.load()
            assert backup_data == data

    def test_backup_with_custom_path(self):
        """Test backup with custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            backup_path = Path(tmpdir) / "my_backup.toml"
            repo = TomlConfigRepository(config_path)

            # Create initial config
            repo.save({"test": "data"})

            # Create backup at custom path
            result_path = repo.backup(backup_path)

            assert result_path == backup_path
            assert backup_path.exists()

    def test_backup_missing_config_raises_error(self):
        """Test backup of non-existent config raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.toml"
            repo = TomlConfigRepository(config_path)

            with pytest.raises(ConfigFileNotFoundError):
                repo.backup()

    def test_delete_removes_file(self):
        """Test delete removes the config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            repo = TomlConfigRepository(config_path)

            # Create config
            repo.save({"test": "data"})
            assert config_path.exists()

            # Delete config
            repo.delete()

            assert not config_path.exists()

    def test_delete_nonexistent_raises_error(self):
        """Test deleting non-existent config raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.toml"
            repo = TomlConfigRepository(config_path)

            with pytest.raises(ConfigFileNotFoundError):
                repo.delete()


class TestFakeConfigRepository:
    """Test FakeConfigRepository in-memory implementation."""

    def test_init_with_no_data(self):
        """Test initialization with no data."""
        repo = FakeConfigRepository()

        assert not repo.exists()

    def test_init_with_initial_data(self):
        """Test initialization with initial data."""
        initial_data = {"key": "value"}
        repo = FakeConfigRepository(initial_data)

        assert repo.exists()
        data = repo.load()
        assert data == initial_data

    def test_load_returns_copy_of_data(self):
        """Test load returns a copy, not the original."""
        initial_data = {"key": "value"}
        repo = FakeConfigRepository(initial_data)

        loaded = repo.load()
        loaded["key"] = "modified"

        # Original data should be unchanged
        assert repo.load()["key"] == "value"

    def test_load_missing_data_raises_error(self):
        """Test loading when no data exists raises error."""
        repo = FakeConfigRepository()

        with pytest.raises(ConfigFileNotFoundError):
            repo.load()

    def test_save_stores_copy_of_data(self):
        """Test save stores a copy, not the original."""
        repo = FakeConfigRepository()

        data = {"key": "value"}
        repo.save(data)

        # Modify original
        data["key"] = "modified"

        # Stored data should be unchanged
        assert repo.load()["key"] == "value"

    def test_save_makes_data_exist(self):
        """Test save makes data exist."""
        repo = FakeConfigRepository()
        assert not repo.exists()

        repo.save({"key": "value"})

        assert repo.exists()

    def test_exists_returns_correct_state(self):
        """Test exists returns correct state."""
        repo = FakeConfigRepository()
        assert not repo.exists()

        repo.save({"data": "test"})
        assert repo.exists()

        repo.delete()
        assert not repo.exists()

    def test_get_path_returns_virtual_path(self):
        """Test get_path returns virtual path."""
        repo = FakeConfigRepository()

        path = repo.get_path()

        assert isinstance(path, Path)
        assert path == Path("/fake/config.toml")

    def test_backup_creates_in_memory_backup(self):
        """Test backup creates in-memory backup."""
        repo = FakeConfigRepository({"key": "value"})

        backup_path = repo.backup()

        assert isinstance(backup_path, Path)
        assert backup_path.suffix == ".bak"

    def test_backup_missing_data_raises_error(self):
        """Test backup with no data raises error."""
        repo = FakeConfigRepository()

        with pytest.raises(ConfigFileNotFoundError):
            repo.backup()

    def test_delete_removes_data(self):
        """Test delete removes data."""
        repo = FakeConfigRepository({"key": "value"})
        assert repo.exists()

        repo.delete()

        assert not repo.exists()
        with pytest.raises(ConfigFileNotFoundError):
            repo.load()

    def test_delete_missing_data_raises_error(self):
        """Test deleting when no data raises error."""
        repo = FakeConfigRepository()

        with pytest.raises(ConfigFileNotFoundError):
            repo.delete()

    def test_get_backups_returns_list(self):
        """Test get_backups returns list of backups."""
        repo = FakeConfigRepository({"version": 1})

        # Create multiple backups
        repo.backup()
        repo.save({"version": 2})
        repo.backup()

        backups = repo.get_backups()

        assert len(backups) == 2
        assert backups[0] == {"version": 1}
        assert backups[1] == {"version": 2}

    def test_restore_backup_restores_data(self):
        """Test restore_backup restores from backup."""
        repo = FakeConfigRepository({"version": 1})
        repo.backup()

        # Change data
        repo.save({"version": 2})
        assert repo.load()["version"] == 2

        # Restore backup
        repo.restore_backup()

        assert repo.load()["version"] == 1

    def test_restore_backup_with_index(self):
        """Test restore_backup with specific index."""
        repo = FakeConfigRepository({"version": 1})
        repo.backup()

        repo.save({"version": 2})
        repo.backup()

        repo.save({"version": 3})

        # Restore first backup
        repo.restore_backup(index=0)

        assert repo.load()["version"] == 1

    def test_restore_backup_no_backups_raises_error(self):
        """Test restore_backup with no backups raises error."""
        repo = FakeConfigRepository({"version": 1})

        with pytest.raises(ConfigFileNotFoundError):
            repo.restore_backup()
