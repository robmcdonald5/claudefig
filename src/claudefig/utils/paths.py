"""Path handling utilities for claudefig.

This module provides utilities for:
- Directory creation and management
- Git repository detection
- Path resolution and validation
"""

from pathlib import Path


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path to ensure exists.

    Raises:
        OSError: If failed to create directory
    """
    path.mkdir(parents=True, exist_ok=True)


def is_git_repository(path: Path) -> bool:
    """Check if path is inside a git repository.

    Walks up the directory tree looking for a .git directory.

    Args:
        path: Path to check

    Returns:
        True if path is in a git repository, False otherwise.

    Example:
        >>> is_git_repository(Path("/projects/my-repo/src"))
        True
        >>> is_git_repository(Path("/tmp"))
        False
    """
    current = path.resolve()

    while current != current.parent:
        if (current / ".git").exists():
            return True
        current = current.parent

    return False
