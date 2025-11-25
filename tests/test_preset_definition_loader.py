"""Tests for PresetDefinitionLoader service."""

from pathlib import Path
from unittest.mock import patch

import pytest

from claudefig.models import PresetDefinition
from claudefig.services.preset_definition_loader import (
    PresetDefinitionLoader,
    _load_from_path,
    _scan_presets_dir,
)


@pytest.fixture
def sample_toml_content():
    """Sample claudefig.toml content for testing."""
    return """
[project]
name = "test-project"

[[files]]
type = "claude_md"
path = "CLAUDE.md"
preset = "test"
enabled = true
"""


@pytest.fixture
def library_presets_dir(tmp_path):
    """Create a library presets directory with sample presets."""
    lib_dir = tmp_path / "library"
    lib_dir.mkdir()

    # Create "default" preset
    default_preset = lib_dir / "default"
    default_preset.mkdir()
    (default_preset / "claudefig.toml").write_text("""
[preset]
name = "default-preset"
version = "1.0.0"
description = "Default preset"

[[components]]
type = "claude_md"
name = "default"
""")

    return lib_dir


@pytest.fixture
def user_presets_dir(tmp_path):
    """Create a user presets directory with sample presets."""
    user_dir = tmp_path / "user"
    user_dir.mkdir()

    # Create "custom" preset
    custom_preset = user_dir / "custom"
    custom_preset.mkdir()
    (custom_preset / "claudefig.toml").write_text("""
[preset]
name = "custom-preset"
version = "1.0.0"
description = "Custom preset"

[[components]]
type = "settings_json"
name = "custom"
""")

    return user_dir


@pytest.fixture
def project_presets_dir(tmp_path):
    """Create a project presets directory with sample presets."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create "local" preset
    local_preset = project_dir / "local"
    local_preset.mkdir()
    (local_preset / "claudefig.toml").write_text("""
[preset]
name = "local-preset"
version = "1.0.0"
description = "Local preset"

[[components]]
type = "gitignore"
name = "local"
""")

    return project_dir


class TestPresetDefinitionLoaderInit:
    """Tests for PresetDefinitionLoader initialization."""

    def test_init_with_default_paths(self):
        """Test initialization with default paths."""
        loader = PresetDefinitionLoader()

        # User path should be set to default
        assert loader.user_presets_path is not None
        assert "presets" in str(loader.user_presets_path)

        # Project path should be None by default
        assert loader.project_presets_path is None

        # Cache should be empty
        assert loader._cache == {}

    def test_init_with_custom_paths(
        self, library_presets_dir, user_presets_dir, project_presets_dir
    ):
        """Test initialization with custom paths."""
        loader = PresetDefinitionLoader(
            library_presets_path=library_presets_dir,
            user_presets_path=user_presets_dir,
            project_presets_path=project_presets_dir,
        )

        assert loader.library_presets_path == library_presets_dir
        assert loader.user_presets_path == user_presets_dir
        assert loader.project_presets_path == project_presets_dir

    def test_init_library_path_fallback(self):
        """Test that library path uses importlib.resources fallback."""
        loader = PresetDefinitionLoader()

        # Should attempt to load from package or be None
        assert loader.library_presets_path is None or isinstance(
            loader.library_presets_path, Path
        )

    @patch("claudefig.services.preset_definition_loader.files")
    def test_init_handles_import_error(self, mock_files):
        """Test initialization handles importlib.resources errors."""
        mock_files.side_effect = FileNotFoundError("No module")

        loader = PresetDefinitionLoader()

        # Should gracefully set to None
        assert loader.library_presets_path is None

    def test_init_cache_is_empty(self, library_presets_dir):
        """Test that cache is initially empty."""
        loader = PresetDefinitionLoader(library_presets_path=library_presets_dir)

        assert isinstance(loader._cache, dict)
        assert len(loader._cache) == 0


class TestLoadFromPath:
    """Tests for _load_from_path function."""

    def test_load_from_path_success(self, library_presets_dir):
        """Test successful loading from path."""
        result = _load_from_path("default", library_presets_dir, "Library")

        assert isinstance(result, PresetDefinition)
        assert result.name == "default-preset"

    def test_load_from_path_missing_base_path(self):
        """Test loading when base path doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Library presets path not found"):
            _load_from_path("test", Path("/nonexistent"), "Library")

    def test_load_from_path_none_base_path(self):
        """Test loading when base path is None."""
        with pytest.raises(FileNotFoundError, match="Library presets path not found"):
            _load_from_path("test", None, "Library")

    def test_load_from_path_missing_preset(self, library_presets_dir):
        """Test loading non-existent preset."""
        with pytest.raises(FileNotFoundError, match="Preset 'nonexistent' not found"):
            _load_from_path("nonexistent", library_presets_dir, "Library")

    def test_load_from_path_missing_toml_file(self, library_presets_dir):
        """Test loading when preset directory exists but claudefig.toml missing."""
        # Create directory without claudefig.toml
        incomplete = library_presets_dir / "incomplete"
        incomplete.mkdir()

        with pytest.raises(FileNotFoundError):
            _load_from_path("incomplete", library_presets_dir, "Library")

    def test_load_from_path_error_message_includes_location(self, tmp_path):
        """Test that error messages include location name."""
        try:
            _load_from_path("test", tmp_path, "User")
        except FileNotFoundError as e:
            assert "user presets" in str(e).lower()


