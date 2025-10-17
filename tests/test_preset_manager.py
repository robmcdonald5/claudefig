"""Tests for PresetManager (file type presets only)."""

from pathlib import Path

import pytest
import tomli_w

from claudefig.models import FileType, Preset, PresetSource
from claudefig.preset_manager import PresetManager


@pytest.fixture
def preset_manager(tmp_path):
    """Create a PresetManager with temporary directories."""
    user_dir = tmp_path / "user_presets"
    project_dir = tmp_path / "project_presets"
    user_dir.mkdir(parents=True)
    project_dir.mkdir(parents=True)

    return PresetManager(user_presets_dir=user_dir, project_presets_dir=project_dir)


@pytest.fixture
def sample_preset_toml(tmp_path):
    """Create a sample preset TOML file."""
    preset_file = tmp_path / "test_preset.toml"
    preset_data = {
        "preset": {
            "id": "claude_md:test",
            "type": "claude_md",
            "name": "Test Preset",
            "description": "A test preset",
            "source": "user",
            "template_path": None,
            "variables": {"key": "value"},
            "extends": None,
            "tags": ["test"],
        }
    }
    with open(preset_file, "wb") as f:
        tomli_w.dump(preset_data, f)
    return preset_file


class TestPresetManagerInit:
    """Tests for PresetManager initialization."""

    def test_init_with_default_paths(self):
        """Test initialization with default paths."""
        manager = PresetManager()

        assert manager.user_presets_dir == Path.home() / ".claudefig" / "presets"
        assert manager.project_presets_dir == Path.cwd() / ".claudefig" / "presets"

    def test_init_with_custom_paths(self, tmp_path):
        """Test initialization with custom paths."""
        user_dir = tmp_path / "user"
        project_dir = tmp_path / "project"

        manager = PresetManager(
            user_presets_dir=user_dir, project_presets_dir=project_dir
        )

        assert manager.user_presets_dir == user_dir
        assert manager.project_presets_dir == project_dir


class TestListPresets:
    """Tests for list_presets method."""

    def test_list_builtin_presets(self):
        """Test listing built-in presets."""
        manager = PresetManager()
        presets = manager.list_presets()

        # Should have built-in presets for all file types
        preset_ids = [p.id for p in presets]
        assert "claude_md:default" in preset_ids
        assert "settings_json:default" in preset_ids
        assert "gitignore:standard" in preset_ids
        assert "commands:default" in preset_ids

    def test_list_presets_by_file_type(self):
        """Test filtering presets by file type."""
        manager = PresetManager()
        presets = manager.list_presets(file_type=FileType.CLAUDE_MD)

        # All should be CLAUDE_MD type
        assert all(p.type == FileType.CLAUDE_MD for p in presets)
        assert len(presets) >= 1  # At least the default

    def test_list_presets_by_source(self):
        """Test filtering presets by source."""
        manager = PresetManager()
        presets = manager.list_presets(source=PresetSource.BUILT_IN)

        # All should be built-in
        assert all(p.source == PresetSource.BUILT_IN for p in presets)

    def test_list_presets_sorted(self):
        """Test that presets are sorted by type and name."""
        manager = PresetManager()
        presets = manager.list_presets()

        # Should be sorted
        for i in range(len(presets) - 1):
            curr_type = presets[i].type.value
            next_type = presets[i + 1].type.value
            if curr_type == next_type:
                # Same type, should be sorted by name
                assert presets[i].name <= presets[i + 1].name
            else:
                # Different types, should be sorted by type
                assert curr_type <= next_type


class TestGetPreset:
    """Tests for get_preset method."""

    def test_get_existing_preset(self):
        """Test getting an existing built-in preset."""
        manager = PresetManager()
        preset = manager.get_preset("claude_md:default")

        assert preset is not None
        assert preset.id == "claude_md:default"
        assert preset.type == FileType.CLAUDE_MD

    def test_get_nonexistent_preset(self):
        """Test getting a preset that doesn't exist."""
        manager = PresetManager()
        preset = manager.get_preset("nonexistent:preset")

        assert preset is None


