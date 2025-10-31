"""Tests for file instance service layer."""

from claudefig.models import FileInstance, FileType, PresetSource
from claudefig.repositories.preset_repository import FakePresetRepository
from claudefig.services import file_instance_service
from tests.factories import FileInstanceFactory, PresetFactory


class TestListInstances:
    """Test list_instances() function."""

    def test_lists_all_instances(self):
        """Test listing all instances without filters."""
        instances = FileInstanceFactory.create_dict(
            ("test-1", {}),
            ("test-2", {"type": FileType.GITIGNORE, "enabled": False}),
        )

        result = file_instance_service.list_instances(instances)

        assert len(result) == 2

    def test_filters_by_file_type(self):
        """Test filtering by file type."""
        instances = FileInstanceFactory.create_dict(
            ("test-1", {}),
            ("test-2", {"type": FileType.GITIGNORE}),
        )

        result = file_instance_service.list_instances(
            instances, file_type=FileType.CLAUDE_MD
        )

        assert len(result) == 1
        assert result[0].type == FileType.CLAUDE_MD

    def test_filters_enabled_only(self):
        """Test filtering enabled instances only."""
        instances = FileInstanceFactory.create_dict(
            ("test-1", {}),
            ("test-2", {"type": FileType.GITIGNORE, "enabled": False}),
        )

        result = file_instance_service.list_instances(instances, enabled_only=True)

        assert len(result) == 1
        assert result[0].enabled is True

    def test_sorts_by_type_and_path(self):
        """Test instances are sorted by type then path."""
        instances = FileInstanceFactory.create_dict(
            ("test-1", {"type": FileType.GITIGNORE, "path": "z.txt"}),
            ("test-2", {}),
            ("test-3", {"preset": "claude_md:custom", "path": "DOCS.md"}),
        )

        result = file_instance_service.list_instances(instances)

        # Should be sorted by type, then path
        assert result[0].type == FileType.CLAUDE_MD
        assert result[0].path == "CLAUDE.md"
        assert result[1].type == FileType.CLAUDE_MD
        assert result[1].path == "DOCS.md"
        assert result[2].type == FileType.GITIGNORE


class TestGetInstance:
    """Test get_instance() function."""

    def test_gets_existing_instance(self):
        """Test getting an existing instance."""
        instance = FileInstanceFactory(id="test-1")
        instances: dict[str, FileInstance] = {"test-1": instance}

        result = file_instance_service.get_instance(instances, "test-1")

        assert result is not None
        assert result.id == "test-1"

    def test_returns_none_for_nonexistent_instance(self):
        """Test returns None for non-existent instance."""
        instances: dict[str, FileInstance] = {}

        result = file_instance_service.get_instance(instances, "nonexistent")

        assert result is None


class TestAddInstance:
    """Test add_instance() function."""

    def test_adds_new_instance(self, tmp_path):
        """Test adding a new instance."""
        instances: dict[str, FileInstance] = {}
        preset = PresetFactory(
            id="claude_md:default",
            name="default",
            type=FileType.CLAUDE_MD,
            source=PresetSource.BUILT_IN,
        )
        preset_repo = FakePresetRepository([preset])

        new_instance = FileInstanceFactory(id="test-1")

        result = file_instance_service.add_instance(
            instances, new_instance, preset_repo, tmp_path
        )

        assert result.valid
        assert "test-1" in instances
        assert instances["test-1"] == new_instance

    def test_returns_error_for_duplicate_id(self, tmp_path):
        """Test returns error when adding duplicate ID."""
        existing = FileInstanceFactory(id="test-1")
        instances: dict[str, FileInstance] = {"test-1": existing}

        # Add presets to repository
        preset1 = PresetFactory(
            id="claude_md:default",
            name="default",
            type=FileType.CLAUDE_MD,
            source=PresetSource.BUILT_IN,
        )
        preset2 = PresetFactory(
            id="gitignore:python",
            name="python",
            type=FileType.GITIGNORE,
            source=PresetSource.BUILT_IN,
        )
        preset_repo = FakePresetRepository([preset1, preset2])

        new_instance = FileInstanceFactory.gitignore(id="test-1")

        result = file_instance_service.add_instance(
            instances, new_instance, preset_repo, tmp_path
        )

        assert not result.valid
        assert "already exists" in result.errors[0].lower()


