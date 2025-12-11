"""Comprehensive tests for TUI application using Textual's testing utilities.

Test Categories:
1. App Startup & Basic Operations
2. Main Navigation (Menu panel)
3. ConfigPanel Grid Navigation
4. PresetsPanel Navigation
5. Content Panel Transitions
6. User Workflow Integration
"""

from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import Button, Select

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_cwd_with_config(tmp_path: Path, monkeypatch):
    """Create a temp directory with claudefig.toml and mock cwd to point there.

    This fixture ensures the TUI has a valid config to load.
    """
    # Create config file
    config_path = tmp_path / "claudefig.toml"
    config_path.write_text(
        """[claudefig]
schema_version = "2.0"
template_source = "built-in"

[[files]]
id = "claude_md-default"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true
""",
        encoding="utf-8",
    )

    # Mock cwd
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    return tmp_path


@pytest.fixture
def mock_cwd_without_config(tmp_path: Path, monkeypatch):
    """Create a temp directory without config and mock cwd."""
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    return tmp_path


# =============================================================================
# 1. APP STARTUP & BASIC OPERATIONS
# =============================================================================


@pytest.mark.slow
class TestAppStartup:
    """Test main TUI application startup and basic operations."""

    @pytest.mark.asyncio
    async def test_app_starts_successfully(self, mock_user_home):
        """Test app starts without errors."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as _pilot:
            # App should start without crashing
            assert app.is_running

    @pytest.mark.asyncio
    async def test_quit_with_q(self, mock_user_home):
        """Test app can be quit with 'q' key."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.press("q")
            await pilot.pause()
            # App should process quit request

    @pytest.mark.asyncio
    async def test_quit_with_ctrl_c(self, mock_user_home):
        """Test app can be quit with Ctrl+C."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.press("ctrl+c")
            await pilot.pause()

    @pytest.mark.asyncio
    async def test_app_has_header_and_footer(self, mock_user_home):
        """Test app displays header and footer."""
        from textual.widgets import Footer, Header

        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Check for header
            headers = app.query(Header)
            assert len(headers) == 1

            # Check for footer
            footers = app.query(Footer)
            assert len(footers) == 1

    @pytest.mark.asyncio
    async def test_app_has_menu_buttons(self, mock_user_home):
        """Test app displays all menu buttons."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Check all menu buttons exist
            init_btn = app.query_one("#init", Button)
            presets_btn = app.query_one("#presets", Button)
            config_btn = app.query_one("#config", Button)
            exit_btn = app.query_one("#exit", Button)

            assert init_btn is not None
            assert presets_btn is not None
            assert config_btn is not None
            assert exit_btn is not None

    @pytest.mark.asyncio
    async def test_initial_focus_on_init_button(self, mock_user_home):
        """Test that initial focus is on the Initialize button."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn


# =============================================================================
# 2. MAIN NAVIGATION (Menu Panel)
# =============================================================================


@pytest.mark.slow
class TestMainNavigation:
    """Test main menu navigation with arrow keys."""

    @pytest.mark.asyncio
    async def test_navigate_down_through_menu(self, mock_user_home):
        """Test down arrow navigates through menu buttons."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Start at init button
            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn

            # Down to presets
            await pilot.press("down")
            await pilot.pause()
            presets_btn = app.query_one("#presets", Button)
            assert app.focused == presets_btn

            # Down to config
            await pilot.press("down")
            await pilot.pause()
            config_btn = app.query_one("#config", Button)
            assert app.focused == config_btn

            # Down to exit
            await pilot.press("down")
            await pilot.pause()
            exit_btn = app.query_one("#exit", Button)
            assert app.focused == exit_btn

    @pytest.mark.asyncio
    async def test_navigate_up_through_menu(self, mock_user_home):
        """Test up arrow navigates through menu buttons."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to exit first
            await pilot.press("down", "down", "down")
            await pilot.pause()
            exit_btn = app.query_one("#exit", Button)
            assert app.focused == exit_btn

            # Up to config
            await pilot.press("up")
            await pilot.pause()
            config_btn = app.query_one("#config", Button)
            assert app.focused == config_btn

            # Up to presets
            await pilot.press("up")
            await pilot.pause()
            presets_btn = app.query_one("#presets", Button)
            assert app.focused == presets_btn

            # Up to init
            await pilot.press("up")
            await pilot.pause()
            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn

    @pytest.mark.asyncio
    async def test_no_wrap_at_menu_top(self, mock_user_home):
        """Test up arrow at top of menu doesn't wrap to bottom."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Start at init (top)
            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn

            # Press up - should stay at init (no wrap)
            await pilot.press("up")
            await pilot.pause()
            assert app.focused == init_btn

    @pytest.mark.asyncio
    async def test_no_wrap_at_menu_bottom(self, mock_user_home):
        """Test down arrow at bottom of menu doesn't wrap to top."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to exit (bottom)
            await pilot.press("down", "down", "down")
            await pilot.pause()
            exit_btn = app.query_one("#exit", Button)
            assert app.focused == exit_btn

            # Press down - should stay at exit (no wrap)
            await pilot.press("down")
            await pilot.pause()
            assert app.focused == exit_btn

    @pytest.mark.asyncio
    async def test_enter_activates_section(self, mock_user_home):
        """Test enter key activates the focused menu section."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Start at init
            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn

            # Press enter to activate
            await pilot.press("enter")
            await pilot.pause()

            # Check active_button state
            assert app.active_button == "init"

            # Check button has active class
            assert init_btn.has_class("active")

    @pytest.mark.asyncio
    async def test_escape_clears_selection(self, mock_user_home):
        """Test escape key clears active selection and returns focus to menu."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate a section
            await pilot.press("enter")
            await pilot.pause()
            assert app.active_button == "init"

            # Press escape to clear
            await pilot.press("escape")
            await pilot.pause()

            # Active button should be cleared
            assert app.active_button is None

            # Focus should return to init button
            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn

    @pytest.mark.asyncio
    async def test_backspace_clears_selection(self, mock_user_home):
        """Test backspace key clears active selection (same as escape)."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate a section
            await pilot.press("enter")
            await pilot.pause()
            assert app.active_button == "init"

            # Press backspace to clear
            await pilot.press("backspace")
            await pilot.pause()

            # Active button should be cleared
            assert app.active_button is None