class TestGetPresetByName:
    """Tests for get_preset_by_name method."""

    def test_get_preset_by_name(self):
        """Test getting preset by file type and name."""
        manager = PresetManager()
        preset = manager.get_preset_by_name(FileType.CLAUDE_MD, "default")

        assert preset is not None
        assert preset.id == "claude_md:default"
        assert preset.name == "Default"


class TestClearCache:
    """Tests for cache management."""

    def test_clear_cache(self):
        """Test clearing the preset cache."""
        manager = PresetManager()
        # Load presets (populates cache)
        manager.list_presets()
        assert manager._cache_loaded is True
        assert len(manager._preset_cache) > 0

        # Clear cache
        manager.clear_cache()
        assert manager._cache_loaded is False
        assert len(manager._preset_cache) == 0


class TestAddDeletePreset:
    """Tests for add_preset and delete_preset methods."""

    def test_add_preset_raises_if_builtin_source(self):
        """Test that adding built-in preset raises error."""
        manager = PresetManager()

        new_preset = Preset(
            id="test:preset",
            type=FileType.CLAUDE_MD,
            name="Test",
            description="Test",
            source=PresetSource.BUILT_IN,
        )

        with pytest.raises(ValueError, match="Cannot add built-in presets"):
            manager.add_preset(new_preset, source=PresetSource.BUILT_IN)

    def test_add_duplicate_preset_raises_error(self):
        """Test that adding duplicate preset raises error."""
        manager = PresetManager()

        # Try to add a preset with ID that already exists
        duplicate = Preset(
            id="claude_md:default",  # Already exists as built-in
            type=FileType.CLAUDE_MD,
            name="Duplicate",
            description="Test",
            source=PresetSource.USER,
        )

        with pytest.raises(ValueError, match="already exists"):
            manager.add_preset(duplicate, source=PresetSource.USER)

    def test_delete_builtin_preset_raises_error(self):
        """Test that deleting built-in preset raises error."""
        manager = PresetManager()

        with pytest.raises(ValueError, match="Cannot delete built-in presets"):
            manager.delete_preset("claude_md:default")

    def test_delete_nonexistent_preset_returns_false(self):
        """Test that deleting non-existent preset returns False."""
        manager = PresetManager()

        result = manager.delete_preset("nonexistent:preset")
        assert result is False


class TestRenderPreset:
    """Tests for render_preset method."""

    def test_render_preset_basic(self, tmp_path):
        """Test rendering a preset with variables."""
        template_file = tmp_path / "template.md"
        template_file.write_text("Hello {name}! Version: {version}", encoding="utf-8")

        preset = Preset(
            id="test:render",
            type=FileType.CLAUDE_MD,
            name="Test",
            description="Test",
            source=PresetSource.USER,
            template_path=template_file,
            variables={"name": "World", "version": "1.0"},
        )

        manager = PresetManager()
        rendered = manager.render_preset(preset)

        assert rendered == "Hello World! Version: 1.0"

    def test_render_preset_with_variable_override(self, tmp_path):
        """Test rendering with user-provided variable overrides."""
        template_file = tmp_path / "template.md"
        template_file.write_text("Name: {name}, Age: {age}", encoding="utf-8")

        preset = Preset(
            id="test:override",
            type=FileType.CLAUDE_MD,
            name="Test",
            description="Test",
            source=PresetSource.USER,
            template_path=template_file,
            variables={"name": "Default", "age": "0"},
        )

        manager = PresetManager()
        rendered = manager.render_preset(preset, variables={"name": "Custom"})

        # Custom overrides default, age stays default
        assert rendered == "Name: Custom, Age: 0"

    def test_render_preset_without_template_raises_error(self):
        """Test that rendering preset without template raises error."""
        preset = Preset(
            id="test:no_template",
            type=FileType.CLAUDE_MD,
            name="No Template",
            description="Test",
            source=PresetSource.BUILT_IN,
            template_path=None,  # No template
        )

        manager = PresetManager()

        with pytest.raises(FileNotFoundError, match="Template file not found"):
            manager.render_preset(preset)


