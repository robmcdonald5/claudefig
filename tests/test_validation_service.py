"""Tests for validation service layer."""

import tempfile
from pathlib import Path

from claudefig.services import validation_service


class TestValidateNotEmpty:
    """Test validate_not_empty() function."""

    def test_valid_non_empty_string(self):
        """Test valid non-empty string passes."""
        result = validation_service.validate_not_empty("test", "field")

        assert result.valid
        assert not result.has_errors

    def test_rejects_empty_string(self):
        """Test empty string is rejected."""
        result = validation_service.validate_not_empty("", "field")

        assert not result.valid
        assert result.has_errors
        assert "cannot be empty" in result.errors[0]

    def test_rejects_whitespace_only(self):
        """Test whitespace-only string is rejected."""
        result = validation_service.validate_not_empty("   ", "field")

        assert not result.valid
        assert "cannot be empty" in result.errors[0]

    def test_includes_field_name_in_error(self):
        """Test error message includes field name."""
        result = validation_service.validate_not_empty("", "preset_name")

        assert "preset_name" in result.errors[0]


class TestValidateIdentifier:
    """Test validate_identifier() function."""

    def test_valid_simple_identifier(self):
        """Test simple alphanumeric identifier."""
        result = validation_service.validate_identifier("mypreset", "name")

        assert result.valid
        assert not result.has_errors

    def test_valid_identifier_with_underscore(self):
        """Test identifier with underscores."""
        result = validation_service.validate_identifier("my_preset_1", "name")

        assert result.valid

    def test_valid_identifier_with_hyphen(self):
        """Test identifier with hyphens."""
        result = validation_service.validate_identifier("my-preset-1", "name")

        assert result.valid

    def test_valid_identifier_starting_with_letter(self):
        """Test identifier starting with letter."""
        result = validation_service.validate_identifier("a123", "name")

        assert result.valid

    def test_valid_identifier_starting_with_underscore(self):
        """Test identifier starting with underscore."""
        result = validation_service.validate_identifier("_private", "name")

        assert result.valid

    def test_rejects_empty_string(self):
        """Test empty string is rejected."""
        result = validation_service.validate_identifier("", "name")

        assert not result.valid
        assert "cannot be empty" in result.errors[0]

    def test_rejects_identifier_with_spaces(self):
        """Test identifier with spaces is rejected."""
        result = validation_service.validate_identifier("my preset", "name")

        assert not result.valid
        assert "letters, numbers, underscores, and hyphens" in result.errors[0]

    def test_rejects_identifier_starting_with_number(self):
        """Test identifier starting with number is rejected."""
        result = validation_service.validate_identifier("1preset", "name")

        assert not result.valid

    def test_rejects_identifier_with_special_chars(self):
        """Test identifier with special characters is rejected."""
        result = validation_service.validate_identifier("my$preset", "name")

        assert not result.valid


class TestValidatePathSafe:
    """Test validate_path_safe() function."""

    def test_valid_relative_path(self):
        """Test valid relative path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            result = validation_service.validate_path_safe("subdir/file.txt", repo_root)

            assert result.valid
            assert not result.has_errors

    def test_rejects_empty_path(self):
        """Test empty path is rejected."""
        repo_root = Path("/tmp")

        result = validation_service.validate_path_safe("", repo_root)

        assert not result.valid
        assert "cannot be empty" in result.errors[0]

    def test_rejects_absolute_path(self):
        """Test absolute path is rejected."""
        repo_root = Path("/tmp/repo")

        result = validation_service.validate_path_safe("/etc/passwd", repo_root)

        assert not result.valid
        # May trigger "must be relative" or "escape repository" depending on OS
        assert any(
            phrase in result.errors[0]
            for phrase in ["must be relative", "escape repository"]
        )

    def test_rejects_parent_directory_references(self):
        """Test parent directory references are rejected."""
        repo_root = Path("/tmp/repo")

        result = validation_service.validate_path_safe("../etc/passwd", repo_root)

        assert not result.valid
        assert "parent directory references" in result.errors[0]

    def test_rejects_path_that_escapes_repo(self):
        """Test path that would escape repo is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir()

            # Try to escape using symlink-like resolution
            result = validation_service.validate_path_safe(
                "subdir/../../outside", repo_root
            )

            # Should be rejected because resolved path escapes repo
            assert not result.valid