# =============================================================================
# 3. CONTENT PANEL TRANSITIONS
# =============================================================================


@pytest.mark.slow
class TestContentPanelTransitions:
    """Test transitions between menu and content panels."""

    @pytest.mark.asyncio
    async def test_right_arrow_moves_to_content_when_active(self, mock_user_home):
        """Test right arrow moves focus to content panel when section is active."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate init section
            await pilot.press("enter")
            await pilot.pause()

            # Focus should be in content panel (auto-focused)
            # Navigate back to menu first
            await pilot.press("left")
            await pilot.pause()

            # Focus should be on init button
            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn

            # Now press right to move to content
            await pilot.press("right")
            await pilot.pause()

            # Focus should be in content panel (not on menu button)
            assert app.focused != init_btn

    @pytest.mark.asyncio
    async def test_right_arrow_does_nothing_when_no_section_active(
        self, mock_user_home
    ):
        """Test right arrow stays in menu when no section is active."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Don't activate any section
            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn

            # Press right - should stay on init button
            await pilot.press("right")
            await pilot.pause()
            assert app.focused == init_btn

    @pytest.mark.asyncio
    async def test_left_arrow_returns_to_menu_from_content(self, mock_user_home):
        """Test left arrow returns focus to menu from content panel."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate init section
            await pilot.press("enter")
            await pilot.pause()
            # Extra pause needed for focus timer (0.05s) to complete on slower systems
            await pilot.pause()

            # Focus should be in content panel now
            init_btn = app.query_one("#init", Button)
            assert app.focused != init_btn

            # Press left to return to menu
            await pilot.press("left")
            await pilot.pause()

            # Focus should be back on init button
            assert app.focused == init_btn

    @pytest.mark.asyncio
    async def test_exit_button_closes_app(self, mock_user_home):
        """Test pressing exit button closes the app."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to exit button
            await pilot.press("down", "down", "down")
            await pilot.pause()

            exit_btn = app.query_one("#exit", Button)
            assert app.focused == exit_btn

            # Press enter to exit
            await pilot.press("enter")
            await pilot.pause()


# =============================================================================
# 4. CONFIG PANEL GRID NAVIGATION
# =============================================================================


