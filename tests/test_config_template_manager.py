"""Tests for ConfigTemplateManager."""

from pathlib import Path

import pytest
import tomli_w

from claudefig.config_template_manager import ConfigTemplateManager


@pytest.fixture
def config_template_manager(tmp_path):
    """Create a ConfigTemplateManager with temporary directory."""
    global_dir = tmp_path / "global_presets"
    global_dir.mkdir(parents=True)
    return ConfigTemplateManager(global_presets_dir=global_dir)


class TestConfigTemplateManagerInit:
    """Tests for ConfigTemplateManager initialization."""

    def test_init_creates_directory(self, tmp_path):
        """Test that initialization creates global presets directory."""
        global_dir = tmp_path / "global"
        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        assert manager.global_presets_dir.exists()

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        manager = ConfigTemplateManager()

        assert manager.global_presets_dir == Path.home() / ".claudefig" / "presets"

    def test_init_creates_default_presets(self, tmp_path):
        """Test that default presets are created on init."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Initialize manager to trigger default preset creation
        ConfigTemplateManager(global_presets_dir=global_dir)

        # Check that preset files were created
        assert (global_dir / "default.toml").exists()
        assert (global_dir / "minimal.toml").exists()
        assert (global_dir / "full.toml").exists()
        assert (global_dir / "backend.toml").exists()
        assert (global_dir / "frontend.toml").exists()


class TestListGlobalPresets:
    """Tests for list_global_presets method."""

    def test_list_global_presets(self, tmp_path):
        """Test listing global config preset templates."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Create a sample preset
        preset_data = {
            "claudefig": {
                "version": "2.0",
                "schema_version": "2.0",
                "description": "Test preset",
            },
            "files": [
                {
                    "id": "test-file",
                    "type": "claude_md",
                    "preset": "claude_md:default",
                    "path": "CLAUDE.md",
                    "enabled": True,
                    "variables": {},
                }
            ],
        }

        preset_file = global_dir / "test.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump(preset_data, f)

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        presets = manager.list_global_presets()

        assert len(presets) >= 1  # At least our test preset
        test_preset = next(p for p in presets if p["name"] == "test")
        assert test_preset["description"] == "Test preset"
        assert test_preset["file_count"] == 1

    def test_list_global_presets_with_validation(self, tmp_path):
        """Test listing global presets with validation."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Create a valid preset
        valid_data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "files": [],
        }
        valid_file = global_dir / "valid.toml"
        with open(valid_file, "wb") as f:
            tomli_w.dump(valid_data, f)

        # Create an invalid preset (missing required fields)
        invalid_file = global_dir / "invalid.toml"
        with open(invalid_file, "wb") as f:
            tomli_w.dump({"incomplete": "data"}, f)

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        presets = manager.list_global_presets(include_validation=True)

        assert len(presets) >= 2  # At least valid and invalid
        # Valid preset should be valid
        valid_preset = next(p for p in presets if p["name"] == "valid")
        assert valid_preset["validation"]["valid"] is True
        # Invalid preset should have errors
        invalid_preset = next(p for p in presets if p["name"] == "invalid")
        assert invalid_preset["validation"]["valid"] is False
        assert len(invalid_preset["validation"]["errors"]) > 0


class TestDeleteGlobalPreset:
    """Tests for delete_global_preset method."""

    def test_delete_existing_preset(self, tmp_path):
        """Test deleting an existing global preset."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Create a preset to delete
        preset_file = global_dir / "to_delete.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump({"claudefig": {}}, f)

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        manager.delete_global_preset("to_delete")

        assert not preset_file.exists()

    def test_delete_default_preset_raises_error(self, tmp_path):
        """Test that deleting 'default' preset raises error."""
        manager = ConfigTemplateManager(global_presets_dir=tmp_path / "global")

        with pytest.raises(ValueError, match="Cannot delete default preset"):
            manager.delete_global_preset("default")

    def test_delete_nonexistent_preset(self, tmp_path):
        """Test deleting a preset that doesn't exist."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)
        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        with pytest.raises(FileNotFoundError):
            manager.delete_global_preset("nonexistent")


class TestApplyPresetToProject:
    """Tests for apply_preset_to_project method."""

    def test_apply_preset_to_project(self, tmp_path):
        """Test applying a global preset to a project directory."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)
        project_dir = tmp_path / "project"
        project_dir.mkdir(parents=True)

        # Create a global preset
        preset_data = {"claudefig": {"version": "2.0"}, "files": []}
        preset_file = global_dir / "test.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump(preset_data, f)

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        manager.apply_preset_to_project("test", target_path=project_dir)

        # Verify config was copied
        config_file = project_dir / ".claudefig.toml"
        assert config_file.exists()

    def test_apply_nonexistent_preset(self, tmp_path):
        """Test applying a preset that doesn't exist."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)
        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        with pytest.raises(FileNotFoundError):
            manager.apply_preset_to_project("nonexistent", target_path=tmp_path)

    def test_apply_preset_to_existing_config(self, tmp_path):
        """Test that applying to existing config raises error."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)
        project_dir = tmp_path / "project"
        project_dir.mkdir(parents=True)

        # Create existing config
        existing_config = project_dir / ".claudefig.toml"
        existing_config.write_text("existing", encoding="utf-8")

        # Create a preset
        preset_file = global_dir / "test.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump({}, f)

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        with pytest.raises(FileExistsError):
            manager.apply_preset_to_project("test", target_path=project_dir)


