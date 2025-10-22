"""Tests for FileInstanceManager."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from claudefig.file_instance_manager import FileInstanceManager
from claudefig.models import (
    FileInstance,
    FileType,
    Preset,
    PresetSource,
)


@pytest.fixture
def mock_preset_manager():
    """Create a mock PresetManager with common presets."""
    manager = Mock()

    # Create mock presets
    mock_presets = {
        "claude_md:default": Preset(
            id="claude_md:default",
            type=FileType.CLAUDE_MD,
            name="Default",
            description="Default CLAUDE.md",
            source=PresetSource.BUILT_IN,
        ),
        "settings_json:default": Preset(
            id="settings_json:default",
            type=FileType.SETTINGS_JSON,
            name="Default",
            description="Default settings",
            source=PresetSource.BUILT_IN,
        ),
        "gitignore:standard": Preset(
            id="gitignore:standard",
            type=FileType.GITIGNORE,
            name="Standard",
            description="Standard gitignore",
            source=PresetSource.BUILT_IN,
        ),
        "commands:default": Preset(
            id="commands:default",
            type=FileType.COMMANDS,
            name="Default",
            description="Default commands",
            source=PresetSource.BUILT_IN,
        ),
        "statusline:default": Preset(
            id="statusline:default",
            type=FileType.STATUSLINE,
            name="Default",
            description="Default statusline",
            source=PresetSource.BUILT_IN,
        ),
    }

    # Mock get_preset to return the appropriate preset
    manager.get_preset.side_effect = lambda preset_id: mock_presets.get(preset_id)

    return manager


@pytest.fixture
def instance_manager(mock_preset_manager, tmp_path):
    """Create a FileInstanceManager with mocked dependencies."""
    return FileInstanceManager(preset_manager=mock_preset_manager, repo_path=tmp_path)


@pytest.fixture
def sample_instance():
    """Create a sample FileInstance for testing."""
    return FileInstance(
        id="test-claude-md",
        type=FileType.CLAUDE_MD,
        preset="claude_md:default",
        path="CLAUDE.md",
        enabled=True,
        variables={},
    )


class TestFileInstanceManagerInit:
    """Tests for FileInstanceManager.__init__ method."""

    def test_init_with_all_parameters(self, mock_preset_manager, tmp_path):
        """Test initialization with all parameters provided."""
        manager = FileInstanceManager(
            preset_manager=mock_preset_manager, repo_path=tmp_path
        )

        assert manager.preset_manager is mock_preset_manager
        assert manager.repo_path == tmp_path
        assert manager._instances == {}

    def test_init_with_default_preset_manager(self, tmp_path):
        """Test initialization creates PresetManager if not provided."""
        manager = FileInstanceManager(repo_path=tmp_path)

        assert manager.preset_manager is not None
        assert manager.repo_path == tmp_path

    def test_init_with_default_repo_path(self, mock_preset_manager):
        """Test initialization uses current directory if no path provided."""
        manager = FileInstanceManager(preset_manager=mock_preset_manager)

        assert manager.preset_manager is mock_preset_manager
        assert manager.repo_path == Path.cwd()


class TestAddInstance:
    """Tests for add_instance method."""

    def test_add_valid_instance(self, instance_manager, sample_instance):
        """Test adding a valid instance."""
        result = instance_manager.add_instance(sample_instance)

        assert result.valid is True
        assert not result.has_errors
        assert sample_instance.id in instance_manager._instances

    def test_add_instance_with_warnings(self, instance_manager, tmp_path):
        """Test adding instance that generates warnings."""
        # Create a file that already exists
        test_file = tmp_path / "existing.md"
        test_file.write_text("existing content", encoding="utf-8")

        instance = FileInstance(
            id="test-existing",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="existing.md",
            enabled=True,
        )

        result = instance_manager.add_instance(instance)

        # Should succeed but with warnings
        assert result.valid is True
        assert result.has_warnings
        assert any("already exists" in w for w in result.warnings)

    def test_add_duplicate_instance_id(self, instance_manager, sample_instance):
        """Test adding instance with duplicate ID."""
        # Add first instance
        instance_manager.add_instance(sample_instance)

        # Try to add same instance again
        duplicate = FileInstance(
            id=sample_instance.id,
            type=FileType.SETTINGS_JSON,
            preset="settings_json:default",
            path=".claude/settings.json",
        )

        result = instance_manager.add_instance(duplicate)

        assert result.valid is False
        assert result.has_errors
        assert any("already exists" in e for e in result.errors)

    def test_add_instance_with_nonexistent_preset(self, instance_manager):
        """Test adding instance with preset that doesn't exist."""
        instance = FileInstance(
            id="test-invalid-preset",
            type=FileType.CLAUDE_MD,
            preset="claude_md:nonexistent",
            path="CLAUDE.md",
        )

        result = instance_manager.add_instance(instance)

        assert result.valid is False
        assert result.has_errors
        assert any("not found" in e for e in result.errors)

    def test_add_instance_with_mismatched_preset_type(self, instance_manager):
        """Test adding instance where preset type doesn't match instance type."""
        # Using a CLAUDE_MD preset for a SETTINGS_JSON instance
        instance = FileInstance(
            id="test-type-mismatch",
            type=FileType.SETTINGS_JSON,
            preset="claude_md:default",  # Wrong type!
            path=".claude/settings.json",
        )

        result = instance_manager.add_instance(instance)

        assert result.valid is False
        assert result.has_errors
        assert any("mismatch" in e.lower() for e in result.errors)

    def test_add_second_single_instance_type(self, instance_manager):
        """Test adding second instance of type that doesn't support multiple."""
        # Add first statusline instance
        first = FileInstance(
            id="statusline-1",
            type=FileType.STATUSLINE,
            preset="statusline:default",
            path=".claude/statusline.sh",
            enabled=True,
        )
        instance_manager.add_instance(first)

        # Try to add second statusline instance
        second = FileInstance(
            id="statusline-2",
            type=FileType.STATUSLINE,
            preset="statusline:default",
            path=".claude/custom-statusline.sh",
            enabled=True,
        )

        result = instance_manager.add_instance(second)

        assert result.valid is False
        assert result.has_errors
        assert any("does not support multiple" in e for e in result.errors)


