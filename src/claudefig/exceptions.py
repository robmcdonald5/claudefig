"""Custom exception hierarchy for claudefig.

This module defines a structured exception hierarchy for better error handling
and programmatic error detection throughout claudefig.
"""

from typing import Optional


class ClaudefigError(Exception):
    """Base exception for all claudefig errors.

    All custom exceptions should inherit from this class.

    Attributes:
        message: Human-readable error message
        error_code: Optional error code for programmatic handling
        details: Optional additional context/details
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        """Initialize exception.

        Args:
            message: Human-readable error message
            error_code: Optional error code (e.g., 'PRESET_NOT_FOUND')
            details: Optional dictionary with additional context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# === Validation Errors ===


class ValidationError(ClaudefigError):
    """Base class for validation errors."""

    pass


class InvalidPresetNameError(ValidationError):
    """Raised when a preset name is invalid."""

    def __init__(self, name: str, reason: Optional[str] = None):
        """Initialize exception.

        Args:
            name: The invalid preset name
            reason: Optional explanation of why it's invalid
        """
        message = f"Invalid preset name: '{name}'"
        if reason:
            message += f" - {reason}"
        super().__init__(
            message, error_code="INVALID_PRESET_NAME", details={"name": name}
        )


class InvalidFileTypeError(ValidationError):
    """Raised when a file type is invalid or unsupported."""

    def __init__(self, file_type: str):
        """Initialize exception.

        Args:
            file_type: The invalid file type
        """
        super().__init__(
            f"Invalid or unsupported file type: '{file_type}'",
            error_code="INVALID_FILE_TYPE",
            details={"file_type": file_type},
        )


class InvalidConfigKeyError(ValidationError):
    """Raised when a config key is invalid."""

    def __init__(self, key: str, reason: Optional[str] = None):
        """Initialize exception.

        Args:
            key: The invalid config key
            reason: Optional explanation
        """
        message = f"Invalid config key: '{key}'"
        if reason:
            message += f" - {reason}"
        super().__init__(message, error_code="INVALID_CONFIG_KEY", details={"key": key})


class InstanceValidationError(ValidationError):
    """Raised when file instance validation fails."""

    def __init__(self, instance_id: str, errors: list[str]):
        """Initialize exception.

        Args:
            instance_id: ID of the invalid instance
            errors: List of validation error messages
        """
        error_list = "\n  - ".join(errors)
        message = f"Validation failed for instance '{instance_id}':\n  - {error_list}"
        super().__init__(
            message,
            error_code="INSTANCE_VALIDATION_FAILED",
            details={"instance_id": instance_id, "errors": errors},
        )


class CircularDependencyError(ValidationError):
    """Raised when circular dependencies are detected in preset inheritance."""

    def __init__(self, cycle: list[str]):
        """Initialize exception.

        Args:
            cycle: List of preset names forming the circular dependency
        """
        cycle_str = " -> ".join(cycle)
        super().__init__(
            f"Circular dependency detected in preset inheritance: {cycle_str}",
            error_code="CIRCULAR_DEPENDENCY",
            details={"cycle": cycle},
        )


# === Resource Not Found Errors ===


class ResourceNotFoundError(ClaudefigError):
    """Base class for resource not found errors."""

    pass


class PresetNotFoundError(ResourceNotFoundError):
    """Raised when a preset cannot be found."""

    def __init__(self, preset_id: str):
        """Initialize exception.

        Args:
            preset_id: The preset ID that wasn't found
        """
        super().__init__(
            f"Preset not found: '{preset_id}'",
            error_code="PRESET_NOT_FOUND",
            details={"preset_id": preset_id},
        )


class TemplateNotFoundError(ResourceNotFoundError):
    """Raised when a template file cannot be found."""

    def __init__(self, template_path: str, preset_id: Optional[str] = None):
        """Initialize exception.

        Args:
            template_path: Path to the missing template
            preset_id: Optional preset ID that referenced this template
        """
        message = f"Template file not found: '{template_path}'"
        if preset_id:
            message += f" (referenced by preset '{preset_id}')"
        super().__init__(
            message,
            error_code="TEMPLATE_NOT_FOUND",
            details={"template_path": template_path, "preset_id": preset_id},
        )


class InstanceNotFoundError(ResourceNotFoundError):
    """Raised when a file instance cannot be found."""

    def __init__(self, instance_id: str):
        """Initialize exception.

        Args:
            instance_id: The instance ID that wasn't found
        """
        super().__init__(
            f"File instance not found: '{instance_id}'",
            error_code="INSTANCE_NOT_FOUND",
            details={"instance_id": instance_id},
        )


class ConfigFileNotFoundError(ResourceNotFoundError):
    """Raised when a config file cannot be found."""

    def __init__(self, path: Optional[str] = None):
        """Initialize exception.

        Args:
            path: Optional path where config was expected
        """
        message = "No configuration file found"
        if path:
            message += f" in '{path}'"
        super().__init__(
            message,
            error_code="CONFIG_NOT_FOUND",
            details={"path": path} if path else {},
        )