class TestUserProjectPresets:
    """Tests for user and project preset operations."""

    def test_load_user_preset(self, tmp_path):
        """Test loading a preset from user directory."""
        user_dir = tmp_path / "user"
        user_dir.mkdir(parents=True)

        # Create a user preset
        preset_data = {
            "preset": {
                "id": "claude_md:my_preset",
                "type": "claude_md",
                "name": "My Preset",
                "description": "User preset",
                "source": "user",
            }
        }
        preset_file = user_dir / "claude_md_my_preset.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump(preset_data, f)

        manager = PresetManager(
            user_presets_dir=user_dir, project_presets_dir=tmp_path / "project"
        )
        presets = manager.list_presets()

        # Should include the user preset
        preset_ids = [p.id for p in presets]
        assert "claude_md:my_preset" in preset_ids

    def test_load_project_preset(self, tmp_path):
        """Test loading a preset from project directory."""
        project_dir = tmp_path / "project"
        project_dir.mkdir(parents=True)

        # Create a project preset
        preset_data = {
            "preset": {
                "id": "settings_json:project_preset",
                "type": "settings_json",
                "name": "Project Preset",
                "description": "Project-specific preset",
                "source": "project",
            }
        }
        preset_file = project_dir / "settings_json_project_preset.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump(preset_data, f)

        manager = PresetManager(
            user_presets_dir=tmp_path / "user", project_presets_dir=project_dir
        )
        presets = manager.list_presets()

        # Should include the project preset
        preset_ids = [p.id for p in presets]
        assert "settings_json:project_preset" in preset_ids


class TestPresetEdgeCases:
    """Tests for preset manager edge cases and error handling."""

    def test_get_preset_with_invalid_id_format(self):
        """Test getting preset with malformed ID."""
        manager = PresetManager()

        # Try to get preset with invalid ID format (no colon separator)
        preset = manager.get_preset("invalid_format_no_colon")

        # Should return None for invalid format
        assert preset is None

    def test_get_preset_by_name_with_empty_name(self):
        """Test getting preset by name with empty string."""
        manager = PresetManager()

        preset = manager.get_preset_by_name(FileType.CLAUDE_MD, "")

        assert preset is None

    def test_list_presets_after_clear_cache(self):
        """Test listing presets after clearing cache reloads."""
        manager = PresetManager()

        # Load presets
        presets1 = manager.list_presets()
        initial_count = len(presets1)

        # Clear cache
        manager.clear_cache()

        # List again - should reload from source
        presets2 = manager.list_presets()

        assert len(presets2) == initial_count
        assert manager._cache_loaded is True

    def test_render_preset_missing_template_file(self, tmp_path):
        """Test rendering preset when template file doesn't exist."""
        nonexistent_template = tmp_path / "does_not_exist.md"

        preset = Preset(
            id="test:missing",
            type=FileType.CLAUDE_MD,
            name="Missing Template",
            description="Test",
            source=PresetSource.USER,
            template_path=nonexistent_template,
            variables={},
        )

        manager = PresetManager()

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            manager.render_preset(preset)

    def test_render_preset_with_empty_variables(self, tmp_path):
        """Test rendering preset with no variables."""
        template_file = tmp_path / "template.md"
        template_file.write_text("Static content with no variables", encoding="utf-8")

        preset = Preset(
            id="test:static",
            type=FileType.CLAUDE_MD,
            name="Static",
            description="Test",
            source=PresetSource.USER,
            template_path=template_file,
            variables={},
        )

        manager = PresetManager()
        rendered = manager.render_preset(preset)

        assert rendered == "Static content with no variables"

    def test_list_presets_with_invalid_source(self):
        """Test listing presets with invalid source filter."""
        manager = PresetManager()

        # This should work without crashing even with invalid source
        # Implementation determines behavior - may return empty list or ignore filter
        try:
            presets = manager.list_presets(source="invalid_source")
            # Should either return empty list or all presets
            assert isinstance(presets, list)
        except (ValueError, KeyError):
            # Or it may raise an error, which is also acceptable
            pass

    def test_render_preset_with_unicode_content(self, tmp_path):
        """Test rendering preset with Unicode characters."""
        template_file = tmp_path / "unicode.md"
        template_file.write_text("Hello {name}! 你好 {greeting} 🎉", encoding="utf-8")

        preset = Preset(
            id="test:unicode",
            type=FileType.CLAUDE_MD,
            name="Unicode Test",
            description="Test",
            source=PresetSource.USER,
            template_path=template_file,
            variables={"name": "World", "greeting": "世界"},
        )

        manager = PresetManager()
        rendered = manager.render_preset(preset)

        assert "Hello World!" in rendered
        assert "你好 世界" in rendered
        assert "🎉" in rendered


