"""Utility functions for claudefig."""

from pathlib import Path


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path to ensure exists.
    """
    path.mkdir(parents=True, exist_ok=True)


def is_git_repository(path: Path) -> bool:
    """Check if path is inside a git repository.

    Args:
        path: Path to check

    Returns:
        True if path is in a git repository, False otherwise.
    """
    current = path.resolve()

    while current != current.parent:
        if (current / ".git").exists():
            return True
        current = current.parent

    return False