# === Resource Conflict Errors ===


class ResourceConflictError(ClaudefigError):
    """Base class for resource conflict errors."""

    pass


class PresetExistsError(ResourceConflictError):
    """Raised when trying to create a preset that already exists."""

    def __init__(self, preset_id: str):
        """Initialize exception.

        Args:
            preset_id: The preset ID that already exists
        """
        super().__init__(
            f"Preset already exists: '{preset_id}'",
            error_code="PRESET_EXISTS",
            details={"preset_id": preset_id},
        )


class InstanceExistsError(ResourceConflictError):
    """Raised when trying to create an instance that already exists."""

    def __init__(self, instance_id: str):
        """Initialize exception.

        Args:
            instance_id: The instance ID that already exists
        """
        super().__init__(
            f"File instance already exists: '{instance_id}'",
            error_code="INSTANCE_EXISTS",
            details={"instance_id": instance_id},
        )


class ConfigFileExistsError(ResourceConflictError):
    """Raised when trying to create a config file that already exists."""

    def __init__(self, path: str):
        """Initialize exception.

        Args:
            path: Path where config file already exists
        """
        super().__init__(
            f"Configuration file already exists at '{path}'",
            error_code="CONFIG_EXISTS",
            details={"path": path},
        )


# === Permission/Access Errors ===


class PermissionError(ClaudefigError):
    """Base class for permission/access errors."""

    pass


class BuiltInModificationError(PermissionError):
    """Raised when trying to modify or delete built-in presets."""

    def __init__(self, preset_id: str, operation: str = "modify"):
        """Initialize exception.

        Args:
            preset_id: The built-in preset ID
            operation: The attempted operation (modify, delete, etc.)
        """
        super().__init__(
            f"Cannot {operation} built-in preset: '{preset_id}'",
            error_code="BUILTIN_MODIFICATION",
            details={"preset_id": preset_id, "operation": operation},
        )


class DefaultPresetProtectionError(PermissionError):
    """Raised when trying to delete the 'default' preset."""

    def __init__(self):
        """Initialize exception."""
        super().__init__(
            "Cannot delete the 'default' preset - it is protected",
            error_code="DEFAULT_PRESET_PROTECTED",
        )


# === Template/Rendering Errors ===


class TemplateError(ClaudefigError):
    """Base class for template-related errors."""

    pass


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""

    def __init__(self, template_path: str, reason: str):
        """Initialize exception.

        Args:
            template_path: Path to the template that failed to render
            reason: Explanation of why rendering failed
        """
        super().__init__(
            f"Failed to render template '{template_path}': {reason}",
            error_code="TEMPLATE_RENDER_FAILED",
            details={"template_path": template_path, "reason": reason},
        )


class MissingVariableError(TemplateError):
    """Raised when a required template variable is missing."""

    def __init__(self, variable_name: str, template_path: str):
        """Initialize exception.

        Args:
            variable_name: Name of the missing variable
            template_path: Path to the template requiring the variable
        """
        super().__init__(
            f"Missing required variable '{variable_name}' for template '{template_path}'",
            error_code="MISSING_VARIABLE",
            details={"variable_name": variable_name, "template_path": template_path},
        )


# === File Operation Errors ===


class FileOperationError(ClaudefigError):
    """Base class for file operation errors."""

    pass


class FileWriteError(FileOperationError):
    """Raised when writing a file fails."""

    def __init__(self, path: str, reason: str):
        """Initialize exception.

        Args:
            path: Path where write failed
            reason: Explanation of why write failed
        """
        super().__init__(
            f"Failed to write file '{path}': {reason}",
            error_code="FILE_WRITE_FAILED",
            details={"path": path, "reason": reason},
        )


class FileReadError(FileOperationError):
    """Raised when reading a file fails."""

    def __init__(self, path: str, reason: str):
        """Initialize exception.

        Args:
            path: Path where read failed
            reason: Explanation of why read failed
        """
        super().__init__(
            f"Failed to read file '{path}': {reason}",
            error_code="FILE_READ_FAILED",
            details={"path": path, "reason": reason},
        )


# === Initialization Errors ===


class InitializationError(ClaudefigError):
    """Base class for initialization errors."""

    pass


class InitializationRollbackError(InitializationError):
    """Raised when initialization is rolled back due to errors."""

    def __init__(self, failed_files: list[str], errors: list[str]):
        """Initialize exception.

        Args:
            failed_files: List of files that failed to initialize
            errors: List of error messages
        """
        error_list = "\n  - ".join(errors)
        message = (
            f"Initialization failed and was rolled back. Errors:\n  - {error_list}"
        )
        super().__init__(
            message,
            error_code="INIT_ROLLBACK",
            details={"failed_files": failed_files, "errors": errors},
        )
