"""Tests for core data models."""

from pathlib import Path

import pytest

from claudefig.models import (
    FileInstance,
    FileType,
    Preset,
    PresetSource,
    ValidationResult,
)
from tests.factories import FileInstanceFactory


class TestFileTypeEnum:
    """Tests for FileType enum."""

    def test_all_file_types_exist(self):
        """Test that all expected file types are defined."""
        expected_types = [
            "CLAUDE_MD",
            "SETTINGS_JSON",
            "SETTINGS_LOCAL_JSON",
            "GITIGNORE",
            "COMMANDS",
            "AGENTS",
            "HOOKS",
            "OUTPUT_STYLES",
            "STATUSLINE",
            "MCP",
            "PLUGINS",
            "SKILLS",
        ]
        for type_name in expected_types:
            assert hasattr(FileType, type_name), f"Missing FileType.{type_name}"

    def test_file_type_values(self):
        """Test that file type enum values are correct."""
        assert FileType.CLAUDE_MD.value == "claude_md"
        assert FileType.SETTINGS_JSON.value == "settings_json"
        assert FileType.SETTINGS_LOCAL_JSON.value == "settings_local_json"
        assert FileType.GITIGNORE.value == "gitignore"
        assert FileType.COMMANDS.value == "commands"
        assert FileType.AGENTS.value == "agents"
        assert FileType.HOOKS.value == "hooks"
        assert FileType.OUTPUT_STYLES.value == "output_styles"
        assert FileType.STATUSLINE.value == "statusline"
        assert FileType.MCP.value == "mcp"
        assert FileType.PLUGINS.value == "plugins"
        assert FileType.SKILLS.value == "skills"

    def test_display_name_property(self):
        """Test display_name property returns human-readable names."""
        assert FileType.CLAUDE_MD.display_name == "CLAUDE.md"
        assert FileType.SETTINGS_JSON.display_name == "settings.json"
        assert FileType.SETTINGS_LOCAL_JSON.display_name == "settings.local.json"
        assert FileType.GITIGNORE.display_name == ".gitignore"
        assert FileType.COMMANDS.display_name == "Slash Commands"
        assert FileType.AGENTS.display_name == "Sub-Agents"
        assert FileType.HOOKS.display_name == "Hooks"
        assert FileType.OUTPUT_STYLES.display_name == "Output Styles"
        assert FileType.STATUSLINE.display_name == "Status Line"
        assert FileType.MCP.display_name == "MCP Servers"
        assert FileType.PLUGINS.display_name == "Plugins"
        assert FileType.SKILLS.display_name == "Skills"

    def test_default_path_property(self):
        """Test default_path property returns correct paths."""
        assert FileType.CLAUDE_MD.default_path == "CLAUDE.md"
        assert FileType.SETTINGS_JSON.default_path == ".claude/settings.json"
        assert (
            FileType.SETTINGS_LOCAL_JSON.default_path == ".claude/settings.local.json"
        )
        assert FileType.GITIGNORE.default_path == ".gitignore"
        assert FileType.COMMANDS.default_path == ".claude/commands/"
        assert FileType.AGENTS.default_path == ".claude/agents/"
        assert FileType.HOOKS.default_path == ".claude/hooks/"
        assert FileType.OUTPUT_STYLES.default_path == ".claude/output-styles/"
        assert FileType.STATUSLINE.default_path == ".claude/statusline.sh"
        assert FileType.MCP.default_path == ".claude/mcp/"
        assert FileType.PLUGINS.default_path == ".claude/plugins/"
        assert FileType.SKILLS.default_path == ".claude/skills/"

    def test_supports_multiple_property(self):
        """Test supports_multiple property identifies single-instance types."""
        # Single instance types
        assert not FileType.SETTINGS_JSON.supports_multiple
        assert not FileType.SETTINGS_LOCAL_JSON.supports_multiple
        assert not FileType.STATUSLINE.supports_multiple

        # Multiple instance types
        assert FileType.CLAUDE_MD.supports_multiple
        assert FileType.GITIGNORE.supports_multiple
        assert FileType.COMMANDS.supports_multiple
        assert FileType.AGENTS.supports_multiple
        assert FileType.HOOKS.supports_multiple
        assert FileType.OUTPUT_STYLES.supports_multiple
        assert FileType.MCP.supports_multiple
        assert FileType.PLUGINS.supports_multiple
        assert FileType.SKILLS.supports_multiple

    def test_is_directory_property(self):
        """Test is_directory property identifies directory types."""
        # Directory types
        assert FileType.COMMANDS.is_directory
        assert FileType.AGENTS.is_directory
        assert FileType.HOOKS.is_directory
        assert FileType.OUTPUT_STYLES.is_directory
        assert FileType.MCP.is_directory
        assert FileType.PLUGINS.is_directory
        assert FileType.SKILLS.is_directory

        # File types
        assert not FileType.CLAUDE_MD.is_directory
        assert not FileType.SETTINGS_JSON.is_directory
        assert not FileType.SETTINGS_LOCAL_JSON.is_directory
        assert not FileType.GITIGNORE.is_directory
        assert not FileType.STATUSLINE.is_directory

    def test_append_mode_property(self):
        """Test append_mode property identifies append-only types."""
        # Gitignore should append, not replace
        assert FileType.GITIGNORE.append_mode

        # All others should not append
        assert not FileType.CLAUDE_MD.append_mode
        assert not FileType.SETTINGS_JSON.append_mode
        assert not FileType.SETTINGS_LOCAL_JSON.append_mode
        assert not FileType.COMMANDS.append_mode
        assert not FileType.AGENTS.append_mode
        assert not FileType.HOOKS.append_mode
        assert not FileType.OUTPUT_STYLES.append_mode
        assert not FileType.STATUSLINE.append_mode
        assert not FileType.MCP.append_mode

    def test_all_types_have_complete_metadata(self):
        """Test that all file types have complete metadata in all properties."""
        for file_type in FileType:
            # All should have display names
            assert file_type.display_name
            assert isinstance(file_type.display_name, str)

            # All should have default paths
            assert file_type.default_path
            assert isinstance(file_type.default_path, str)

            # All should have boolean flags
            assert isinstance(file_type.supports_multiple, bool)
            assert isinstance(file_type.is_directory, bool)
            assert isinstance(file_type.append_mode, bool)

    def test_path_customizable_property(self):
        """Test path_customizable property identifies customizable types."""
        # Only CLAUDE.md and .gitignore allow custom paths
        assert FileType.CLAUDE_MD.path_customizable
        assert FileType.GITIGNORE.path_customizable

        # All other types have fixed paths/directories
        assert not FileType.SETTINGS_JSON.path_customizable
        assert not FileType.SETTINGS_LOCAL_JSON.path_customizable
        assert not FileType.COMMANDS.path_customizable
        assert not FileType.AGENTS.path_customizable
        assert not FileType.HOOKS.path_customizable
        assert not FileType.OUTPUT_STYLES.path_customizable
        assert not FileType.STATUSLINE.path_customizable
        assert not FileType.MCP.path_customizable