class TestUpdateInstance:
    """Tests for update_instance method."""

    def test_update_existing_instance(self, instance_manager, sample_instance):
        """Test updating an existing instance."""
        # Add instance first
        instance_manager.add_instance(sample_instance)

        # Update it
        sample_instance.enabled = False
        sample_instance.variables = {"updated": True}

        result = instance_manager.update_instance(sample_instance)

        assert result.valid is True
        updated = instance_manager.get_instance(sample_instance.id)
        assert updated.enabled is False
        assert updated.variables == {"updated": True}

    def test_update_nonexistent_instance(self, instance_manager, sample_instance):
        """Test updating instance that doesn't exist."""
        result = instance_manager.update_instance(sample_instance)

        assert result.valid is False
        assert result.has_errors
        assert any("not found" in e for e in result.errors)

    def test_update_with_invalid_data(self, instance_manager, sample_instance):
        """Test updating instance with invalid preset."""
        # Add instance first
        instance_manager.add_instance(sample_instance)

        # Change to invalid preset
        sample_instance.preset = "nonexistent:preset"

        result = instance_manager.update_instance(sample_instance)

        assert result.valid is False
        assert result.has_errors


class TestRemoveInstance:
    """Tests for remove_instance method."""

    def test_remove_existing_instance(self, instance_manager, sample_instance):
        """Test removing an existing instance."""
        instance_manager.add_instance(sample_instance)

        result = instance_manager.remove_instance(sample_instance.id)

        assert result is True
        assert sample_instance.id not in instance_manager._instances

    def test_remove_nonexistent_instance(self, instance_manager):
        """Test removing instance that doesn't exist."""
        result = instance_manager.remove_instance("nonexistent-id")

        assert result is False


class TestEnableDisableInstance:
    """Tests for enable_instance and disable_instance methods."""

    def test_enable_instance(self, instance_manager, sample_instance):
        """Test enabling an instance."""
        sample_instance.enabled = False
        instance_manager.add_instance(sample_instance)

        result = instance_manager.enable_instance(sample_instance.id)

        assert result is True
        assert instance_manager.get_instance(sample_instance.id).enabled is True

    def test_disable_instance(self, instance_manager, sample_instance):
        """Test disabling an instance."""
        instance_manager.add_instance(sample_instance)

        result = instance_manager.disable_instance(sample_instance.id)

        assert result is True
        assert instance_manager.get_instance(sample_instance.id).enabled is False

    def test_enable_nonexistent_instance(self, instance_manager):
        """Test enabling instance that doesn't exist."""
        result = instance_manager.enable_instance("nonexistent-id")

        assert result is False

    def test_disable_nonexistent_instance(self, instance_manager):
        """Test disabling instance that doesn't exist."""
        result = instance_manager.disable_instance("nonexistent-id")

        assert result is False


