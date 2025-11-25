"""Tests for preset repository implementations."""

import tempfile
from pathlib import Path

import pytest

from claudefig.exceptions import (
    BuiltInModificationError,
    PresetExistsError,
    PresetNotFoundError,
)
from claudefig.models import FileType, PresetSource
from claudefig.repositories.preset_repository import (
    FakePresetRepository,
    TomlPresetRepository,
)
from tests.factories import PresetFactory


class TestTomlPresetRepository:
    """Test TomlPresetRepository implementation."""

    def test_init_with_paths(self):
        """Test initialization with preset paths."""
        user_path = Path("/tmp/user")
        project_path = Path("/tmp/project")

        repo = TomlPresetRepository(
            user_presets_dir=user_path, project_presets_dir=project_path
        )

        assert repo.user_presets_dir == user_path
        assert repo.project_presets_dir == project_path

    def test_list_presets_returns_builtin_presets(self):
        """Test list_presets returns built-in presets."""
        repo = TomlPresetRepository()

        presets = repo.list_presets()

        # Should have at least some built-in presets
        assert len(presets) > 0
        builtin_presets = [p for p in presets if p.source == PresetSource.BUILT_IN]
        assert len(builtin_presets) > 0

    def test_list_presets_filter_by_file_type(self):
        """Test filtering presets by file type."""
        repo = TomlPresetRepository()

        claude_md_presets = repo.list_presets(file_type="claude_md")

        assert all(p.type == FileType.CLAUDE_MD for p in claude_md_presets)

    def test_list_presets_filter_by_source(self):
        """Test filtering presets by source."""
        repo = TomlPresetRepository()

        builtin_presets = repo.list_presets(source=PresetSource.BUILT_IN)

        assert all(p.source == PresetSource.BUILT_IN for p in builtin_presets)

    def test_get_preset_existing(self):
        """Test getting an existing preset."""
        repo = TomlPresetRepository()

        # Get a built-in preset
        preset = repo.get_preset("claude_md:default")

        assert preset is not None
        assert preset.id == "claude_md:default"
        assert preset.type == FileType.CLAUDE_MD

    def test_get_preset_nonexistent(self):
        """Test getting non-existent preset returns None."""
        repo = TomlPresetRepository()

        preset = repo.get_preset("nonexistent:preset")

        assert preset is None

    def test_exists_true_for_existing_preset(self):
        """Test exists returns True for existing preset."""
        repo = TomlPresetRepository()

        assert repo.exists("claude_md:default")

    def test_exists_false_for_nonexistent_preset(self):
        """Test exists returns False for non-existent preset."""
        repo = TomlPresetRepository()

        assert not repo.exists("nonexistent:preset")

    def test_add_preset_user_source(self):
        """Test adding a preset to user source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            user_dir = Path(tmpdir) / "user"
            repo = TomlPresetRepository(user_presets_dir=user_dir)

            preset = PresetFactory(
                id="claude_md:test", name="test", description="Test preset"
            )

            repo.add_preset(preset, PresetSource.USER)

            # Clear cache to force reload from disk
            repo.clear_cache()

            # Verify preset can be retrieved
            retrieved = repo.get_preset("claude_md:test")
            assert retrieved is not None
            assert retrieved.name == "test"

    def test_add_preset_project_source(self):
        """Test adding a preset to project source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "project"
            repo = TomlPresetRepository(project_presets_dir=project_dir)

            preset = PresetFactory(
                id="claude_md:test",
                name="test",
                description="Test preset",
                source=PresetSource.PROJECT,
            )

            repo.add_preset(preset, PresetSource.PROJECT)

            # Clear cache and verify can be retrieved
            repo.clear_cache()
            retrieved = repo.get_preset("claude_md:test")
            assert retrieved is not None

    def test_add_preset_builtin_source_raises_error(self):
        """Test adding to built-in source raises error."""
        repo = TomlPresetRepository()

        preset = PresetFactory(
            id="claude_md:test",
            name="test",
            description="Test",
            source=PresetSource.BUILT_IN,
        )

        with pytest.raises(BuiltInModificationError):
            repo.add_preset(preset, PresetSource.BUILT_IN)

    def test_add_preset_duplicate_raises_error(self):
        """Test adding duplicate preset raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            user_dir = Path(tmpdir) / "user"
            repo = TomlPresetRepository(user_presets_dir=user_dir)

            preset = PresetFactory(id="claude_md:test", name="test", description="Test")

            repo.add_preset(preset, PresetSource.USER)

            with pytest.raises(PresetExistsError):
                repo.add_preset(preset, PresetSource.USER)

    def test_delete_preset_user(self):
        """Test deleting a user preset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            user_dir = Path(tmpdir) / "user"
            repo = TomlPresetRepository(user_presets_dir=user_dir)

            # Add preset
            preset = PresetFactory(id="claude_md:test", name="test", description="Test")
            repo.add_preset(preset, PresetSource.USER)

            # Delete preset
            repo.delete_preset("claude_md:test")

            # Verify deleted
            assert not repo.exists("claude_md:test")

    def test_delete_preset_builtin_raises_error(self):
        """Test deleting built-in preset raises error."""
        repo = TomlPresetRepository()

        with pytest.raises(BuiltInModificationError):
            repo.delete_preset("claude_md:default")

    def test_delete_preset_nonexistent_raises_error(self):
        """Test deleting non-existent preset raises error."""
        repo = TomlPresetRepository()

        with pytest.raises(PresetNotFoundError):
            repo.delete_preset("nonexistent:preset")

    def test_get_template_content_with_template_path(self):
        """Test getting template content for preset with template_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = Path(tmpdir) / "template.md"
            template_file.write_text("# Template Content")

            preset = PresetFactory(
                id="claude_md:test",
                name="test",
                description="Test",
                template_path=template_file,
            )

            repo = TomlPresetRepository()

            content = repo.get_template_content(preset)

            assert content == "# Template Content"

    def test_caching_works(self):
        """Test that caching reduces file I/O."""
        repo = TomlPresetRepository()

        # First call loads built-in presets
        preset1 = repo.get_preset("claude_md:default")
        assert preset1 is not None

        # Second call uses cache
        preset2 = repo.get_preset("claude_md:default")
        assert preset2 is not None
        assert preset2.id == preset1.id

    def test_get_load_errors_returns_errors(self):
        """Test get_load_errors returns loading errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            user_dir = Path(tmpdir) / "user"
            user_dir.mkdir(parents=True)

            # Create invalid preset file directly in user_dir
            invalid_file = user_dir / "invalid.toml"
            invalid_file.write_text("invalid toml {{{")

            repo = TomlPresetRepository(user_presets_dir=user_dir)

            # Trigger loading
            repo.list_presets()

            errors = repo.get_load_errors()

            assert len(errors) > 0
            assert any("invalid" in err.lower() for err in errors)


