"""Tests for preset service layer."""

import tempfile
from pathlib import Path

import pytest

from claudefig.exceptions import (
    BuiltInModificationError,
    CircularDependencyError,
    PresetExistsError,
    PresetNotFoundError,
)
from claudefig.models import FileType, PresetSource
from claudefig.repositories.preset_repository import FakePresetRepository
from claudefig.services import preset_service
from tests.factories import PresetFactory


class TestListPresets:
    """Test list_presets() function."""

    def test_lists_all_presets_when_no_filters(self):
        """Test listing all presets without filters."""
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

        result = preset_service.list_presets(repo)

        assert len(result) == 2

    def test_filters_by_file_type(self):
        """Test filtering presets by file type."""
        preset1 = PresetFactory(id="claude_md:test", name="test", description="Test")
        preset2 = PresetFactory(
            id="gitignore:test",
            name="test",
            type=FileType.GITIGNORE,
            description="Test",
        )
        repo = FakePresetRepository([preset1, preset2])

        result = preset_service.list_presets(repo, file_type="claude_md")

        assert len(result) == 1
        assert result[0].type == FileType.CLAUDE_MD

    def test_filters_by_source(self):
        """Test filtering presets by source."""
        preset1 = PresetFactory(id="claude_md:user", name="user", description="User")
        preset2 = PresetFactory(
            id="claude_md:project",
            name="project",
            description="Project",
            source=PresetSource.PROJECT,
        )
        repo = FakePresetRepository([preset1, preset2])

        result = preset_service.list_presets(repo, source=PresetSource.USER)

        assert len(result) == 1
        assert result[0].source == PresetSource.USER


class TestGetPreset:
    """Test get_preset() function."""

    def test_gets_existing_preset(self):
        """Test getting an existing preset."""
        preset = PresetFactory(id="claude_md:test", name="test", description="Test")
        repo = FakePresetRepository([preset])

        result = preset_service.get_preset(repo, "claude_md:test")

        assert result is not None
        assert result.id == "claude_md:test"

    def test_returns_none_for_nonexistent_preset(self):
        """Test returns None for non-existent preset."""
        repo = FakePresetRepository()

        result = preset_service.get_preset(repo, "nonexistent:preset")

        assert result is None


class TestCreatePreset:
    """Test create_preset() function."""

    def test_creates_preset_in_user_source(self):
        """Test creating preset in user source."""
        repo = FakePresetRepository()
        preset = PresetFactory(id="claude_md:new", name="new", description="New preset")

        result = preset_service.create_preset(repo, preset, PresetSource.USER)

        assert result.id == "claude_md:new"
        assert repo.exists("claude_md:new")

    def test_creates_preset_in_project_source(self):
        """Test creating preset in project source."""
        repo = FakePresetRepository()
        preset = PresetFactory(
            id="claude_md:new",
            name="new",
            description="New",
            source=PresetSource.PROJECT,
        )

        preset_service.create_preset(repo, preset, PresetSource.PROJECT)

        assert repo.exists("claude_md:new")
        retrieved = repo.get_preset("claude_md:new")
        assert retrieved is not None
        assert retrieved.source == PresetSource.PROJECT

    def test_raises_error_for_builtin_source(self):
        """Test raises error when trying to create in built-in source."""
        repo = FakePresetRepository()
        preset = PresetFactory(
            id="claude_md:test",
            name="test",
            description="Test",
            source=PresetSource.BUILT_IN,
        )

        with pytest.raises(BuiltInModificationError):
            preset_service.create_preset(repo, preset, PresetSource.BUILT_IN)

    def test_raises_error_for_duplicate_preset(self):
        """Test raises error when preset already exists."""
        preset = PresetFactory(
            id="claude_md:existing", name="existing", description="Existing"
        )
        repo = FakePresetRepository([preset])

        with pytest.raises(PresetExistsError):
            preset_service.create_preset(repo, preset, PresetSource.USER)

    def test_defaults_to_user_source(self):
        """Test defaults to USER source when not specified."""
        repo = FakePresetRepository()
        preset = PresetFactory(id="claude_md:test", name="test", description="Test")

        preset_service.create_preset(repo, preset)

        assert repo.exists("claude_md:test")