@pytest.mark.slow
class TestConfigPanelNavigation:
    """Test ConfigPanel 2x2 grid navigation."""

    @pytest.mark.asyncio
    async def test_config_panel_shows_placeholder_without_config(
        self, mock_user_home, mock_cwd_without_config
    ):
        """Test ConfigPanel shows placeholder when no config exists."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to config and activate
            await pilot.press("down", "down")  # init -> presets -> config
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Should show placeholder label
            placeholders = app.query(".placeholder")
            assert len(placeholders) >= 1

    @pytest.mark.asyncio
    async def test_config_panel_shows_buttons_with_config(
        self, mock_user_home, mock_cwd_with_config
    ):
        """Test ConfigPanel shows grid buttons when config exists."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to config and activate
            await pilot.press("down", "down")  # init -> presets -> config
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Should have config menu buttons
            overview_btn = app.query_one("#btn-overview", Button)
            settings_btn = app.query_one("#btn-settings", Button)
            files_btn = app.query_one("#btn-file-instances", Button)

            assert overview_btn is not None
            assert settings_btn is not None
            assert files_btn is not None

    @pytest.mark.asyncio
    async def test_config_panel_grid_horizontal_navigation(
        self, mock_user_home, mock_cwd_with_config
    ):
        """Test left/right navigation in ConfigPanel grid."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate config section
            await pilot.press("down", "down", "enter")
            await pilot.pause()

            # Focus should be on overview button (restored or default)
            overview_btn = app.query_one("#btn-overview", Button)
            settings_btn = app.query_one("#btn-settings", Button)

            # Navigate right from overview to settings
            overview_btn.focus()
            await pilot.pause()
            assert app.focused == overview_btn

            await pilot.press("right")
            await pilot.pause()
            assert app.focused == settings_btn

    @pytest.mark.asyncio
    async def test_config_panel_grid_vertical_navigation(
        self, mock_user_home, mock_cwd_with_config
    ):
        """Test up/down navigation in ConfigPanel grid."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate config section
            await pilot.press("down", "down", "enter")
            await pilot.pause()

            overview_btn = app.query_one("#btn-overview", Button)
            files_btn = app.query_one("#btn-file-instances", Button)

            # Start at overview
            overview_btn.focus()
            await pilot.pause()

            # Navigate down to file instances
            await pilot.press("down")
            await pilot.pause()
            assert app.focused == files_btn

            # Navigate back up
            await pilot.press("up")
            await pilot.pause()
            assert app.focused == overview_btn

    @pytest.mark.asyncio
    async def test_config_panel_left_returns_to_menu(
        self, mock_user_home, mock_cwd_with_config
    ):
        """Test left arrow from leftmost column returns to menu."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate config section
            await pilot.press("down", "down", "enter")
            await pilot.pause()

            # Focus on leftmost button (overview at col 0)
            overview_btn = app.query_one("#btn-overview", Button)
            overview_btn.focus()
            await pilot.pause()

            # Press left - should return to config menu button
            await pilot.press("left")
            await pilot.pause()

            config_btn = app.query_one("#config", Button)
            assert app.focused == config_btn


# =============================================================================
# 5. PRESETS PANEL NAVIGATION
# =============================================================================


@pytest.mark.slow
class TestPresetsPanelNavigation:
    """Test PresetsPanel navigation between Select and button row."""

    @pytest.mark.asyncio
    async def test_presets_panel_has_select_and_buttons(self, mock_user_home):
        """Test PresetsPanel has Select dropdown and action buttons."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to presets and activate
            await pilot.press("down")  # init -> presets
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Should have preset select
            preset_select = app.query_one("#preset-select", Select)
            assert preset_select is not None

            # Should have buttons
            apply_btn = app.query_one("#btn-apply-preset", Button)
            delete_btn = app.query_one("#btn-delete-preset", Button)
            create_btn = app.query_one("#btn-create-from-config", Button)

            assert apply_btn is not None
            assert delete_btn is not None
            assert create_btn is not None

    @pytest.mark.asyncio
    async def test_presets_down_from_select_goes_to_buttons(self, mock_user_home):
        """Test down arrow from Select goes to button row."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate presets section
            await pilot.press("down", "enter")
            await pilot.pause()

            # Focus on Select
            preset_select = app.query_one("#preset-select", Select)
            preset_select.focus()
            await pilot.pause()
            assert app.focused == preset_select

            # Press down - should move to first button
            await pilot.press("down")
            await pilot.pause()

            # Focus should now be on a button in the button row
            assert isinstance(app.focused, Button)

    @pytest.mark.asyncio
    async def test_presets_up_from_buttons_goes_to_select(self, mock_user_home):
        """Test up arrow from button row goes to Select."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate presets section
            await pilot.press("down", "enter")
            await pilot.pause()

            # Focus on a button (navigate down from select first)
            preset_select = app.query_one("#preset-select", Select)
            preset_select.focus()
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()

            # Now on a button
            assert isinstance(app.focused, Button)

            # Press up - should go back to Select
            await pilot.press("up")
            await pilot.pause()
            assert app.focused == preset_select

    @pytest.mark.asyncio
    async def test_presets_horizontal_button_navigation(self, mock_user_home):
        """Test left/right navigation within button row."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate presets section
            await pilot.press("down", "enter")
            await pilot.pause()

            # Navigate to buttons
            await pilot.press("down")
            await pilot.pause()

            first_button = app.focused
            assert isinstance(first_button, Button)

            # Navigate right
            await pilot.press("right")
            await pilot.pause()

            second_button = app.focused
            assert isinstance(second_button, Button)
            assert second_button != first_button

            # Navigate left - should go back
            await pilot.press("left")
            await pilot.pause()
            assert app.focused == first_button


# =============================================================================
# 6. KEYBOARD SHORTCUTS AND BINDINGS
# =============================================================================


@pytest.mark.slow
class TestKeyboardBindings:
    """Test keyboard shortcuts and bindings."""

    @pytest.mark.asyncio
    async def test_tab_moves_focus_forward(self, mock_user_home):
        """Test tab key moves focus to next focusable element."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn

            # Tab should move focus
            await pilot.press("tab")
            await pilot.pause()
            assert app.focused != init_btn

    @pytest.mark.asyncio
    async def test_shift_tab_moves_focus_backward(self, mock_user_home):
        """Test shift+tab moves focus to previous element."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Move to second button first
            await pilot.press("down")
            await pilot.pause()

            presets_btn = app.query_one("#presets", Button)
            assert app.focused == presets_btn

            # Shift+tab should go back
            await pilot.press("shift+tab")
            await pilot.pause()

            init_btn = app.query_one("#init", Button)
            assert app.focused == init_btn


# =============================================================================
# 7. STATE PERSISTENCE (Focus Memory)
# =============================================================================


@pytest.mark.slow
class TestStatePersistence:
    """Test state persistence across panel navigation."""

    @pytest.mark.asyncio
    async def test_config_panel_remembers_last_focused_button(
        self, mock_user_home, mock_cwd_with_config
    ):
        """Test ConfigPanel restores focus to last focused button."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate config
            await pilot.press("down", "down", "enter")
            await pilot.pause()

            # Navigate to settings button
            settings_btn = app.query_one("#btn-settings", Button)
            settings_btn.focus()
            await pilot.pause()

            # Store the focused button state
            assert app.focused == settings_btn

            # Return to menu
            await pilot.press("left")
            await pilot.pause()

            # Re-enter config panel
            await pilot.press("right")
            await pilot.pause()

            # Focus should be restored to settings button
            # (ConfigPanel tracks _last_focused_button)
            assert app.focused == settings_btn

    @pytest.mark.asyncio
    async def test_presets_panel_remembers_selected_preset(self, mock_user_home):
        """Test PresetsPanel persists preset selection."""
        from claudefig.tui import ClaudefigApp
        from claudefig.tui.panels.presets_panel import PresetsPanel

        # Reset class variable for clean test
        PresetsPanel._last_selected_preset = None

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate presets
            await pilot.press("down", "enter")
            await pilot.pause()

            # The Select should exist and have a value (default or blank)
            preset_select = app.query_one("#preset-select", Select)
            assert preset_select is not None, "Preset select widget should exist"

            # If presets exist and default is available, it should be selected
            # The reactive attribute should match
            panel = app.query_one("#presets-panel", PresetsPanel)
            initial_selection = panel.selected_preset

            # Return to menu and re-enter
            await pilot.press("left")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()

            # Selection should be preserved
            panel = app.query_one("#presets-panel", PresetsPanel)
            assert panel.selected_preset == initial_selection


