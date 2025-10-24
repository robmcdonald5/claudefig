"""Tests for file instance service layer."""

from claudefig.models import FileInstance, FileType, Preset, PresetSource
from claudefig.repositories.preset_repository import FakePresetRepository
from claudefig.services import file_instance_service


class TestListInstances:
    """Test list_instances() function."""

    def test_lists_all_instances(self):
        """Test listing all instances without filters."""
        instances = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            "test-2": FileInstance(
                id="test-2",
                type=FileType.GITIGNORE,
                preset="gitignore:python",
                path=".gitignore",
                enabled=False,
            ),
        }

        result = file_instance_service.list_instances(instances)

        assert len(result) == 2

    def test_filters_by_file_type(self):
        """Test filtering by file type."""
        instances = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            "test-2": FileInstance(
                id="test-2",
                type=FileType.GITIGNORE,
                preset="gitignore:python",
                path=".gitignore",
                enabled=True,
            ),
        }

        result = file_instance_service.list_instances(
            instances, file_type=FileType.CLAUDE_MD
        )

        assert len(result) == 1
        assert result[0].type == FileType.CLAUDE_MD

    def test_filters_enabled_only(self):
        """Test filtering enabled instances only."""
        instances = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            "test-2": FileInstance(
                id="test-2",
                type=FileType.GITIGNORE,
                preset="gitignore:python",
                path=".gitignore",
                enabled=False,
            ),
        }

        result = file_instance_service.list_instances(instances, enabled_only=True)

        assert len(result) == 1
        assert result[0].enabled is True

    def test_sorts_by_type_and_path(self):
        """Test instances are sorted by type then path."""
        instances = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.GITIGNORE,
                preset="gitignore:python",
                path="z.txt",
                enabled=True,
            ),
            "test-2": FileInstance(
                id="test-2",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            "test-3": FileInstance(
                id="test-3",
                type=FileType.CLAUDE_MD,
                preset="claude_md:custom",
                path="DOCS.md",
                enabled=True,
            ),
        }

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
        instance = FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )
        instances = {"test-1": instance}

        result = file_instance_service.get_instance(instances, "test-1")

        assert result is not None
        assert result.id == "test-1"

    def test_returns_none_for_nonexistent_instance(self):
        """Test returns None for non-existent instance."""
        instances = {}

        result = file_instance_service.get_instance(instances, "nonexistent")

        assert result is None


class TestAddInstance:
    """Test add_instance() function."""

    def test_adds_new_instance(self, tmp_path):
        """Test adding a new instance."""
        instances = {}
        # Add preset to repository
        preset = Preset(
            id="claude_md:default",
            name="default",
            type=FileType.CLAUDE_MD,
            description="Default",
            source=PresetSource.BUILT_IN,
        )
        preset_repo = FakePresetRepository([preset])

        new_instance = FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )

        result = file_instance_service.add_instance(
            instances, new_instance, preset_repo, tmp_path
        )

        assert result.valid
        assert "test-1" in instances
        assert instances["test-1"] == new_instance

    def test_returns_error_for_duplicate_id(self, tmp_path):
        """Test returns error when adding duplicate ID."""
        existing = FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )
        instances = {"test-1": existing}

        # Add presets to repository
        preset1 = Preset(
            id="claude_md:default",
            name="default",
            type=FileType.CLAUDE_MD,
            description="Default",
            source=PresetSource.BUILT_IN,
        )
        preset2 = Preset(
            id="gitignore:python",
            name="python",
            type=FileType.GITIGNORE,
            description="Python",
            source=PresetSource.BUILT_IN,
        )
        preset_repo = FakePresetRepository([preset1, preset2])

        new_instance = FileInstance(
            id="test-1",
            type=FileType.GITIGNORE,
            preset="gitignore:python",
            path=".gitignore",
            enabled=True,
        )

        result = file_instance_service.add_instance(
            instances, new_instance, preset_repo, tmp_path
        )

        assert not result.valid
        assert "already exists" in result.errors[0].lower()