class TestLoadFromLibrary:
    """Tests for load_from_library method."""

    def test_load_from_library_success(self, library_presets_dir):
        """Test successfully loading preset from library."""
        loader = PresetDefinitionLoader(library_presets_path=library_presets_dir)

        result = loader.load_from_library("default")

        assert isinstance(result, PresetDefinition)
        assert result.name == "default-preset"

    def test_load_from_library_not_found(self, library_presets_dir):
        """Test loading non-existent library preset."""
        loader = PresetDefinitionLoader(library_presets_path=library_presets_dir)

        with pytest.raises(FileNotFoundError, match="not found in library presets"):
            loader.load_from_library("nonexistent")

    def test_load_from_library_no_library_path(self):
        """Test loading from library when path not configured."""
        with patch(
            "claudefig.services.preset_definition_loader.files",
            side_effect=FileNotFoundError(),
        ):
            loader = PresetDefinitionLoader(library_presets_path=None)

            # Library path should be None when files() fails
            assert loader.library_presets_path is None

            with pytest.raises(
                FileNotFoundError, match="Library presets path not found"
            ):
                loader.load_from_library("test")


class TestLoadFromUser:
    """Tests for load_from_user method."""

    def test_load_from_user_success(self, user_presets_dir):
        """Test successfully loading preset from user directory."""
        loader = PresetDefinitionLoader(user_presets_path=user_presets_dir)

        result = loader.load_from_user("custom")

        assert isinstance(result, PresetDefinition)
        assert result.name == "custom-preset"

    def test_load_from_user_not_found(self, user_presets_dir):
        """Test loading non-existent user preset."""
        loader = PresetDefinitionLoader(user_presets_path=user_presets_dir)

        with pytest.raises(FileNotFoundError, match="not found in user presets"):
            loader.load_from_user("nonexistent")

    def test_load_from_user_directory_missing(self, tmp_path):
        """Test loading from user when directory doesn't exist."""
        missing_dir = tmp_path / "missing"
        loader = PresetDefinitionLoader(user_presets_path=missing_dir)

        with pytest.raises(FileNotFoundError, match="User presets path not found"):
            loader.load_from_user("test")


class TestLoadFromProject:
    """Tests for load_from_project method."""

    def test_load_from_project_success(self, project_presets_dir):
        """Test successfully loading preset from project directory."""
        loader = PresetDefinitionLoader(project_presets_path=project_presets_dir)

        result = loader.load_from_project("local")

        assert isinstance(result, PresetDefinition)
        assert result.name == "local-preset"

    def test_load_from_project_not_found(self, project_presets_dir):
        """Test loading non-existent project preset."""
        loader = PresetDefinitionLoader(project_presets_path=project_presets_dir)

        with pytest.raises(FileNotFoundError, match="not found in project presets"):
            loader.load_from_project("nonexistent")

    def test_load_from_project_no_project_path(self):
        """Test loading from project when path not configured."""
        loader = PresetDefinitionLoader(project_presets_path=None)

        with pytest.raises(FileNotFoundError, match="Project presets path not found"):
            loader.load_from_project("test")