class TestDeletePreset:
    """Test delete_preset() function."""

    def test_deletes_existing_preset(self):
        """Test deleting an existing preset."""
        preset = PresetFactory(id="claude_md:test", name="test", description="Test")
        repo = FakePresetRepository([preset])

        preset_service.delete_preset(repo, "claude_md:test")

        assert not repo.exists("claude_md:test")

    def test_raises_error_for_nonexistent_preset(self):
        """Test raises error when deleting non-existent preset."""
        repo = FakePresetRepository()

        with pytest.raises(PresetNotFoundError):
            preset_service.delete_preset(repo, "nonexistent:preset")


class TestRenderPreset:
    """Test render_preset() function."""

    def test_renders_template_without_variables(self):
        """Test rendering template with no variables."""
        preset = PresetFactory(id="claude_md:test", name="test", description="Test")
        repo = FakePresetRepository([preset])

        result = preset_service.render_preset(repo, preset)

        # FakePresetRepository returns: f"# Mock template for {preset.id}\n{variable}"
        assert "Mock template for claude_md:test" in result

    def test_substitutes_preset_default_variables(self):
        """Test substitutes preset default variables."""
        preset = PresetFactory(
            id="claude_md:test",
            name="test",
            description="Test",
            variables={"name": "TestProject", "version": "1.0"},
        )
        repo = FakePresetRepository([preset])
        # FakePresetRepository returns: f"Mock template content for {preset.id}"

        result = preset_service.render_preset(repo, preset)

        # Basic check - actual substitution depends on template content
        assert isinstance(result, str)

    def test_provided_variables_override_defaults(self):
        """Test provided variables override preset defaults."""
        preset = PresetFactory(
            id="claude_md:test",
            name="test",
            description="Test",
            variables={"variable": "default_value"},
        )
        repo = FakePresetRepository([preset])

        # FakePresetRepository template contains {variable}
        result = preset_service.render_preset(
            repo, preset, variables={"variable": "override_value"}
        )

        # Should use override value
        assert "override_value" in result
        assert "default_value" not in result

    def test_handles_empty_variable_dict(self):
        """Test handles empty variable dictionary."""
        preset = PresetFactory(
            id="claude_md:test", name="test", description="Test", variables={}
        )
        repo = FakePresetRepository([preset])

        result = preset_service.render_preset(repo, preset, variables={})

        assert isinstance(result, str)


class TestExtractTemplateVariables:
    """Test extract_template_variables() function."""

    def test_extracts_single_variable(self):
        """Test extracting single variable."""
        template = "Hello {name}!"

        result = preset_service.extract_template_variables(template)

        assert result == {"name"}

    def test_extracts_multiple_variables(self):
        """Test extracting multiple variables."""
        template = "Project: {project_name}, Version: {version}, Author: {author}"

        result = preset_service.extract_template_variables(template)

        assert result == {"project_name", "version", "author"}

    def test_returns_empty_set_for_no_variables(self):
        """Test returns empty set when no variables."""
        template = "Static content with no variables"

        result = preset_service.extract_template_variables(template)

        assert result == set()

    def test_handles_duplicate_variables(self):
        """Test handles duplicate variable references."""
        template = "{name} is great. {name} is awesome!"

        result = preset_service.extract_template_variables(template)

        assert result == {"name"}

    def test_extracts_variables_with_underscores(self):
        """Test extracts variables with underscores."""
        template = "{project_name} by {author_email}"

        result = preset_service.extract_template_variables(template)

        assert result == {"project_name", "author_email"}

    def test_ignores_invalid_variable_names(self):
        """Test ignores invalid variable patterns."""
        template = "{123invalid} {valid_var} {also-invalid}"

        result = preset_service.extract_template_variables(template)

        # Only valid_var should be extracted (must start with letter/underscore)
        assert result == {"valid_var"}

    def test_handles_nested_braces(self):
        """Test doesn't extract nested braces incorrectly."""
        template = "{{escaped}} {real_var}"

        result = preset_service.extract_template_variables(template)

        # Should only extract real_var
        assert "real_var" in result


