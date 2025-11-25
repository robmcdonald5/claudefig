"""Tests for structure validation and auto-healing service."""

from pathlib import Path

from claudefig.services.structure_validator import (
    StructureValidationResult,
    check_initialization_marker,
    create_initialization_marker,
    validate_preset_integrity,
    validate_user_directory,
)


class TestStructureValidationResult:
    """Tests for StructureValidationResult class."""

    def test_initialization(self):
        """Test result object initialization."""
        result = StructureValidationResult()
        assert result.is_valid is True
        assert result.missing_dirs == []
        assert result.missing_files == []
        assert result.repaired_dirs == []
        assert result.repaired_files == []
        assert result.errors == []
        assert result.warnings == []

    def test_add_error(self):
        """Test adding error marks result as invalid."""
        result = StructureValidationResult()
        result.add_error("Test error")
        assert result.is_valid is False
        assert "Test error" in result.errors

    def test_add_warning(self):
        """Test adding warning keeps result valid."""
        result = StructureValidationResult()
        result.add_warning("Test warning")
        assert result.is_valid is True
        assert "Test warning" in result.warnings

    def test_needs_repair_property(self):
        """Test needs_repair property."""
        result = StructureValidationResult()
        assert result.needs_repair is False

        result.missing_dirs.append(Path("/some/dir"))
        assert result.needs_repair is True

    def test_was_repaired_property(self):
        """Test was_repaired property."""
        result = StructureValidationResult()
        assert result.was_repaired is False

        result.repaired_dirs.append(Path("/some/dir"))
        assert result.was_repaired is True


class TestValidateUserDirectory:
    """Tests for validate_user_directory function."""

    def test_validate_nonexistent_directory_with_auto_heal(self, tmp_path):
        """Test validation creates missing directory with auto-heal."""
        config_dir = tmp_path / "nonexistent"
        result = validate_user_directory(config_dir, auto_heal=True, verbose=False)

        assert config_dir.exists()
        assert config_dir in result.repaired_dirs
        assert result.was_repaired is True

    def test_validate_nonexistent_directory_without_auto_heal(self, tmp_path):
        """Test validation fails for missing directory without auto-heal."""
        config_dir = tmp_path / "nonexistent"
        result = validate_user_directory(config_dir, auto_heal=False, verbose=False)

        assert not config_dir.exists()
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_missing_subdirectories_with_auto_heal(self, tmp_path):
        """Test validation creates missing subdirectories with auto-heal."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        result = validate_user_directory(config_dir, auto_heal=True, verbose=False)

        # Check critical subdirectories were created
        assert (config_dir / "presets").exists()
        assert (config_dir / "cache").exists()
        assert (config_dir / "components").exists()
        assert (config_dir / "components" / "claude_md").exists()
        assert (config_dir / "components" / "gitignore").exists()

        assert result.was_repaired is True
        assert len(result.repaired_dirs) > 0

    def test_validate_missing_subdirectories_without_auto_heal(self, tmp_path):
        """Test validation detects missing subdirectories without auto-heal."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        result = validate_user_directory(config_dir, auto_heal=False, verbose=False)

        # Check subdirectories were not created
        assert not (config_dir / "presets").exists()
        assert result.was_repaired is False
        assert len(result.missing_dirs) > 0

    def test_validate_complete_directory(self, tmp_path):
        """Test validation passes for complete directory structure."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create all required subdirectories
        (config_dir / "presets").mkdir()
        (config_dir / "cache").mkdir()
        (config_dir / "components").mkdir()
        (config_dir / "components" / "claude_md").mkdir()
        (config_dir / "components" / "gitignore").mkdir()
        (config_dir / "components" / "commands").mkdir()
        (config_dir / "components" / "agents").mkdir()
        (config_dir / "components" / "hooks").mkdir()
        (config_dir / "components" / "output_styles").mkdir()
        (config_dir / "components" / "mcp").mkdir()
        (config_dir / "components" / "settings_json").mkdir()
        (config_dir / "components" / "settings_local_json").mkdir()
        (config_dir / "components" / "statusline").mkdir()
        (config_dir / "components" / "plugins").mkdir()
        (config_dir / "components" / "skills").mkdir()

        # Create config file
        (config_dir / "config.toml").write_text("# config", encoding="utf-8")

        result = validate_user_directory(config_dir, auto_heal=False, verbose=False)

        assert result.is_valid is True
        assert len(result.missing_dirs) == 0
        assert result.was_repaired is False


class TestValidatePresetIntegrity:
    """Tests for validate_preset_integrity function."""

    def test_validate_nonexistent_preset_directory(self, tmp_path):
        """Test validation fails for nonexistent preset."""
        preset_dir = tmp_path / "nonexistent"
        result = validate_preset_integrity(preset_dir, verbose=False)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_preset_without_toml(self, tmp_path):
        """Test validation fails when claudefig.toml missing."""
        preset_dir = tmp_path / "preset"
        preset_dir.mkdir()

        result = validate_preset_integrity(preset_dir, verbose=False)

        assert result.is_valid is False
        assert any("claudefig.toml" in error for error in result.errors)

    def test_validate_preset_with_empty_components_section(self, tmp_path):
        """Test validation passes with empty components section."""
        preset_dir = tmp_path / "preset"
        preset_dir.mkdir()

        toml_content = """