class TestPresetSourceEnum:
    """Tests for PresetSource enum."""

    def test_preset_source_values(self):
        """Test preset source enum values."""
        assert PresetSource.BUILT_IN.value == "built-in"
        assert PresetSource.USER.value == "user"
        assert PresetSource.PROJECT.value == "project"


class TestPreset:
    """Tests for Preset dataclass."""

    def test_preset_creation(self):
        """Test creating a Preset with all fields."""
        preset = Preset(
            id="claude_md:default",
            type=FileType.CLAUDE_MD,
            name="Default",
            description="Standard Claude Code configuration file",
            source=PresetSource.BUILT_IN,
            template_path=Path("/templates/claude_md_default.md"),
            variables={"version": "1.0"},
            extends="claude_md:base",
            tags=["standard", "general"],
        )

        assert preset.id == "claude_md:default"
        assert preset.type == FileType.CLAUDE_MD
        assert preset.name == "Default"
        assert preset.description == "Standard Claude Code configuration file"
        assert preset.source == PresetSource.BUILT_IN
        assert preset.template_path == Path("/templates/claude_md_default.md")
        assert preset.variables == {"version": "1.0"}
        assert preset.extends == "claude_md:base"
        assert preset.tags == ["standard", "general"]

    def test_preset_minimal_creation(self):
        """Test creating a Preset with minimal fields."""
        preset = Preset(
            id="test:minimal",
            type=FileType.CLAUDE_MD,
            name="Minimal",
            description="Minimal preset",
            source=PresetSource.USER,
        )

        assert preset.id == "test:minimal"
        assert preset.type == FileType.CLAUDE_MD
        assert preset.name == "Minimal"
        assert preset.description == "Minimal preset"
        assert preset.source == PresetSource.USER
        assert preset.template_path is None
        assert preset.variables == {}
        assert preset.extends is None
        assert preset.tags == []

    def test_preset_to_dict(self):
        """Test converting Preset to dictionary."""
        preset = Preset(
            id="claude_md:test",
            type=FileType.CLAUDE_MD,
            name="Test",
            description="Test preset",
            source=PresetSource.USER,
            template_path=Path("/test/template.md"),
            variables={"key": "value"},
            extends="claude_md:base",
            tags=["test", "example"],
        )

        preset_dict = preset.to_dict()

        assert preset_dict == {
            "id": "claude_md:test",
            "type": "claude_md",
            "name": "Test",
            "description": "Test preset",
            "source": "user",
            "template_path": str(Path("/test/template.md")),
            "variables": {"key": "value"},
            "extends": "claude_md:base",
            "tags": ["test", "example"],
        }

    def test_preset_to_dict_minimal(self):
        """Test converting minimal Preset to dictionary (None values are filtered out)."""
        preset = Preset(
            id="test:minimal",
            type=FileType.GITIGNORE,
            name="Minimal",
            description="",
            source=PresetSource.BUILT_IN,
        )

        preset_dict = preset.to_dict()

        # After Phase 2 fix: to_dict() filters out None values for TOML compatibility
        assert preset_dict == {
            "id": "test:minimal",
            "type": "gitignore",
            "name": "Minimal",
            "description": "",
            "source": "built-in",
            "variables": {},
            # template_path, extends, and tags are omitted when None/empty
        }

    def test_preset_from_dict(self):
        """Test creating Preset from dictionary."""
        preset_data = {
            "id": "claude_md:from_dict",
            "type": "claude_md",
            "name": "From Dict",
            "description": "Created from dict",
            "source": "project",
            "template_path": "/path/to/template.md",
            "variables": {"foo": "bar"},
            "extends": "claude_md:parent",
            "tags": ["imported"],
        }

        preset = Preset.from_dict(preset_data)

        assert preset.id == "claude_md:from_dict"
        assert preset.type == FileType.CLAUDE_MD
        assert preset.name == "From Dict"
        assert preset.description == "Created from dict"
        assert preset.source == PresetSource.PROJECT
        assert preset.template_path == Path("/path/to/template.md")
        assert preset.variables == {"foo": "bar"}
        assert preset.extends == "claude_md:parent"
        assert preset.tags == ["imported"]

    def test_preset_from_dict_minimal(self):
        """Test creating Preset from minimal dictionary."""
        preset_data = {
            "id": "test:minimal",
            "type": "settings_json",
            "name": "Minimal",
        }

        preset = Preset.from_dict(preset_data)

        assert preset.id == "test:minimal"
        assert preset.type == FileType.SETTINGS_JSON
        assert preset.name == "Minimal"
        assert preset.description == ""
        assert preset.source == PresetSource.BUILT_IN  # Default
        assert preset.template_path is None
        assert preset.variables == {}
        assert preset.extends is None
        assert preset.tags == []

    def test_preset_serialization_roundtrip(self):
        """Test that to_dict -> from_dict preserves data."""
        original = Preset(
            id="roundtrip:test",
            type=FileType.COMMANDS,
            name="Roundtrip Test",
            description="Testing serialization",
            source=PresetSource.USER,
            template_path=Path("/templates/commands"),
            variables={"version": "2.0", "author": "Test"},
            extends="commands:base",
            tags=["test", "roundtrip", "example"],
        )

        # Convert to dict and back
        preset_dict = original.to_dict()
        restored = Preset.from_dict(preset_dict)

        # Verify all fields match
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.source == original.source
        assert restored.template_path == original.template_path
        assert restored.variables == original.variables
        assert restored.extends == original.extends
        assert restored.tags == original.tags

    def test_preset_repr(self):
        """Test Preset string representation."""
        preset = Preset(
            id="test:repr",
            type=FileType.CLAUDE_MD,
            name="Repr Test",
            description="Testing repr",
            source=PresetSource.USER,
        )

        repr_str = repr(preset)
        assert repr_str == "Preset(id=test:repr, name=Repr Test, source=user)"


