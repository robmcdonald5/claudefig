"""Tests for utility functions in claudefig.utils.paths."""

from pathlib import Path
from unittest.mock import patch

import pytest

from claudefig.utils.paths import ensure_directory, is_git_repository


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "test_dir"
        assert not new_dir.exists()

        ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_nested_directories(self, tmp_path):
        """Test creating nested directories with parents=True."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()

        ensure_directory(nested_dir)

        assert nested_dir.exists()
        assert nested_dir.is_dir()
        # Verify all parent directories were created
        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()

    def test_directory_already_exists(self, tmp_path):
        """Test that existing directory doesn't raise error (exist_ok=True)."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        assert existing_dir.exists()

        # Should not raise an error
        ensure_directory(existing_dir)

        assert existing_dir.exists()
        assert existing_dir.is_dir()

    def test_directory_with_file_conflict(self, tmp_path):
        """Test behavior when a file exists with the same name as target directory."""
        file_path = tmp_path / "conflicting_name"
        file_path.write_text("I am a file", encoding="utf-8")
        assert file_path.is_file()

        # Should raise error because a file exists with this name
        with pytest.raises(FileExistsError):
            ensure_directory(file_path)

    def test_permission_denied_simulation(self, tmp_path):
        """Test handling when permission is denied (simulated)."""
        restricted_dir = tmp_path / "restricted"

        # Mock mkdir to raise PermissionError
        with (
            patch.object(Path, "mkdir", side_effect=PermissionError("Access denied")),
            pytest.raises(PermissionError),
        ):
            ensure_directory(restricted_dir)


class TestIsGitRepository:
    """Tests for is_git_repository function."""

    def test_is_git_repo_root(self, tmp_path):
        """Test when .git directory is in the current directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = is_git_repository(tmp_path)

        assert result is True

    def test_is_git_repo_subdirectory(self, tmp_path):
        """Test when .git directory is in a parent directory."""
        # Create .git in root
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Test from a subdirectory
        subdir = tmp_path / "src" / "claudefig"
        subdir.mkdir(parents=True)

        result = is_git_repository(subdir)

        assert result is True

    def test_is_git_repo_multiple_levels(self, tmp_path):
        """Test walking up multiple directory levels to find .git."""
        # Create .git in root
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Test from deeply nested directory
        deep_dir = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_dir.mkdir(parents=True)

        result = is_git_repository(deep_dir)

        assert result is True

    def test_not_git_repo(self, tmp_path):
        """Test when no .git directory exists in hierarchy."""
        # tmp_path has no .git directory
        subdir = tmp_path / "not_a_repo"
        subdir.mkdir()

        result = is_git_repository(subdir)

        assert result is False

    def test_walks_up_to_filesystem_root(self, tmp_path):
        """Test that function stops at filesystem root without infinite loop."""
        # Create a directory with no .git anywhere
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        result = is_git_repository(test_dir)

        # Should return False and not hang or crash
        assert result is False

    def test_handles_symlinks(self, tmp_path):
        """Test behavior with symlinks in path."""
        # Create actual directory with .git
        real_dir = tmp_path / "real_repo"
        real_dir.mkdir()
        git_dir = real_dir / ".git"
        git_dir.mkdir()

        # Create symlink to the real directory
        link_dir = tmp_path / "link_to_repo"

        try:
            link_dir.symlink_to(real_dir, target_is_directory=True)
        except OSError:
            # Skip test on Windows without admin privileges
            pytest.skip("Symlink creation requires elevated privileges on Windows")

        # Test from symlinked directory
        result = is_git_repository(link_dir)

        # Should resolve symlink and find .git
        assert result is True

    def test_git_file_not_directory(self, tmp_path):
        """Test when .git is a file (not a directory) - worktree case."""
        # In git worktrees, .git can be a file pointing to the real git directory
        git_file = tmp_path / ".git"
        git_file.write_text("gitdir: /path/to/real/git", encoding="utf-8")

        result = is_git_repository(tmp_path)

        # Should still return True because .git exists
        assert result is True

    def test_current_directory_is_parent_edge_case(self, tmp_path):
        """Test edge case handling when current == parent (filesystem root)."""
        # This tests the loop termination condition: while current != current.parent
        # At filesystem root, current.parent returns current
        result = is_git_repository(tmp_path)

        # Should return False or True depending on if tmp_path has .git
        # In any case, should not infinite loop
        assert isinstance(result, bool)
