"""claudefig - Universal config CLI tool for Claude Code repository setup."""

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

# Import custom exceptions for convenience
from .exceptions import (
    AccessDeniedError,
    BuiltInModificationError,
    CircularDependencyError,
    ClaudefigError,
    ConfigFileExistsError,
    ConfigFileNotFoundError,
    DefaultPresetProtectionError,
    FileOperationError,
    FileReadError,
    FileWriteError,
    InitializationError,
    InitializationRollbackError,
    InstanceExistsError,
    InstanceNotFoundError,
    InstanceValidationError,
    InvalidConfigKeyError,
    InvalidFileTypeError,
    InvalidPresetNameError,
    MissingVariableError,
    PresetExistsError,
    PresetNotFoundError,
    ResourceConflictError,
    ResourceNotFoundError,
    TemplateError,
    TemplateNotFoundError,
    TemplateRenderError,
    ValidationError,
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
    "AccessDeniedError",
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
