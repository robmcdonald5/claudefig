"""Tests for custom exception hierarchy."""

from claudefig import exceptions


class TestClaudefigError:
    """Test base ClaudefigError class."""

    def test_basic_error_message(self):
        """Test error with just message."""
        error = exceptions.ClaudefigError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code is None
        assert error.details == {}

    def test_error_with_code(self):
        """Test error with error code."""
        error = exceptions.ClaudefigError("Test error", error_code="TEST_ERROR")

        assert str(error) == "[TEST_ERROR] Test error"
        assert error.error_code == "TEST_ERROR"

    def test_error_with_details(self):
        """Test error with details dictionary."""
        error = exceptions.ClaudefigError(
            "Test error", details={"key": "value", "count": 42}
        )

        assert error.details == {"key": "value", "count": 42}


class TestValidationErrors:
    """Test validation error classes."""

    def test_invalid_preset_name_basic(self):
        """Test InvalidPresetNameError without reason."""
        error = exceptions.InvalidPresetNameError("bad-name")

        assert "Invalid preset name: 'bad-name'" in str(error)
        assert error.error_code == "INVALID_PRESET_NAME"
        assert error.details["name"] == "bad-name"

    def test_invalid_preset_name_with_reason(self):
        """Test InvalidPresetNameError with reason."""
        error = exceptions.InvalidPresetNameError(
            "123", reason="cannot start with number"
        )

        assert "'123'" in str(error)
        assert "cannot start with number" in str(error)

    def test_invalid_file_type(self):
        """Test InvalidFileTypeError."""
        error = exceptions.InvalidFileTypeError("unknown_type")

        assert "Invalid or unsupported file type: 'unknown_type'" in str(error)
        assert error.error_code == "INVALID_FILE_TYPE"
        assert error.details["file_type"] == "unknown_type"

    def test_invalid_config_key_basic(self):
        """Test InvalidConfigKeyError without reason."""
        error = exceptions.InvalidConfigKeyError("bad.key")

        assert "Invalid config key: 'bad.key'" in str(error)
        assert error.error_code == "INVALID_CONFIG_KEY"

    def test_invalid_config_key_with_reason(self):
        """Test InvalidConfigKeyError with reason."""
        error = exceptions.InvalidConfigKeyError("key", reason="reserved keyword")

        assert "'key'" in str(error)
        assert "reserved keyword" in str(error)

    def test_instance_validation_error(self):
        """Test InstanceValidationError."""
        errors = ["Missing required field 'path'", "Invalid type"]
        error = exceptions.InstanceValidationError("inst_123", errors)

        assert "inst_123" in str(error)
        assert "Missing required field 'path'" in str(error)
        assert error.error_code == "INSTANCE_VALIDATION_FAILED"
        assert error.details["instance_id"] == "inst_123"
        assert error.details["errors"] == errors

    def test_circular_dependency_error(self):
        """Test CircularDependencyError."""
        cycle = ["preset_a", "preset_b", "preset_c", "preset_a"]
        error = exceptions.CircularDependencyError(cycle)

        assert "Circular dependency" in str(error)
        assert "preset_a -> preset_b -> preset_c -> preset_a" in str(error)
        assert error.error_code == "CIRCULAR_DEPENDENCY"
        assert error.details["cycle"] == cycle


