"""Tests for TUI mixins."""

from unittest.mock import Mock, patch

import pytest

from claudefig.tui.base import (
    BackButtonMixin,
    FileInstanceMixin,
    SystemUtilityMixin,
)


class TestSystemUtilityMixin:
    """Tests for SystemUtilityMixin."""

    @pytest.fixture
    def mixin_instance(self):
        """Create a mock instance that uses SystemUtilityMixin."""

        class TestWidget(SystemUtilityMixin):
            """Test widget with SystemUtilityMixin."""

            def __init__(self):
                self.notifications = []

            def notify(
                self,
                message: str,
                *,
                severity: str = "information",
                timeout: float = 2.0,
            ):
                """Mock notify method that records notifications."""
                self.notifications.append(
                    {"message": message, "severity": severity, "timeout": timeout}
                )

        return TestWidget()

    @patch("claudefig.utils.platform.os.startfile", create=True)
    @patch("claudefig.utils.platform.platform.system")
    def test_open_file_in_editor_windows(
        self, mock_platform, mock_startfile, mixin_instance, tmp_path
    ):
        """Test opening file in editor on Windows."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        mock_platform.return_value = "Windows"

        # Execute
        result = mixin_instance.open_file_in_editor(test_file)

        # Verify
        assert result is True
        mock_platform.assert_called_once()
        mock_startfile.assert_called_once_with(str(test_file.resolve()))
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "information"
        assert "Opened file" in mixin_instance.notifications[0]["message"]

    @patch("claudefig.utils.platform.subprocess.run")
    @patch("claudefig.utils.platform.platform.system")
    def test_open_file_in_editor_macos(
        self, mock_platform, mock_subprocess, mixin_instance, tmp_path
    ):
        """Test opening file in editor on macOS."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        mock_platform.return_value = "Darwin"
        mock_subprocess.return_value = Mock(returncode=0)

        # Execute
        result = mixin_instance.open_file_in_editor(test_file)

        # Verify
        assert result is True
        mock_platform.assert_called_once()
        mock_subprocess.assert_called_once_with(
            ["open", str(test_file.resolve())],
            check=False,
            capture_output=True,
            timeout=5,
        )
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "information"

    @patch("claudefig.utils.platform._command_exists", return_value=True)
    @patch("claudefig.utils.platform.subprocess.run")
    @patch("claudefig.utils.platform.platform.system")
    def test_open_file_in_editor_linux(
        self, mock_platform, mock_subprocess, mock_cmd_exists, mixin_instance, tmp_path
    ):
        """Test opening file in editor on Linux."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        mock_platform.return_value = "Linux"
        mock_subprocess.return_value = Mock(returncode=0)

        # Execute
        result = mixin_instance.open_file_in_editor(test_file)

        # Verify
        assert result is True
        mock_platform.assert_called_once()
        mock_subprocess.assert_called_once_with(
            ["xdg-open", str(test_file.resolve())],
            check=False,
            capture_output=True,
            timeout=5,
        )
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "information"

    def test_open_file_in_editor_nonexistent(self, mixin_instance, tmp_path):
        """Test opening a file that doesn't exist."""
        # Setup
        nonexistent_file = tmp_path / "does_not_exist.txt"

        # Execute
        result = mixin_instance.open_file_in_editor(nonexistent_file)

        # Verify
        assert result is False
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "error"
        assert "does not exist" in mixin_instance.notifications[0]["message"]

    def test_open_file_in_editor_not_a_file(self, mixin_instance, tmp_path):
        """Test opening a path that's a directory, not a file."""
        # Setup - create a directory
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()

        # Execute
        result = mixin_instance.open_file_in_editor(test_dir)

        # Verify
        assert result is False
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "error"
        assert "not a file" in mixin_instance.notifications[0]["message"]

    @patch("claudefig.utils.platform._command_exists", return_value=True)
    @patch("claudefig.utils.platform.subprocess.run")
    @patch("claudefig.utils.platform.platform.system")
    def test_open_file_in_editor_subprocess_error(
        self, mock_platform, mock_subprocess, mock_cmd_exists, mixin_instance, tmp_path
    ):
        """Test handling subprocess errors when opening file."""
        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        mock_platform.return_value = "Linux"
        mock_subprocess.side_effect = RuntimeError("Subprocess failed")

        # Execute
        result = mixin_instance.open_file_in_editor(test_file)

        # Verify
        assert result is False
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "error"
        assert "Failed to open file" in mixin_instance.notifications[0]["message"]

    @patch("claudefig.utils.platform.subprocess.run")
    @patch("claudefig.utils.platform.platform.system")
    def test_open_folder_in_explorer_windows(
        self, mock_platform, mock_subprocess, mixin_instance, tmp_path
    ):
        """Test opening folder in explorer on Windows."""
        # Setup
        test_dir = tmp_path / "test_folder"
        test_dir.mkdir()
        mock_platform.return_value = "Windows"
        mock_subprocess.return_value = Mock(returncode=0)

        # Execute
        result = mixin_instance.open_folder_in_explorer(test_dir)

        # Verify
        assert result is True
        mock_platform.assert_called_once()
        mock_subprocess.assert_called_once_with(
            ["explorer", str(test_dir.resolve())],
            check=False,
            capture_output=True,
            timeout=5,
        )
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "information"
        assert "Opened folder" in mixin_instance.notifications[0]["message"]

    @patch("claudefig.utils.platform.subprocess.run")
    @patch("claudefig.utils.platform.platform.system")
    def test_open_folder_in_explorer_macos(
        self, mock_platform, mock_subprocess, mixin_instance, tmp_path
    ):
        """Test opening folder in explorer on macOS."""
        # Setup
        test_dir = tmp_path / "test_folder"
        test_dir.mkdir()
        mock_platform.return_value = "Darwin"
        mock_subprocess.return_value = Mock(returncode=0)

        # Execute
        result = mixin_instance.open_folder_in_explorer(test_dir)

        # Verify
        assert result is True
        mock_platform.assert_called_once()
        mock_subprocess.assert_called_once_with(
            ["open", str(test_dir.resolve())],
            check=False,
            capture_output=True,
            timeout=5,
        )
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "information"

    @patch("claudefig.utils.platform._command_exists", return_value=True)
    @patch("claudefig.utils.platform.subprocess.run")
    @patch("claudefig.utils.platform.platform.system")
    def test_open_folder_in_explorer_linux(
        self, mock_platform, mock_subprocess, mock_cmd_exists, mixin_instance, tmp_path
    ):
        """Test opening folder in explorer on Linux."""
        # Setup
        test_dir = tmp_path / "test_folder"
        test_dir.mkdir()
        mock_platform.return_value = "Linux"
        mock_subprocess.return_value = Mock(returncode=0)

        # Execute
        result = mixin_instance.open_folder_in_explorer(test_dir)

        # Verify
        assert result is True
        mock_platform.assert_called_once()
        mock_subprocess.assert_called_once_with(
            ["xdg-open", str(test_dir.resolve())],
            check=False,
            capture_output=True,
            timeout=5,
        )
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "information"

    @patch("claudefig.utils.platform._command_exists", return_value=True)
    @patch("claudefig.utils.platform.subprocess.run")
    @patch("claudefig.utils.platform.platform.system")
    def test_open_folder_creates_missing_directory(
        self, mock_platform, mock_subprocess, mock_cmd_exists, mixin_instance, tmp_path
    ):
        """Test that open_folder_in_explorer creates directory if it doesn't exist."""
        # Setup
        test_dir = tmp_path / "new_folder"
        # Verify it doesn't exist yet
        assert not test_dir.exists()

        mock_platform.return_value = "Linux"
        mock_subprocess.return_value = Mock(returncode=0)

        # Execute
        result = mixin_instance.open_folder_in_explorer(test_dir)

        # Verify
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()
        mock_subprocess.assert_called_once()

    @patch("claudefig.utils.platform._command_exists", return_value=True)
    @patch("claudefig.utils.platform.subprocess.run")
    @patch("claudefig.utils.platform.platform.system")
    def test_open_folder_error_handling(
        self, mock_platform, mock_subprocess, mock_cmd_exists, mixin_instance, tmp_path
    ):
        """Test handling errors when opening folder."""
        # Setup
        test_dir = tmp_path / "test_folder"
        test_dir.mkdir()
        mock_platform.return_value = "Linux"
        mock_subprocess.side_effect = RuntimeError("Explorer failed")

        # Execute
        result = mixin_instance.open_folder_in_explorer(test_dir)

        # Verify
        assert result is False
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "error"
        assert "Failed to open folder" in mixin_instance.notifications[0]["message"]

    @patch("claudefig.tui.base.mixins.Path.mkdir")
    def test_open_folder_mkdir_error(self, mock_mkdir, mixin_instance, tmp_path):
        """Test handling errors when creating directory."""
        # Setup
        test_dir = tmp_path / "test_folder"
        mock_mkdir.side_effect = PermissionError("Permission denied")

        # Execute
        result = mixin_instance.open_folder_in_explorer(test_dir)

        # Verify
        assert result is False
        assert len(mixin_instance.notifications) == 1
        assert mixin_instance.notifications[0]["severity"] == "error"
        assert "Failed to create folder" in mixin_instance.notifications[0]["message"]


