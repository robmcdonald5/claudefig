"""Tests for platform detection and system operation utilities."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from claudefig.utils.platform import (
    _command_exists,
    get_editor_command,
    get_platform,
    is_linux,
    is_macos,
    is_windows,
    open_file_in_editor,
    open_folder_in_explorer,
    run_platform_command,
)


class TestPlatformDetection:
    """Tests for platform detection functions."""

    @patch("claudefig.utils.platform._get_system", return_value="Windows")
    def test_is_windows_true(self, mock_system):
        """Test is_windows returns True on Windows."""
        assert is_windows() is True
        assert is_macos() is False
        assert is_linux() is False

    @patch("claudefig.utils.platform._get_system", return_value="Darwin")
    def test_is_macos_true(self, mock_system):
        """Test is_macos returns True on macOS."""
        assert is_macos() is True
        assert is_windows() is False
        assert is_linux() is False

    @patch("claudefig.utils.platform._get_system", return_value="Linux")
    def test_is_linux_true(self, mock_system):
        """Test is_linux returns True on Linux."""
        assert is_linux() is True
        assert is_windows() is False
        assert is_macos() is False

    @patch("claudefig.utils.platform._get_system", return_value="Windows")
    def test_get_platform_windows(self, mock_system):
        """Test get_platform returns correct platform name."""
        assert get_platform() == "Windows"


class TestCommandExists:
    """Tests for _command_exists helper."""

    @patch("shutil.which", return_value="/usr/bin/xdg-open")
    def test_command_exists_true(self, mock_which):
        """Test _command_exists returns True when command found."""
        assert _command_exists("xdg-open") is True
        mock_which.assert_called_once_with("xdg-open")

    @patch("shutil.which", return_value=None)
    def test_command_exists_false(self, mock_which):
        """Test _command_exists returns False when command not found."""
        assert _command_exists("nonexistent-command") is False
        mock_which.assert_called_once_with("nonexistent-command")


class TestOpenFileInEditor:
    """Tests for open_file_in_editor function."""

    @patch("claudefig.utils.platform._get_system", return_value="Windows")
    @patch("claudefig.utils.platform.os.startfile", create=True)
    def test_open_file_windows(self, mock_startfile, mock_system, tmp_path):
        """Test opening file on Windows uses os.startfile() (secure)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = open_file_in_editor(test_file)

        assert result is True
        mock_startfile.assert_called_once_with(str(test_file.resolve()))

    @patch("claudefig.utils.platform._get_system", return_value="Darwin")
    @patch("subprocess.run")
    def test_open_file_macos(self, mock_run, mock_system, tmp_path):
        """Test opening file on macOS uses 'open' command."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        mock_run.return_value = MagicMock(returncode=0)

        result = open_file_in_editor(test_file)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "open"
        assert str(test_file.resolve()) in args

    @patch("claudefig.utils.platform._get_system", return_value="Linux")
    @patch("claudefig.utils.platform._command_exists", return_value=True)
    @patch("subprocess.run")
    def test_open_file_linux_xdg_open(
        self, mock_run, mock_exists, mock_system, tmp_path
    ):
        """Test opening file on Linux uses xdg-open."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        mock_run.return_value = MagicMock(returncode=0)

        result = open_file_in_editor(test_file)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "xdg-open"
        assert str(test_file.resolve()) in args

    @patch("claudefig.utils.platform._get_system", return_value="Linux")
    @patch("claudefig.utils.platform._command_exists")
    @patch("subprocess.run")
    def test_open_file_linux_fallback(
        self, mock_run, mock_exists, mock_system, tmp_path
    ):
        """Test Linux fallback commands when xdg-open not available."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        mock_run.return_value = MagicMock(returncode=0)

        # Simulate xdg-open missing, gnome-open available
        def command_exists_side_effect(cmd):
            return cmd == "gnome-open"

        mock_exists.side_effect = command_exists_side_effect

        result = open_file_in_editor(test_file)

        assert result is True
        assert mock_exists.call_count >= 2  # Tried xdg-open, then gnome-open
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "gnome-open"

    def test_open_file_nonexistent_raises_error(self, tmp_path):
        """Test that opening non-existent file raises FileNotFoundError."""
        nonexistent_file = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError, match="File does not exist"):
            open_file_in_editor(nonexistent_file)

    def test_open_folder_as_file_raises_error(self, tmp_path):
        """Test that opening a folder as file raises ValueError."""
        test_folder = tmp_path / "folder"
        test_folder.mkdir()

        with pytest.raises(ValueError, match="Path is not a file"):
            open_file_in_editor(test_folder)

    @patch("claudefig.utils.platform._get_system", return_value="Darwin")
    @patch("subprocess.run")
    def test_open_file_timeout(self, mock_run, mock_system, tmp_path):
        """Test that subprocess timeout is caught and handled."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        mock_run.side_effect = subprocess.TimeoutExpired("open", 5)

        with pytest.raises(RuntimeError, match="Timeout opening file"):
            open_file_in_editor(test_file)

    @patch("claudefig.utils.platform._get_system", return_value="Windows")
    @patch("claudefig.utils.platform.os.startfile", create=True)
    def test_open_file_windows_error(self, mock_startfile, mock_system, tmp_path):
        """Test error handling when os.startfile fails."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        mock_startfile.side_effect = OSError("Failed to start file")

        with pytest.raises(RuntimeError, match="Failed to open file"):
            open_file_in_editor(test_file)


class TestOpenFolderInExplorer:
    """Tests for open_folder_in_explorer function."""

    @patch("claudefig.utils.platform._get_system", return_value="Windows")
    @patch("subprocess.run")
    def test_open_folder_windows(self, mock_run, mock_system, tmp_path):
        """Test opening folder on Windows uses explorer."""
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir()
        mock_run.return_value = MagicMock(returncode=0)

        result = open_folder_in_explorer(test_folder)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "explorer"
        assert str(test_folder.resolve()) in args

    @patch("claudefig.utils.platform._get_system", return_value="Darwin")
    @patch("subprocess.run")
    def test_open_folder_macos(self, mock_run, mock_system, tmp_path):
        """Test opening folder on macOS uses 'open' command."""
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir()
        mock_run.return_value = MagicMock(returncode=0)

        result = open_folder_in_explorer(test_folder)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "open"

    @patch("claudefig.utils.platform._get_system", return_value="Linux")
    @patch("claudefig.utils.platform._command_exists", return_value=True)
    @patch("subprocess.run")
    def test_open_folder_linux(self, mock_run, mock_exists, mock_system, tmp_path):
        """Test opening folder on Linux uses xdg-open."""
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir()
        mock_run.return_value = MagicMock(returncode=0)

        result = open_folder_in_explorer(test_folder)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "xdg-open"

    @patch("claudefig.utils.platform._get_system", return_value="Linux")
    @patch("subprocess.run")
    def test_open_folder_creates_if_missing(self, mock_run, mock_system, tmp_path):
        """Test that folder is created if create_if_missing=True."""
        test_folder = tmp_path / "new_folder"
        assert not test_folder.exists()
        mock_run.return_value = MagicMock(returncode=0)

        result = open_folder_in_explorer(test_folder, create_if_missing=True)

        assert result is True
        assert test_folder.exists()
        assert test_folder.is_dir()

    def test_open_folder_raises_if_missing_and_not_create(self, tmp_path):
        """Test that FileNotFoundError raised if folder missing and create_if_missing=False."""
        test_folder = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError, match="Folder does not exist"):
            open_folder_in_explorer(test_folder, create_if_missing=False)

    @patch("claudefig.utils.platform._get_system", return_value="Windows")
    @patch("subprocess.run")
    def test_open_folder_timeout(self, mock_run, mock_system, tmp_path):
        """Test that subprocess timeout is caught and handled."""
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir()
        mock_run.side_effect = subprocess.TimeoutExpired("explorer", 5)

        with pytest.raises(RuntimeError, match="Timeout opening folder"):
            open_folder_in_explorer(test_folder)


class TestGetEditorCommand:
    """Tests for get_editor_command function."""

    @patch.dict("os.environ", {"VISUAL": "emacs"}, clear=True)
    def test_get_editor_visual(self):
        """Test that $VISUAL is checked first."""
        editor = get_editor_command()
        assert editor == "emacs"

    @patch.dict("os.environ", {"EDITOR": "vim"}, clear=True)
    def test_get_editor_editor(self):
        """Test that $EDITOR is checked second."""
        editor = get_editor_command()
        assert editor == "vim"

    @patch.dict("os.environ", {"VISUAL": "emacs", "EDITOR": "vim"}, clear=True)
    def test_get_editor_visual_takes_precedence(self):
        """Test that $VISUAL takes precedence over $EDITOR."""
        editor = get_editor_command()
        assert editor == "emacs"

    @patch.dict("os.environ", {}, clear=True)
    @patch("claudefig.utils.platform._get_system", return_value="Windows")
    def test_get_editor_windows_default(self, mock_system):
        """Test Windows default editor is notepad.exe."""
        editor = get_editor_command()
        assert editor == "notepad.exe"

    @patch.dict("os.environ", {}, clear=True)
    @patch("claudefig.utils.platform._get_system", return_value="Darwin")
    def test_get_editor_macos_default(self, mock_system):
        """Test macOS default editor is nano."""
        editor = get_editor_command()
        assert editor == "nano"

    @patch.dict("os.environ", {}, clear=True)
    @patch("claudefig.utils.platform._get_system", return_value="Linux")
    def test_get_editor_linux_default(self, mock_system):
        """Test Linux default editor is nano."""
        editor = get_editor_command()
        assert editor == "nano"


class TestRunPlatformCommand:
    """Tests for run_platform_command function."""

    @patch("claudefig.utils.platform._get_system", return_value="Windows")
    @patch("subprocess.run")
    def test_run_platform_command_windows(self, mock_run, mock_system):
        """Test that Windows command is run on Windows platform."""
        mock_run.return_value = MagicMock(returncode=0)

        run_platform_command(
            windows_cmd=["cmd", "/c", "dir"],
            macos_cmd=["ls", "-la"],
            linux_cmd=["ls", "-la"],
        )

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["cmd", "/c", "dir"]

    @patch("claudefig.utils.platform._get_system", return_value="Darwin")
    @patch("subprocess.run")
    def test_run_platform_command_macos(self, mock_run, mock_system):
        """Test that macOS command is run on macOS platform."""
        mock_run.return_value = MagicMock(returncode=0)

        run_platform_command(
            windows_cmd=["dir"],
            macos_cmd=["ls", "-la"],
            linux_cmd=["ls", "-l"],
        )

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["ls", "-la"]

    @patch("claudefig.utils.platform._get_system", return_value="Linux")
    @patch("subprocess.run")
    def test_run_platform_command_linux(self, mock_run, mock_system):
        """Test that Linux command is run on Linux platform."""
        mock_run.return_value = MagicMock(returncode=0)

        run_platform_command(
            windows_cmd=["dir"],
            macos_cmd=["ls"],
            linux_cmd=["ls", "-la"],
        )

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["ls", "-la"]

    @patch("claudefig.utils.platform._get_system", return_value="FreeBSD")
    def test_run_platform_command_unsupported(self, mock_system):
        """Test that unsupported platform raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Unsupported platform"):
            run_platform_command(
                windows_cmd=["dir"],
                macos_cmd=["ls"],
                linux_cmd=["ls"],
            )

    @patch("claudefig.utils.platform._get_system", return_value="Windows")
    @patch("subprocess.run")
    def test_run_platform_command_with_timeout(self, mock_run, mock_system):
        """Test that custom timeout is passed to subprocess."""
        mock_run.return_value = MagicMock(returncode=0)

        run_platform_command(
            windows_cmd=["cmd", "/c", "dir"],
            macos_cmd=["ls"],
            linux_cmd=["ls"],
            timeout=10,
        )

        mock_run.assert_called_once()
        assert mock_run.call_args[1]["timeout"] == 10