class TestResourceNotFoundErrors:
    """Test resource not found error classes."""

    def test_preset_not_found(self):
        """Test PresetNotFoundError."""
        error = exceptions.PresetNotFoundError("claude_md:missing")

        assert "Preset not found: 'claude_md:missing'" in str(error)
        assert error.error_code == "PRESET_NOT_FOUND"
        assert error.details["preset_id"] == "claude_md:missing"

    def test_template_not_found_basic(self):
        """Test TemplateNotFoundError without preset_id."""
        error = exceptions.TemplateNotFoundError("/path/to/missing.md")

        assert "Template file not found: '/path/to/missing.md'" in str(error)
        assert error.error_code == "TEMPLATE_NOT_FOUND"
        assert error.details["template_path"] == "/path/to/missing.md"

    def test_template_not_found_with_preset(self):
        """Test TemplateNotFoundError with preset_id."""
        error = exceptions.TemplateNotFoundError(
            "/path/to/missing.md", preset_id="claude_md:custom"
        )

        assert "/path/to/missing.md" in str(error)
        assert "claude_md:custom" in str(error)
        assert error.details["preset_id"] == "claude_md:custom"

    def test_instance_not_found(self):
        """Test InstanceNotFoundError."""
        error = exceptions.InstanceNotFoundError("inst_999")

        assert "File instance not found: 'inst_999'" in str(error)
        assert error.error_code == "INSTANCE_NOT_FOUND"
        assert error.details["instance_id"] == "inst_999"

    def test_config_file_not_found_basic(self):
        """Test ConfigFileNotFoundError without path."""
        error = exceptions.ConfigFileNotFoundError()

        assert "No configuration file found" in str(error)
        assert error.error_code == "CONFIG_NOT_FOUND"
        assert error.details == {}

    def test_config_file_not_found_with_path(self):
        """Test ConfigFileNotFoundError with path."""
        error = exceptions.ConfigFileNotFoundError(path="/project/dir")

        assert "No configuration file found in '/project/dir'" in str(error)
        assert error.details["path"] == "/project/dir"


class TestResourceConflictErrors:
    """Test resource conflict error classes."""

    def test_preset_exists(self):
        """Test PresetExistsError."""
        error = exceptions.PresetExistsError("claude_md:duplicate")

        assert "Preset already exists: 'claude_md:duplicate'" in str(error)
        assert error.error_code == "PRESET_EXISTS"
        assert error.details["preset_id"] == "claude_md:duplicate"

    def test_instance_exists(self):
        """Test InstanceExistsError."""
        error = exceptions.InstanceExistsError("inst_123")

        assert "File instance already exists: 'inst_123'" in str(error)
        assert error.error_code == "INSTANCE_EXISTS"
        assert error.details["instance_id"] == "inst_123"

    def test_config_file_exists(self):
        """Test ConfigFileExistsError."""
        error = exceptions.ConfigFileExistsError("/project/claudefig.toml")

        assert "Configuration file already exists" in str(error)
        assert error.error_code == "CONFIG_EXISTS"
        assert error.details["path"] == "/project/claudefig.toml"


class TestPermissionErrors:
    """Test permission/access error classes."""

    def test_builtin_modification_error_default_operation(self):
        """Test BuiltInModificationError with default operation."""
        error = exceptions.BuiltInModificationError("claude_md:default")

        assert "Cannot modify built-in preset: 'claude_md:default'" in str(error)
        assert error.error_code == "BUILTIN_MODIFICATION"
        assert error.details["operation"] == "modify"

    def test_builtin_modification_error_delete_operation(self):
        """Test BuiltInModificationError with delete operation."""
        error = exceptions.BuiltInModificationError(
            "claude_md:default", operation="delete"
        )

        assert "Cannot delete built-in preset: 'claude_md:default'" in str(error)
        assert error.details["operation"] == "delete"

    def test_default_preset_protection_error(self):
        """Test DefaultPresetProtectionError."""
        error = exceptions.DefaultPresetProtectionError()

        assert "Cannot delete the 'default' preset" in str(error)
        assert "protected" in str(error)
        assert error.error_code == "DEFAULT_PRESET_PROTECTED"