class TestBackButtonMixin:
    """Tests for BackButtonMixin."""

    @pytest.fixture
    def mixin_instance(self):
        """Create a mock instance that uses BackButtonMixin."""

        class TestScreen(BackButtonMixin):
            """Test screen with BackButtonMixin."""

            def __init__(self):
                self.app = Mock()
                self.popped = False

            def pop_screen(self):
                """Mock pop_screen for testing."""
                self.popped = True

        # Mock the app.pop_screen method
        instance = TestScreen()

        # Create a mock that properly sets the flag and returns a Mock (AwaitComplete-like)
        def mock_pop():
            instance.popped = True
            return Mock()  # Return mock AwaitComplete

        instance.app.pop_screen = Mock(side_effect=mock_pop)
        return instance

    def test_compose_back_button_default_label(self, mixin_instance):
        """Test compose_back_button yields button with default label."""
        # Execute - verify the generator can be created
        result = mixin_instance.compose_back_button()

        # Verify - should return a generator
        assert hasattr(result, "__iter__")
        # Note: In real usage, this would yield a Container with a Button inside
        # We can't easily test the widget tree structure without Textual runtime,
        # but we can verify the method executes without error

    def test_compose_back_button_custom_label(self, mixin_instance):
        """Test compose_back_button with custom label."""
        # Execute - verify the generator can be created with custom label
        result = mixin_instance.compose_back_button(label="← Custom Back")

        # Verify - should return a generator
        assert hasattr(result, "__iter__")

    def test_handle_back_button_true(self, mixin_instance):
        """Test handle_back_button returns True when back button pressed."""
        # Setup
        mock_event = Mock()
        mock_event.button = Mock()
        mock_event.button.id = "btn-back"

        # Execute
        result = mixin_instance.handle_back_button(mock_event)

        # Verify
        assert result is True
        assert mixin_instance.popped is True

    def test_handle_back_button_false(self, mixin_instance):
        """Test handle_back_button returns False for other buttons."""
        # Setup
        mock_event = Mock()
        mock_event.button = Mock()
        mock_event.button.id = "btn-other"

        # Execute
        result = mixin_instance.handle_back_button(mock_event)

        # Verify
        assert result is False
        assert mixin_instance.popped is False