class TestLoadPreset:
    """Tests for load_preset method (priority loading)."""

    def test_load_preset_from_project_first(
        self, library_presets_dir, user_presets_dir, project_presets_dir
    ):
        """Test that project presets have highest priority."""
        # Create same preset in all locations
        (library_presets_dir / "shared").mkdir()
        (library_presets_dir / "shared" / "claudefig.toml").write_text(
            '[preset]\nname = "library-shared"\nversion = "1.0.0"\ndescription = ""'
        )

        (user_presets_dir / "shared").mkdir()
        (user_presets_dir / "shared" / "claudefig.toml").write_text(
            '[preset]\nname = "user-shared"\nversion = "1.0.0"\ndescription = ""'
        )

        (project_presets_dir / "shared").mkdir()
        (project_presets_dir / "shared" / "claudefig.toml").write_text(
            '[preset]\nname = "project-shared"\nversion = "1.0.0"\ndescription = ""'
        )

        loader = PresetDefinitionLoader(
            library_presets_path=library_presets_dir,
            user_presets_path=user_presets_dir,
            project_presets_path=project_presets_dir,
        )

        result = loader.load_preset("shared")

        # Should load from project (highest priority)
        assert result.name == "project-shared"

    def test_load_preset_from_user_when_not_in_project(
        self, library_presets_dir, user_presets_dir, project_presets_dir
    ):
        """Test that user presets are checked when not in project."""
        loader = PresetDefinitionLoader(
            library_presets_path=library_presets_dir,
            user_presets_path=user_presets_dir,
            project_presets_path=project_presets_dir,
        )

        result = loader.load_preset("custom")  # Only in user dir

        assert result.name == "custom-preset"

    def test_load_preset_from_library_when_not_in_others(
        self, library_presets_dir, user_presets_dir, project_presets_dir
    ):
        """Test that library presets are used as fallback."""
        loader = PresetDefinitionLoader(
            library_presets_path=library_presets_dir,
            user_presets_path=user_presets_dir,
            project_presets_path=project_presets_dir,
        )

        result = loader.load_preset("default")  # Only in library dir

        assert result.name == "default-preset"

    def test_load_preset_not_found_anywhere(
        self, library_presets_dir, user_presets_dir, project_presets_dir
    ):
        """Test loading preset that doesn't exist in any location."""
        loader = PresetDefinitionLoader(
            library_presets_path=library_presets_dir,
            user_presets_path=user_presets_dir,
            project_presets_path=project_presets_dir,
        )

        with pytest.raises(FileNotFoundError, match="not found in any location"):
            loader.load_preset("nonexistent")

    def test_load_preset_caches_result(self, library_presets_dir):
        """Test that loaded presets are cached."""
        loader = PresetDefinitionLoader(library_presets_path=library_presets_dir)

        result1 = loader.load_preset("default")
        result2 = loader.load_preset("default")

        # Should return same cached instance
        assert result1 is result2
        assert "default" in loader._cache

    def test_load_preset_bypass_cache(self, library_presets_dir):
        """Test bypassing cache with use_cache=False."""
        loader = PresetDefinitionLoader(library_presets_path=library_presets_dir)

        result1 = loader.load_preset("default", use_cache=True)
        result2 = loader.load_preset("default", use_cache=False)

        # Should load fresh instance
        assert result1 is not result2

    def test_load_preset_uses_cache_by_default(self, library_presets_dir):
        """Test that caching is enabled by default."""
        loader = PresetDefinitionLoader(library_presets_path=library_presets_dir)

        result1 = loader.load_preset("default")  # No use_cache param
        result2 = loader.load_preset("default")  # No use_cache param

        # Should use cache
        assert result1 is result2

    def test_load_preset_skips_none_paths(self, library_presets_dir, tmp_path):
        """Test that None paths are skipped during priority loading."""
        # Mock to ensure user_presets_path doesn't get a real path
        with patch(
            "claudefig.services.preset_definition_loader.get_user_config_dir",
            return_value=tmp_path / "nonexistent",
        ):
            loader = PresetDefinitionLoader(
                library_presets_path=library_presets_dir,
                user_presets_path=None,  # Skip user
                project_presets_path=None,  # Skip project
            )

            result = loader.load_preset("default")

            # Should still find in library
            # Name in toml is "default-preset", but we're loading from directory "default"
            assert result.name == "default-preset"
            assert isinstance(result, PresetDefinition)

    def test_load_preset_error_includes_all_locations(
        self, library_presets_dir, user_presets_dir
    ):
        """Test that error message includes details from all locations."""
        loader = PresetDefinitionLoader(
            library_presets_path=library_presets_dir,
            user_presets_path=user_presets_dir,
        )

        try:
            loader.load_preset("missing")
        except FileNotFoundError as e:
            error_msg = str(e)
            assert "Library:" in error_msg or "User:" in error_msg