class TestUpdateInstance:
    """Test update_instance() function."""

    def test_updates_existing_instance(self, tmp_path):
        """Test updating an existing instance."""
        instance = FileInstanceFactory(id="test-1")
        instances: dict[str, FileInstance] = {"test-1": instance}

        # Add presets to repository
        preset1 = PresetFactory(
            id="claude_md:default",
            name="default",
            type=FileType.CLAUDE_MD,
            source=PresetSource.BUILT_IN,
        )
        preset2 = PresetFactory(
            id="claude_md:custom",
            name="custom",
            type=FileType.CLAUDE_MD,
            source=PresetSource.USER,
        )
        preset_repo = FakePresetRepository([preset1, preset2])

        # Create updated instance
        updated_instance = FileInstanceFactory(
            id="test-1", preset="claude_md:custom", enabled=False
        )

        result = file_instance_service.update_instance(
            instances,
            updated_instance,
            preset_repo,
            tmp_path,
        )

        assert result.valid
        assert instances["test-1"].preset == "claude_md:custom"
        assert instances["test-1"].enabled is False

    def test_returns_error_for_nonexistent_instance(self, tmp_path):
        """Test returns error when updating non-existent instance."""
        instances: dict[str, FileInstance] = {}
        preset_repo = FakePresetRepository()

        nonexistent_instance = FileInstanceFactory(
            id="nonexistent", preset="claude_md:custom"
        )

        result = file_instance_service.update_instance(
            instances,
            nonexistent_instance,
            preset_repo,
            tmp_path,
        )

        assert not result.valid
        assert "not found" in result.errors[0].lower()


class TestRemoveInstance:
    """Test remove_instance() function."""

    def test_removes_existing_instance(self):
        """Test removing an existing instance."""
        instance = FileInstanceFactory(id="test-1")
        instances: dict[str, FileInstance] = {"test-1": instance}

        result = file_instance_service.remove_instance(instances, "test-1")

        assert result is True
        assert "test-1" not in instances

    def test_returns_false_for_nonexistent_instance(self):
        """Test returns False for non-existent instance."""
        instances: dict[str, FileInstance] = {}

        result = file_instance_service.remove_instance(instances, "nonexistent")

        assert result is False


class TestEnableInstance:
    """Test enable_instance() function."""

    def test_enables_disabled_instance(self):
        """Test enabling a disabled instance."""
        instance = FileInstanceFactory.disabled(id="test-1")
        instances: dict[str, FileInstance] = {"test-1": instance}

        result = file_instance_service.enable_instance(instances, "test-1")

        assert result is True
        assert instances["test-1"].enabled is True

    def test_returns_false_for_nonexistent_instance(self):
        """Test returns False for non-existent instance."""
        instances: dict[str, FileInstance] = {}

        result = file_instance_service.enable_instance(instances, "nonexistent")

        assert result is False


class TestDisableInstance:
    """Test disable_instance() function."""

    def test_disables_enabled_instance(self):
        """Test disabling an enabled instance."""
        instance = FileInstanceFactory(id="test-1")
        instances: dict[str, FileInstance] = {"test-1": instance}

        result = file_instance_service.disable_instance(instances, "test-1")

        assert result is True
        assert instances["test-1"].enabled is False

    def test_returns_false_for_nonexistent_instance(self):
        """Test returns False for non-existent instance."""
        instances: dict[str, FileInstance] = {}

        result = file_instance_service.disable_instance(instances, "nonexistent")

        assert result is False


class TestGenerateInstanceId:
    """Test generate_instance_id() function."""

    def test_generates_unique_id(self):
        """Test generating a unique instance ID."""
        instances: dict[str, FileInstance] = {
            "claude_md-default": FileInstanceFactory(id="claude_md-default")
        }

        result = file_instance_service.generate_instance_id(
            FileType.CLAUDE_MD,
            "default",
            None,
            instances,
        )

        assert result != "claude_md-default"
        assert result.startswith("claude_md-default")

    def test_generates_base_id_when_no_conflict(self):
        """Test generates base ID when no conflict exists."""
        instances: dict[str, FileInstance] = {}

        result = file_instance_service.generate_instance_id(
            FileType.CLAUDE_MD,
            "custom",
            None,
            instances,
        )

        assert result == "claude_md-custom"


class TestGetDefaultPath:
    """Test get_default_path() function."""

    def test_returns_default_path_for_file_type(self):
        """Test returns default path for each file type."""
        result = file_instance_service.get_default_path(FileType.CLAUDE_MD)

        assert result == FileType.CLAUDE_MD.default_path