class TestFileInstance:
    """Tests for FileInstance dataclass."""

    def test_file_instance_creation(self):
        """Test creating a FileInstance with all fields."""
        instance = FileInstance(
            id="test-instance",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
            variables={"project_name": "Test Project"},
        )

        assert instance.id == "test-instance"
        assert instance.type == FileType.CLAUDE_MD
        assert instance.preset == "claude_md:default"
        assert instance.path == "CLAUDE.md"
        assert instance.enabled is True
        assert instance.variables == {"project_name": "Test Project"}

    def test_file_instance_default_values(self):
        """Test FileInstance default values."""
        instance = FileInstance(
            id="minimal-instance",
            type=FileType.GITIGNORE,
            preset="gitignore:standard",
            path=".gitignore",
        )

        assert instance.enabled is True  # Default
        assert instance.variables == {}  # Default

    def test_file_instance_to_dict(self):
        """Test converting FileInstance to dictionary."""
        instance = FileInstance(
            id="dict-test",
            type=FileType.SETTINGS_JSON,
            preset="settings_json:default",
            path=".claude/settings.json",
            enabled=False,
            variables={"strict_mode": True},
        )

        instance_dict = instance.to_dict()

        assert instance_dict == {
            "id": "dict-test",
            "type": "settings_json",
            "preset": "settings_json:default",
            "path": ".claude/settings.json",
            "enabled": False,
            "variables": {"strict_mode": True},
        }

    def test_file_instance_from_dict(self):
        """Test creating FileInstance from dictionary."""
        instance_data = {
            "id": "from-dict-test",
            "type": "commands",
            "preset": "commands:default",
            "path": ".claude/commands/",
            "enabled": True,
            "variables": {"language": "python"},
        }

        instance = FileInstance.from_dict(instance_data)

        assert instance.id == "from-dict-test"
        assert instance.type == FileType.COMMANDS
        assert instance.preset == "commands:default"
        assert instance.path == ".claude/commands/"
        assert instance.enabled is True
        assert instance.variables == {"language": "python"}

    def test_file_instance_from_dict_minimal(self):
        """Test creating FileInstance from minimal dictionary."""
        instance_data = {
            "id": "minimal",
            "type": "claude_md",
            "preset": "claude_md:minimal",
            "path": "CLAUDE.md",
        }

        instance = FileInstance.from_dict(instance_data)

        assert instance.id == "minimal"
        assert instance.type == FileType.CLAUDE_MD
        assert instance.preset == "claude_md:minimal"
        assert instance.path == "CLAUDE.md"
        assert instance.enabled is True  # Default
        assert instance.variables == {}  # Default

    def test_file_instance_serialization_roundtrip(self):
        """Test that to_dict -> from_dict preserves data."""
        original = FileInstance(
            id="roundtrip-instance",
            type=FileType.HOOKS,
            preset="hooks:default",
            path=".claude/hooks/",
            enabled=False,
            variables={"pre_commit": True, "post_commit": False},
        )

        # Convert to dict and back
        instance_dict = original.to_dict()
        restored = FileInstance.from_dict(instance_dict)

        # Verify all fields match
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.preset == original.preset
        assert restored.path == original.path
        assert restored.enabled == original.enabled
        assert restored.variables == original.variables

    def test_file_instance_create_default(self):
        """Test creating default file instance."""
        instance = FileInstance.create_default(FileType.CLAUDE_MD, "default")

        assert instance.id == "claude_md-default"
        assert instance.type == FileType.CLAUDE_MD
        assert instance.preset == "claude_md:default"
        assert instance.path == "CLAUDE.md"  # From FileType.CLAUDE_MD.default_path
        assert instance.enabled is True
        assert instance.variables == {}

    def test_file_instance_create_default_different_types(self):
        """Test create_default for various file types."""
        # Test settings
        settings = FileInstance.create_default(FileType.SETTINGS_JSON, "strict")
        assert settings.id == "settings_json-strict"
        assert settings.preset == "settings_json:strict"
        assert settings.path == ".claude/settings.json"

        # Test commands directory
        commands = FileInstance.create_default(FileType.COMMANDS)
        assert commands.id == "commands-default"
        assert commands.preset == "commands:default"
        assert commands.path == ".claude/commands/"

        # Test statusline
        statusline = FileInstance.create_default(FileType.STATUSLINE)
        assert statusline.id == "statusline-default"
        assert statusline.preset == "statusline:default"
        assert statusline.path == ".claude/statusline.sh"

    def test_file_instance_repr(self):
        """Test FileInstance string representation."""
        instance = FileInstance(
            id="repr-test",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )

        repr_str = repr(instance)
        assert (
            repr_str
            == "FileInstance(id=repr-test, type=claude_md, path=CLAUDE.md, enabled)"
        )

    def test_file_instance_repr_disabled(self):
        """Test FileInstance string representation when disabled."""
        instance = FileInstance(
            id="disabled-test",
            type=FileType.GITIGNORE,
            preset="gitignore:standard",
            path=".gitignore",
            enabled=False,
        )

        repr_str = repr(instance)
        assert (
            repr_str
            == "FileInstance(id=disabled-test, type=gitignore, path=.gitignore, disabled)"
        )

    def test_get_component_name_from_variables(self):
        """Test get_component_name() extracts from variables dict (Priority 1)."""
        instance = FileInstanceFactory(
            id="test-instance", variables={"component_name": "my-custom-component"}
        )

        assert instance.get_component_name() == "my-custom-component"  # type: ignore[attr-defined]

    def test_get_component_name_from_preset(self):
        """Test get_component_name() extracts from preset field (Priority 2)."""
        instance = FileInstanceFactory(
            id="test-instance",
            type=FileType.COMMANDS,
            preset="commands:backend-focused",
            path=".claude/commands/",
        )

        # No component_name in variables, should extract from preset
        assert instance.get_component_name() == "backend-focused"  # type: ignore[attr-defined]

    def test_get_component_name_empty(self):
        """Test get_component_name() returns empty string when not found (Priority 3)."""
        instance = FileInstanceFactory(
            id="test-instance",
            type=FileType.SETTINGS_JSON,
            preset="no_colon_preset",  # No colon separator
            path=".claude/settings.json",
        )

        # No component_name in variables, no colon in preset
        assert instance.get_component_name() == ""  # type: ignore[attr-defined]

    def test_get_component_name_priority(self):
        """Test get_component_name() prioritizes variables over preset."""
        instance = FileInstanceFactory(
            id="test-instance", variables={"component_name": "from-variables"}
        )

        # Should prefer variables over preset extraction
        assert instance.get_component_name() == "from-variables"  # type: ignore[attr-defined]


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_valid(self):
        """Test creating a valid ValidationResult."""
        result = ValidationResult(valid=True)

        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []
        assert not result.has_errors
        assert not result.has_warnings

    def test_validation_result_invalid(self):
        """Test creating an invalid ValidationResult."""
        result = ValidationResult(valid=False)

        assert result.valid is False
        assert result.errors == []
        assert result.warnings == []

    def test_add_error(self):
        """Test adding errors to ValidationResult."""
        result = ValidationResult(valid=True)
        assert result.valid is True

        result.add_error("First error")
        assert result.valid is False  # Should change to False
        assert result.has_errors
        assert result.errors == ["First error"]

        result.add_error("Second error")
        assert result.valid is False
        assert result.errors == ["First error", "Second error"]

    def test_add_warning(self):
        """Test adding warnings to ValidationResult."""
        result = ValidationResult(valid=True)

        result.add_warning("First warning")
        assert result.valid is True  # Should stay True
        assert result.has_warnings
        assert result.warnings == ["First warning"]

        result.add_warning("Second warning")
        assert result.valid is True
        assert result.warnings == ["First warning", "Second warning"]

    def test_errors_and_warnings_together(self):
        """Test ValidationResult with both errors and warnings."""
        result = ValidationResult(valid=True)

        result.add_warning("Warning message")
        assert result.valid is True

        result.add_error("Error message")
        assert result.valid is False

        result.add_warning("Another warning")
        assert result.valid is False  # Errors make it invalid

        assert result.has_errors
        assert result.has_warnings
        assert result.errors == ["Error message"]
        assert result.warnings == ["Warning message", "Another warning"]

    def test_validation_result_repr_valid(self):
        """Test ValidationResult string representation when valid."""
        result = ValidationResult(valid=True)
        assert repr(result) == "ValidationResult(valid=True)"

    def test_validation_result_repr_invalid(self):
        """Test ValidationResult string representation when invalid."""
        result = ValidationResult(valid=False)
        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_warning("Warning 1")

        repr_str = repr(result)
        assert repr_str == "ValidationResult(valid=False, errors=2, warnings=1)"

    def test_validation_result_repr_no_errors_but_warnings(self):
        """Test ValidationResult repr with only warnings."""
        result = ValidationResult(valid=True)
        result.add_warning("Warning")

        # Still shows counts even if valid
        repr_str = repr(result)
        # Valid=True so uses simple repr
        assert repr_str == "ValidationResult(valid=True)"

    def test_has_errors_property(self):
        """Test has_errors property."""
        result = ValidationResult(valid=True)
        assert not result.has_errors

        result.add_error("Error")
        assert result.has_errors

    def test_has_warnings_property(self):
        """Test has_warnings property."""
        result = ValidationResult(valid=True)
        assert not result.has_warnings

        result.add_warning("Warning")
        assert result.has_warnings

    def test_multiple_operations(self):
        """Test multiple validation operations."""
        result = ValidationResult(valid=True)

        # Add some warnings (valid stays True)
        result.add_warning("Path exists")
        result.add_warning("File will be overwritten")
        assert result.valid is True
        assert len(result.warnings) == 2

        # Add an error (valid becomes False)
        result.add_error("Invalid path format")
        assert result.valid is False
        assert len(result.errors) == 1

        # Add more errors
        result.add_error("Preset not found")
        result.add_error("Path outside repository")
        assert result.valid is False
        assert len(result.errors) == 3

        # Verify final state
        assert result.has_errors
        assert result.has_warnings
        assert result.errors == [
            "Invalid path format",
            "Preset not found",
            "Path outside repository",
        ]
        assert result.warnings == ["Path exists", "File will be overwritten"]