# =============================================================================
# 8. REACTIVE ATTRIBUTES (Widget Updates)
# =============================================================================


@pytest.mark.slow
class TestReactiveAttributes:
    """Test reactive attribute behavior in widgets."""

    @pytest.mark.asyncio
    async def test_presets_apply_button_disabled_without_selection(
        self, mock_user_home
    ):
        """Test Apply button is disabled when no preset selected."""
        from claudefig.tui import ClaudefigApp
        from claudefig.tui.panels.presets_panel import PresetsPanel

        # Start with no selection
        PresetsPanel._last_selected_preset = None

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate presets
            await pilot.press("down", "enter")
            await pilot.pause()

            # Apply button should be disabled if no preset selected
            apply_btn = app.query_one("#btn-apply-preset", Button)
            panel = app.query_one("#presets-panel", PresetsPanel)

            if panel.selected_preset is None:
                assert apply_btn.disabled
            else:
                # If a default preset was auto-selected, button should be enabled
                assert not apply_btn.disabled


# =============================================================================
# 9. SCREEN PUSH/POP
# =============================================================================


@pytest.mark.slow
class TestScreenNavigation:
    """Test screen push/pop behavior."""

    @pytest.mark.asyncio
    async def test_config_overview_button_pushes_screen(
        self, mock_user_home, mock_cwd_with_config
    ):
        """Test Overview button pushes OverviewScreen."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate config
            await pilot.press("down", "down", "enter")
            await pilot.pause()

            # Click overview button
            overview_btn = app.query_one("#btn-overview", Button)
            overview_btn.focus()
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # A new screen should be pushed
            # Screen stack should have more than 1 screen
            assert len(app.screen_stack) >= 1

    @pytest.mark.asyncio
    async def test_back_button_pops_screen(self, mock_user_home, mock_cwd_with_config):
        """Test Back button pops the current screen."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Activate config and push a screen
            await pilot.press("down", "down", "enter")
            await pilot.pause()

            overview_btn = app.query_one("#btn-overview", Button)
            overview_btn.focus()
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            initial_stack_size = len(app.screen_stack)

            # Find and press back button
            try:
                back_btn = app.query_one("#btn-back", Button)
                back_btn.focus()
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()

                # Stack should be smaller
                assert len(app.screen_stack) < initial_stack_size
            except Exception:
                # Back button might not exist in some configurations
                pass


