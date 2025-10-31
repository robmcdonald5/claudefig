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
        """Test that ConfigTemplateManager initializes without creating default presets.

        Note: Default presets are now created by user_config.py during user
        directory initialization, not by ConfigTemplateManager.
        """
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Initialize manager - should not create any presets
        ConfigTemplateManager(global_presets_dir=global_dir)

        # Verify directory exists but no presets created by ConfigTemplateManager
        assert global_dir.exists()

        # No flat .toml files should be created (old behavior)
        preset_files = list(global_dir.glob("*.toml"))
        assert len(preset_files) == 0

        # No directories with .claudefig.toml should be created either
        # (that's handled by user_config.py)
        preset_dirs = [d for d in global_dir.iterdir() if d.is_dir()]
        assert len(preset_dirs) == 0


class TestListGlobalPresets:
    """Tests for list_global_presets method."""

    def test_list_global_presets(self, tmp_path):
        """Test listing global config preset templates (directory-based)."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Create a sample preset (directory structure)
        preset_dir = global_dir / "test"
        preset_dir.mkdir()

        preset_data = {
            "claudefig": {
                "version": "2.0",
                "schema_version": "2.0",
            },
            "preset": {
                "name": "test",
                "description": "Test preset",
            },
            "components": {
                "claude_md": {
                    "variants": ["default"],
                    "required_files": ["CLAUDE.md"],
                }
            },
        }

        preset_file = preset_dir / ".claudefig.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump(preset_data, f)

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        presets = manager.list_global_presets()

        assert len(presets) >= 1  # At least our test preset
        test_preset = next(p for p in presets if p["name"] == "test")
        assert test_preset["description"] == "Test preset"
        assert test_preset["file_count"] == 1  # 1 variant in claude_md component

    def test_list_global_presets_with_validation(self, tmp_path):
        """Test listing global presets with validation (directory-based)."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Create a valid preset directory
        valid_dir = global_dir / "valid"
        valid_dir.mkdir()
        valid_data = {
            "claudefig": {"version": "2.0", "schema_version": "2.0"},
            "preset": {"name": "valid", "description": "Valid preset"},
            "components": {},
        }
        valid_file = valid_dir / ".claudefig.toml"
        with open(valid_file, "wb") as f:
            tomli_w.dump(valid_data, f)

        # Create an invalid preset directory (missing required fields)
        invalid_dir = global_dir / "invalid"
        invalid_dir.mkdir()
        invalid_file = invalid_dir / ".claudefig.toml"
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
        """Test deleting an existing global preset (directory)."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Create a preset directory to delete
        preset_dir = global_dir / "to_delete"
        preset_dir.mkdir()
        preset_file = preset_dir / ".claudefig.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump({"claudefig": {}, "preset": {}, "components": {}}, f)

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        manager.delete_global_preset("to_delete")

        assert not preset_dir.exists()

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
        """Test applying a global preset converts PresetDefinition to project config format."""
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib

        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)
        project_dir = tmp_path / "project"
        project_dir.mkdir(parents=True)

        # Create a global preset directory with PresetDefinition format
        preset_dir = global_dir / "test"
        preset_dir.mkdir()
        preset_data = {
            "preset": {
                "name": "test",
                "version": "1.0.0",
                "description": "Test preset",
            },
            "components": [
                {
                    "type": "claude_md",
                    "name": "default",
                    "path": "CLAUDE.md",
                    "enabled": True,
                },
                {
                    "type": "gitignore",
                    "name": "default",
                    "path": ".gitignore",
                    "enabled": False,
                },
            ],
        }
        preset_file = preset_dir / ".claudefig.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump(preset_data, f)

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        manager.apply_preset_to_project("test", target_path=project_dir)

        # Verify config was created
        config_file = project_dir / ".claudefig.toml"
        assert config_file.exists()

        # Load and verify it's in project config format (not PresetDefinition format)
        with open(config_file, "rb") as f:
            project_config = tomllib.load(f)

        # Should have [claudefig] section (project config format)
        assert "claudefig" in project_config
        assert project_config["claudefig"]["version"] == "2.0"

        # Should have [[files]] section (not [[components]])
        assert "files" in project_config
        assert len(project_config["files"]) == 2

        # Should NOT have [preset] or [[components]] sections
        assert "preset" not in project_config
        assert "components" not in project_config or isinstance(
            project_config.get("components"), dict
        )  # If exists, should be dict not list

        # Verify file instances were created correctly
        files = project_config["files"]
        claude_md_file = next(f for f in files if f["type"] == "claude_md")
        assert claude_md_file["preset"] == "claude_md:default"
        assert claude_md_file["path"] == "CLAUDE.md"
        assert claude_md_file["enabled"] is True

        gitignore_file = next(f for f in files if f["type"] == "gitignore")
        assert gitignore_file["preset"] == "gitignore:default"
        assert gitignore_file["path"] == ".gitignore"
        assert gitignore_file["enabled"] is False

    def test_apply_nonexistent_preset(self, tmp_path):
        """Test applying a preset that doesn't exist."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)
        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        with pytest.raises(FileNotFoundError):
            manager.apply_preset_to_project("nonexistent", target_path=tmp_path)

    def test_apply_preset_to_existing_config(self, tmp_path):
        """Test that applying to existing config raises error unless overwrite=True."""
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib

        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)
        project_dir = tmp_path / "project"
        project_dir.mkdir(parents=True)

        # Create existing config
        existing_config = project_dir / ".claudefig.toml"
        existing_config.write_text("existing", encoding="utf-8")

        # Create a preset directory with valid PresetDefinition
        preset_dir = global_dir / "test"
        preset_dir.mkdir()
        preset_data = {
            "preset": {
                "name": "test",
                "version": "1.0.0",
                "description": "Test preset",
            },
            "components": [
                {
                    "type": "claude_md",
                    "name": "default",
                    "path": "CLAUDE.md",
                    "enabled": True,
                }
            ],
        }
        preset_file = preset_dir / ".claudefig.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump(preset_data, f)

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        # Should raise error when overwrite=False (default)
        with pytest.raises(FileExistsError):
            manager.apply_preset_to_project("test", target_path=project_dir)

        # Should succeed when overwrite=True
        manager.apply_preset_to_project("test", target_path=project_dir, overwrite=True)
        assert existing_config.exists()

        # Verify it was overwritten with project config format
        with open(existing_config, "rb") as f:
            new_config = tomllib.load(f)
        assert "claudefig" in new_config
        assert "files" in new_config