class TestFakePresetRepository:
    """Test FakePresetRepository in-memory implementation."""

    def test_init_empty(self):
        """Test initialization with no presets."""
        repo = FakePresetRepository()

        presets = repo.list_presets()

        assert len(presets) == 0

    def test_init_with_presets(self):
        """Test initialization with preset list."""
        preset1 = PresetFactory(
            id="claude_md:test1", name="test1", description="Test 1"
        )
        preset2 = PresetFactory(
            id="gitignore:test2",
            name="test2",
            type=FileType.GITIGNORE,
            description="Test 2",
        )

        repo = FakePresetRepository([preset1, preset2])

        presets = repo.list_presets()

        assert len(presets) == 2

    def test_list_presets_filter_by_file_type(self):
        """Test filtering by file type."""
        preset1 = PresetFactory(id="claude_md:test1", name="test1", description="Test")
        preset2 = PresetFactory(
            id="gitignore:test2",
            name="test2",
            type=FileType.GITIGNORE,
            description="Test",
        )

        repo = FakePresetRepository([preset1, preset2])

        claude_presets = repo.list_presets(file_type="claude_md")

        assert len(claude_presets) == 1
        assert claude_presets[0].type == FileType.CLAUDE_MD

    def test_list_presets_filter_by_source(self):
        """Test filtering by source."""
        preset1 = PresetFactory(id="claude_md:test1", name="test1", description="Test")
        preset2 = PresetFactory(
            id="claude_md:test2",
            name="test2",
            description="Test",
            source=PresetSource.PROJECT,
        )

        repo = FakePresetRepository([preset1, preset2])

        user_presets = repo.list_presets(source=PresetSource.USER)

        assert len(user_presets) == 1
        assert user_presets[0].source == PresetSource.USER

    def test_get_preset_existing(self):
        """Test getting existing preset."""
        preset = PresetFactory(id="claude_md:test", name="test", description="Test")

        repo = FakePresetRepository([preset])

        result = repo.get_preset("claude_md:test")

        assert result is not None
        assert result.id == "claude_md:test"

    def test_get_preset_nonexistent(self):
        """Test getting non-existent preset returns None."""
        repo = FakePresetRepository()

        result = repo.get_preset("nonexistent:preset")

        assert result is None

    def test_exists(self):
        """Test exists method."""
        preset = PresetFactory(id="claude_md:test", name="test", description="Test")

        repo = FakePresetRepository([preset])

        assert repo.exists("claude_md:test")
        assert not repo.exists("nonexistent:preset")

    def test_add_preset_success(self):
        """Test adding a preset."""
        repo = FakePresetRepository()

        preset = PresetFactory(id="claude_md:test", name="test", description="Test")

        repo.add_preset(preset, PresetSource.USER)

        assert repo.exists("claude_md:test")
        assert len(repo.list_presets()) == 1

    def test_add_preset_duplicate_raises_error(self):
        """Test adding duplicate preset raises error."""
        preset = PresetFactory(id="claude_md:test", name="test", description="Test")

        repo = FakePresetRepository([preset])

        with pytest.raises(PresetExistsError) as exc_info:
            repo.add_preset(preset, PresetSource.USER)

        assert "claude_md:test" in str(exc_info.value)

    def test_add_preset_builtin_raises_error(self):
        """Test adding to built-in source raises error."""
        repo = FakePresetRepository()

        preset = PresetFactory(
            id="claude_md:test",
            name="test",
            description="Test",
            source=PresetSource.BUILT_IN,
        )

        with pytest.raises(BuiltInModificationError) as exc_info:
            repo.add_preset(preset, PresetSource.BUILT_IN)

        assert "claude_md:test" in str(exc_info.value)

    def test_delete_preset_success(self):
        """Test deleting a preset."""
        preset = PresetFactory(id="claude_md:test", name="test", description="Test")

        repo = FakePresetRepository([preset])

        repo.delete_preset("claude_md:test")

        assert not repo.exists("claude_md:test")
        assert len(repo.list_presets()) == 0

    def test_delete_preset_nonexistent_raises_error(self):
        """Test deleting non-existent preset raises error."""
        repo = FakePresetRepository()

        with pytest.raises(PresetNotFoundError):
            repo.delete_preset("nonexistent:preset")

    def test_get_template_content(self):
        """Test getting template content returns mock."""
        preset = PresetFactory(id="claude_md:test", name="test", description="Test")

        repo = FakePresetRepository([preset])

        content = repo.get_template_content(preset)

        # FakePresetRepository returns mock content
        assert "Mock template" in content
        assert preset.id in content
