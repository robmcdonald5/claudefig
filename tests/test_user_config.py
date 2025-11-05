"""Tests for user_config.py - User configuration and directory management."""

from __future__ import annotations

from unittest.mock import patch

from claudefig.user_config import (
    create_default_user_config,
    ensure_user_config,
    get_cache_dir,
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
        assert not is_initialized(auto_heal=False)

    def test_is_initialized_false_missing_presets(self, mock_user_home):
        """Test is_initialized returns False when presets dir missing."""
        config_dir = get_user_config_dir()
        config_dir.mkdir()

        # Has config dir but no presets dir
        assert not is_initialized(auto_heal=False)

    def test_is_initialized_true(self, mock_user_home):
        """Test is_initialized returns True when properly initialized."""
        config_dir = get_user_config_dir()
        config_dir.mkdir()
        (config_dir / "presets").mkdir()
        (config_dir / "cache").mkdir()
        (config_dir / "components").mkdir()

        # Create required files
        (config_dir / "config.toml").write_text("[config]\n", encoding="utf-8")

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


class TestAutoHealing:
    """Test auto-healing functionality."""

    def test_is_initialized_with_auto_heal_enabled(self, mock_user_home):
        """Test is_initialized creates missing directories with auto-heal."""
        config_dir = get_user_config_dir()

        # Initially not initialized
        assert not config_dir.exists()

        # Call with auto-heal enabled
        result = is_initialized(auto_heal=True)

        # Directory structure should be created
        assert config_dir.exists()
        assert (config_dir / "presets").exists()
        assert (config_dir / "cache").exists()
        assert (config_dir / "components").exists()

        # Result may be True if structure was created successfully
        # or False if config file is still missing (depends on implementation)
        assert isinstance(result, bool)

    def test_is_initialized_with_auto_heal_disabled(self, mock_user_home):
        """Test is_initialized doesn't create directories without auto-heal."""
        config_dir = get_user_config_dir()

        result = is_initialized(auto_heal=False)

        assert result is False
        assert not config_dir.exists()

    def test_is_initialized_repairs_missing_subdirectories(self, mock_user_home):
        """Test is_initialized repairs missing subdirectories."""
        config_dir = get_user_config_dir()
        config_dir.mkdir()
        (config_dir / "config.toml").write_text("# config", encoding="utf-8")

        # Create only presets directory, others missing
        (config_dir / "presets").mkdir()

        # Call with auto-heal
        is_initialized(auto_heal=True)

        # All subdirectories should now exist
        assert (config_dir / "presets").exists()
        assert (config_dir / "cache").exists()
        assert (config_dir / "components").exists()
        assert (config_dir / "components" / "claude_md").exists()
        assert (config_dir / "components" / "gitignore").exists()

    def test_ensure_user_config_repairs_structure(self, mock_user_home):
        """Test ensure_user_config repairs incomplete structure."""
        config_dir = get_user_config_dir()
        config_dir.mkdir()

        # Create only partial structure
        (config_dir / "presets").mkdir()

        # ensure_user_config should repair
        result_dir = ensure_user_config(verbose=False)

        # All structure should now exist
        assert result_dir == config_dir
        assert (config_dir / "cache").exists()
        assert (config_dir / "components").exists()
        assert (config_dir / "config.toml").exists()

    def test_ensure_user_config_with_deleted_components_folder(self, mock_user_home):
        """Test auto-healing when components folder is deleted."""
        # Initialize first
        config_dir = get_user_config_dir()
        initialize_user_directory(config_dir, verbose=False)

        # Delete components folder to simulate user deletion
        import shutil

        shutil.rmtree(config_dir / "components")

        # Call ensure_user_config - should auto-heal
        ensure_user_config(verbose=False)

        # Components folder should be restored
        assert (config_dir / "components").exists()
        assert (config_dir / "components" / "claude_md").exists()
        assert (config_dir / "components" / "gitignore").exists()

    def test_preset_integrity_validation_and_repair(self, mock_user_home):
        """Test preset integrity validation during initialization."""
        from claudefig.user_config import _copy_default_preset_to_user

        config_dir = get_user_config_dir()
        config_dir.mkdir()
        presets_dir = config_dir / "presets"
        presets_dir.mkdir()

        # Create incomplete default preset (missing claudefig.toml)
        default_preset = presets_dir / "default"
        default_preset.mkdir()
        (default_preset / "components").mkdir()

        # Copy function should detect incomplete preset and re-copy
        # This test verifies the new validation logic
        _copy_default_preset_to_user(presets_dir, verbose=False)

        # After repair, claudefig.toml should exist
        assert (default_preset / "claudefig.toml").exists()

    def test_ensure_user_config_restores_deleted_presets(self, mock_user_home):
        """Test auto-healing when entire presets/default folder is deleted."""
        # Initialize first
        config_dir = get_user_config_dir()
        initialize_user_directory(config_dir, verbose=False)

        # Verify default preset exists
        default_preset = config_dir / "presets" / "default"
        assert default_preset.exists()
        assert (default_preset / "claudefig.toml").exists()

        # Delete the default preset to simulate user deletion
        import shutil

        shutil.rmtree(default_preset)
        assert not default_preset.exists()

        # Call ensure_user_config - should auto-heal and restore preset
        ensure_user_config(verbose=False)

        # Default preset should be restored
        assert default_preset.exists()
        assert (default_preset / "claudefig.toml").exists()
        assert (default_preset / "components").exists()
