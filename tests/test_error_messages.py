"""Tests for error_messages module."""

from claudefig.error_messages import ErrorMessages, FormattedMessages


class TestResourceNotFoundErrors:
    """Test resource not found error messages."""

    def test_not_found_basic(self):
        """Test not_found with basic resource type."""
        result = ErrorMessages.not_found("preset", "my-preset")
        assert result == "Preset not found: my-preset"

    def test_not_found_capitalizes_type(self):
        """Test that resource type is capitalized."""
        result = ErrorMessages.not_found("file instance", "test-1")
        assert result == "File instance not found: test-1"

    def test_config_file_not_found(self):
        """Test config_file_not_found message."""
        result = ErrorMessages.config_file_not_found("/path/to/project")
        assert result == "No configuration file found in /path/to/project"


class TestValidationErrors:
    """Test validation error messages."""

    def test_validation_failed_without_details(self):
        """Test validation_failed without details."""
        result = ErrorMessages.validation_failed()
        assert result == "Validation failed"

    def test_validation_failed_with_details(self):
        """Test validation_failed with details."""
        result = ErrorMessages.validation_failed("Path cannot be empty")
        assert result == "Validation failed: Path cannot be empty"

    def test_invalid_type_without_options(self):
        """Test invalid_type without valid options."""
        result = ErrorMessages.invalid_type("file type", "invalid")
        assert result == "Invalid file type: invalid"

    def test_invalid_type_with_options(self):
        """Test invalid_type with valid options list."""
        result = ErrorMessages.invalid_type(
            "file type", "invalid", ["claude_md", "gitignore", "commands"]
        )
        assert "Invalid file type: invalid" in result
        assert "(valid: claude_md, gitignore, commands)" in result

    def test_empty_value(self):
        """Test empty_value error message."""
        result = ErrorMessages.empty_value("preset name")
        assert result == "Preset name cannot be empty"

    def test_empty_value_capitalizes(self):
        """Test that empty_value capitalizes field name."""
        result = ErrorMessages.empty_value("path")
        assert result == "Path cannot be empty"


class TestOperationErrors:
    """Test operation error messages."""

    def test_operation_failed_without_details(self):
        """Test operation_failed without details."""
        result = ErrorMessages.operation_failed("syncing files")
        assert result == "Error during syncing files"

    def test_operation_failed_with_details(self):
        """Test operation_failed with details."""
        result = ErrorMessages.operation_failed("syncing files", "Permission denied")
        assert result == "Error during syncing files: Permission denied"

    def test_file_exists(self):
        """Test file_exists error message."""
        result = ErrorMessages.file_exists("/path/to/project")
        assert result == "Configuration file already exists in /path/to/project"

    def test_failed_to_perform(self):
        """Test failed_to_perform error message."""
        result = ErrorMessages.failed_to_perform("remove", "file instance", "test-1")
        assert result == "Failed to remove file instance: test-1"


class TestSuccessMessages:
    """Test success and info messages."""

    def test_success_with_all_params(self):
        """Test success message with all parameters."""
        result = ErrorMessages.success("added", "file instance", "test-1")
        assert result == "Added file instance : test-1"

    def test_success_with_action_and_type_only(self):
        """Test success message with action and resource type."""
        result = ErrorMessages.success("removed", "preset")
        assert result == "Removed preset"

    def test_success_with_action_only(self):
        """Test success message with action only."""
        result = ErrorMessages.success("completed")
        assert result == "Completed"

    def test_no_changes_made(self):
        """Test no_changes_made message."""
        result = ErrorMessages.no_changes_made()
        assert result == "No changes specified"

    def test_partial_failure(self):
        """Test partial_failure message."""
        result = ErrorMessages.partial_failure(10, 3)
        assert result == "3 of 10 operations failed"

    def test_no_resources(self):
        """Test no_resources message."""
        result = ErrorMessages.no_resources("presets")
        assert result == "No presets configured"


class TestHelpMessages:
    """Test help and hint messages."""

    def test_use_command_hint(self):
        """Test use_command_hint message."""
        result = ErrorMessages.use_command_hint(
            "claudefig init", "initialize a new project"
        )
        assert "claudefig init" in result
        assert "initialize a new project" in result


class TestFormatting:
    """Test Rich formatting functions from FormattedMessages class."""

    def test_error_formatting(self):
        """Test error message formatting."""
        result = FormattedMessages.error("Something went wrong")
        assert "[red]" in result
        assert "Something went wrong" in result
        assert "Error:" in result

    def test_warning_formatting(self):
        """Test warning message formatting."""
        result = FormattedMessages.warning("This is a warning")
        assert "[yellow]" in result
        assert "This is a warning" in result
        assert "Warning:" in result

    def test_success_formatting(self):
        """Test success message formatting."""
        result = FormattedMessages.success("Operation complete")
        assert "[green]" in result
        assert "Operation complete" in result

    def test_info_formatting(self):
        """Test info message formatting."""
        result = FormattedMessages.info("Here is some info")
        assert "[blue]" in result
        assert "Here is some info" in result
        assert "Info:" in result

    def test_highlight_formatting(self):
        """Test highlight text formatting."""
        result = FormattedMessages.highlight("important text")
        assert "[cyan]" in result
        assert "important text" in result

    def test_dim_formatting(self):
        """Test dim text formatting."""
        result = FormattedMessages.dim("secondary text")
        assert "[dim]" in result
        assert "secondary text" in result