class TestCountByType:
    """Test count_by_type() function."""

    def test_counts_instances_by_type(self):
        """Test counting instances by file type."""
        instances = FileInstanceFactory.create_dict(
            ("test-1", {}),
            ("test-2", {"preset": "claude_md:custom", "path": "DOCS.md"}),
            ("test-3", {"type": FileType.GITIGNORE}),
        )

        result = file_instance_service.count_by_type(instances)

        assert result[FileType.CLAUDE_MD] == 2
        assert result[FileType.GITIGNORE] == 1

    def test_returns_empty_dict_for_no_instances(self):
        """Test returns empty dict when no instances."""
        instances: dict[str, FileInstance] = {}

        result = file_instance_service.count_by_type(instances)

        assert result == {}


class TestGetInstancesByType:
    """Test get_instances_by_type() function."""

    def test_returns_instances_of_specified_type(self):
        """Test getting instances by file type."""
        instances = FileInstanceFactory.create_dict(
            ("test-1", {}),
            ("test-2", {"type": FileType.GITIGNORE}),
        )

        result = file_instance_service.get_instances_by_type(
            instances, FileType.CLAUDE_MD
        )

        assert len(result) == 1
        assert result[0].type == FileType.CLAUDE_MD

    def test_returns_empty_list_for_type_with_no_instances(self):
        """Test returns empty list for type with no instances."""
        instances: dict[str, FileInstance] = {
            "test-1": FileInstanceFactory(id="test-1")
        }

        result = file_instance_service.get_instances_by_type(
            instances, FileType.GITIGNORE
        )

        assert result == []


class TestLoadInstancesFromConfig:
    """Test load_instances_from_config() function."""

    def test_loads_valid_instances(self):
        """Test loading valid instances from config data."""
        instances_data = [
            {
                "id": "test-1",
                "type": "claude_md",
                "preset": "claude_md:default",
                "path": "CLAUDE.md",
                "enabled": True,
            },
            {
                "id": "test-2",
                "type": "gitignore",
                "preset": "gitignore:python",
                "path": ".gitignore",
                "enabled": False,
            },
        ]

        instances_dict, errors = file_instance_service.load_instances_from_config(
            instances_data
        )

        assert len(instances_dict) == 2
        assert "test-1" in instances_dict
        assert "test-2" in instances_dict
        assert len(errors) == 0

    def test_skips_invalid_instances_and_returns_errors(self):
        """Test skips invalid instances and returns error messages."""
        instances_data = [
            {
                "id": "test-1",
                "type": "claude_md",
                "preset": "claude_md:default",
                "path": "CLAUDE.md",
                "enabled": True,
            },
            {
                # Missing required field 'type'
                "id": "test-2",
                "preset": "gitignore:python",
                "path": ".gitignore",
                "enabled": False,
            },
        ]

        instances_dict, errors = file_instance_service.load_instances_from_config(
            instances_data
        )

        assert len(instances_dict) == 1
        assert "test-1" in instances_dict
        assert len(errors) == 1
        assert "test-2" in errors[0]

    def test_handles_empty_instances_data(self):
        """Test handles empty instances data."""
        instances_data: list[dict[str, object]] = []

        instances_dict, errors = file_instance_service.load_instances_from_config(
            instances_data
        )

        assert instances_dict == {}
        assert errors == []


class TestSaveInstancesToConfig:
    """Test save_instances_to_config() function."""

    def test_saves_instances_to_config_format(self):
        """Test converting instances dict to config format."""
        instances = FileInstanceFactory.create_dict(
            ("test-1", {}),
            ("test-2", {"type": FileType.GITIGNORE, "enabled": False}),
        )

        result = file_instance_service.save_instances_to_config(instances)

        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)
        assert any(item["id"] == "test-1" for item in result)
        assert any(item["id"] == "test-2" for item in result)

    def test_preserves_instance_properties(self):
        """Test preserves all instance properties."""
        instances: dict[str, FileInstance] = {
            "test-1": FileInstanceFactory(id="test-1", variables={"key": "value"})
        }

        result = file_instance_service.save_instances_to_config(instances)

        assert result[0]["id"] == "test-1"
        assert result[0]["type"] == "claude_md"
        assert result[0]["preset"] == "claude_md:default"
        assert result[0]["path"] == "CLAUDE.md"
        assert result[0]["enabled"] is True
        assert result[0]["variables"] == {"key": "value"}

    def test_handles_empty_instances(self):
        """Test handles empty instances dict."""
        instances: dict[str, FileInstance] = {}

        result = file_instance_service.save_instances_to_config(instances)

        assert result == []