class TestListInstances:
    """Tests for list_instances method."""

    def test_list_all_instances(self, instance_manager):
        """Test listing all instances."""
        # Add multiple instances
        instances = [
            FileInstance(
                id="claude-md",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
            ),
            FileInstance(
                id="gitignore",
                type=FileType.GITIGNORE,
                preset="gitignore:standard",
                path=".gitignore",
            ),
            FileInstance(
                id="settings",
                type=FileType.SETTINGS_JSON,
                preset="settings_json:default",
                path=".claude/settings.json",
            ),
        ]

        for instance in instances:
            instance_manager.add_instance(instance)

        result = instance_manager.list_instances()

        assert len(result) == 3
        # Should be sorted by file type, then path
        assert result[0].type == FileType.CLAUDE_MD
        assert result[1].type == FileType.GITIGNORE
        assert result[2].type == FileType.SETTINGS_JSON

    def test_list_instances_by_type(self, instance_manager):
        """Test filtering instances by file type."""
        # Add instances of different types
        claude_md = FileInstance(
            id="claude-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )
        gitignore = FileInstance(
            id="gitignore",
            type=FileType.GITIGNORE,
            preset="gitignore:standard",
            path=".gitignore",
        )

        instance_manager.add_instance(claude_md)
        instance_manager.add_instance(gitignore)

        result = instance_manager.list_instances(file_type=FileType.CLAUDE_MD)

        assert len(result) == 1
        assert result[0].type == FileType.CLAUDE_MD

    def test_list_instances_enabled_only(self, instance_manager):
        """Test filtering instances by enabled status."""
        enabled = FileInstance(
            id="enabled",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )
        disabled = FileInstance(
            id="disabled",
            type=FileType.GITIGNORE,
            preset="gitignore:standard",
            path=".gitignore",
            enabled=False,
        )

        instance_manager.add_instance(enabled)
        instance_manager.add_instance(disabled)

        result = instance_manager.list_instances(enabled_only=True)

        assert len(result) == 1
        assert result[0].enabled is True

    def test_list_instances_combined_filters(self, instance_manager):
        """Test using multiple filters together."""
        instances = [
            FileInstance(
                id="claude-enabled",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            FileInstance(
                id="claude-disabled",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="docs/CLAUDE.md",
                enabled=False,
            ),
            FileInstance(
                id="gitignore-enabled",
                type=FileType.GITIGNORE,
                preset="gitignore:standard",
                path=".gitignore",
                enabled=True,
            ),
        ]

        for instance in instances:
            instance_manager.add_instance(instance)

        result = instance_manager.list_instances(
            file_type=FileType.CLAUDE_MD, enabled_only=True
        )

        assert len(result) == 1
        assert result[0].id == "claude-enabled"


class TestValidatePath:
    """Tests for validate_path method."""

    def test_validate_valid_relative_path(self, instance_manager):
        """Test validating a valid relative path."""
        result = instance_manager.validate_path("CLAUDE.md", FileType.CLAUDE_MD)

        assert result.valid is True
        assert not result.has_errors

    def test_validate_absolute_path(self, instance_manager):
        """Test that absolute paths are rejected."""
        # Use proper absolute path for Windows
        import platform

        if platform.system() == "Windows":
            abs_path = "C:\\absolute\\path.md"
        else:
            abs_path = "/absolute/path.md"

        result = instance_manager.validate_path(abs_path, FileType.CLAUDE_MD)

        assert result.valid is False
        assert result.has_errors
        assert any("must be relative" in e for e in result.errors)

    def test_validate_path_with_parent_references(self, instance_manager):
        """Test that paths with ../ are rejected."""
        result = instance_manager.validate_path(
            "../outside/CLAUDE.md", FileType.CLAUDE_MD
        )

        assert result.valid is False
        assert result.has_errors
        assert any("cannot contain parent" in e for e in result.errors)

    def test_validate_empty_path(self, instance_manager):
        """Test that empty path is rejected."""
        result = instance_manager.validate_path("", FileType.CLAUDE_MD)

        assert result.valid is False
        assert result.has_errors
        assert any("cannot be empty" in e for e in result.errors)

    def test_validate_directory_without_trailing_slash(self, instance_manager):
        """Test that directory paths should end with /."""
        result = instance_manager.validate_path(".claude/commands", FileType.COMMANDS)

        assert result.valid is True
        assert result.has_warnings
        assert any("should end with '/'" in w for w in result.warnings)

    def test_validate_directory_with_trailing_slash(self, instance_manager):
        """Test that directory paths with / are valid."""
        result = instance_manager.validate_path(".claude/commands/", FileType.COMMANDS)

        assert result.valid is True
        assert not result.has_warnings

    def test_validate_existing_file_warning(self, instance_manager, tmp_path):
        """Test that existing files generate warning."""
        # Create a file
        test_file = tmp_path / "existing.md"
        test_file.write_text("content", encoding="utf-8")

        result = instance_manager.validate_path("existing.md", FileType.CLAUDE_MD)

        assert result.valid is True
        assert result.has_warnings
        assert any("already exists" in w for w in result.warnings)

    def test_validate_existing_file_append_mode(self, instance_manager, tmp_path):
        """Test that existing files don't warn in append mode."""
        # Create a file
        test_file = tmp_path / ".gitignore"
        test_file.write_text("content", encoding="utf-8")

        # GITIGNORE has append_mode=True
        result = instance_manager.validate_path(".gitignore", FileType.GITIGNORE)

        # Should be valid without warnings about overwriting
        assert result.valid is True
        # May have other warnings but not about overwriting


class TestValidateInstance:
    """Tests for validate_instance method."""

    def test_validate_instance_path_errors(self, instance_manager):
        """Test validation when path validation returns errors."""
        # Create instance with path containing parent references
        instance = FileInstance(
            id="test-invalid-path",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="../../../etc/passwd",  # Parent references not allowed
            enabled=True,
        )

        # Execute
        result = instance_manager.validate_instance(instance)

        # Verify - should have errors from path validation
        assert not result.valid
        assert result.has_errors
        # Error message should mention parent directory or similar
        assert len(result.errors) > 0

    def test_validate_instance_path_conflict_warning(self, instance_manager):
        """Test path conflict detection between instances."""
        # Add first instance
        instance1 = FileInstance(
            id="first-instance",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )
        instance_manager.add_instance(instance1)

        # Create second instance with same path
        instance2 = FileInstance(
            id="second-instance",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",  # Same path
            enabled=True,
        )

        # Execute
        result = instance_manager.validate_instance(instance2)

        # Verify - should have warning about path conflict
        assert result.has_warnings
        assert any("already used" in warn for warn in result.warnings)
        assert any("first-instance" in warn for warn in result.warnings)

    def test_validate_instance_preset_type_mismatch(self, instance_manager):
        """Test validation when preset type doesn't match instance type."""
        # Create instance with mismatched preset type
        # preset is for SETTINGS_JSON but instance is CLAUDE_MD
        instance = FileInstance(
            id="test-mismatch",
            type=FileType.CLAUDE_MD,
            preset="settings_json:default",  # Wrong type!
            path="CLAUDE.md",
            enabled=True,
        )

        # Execute
        result = instance_manager.validate_instance(instance)

        # Verify - should have error about type mismatch
        assert not result.valid
        assert result.has_errors
        assert any("type mismatch" in err.lower() for err in result.errors)

    def test_validate_instance_duplicate_id_error(self, instance_manager):
        """Test validation rejects duplicate instance IDs."""
        # Add first instance
        instance1 = FileInstance(
            id="duplicate-id",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )
        instance_manager.add_instance(instance1)

        # Try to add second instance with same ID
        instance2 = FileInstance(
            id="duplicate-id",  # Duplicate!
            type=FileType.GITIGNORE,
            preset="gitignore:standard",
            path=".gitignore",
        )

        # Execute
        result = instance_manager.validate_instance(instance2, is_update=False)

        # Verify - should have error about duplicate ID
        assert not result.valid
        assert result.has_errors
        assert any("already exists" in err for err in result.errors)


class TestGenerateInstanceId:
    """Tests for generate_instance_id method."""

    def test_generate_basic_id(self, instance_manager):
        """Test generating a basic instance ID."""
        instance_id = instance_manager.generate_instance_id(
            FileType.CLAUDE_MD, "default"
        )

        assert instance_id == "claude_md-default"

    def test_generate_id_with_non_default_path(self, instance_manager):
        """Test generating ID with custom path."""
        instance_id = instance_manager.generate_instance_id(
            FileType.CLAUDE_MD, "default", "docs/CLAUDE.md"
        )

        # Should include path component for uniqueness
        assert "claude_md-default" in instance_id
        assert "docs" in instance_id

    def test_generate_unique_ids_for_duplicates(self, instance_manager):
        """Test that duplicate IDs get incremented counter."""
        # Add an instance
        instance = FileInstance(
            id="claude_md-default",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )
        instance_manager.add_instance(instance)

        # Generate ID for same type/preset
        new_id = instance_manager.generate_instance_id(FileType.CLAUDE_MD, "default")

        # Should have counter appended
        assert new_id == "claude_md-default-1"

    def test_generate_multiple_unique_ids(self, instance_manager):
        """Test generating multiple unique IDs."""
        # Add two instances
        instance1 = FileInstance(
            id="claude_md-default",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )
        instance2 = FileInstance(
            id="claude_md-default-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="docs/CLAUDE.md",
        )
        instance_manager.add_instance(instance1)
        instance_manager.add_instance(instance2)

        # Generate ID for same type/preset
        new_id = instance_manager.generate_instance_id(FileType.CLAUDE_MD, "default")

        # Should increment to next available
        assert new_id == "claude_md-default-2"


class TestLoadSaveInstances:
    """Tests for load_instances and save_instances methods."""

    def test_load_instances_from_dicts(self, instance_manager):
        """Test loading instances from dict data."""
        instances_data = [
            {
                "id": "claude-md",
                "type": "claude_md",
                "preset": "claude_md:default",
                "path": "CLAUDE.md",
                "enabled": True,
                "variables": {},
            },
            {
                "id": "gitignore",
                "type": "gitignore",
                "preset": "gitignore:standard",
                "path": ".gitignore",
                "enabled": False,
                "variables": {"python": True},
            },
        ]

        instance_manager.load_instances(instances_data)

        assert len(instance_manager._instances) == 2
        assert "claude-md" in instance_manager._instances
        assert "gitignore" in instance_manager._instances
        assert instance_manager._instances["gitignore"].enabled is False
        assert instance_manager._instances["gitignore"].variables == {"python": True}

    def test_load_instances_clears_existing(self, instance_manager, sample_instance):
        """Test that loading instances clears existing ones."""
        # Add an instance
        instance_manager.add_instance(sample_instance)

        # Load new instances
        instance_manager.load_instances([])

        # Should be empty now
        assert len(instance_manager._instances) == 0

    def test_load_instances_with_invalid_data(self, instance_manager):
        """Test loading instances with invalid data tracks errors."""
        instances_data = [
            {
                "id": "valid",
                "type": "claude_md",
                "preset": "claude_md:default",
                "path": "CLAUDE.md",
            },
            {
                # Missing required fields
                "id": "invalid",
            },
        ]

        instance_manager.load_instances(instances_data)

        # Valid instance should be loaded
        assert "valid" in instance_manager._instances
        # Invalid instance should be skipped
        assert "invalid" not in instance_manager._instances

        # Should have tracked error
        errors = instance_manager.get_load_errors()
        assert len(errors) > 0
        assert any("invalid" in e.lower() for e in errors)

    def test_save_instances_to_dicts(self, instance_manager):
        """Test saving instances to dict format."""
        # Add some instances
        instances = [
            FileInstance(
                id="claude-md",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
                variables={"version": "1.0"},
            ),
            FileInstance(
                id="settings",
                type=FileType.SETTINGS_JSON,
                preset="settings_json:default",
                path=".claude/settings.json",
                enabled=False,
            ),
        ]

        for instance in instances:
            instance_manager.add_instance(instance)

        saved = instance_manager.save_instances()

        assert len(saved) == 2
        assert all(isinstance(d, dict) for d in saved)
        # Check specific fields
        claude_md_dict = next(d for d in saved if d["id"] == "claude-md")
        assert claude_md_dict["type"] == "claude_md"
        assert claude_md_dict["enabled"] is True
        assert claude_md_dict["variables"] == {"version": "1.0"}

    def test_load_save_roundtrip(self, instance_manager):
        """Test that save -> load preserves data."""
        # Add instances
        instances = [
            FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
                variables={"test": "value"},
            ),
            FileInstance(
                id="test-2",
                type=FileType.GITIGNORE,
                preset="gitignore:standard",
                path=".gitignore",
                enabled=False,
            ),
        ]

        for instance in instances:
            instance_manager.add_instance(instance)

        # Save and load
        saved = instance_manager.save_instances()
        instance_manager.load_instances(saved)

        # Verify data preserved
        assert len(instance_manager._instances) == 2
        test1 = instance_manager.get_instance("test-1")
        assert test1.enabled is True
        assert test1.variables == {"test": "value"}


class TestCountByType:
    """Tests for count_by_type method."""

    def test_count_empty(self, instance_manager):
        """Test counting with no instances."""
        counts = instance_manager.count_by_type()

        assert counts == {}

    def test_count_multiple_types(self, instance_manager):
        """Test counting instances of different types."""
        instances = [
            FileInstance(
                id="claude-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            FileInstance(
                id="claude-2",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="docs/CLAUDE.md",
                enabled=True,
            ),
            FileInstance(
                id="gitignore",
                type=FileType.GITIGNORE,
                preset="gitignore:standard",
                path=".gitignore",
                enabled=True,
            ),
        ]

        for instance in instances:
            instance_manager.add_instance(instance)

        counts = instance_manager.count_by_type()

        assert counts[FileType.CLAUDE_MD] == 2
        assert counts[FileType.GITIGNORE] == 1

    def test_count_only_enabled(self, instance_manager):
        """Test that count only includes enabled instances."""
        instances = [
            FileInstance(
                id="enabled",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            FileInstance(
                id="disabled",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="docs/CLAUDE.md",
                enabled=False,
            ),
        ]

        for instance in instances:
            instance_manager.add_instance(instance)

        counts = instance_manager.count_by_type()

        # Should only count enabled
        assert counts[FileType.CLAUDE_MD] == 1


class TestGetInstancesByType:
    """Tests for get_instances_by_type method."""

    def test_get_instances_by_type(self, instance_manager):
        """Test retrieving instances by type."""
        instances = [
            FileInstance(
                id="claude-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
            ),
            FileInstance(
                id="claude-2",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="docs/CLAUDE.md",
            ),
            FileInstance(
                id="gitignore",
                type=FileType.GITIGNORE,
                preset="gitignore:standard",
                path=".gitignore",
            ),
        ]

        for instance in instances:
            instance_manager.add_instance(instance)

        result = instance_manager.get_instances_by_type(FileType.CLAUDE_MD)

        assert len(result) == 2
        assert all(i.type == FileType.CLAUDE_MD for i in result)

    def test_get_instances_by_type_empty(self, instance_manager):
        """Test retrieving instances for type with no instances."""
        result = instance_manager.get_instances_by_type(FileType.MCP)

        assert result == []


class TestGetDefaultPath:
    """Tests for get_default_path method."""

    def test_get_default_path(self, instance_manager):
        """Test retrieving default path for file types."""
        assert instance_manager.get_default_path(FileType.CLAUDE_MD) == "CLAUDE.md"
        assert (
            instance_manager.get_default_path(FileType.SETTINGS_JSON)
            == ".claude/settings.json"
        )
        assert (
            instance_manager.get_default_path(FileType.COMMANDS) == ".claude/commands/"
        )


class TestSaveAsComponent:
    """Tests for save_as_component method."""

    def test_save_component_claude_md(self, instance_manager, tmp_path, monkeypatch):
        """Test saving CLAUDE.md component with folder-based storage."""
        import json

        # Mock get_components_dir to use tmp_path instead of ~/.claudefig
        test_components_dir = tmp_path / "test_components"

        def mock_get_components_dir():
            return test_components_dir

        monkeypatch.setattr(
            "claudefig.file_instance_manager.get_components_dir",
            mock_get_components_dir,
        )

        # Create instance
        instance = FileInstance(
            id="test-claude",
            type=FileType.CLAUDE_MD,
            preset="claude_md:backend",
            path="docs/CLAUDE.md",
            enabled=True,
        )

        # Execute
        success, message = instance_manager.save_as_component(instance, "backend-focused")

        # Verify success
        assert success is True, f"Expected success but got: {message}"
        assert "Component saved" in message

        # Verify folder structure was created
        components_dir = test_components_dir
        component_folder = components_dir / "claude_md" / "backend-focused"
        assert component_folder.exists()
        assert component_folder.is_dir()

        # Verify metadata file exists
        metadata_file = component_folder / "component.json"
        assert metadata_file.exists()

        # Verify metadata content
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        assert metadata["type"] == "claude_md"
        assert metadata["path"] == "docs/CLAUDE.md"
        assert metadata["component_name"] == "backend-focused"

        # Verify placeholder file was created
        actual_file = component_folder / "CLAUDE.md"
        assert actual_file.exists()
        content = actual_file.read_text(encoding="utf-8")
        assert "backend-focused" in content

    def test_save_component_gitignore(self, instance_manager, tmp_path, monkeypatch):
        """Test saving .gitignore component with folder-based storage."""
        import json

        # Mock get_components_dir to use tmp_path
        test_components_dir = tmp_path / "test_components"

        def mock_get_components_dir():
            return test_components_dir

        monkeypatch.setattr(
            "claudefig.file_instance_manager.get_components_dir",
            mock_get_components_dir,
        )

        # Create instance
        instance = FileInstance(
            id="test-gitignore",
            type=FileType.GITIGNORE,
            preset="gitignore:python",
            path=".gitignore",
            enabled=True,
        )

        # Execute
        success, message = instance_manager.save_as_component(instance, "python-project")

        # Verify success
        assert success is True

        # Verify folder structure
        components_dir = test_components_dir
        component_folder = components_dir / "gitignore" / "python-project"
        assert component_folder.exists()

        # Verify .gitignore file was created
        gitignore_file = component_folder / ".gitignore"
        assert gitignore_file.exists()

    def test_save_component_already_exists(self, instance_manager, tmp_path, monkeypatch):
        """Test error when component already exists."""
        # Mock get_components_dir to use tmp_path
        test_components_dir = tmp_path / "test_components"

        def mock_get_components_dir():
            return test_components_dir

        monkeypatch.setattr(
            "claudefig.file_instance_manager.get_components_dir",
            mock_get_components_dir,
        )

        # Create and save first component
        instance1 = FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )
        success1, _ = instance_manager.save_as_component(instance1, "existing-component")
        assert success1 is True

        # Try to save another component with same name
        instance2 = FileInstance(
            id="test-2",
            type=FileType.CLAUDE_MD,
            preset="claude_md:other",
            path="other/CLAUDE.md",
        )

        # Execute
        success2, message = instance_manager.save_as_component(
            instance2, "existing-component"
        )

        # Verify failure
        assert success2 is False
        assert "already exists" in message

    def test_save_component_json_storage(self, instance_manager, tmp_path, monkeypatch):
        """Test saving component with JSON storage for non-customizable types."""
        import json

        # Mock get_components_dir to use tmp_path
        test_components_dir = tmp_path / "test_components"

        def mock_get_components_dir():
            return test_components_dir

        monkeypatch.setattr(
            "claudefig.file_instance_manager.get_components_dir",
            mock_get_components_dir,
        )

        # Create instance for non-customizable type (COMMANDS)
        instance = FileInstance(
            id="test-commands",
            type=FileType.COMMANDS,
            preset="commands:default",
            path=".claude/commands/",
            enabled=True,
            variables={"language": "python"},
        )

        # Execute
        success, message = instance_manager.save_as_component(instance, "python-commands")

        # Verify success
        assert success is True

        # Verify JSON file was created
        components_dir = test_components_dir
        component_file = components_dir / "commands" / "python-commands.json"
        assert component_file.exists()

        # Verify JSON content
        data = json.loads(component_file.read_text(encoding="utf-8"))
        assert data["id"] == "test-commands"
        assert data["type"] == "commands"
        assert data["variables"]["language"] == "python"

    def test_save_component_json_already_exists(self, instance_manager, tmp_path, monkeypatch):
        """Test error when JSON component already exists."""
        # Mock get_components_dir to use tmp_path
        test_components_dir = tmp_path / "test_components"

        def mock_get_components_dir():
            return test_components_dir

        monkeypatch.setattr(
            "claudefig.file_instance_manager.get_components_dir",
            mock_get_components_dir,
        )

        # Save first component
        instance1 = FileInstance(
            id="test-1",
            type=FileType.COMMANDS,
            preset="commands:default",
            path=".claude/commands/",
        )
        success1, _ = instance_manager.save_as_component(instance1, "duplicate-json")
        assert success1 is True

        # Try to save duplicate
        instance2 = FileInstance(
            id="test-2",
            type=FileType.COMMANDS,
            preset="commands:other",
            path=".claude/commands/",
        )

        # Execute
        success2, message = instance_manager.save_as_component(instance2, "duplicate-json")

        # Verify failure
        assert success2 is False
        assert "already exists" in message

    def test_save_component_error_handling(self, instance_manager, tmp_path, monkeypatch):
        """Test exception handling in save_component."""
        # Create instance
        instance = FileInstance(
            id="test-error",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )

        # Mock Path.mkdir to raise exception
        original_mkdir = Path.mkdir

        def mock_mkdir(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(Path, "mkdir", mock_mkdir)

        # Execute
        success, message = instance_manager.save_as_component(instance, "error-component")

        # Verify failure
        assert success is False
        assert "Failed" in message or "Error" in message or "error" in message


class TestLoadComponent:
    """Tests for load_component method."""

    def test_load_component_from_folder(self, instance_manager, tmp_path, monkeypatch):
        """Test loading CLAUDE.md component from folder storage."""
        import json

        # Mock get_components_dir to use tmp_path
        test_components_dir = tmp_path / "test_components"

        def mock_get_components_dir():
            return test_components_dir

        monkeypatch.setattr(
            "claudefig.file_instance_manager.get_components_dir",
            mock_get_components_dir,
        )

        # First save a component to load
        instance = FileInstance(
            id="test-save",
            type=FileType.CLAUDE_MD,
            preset="claude_md:backend",
            path="docs/CLAUDE.md",
        )
        instance_manager.save_as_component(instance, "test-load-folder")

        # Execute - load the component
        loaded_instance = instance_manager.load_component(
            FileType.CLAUDE_MD, "test-load-folder"
        )

        # Verify
        assert loaded_instance is not None
        assert loaded_instance.type == FileType.CLAUDE_MD
        assert loaded_instance.path == "docs/CLAUDE.md"
        assert loaded_instance.variables.get("component_name") == "test-load-folder"

    def test_load_component_from_json(self, instance_manager, tmp_path, monkeypatch):
        """Test loading component from JSON storage."""
        # Mock get_components_dir to use tmp_path
        test_components_dir = tmp_path / "test_components"

        def mock_get_components_dir():
            return test_components_dir

        monkeypatch.setattr(
            "claudefig.file_instance_manager.get_components_dir",
            mock_get_components_dir,
        )

        # First save a JSON component
        instance = FileInstance(
            id="test-json-save",
            type=FileType.COMMANDS,
            preset="commands:default",
            path=".claude/commands/",
            variables={"test": "value"},
        )
        instance_manager.save_as_component(instance, "test-load-json")

        # Execute - load the component
        loaded_instance = instance_manager.load_component(
            FileType.COMMANDS, "test-load-json"
        )

        # Verify
        assert loaded_instance is not None
        assert loaded_instance.type == FileType.COMMANDS
        assert loaded_instance.path == ".claude/commands/"
        assert loaded_instance.variables.get("test") == "value"

    def test_load_component_not_found(self, instance_manager, tmp_path, monkeypatch):
        """Test loading component that doesn't exist."""
        # Mock get_components_dir to use tmp_path
        test_components_dir = tmp_path / "test_components"

        def mock_get_components_dir():
            return test_components_dir

        monkeypatch.setattr(
            "claudefig.file_instance_manager.get_components_dir",
            mock_get_components_dir,
        )

        # Execute - try to load non-existent component
        loaded_instance = instance_manager.load_component(
            FileType.CLAUDE_MD, "does-not-exist"
        )

        # Verify
        assert loaded_instance is None