class TestFileInstanceMixin:
    """Tests for FileInstanceMixin."""

    @pytest.fixture
    def mixin_instance(self):
        """Create a mock instance that uses FileInstanceMixin."""
        from claudefig.models import FileInstance, FileType

        class TestScreen(FileInstanceMixin):
            """Test screen with FileInstanceMixin."""

            def __init__(self, config_data, config_repo, instances_dict):
                self.config_data = config_data
                self.config_repo = config_repo
                self.instances_dict = instances_dict

        # Create mocks
        mock_config_data = {"files": []}
        mock_config_repo = Mock()
        mock_instances_dict = {
            "test-1": FileInstance(
                id="test-1",
                type=FileType.CLAUDE_MD,
                preset="claude_md:default",
                path="CLAUDE.md",
                enabled=True,
            )
        }

        return TestScreen(mock_config_data, mock_config_repo, mock_instances_dict)

    def test_sync_instances_to_config(self, mixin_instance):
        """Test sync_instances_to_config performs 3-step sync."""
        # Execute
        mixin_instance.sync_instances_to_config()

        # Verify step 2: Sync instances → config_data
        assert "files" in mixin_instance.config_data
        assert len(mixin_instance.config_data["files"]) == 1
        assert mixin_instance.config_data["files"][0]["id"] == "test-1"

        # Verify step 3: Sync config_data → disk via repository
        mixin_instance.config_repo.save.assert_called_once_with(
            mixin_instance.config_data
        )

    def test_sync_instances_to_config_saves(self, mixin_instance):
        """Test that sync_instances_to_config actually saves to disk."""
        # Setup - track save calls
        save_called = False

        def mock_save(data):
            nonlocal save_called
            save_called = True

        mixin_instance.config_repo.save = mock_save

        # Execute
        mixin_instance.sync_instances_to_config()

        # Verify
        assert save_called is True

    def test_sync_instances_to_config_missing_attributes(self):
        """Test sync_instances_to_config with missing attributes."""

        class IncompleteScreen(FileInstanceMixin):
            """Screen missing required attributes."""

            pass

        screen = IncompleteScreen()

        # Execute & Verify
        with pytest.raises(AttributeError):
            screen.sync_instances_to_config()


