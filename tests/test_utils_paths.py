"""Tests for utils/paths.py module."""

import tempfile
from pathlib import Path

import pytest

from claudefig.utils import paths


class TestEnsureDirectory:
    """Test ensure_directory() function."""

    def test_creates_new_directory(self):
        """Test creates directory when it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "new_dir"
            assert not test_dir.exists()

            paths.ensure_directory(test_dir)

            assert test_dir.exists()
            assert test_dir.is_dir()

    def test_creates_nested_directories(self):
        """Test creates nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "level1" / "level2" / "level3"

            paths.ensure_directory(test_dir)

            assert test_dir.exists()
            assert (Path(tmpdir) / "level1").exists()
            assert (Path(tmpdir) / "level1" / "level2").exists()

    def test_does_not_error_when_directory_exists(self):
        """Test doesn't raise error if directory already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "existing"
            test_dir.mkdir()

            # Should not raise error
            paths.ensure_directory(test_dir)

            assert test_dir.exists()


class TestIsGitRepository:
    """Test is_git_repository() function."""

    def test_returns_true_when_git_directory_exists(self):
        """Test returns True when .git directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            git_dir = repo_dir / ".git"
            git_dir.mkdir()

            result = paths.is_git_repository(repo_dir)

            assert result is True

    def test_returns_true_for_subdirectory_of_git_repo(self):
        """Test returns True for subdirectory of git repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            git_dir = repo_dir / ".git"
            git_dir.mkdir()

            subdir = repo_dir / "src" / "nested"
            subdir.mkdir(parents=True)

            result = paths.is_git_repository(subdir)

            assert result is True

    def test_returns_false_when_not_in_git_repo(self):
        """Test returns False when not in git repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_repo_dir = Path(tmpdir) / "not_a_repo"
            non_repo_dir.mkdir()

            result = paths.is_git_repository(non_repo_dir)

            assert result is False

    def test_stops_at_filesystem_root(self):
        """Test stops searching at filesystem root."""
        # Use temp directory which definitely has no .git above it
        with tempfile.TemporaryDirectory() as tmpdir:
            result = paths.is_git_repository(Path(tmpdir))

            # Should return False, not hang or error
            assert result is False


class TestFindFileUpwards:
    """Test find_file_upwards() function."""

    def test_finds_file_in_current_directory(self):
        """Test finds file in starting directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            target_file = test_dir / "config.toml"
            target_file.write_text("test")

            result = paths.find_file_upwards(test_dir, "config.toml")

            assert result is not None
            assert result.resolve() == target_file.resolve()

    def test_finds_file_in_parent_directory(self):
        """Test finds file in parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_dir = Path(tmpdir)
            target_file = parent_dir / "config.toml"
            target_file.write_text("test")

            child_dir = parent_dir / "subdir"
            child_dir.mkdir()

            result = paths.find_file_upwards(child_dir, "config.toml")

            assert result is not None
            assert result.resolve() == target_file.resolve()

    def test_finds_file_multiple_levels_up(self):
        """Test finds file multiple levels up."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir)
            target_file = root_dir / "config.toml"
            target_file.write_text("test")

            deep_dir = root_dir / "a" / "b" / "c"
            deep_dir.mkdir(parents=True)

            result = paths.find_file_upwards(deep_dir, "config.toml")

            assert result is not None
            assert result.resolve() == target_file.resolve()

    def test_returns_none_when_file_not_found(self):
        """Test returns None when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = paths.find_file_upwards(Path(tmpdir), "nonexistent.txt")

            assert result is None

    def test_respects_max_levels_limit(self):
        """Test respects max_levels parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir)
            target_file = root_dir / "config.toml"
            target_file.write_text("test")

            # Create directory 5 levels deep
            deep_dir = root_dir / "a" / "b" / "c" / "d" / "e"
            deep_dir.mkdir(parents=True)

            # Search with max_levels=2 (should not reach root)
            result = paths.find_file_upwards(deep_dir, "config.toml", max_levels=2)

            assert result is None

    def test_finds_closest_file_when_multiple_exist(self):
        """Test finds closest file when multiple exist at different levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir)
            root_file = root_dir / "config.toml"
            root_file.write_text("root")

            subdir = root_dir / "subdir"
            subdir.mkdir()
            subdir_file = subdir / "config.toml"
            subdir_file.write_text("subdir")

            result = paths.find_file_upwards(subdir, "config.toml")

            # Should find closest one
            assert result.resolve() == subdir_file.resolve()


