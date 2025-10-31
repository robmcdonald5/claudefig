"""Tests for PresetManager (file type presets only)."""

from pathlib import Path

import pytest
import tomli_w

from claudefig.exceptions import (
    BuiltInModificationError,
    PresetExistsError,
    PresetNotFoundError,
    TemplateNotFoundError,
)
from claudefig.models import FileType, PresetSource
from claudefig.preset_manager import PresetManager
from tests.factories import PresetFactory


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

        new_preset = PresetFactory(
            id="test:preset",
            name="Test",
            description="Test",
            source=PresetSource.BUILT_IN,
        )

        with pytest.raises(BuiltInModificationError):
            manager.add_preset(new_preset, source=PresetSource.BUILT_IN)

    def test_add_duplicate_preset_raises_error(self):
        """Test that adding duplicate preset raises error."""
        manager = PresetManager()

        # Try to add a preset with ID that already exists
        duplicate = PresetFactory(
            id="claude_md:default",  # Already exists as built-in
            name="Duplicate",
            description="Test",
        )

        with pytest.raises(PresetExistsError):
            manager.add_preset(duplicate, source=PresetSource.USER)

    def test_delete_builtin_preset_raises_error(self):
        """Test that deleting built-in preset raises error."""
        manager = PresetManager()

        with pytest.raises(BuiltInModificationError):
            manager.delete_preset("claude_md:default")

    def test_delete_nonexistent_preset_raises_error(self):
        """Test that deleting non-existent preset raises error."""
        manager = PresetManager()

        with pytest.raises(PresetNotFoundError):
            manager.delete_preset("nonexistent:preset")

    def test_add_user_preset_success(self, preset_manager, tmp_path):
        """Test successfully adding a user preset (Priority 4)."""
        new_preset = PresetFactory(
            id="claude_md:my_user_preset",
            name="My User Preset",
            description="Custom user preset",
            template_path=None,
            variables={"key": "value"},
            extends=None,
            tags=[],
        )

        # Add preset as user preset
        preset_manager.add_preset(new_preset, source=PresetSource.USER)

        # Verify preset was added to cache
        assert "claude_md:my_user_preset" in preset_manager._preset_cache
        cached_preset = preset_manager._preset_cache["claude_md:my_user_preset"]
        assert cached_preset.name == "My User Preset"
        assert cached_preset.source == PresetSource.USER

        # Verify preset file was created
        expected_file = (
            preset_manager.user_presets_dir / "claude_md_my_user_preset.toml"
        )
        assert expected_file.exists()

        # Verify preset is in list
        presets = preset_manager.list_presets()
        assert any(p.id == "claude_md:my_user_preset" for p in presets)

    def test_add_project_preset_success(self, preset_manager, tmp_path):
        """Test successfully adding a project preset (Priority 4)."""
        new_preset = PresetFactory(
            id="settings_json:my_project_preset",
            type=FileType.SETTINGS_JSON,
            name="My Project Preset",
            description="Custom project preset",
            source=PresetSource.PROJECT,
            template_path=None,
            variables={"feature": "enabled"},
            extends=None,
            tags=[],
        )

        # Add preset as project preset
        preset_manager.add_preset(new_preset, source=PresetSource.PROJECT)

        # Verify preset was added to cache
        assert "settings_json:my_project_preset" in preset_manager._preset_cache
        cached_preset = preset_manager._preset_cache["settings_json:my_project_preset"]
        assert cached_preset.name == "My Project Preset"
        assert cached_preset.source == PresetSource.PROJECT

        # Verify preset file was created
        expected_file = (
            preset_manager.project_presets_dir / "settings_json_my_project_preset.toml"
        )
        assert expected_file.exists()

        # Verify preset is in list
        presets = preset_manager.list_presets()
        assert any(p.id == "settings_json:my_project_preset" for p in presets)

    def test_delete_user_preset_success(self, preset_manager, tmp_path):
        """Test successfully deleting a user preset (Priority 4)."""
        # First, add a user preset
        new_preset = PresetFactory(
            id="claude_md:delete_me",
            name="Delete Me",
            description="Preset to delete",
            template_path=None,
            variables={},
            extends=None,
            tags=[],
        )
        preset_manager.add_preset(new_preset, source=PresetSource.USER)

        # Verify it exists
        assert "claude_md:delete_me" in preset_manager._preset_cache
        preset_file = preset_manager.user_presets_dir / "claude_md_delete_me.toml"
        assert preset_file.exists()

        # Delete the preset
        result = preset_manager.delete_preset("claude_md:delete_me")

        # Verify deletion was successful
        assert result is True
        assert "claude_md:delete_me" not in preset_manager._preset_cache
        assert not preset_file.exists()

        # Verify it's not in list
        presets = preset_manager.list_presets()
        assert not any(p.id == "claude_md:delete_me" for p in presets)

    def test_delete_project_preset_success(self, preset_manager, tmp_path):
        """Test successfully deleting a project preset (Priority 4)."""
        # First, add a project preset
        new_preset = PresetFactory(
            id="gitignore:delete_me_project",
            type=FileType.GITIGNORE,
            name="Delete Me Project",
            description="Project preset to delete",
            source=PresetSource.PROJECT,
            template_path=None,
            variables={},
            extends=None,
            tags=[],
        )
        preset_manager.add_preset(new_preset, source=PresetSource.PROJECT)

        # Verify it exists
        assert "gitignore:delete_me_project" in preset_manager._preset_cache
        preset_file = (
            preset_manager.project_presets_dir / "gitignore_delete_me_project.toml"
        )
        assert preset_file.exists()

        # Delete the preset
        result = preset_manager.delete_preset("gitignore:delete_me_project")

        # Verify deletion was successful
        assert result is True
        assert "gitignore:delete_me_project" not in preset_manager._preset_cache
        assert not preset_file.exists()

        # Verify it's not in list
        presets = preset_manager.list_presets()
        assert not any(p.id == "gitignore:delete_me_project" for p in presets)