class TestDiscoveredComponent:
    """Tests for DiscoveredComponent dataclass."""

    def test_discovered_component_creation(self, tmp_path):
        """Test creating a DiscoveredComponent with valid data."""
        from claudefig.models import DiscoveredComponent

        file_path = tmp_path / "CLAUDE.md"
        file_path.write_text("# Test")

        component = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=file_path,
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
            is_duplicate=False,
            duplicate_paths=[],
        )

        assert component.name == "CLAUDE"
        assert component.type == FileType.CLAUDE_MD
        assert component.path == file_path
        assert component.relative_path == Path("CLAUDE.md")
        assert component.parent_folder == "."
        assert not component.is_duplicate
        assert component.duplicate_paths == []

    def test_discovered_component_empty_name_raises(self, tmp_path):
        """Test that empty name raises ValueError."""
        from claudefig.models import DiscoveredComponent

        file_path = tmp_path / "CLAUDE.md"
        file_path.write_text("# Test")

        with pytest.raises(ValueError, match="cannot be empty"):
            DiscoveredComponent(
                name="",
                type=FileType.CLAUDE_MD,
                path=file_path,
                relative_path=Path("CLAUDE.md"),
                parent_folder=".",
            )

    def test_discovered_component_whitespace_name_raises(self, tmp_path):
        """Test that whitespace-only name raises ValueError."""
        from claudefig.models import DiscoveredComponent

        file_path = tmp_path / "CLAUDE.md"
        file_path.write_text("# Test")

        with pytest.raises(ValueError, match="cannot be empty"):
            DiscoveredComponent(
                name="   ",
                type=FileType.CLAUDE_MD,
                path=file_path,
                relative_path=Path("CLAUDE.md"),
                parent_folder=".",
            )

    def test_discovered_component_relative_path_raises(self, tmp_path):
        """Test that non-absolute path raises ValueError."""
        from claudefig.models import DiscoveredComponent

        with pytest.raises(ValueError, match="must be absolute"):
            DiscoveredComponent(
                name="CLAUDE",
                type=FileType.CLAUDE_MD,
                path=Path("relative/path/CLAUDE.md"),  # Not absolute
                relative_path=Path("CLAUDE.md"),
                parent_folder=".",
            )

    def test_discovered_component_absolute_relative_raises(self, tmp_path):
        """Test that absolute relative_path raises ValueError."""
        from claudefig.models import DiscoveredComponent

        file_path = tmp_path / "CLAUDE.md"
        file_path.write_text("# Test")

        with pytest.raises(ValueError, match="must be relative"):
            DiscoveredComponent(
                name="CLAUDE",
                type=FileType.CLAUDE_MD,
                path=file_path,
                relative_path=file_path,  # Absolute, should be relative
                parent_folder=".",
            )

    def test_discovered_component_repr(self, tmp_path):
        """Test DiscoveredComponent string representation."""
        from claudefig.models import DiscoveredComponent

        file_path = tmp_path / "CLAUDE.md"
        file_path.write_text("# Test")

        component = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=file_path,
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
        )

        repr_str = repr(component)
        assert "DiscoveredComponent" in repr_str
        assert "name=CLAUDE" in repr_str
        assert "type=claude_md" in repr_str
        assert "path=CLAUDE.md" in repr_str
        assert "(duplicate)" not in repr_str

    def test_discovered_component_repr_with_duplicate(self, tmp_path):
        """Test DiscoveredComponent repr includes duplicate indicator."""
        from claudefig.models import DiscoveredComponent

        file_path = tmp_path / "CLAUDE.md"
        file_path.write_text("# Test")

        component = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=file_path,
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
            is_duplicate=True,
            duplicate_paths=[tmp_path / "other" / "CLAUDE.md"],
        )

        repr_str = repr(component)
        assert "(duplicate)" in repr_str

    def test_discovered_component_with_all_types(self, tmp_path):
        """Test DiscoveredComponent creation with various FileTypes."""
        from claudefig.models import DiscoveredComponent

        test_cases = [
            (FileType.CLAUDE_MD, "CLAUDE.md"),
            (FileType.GITIGNORE, ".gitignore"),
            (FileType.COMMANDS, "test-cmd.md"),
            (FileType.AGENTS, "helper.md"),
            (FileType.HOOKS, "pre-commit.py"),
            (FileType.SETTINGS_JSON, "settings.json"),
            (FileType.MCP, "filesystem.json"),
        ]

        for file_type, filename in test_cases:
            file_path = tmp_path / filename
            file_path.write_text("content")

            component = DiscoveredComponent(
                name=f"test-{file_type.value}",
                type=file_type,
                path=file_path,
                relative_path=Path(filename),
                parent_folder=".",
            )

            assert component.type == file_type