class TestIsSubdirectory:
    """Test is_subdirectory() function."""

    def test_returns_true_for_direct_child(self):
        """Test returns True for direct child directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = Path(tmpdir)
            child = parent / "child"
            child.mkdir()

            result = paths.is_subdirectory(child, parent)

            assert result is True

    def test_returns_true_for_nested_child(self):
        """Test returns True for nested child directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = Path(tmpdir)
            child = parent / "a" / "b" / "c"
            child.mkdir(parents=True)

            result = paths.is_subdirectory(child, parent)

            assert result is True

    def test_returns_false_for_sibling(self):
        """Test returns False for sibling directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = Path(tmpdir)
            dir1 = parent / "dir1"
            dir2 = parent / "dir2"
            dir1.mkdir()
            dir2.mkdir()

            result = paths.is_subdirectory(dir1, dir2)

            assert result is False

    def test_returns_false_for_unrelated_paths(self):
        """Test returns False for completely unrelated paths."""
        path1 = Path("/tmp/path1")
        path2 = Path("/usr/local")

        result = paths.is_subdirectory(path1, path2)

        assert result is False

    def test_returns_false_when_child_is_parent(self):
        """Test returns False when child is actually parent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = Path(tmpdir)
            child = parent / "child"
            child.mkdir()

            # Reversed - child should not be parent of parent
            result = paths.is_subdirectory(parent, child)

            assert result is False


class TestGetRelativePath:
    """Test get_relative_path() function."""

    def test_returns_relative_path_for_child(self):
        """Test returns correct relative path for child."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            target = base / "subdir" / "file.txt"

            result = paths.get_relative_path(target, base)

            assert result == Path("subdir/file.txt")

    def test_returns_relative_path_for_deeply_nested(self):
        """Test returns relative path for deeply nested file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            target = base / "a" / "b" / "c" / "file.txt"

            result = paths.get_relative_path(target, base)

            assert result == Path("a/b/c/file.txt")

    def test_raises_error_for_unrelated_paths(self):
        """Test raises ValueError for unrelated paths."""
        path1 = Path("/tmp/path1")
        path2 = Path("/usr/local")

        with pytest.raises(ValueError):
            paths.get_relative_path(path1, path2)


class TestSafePathJoin:
    """Test safe_path_join() function."""

    def test_joins_simple_path_components(self):
        """Test joins simple path components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            result = paths.safe_path_join(base, "subdir", "file.txt")

            expected = base / "subdir" / "file.txt"
            assert result == expected

    def test_joins_single_component(self):
        """Test joins single path component."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            result = paths.safe_path_join(base, "file.txt")

            assert result == base / "file.txt"

    def test_raises_error_for_parent_directory_traversal(self):
        """Test raises error for directory traversal attempts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "base"
            base.mkdir()

            with pytest.raises(ValueError) as exc_info:
                paths.safe_path_join(base, "..", "etc", "passwd")

            assert "escapes base directory" in str(exc_info.value)

    def test_raises_error_for_multiple_parent_refs(self):
        """Test raises error for multiple parent references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "base"
            base.mkdir()

            with pytest.raises(ValueError):
                paths.safe_path_join(base, "..", "..", "etc")

    def test_allows_valid_nested_paths(self):
        """Test allows valid nested path construction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            result = paths.safe_path_join(base, "a", "b", "c", "d")

            expected = base / "a" / "b" / "c" / "d"
            assert result == expected
