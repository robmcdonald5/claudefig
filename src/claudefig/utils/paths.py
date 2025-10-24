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


def find_file_upwards(
    start_path: Path, filename: str, max_levels: int = 10
) -> Path | None:
    """Search for a file by walking up the directory tree.

    Args:
        start_path: Starting directory
        filename: Name of file to find
        max_levels: Maximum number of parent directories to check

    Returns:
        Path to file if found, None otherwise

    Example:
        >>> find_file_upwards(Path.cwd(), ".claudefig.toml")
        Path("/projects/my-repo/.claudefig.toml")
    """
    current = start_path.resolve()
    levels = 0

    while current != current.parent and levels < max_levels:
        candidate = current / filename
        if candidate.exists():
            return candidate
        current = current.parent
        levels += 1

    return None


def is_subdirectory(child: Path, parent: Path) -> bool:
    """Check if child is a subdirectory of parent.

    Args:
        child: Potential child directory
        parent: Potential parent directory

    Returns:
        True if child is under parent, False otherwise

    Example:
        >>> is_subdirectory(Path("/a/b/c"), Path("/a"))
        True
        >>> is_subdirectory(Path("/x/y"), Path("/a"))
        False
    """
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def get_relative_path(path: Path, base: Path) -> Path:
    """Get relative path from base to path.

    Args:
        path: Target path
        base: Base path

    Returns:
        Relative path from base to path

    Raises:
        ValueError: If path is not relative to base

    Example:
        >>> get_relative_path(Path("/a/b/c/file.txt"), Path("/a/b"))
        Path("c/file.txt")
    """
    return path.resolve().relative_to(base.resolve())


def safe_path_join(base: Path, *parts: str) -> Path:
    """Safely join path components, preventing directory traversal.

    Args:
        base: Base directory path
        *parts: Path components to join

    Returns:
        Joined path

    Raises:
        ValueError: If resulting path would escape base directory

    Example:
        >>> safe_path_join(Path("/base"), "subdir", "file.txt")
        Path("/base/subdir/file.txt")
        >>> safe_path_join(Path("/base"), "../etc/passwd")  # Raises ValueError
    """
    result = base
    for part in parts:
        result = result / part

    # Ensure result is under base
    if not is_subdirectory(result, base):
        raise ValueError(f"Path '{result}' escapes base directory '{base}'")

    return result
