"""Platform detection and system operation utilities for claudefig.

This module provides cross-platform utilities for:
- Platform detection (Windows, macOS, Linux)
- Opening files in system editors
- Opening folders in file explorers
- Getting platform-specific paths and commands
"""

import platform
import subprocess
from pathlib import Path
from typing import Union


def get_platform() -> str:
    """Get the current platform name.

    Returns:
        Platform name: 'Windows', 'Darwin' (macOS), or 'Linux'
    """
    return platform.system()


def is_windows() -> bool:
    """Check if running on Windows.

    Returns:
        True if Windows, False otherwise
    """
    return platform.system() == "Windows"


def is_macos() -> bool:
    """Check if running on macOS.

    Returns:
        True if macOS (Darwin), False otherwise
    """
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if running on Linux.

    Returns:
        True if Linux, False otherwise
    """
    return platform.system() == "Linux"


def open_file_in_editor(file_path: Union[Path, str]) -> bool:
    """Open a file in the system's default editor.

    Args:
        file_path: Path to the file to open

    Returns:
        True if successful, False if failed

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If path is not a file

    Note:
        Uses platform-specific commands:
        - Windows: start (via cmd)
        - macOS: open
        - Linux: xdg-open
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    try:
        system = platform.system()
        if system == "Windows":
            subprocess.run(["start", "", str(file_path)], shell=True, check=False)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(file_path)], check=False)
        else:  # Linux
            subprocess.run(["xdg-open", str(file_path)], check=False)

        return True

    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f"Failed to open file: {e}") from e


def open_folder_in_explorer(folder_path: Union[Path, str], create_if_missing: bool = True) -> bool:
    """Open a folder in the system's file explorer.

    Args:
        folder_path: Path to the folder to open
        create_if_missing: If True, create folder if it doesn't exist

    Returns:
        True if successful, False if failed

    Raises:
        FileNotFoundError: If folder doesn't exist and create_if_missing=False
        OSError: If failed to create or open folder

    Note:
        Uses platform-specific commands:
        - Windows: explorer
        - macOS: open
        - Linux: xdg-open
    """
    folder_path = Path(folder_path)

    # Ensure directory exists
    if not folder_path.exists():
        if create_if_missing:
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise OSError(f"Failed to create folder: {e}") from e
        else:
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")

    try:
        system = platform.system()
        if system == "Windows":
            subprocess.run(["explorer", str(folder_path)], check=False)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)], check=False)
        else:  # Linux
            subprocess.run(["xdg-open", str(folder_path)], check=False)

        return True

    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f"Failed to open folder: {e}") from e


def get_editor_command() -> str | None:
    """Get the system's default text editor command.

    Checks $EDITOR environment variable first, then falls back to
    platform-specific defaults.

    Returns:
        Editor command string, or None if no suitable editor found

    Note:
        Default editors by platform:
        - Windows: notepad
        - macOS: open -e (TextEdit)
        - Linux: nano (or $EDITOR if set)
    """
    import os

    # Check environment variable first
    editor = os.environ.get("EDITOR")
    if editor:
        return editor

    # Platform-specific defaults
    system = platform.system()
    if system == "Windows":
        return "notepad"
    elif system == "Darwin":
        return "open -e"  # TextEdit on macOS
    else:  # Linux
        return "nano"  # Safe fallback


def run_platform_command(
    windows_cmd: list[str],
    macos_cmd: list[str],
    linux_cmd: list[str],
    shell: bool = False,
) -> subprocess.CompletedProcess:
    """Run a platform-specific command.

    Args:
        windows_cmd: Command to run on Windows
        macos_cmd: Command to run on macOS
        linux_cmd: Command to run on Linux
        shell: Whether to run command through shell

    Returns:
        CompletedProcess object from subprocess.run

    Raises:
        RuntimeError: If platform is unknown

    Example:
        >>> run_platform_command(
        ...     windows_cmd=["dir"],
        ...     macos_cmd=["ls", "-la"],
        ...     linux_cmd=["ls", "-la"]
        ... )
    """
    system = platform.system()
    if system == "Windows":
        cmd = windows_cmd
    elif system == "Darwin":
        cmd = macos_cmd
    elif system == "Linux":
        cmd = linux_cmd
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    return subprocess.run(cmd, shell=shell, check=False, capture_output=True)