class TestPresetConfigCreation:
    """Tests for preset config creation methods."""

    def test_create_default_preset_config(self):
        """Test creating default preset configuration."""
        manager = ConfigTemplateManager(global_presets_dir=Path("/tmp/test"))
        config = manager._create_default_preset_config()

        assert "claudefig" in config
        assert config["claudefig"]["version"] == "2.0"
        assert "files" in config
        assert len(config["files"]) > 0
        # Should have at least CLAUDE.md, gitignore, settings
        file_ids = [f["id"] for f in config["files"]]
        assert any("claude-md" in fid for fid in file_ids)
        assert any("gitignore" in fid for fid in file_ids)

    def test_create_minimal_preset_config(self):
        """Test creating minimal preset configuration."""
        manager = ConfigTemplateManager(global_presets_dir=Path("/tmp/test"))
        config = manager._create_minimal_preset_config()

        assert "claudefig" in config
        assert "files" in config
        # Minimal should only have CLAUDE.md
        assert len(config["files"]) == 1
        assert config["files"][0]["type"] == "claude_md"

    def test_create_full_preset_config(self):
        """Test creating full preset configuration."""
        manager = ConfigTemplateManager(global_presets_dir=Path("/tmp/test"))
        config = manager._create_full_preset_config()

        assert "claudefig" in config
        assert "files" in config
        # Full should have all file types
        file_types = {f["type"] for f in config["files"]}
        assert "claude_md" in file_types
        assert "gitignore" in file_types
        assert "settings_json" in file_types
        assert "commands" in file_types
        assert "agents" in file_types
        assert "hooks" in file_types
        assert "output_styles" in file_types
        assert "statusline" in file_types
        assert "mcp" in file_types

    def test_create_backend_preset_config(self):
        """Test creating backend preset configuration."""
        manager = ConfigTemplateManager(global_presets_dir=Path("/tmp/test"))
        config = manager._create_backend_preset_config()

        assert "claudefig" in config
        assert "files" in config
        assert "backend" in config["claudefig"]["description"].lower()

    def test_create_frontend_preset_config(self):
        """Test creating frontend preset configuration."""
        manager = ConfigTemplateManager(global_presets_dir=Path("/tmp/test"))
        config = manager._create_frontend_preset_config()

        assert "claudefig" in config
        assert "files" in config
        assert "frontend" in config["claudefig"]["description"].lower()


class TestSaveGlobalPreset:
    """Tests for save_global_preset method."""

    def test_save_global_preset_invalid_name(self, tmp_path):
        """Test that invalid preset names are rejected."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)
        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        # Names with path separators should be rejected
        with pytest.raises(ValueError, match="Invalid preset name"):
            manager.save_global_preset("name/with/slash", "description")

        with pytest.raises(ValueError, match="Invalid preset name"):
            manager.save_global_preset("name\\with\\backslash", "description")

    def test_save_global_preset_already_exists(self, tmp_path):
        """Test that saving over existing preset is rejected."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Create existing preset
        existing = global_dir / "existing.toml"
        existing.write_text("data", encoding="utf-8")

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        with pytest.raises(ValueError, match="already exists"):
            manager.save_global_preset("existing", "description")
