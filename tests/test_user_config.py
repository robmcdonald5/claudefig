"""Tests for user_config.py - User configuration and directory management."""

from __future__ import annotations

from unittest.mock import patch

from claudefig.user_config import (
    create_default_user_config,
    ensure_user_config,
    get_cache_dir,
    get_template_dir,
    get_user_config_dir,
    get_user_config_file,
    initialize_user_directory,
    is_initialized,
    reset_user_config,
)


class TestPathFunctions:
    """Test path getter functions."""

    def test_get_user_config_dir(self, mock_user_home):
        """Test getting user config directory."""
        config_dir = get_user_config_dir()

        assert config_dir == mock_user_home / ".claudefig"
        assert config_dir.parent == mock_user_home

    def test_get_template_dir(self, mock_user_home):
        """Test getting template directory."""
        template_dir = get_template_dir()

        assert template_dir == mock_user_home / ".claudefig" / "templates"

    def test_get_cache_dir(self, mock_user_home):
        """Test getting cache directory."""
        cache_dir = get_cache_dir()

        assert cache_dir == mock_user_home / ".claudefig" / "cache"

    def test_get_user_config_file(self, mock_user_home):
        """Test getting user config file path."""
        config_file = get_user_config_file()

        assert config_file == mock_user_home / ".claudefig" / "config.toml"
        assert config_file.parent == mock_user_home / ".claudefig"


class TestInitializationChecks:
    """Test initialization checking functions."""

    def test_is_initialized_false_no_directory(self, mock_user_home):
        """Test is_initialized returns False when directory doesn't exist."""
        assert not is_initialized()

    def test_is_initialized_false_missing_presets(self, mock_user_home):
        """Test is_initialized returns False when presets dir missing."""
        config_dir = get_user_config_dir()
        config_dir.mkdir()

        # Has config dir but no presets dir
        assert not is_initialized()

    def test_is_initialized_true(self, mock_user_home):
        """Test is_initialized returns True when properly initialized."""
        config_dir = get_user_config_dir()
        config_dir.mkdir()
        (config_dir / "presets").mkdir()
        (config_dir / "components").mkdir()  # is_initialized() requires this too

        assert is_initialized()


class TestUserConfigCreation:
    """Test user config file creation."""

    def test_create_default_user_config(self, mock_user_home):
        """Test creating default user config file."""
        config_path = get_user_config_file()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        create_default_user_config(config_path, verbose=False)

        assert config_path.exists()
        content = config_path.read_text(encoding="utf-8")

        # Check for expected config sections
        assert "[user]" in content
        assert "[ui]" in content
        assert "default_template" in content
        assert "prefer_interactive" in content
        assert "theme" in content
        assert "show_hints" in content

    def test_create_default_user_config_already_exists(self, mock_user_home):
        """Test that existing config file is not overwritten."""
        config_path = get_user_config_file()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create existing config with custom content
        original_content = "# My custom config\n"
        config_path.write_text(original_content, encoding="utf-8")

        # Try to create default config
        create_default_user_config(config_path, verbose=False)

        # Should still have original content
        assert config_path.read_text(encoding="utf-8") == original_content

    def test_create_default_user_config_verbose(self, mock_user_home, capsys):
        """Test verbose output when creating config."""
        config_path = get_user_config_file()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        create_default_user_config(config_path, verbose=True)

        captured = capsys.readouterr()
        assert "Created config:" in captured.out