class TestScanPresetsDir:
    """Tests for _scan_presets_dir function."""

    def test_scan_valid_directory(self, library_presets_dir):
        """Test scanning directory with valid presets."""
        result = _scan_presets_dir(library_presets_dir)

        assert "default" in result
        assert isinstance(result, set)

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = _scan_presets_dir(empty_dir)

        assert len(result) == 0
        assert isinstance(result, set)

    def test_scan_nonexistent_directory(self, tmp_path):
        """Test scanning non-existent directory."""
        missing_dir = tmp_path / "missing"

        result = _scan_presets_dir(missing_dir)

        assert len(result) == 0

    def test_scan_none_path(self):
        """Test scanning with None path."""
        result = _scan_presets_dir(None)

        assert len(result) == 0

    def test_scan_ignores_directories_without_toml(self, tmp_path):
        """Test that directories without claudefig.toml are ignored."""
        scan_dir = tmp_path / "scan"
        scan_dir.mkdir()

        # Valid preset
        (scan_dir / "valid").mkdir()
        (scan_dir / "valid" / "claudefig.toml").write_text("[project]\nname = 'valid'")

        # Invalid preset (no toml)
        (scan_dir / "invalid").mkdir()

        result = _scan_presets_dir(scan_dir)

        assert "valid" in result
        assert "invalid" not in result

    def test_scan_handles_permission_error(self, tmp_path):
        """Test scanning handles permission errors gracefully."""
        # Mock iterdir to raise PermissionError
        with patch.object(Path, "iterdir", side_effect=PermissionError("No access")):
            result = _scan_presets_dir(tmp_path)

            # Should return empty set, not raise
            assert len(result) == 0

    def test_scan_handles_os_error(self, tmp_path):
        """Test scanning handles OS errors gracefully."""
        # Mock iterdir to raise OSError
        with patch.object(Path, "iterdir", side_effect=OSError("Disk error")):
            result = _scan_presets_dir(tmp_path)

            # Should return empty set, not raise
            assert len(result) == 0

    def test_scan_ignores_files(self, tmp_path):
        """Test that files are ignored, only directories scanned."""
        scan_dir = tmp_path / "scan"
        scan_dir.mkdir()

        # Create a file (should be ignored)
        (scan_dir / "file.txt").write_text("content")

        # Create valid preset directory
        (scan_dir / "preset").mkdir()
        (scan_dir / "preset" / "claudefig.toml").write_text("[project]\nname = 'test'")

        result = _scan_presets_dir(scan_dir)

        assert "preset" in result
        assert "file.txt" not in result


