"""Utility functions for claudefig."""

from pathlib import Path
from typing import List


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path to ensure exists.
    """
    path.mkdir(parents=True, exist_ok=True)


def append_to_gitignore(repo_path: Path, entries: List[str]) -> None:
    """Append entries to .gitignore file.

    Args:
        repo_path: Path to repository root
        entries: List of gitignore entries to add
    """
    gitignore_path = repo_path / ".gitignore"

    # Read existing content
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text(encoding="utf-8")
        existing_lines = set(existing_content.splitlines())
    else:
        existing_content = ""
        existing_lines = set()

    # Filter out entries that already exist
    new_entries = [entry for entry in entries if entry not in existing_lines]

    if not new_entries:
        return  # Nothing to add

    # Append new entries
    with gitignore_path.open("a", encoding="utf-8") as f:
        if existing_content and not existing_content.endswith("\n"):
            f.write("\n")
        f.write("\n".join(new_entries))
        f.write("\n")


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