class TestTemplateErrors:
    """Test template-related error classes."""

    def test_template_render_error(self):
        """Test TemplateRenderError."""
        error = exceptions.TemplateRenderError(
            "/path/template.md", reason="Syntax error at line 5"
        )

        assert "Failed to render template '/path/template.md'" in str(error)
        assert "Syntax error at line 5" in str(error)
        assert error.error_code == "TEMPLATE_RENDER_FAILED"
        assert error.details["template_path"] == "/path/template.md"
        assert error.details["reason"] == "Syntax error at line 5"

    def test_missing_variable_error(self):
        """Test MissingVariableError."""
        error = exceptions.MissingVariableError("project_name", "/path/template.md")

        assert "Missing required variable 'project_name'" in str(error)
        assert "'/path/template.md'" in str(error)
        assert error.error_code == "MISSING_VARIABLE"
        assert error.details["variable_name"] == "project_name"
        assert error.details["template_path"] == "/path/template.md"


class TestFileOperationErrors:
    """Test file operation error classes."""

    def test_file_write_error(self):
        """Test FileWriteError."""
        error = exceptions.FileWriteError("/path/file.txt", reason="Permission denied")

        assert "Failed to write file '/path/file.txt'" in str(error)
        assert "Permission denied" in str(error)
        assert error.error_code == "FILE_WRITE_FAILED"
        assert error.details["path"] == "/path/file.txt"
        assert error.details["reason"] == "Permission denied"

    def test_file_read_error(self):
        """Test FileReadError."""
        error = exceptions.FileReadError("/path/file.txt", reason="File corrupted")

        assert "Failed to read file '/path/file.txt'" in str(error)
        assert "File corrupted" in str(error)
        assert error.error_code == "FILE_READ_FAILED"
        assert error.details["path"] == "/path/file.txt"
        assert error.details["reason"] == "File corrupted"


class TestInitializationErrors:
    """Test initialization error classes."""

    def test_initialization_rollback_error(self):
        """Test InitializationRollbackError."""
        failed_files = ["CLAUDE.md", "README.md"]
        errors = ["Failed to write CLAUDE.md", "Template not found for README.md"]
        error = exceptions.InitializationRollbackError(failed_files, errors)

        assert "Initialization failed and was rolled back" in str(error)
        assert "Failed to write CLAUDE.md" in str(error)
        assert "Template not found" in str(error)
        assert error.error_code == "INIT_ROLLBACK"
        assert error.details["failed_files"] == failed_files
        assert error.details["errors"] == errors


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_claudefig_error(self):
        """Test all custom exceptions inherit from ClaudefigError."""
        exception_classes = [
            exceptions.ValidationError,
            exceptions.ResourceNotFoundError,
            exceptions.ResourceConflictError,
            exceptions.AccessDeniedError,
            exceptions.TemplateError,
            exceptions.FileOperationError,
            exceptions.InitializationError,
        ]

        for exc_class in exception_classes:
            assert issubclass(exc_class, exceptions.ClaudefigError)

    def test_specific_exceptions_inherit_from_base(self):
        """Test specific exceptions inherit from their base classes."""
        # Validation errors
        assert issubclass(exceptions.InvalidPresetNameError, exceptions.ValidationError)
        assert issubclass(exceptions.InvalidFileTypeError, exceptions.ValidationError)

        # Resource not found errors
        assert issubclass(
            exceptions.PresetNotFoundError, exceptions.ResourceNotFoundError
        )
        assert issubclass(
            exceptions.TemplateNotFoundError, exceptions.ResourceNotFoundError
        )

        # Conflict errors
        assert issubclass(
            exceptions.PresetExistsError, exceptions.ResourceConflictError
        )
        assert issubclass(
            exceptions.InstanceExistsError, exceptions.ResourceConflictError
        )

        # Permission errors
        assert issubclass(
            exceptions.BuiltInModificationError, exceptions.AccessDeniedError
        )

        # Template errors
        assert issubclass(exceptions.TemplateRenderError, exceptions.TemplateError)
        assert issubclass(exceptions.MissingVariableError, exceptions.TemplateError)

        # File operation errors
        assert issubclass(exceptions.FileWriteError, exceptions.FileOperationError)
        assert issubclass(exceptions.FileReadError, exceptions.FileOperationError)