class TestPresetConfigCreation:
    """Tests for preset config creation methods."""

    def test_create_default_preset_config(self):
        """Test creating default preset configuration."""
        manager = ConfigTemplateManager(global_presets_dir=Path("/tmp/test"))
        preset_def = manager.preset_loader.load_preset("default")
        config = manager._build_from_preset_definition(preset_def)

        assert "claudefig" in config
        assert config["claudefig"]["version"] == "2.0"
        assert "files" in config
        assert len(config["files"]) > 0
        # Should have at least CLAUDE.md, gitignore, settings
        file_ids = [f["id"] for f in config["files"]]
        assert any("claude-md" in fid for fid in file_ids)
        assert any("gitignore" in fid for fid in file_ids)


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

        # Create existing preset directory
        existing = global_dir / "existing"
        existing.mkdir()

        manager = ConfigTemplateManager(global_presets_dir=global_dir)

        with pytest.raises(ValueError, match="already exists"):
            manager.save_global_preset("existing", "description")

    def test_save_global_preset_with_components(self, tmp_path, monkeypatch):
        """Test that save_global_preset copies components and creates PresetDefinition."""
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib

        # Setup directories
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)
        components_dir = tmp_path / "components"
        components_dir.mkdir()

        # Create mock component directories
        claude_md_component = components_dir / "claude_md" / "default"
        claude_md_component.mkdir(parents=True)
        (claude_md_component / "CLAUDE.md").write_text("# Test CLAUDE.md")

        gitignore_component = components_dir / "gitignore" / "default"
        gitignore_component.mkdir(parents=True)
        (gitignore_component / ".gitignore").write_text(".claudefig.toml\n.claude/")

        # Create project config with file instances
        config_file = project_dir / ".claudefig.toml"
        config_content = """
[claudefig]
version = "2.0"
schema_version = "2.0"
template_source = "default"

[[files]]
id = "claude-md-1"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true

[[files]]
id = "gitignore-1"
type = "gitignore"
preset = "gitignore:default"
path = ".gitignore"
enabled = true

[[files]]
id = "settings-1"
type = "settings_json"
preset = "settings_json:default"
path = ".claude/settings.json"
enabled = false
"""
        config_file.write_text(config_content)

        # Change to project directory
        monkeypatch.chdir(project_dir)

        # Mock get_components_dir to return our test components directory
        def mock_get_components_dir():
            return components_dir

        import claudefig.user_config

        monkeypatch.setattr(
            claudefig.user_config, "get_components_dir", mock_get_components_dir
        )

        # Create manager and save preset
        manager = ConfigTemplateManager(global_presets_dir=global_dir)
        manager.save_global_preset("test-preset", "Test preset description")

        # Verify preset directory was created
        preset_dir = global_dir / "test-preset"
        assert preset_dir.exists()
        assert preset_dir.is_dir()

        # Verify .claudefig.toml was created in PresetDefinition format
        preset_file = preset_dir / ".claudefig.toml"
        assert preset_file.exists()

        # Load and verify preset definition
        with open(preset_file, "rb") as f:
            preset_data = tomllib.load(f)

        # Check preset metadata
        assert "preset" in preset_data
        assert preset_data["preset"]["name"] == "test-preset"
        assert preset_data["preset"]["description"] == "Test preset description"
        assert preset_data["preset"]["version"] == "1.0.0"

        # Check components section (should include both enabled AND disabled components)
        assert "components" in preset_data
        assert (
            len(preset_data["components"]) == 3
        )  # All instances, enabled and disabled

        # Verify CLAUDE.md component (enabled)
        claude_md_comp = next(
            c for c in preset_data["components"] if c["type"] == "claude_md"
        )
        assert claude_md_comp["name"] == "default"
        assert claude_md_comp["path"] == "CLAUDE.md"
        assert claude_md_comp["enabled"] is True

        # Verify gitignore component (enabled)
        gitignore_comp = next(
            c for c in preset_data["components"] if c["type"] == "gitignore"
        )
        assert gitignore_comp["name"] == "default"
        assert gitignore_comp["path"] == ".gitignore"
        assert gitignore_comp["enabled"] is True

        # Verify settings_json component (disabled)
        settings_comp = next(
            c for c in preset_data["components"] if c["type"] == "settings_json"
        )
        assert settings_comp["name"] == "default"
        assert settings_comp["path"] == ".claude/settings.json"
        assert settings_comp["enabled"] is False

        # Verify component files were copied (both enabled and disabled)
        # Note: The loader chain prioritizes built-in preset components,
        # so it will copy from src/presets/default/ rather than our test components.
        # This is correct behavior - we just need to verify the structure was created.

        # Verify enabled component: CLAUDE.md
        copied_claude_md = (
            preset_dir / "components" / "claude_md" / "default" / "CLAUDE.md"
        )
        assert copied_claude_md.exists()
        assert copied_claude_md.read_text().startswith(
            "# CLAUDE.md"
        )  # Verify it's a CLAUDE.md file

        # Verify enabled component: gitignore
        copied_gitignore = (
            preset_dir / "components" / "gitignore" / "default" / ".gitignore"
        )
        assert copied_gitignore.exists()
        assert (
            ".claudefig.toml" in copied_gitignore.read_text()
        )  # Verify it has gitignore content

        # Verify disabled component was ALSO copied (settings_json)
        copied_settings = (
            preset_dir / "components" / "settings_json" / "default" / "settings.json"
        )
        assert copied_settings.exists()
        # Just verify it's a JSON file by checking it can be read
        assert copied_settings.read_text().strip() != ""
