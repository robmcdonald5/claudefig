"""claudefig - Universal config CLI tool for Claude Code repository setup."""

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

# Import custom exceptions for convenience
from .exceptions import (
    ClaudefigError,
    ValidationError,
    InvalidPresetNameError,
    InvalidFileTypeError,
    InvalidConfigKeyError,
    InstanceValidationError,
    CircularDependencyError,
    ResourceNotFoundError,
    PresetNotFoundError,
    TemplateNotFoundError,
    InstanceNotFoundError,
    ConfigFileNotFoundError,
    ResourceConflictError,
    PresetExistsError,
    InstanceExistsError,
    ConfigFileExistsError,
    PermissionError,
    BuiltInModificationError,
    DefaultPresetProtectionError,
    TemplateError,
    TemplateRenderError,
    MissingVariableError,
    FileOperationError,
    FileWriteError,
    FileReadError,
    InitializationError,
    InitializationRollbackError,
)

__all__ = [
    "__version__",
    # Base exceptions
    "ClaudefigError",
    # Validation errors
    "ValidationError",
    "InvalidPresetNameError",
    "InvalidFileTypeError",
    "InvalidConfigKeyError",
    "InstanceValidationError",
    "CircularDependencyError",
    # Resource not found errors
    "ResourceNotFoundError",
    "PresetNotFoundError",
    "TemplateNotFoundError",
    "InstanceNotFoundError",
    "ConfigFileNotFoundError",
    # Resource conflict errors
    "ResourceConflictError",
    "PresetExistsError",
    "InstanceExistsError",
    "ConfigFileExistsError",
    # Permission errors
    "PermissionError",
    "BuiltInModificationError",
    "DefaultPresetProtectionError",
    # Template errors
    "TemplateError",
    "TemplateRenderError",
    "MissingVariableError",
    # File operation errors
    "FileOperationError",
    "FileWriteError",
    "FileReadError",
    # Initialization errors
    "InitializationError",
    "InitializationRollbackError",
]