class TestRenderPreset:
    """Tests for render_preset method."""

    def test_render_preset_basic(self, tmp_path):
        """Test rendering a preset with variables."""
        template_file = tmp_path / "template.md"
        template_file.write_text("Hello {name}! Version: {version}", encoding="utf-8")

        preset = PresetFactory(
            id="test:render",
            name="Test",
            description="Test",
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

        preset = PresetFactory(
            id="test:override",
            name="Test",
            description="Test",
            template_path=template_file,
            variables={"name": "Default", "age": "0"},
        )

        manager = PresetManager()
        rendered = manager.render_preset(preset, variables={"name": "Custom"})

        # Custom overrides default, age stays default
        assert rendered == "Name: Custom, Age: 0"

    def test_render_preset_without_template_raises_error(self):
        """Test that rendering preset without template raises error."""
        preset = PresetFactory(
            id="test:no_template",
            name="No Template",
            description="Test",
            source=PresetSource.BUILT_IN,
            template_path=None,  # No template
        )

        manager = PresetManager()

        with pytest.raises(TemplateNotFoundError):
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

        preset = PresetFactory(
            id="test:missing",
            name="Missing Template",
            description="Test",
            template_path=nonexistent_template,
            variables={},
        )

        manager = PresetManager()

        # Should raise TemplateNotFoundError
        with pytest.raises(TemplateNotFoundError):
            manager.render_preset(preset)

    def test_render_preset_with_empty_variables(self, tmp_path):
        """Test rendering preset with no variables."""
        template_file = tmp_path / "template.md"
        template_file.write_text("Static content with no variables", encoding="utf-8")

        preset = PresetFactory(
            id="test:static",
            name="Static",
            description="Test",
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
            presets = manager.list_presets(source="invalid_source")  # type: ignore[arg-type]
            # Should either return empty list or all presets
            assert isinstance(presets, list)
        except (ValueError, KeyError):
            # Or it may raise an error, which is also acceptable
            pass

    def test_render_preset_with_unicode_content(self, tmp_path):
        """Test rendering preset with Unicode characters."""
        template_file = tmp_path / "unicode.md"
        template_file.write_text("Hello {name}! 你好 {greeting} 🎉", encoding="utf-8")

        preset = PresetFactory(
            id="test:unicode",
            name="Unicode Test",
            description="Test",
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


class TestValidateTemplateVariables:
    """Tests for validate_template_variables method (Phase 2 - Priority 3)."""

    def test_validate_template_missing_variables(self, preset_manager, tmp_path):
        """Test warning when template uses undefined variables."""
        # Create template with variables
        template_file = tmp_path / "template.md"
        template_file.write_text(
            "Hello {name}! Version: {version}, Environment: {env}",
            encoding="utf-8",
        )

        # Preset only defines 'name' and 'version', missing 'env'
        preset = PresetFactory(
            id="test:missing_vars",
            name="Missing Variables",
            description="Test",
            template_path=template_file,
            variables={"name": "World", "version": "1.0"},
        )

        # Validate - should have warning about missing 'env'
        result = preset_manager.validate_template_variables(preset)

        assert result.valid is True  # Still valid, just a warning
        assert result.has_warnings is True
        assert len(result.warnings) == 1
        assert "env" in result.warnings[0]
        assert "no default value is provided" in result.warnings[0]

    def test_validate_template_unused_variables(self, preset_manager, tmp_path):
        """Test warning when preset defines unused variables."""
        # Create template with only {name}
        template_file = tmp_path / "template.md"
        template_file.write_text("Hello {name}!", encoding="utf-8")

        # Preset defines extra variables not used in template
        preset = PresetFactory(
            id="test:unused_vars",
            name="Unused Variables",
            description="Test",
            template_path=template_file,
            variables={
                "name": "World",
                "unused_var1": "value1",
                "unused_var2": "value2",
            },
        )

        # Validate - should have warnings about unused variables
        result = preset_manager.validate_template_variables(preset)

        assert result.valid is True  # Still valid, just warnings
        assert result.has_warnings is True
        assert len(result.warnings) == 2
        # Check both unused variables are mentioned
        warnings_text = " ".join(result.warnings)
        assert "unused_var1" in warnings_text
        assert "unused_var2" in warnings_text
        assert "not used in the template" in warnings_text

    def test_validate_template_with_user_variables(self, preset_manager, tmp_path):
        """Test that user-provided variables are considered available."""
        # Template uses {name} and {env}
        template_file = tmp_path / "template.md"
        template_file.write_text("Hello {name} in {env}!", encoding="utf-8")

        # Preset only defines {name}
        preset = PresetFactory(
            id="test:user_vars",
            name="User Variables",
            description="Test",
            template_path=template_file,
            variables={"name": "World"},
        )

        # Pass {env} as user variable - should not warn about missing
        result = preset_manager.validate_template_variables(
            preset, variables={"env": "production"}
        )

        assert result.valid is True
        assert not result.has_warnings
        assert not result.has_errors

    def test_validate_template_no_template_path(self, preset_manager):
        """Test validation when preset has no template path."""
        preset = PresetFactory(
            id="test:no_template",
            name="No Template",
            description="Test",
            template_path=None,
            variables={},
        )

        # Should return valid result with no errors/warnings
        result = preset_manager.validate_template_variables(preset)

        assert result.valid is True
        assert not result.has_errors
        assert not result.has_warnings

    def test_validate_template_file_not_found(self, preset_manager, tmp_path):
        """Test validation when template file doesn't exist."""
        nonexistent_file = tmp_path / "does_not_exist.md"

        preset = PresetFactory(
            id="test:missing_file",
            name="Missing File",
            description="Test",
            template_path=nonexistent_file,
            variables={},
        )

        # Should return error about missing file
        result = preset_manager.validate_template_variables(preset)

        assert result.valid is False
        assert result.has_errors is True
        assert len(result.errors) == 1
        assert "Template file not found" in result.errors[0]

    def test_validate_template_read_error(self, preset_manager, tmp_path, monkeypatch):
        """Test OSError handling when reading template fails."""
        template_file = tmp_path / "template.md"
        template_file.write_text("Hello {name}!", encoding="utf-8")

        preset = PresetFactory(
            id="test:read_error",
            name="Read Error",
            description="Test",
            template_path=template_file,
            variables={},
        )

        # Mock read_text to raise OSError
        def mock_read_text(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr("pathlib.Path.read_text", mock_read_text)

        # Should catch OSError and add error
        result = preset_manager.validate_template_variables(preset)

        assert result.valid is False
        assert result.has_errors is True
        assert len(result.errors) == 1
        assert "Failed to read template file" in result.errors[0]
        assert "Permission denied" in result.errors[0]

    def test_validate_template_all_valid(self, preset_manager, tmp_path):
        """Test successful validation with all variables properly defined."""
        template_file = tmp_path / "template.md"
        template_file.write_text("Name: {name}, Version: {version}", encoding="utf-8")

        preset = PresetFactory(
            id="test:all_valid",
            name="All Valid",
            description="Test",
            template_path=template_file,
            variables={"name": "Project", "version": "1.0.0"},
        )

        # Should validate successfully
        result = preset_manager.validate_template_variables(preset)

        assert result.valid is True
        assert not result.has_errors
        assert not result.has_warnings