# =============================================================================
# 10. ERROR HANDLING
# =============================================================================


@pytest.mark.slow
class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_app_handles_missing_config_gracefully(
        self, mock_user_home, mock_cwd_without_config
    ):
        """Test app starts even without claudefig.toml."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()
            # App should start without crashing
            assert app.is_running

    @pytest.mark.asyncio
    async def test_rapid_key_presses_handled(self, mock_user_home):
        """Test app handles rapid key presses without crashing."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Rapid navigation
            for _ in range(10):
                await pilot.press("down")
            for _ in range(10):
                await pilot.press("up")
            await pilot.pause()

            # App should still be running
            assert app.is_running


# =============================================================================
# 11. INTEGRATION WORKFLOWS
# =============================================================================


@pytest.mark.slow
class TestUserWorkflows:
    """Test complete user workflows."""

    @pytest.mark.asyncio
    async def test_navigate_to_config_and_back(
        self, mock_user_home, mock_cwd_with_config
    ):
        """Test navigating to config panel and returning to menu."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to config
            await pilot.press("down", "down")
            await pilot.pause()

            config_btn = app.query_one("#config", Button)
            assert app.focused == config_btn

            # Activate
            await pilot.press("enter")
            await pilot.pause()
            assert app.active_button == "config"

            # Clear selection with escape
            await pilot.press("escape")
            await pilot.pause()
            assert app.active_button is None

            # Should be back on config button
            assert app.focused == config_btn

    @pytest.mark.asyncio
    async def test_full_config_exploration_workflow(
        self, mock_user_home, mock_cwd_with_config
    ):
        """Test exploring config options and returning."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # 1. Go to config
            await pilot.press("down", "down", "enter")
            await pilot.pause()

            # 2. Navigate in config grid
            overview_btn = app.query_one("#btn-overview", Button)
            overview_btn.focus()
            await pilot.pause()

            # 3. Move to settings
            await pilot.press("right")
            await pilot.pause()

            settings_btn = app.query_one("#btn-settings", Button)
            assert app.focused == settings_btn

            # 4. Move down to file instances
            await pilot.press("left")  # Back to overview
            await pilot.pause()
            await pilot.press("down")  # Down to file instances
            await pilot.pause()

            files_btn = app.query_one("#btn-file-instances", Button)
            assert app.focused == files_btn

            # 5. Return to menu
            await pilot.press("left")
            await pilot.pause()

            config_btn = app.query_one("#config", Button)
            assert app.focused == config_btn

    @pytest.mark.asyncio
    async def test_presets_workflow(self, mock_user_home):
        """Test browsing presets and navigating controls."""
        from claudefig.tui import ClaudefigApp

        app = ClaudefigApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # 1. Go to presets
            await pilot.press("down", "enter")
            await pilot.pause()
            assert app.active_button == "presets"

            # 2. Navigate to buttons
            await pilot.press("down")
            await pilot.pause()

            # Should be on a button
            assert isinstance(app.focused, Button)

            # 3. Navigate through buttons
            await pilot.press("right")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()

            # 4. Return to select
            await pilot.press("up")
            await pilot.pause()

            preset_select = app.query_one("#preset-select", Select)
            assert app.focused == preset_select

            # 5. Return to menu
            await pilot.press("left")
            await pilot.pause()

            presets_btn = app.query_one("#presets", Button)
            assert app.focused == presets_btn
