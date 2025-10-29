"""Tests for FileInstanceItem widget."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from claudefig.models import FileInstance, FileType
from claudefig.tui.widgets.file_instance_item import FileInstanceItem


class FileInstanceItemTestApp(App):
    """Test app for FileInstanceItem widget."""

    def __init__(self, instance: FileInstance, **kwargs):
        """Initialize test app with instance."""
        super().__init__(**kwargs)
        self.test_instance = instance

    def compose(self) -> ComposeResult:
        """Compose the test app."""
        yield FileInstanceItem(instance=self.test_instance)


class TestFileInstanceItemReactiveAttributes:
    """Test reactive attribute behavior."""

    @pytest.fixture
    def sample_instance(self):
        """Create a sample FileInstance."""
        return FileInstance(
            id="test-1",
            type=FileType.CLAUDE_MD,
            preset="component:default",
            path="CLAUDE.md",
            enabled=True,
        )

    @pytest.mark.asyncio
    async def test_initial_enabled_state_displays_correctly(self, sample_instance):
        """Test that enabled state shows correctly on initial mount."""
        sample_instance.enabled = True
        app = FileInstanceItemTestApp(sample_instance)
        async with app.run_test() as pilot:
            item = app.query_one(FileInstanceItem)
            status_label = item.query_one("#status-label", Static)

            # Wait for mount to complete
            await pilot.pause()

            # Status label should show "+ Enabled"
            assert "+ Enabled" in str(status_label.render())
            # Should have enabled CSS class
            assert status_label.has_class("instance-enabled")
            assert not status_label.has_class("instance-disabled")

    @pytest.mark.asyncio
    async def test_initial_disabled_state_displays_correctly(self):
        """Test that disabled state shows correctly on initial mount."""
        instance = FileInstance(
            id="test-disabled",
            type=FileType.CLAUDE_MD,
            preset="component:default",
            path="CLAUDE.md",
            enabled=False,
        )
        app = FileInstanceItemTestApp(instance)
        async with app.run_test() as pilot:
            item = app.query_one(FileInstanceItem)
            status_label = item.query_one("#status-label", Static)
            path_label = item.query_one("#path-label", Static)

            # Wait for mount to complete
            await pilot.pause()

            # Status label should show "- Disabled"
            assert "- Disabled" in str(status_label.render())
            # Should have disabled CSS class
            assert status_label.has_class("instance-disabled")
            assert not status_label.has_class("instance-enabled")
            # Path label should have disabled CSS class (provides visual feedback)
            assert path_label.has_class("instance-disabled")
            # Verify the path is shown
            assert "CLAUDE.md" in str(path_label.render())

    @pytest.mark.asyncio
    async def test_watch_is_enabled_updates_status_label(self, sample_instance):
        """Test that changing is_enabled updates status label."""
        app = FileInstanceItemTestApp(sample_instance)
        async with app.run_test() as pilot:
            item = app.query_one(FileInstanceItem)
            status_label = item.query_one("#status-label", Static)

            # Initial state - enabled
            await pilot.pause()
            assert "+ Enabled" in str(status_label.render())

            # Disable
            item.is_enabled = False
            await pilot.pause()
            assert "- Disabled" in str(status_label.render())

            # Enable again
            item.is_enabled = True
            await pilot.pause()
            assert "+ Enabled" in str(status_label.render())

    @pytest.mark.asyncio
    async def test_watch_is_enabled_toggles_css_classes(self, sample_instance):
        """Test CSS class toggling on enable/disable."""
        app = FileInstanceItemTestApp(sample_instance)
        async with app.run_test() as pilot:
            item = app.query_one(FileInstanceItem)
            status_label = item.query_one("#status-label", Static)

            # Initial state - enabled
            await pilot.pause()
            assert status_label.has_class("instance-enabled")
            assert not status_label.has_class("instance-disabled")

            # Disable
            item.is_enabled = False
            await pilot.pause()
            assert status_label.has_class("instance-disabled")
            assert not status_label.has_class("instance-enabled")

            # Enable again
            item.is_enabled = True
            await pilot.pause()
            assert status_label.has_class("instance-enabled")
            assert not status_label.has_class("instance-disabled")

    @pytest.mark.asyncio
    async def test_watch_file_path_updates_path_label(self, sample_instance):
        """Test that changing file_path updates path label."""
        app = FileInstanceItemTestApp(sample_instance)
        async with app.run_test() as pilot:
            item = app.query_one(FileInstanceItem)
            path_label = item.query_one("#path-label", Static)

            # Initial path
            assert "CLAUDE.md" in str(path_label.render())

            # Change path
            item.file_path = "docs/CLAUDE.md"
            await pilot.pause()

            # Path label should update
            assert "docs/CLAUDE.md" in str(path_label.render())

    @pytest.mark.asyncio
    async def test_watch_component_name_updates_label(self, sample_instance):
        """Test component name label updates."""
        app = FileInstanceItemTestApp(sample_instance)
        async with app.run_test() as pilot:
            item = app.query_one(FileInstanceItem)
            component_label = item.query_one("#component-label", Static)

            # Initial component name
            assert "Component: default" in str(component_label.render())

            # Change component name
            item.component_name = "custom"
            await pilot.pause()

            # Component label should update
            assert "Component: custom" in str(component_label.render())

    @pytest.mark.asyncio
    async def test_disabled_toggles_path_label_css_classes(self, sample_instance):
        """Test that path label CSS classes toggle with enabled state."""
        app = FileInstanceItemTestApp(sample_instance)
        async with app.run_test() as pilot:
            item = app.query_one(FileInstanceItem)
            path_label = item.query_one("#path-label", Static)

            # Initially enabled - no disabled class
            assert not path_label.has_class("instance-disabled")

            # Disable
            item.is_enabled = False
            await pilot.pause()

            # Path label should have disabled class
            assert path_label.has_class("instance-disabled")

            # Enable
            item.is_enabled = True
            await pilot.pause()

            # Disabled class should be removed
            assert not path_label.has_class("instance-disabled")


class TestFileInstanceItemButtons:
    """Test button composition and IDs."""

    @pytest.fixture
    def sample_instance(self):
        """Create a sample FileInstance."""
        return FileInstance(
            id="test-buttons",
            type=FileType.CLAUDE_MD,
            preset="component:default",
            path="CLAUDE.md",
            enabled=True,
        )

    @pytest.mark.asyncio
    async def test_buttons_have_correct_ids(self, sample_instance):
        """Test that buttons have correct IDs based on instance_id."""
        app = FileInstanceItemTestApp(sample_instance)
        async with app.run_test() as _pilot:
            item = app.query_one(FileInstanceItem)

            # Check button IDs
            edit_button = item.query_one("#edit-test-buttons")
            remove_button = item.query_one("#remove-test-buttons")
            toggle_button = item.query_one("#toggle-test-buttons")

            assert edit_button is not None
            assert remove_button is not None
            assert toggle_button is not None

    @pytest.mark.asyncio
    async def test_path_button_for_claude_md(self, sample_instance):
        """Test that CLAUDE.md instances have Path button."""
        sample_instance.type = FileType.CLAUDE_MD
        app = FileInstanceItemTestApp(sample_instance)
        async with app.run_test() as _pilot:
            item = app.query_one(FileInstanceItem)

            # Should have Path button
            path_button = item.query_one("#path-test-buttons")
            assert path_button is not None

    @pytest.mark.asyncio
    async def test_path_button_for_gitignore(self):
        """Test that .gitignore instances have Path button."""
        instance = FileInstance(
            id="test-gitignore",
            type=FileType.GITIGNORE,
            preset="component:default",
            path=".gitignore",
            enabled=True,
        )
        app = FileInstanceItemTestApp(instance)
        async with app.run_test() as _pilot:
            item = app.query_one(FileInstanceItem)

            # Should have Path button
            path_button = item.query_one("#path-test-gitignore")
            assert path_button is not None

    @pytest.mark.asyncio
    async def test_no_path_button_for_other_types(self):
        """Test that other file types don't have Path button."""
        instance = FileInstance(
            id="test-settings",
            type=FileType.SETTINGS_JSON,
            preset="component:default",
            path=".claude/settings.json",
            enabled=True,
        )
        app = FileInstanceItemTestApp(instance)
        async with app.run_test() as _pilot:
            item = app.query_one(FileInstanceItem)

            # Should not have Path button
            path_buttons = item.query("#path-test-settings")
            assert len(path_buttons) == 0
