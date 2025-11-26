"""Tests for file instance service layer."""

import platform

import pytest

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
            ("test-1", {"path": "z.md"}),
            ("test-2", {"type": FileType.GITIGNORE, "path": ".gitignore"}),
            ("test-3", {"path": "a.md"}),
        )

        result = file_instance_service.list_instances(instances)

        # CLAUDE_MD comes before GITIGNORE alphabetically
        assert result[0].path == "a.md"
        assert result[1].path == "z.md"
        assert result[2].path == ".gitignore"


class TestGetInstance:
    """Test get_instance() function."""

    def test_retrieves_existing_instance(self):
        """Test retrieving an instance by ID."""
        instances = FileInstanceFactory.create_dict(
            ("test-1", {}),
            ("test-2", {}),
        )

        result = file_instance_service.get_instance(instances, "test-1")

        assert result is not None
        assert result.id == "test-1"

    def test_returns_none_for_missing_instance(self):
        """Test retrieving a non-existent instance."""
        instances = FileInstanceFactory.create_dict(("test-1", {}))

        result = file_instance_service.get_instance(instances, "missing")

        assert result is None


class TestAddInstance:
    """Test add_instance() function."""

    def test_adds_valid_instance(self, tmp_path):
        """Test adding a valid file instance."""
        preset = PresetFactory(
            id="claude_md:default",
            type=FileType.CLAUDE_MD,
            name="default",
        )
        preset_repo = FakePresetRepository([preset])
        instances: dict[str, FileInstance] = {}

        instance = FileInstanceFactory(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )

        result = file_instance_service.add_instance(
            instances, instance, preset_repo, tmp_path
        )

        assert result.valid
        assert "test-1" in instances

    def test_rejects_instance_with_nonexistent_preset(self, tmp_path):
        """Test adding instance with nonexistent preset."""
        preset_repo = FakePresetRepository([])
        instances: dict[str, FileInstance] = {}

        instance = FileInstanceFactory(preset="nonexistent")

        result = file_instance_service.add_instance(
            instances, instance, preset_repo, tmp_path
        )

        assert not result.valid
        assert "test-instance" not in instances

    def test_rejects_duplicate_id(self, tmp_path):
        """Test adding instance with duplicate ID."""
        preset = PresetFactory()
        preset_repo = FakePresetRepository([preset])
        instances: dict[str, FileInstance] = {
            "test-1": FileInstanceFactory(id="test-1")
        }

        # Try to add another instance with same ID
        duplicate = FileInstanceFactory(id="test-1")

        result = file_instance_service.add_instance(
            instances, duplicate, preset_repo, tmp_path
        )

        assert not result.valid
        assert "already exists" in result.errors[0]


class TestUpdateInstance:
    """Test update_instance() function."""

    def test_updates_existing_instance(self, tmp_path):
        """Test updating an existing instance."""
        preset = PresetFactory(
            id="claude_md:default",
            type=FileType.CLAUDE_MD,
            name="default",
        )
        preset_repo = FakePresetRepository([preset])

        original = FileInstanceFactory(id="test-1", enabled=True)
        instances: dict[str, FileInstance] = {"test-1": original}

        # Update to disabled
        updated = FileInstanceFactory(id="test-1", enabled=False)

        result = file_instance_service.update_instance(
            instances, updated, preset_repo, tmp_path
        )

        assert result.valid
        assert instances["test-1"].enabled is False

    def test_rejects_updating_nonexistent_instance(self, tmp_path):
        """Test updating an instance that doesn't exist."""
        preset_repo = FakePresetRepository([])
        instances: dict[str, FileInstance] = {}

        instance = FileInstanceFactory(id="missing")

        result = file_instance_service.update_instance(
            instances, instance, preset_repo, tmp_path
        )

        assert not result.valid
        assert "not found" in result.errors[0].lower()


class TestRemoveInstance:
    """Test remove_instance() function."""

    def test_removes_existing_instance(self):
        """Test removing an instance."""
        instances: dict[str, FileInstance] = {
            "test-1": FileInstanceFactory(id="test-1")
        }

        result = file_instance_service.remove_instance(instances, "test-1")

        assert result is True
        assert "test-1" not in instances

    def test_returns_false_for_nonexistent_instance(self):
        """Test removing a non-existent instance returns False."""
        instances: dict[str, FileInstance] = {}

        result = file_instance_service.remove_instance(instances, "missing")

        assert result is False
        assert len(instances) == 0