class TestPresetManagerListFiltering:
    """Tests for preset list filtering combinations."""

    def test_list_by_both_type_and_source(self):
        """Test filtering by both file type and source."""
        manager = PresetManager()

        presets = manager.list_presets(
            file_type=FileType.CLAUDE_MD, source=PresetSource.BUILT_IN
        )

        # All should match both filters
        assert all(p.type == FileType.CLAUDE_MD for p in presets)
        assert all(p.source == PresetSource.BUILT_IN for p in presets)

    def test_list_empty_result_with_filters(self, tmp_path):
        """Test listing with filters that match no presets."""
        # Create manager with empty custom directories
        user_dir = tmp_path / "empty_user"
        project_dir = tmp_path / "empty_project"
        user_dir.mkdir()
        project_dir.mkdir()

        manager = PresetManager(
            user_presets_dir=user_dir, project_presets_dir=project_dir
        )

        # Try to list USER source presets (should be empty)
        presets = manager.list_presets(source=PresetSource.USER)

        assert len(presets) == 0

    def test_list_presets_multiple_types(self):
        """Test that list includes multiple file types."""
        manager = PresetManager()

        presets = manager.list_presets()
        preset_types = {p.type for p in presets}

        # Should have multiple types
        assert len(preset_types) >= 2  # At least Claude MD and Settings JSON


class TestPresetCaching:
    """Tests for preset caching behavior."""

    def test_cache_persists_across_list_calls(self):
        """Test that cache persists across multiple list calls."""
        manager = PresetManager()

        # First call loads and caches
        presets1 = manager.list_presets()
        cache_loaded_after_first = manager._cache_loaded

        # Second call uses cache
        presets2 = manager.list_presets()
        cache_loaded_after_second = manager._cache_loaded

        assert cache_loaded_after_first is True
        assert cache_loaded_after_second is True
        # Results should be identical
        assert len(presets1) == len(presets2)

    def test_cache_cleared_allows_reload(self, tmp_path):
        """Test that clearing cache allows fresh reload."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()

        manager = PresetManager(user_presets_dir=user_dir, project_presets_dir=tmp_path)

        # Load initially (no custom presets)
        presets1 = manager.list_presets()
        initial_count = len(presets1)

        # Add a custom preset file
        preset_data = {
            "preset": {
                "id": "claude_md:custom",
                "type": "claude_md",
                "name": "Custom",
                "description": "Added later",
                "source": "user",
            }
        }
        preset_file = user_dir / "custom.toml"
        with open(preset_file, "wb") as f:
            tomli_w.dump(preset_data, f)

        # Without clearing cache, won't see new preset
        presets2 = manager.list_presets()
        assert len(presets2) == initial_count

        # Clear cache and reload
        manager.clear_cache()
        presets3 = manager.list_presets()

        # Should now include the new preset
        assert len(presets3) == initial_count + 1
        assert any(p.id == "claude_md:custom" for p in presets3)