class TestComponentDiscoveryResult:
    """Tests for ComponentDiscoveryResult dataclass."""

    def test_discovery_result_creation(self):
        """Test creating ComponentDiscoveryResult with basic data."""
        from claudefig.models import ComponentDiscoveryResult

        result = ComponentDiscoveryResult(
            components=[],
            total_found=0,
            warnings=[],
            scan_time_ms=10.5,
        )

        assert result.components == []
        assert result.total_found == 0
        assert result.warnings == []
        assert result.scan_time_ms == 10.5

    def test_discovery_result_has_warnings_true(self):
        """Test has_warnings returns True when warnings exist."""
        from claudefig.models import ComponentDiscoveryResult

        result = ComponentDiscoveryResult(
            components=[],
            total_found=0,
            warnings=["Duplicate name found"],
            scan_time_ms=5.0,
        )

        assert result.has_warnings is True

    def test_discovery_result_has_warnings_false(self):
        """Test has_warnings returns False when no warnings."""
        from claudefig.models import ComponentDiscoveryResult

        result = ComponentDiscoveryResult(
            components=[],
            total_found=0,
            warnings=[],
            scan_time_ms=5.0,
        )

        assert result.has_warnings is False

    def test_discovery_result_get_by_type(self, tmp_path):
        """Test get_components_by_type filters correctly."""
        from claudefig.models import ComponentDiscoveryResult, DiscoveredComponent

        # Create test components
        claude_md = DiscoveredComponent(
            name="CLAUDE",
            type=FileType.CLAUDE_MD,
            path=tmp_path / "CLAUDE.md",
            relative_path=Path("CLAUDE.md"),
            parent_folder=".",
        )

        gitignore = DiscoveredComponent(
            name="gitignore",
            type=FileType.GITIGNORE,
            path=tmp_path / ".gitignore",
            relative_path=Path(".gitignore"),
            parent_folder=".",
        )

        command = DiscoveredComponent(
            name="test-cmd",
            type=FileType.COMMANDS,
            path=tmp_path / ".claude" / "commands" / "test-cmd.md",
            relative_path=Path(".claude/commands/test-cmd.md"),
            parent_folder="commands",
        )

        # Create files for validation
        (tmp_path / "CLAUDE.md").write_text("# Claude")
        (tmp_path / ".gitignore").write_text("*.pyc")
        cmd_dir = tmp_path / ".claude" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "test-cmd.md").write_text("# Command")

        result = ComponentDiscoveryResult(
            components=[claude_md, gitignore, command],
            total_found=3,
            warnings=[],
            scan_time_ms=15.0,
        )

        # Test filtering
        claude_comps = result.get_components_by_type(FileType.CLAUDE_MD)
        assert len(claude_comps) == 1
        assert claude_comps[0].name == "CLAUDE"

        gitignore_comps = result.get_components_by_type(FileType.GITIGNORE)
        assert len(gitignore_comps) == 1
        assert gitignore_comps[0].name == "gitignore"

        command_comps = result.get_components_by_type(FileType.COMMANDS)
        assert len(command_comps) == 1
        assert command_comps[0].name == "test-cmd"

        # Type with no components
        agent_comps = result.get_components_by_type(FileType.AGENTS)
        assert len(agent_comps) == 0

    def test_discovery_result_repr(self):
        """Test ComponentDiscoveryResult string representation."""
        from claudefig.models import ComponentDiscoveryResult

        result = ComponentDiscoveryResult(
            components=[],
            total_found=5,
            warnings=["Warning 1", "Warning 2"],
            scan_time_ms=25.3,
        )

        repr_str = repr(result)
        assert "ComponentDiscoveryResult" in repr_str
        assert "found=5" in repr_str
        assert "warnings=2" in repr_str
        assert "time=25.3ms" in repr_str

    def test_discovery_result_defaults(self):
        """Test ComponentDiscoveryResult default values."""
        from claudefig.models import ComponentDiscoveryResult

        result = ComponentDiscoveryResult(
            components=[],
            total_found=0,
        )

        assert result.warnings == []
        assert result.scan_time_ms == 0.0