[claudefig]
version = "2.0"

[components]
"""
        (preset_dir / "claudefig.toml").write_text(toml_content, encoding="utf-8")

        result = validate_preset_integrity(preset_dir, verbose=False)

        assert result.is_valid is True

    def test_validate_preset_missing_component_files(self, tmp_path):
        """Test validation detects missing component files."""
        preset_dir = tmp_path / "preset"
        preset_dir.mkdir()
        (preset_dir / "components").mkdir()

        toml_content = """
[claudefig]
version = "2.0"

[components.claude_md]
variants = ["default"]
required_files = ["CLAUDE.md"]
"""
        (preset_dir / "claudefig.toml").write_text(toml_content, encoding="utf-8")

        result = validate_preset_integrity(preset_dir, verbose=False)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("Component variant missing" in error for error in result.errors)

    def test_validate_complete_preset(self, tmp_path):
        """Test validation passes for complete preset."""
        preset_dir = tmp_path / "preset"
        preset_dir.mkdir()
        (preset_dir / "components").mkdir()
        (preset_dir / "components" / "claude_md").mkdir()
        (preset_dir / "components" / "claude_md" / "default").mkdir()

        toml_content = """
[claudefig]
version = "2.0"

[components.claude_md]
variants = ["default"]
required_files = ["CLAUDE.md"]
"""
        (preset_dir / "claudefig.toml").write_text(toml_content, encoding="utf-8")
        (preset_dir / "components" / "claude_md" / "default" / "CLAUDE.md").write_text(
            "# CLAUDE.md", encoding="utf-8"
        )

        result = validate_preset_integrity(preset_dir, verbose=False)

        assert result.is_valid is True
        assert len(result.errors) == 0


class TestInitializationMarker:
    """Tests for initialization marker functions."""

    def test_create_and_check_marker(self, tmp_path):
        """Test creating and checking initialization marker."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Initially no marker
        assert check_initialization_marker(config_dir) is False

        # Create marker
        assert create_initialization_marker(config_dir) is True

        # Check marker exists
        assert check_initialization_marker(config_dir) is True

        # Verify marker file content
        marker_file = config_dir / ".initialized"
        content = marker_file.read_text(encoding="utf-8")
        assert "initialization completed successfully" in content.lower()

    def test_create_marker_fails_gracefully(self, tmp_path):
        """Test marker creation fails gracefully for invalid directory."""
        config_dir = tmp_path / "nonexistent" / "nested" / "path"

        result = create_initialization_marker(config_dir)

        assert result is False