class TestUpdateInstance:
    """Test update_instance() function."""

    def test_updates_existing_instance(self, tmp_path):
        """Test updating an existing instance."""
        instance = FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )
        instances = {"test-1": instance}

        # Add presets to repository
        preset1 = Preset(
            id="claude_md:default",
            name="default",
            type=FileType.CLAUDE_MD,
            description="Default",
            source=PresetSource.BUILT_IN,
        )
        preset2 = Preset(
            id="claude_md:custom",
            name="custom",
            type=FileType.CLAUDE_MD,
            description="Custom",
            source=PresetSource.USER,
        )
        preset_repo = FakePresetRepository([preset1, preset2])

        # Create updated instance
        updated_instance = FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:custom",
            path="CLAUDE.md",
            enabled=False,
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
        instances = {}
        preset_repo = FakePresetRepository()

        nonexistent_instance = FileInstance(
            id="nonexistent",
            type=FileType.CLAUDE_MD,
            preset="claude_md:custom",
            path="CLAUDE.md",
            enabled=True,
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
        instance = FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )
        instances = {"test-1": instance}

        result = file_instance_service.remove_instance(instances, "test-1")

        assert result is True
        assert "test-1" not in instances

    def test_returns_false_for_nonexistent_instance(self):
        """Test returns False for non-existent instance."""
        instances = {}

        result = file_instance_service.remove_instance(instances, "nonexistent")

        assert result is False


class TestEnableInstance:
    """Test enable_instance() function."""

    def test_enables_disabled_instance(self):
        """Test enabling a disabled instance."""
        instance = FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=False,
        )
        instances = {"test-1": instance}

        result = file_instance_service.enable_instance(instances, "test-1")

        assert result is True
        assert instances["test-1"].enabled is True

    def test_returns_false_for_nonexistent_instance(self):
        """Test returns False for non-existent instance."""
        instances = {}

        result = file_instance_service.enable_instance(instances, "nonexistent")

        assert result is False


class TestDisableInstance:
    """Test disable_instance() function."""

    def test_disables_enabled_instance(self):
        """Test disabling an enabled instance."""
        instance = FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
            enabled=True,
        )
        instances = {"test-1": instance}

        result = file_instance_service.disable_instance(instances, "test-1")

        assert result is True
        assert instances["test-1"].enabled is False

    def test_returns_false_for_nonexistent_instance(self):
        """Test returns False for non-existent instance."""
        instances = {}

        result = file_instance_service.disable_instance(instances, "nonexistent")

        assert result is False


class TestGenerateInstanceId:
    """Test generate_instance_id() function."""

    def test_generates_unique_id(self):
        """Test generating a unique instance ID."""
        instances = {
            "claude_md-default": FileInstance(
                id="claude_md-default",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            )
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
        instances = {}

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
        instances = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            "test-2": FileInstance(
                id="test-2",
                type=FileType.CLAUDE_MD,
                preset="claude_md:custom",
                path="DOCS.md",
                enabled=True,
            ),
            "test-3": FileInstance(
                id="test-3",
                type=FileType.GITIGNORE,
                preset="gitignore:python",
                path=".gitignore",
                enabled=True,
            ),
        }

        result = file_instance_service.count_by_type(instances)

        assert result[FileType.CLAUDE_MD] == 2
        assert result[FileType.GITIGNORE] == 1

    def test_returns_empty_dict_for_no_instances(self):
        """Test returns empty dict when no instances."""
        instances = {}

        result = file_instance_service.count_by_type(instances)

        assert result == {}


class TestGetInstancesByType:
    """Test get_instances_by_type() function."""

    def test_returns_instances_of_specified_type(self):
        """Test getting instances by file type."""
        instances = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            "test-2": FileInstance(
                id="test-2",
                type=FileType.GITIGNORE,
                preset="gitignore:python",
                path=".gitignore",
                enabled=True,
            ),
        }

        result = file_instance_service.get_instances_by_type(
            instances, FileType.CLAUDE_MD
        )

        assert len(result) == 1
        assert result[0].type == FileType.CLAUDE_MD

    def test_returns_empty_list_for_type_with_no_instances(self):
        """Test returns empty list for type with no instances."""
        instances = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
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
        instances_data = []

        instances_dict, errors = file_instance_service.load_instances_from_config(
            instances_data
        )

        assert instances_dict == {}
        assert errors == []


class TestSaveInstancesToConfig:
    """Test save_instances_to_config() function."""

    def test_saves_instances_to_config_format(self):
        """Test converting instances dict to config format."""
        instances = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            ),
            "test-2": FileInstance(
                id="test-2",
                type=FileType.GITIGNORE,
                preset="gitignore:python",
                path=".gitignore",
                enabled=False,
            ),
        }

        result = file_instance_service.save_instances_to_config(instances)

        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)
        assert any(item["id"] == "test-1" for item in result)
        assert any(item["id"] == "test-2" for item in result)

    def test_preserves_instance_properties(self):
        """Test preserves all instance properties."""
        instances = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
                variables={"key": "value"},
            ),
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
        instances = {}

        result = file_instance_service.save_instances_to_config(instances)

        assert result == []