class TestValidateDictStructure:
    """Test validate_dict_structure() function."""

    def test_valid_dict_with_all_required_keys(self):
        """Test valid dictionary with all required keys."""
        data = {"name": "test", "type": "claude_md", "path": "CLAUDE.md"}

        result = validation_service.validate_dict_structure(
            data, ["name", "type", "path"], "instance"
        )

        assert result.valid
        assert not result.has_errors

    def test_rejects_non_dict(self):
        """Test non-dictionary data is rejected."""
        result = validation_service.validate_dict_structure(
            "not a dict", ["key"], "data"
        )

        assert not result.valid
        assert "must be a dictionary" in result.errors[0]

    def test_reports_missing_keys(self):
        """Test reports all missing required keys."""
        data = {"name": "test"}

        result = validation_service.validate_dict_structure(
            data, ["name", "type", "path"], "instance"
        )

        assert not result.valid
        assert len(result.errors) == 2
        assert any("type" in err for err in result.errors)
        assert any("path" in err for err in result.errors)

    def test_valid_dict_with_no_required_keys(self):
        """Test dictionary with no required keys."""
        data = {"any": "value"}

        result = validation_service.validate_dict_structure(data, [], "data")

        assert result.valid

    def test_includes_dict_name_in_error(self):
        """Test error includes dict name."""
        result = validation_service.validate_dict_structure(
            "string", ["key"], "my_config"
        )

        assert "my_config" in result.errors[0]


class TestValidateType:
    """Test validate_type() function."""

    def test_valid_string_type(self):
        """Test valid string type."""
        result = validation_service.validate_type("test", str, "name")

        assert result.valid

    def test_valid_int_type(self):
        """Test valid int type."""
        result = validation_service.validate_type(42, int, "count")

        assert result.valid

    def test_valid_bool_type(self):
        """Test valid bool type."""
        result = validation_service.validate_type(True, bool, "flag")

        assert result.valid

    def test_valid_dict_type(self):
        """Test valid dict type."""
        result = validation_service.validate_type({"key": "value"}, dict, "config")

        assert result.valid

    def test_rejects_wrong_type(self):
        """Test rejects wrong type."""
        result = validation_service.validate_type(42, str, "name")

        assert not result.valid
        assert "must be str" in result.errors[0]
        assert "got int" in result.errors[0]


class TestValidateInRange:
    """Test validate_in_range() function."""

    def test_value_within_range(self):
        """Test value within range is valid."""
        result = validation_service.validate_in_range(5, 1, 10, "count")

        assert result.valid

    def test_value_at_minimum(self):
        """Test value at minimum bound is valid."""
        result = validation_service.validate_in_range(1, 1, 10, "count")

        assert result.valid

    def test_value_at_maximum(self):
        """Test value at maximum bound is valid."""
        result = validation_service.validate_in_range(10, 1, 10, "count")

        assert result.valid

    def test_rejects_value_below_minimum(self):
        """Test value below minimum is rejected."""
        result = validation_service.validate_in_range(0, 1, 10, "count")

        assert not result.valid
        assert "between 1 and 10" in result.errors[0]
        assert "got 0" in result.errors[0]

    def test_rejects_value_above_maximum(self):
        """Test value above maximum is rejected."""
        result = validation_service.validate_in_range(11, 1, 10, "count")

        assert not result.valid
        assert "between 1 and 10" in result.errors[0]

    def test_works_with_floats(self):
        """Test works with float values."""
        result = validation_service.validate_in_range(5.5, 1.0, 10.0, "value")

        assert result.valid


class TestValidateOneOf:
    """Test validate_one_of() function."""

    def test_value_in_allowed_list(self):
        """Test value in allowed list is valid."""
        result = validation_service.validate_one_of(
            "claude_md", ["claude_md", "gitignore"], "type"
        )

        assert result.valid

    def test_rejects_value_not_in_list(self):
        """Test value not in list is rejected."""
        result = validation_service.validate_one_of(
            "invalid", ["claude_md", "gitignore"], "type"
        )

        assert not result.valid
        assert "must be one of" in result.errors[0]
        assert "invalid" in result.errors[0]

    def test_works_with_integers(self):
        """Test works with integer values."""
        result = validation_service.validate_one_of(2, [1, 2, 3], "choice")

        assert result.valid

    def test_works_with_mixed_types(self):
        """Test works with mixed type list."""
        result = validation_service.validate_one_of("a", ["a", 1, True], "value")

        assert result.valid


