"""Tests for PresetValidator."""

import pytest
import tomli_w

from claudefig.preset_validator import PresetValidator


@pytest.fixture
def preset_validator(tmp_path):
    """Create a PresetValidator with temporary directory."""
    global_dir = tmp_path / "global_presets"
    global_dir.mkdir(parents=True)
    return PresetValidator(global_presets_dir=global_dir)


class TestValidatePresetConfig:
    """Tests for validate_preset_config method."""

    def test_validate_valid_preset(self, tmp_path):
        """Test validating a valid preset config."""
        preset_file = tmp_path / "valid.toml"
        valid_data = {
            "claudefig": {
                "version": "2.0",
                "schema_version": "2.0",
                "description": "Valid preset",
            },
            "files": [
                {
                    "id": "test-file",
                    "type": "claude_md",
                    "preset": "claude_md:default",
                    "path": "CLAUDE.md",
                    "enabled": True,
                    "variables": {},
                }
            ],
        }

        with open(preset_file, "wb") as f:
            tomli_w.dump(valid_data, f)

        validator = PresetValidator(global_presets_dir=tmp_path)
        result = validator.validate_preset_config(preset_file)

        assert result.valid is True
        assert not result.has_errors

    def test_validate_missing_claudefig_section(self, tmp_path):
        """Test validating preset missing [claudefig] section."""
        preset_file = tmp_path / "missing_section.toml"
        invalid_data = {"files": []}

        with open(preset_file, "wb") as f:
            tomli_w.dump(invalid_data, f)

        validator = PresetValidator(global_presets_dir=tmp_path)
        result = validator.validate_preset_config(preset_file)

        assert result.valid is False
        assert result.has_errors
        assert any("Missing required section: [claudefig]" in e for e in result.errors)

    def test_validate_missing_files_section(self, tmp_path):
        """Test validating preset missing [[files]] section."""
        preset_file = tmp_path / "missing_files.toml"
        invalid_data = {"claudefig": {"version": "2.0"}}

        with open(preset_file, "wb") as f:
            tomli_w.dump(invalid_data, f)

        validator = PresetValidator(global_presets_dir=tmp_path)
        result = validator.validate_preset_config(preset_file)

        assert result.valid is False
        assert result.has_errors
        assert any("Missing required section: [[files]]" in e for e in result.errors)

    def test_validate_missing_file_fields(self, tmp_path):
        """Test validating preset with file instance missing required fields."""
        preset_file = tmp_path / "missing_fields.toml"
        invalid_data = {
            "claudefig": {"version": "2.0"},
            "files": [
                {
                    "id": "incomplete",
                    # Missing: type, preset, path
                }
            ],
        }

        with open(preset_file, "wb") as f:
            tomli_w.dump(invalid_data, f)

        validator = PresetValidator(global_presets_dir=tmp_path)
        result = validator.validate_preset_config(preset_file)

        assert result.valid is False
        assert result.has_errors

    def test_validate_invalid_file_type(self, tmp_path):
        """Test validating preset with invalid file type."""
        preset_file = tmp_path / "invalid_type.toml"
        invalid_data = {
            "claudefig": {"version": "2.0"},
            "files": [
                {
                    "id": "test",
                    "type": "invalid_type",
                    "preset": "test:default",
                    "path": "test.md",
                }
            ],
        }

        with open(preset_file, "wb") as f:
            tomli_w.dump(invalid_data, f)

        validator = PresetValidator(global_presets_dir=tmp_path)
        result = validator.validate_preset_config(preset_file)

        assert result.valid is False
        assert result.has_errors
        assert any("invalid file type" in e for e in result.errors)

    def test_validate_nonexistent_file(self, tmp_path):
        """Test validating a file that doesn't exist."""
        nonexistent = tmp_path / "does_not_exist.toml"

        validator = PresetValidator(global_presets_dir=tmp_path)
        result = validator.validate_preset_config(nonexistent)

        assert result.valid is False
        assert result.has_errors
        assert any("not found" in e for e in result.errors)

    def test_validate_invalid_toml(self, tmp_path):
        """Test validating a file with invalid TOML syntax."""
        invalid_toml = tmp_path / "invalid.toml"
        with open(invalid_toml, "w", encoding="utf-8") as f:
            f.write("[incomplete")  # Invalid TOML

        validator = PresetValidator(global_presets_dir=tmp_path)
        result = validator.validate_preset_config(invalid_toml)

        assert result.valid is False
        assert result.has_errors
        assert any("TOML syntax" in e for e in result.errors)


class TestValidateAllPresets:
    """Tests for validate_all_presets method."""

    def test_validate_all_presets(self, tmp_path):
        """Test validating all global presets (directory-based structure)."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Create valid and invalid presets using directory structure
        valid_data = {
            "claudefig": {"version": "2.0"},
            "files": [],
        }
        invalid_data = {"missing": "sections"}

        # Create directory-based presets
        valid_preset_dir = global_dir / "valid"
        valid_preset_dir.mkdir()
        valid_file = valid_preset_dir / "claudefig.toml"
        with open(valid_file, "wb") as f:
            tomli_w.dump(valid_data, f)

        invalid_preset_dir = global_dir / "invalid"
        invalid_preset_dir.mkdir()
        invalid_file = invalid_preset_dir / "claudefig.toml"
        with open(invalid_file, "wb") as f:
            tomli_w.dump(invalid_data, f)

        validator = PresetValidator(global_presets_dir=global_dir)

        results = validator.validate_all_presets()

        assert "valid" in results
        assert "invalid" in results
        assert results["valid"].valid is True
        assert results["invalid"].valid is False


class TestGetValidationSummary:
    """Tests for get_validation_summary method."""

    def test_get_validation_summary(self, tmp_path):
        """Test getting validation summary for all presets (directory-based structure)."""
        global_dir = tmp_path / "global"
        global_dir.mkdir(parents=True)

        # Create various presets using directory structure
        valid_data = {"claudefig": {"version": "2.0"}, "files": []}
        valid_preset_dir = global_dir / "valid"
        valid_preset_dir.mkdir()
        valid_file = valid_preset_dir / "claudefig.toml"
        with open(valid_file, "wb") as f:
            tomli_w.dump(valid_data, f)

        invalid_data = {}
        invalid_preset_dir = global_dir / "invalid"
        invalid_preset_dir.mkdir()
        invalid_file = invalid_preset_dir / "claudefig.toml"
        with open(invalid_file, "wb") as f:
            tomli_w.dump(invalid_data, f)

        validator = PresetValidator(global_presets_dir=global_dir)

        summary = validator.get_validation_summary()

        assert summary["total"] == 2
        assert summary["valid"] == 1
        assert summary["invalid"] == 1
        assert "results" in summary
        assert len(summary["results"]) == 2