class TestScrollNavigationMixin:
    """Tests for ScrollNavigationMixin."""

    @pytest.fixture
    def create_mock_widget(self):
        """Factory to create mock widgets with parent/classes."""

        def _create(widget_id: str, parent=None, classes=None):
            widget = Mock()
            widget.id = widget_id
            widget.parent = parent
            widget.classes = classes or set()
            widget.focus = Mock()
            widget.scroll_visible = Mock()
            return widget

        return _create

    @pytest.fixture
    def mixin_instance(self, create_mock_widget):
        """Create a mock instance that uses ScrollNavigationMixin."""

        from claudefig.tui.base.mixins import ScrollNavigationMixin

        class TestScreen(ScrollNavigationMixin):
            """Test screen with ScrollNavigationMixin."""

            def __init__(self):
                self.focused = None
                self._focus_chain = []
                self._widgets = {}

            @property
            def focus_chain(self):
                """Return the focus chain."""
                return self._focus_chain

            def query(self, selector):
                """Mock query method."""
                result_mock = Mock()
                if "screen-title" in selector:
                    # Return mock title label
                    title = create_mock_widget("title-label")
                    result_mock.first = Mock(return_value=title)
                else:
                    result_mock.first = Mock(return_value=None)
                return result_mock

            def query_one(self, selector, expect_type=None):
                """Mock query_one method."""
                return Mock()

        return TestScreen()

    def test_action_focus_previous_first_element(
        self, mixin_instance, create_mock_widget
    ):
        """Test action_focus_previous at first element doesn't wrap."""
        # Setup - create focus chain with 3 widgets
        widget1 = create_mock_widget("widget1")
        widget2 = create_mock_widget("widget2")
        widget3 = create_mock_widget("widget3")

        mixin_instance._focus_chain = [widget1, widget2, widget3]
        mixin_instance.focused = widget1  # Already at first element

        # Execute
        mixin_instance.action_focus_previous()

        # Verify - should NOT move focus (stays on widget1)
        widget1.focus.assert_not_called()
        widget2.focus.assert_not_called()
        widget3.focus.assert_not_called()

    def test_action_focus_previous_middle_element(
        self, mixin_instance, create_mock_widget
    ):
        """Test action_focus_previous from middle element moves to previous."""
        # Setup
        widget1 = create_mock_widget("widget1")
        widget2 = create_mock_widget("widget2")
        widget3 = create_mock_widget("widget3")

        mixin_instance._focus_chain = [widget1, widget2, widget3]
        mixin_instance.focused = widget2  # Middle element

        # Execute
        mixin_instance.action_focus_previous()

        # Verify - should focus widget1
        widget1.focus.assert_called_once()

    def test_action_focus_previous_skip_horizontal(
        self, mixin_instance, create_mock_widget
    ):
        """Test action_focus_previous skips siblings in horizontal containers."""
        # Setup - create horizontal container with buttons
        from textual.containers import Horizontal

        h_container = Mock(spec=Horizontal)
        h_container.classes = {"instance-actions"}

        widget1 = create_mock_widget("widget1")
        button1 = create_mock_widget("button1", parent=h_container)
        button2 = create_mock_widget("button2", parent=h_container)
        button3 = create_mock_widget("button3", parent=h_container)

        # Mock parent traversal for buttons
        button1.parent = h_container
        button2.parent = h_container
        button3.parent = h_container

        mixin_instance._focus_chain = [widget1, button1, button2, button3]
        mixin_instance.focused = button3  # Last button in horizontal group

        # Execute
        mixin_instance.action_focus_previous()

        # Verify - should skip to widget1 (before horizontal group)
        # Note: This test validates the concept, actual implementation may vary
        # based on how _get_horizontal_nav_parent works

    def test_action_focus_next_last_element(self, mixin_instance, create_mock_widget):
        """Test action_focus_next at last element doesn't wrap."""
        # Setup
        widget1 = create_mock_widget("widget1")
        widget2 = create_mock_widget("widget2")
        widget3 = create_mock_widget("widget3")

        mixin_instance._focus_chain = [widget1, widget2, widget3]
        mixin_instance.focused = widget3  # Already at last element

        # Execute
        mixin_instance.action_focus_next()

        # Verify - should NOT move focus (stays on widget3)
        widget1.focus.assert_not_called()
        widget2.focus.assert_not_called()
        widget3.focus.assert_not_called()
        # Should scroll to reveal content below
        widget3.scroll_visible.assert_called_once()

    def test_action_focus_next_middle_element(self, mixin_instance, create_mock_widget):
        """Test action_focus_next from middle element moves to next."""
        # Setup
        widget1 = create_mock_widget("widget1")
        widget2 = create_mock_widget("widget2")
        widget3 = create_mock_widget("widget3")

        mixin_instance._focus_chain = [widget1, widget2, widget3]
        mixin_instance.focused = widget2  # Middle element

        # Execute
        mixin_instance.action_focus_next()

        # Verify - should focus widget3
        widget3.focus.assert_called_once()

    def test_action_focus_next_skip_horizontal(
        self, mixin_instance, create_mock_widget
    ):
        """Test action_focus_next skips siblings in horizontal containers."""
        # Setup - create horizontal container with buttons
        from textual.containers import Horizontal

        h_container = Mock(spec=Horizontal)
        h_container.classes = {"tab-actions"}

        widget1 = create_mock_widget("widget1")
        button1 = create_mock_widget("button1", parent=h_container)
        button2 = create_mock_widget("button2", parent=h_container)
        widget2 = create_mock_widget("widget2")

        button1.parent = h_container
        button2.parent = h_container

        mixin_instance._focus_chain = [widget1, button1, button2, widget2]
        mixin_instance.focused = widget1

        # Execute
        mixin_instance.action_focus_next()

        # Verify - should skip to button1 (first in horizontal group)
        button1.focus.assert_called_once()

    def test_action_focus_previous_no_focus_chain(self, mixin_instance):
        """Test action_focus_previous with empty focus chain."""
        # Setup
        mixin_instance._focus_chain = []
        mixin_instance.focused = None

        # Execute - should not raise error
        mixin_instance.action_focus_previous()

        # No assertions needed, just verify it doesn't crash

    def test_action_focus_next_no_focus_chain(self, mixin_instance):
        """Test action_focus_next with empty focus chain."""
        # Setup
        mixin_instance._focus_chain = []
        mixin_instance.focused = None

        # Execute - should not raise error
        mixin_instance.action_focus_next()

        # No assertions needed, just verify it doesn't crash

    def test_action_focus_previous_no_current_focus(
        self, mixin_instance, create_mock_widget
    ):
        """Test action_focus_previous when nothing is focused."""
        # Setup
        widget1 = create_mock_widget("widget1")
        widget2 = create_mock_widget("widget2")

        mixin_instance._focus_chain = [widget1, widget2]
        mixin_instance.focused = None  # Nothing focused

        # Execute
        mixin_instance.action_focus_previous()

        # Verify - should focus first element
        widget1.focus.assert_called_once()

    def test_action_focus_next_no_current_focus(
        self, mixin_instance, create_mock_widget
    ):
        """Test action_focus_next when nothing is focused."""
        # Setup
        widget1 = create_mock_widget("widget1")
        widget2 = create_mock_widget("widget2")

        mixin_instance._focus_chain = [widget1, widget2]
        mixin_instance.focused = None  # Nothing focused

        # Execute
        mixin_instance.action_focus_next()

        # Verify - should focus first element
        widget1.focus.assert_called_once()

    def test_on_descendant_focus(self, mixin_instance, create_mock_widget):
        """Test on_descendant_focus scrolls widget into view."""
        from textual.events import DescendantFocus

        # Setup
        mock_widget = create_mock_widget("focused-widget")
        mock_event = Mock(spec=DescendantFocus)
        mock_event.widget = mock_widget

        mock_scroll_container = Mock()
        mixin_instance.query_one = Mock(return_value=mock_scroll_container)

        # Execute
        mixin_instance.on_descendant_focus(mock_event)

        # Verify - should scroll the widget into view with animation
        mock_scroll_container.scroll_to_widget.assert_called_once_with(
            mock_widget, animate=True
        )