class TestValidateInstanceComponentPresets:
    """Test validate_instance() with component-based presets."""

    def test_component_preset_skips_repository_validation(self, tmp_path):
        """Test that component: prefix skips preset repository validation."""
        # Create instance with component-based preset
        instance = FileInstanceFactory(
            id="test-1",
            type=FileType.SETTINGS_JSON,
            preset="component:default",
            path=".claude/settings.json",
        )

        # Use empty preset repository (component presets shouldn't need it)
        preset_repo = FakePresetRepository([])
        instances: dict[str, FileInstance] = {}

        # Should pass validation even though preset isn't in repository
        result = file_instance_service.validate_instance(
            instance, instances, preset_repo, tmp_path, is_update=False
        )

        assert result.valid
        assert len(result.errors) == 0

    def test_regular_preset_requires_repository_validation(self, tmp_path):
        """Test that regular presets still require repository validation."""
        # Create instance with regular preset
        instance = FileInstanceFactory(id="test-1", preset="claude_md:missing")

        # Use empty preset repository
        preset_repo = FakePresetRepository([])
        instances: dict[str, FileInstance] = {}

        # Should fail validation because preset isn't in repository
        result = file_instance_service.validate_instance(
            instance, instances, preset_repo, tmp_path, is_update=False
        )

        assert not result.valid
        assert any("not found" in error.lower() for error in result.errors)

    def test_add_instance_with_component_preset(self, tmp_path):
        """Test adding instance with component-based preset."""
        instances: dict[str, FileInstance] = {}
        preset_repo = FakePresetRepository([])

        new_instance = FileInstanceFactory(
            id="settings-json-default",
            type=FileType.SETTINGS_JSON,
            preset="component:default",
            path=".claude/settings.json",
            variables={
                "component_folder": "C:/Users/Test/.claudefig/components/settings_json/default",
                "component_name": "default",
            },
        )

        result = file_instance_service.add_instance(
            instances, new_instance, preset_repo, tmp_path
        )

        assert result.valid
        assert "settings-json-default" in instances
        assert instances["settings-json-default"] == new_instance

    def test_update_instance_with_component_preset(self, tmp_path):
        """Test updating instance with component-based preset."""
        # Create existing instance
        existing = FileInstanceFactory(
            id="statusline-default",
            type=FileType.STATUSLINE,
            preset="component:default",
            path=".claude/statusline.sh",
            variables={"component_name": "default"},
        )
        instances: dict[str, FileInstance] = {"statusline-default": existing}
        preset_repo = FakePresetRepository([])

        # Update the instance (change variables, keep enabled=True)
        updated = FileInstanceFactory(
            id="statusline-default",
            type=FileType.STATUSLINE,
            preset="component:default",
            path=".claude/statusline.sh",
            variables={"component_name": "default", "updated": True},
        )

        result = file_instance_service.update_instance(
            instances, updated, preset_repo, tmp_path
        )

        assert result.valid
        assert instances["statusline-default"].variables["updated"] is True

    def test_component_preset_with_custom_name(self, tmp_path):
        """Test component preset with custom component name."""
        instance = FileInstanceFactory(
            id="test-custom",
            preset="component:my-custom-component",
        )

        preset_repo = FakePresetRepository([])
        instances: dict[str, FileInstance] = {}

        result = file_instance_service.validate_instance(
            instance, instances, preset_repo, tmp_path, is_update=False
        )

        assert result.valid
        assert len(result.errors) == 0

    def test_mixed_preset_types_in_instances(self, tmp_path):
        """Test validation works with mix of component and regular presets."""
        # Setup: one component preset, one regular preset
        regular_preset = PresetFactory(
            id="claude_md:default",
            name="default",
            type=FileType.CLAUDE_MD,
            source=PresetSource.BUILT_IN,
        )
        preset_repo = FakePresetRepository([regular_preset])

        # Existing instances
        existing_component = FileInstanceFactory(
            id="settings-1",
            type=FileType.SETTINGS_JSON,
            preset="component:default",
            path=".claude/settings.json",
        )
        existing_regular = FileInstanceFactory(id="claude-1")

        instances: dict[str, FileInstance] = {
            "settings-1": existing_component,
            "claude-1": existing_regular,
        }

        # New instance with component preset should validate
        new_component = FileInstanceFactory(
            id="statusline-1",
            type=FileType.STATUSLINE,
            preset="component:custom",
            path=".claude/statusline.sh",
        )

        result = file_instance_service.validate_instance(
            new_component, instances, preset_repo, tmp_path, is_update=False
        )

        assert result.valid