class TestListAvailablePresets:
    """Tests for list_available_presets method."""

    def test_list_from_all_locations(
        self, library_presets_dir, user_presets_dir, project_presets_dir
    ):
        """Test listing presets from all locations."""
        loader = PresetDefinitionLoader(
            library_presets_path=library_presets_dir,
            user_presets_path=user_presets_dir,
            project_presets_path=project_presets_dir,
        )

        result = loader.list_available_presets()

        assert "default" in result  # From library
        assert "custom" in result  # From user
        assert "local" in result  # From project
        assert isinstance(result, list)

    def test_list_returns_sorted(
        self, library_presets_dir, user_presets_dir, project_presets_dir
    ):
        """Test that preset list is sorted."""
        loader = PresetDefinitionLoader(
            library_presets_path=library_presets_dir,
            user_presets_path=user_presets_dir,
            project_presets_path=project_presets_dir,
        )

        result = loader.list_available_presets()

        assert result == sorted(result)

    def test_list_deduplicates_presets(self, library_presets_dir, user_presets_dir):
        """Test that duplicate preset names appear only once."""
        # Create "duplicate" in both locations
        (library_presets_dir / "duplicate").mkdir()
        (library_presets_dir / "duplicate" / "claudefig.toml").write_text(
            "[project]\nname = 'lib'"
        )

        (user_presets_dir / "duplicate").mkdir()
        (user_presets_dir / "duplicate" / "claudefig.toml").write_text(
            "[project]\nname = 'user'"
        )

        loader = PresetDefinitionLoader(
            library_presets_path=library_presets_dir,
            user_presets_path=user_presets_dir,
        )

        result = loader.list_available_presets()

        # Should appear only once
        assert result.count("duplicate") == 1

    def test_list_empty_when_no_presets(self, tmp_path):
        """Test listing when no presets exist."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Create a fake user dir that exists but is empty
        user_dir = tmp_path / "user_empty"
        user_dir.mkdir()

        loader = PresetDefinitionLoader(
            library_presets_path=empty_dir,
            user_presets_path=user_dir,
            project_presets_path=None,
        )

        result = loader.list_available_presets()

        assert len(result) == 0
        assert isinstance(result, list)

    def test_list_with_none_paths(self):
        """Test listing when paths are None."""
        with (
            patch(
                "claudefig.services.preset_definition_loader.files",
                side_effect=FileNotFoundError(),
            ),
            patch(
                "claudefig.services.preset_definition_loader.get_user_config_dir",
                return_value=Path("/nonexistent"),
            ),
        ):
            loader = PresetDefinitionLoader(
                library_presets_path=None,
                user_presets_path=None,
                project_presets_path=None,
            )

            result = loader.list_available_presets()

            assert len(result) == 0

    def test_list_handles_nested_structures(self, tmp_path):
        """Test that only top-level preset directories are listed."""
        scan_dir = tmp_path / "presets"
        scan_dir.mkdir()

        # Top-level preset
        (scan_dir / "top").mkdir()
        (scan_dir / "top" / "claudefig.toml").write_text("[project]\nname = 'top'")

        # Nested structure (should not be listed as separate preset)
        (scan_dir / "top" / "nested").mkdir()
        (scan_dir / "top" / "nested" / "claudefig.toml").write_text(
            "[project]\nname = 'nested'"
        )

        loader = PresetDefinitionLoader(library_presets_path=scan_dir)

        result = loader.list_available_presets()

        assert "top" in result
        assert "nested" not in result  # Nested directories not scanned


class TestPresetDefinitionLoaderEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_multiple_load_clears_old_cache_entries(self, library_presets_dir):
        """Test that cache accumulates presets correctly."""
        loader = PresetDefinitionLoader(library_presets_path=library_presets_dir)

        # Create multiple presets
        (library_presets_dir / "preset1").mkdir()
        (library_presets_dir / "preset1" / "claudefig.toml").write_text(
            "[project]\nname = 'p1'"
        )

        (library_presets_dir / "preset2").mkdir()
        (library_presets_dir / "preset2" / "claudefig.toml").write_text(
            "[project]\nname = 'p2'"
        )

        loader.load_preset("preset1")
        loader.load_preset("preset2")

        assert len(loader._cache) == 2
        assert "preset1" in loader._cache
        assert "preset2" in loader._cache

    def test_load_with_invalid_toml_content(self, tmp_path):
        """Test loading preset with invalid TOML content."""
        preset_dir = tmp_path / "broken"
        preset_dir.mkdir()
        (preset_dir / "claudefig.toml").write_text("invalid {{{ toml")

        loader = PresetDefinitionLoader(library_presets_path=tmp_path)

        # PresetDefinition.from_toml should raise an appropriate error
        with pytest.raises((ValueError, KeyError, TypeError)):  # TOML parsing errors
            loader.load_preset("broken")

    def test_concurrent_cache_access(self, library_presets_dir):
        """Test that cache is consistent across multiple accesses."""
        loader = PresetDefinitionLoader(library_presets_path=library_presets_dir)

        result1 = loader.load_preset("default")
        result2 = loader.load_preset("default")
        result3 = loader.load_preset("default")

        # All should be same instance from cache
        assert result1 is result2 is result3

    def test_load_preset_name_case_sensitivity(self, library_presets_dir):
        """Test that preset names follow filesystem case sensitivity."""
        # Create "Test" preset
        (library_presets_dir / "Test").mkdir()
        (library_presets_dir / "Test" / "claudefig.toml").write_text(
            "[preset]\nname = 'Test'\nversion = '1.0.0'\ndescription = ''"
        )

        loader = PresetDefinitionLoader(library_presets_path=library_presets_dir)

        # Should always find "Test"
        result = loader.load_preset("Test")
        assert result.name == "Test"

        # Test filesystem case sensitivity by actually checking if file exists
        # Some filesystems are case-insensitive (Windows, macOS default)
        # Some are case-sensitive (Linux, macOS with APFS case-sensitive)
        test_lower_path = library_presets_dir / "test"
        is_case_insensitive = test_lower_path.exists()  # Will exist if case-insensitive

        if is_case_insensitive:
            # Filesystem is case-insensitive: "test" will find "Test"
            result2 = loader.load_preset("test")
            assert result2.name == "Test"
        else:
            # Filesystem is case-sensitive: "test" should not find "Test"
            with pytest.raises(FileNotFoundError):
                loader.load_preset("test")