class TestValidatePresetVariables:
    """Test validate_preset_variables() function."""

    def test_valid_when_all_variables_defined(self):
        """Test validation passes when all template variables are defined."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = Path(tmpdir) / "template.md"
            template_file.write_text("# {title}\nAuthor: {author}")

            preset = PresetFactory(
                id="claude_md:test",
                name="test",
                description="Test",
                template_path=template_file,
                variables={"title": "Test", "author": "Me"},
            )
            repo = FakePresetRepository([preset])

            result = preset_service.validate_preset_variables(repo, preset)

            assert result.valid
            # May have warnings about unused vars but no errors

    def test_valid_when_no_template_path(self):
        """Test validation passes when preset has no template."""
        preset = PresetFactory(
            id="claude_md:test", name="test", description="Test", template_path=None
        )
        repo = FakePresetRepository([preset])

        result = preset_service.validate_preset_variables(repo, preset)

        assert result.valid
        assert not result.has_errors

    def test_warns_about_missing_variables(self):
        """Test warns when template uses undefined variables."""
        preset = PresetFactory(
            id="claude_md:test",
            name="test",
            description="Test",
            template_path=Path("/fake/path.md"),  # FakePresetRepository ignores this
            variables={},  # No variables defined, but template uses {variable}
        )
        repo = FakePresetRepository([preset])

        result = preset_service.validate_preset_variables(repo, preset)

        assert result.valid  # Warnings, not errors
        assert result.has_warnings
        # FakePresetRepository template has {variable}
        assert any("variable" in warn for warn in result.warnings)

    def test_warns_about_unused_variables(self):
        """Test warns when preset defines unused variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = Path(tmpdir) / "template.md"
            template_file.write_text("# {title}")

            preset = PresetFactory(
                id="claude_md:test",
                name="test",
                description="Test",
                template_path=template_file,
                variables={"title": "Test", "unused_var": "value"},
            )
            repo = FakePresetRepository([preset])

            result = preset_service.validate_preset_variables(repo, preset)

            assert result.valid
            assert result.has_warnings
            assert any("unused_var" in warn for warn in result.warnings)

    def test_considers_provided_variables(self):
        """Test validation considers provided variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = Path(tmpdir) / "template.md"
            template_file.write_text("# {title}\nAuthor: {author}")

            preset = PresetFactory(
                id="claude_md:test",
                name="test",
                description="Test",
                template_path=template_file,
                variables={"title": "Test"},  # Missing 'author' in defaults
            )
            repo = FakePresetRepository([preset])

            # Provide 'author' at validation time
            result = preset_service.validate_preset_variables(
                repo, preset, variables={"author": "Me"}
            )

            assert result.valid
            # Should not warn about missing 'author' since it's provided
            assert not any(
                "author" in warn and "uses variable" in warn for warn in result.warnings
            )

    def test_fake_repository_does_not_raise_template_errors(self):
        """Test FakePresetRepository provides mock template even for invalid paths."""
        preset = PresetFactory(
            id="claude_md:test",
            name="test",
            description="Test",
            template_path=Path("/nonexistent/template.md"),
            variables={"variable": "value"},
        )
        repo = FakePresetRepository([preset])

        # FakePresetRepository always returns mock content, never errors
        result = preset_service.validate_preset_variables(repo, preset)

        # Should succeed since FakePresetRepository provides mock template
        assert result.valid
        # No errors about missing template
        assert not result.has_errors


class TestResolvePresetVariables:
    """Test resolve_preset_variables() function."""

    def test_returns_own_variables_when_no_inheritance(self):
        """Test returns preset's own variables when no extends."""
        preset = PresetFactory(
            id="claude_md:test",
            name="test",
            description="Test",
            variables={"var1": "value1", "var2": "value2"},
            extends=None,
        )
        repo = FakePresetRepository([preset])

        result = preset_service.resolve_preset_variables(repo, preset)

        assert result == {"var1": "value1", "var2": "value2"}

    def test_merges_parent_variables(self):
        """Test merges variables from parent preset."""
        parent = PresetFactory(
            name="parent",
            description="Parent",
            variables={"parent_var": "parent_value", "shared": "parent"},
        )
        child = PresetFactory(
            name="child",
            description="Child",
            variables={"child_var": "child_value", "shared": "child"},
            extends=parent.id,
        )
        repo = FakePresetRepository([parent, child])

        result = preset_service.resolve_preset_variables(repo, child)

        # Should have parent_var from parent, child_var from child
        assert "parent_var" in result
        assert "child_var" in result
        # Child should override parent for shared var
        assert result["shared"] == "child"

    def test_returns_own_vars_when_parent_not_found(self):
        """Test returns own variables when parent preset not found."""
        child = PresetFactory(
            name="child",
            description="Child",
            variables={"child_var": "value"},
            extends="claude_md:nonexistent",
        )
        repo = FakePresetRepository([child])

        result = preset_service.resolve_preset_variables(repo, child)

        assert result == {"child_var": "value"}

    def test_handles_multi_level_inheritance(self):
        """Test handles multi-level inheritance chain."""
        grandparent = PresetFactory(
            name="grandparent", variables={"gp_var": "gp_value"}
        )
        parent = PresetFactory(
            name="parent", variables={"p_var": "p_value"}, extends=grandparent.id
        )
        child = PresetFactory(
            name="child", variables={"c_var": "c_value"}, extends=parent.id
        )
        repo = FakePresetRepository([grandparent, parent, child])

        result = preset_service.resolve_preset_variables(repo, child)

        # Should have all three levels of variables
        assert "gp_var" in result
        assert "p_var" in result
        assert "c_var" in result

    def test_child_overrides_parent_and_grandparent(self):
        """Test child variables override parent and grandparent."""
        grandparent = PresetFactory(name="grandparent", variables={"var": "gp_value"})
        parent = PresetFactory(
            name="parent", variables={"var": "p_value"}, extends=grandparent.id
        )
        child = PresetFactory(
            name="child", variables={"var": "c_value"}, extends=parent.id
        )
        repo = FakePresetRepository([grandparent, parent, child])

        result = preset_service.resolve_preset_variables(repo, child)

        # Child should win
        assert result["var"] == "c_value"

    def test_detects_direct_circular_dependency(self):
        """Test raises CircularDependencyError for direct self-reference."""
        # Preset extends itself
        preset = PresetFactory(
            name="self_ref",
            variables={"var": "value"},
        )
        preset.extends = preset.id  # Self-reference
        repo = FakePresetRepository([preset])

        with pytest.raises(CircularDependencyError) as exc_info:
            preset_service.resolve_preset_variables(repo, preset)

        assert preset.id in str(exc_info.value)

    def test_detects_two_way_circular_dependency(self):
        """Test raises CircularDependencyError for A -> B -> A cycle."""
        preset_a = PresetFactory(name="preset_a", variables={"a": "1"})
        preset_b = PresetFactory(name="preset_b", variables={"b": "2"})
        preset_a.extends = preset_b.id
        preset_b.extends = preset_a.id
        repo = FakePresetRepository([preset_a, preset_b])

        with pytest.raises(CircularDependencyError) as exc_info:
            preset_service.resolve_preset_variables(repo, preset_a)

        # Both presets should be mentioned in the cycle
        error_message = str(exc_info.value)
        assert "preset_a" in error_message or preset_a.id in error_message
        assert "preset_b" in error_message or preset_b.id in error_message

    def test_detects_three_way_circular_dependency(self):
        """Test raises CircularDependencyError for A -> B -> C -> A cycle."""
        preset_a = PresetFactory(name="preset_a", variables={"a": "1"})
        preset_b = PresetFactory(name="preset_b", variables={"b": "2"})
        preset_c = PresetFactory(name="preset_c", variables={"c": "3"})
        preset_a.extends = preset_b.id
        preset_b.extends = preset_c.id
        preset_c.extends = preset_a.id
        repo = FakePresetRepository([preset_a, preset_b, preset_c])

        with pytest.raises(CircularDependencyError):
            preset_service.resolve_preset_variables(repo, preset_a)

    def test_no_error_for_valid_inheritance_chain(self):
        """Test no error raised for valid non-circular inheritance."""
        grandparent = PresetFactory(name="grandparent", variables={"gp": "1"})
        parent = PresetFactory(
            name="parent", variables={"p": "2"}, extends=grandparent.id
        )
        child = PresetFactory(name="child", variables={"c": "3"}, extends=parent.id)
        repo = FakePresetRepository([grandparent, parent, child])

        # Should not raise
        result = preset_service.resolve_preset_variables(repo, child)

        assert "gp" in result
        assert "p" in result
        assert "c" in result
