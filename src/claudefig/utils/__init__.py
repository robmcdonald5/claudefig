"""Utility modules for claudefig.

This package provides utility functions organized by category:
- paths: Path handling and directory operations
- platform: Platform detection and system operations
- validation: Input validation (see services/validation_service.py)
"""

# Path utilities
from claudefig.utils.paths import ensure_directory, is_git_repository

# Platform utilities
from claudefig.utils.platform import (
    get_editor_command,
    get_platform,
    is_linux,
    is_macos,
    is_windows,
    open_file_in_editor,
    open_folder_in_explorer,
    run_platform_command,
)

__all__ = [
    # Platform
    "get_platform",
    "is_windows",
    "is_macos",
    "is_linux",
    "open_file_in_editor",
    "open_folder_in_explorer",
    "get_editor_command",
    "run_platform_command",
    # Paths
    "ensure_directory",
    "is_git_repository",
]