class TestDirectoryInitialization:
    """Test directory initialization."""

    def test_initialize_user_directory_creates_structure(self, mock_user_home):
        """Test that initialize_user_directory creates all necessary directories."""
        config_dir = get_user_config_dir()

        initialize_user_directory(config_dir, verbose=False)

        # Check all directories were created
        assert config_dir.exists()
        assert (config_dir / "presets").exists()
        assert (config_dir / "templates").exists()
        assert (config_dir / "cache").exists()

    def test_initialize_user_directory_creates_config_file(self, mock_user_home):
        """Test that config.toml is created during initialization."""
        config_dir = get_user_config_dir()

        initialize_user_directory(config_dir, verbose=False)

        config_file = config_dir / "config.toml"
        assert config_file.exists()

    def test_initialize_user_directory_verbose(self, mock_user_home, capsys):
        """Test verbose output during initialization."""
        config_dir = get_user_config_dir()

        initialize_user_directory(config_dir, verbose=True)

        captured = capsys.readouterr()
        assert "Created directory:" in captured.out
        assert "User configuration initialized successfully!" in captured.out

    def test_initialize_user_directory_idempotent(self, mock_user_home):
        """Test that initializing twice doesn't cause errors."""
        config_dir = get_user_config_dir()

        # Initialize twice
        initialize_user_directory(config_dir, verbose=False)
        initialize_user_directory(config_dir, verbose=False)

        # Should still work
        assert config_dir.exists()
        assert (config_dir / "presets").exists()

    def test_ensure_user_config_first_run(self, mock_user_home, capsys):
        """Test ensure_user_config on first run."""
        result = ensure_user_config(verbose=True)

        assert result == get_user_config_dir()
        assert is_initialized()

        captured = capsys.readouterr()
        assert "First run detected" in captured.out

    def test_ensure_user_config_already_initialized(self, mock_user_home, capsys):
        """Test ensure_user_config when already initialized."""
        # Initialize first
        ensure_user_config(verbose=False)

        # Call again
        result = ensure_user_config(verbose=True)

        assert result == get_user_config_dir()

        # Should not print first run message
        captured = capsys.readouterr()
        assert "First run detected" not in captured.out

    def test_ensure_user_config_returns_path(self, mock_user_home):
        """Test that ensure_user_config returns correct path."""
        result = ensure_user_config(verbose=False)

        assert result == mock_user_home / ".claudefig"
        assert result.exists()


class TestConfigReset:
    """Test configuration reset functionality."""

    def test_reset_user_config_no_config(self, mock_user_home, capsys):
        """Test resetting when no config exists."""
        result = reset_user_config(force=True)

        assert result is False
        captured = capsys.readouterr()
        assert "No user configuration to reset" in captured.out

    def test_reset_user_config_force(self, mock_user_home):
        """Test force reset without confirmation."""
        # Create config directory
        config_dir = get_user_config_dir()
        config_dir.mkdir()
        (config_dir / "presets").mkdir()
        (config_dir / "test.txt").write_text("test", encoding="utf-8")

        assert config_dir.exists()

        # Force reset
        result = reset_user_config(force=True)

        assert result is True
        assert not config_dir.exists()

    def test_reset_user_config_with_confirmation(self, mock_user_home):
        """Test reset with user confirmation."""
        # Create config directory
        config_dir = get_user_config_dir()
        config_dir.mkdir()
        (config_dir / "presets").mkdir()

        # Mock user input to confirm
        with patch("claudefig.user_config.console.input", return_value="yes"):
            result = reset_user_config(force=False)

        assert result is True
        assert not config_dir.exists()

    def test_reset_user_config_cancelled(self, mock_user_home, capsys):
        """Test reset cancelled by user."""
        # Create config directory
        config_dir = get_user_config_dir()
        config_dir.mkdir()
        (config_dir / "presets").mkdir()

        # Mock user input to cancel
        with patch("claudefig.user_config.console.input", return_value="no"):
            result = reset_user_config(force=False)

        assert result is False
        assert config_dir.exists()  # Should still exist

        captured = capsys.readouterr()
        assert "Reset cancelled" in captured.out

    def test_reset_user_config_case_insensitive_confirmation(self, mock_user_home):
        """Test that confirmation is case-insensitive."""
        # Create config directory
        config_dir = get_user_config_dir()
        config_dir.mkdir()

        # Test various cases
        for response in ["YES", "Yes", "yEs"]:
            config_dir.mkdir(exist_ok=True)

            with patch("claudefig.user_config.console.input", return_value=response):
                result = reset_user_config(force=False)

            assert result is True
            assert not config_dir.exists()

    def test_reset_user_config_verbose_output(self, mock_user_home, capsys):
        """Test verbose output during reset."""
        config_dir = get_user_config_dir()
        config_dir.mkdir()
        (config_dir / "presets").mkdir()

        reset_user_config(force=True)

        captured = capsys.readouterr()
        assert "User configuration reset successfully" in captured.out
        assert "Run claudefig again to reinitialize" in captured.out