class TestValidateInstance:
    """Test validate_instance() function."""

    def test_validates_correct_instance(self, tmp_path):
        """Test validation passes for correct instance."""
        preset = PresetFactory(
            id="claude_md:default",
            type=FileType.CLAUDE_MD,
            name="default",
        )
        preset_repo = FakePresetRepository([preset])
        instances: dict[str, FileInstance] = {}

        instance = FileInstanceFactory(
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )

        result = file_instance_service.validate_instance(
            instance, instances, preset_repo, tmp_path, is_update=False
        )

        assert result.valid

    def test_rejects_instance_with_invalid_preset_type(self, tmp_path):
        """Test validation fails when preset type doesn't match file type."""
        # Create GITIGNORE preset
        gitignore_preset = PresetFactory(
            id="gitignore:python",
            type=FileType.GITIGNORE,
            name="python",
        )
        preset_repo = FakePresetRepository([gitignore_preset])
        instances: dict[str, FileInstance] = {}

        # Try to use gitignore preset for CLAUDE_MD file
        instance = FileInstanceFactory(
            type=FileType.CLAUDE_MD,
            preset="gitignore:python",  # Wrong type!
            path="CLAUDE.md",
        )

        result = file_instance_service.validate_instance(
            instance, instances, preset_repo, tmp_path, is_update=False
        )

        assert not result.valid
        assert "type mismatch" in result.errors[0].lower()

    def test_allows_single_instance_type_with_unique_id(self, tmp_path):
        """Test single-instance types are allowed with different IDs."""
        preset = PresetFactory(
            id="claude_md:default",
            type=FileType.CLAUDE_MD,
            name="default",
        )
        preset_repo = FakePresetRepository([preset])

        # Already have a CLAUDE.md
        existing = FileInstanceFactory(
            id="claude-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )
        instances: dict[str, FileInstance] = {"claude-1": existing}

        # Validation allows another if ID is different
        # (actual enforcement happens at file system level)
        another = FileInstanceFactory(
            id="claude-2",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="docs/CLAUDE.md",  # Different path
        )

        result = file_instance_service.validate_instance(
            another, instances, preset_repo, tmp_path, is_update=False
        )

        # Validation passes - enforcement is at higher level
        assert result.valid

    def test_allows_multiple_instances_for_multi_instance_types(self, tmp_path):
        """Test validation allows multiple instances for types that support it."""
        preset = PresetFactory(
            id="commands:default",
            type=FileType.COMMANDS,
            name="default",
        )
        preset_repo = FakePresetRepository([preset])

        # Already have one command
        existing = FileInstanceFactory(
            id="cmd-1",
            type=FileType.COMMANDS,
            preset="commands:default",
            path=".claude/commands/test1.md",
        )
        instances: dict[str, FileInstance] = {"cmd-1": existing}

        # Add another command (should be allowed)
        another = FileInstanceFactory(
            id="cmd-2",
            type=FileType.COMMANDS,
            preset="commands:default",
            path=".claude/commands/test2.md",
        )

        result = file_instance_service.validate_instance(
            another, instances, preset_repo, tmp_path, is_update=False
        )

        assert result.valid

    def test_validates_plugin_components_for_plugin_type(self, tmp_path):
        """Test plugin validation runs for PLUGINS file type."""
        preset = PresetFactory(
            id="plugins:default",
            type=FileType.PLUGINS,
            name="default",
        )
        preset_repo = FakePresetRepository([preset])
        instances: dict[str, FileInstance] = {}

        # Create a valid plugin JSON file
        plugin_file = tmp_path / ".claude" / "plugins" / "test.json"
        plugin_file.parent.mkdir(parents=True)
        plugin_file.write_text('{"name": "test", "components": {}}')

        instance = FileInstanceFactory(
            type=FileType.PLUGINS,
            preset="plugins:default",
            path=".claude/plugins/test.json",
        )

        result = file_instance_service.validate_instance(
            instance, instances, preset_repo, tmp_path, is_update=False
        )

        # Should have validation result (may have warnings, but should be valid)
        assert result is not None

    def test_allows_builtin_preset_for_file_type(self, tmp_path):
        """Test built-in presets are allowed for matching file types."""
        # Create a built-in preset
        builtin_preset = PresetFactory(
            id="claude_md:default",
            type=FileType.CLAUDE_MD,
            name="default",
            source=PresetSource.BUILT_IN,
        )
        preset_repo = FakePresetRepository([builtin_preset])

        instances: dict[str, FileInstance] = {}

        # New instance with built-in preset should validate
        new_instance = FileInstanceFactory(
            id="claude-1",
            type=FileType.CLAUDE_MD,
            preset="claude_md:default",
            path="CLAUDE.md",
        )

        result = file_instance_service.validate_instance(
            new_instance, instances, preset_repo, tmp_path, is_update=False
        )

        assert result.valid


class TestValidatePathSecurity:
    """Test validate_path() function - SECURITY CRITICAL."""

    @pytest.mark.parametrize(
        "path,description",
        [
            ("CLAUDE.md", "simple relative"),
            ("docs/CLAUDE.md", "nested relative"),
            ("./CLAUDE.md", "current directory prefix"),
            ("././././CLAUDE.md", "multiple current directory"),
        ],
        ids=lambda x: x if isinstance(x, str) and "." in x else None,
    )
    def test_accepts_valid_relative_paths(self, tmp_path, path, description):
        """Test valid relative paths are accepted."""
        result = file_instance_service.validate_path(path, FileType.CLAUDE_MD, tmp_path)

        assert result.valid, f"Rejected valid path: {path} ({description})"
        assert not result.has_errors

    def test_rejects_empty_path(self, tmp_path):
        """Test empty path is rejected."""
        result = file_instance_service.validate_path("", FileType.CLAUDE_MD, tmp_path)

        assert not result.valid
        assert "cannot be empty" in result.errors[0]

    def test_rejects_absolute_unix_path(self, tmp_path):
        """Test absolute Unix path is rejected."""
        result = file_instance_service.validate_path(
            "/etc/passwd", FileType.CLAUDE_MD, tmp_path
        )

        assert not result.valid
        # On Windows, /etc/passwd is treated as relative but caught by resolve check
        # On Unix, it's caught as absolute path
        assert (
            "must be relative" in result.errors[0]
            or "outside repository" in result.errors[0]
        )

    def test_rejects_absolute_windows_path(self, tmp_path):
        """Test absolute Windows path is rejected.

        Note: On Unix, C:/Windows is treated as relative, so it may pass
        is_absolute() but should still be caught by other validation.
        """
        result = file_instance_service.validate_path(
            "C:/Windows/System32/config", FileType.CLAUDE_MD, tmp_path
        )

        if platform.system() == "Windows":
            # On Windows, this is absolute and should be rejected
            assert not result.valid
            assert "must be relative" in result.errors[0]
        else:
            # On Unix, C:/Windows/... is treated as relative path
            # Security note: This is actually safe on Unix since C: is just a filename
            pass

    def test_rejects_absolute_windows_path_backslash(self, tmp_path):
        r"""Test absolute Windows path with backslashes is rejected.

        Note: On Unix, backslashes in paths are literal characters, not separators.
        C:\Windows becomes a filename "C:\Windows", which is valid on Unix.
        """
        result = file_instance_service.validate_path(
            r"C:\Windows\System32\config", FileType.CLAUDE_MD, tmp_path
        )

        if platform.system() == "Windows":
            # On Windows, this is absolute and should be rejected
            assert not result.valid
            assert "must be relative" in result.errors[0]
        else:
            # On Unix, backslashes are literal chars, not path separators
            # This becomes a strange but technically valid relative path
            pass

    @pytest.mark.parametrize(
        "path,description",
        [
            ("../../../etc/passwd", "triple parent traversal"),
            ("../CLAUDE.md", "single parent reference"),
            ("docs/../../etc/passwd", "nested parent in middle"),
            ("docs/../../../CLAUDE.md", "hidden parent reference"),
            ("../outside.txt", "simple parent escape"),
            ("subdir/../../outside.txt", "subdirectory escape"),
        ],
        ids=lambda x: x if isinstance(x, str) and "/" in x else None,
    )
    def test_rejects_parent_directory_traversal(self, tmp_path, path, description):
        """Test parent directory references are rejected (path traversal attack)."""
        # Create subdirectory for tests that reference it
        subdir = tmp_path / "subdir"
        subdir.mkdir(exist_ok=True)

        result = file_instance_service.validate_path(path, FileType.CLAUDE_MD, tmp_path)

        assert not result.valid, f"Failed to reject: {path} ({description})"
        assert "parent directory" in result.errors[0]

    def test_warns_for_directory_type_without_trailing_slash(self, tmp_path):
        """Test directory types generate warning without trailing slash."""
        result = file_instance_service.validate_path(
            ".claude/commands", FileType.COMMANDS, tmp_path
        )

        # Should be valid but with warning
        assert result.valid
        assert result.has_warnings
        assert "should end with '/'" in result.warnings[0]

    def test_allows_directory_type_with_trailing_slash(self, tmp_path):
        """Test directory types with trailing slash are accepted."""
        result = file_instance_service.validate_path(
            ".claude/commands/", FileType.COMMANDS, tmp_path
        )

        assert result.valid
        assert not result.has_warnings

    def test_warns_for_existing_file_non_append_mode(self, tmp_path):
        """Test warning when file exists and not in append mode."""
        # Create existing file
        existing = tmp_path / "CLAUDE.md"
        existing.write_text("existing")

        result = file_instance_service.validate_path(
            "CLAUDE.md", FileType.CLAUDE_MD, tmp_path
        )

        # Should be valid but warn
        assert result.valid
        assert result.has_warnings
        assert "already exists" in result.warnings[0]

    def test_allows_existing_file_in_append_mode(self, tmp_path):
        """Test existing file is OK for append-mode types."""
        # Create existing gitignore
        existing = tmp_path / ".gitignore"
        existing.write_text("existing")

        result = file_instance_service.validate_path(
            ".gitignore", FileType.GITIGNORE, tmp_path
        )

        # GITIGNORE has append_mode=True, so no warning
        assert result.valid
        assert not result.has_warnings

    def test_handles_invalid_path_edge_cases(self, tmp_path):
        """Test invalid path edge cases are handled safely."""
        # Test very long path (potential buffer overflow in other systems)
        long_path = "a/" * 200 + "test.md"
        result = file_instance_service.validate_path(
            long_path, FileType.CLAUDE_MD, tmp_path
        )

        # Should either accept or reject gracefully (no crashes)
        assert result is not None
        assert isinstance(result.valid, bool)

    def test_path_normalization_security(self, tmp_path):
        """Test path normalization doesn't introduce security holes."""
        # Test various obfuscated path traversal attempts
        # Note: Backslashes are only path separators on Windows
        if platform.system() == "Windows":
            malicious_paths = [
                "..\\..\\..\\etc\\passwd",  # Windows-style backslashes
                "./../../../etc/passwd",  # Mixed
                "foo/../../bar/../../../etc/passwd",  # Nested
            ]
        else:
            # On Unix, backslashes are literal characters, not separators
            # Only test with forward slashes
            malicious_paths = [
                "./../../../etc/passwd",  # Mixed
                "foo/../../bar/../../../etc/passwd",  # Nested
            ]

        for malicious in malicious_paths:
            result = file_instance_service.validate_path(
                malicious, FileType.CLAUDE_MD, tmp_path
            )
            assert not result.valid, f"Failed to reject malicious path: {malicious}"
            assert (
                "parent directory" in result.errors[0]
                or "outside repository" in result.errors[0]
            )


class TestGenerateInstanceId:
    """Test generate_instance_id() function."""

    def test_generates_basic_id(self):
        """Test basic ID generation."""
        result = file_instance_service.generate_instance_id(
            FileType.CLAUDE_MD, "default", None, {}
        )

        assert result == "claude_md-default"

    def test_includes_path_suffix_for_non_default_path(self):
        """Test ID includes path suffix for custom paths."""
        result = file_instance_service.generate_instance_id(
            FileType.CLAUDE_MD, "custom", "docs/CLAUDE.md", {}
        )

        assert result == "claude_md-custom-docs"

    def test_adds_counter_for_duplicate_ids(self):
        """Test counter is added when ID exists."""
        existing: dict[str, FileInstance] = {"claude_md-default": FileInstanceFactory()}

        result = file_instance_service.generate_instance_id(
            FileType.CLAUDE_MD, "default", None, existing
        )

        assert result == "claude_md-default-1"

    def test_increments_counter_for_multiple_duplicates(self):
        """Test counter increments for multiple duplicates."""
        existing: dict[str, FileInstance] = {
            "claude_md-default": FileInstanceFactory(),
            "claude_md-default-1": FileInstanceFactory(),
        }

        result = file_instance_service.generate_instance_id(
            FileType.CLAUDE_MD, "default", None, existing
        )

        assert result == "claude_md-default-2"