class TestValidateRegex:
    """Test validate_regex() function."""

    def test_value_matches_pattern(self):
        """Test value matching pattern is valid."""
        result = validation_service.validate_regex("test123", r"^[a-z]+\d+$", "code")

        assert result.valid

    def test_rejects_non_matching_pattern(self):
        """Test non-matching pattern is rejected."""
        result = validation_service.validate_regex("test", r"^\d+$", "code")

        assert not result.valid
        assert "does not match required pattern" in result.errors[0]

    def test_email_pattern(self):
        """Test email validation pattern."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        result_valid = validation_service.validate_regex(
            "test@example.com", pattern, "email"
        )
        assert result_valid.valid

        result_invalid = validation_service.validate_regex(
            "not-an-email", pattern, "email"
        )
        assert not result_invalid.valid


class TestMergeValidationResults:
    """Test merge_validation_results() function."""

    def test_merge_all_valid_results(self):
        """Test merging all valid results."""
        from claudefig.models import ValidationResult

        result1 = ValidationResult(valid=True)
        result2 = ValidationResult(valid=True)

        merged = validation_service.merge_validation_results(result1, result2)

        assert merged.valid
        assert not merged.has_errors

    def test_merge_includes_all_errors(self):
        """Test merged result includes all errors."""
        from claudefig.models import ValidationResult

        result1 = ValidationResult(valid=True)
        result1.add_error("Error 1")

        result2 = ValidationResult(valid=True)
        result2.add_error("Error 2")

        merged = validation_service.merge_validation_results(result1, result2)

        assert not merged.valid
        assert len(merged.errors) == 2
        assert "Error 1" in merged.errors
        assert "Error 2" in merged.errors

    def test_merge_includes_all_warnings(self):
        """Test merged result includes all warnings."""
        from claudefig.models import ValidationResult

        result1 = ValidationResult(valid=True)
        result1.add_warning("Warning 1")

        result2 = ValidationResult(valid=True)
        result2.add_warning("Warning 2")

        merged = validation_service.merge_validation_results(result1, result2)

        assert merged.valid  # Still valid with just warnings
        assert len(merged.warnings) == 2
        assert "Warning 1" in merged.warnings
        assert "Warning 2" in merged.warnings

    def test_merge_with_mixed_results(self):
        """Test merging valid and invalid results."""
        from claudefig.models import ValidationResult

        result1 = ValidationResult(valid=True)
        result2 = ValidationResult(valid=True)
        result2.add_error("Error")

        merged = validation_service.merge_validation_results(result1, result2)

        assert not merged.valid
        assert len(merged.errors) == 1

    def test_merge_empty_list(self):
        """Test merging no results."""
        merged = validation_service.merge_validation_results()

        assert merged.valid
        assert not merged.has_errors


class TestValidateFileExtension:
    """Test validate_file_extension() function."""

    def test_valid_markdown_extension(self):
        """Test valid markdown extension."""
        result = validation_service.validate_file_extension(
            "CLAUDE.md", [".md"], "file"
        )

        assert result.valid

    def test_valid_extension_case_insensitive(self):
        """Test extension matching is case-insensitive."""
        result = validation_service.validate_file_extension("FILE.MD", [".md"], "file")

        assert result.valid

    def test_multiple_allowed_extensions(self):
        """Test multiple allowed extensions."""
        result = validation_service.validate_file_extension(
            "config.toml", [".json", ".toml", ".yaml"], "config"
        )

        assert result.valid

    def test_rejects_wrong_extension(self):
        """Test rejects wrong extension."""
        result = validation_service.validate_file_extension(
            "script.py", [".md", ".txt"], "file"
        )

        assert not result.valid
        assert "must have one of these extensions" in result.errors[0]
        assert ".py" in result.errors[0]

    def test_rejects_no_extension(self):
        """Test rejects file with no extension."""
        result = validation_service.validate_file_extension("README", [".md"], "file")

        assert not result.valid


class TestValidateNoConflicts:
    """Test validate_no_conflicts() function."""

    def test_no_conflict_when_unique(self):
        """Test no conflict when value is unique."""
        result = validation_service.validate_no_conflicts(
            "new", ["existing1", "existing2"], "name"
        )

        assert result.valid

    def test_rejects_exact_duplicate(self):
        """Test rejects exact duplicate."""
        result = validation_service.validate_no_conflicts(
            "test", ["test", "other"], "name"
        )

        assert not result.valid
        assert "already exists" in result.errors[0]

    def test_case_sensitive_by_default(self):
        """Test comparison is case-sensitive by default."""
        result = validation_service.validate_no_conflicts("Test", ["test"], "name")

        assert result.valid  # Different case, no conflict

    def test_case_insensitive_when_specified(self):
        """Test case-insensitive comparison when specified."""
        result = validation_service.validate_no_conflicts(
            "Test", ["test"], "name", case_sensitive=False
        )

        assert not result.valid  # Same when case-insensitive
        assert "already exists" in result.errors[0]

    def test_no_conflict_with_empty_list(self):
        """Test no conflict with empty existing list."""
        result = validation_service.validate_no_conflicts("new", [], "name")

        assert result.valid
