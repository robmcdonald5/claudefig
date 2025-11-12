"""Platform detection and system operation utilities for claudefig.

This module provides cross-platform utilities for:
- Platform detection (Windows, macOS, Linux)
- Opening files in system editors
- Opening folders in file explorers
- Getting platform-specific paths and commands
"""

import os
import platform
import subprocess
from pathlib import Path


def _get_system() -> str:
    """Get the current platform name (wrapper for testing).

    This wrapper function enables mocking platform.system() in unit tests.

    Returns:
        Platform name: 'Windows', 'Darwin' (macOS), or 'Linux'
    """
    return platform.system()


def _command_exists(command: str) -> bool:
    """Check if a command exists in PATH.

    Args:
        command: Command name to check (e.g., 'xdg-open', 'gnome-open')

    Returns:
        True if command is available in PATH, False otherwise
    """
    from shutil import which

    return which(command) is not None


def get_platform() -> str:
    """Get the current platform name.

    Returns:
        Platform name: 'Windows', 'Darwin' (macOS), or 'Linux'
    """
    return _get_system()


def is_windows() -> bool:
    """Check if running on Windows.

    Returns:
        True if Windows, False otherwise
    """
    return _get_system() == "Windows"


def is_macos() -> bool:
    """Check if running on macOS.

    Returns:
        True if macOS (Darwin), False otherwise
    """
    return _get_system() == "Darwin"


def is_linux() -> bool:
    """Check if running on Linux.

    Returns:
        True if Linux, False otherwise
    """
    return _get_system() == "Linux"


def open_file_in_editor(file_path: Path | str) -> bool:
    """Open a file in the system's default editor.

    Args:
        file_path: Path to the file to open

    Returns:
        True if successful

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If path is not a file
        RuntimeError: If failed to open file or timeout occurred
    """
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    try:
        system = _get_system()

        if system == "Windows":
            os.startfile(str(file_path))

        elif system == "Darwin":
            subprocess.run(
                ["open", str(file_path)],
                check=False,
                capture_output=True,
                timeout=5,
            )

        else:
            for cmd in ["xdg-open", "gnome-open", "kde-open"]:
                if _command_exists(cmd):
                    subprocess.run(
                        [cmd, str(file_path)],
                        check=False,
                        capture_output=True,
                        timeout=5,
                    )
                    break

        return True

    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Timeout opening file (exceeded 5 seconds): {e}") from e
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f"Failed to open file: {e}") from e


def open_folder_in_explorer(
    folder_path: Path | str, create_if_missing: bool = True
) -> bool:
    """Open a folder in the system's file explorer.

    Args:
        folder_path: Path to the folder to open
        create_if_missing: If True, create folder if it doesn't exist

    Returns:
        True if successful

    Raises:
        FileNotFoundError: If folder doesn't exist and create_if_missing=False
        OSError: If failed to create folder
        RuntimeError: If failed to open folder or timeout occurred
    """
    folder_path = Path(folder_path).resolve()

    if not folder_path.exists():
        if create_if_missing:
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise OSError(f"Failed to create folder: {e}") from e
        else:
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")

    try:
        system = _get_system()

        if system == "Windows":
            subprocess.run(
                ["explorer", str(folder_path)],
                check=False,
                capture_output=True,
                timeout=5,
            )

        elif system == "Darwin":
            subprocess.run(
                ["open", str(folder_path)],
                check=False,
                capture_output=True,
                timeout=5,
            )

        else:
            for cmd in ["xdg-open", "gnome-open", "kde-open"]:
                if _command_exists(cmd):
                    subprocess.run(
                        [cmd, str(folder_path)],
                        check=False,
                        capture_output=True,
                        timeout=5,
                    )
                    break

        return True

    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Timeout opening folder (exceeded 5 seconds): {e}") from e
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f"Failed to open folder: {e}") from e


def get_editor_command() -> str:
    """Get the system's default text editor command.

    Checks environment variables in order:
    1. $VISUAL (preferred by POSIX)
    2. $EDITOR (standard fallback)
    3. Platform-specific defaults

    Returns:
        Editor command string

    Note:
        Default editors by platform:
        - Windows: notepad.exe
        - macOS: nano
        - Linux: nano
    """
    visual = os.environ.get("VISUAL")
    if visual:
        return visual

    editor = os.environ.get("EDITOR")
    if editor:
        return editor

    # Platform-specific defaults
    system = _get_system()
    if system == "Windows":
        return "notepad.exe"
    elif system == "Darwin":
        return "nano"
    else:
        return "nano"


def run_platform_command(
    windows_cmd: list[str],
    macos_cmd: list[str],
    linux_cmd: list[str],
    shell: bool = False,
    timeout: int | None = 5,
) -> subprocess.CompletedProcess:
    """Run a platform-specific command.

    Args:
        windows_cmd: Command to run on Windows
        macos_cmd: Command to run on macOS
        linux_cmd: Command to run on Linux
        shell: Whether to run command through shell (default: False)
        timeout: Timeout in seconds (default: 5, None for no timeout)

    Returns:
        CompletedProcess object from subprocess.run

    Raises:
        RuntimeError: If platform is unsupported

    Example:
        >>> run_platform_command(
        ...     windows_cmd=["cmd", "/c", "dir"],
        ...     macos_cmd=["ls", "-la"],
        ...     linux_cmd=["ls", "-la"],
        ...     timeout=10
        ... )
    """
    system = _get_system()

    if system == "Windows":
        cmd = windows_cmd
    elif system == "Darwin":
        cmd = macos_cmd
    elif system == "Linux":
        cmd = linux_cmd
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    return subprocess.run(
        cmd,
        shell=shell,
        check=False,
        capture_output=True,
        timeout=timeout,
    )
