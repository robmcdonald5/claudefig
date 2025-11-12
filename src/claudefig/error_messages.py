"""Standardized error messages for claudefig CLI and TUI.

This module provides consistent error messaging across the application,
ensuring uniform formatting, color schemes, and terminology.
"""

from typing import Literal

# Color scheme constants for Rich markup
COLOR_ERROR = "red"
COLOR_WARNING = "yellow"
COLOR_INFO = "blue"
COLOR_SUCCESS = "green"
COLOR_HIGHLIGHT = "cyan"
COLOR_DIM = "dim"

# Message type
MessageSeverity = Literal["error", "warning", "information", "success"]


class ErrorMessages:
    """Centralized error message templates with consistent formatting."""

    # --- Resource Not Found Errors ---

    @staticmethod
    def not_found(resource_type: str, identifier: str) -> str:
        """Format a 'not found' error message.

        Args:
            resource_type: Type of resource (e.g., "file instance", "preset", "template")
            identifier: Identifier of the missing resource

        Returns:
            Formatted error message
        """
        return f"{resource_type.capitalize()} not found: {identifier}"

    @staticmethod
    def config_file_not_found(path: str) -> str:
        """Format error for missing configuration file.

        Args:
            path: Path where config was expected

        Returns:
            Formatted error message
        """
        return f"No configuration file found in {path}"

    # --- Validation Errors ---

    @staticmethod
    def validation_failed(details: str | None = None) -> str:
        """Format a validation failure message.

        Args:
            details: Optional details about the validation failure

        Returns:
            Formatted error message
        """
        if details:
            return f"Validation failed: {details}"
        return "Validation failed"

    @staticmethod
    def invalid_type(
        type_name: str, value: str, valid_options: list[str] | None = None
    ) -> str:
        """Format an invalid type error message.

        Args:
            type_name: Name of the type (e.g., "file type")
            value: Invalid value provided
            valid_options: Optional list of valid values

        Returns:
            Formatted error message with optional valid options
        """
        msg = f"Invalid {type_name}: {value}"
        if valid_options:
            msg += f" (valid: {', '.join(valid_options)})"
        return msg

    @staticmethod
    def empty_value(field_name: str) -> str:
        """Format an empty value error message.

        Args:
            field_name: Name of the field that cannot be empty

        Returns:
            Formatted error message
        """
        return f"{field_name.capitalize()} cannot be empty"

    # --- Operation Errors ---

    @staticmethod
    def operation_failed(operation: str, details: str | None = None) -> str:
        """Format a generic operation failure message.

        Args:
            operation: Operation that failed (e.g., "initialization", "saving file")
            details: Optional exception or error details

        Returns:
            Formatted error message
        """
        if details:
            return f"Error during {operation}: {details}"
        return f"Error during {operation}"

    @staticmethod
    def file_exists(path: str) -> str:
        """Format error for file already existing.

        Args:
            path: Path to the existing file

        Returns:
            Formatted error message
        """
        return f"Configuration file already exists in {path}"

    @staticmethod
    def failed_to_perform(action: str, resource_type: str, identifier: str) -> str:
        """Format error for failed action on resource.

        Args:
            action: Action that failed (e.g., "remove", "update", "enable")
            resource_type: Type of resource (e.g., "file instance", "preset")
            identifier: Resource identifier

        Returns:
            Formatted error message
        """
        return f"Failed to {action} {resource_type}: {identifier}"

    # --- Success Messages ---

    @staticmethod
    def success(
        action: str,
        resource_type: str | None = None,
        identifier: str | None = None,
    ) -> str:
        """Format a success message.

        Args:
            action: Action performed (e.g., "added", "removed", "updated")
            resource_type: Optional type of resource affected
            identifier: Optional identifier of the affected resource

        Returns:
            Formatted success message
        """
        parts = [action.capitalize()]
        if resource_type:
            parts.append(resource_type)
        if identifier:
            parts.append(f": {identifier}")
        return " ".join(parts)

    # --- Warning Messages ---

    @staticmethod
    def no_changes_made() -> str:
        """Format warning for no changes made.

        Returns:
            Formatted warning message
        """
        return "No changes specified"

    @staticmethod
    def partial_failure(total: int, failed: int) -> str:
        """Format warning for partial operation failure.

        Args:
            total: Total number of operations attempted
            failed: Number of operations that failed

        Returns:
            Formatted warning message
        """
        return f"{failed} of {total} operations failed"

    # --- Info Messages ---

    @staticmethod
    def no_resources(resource_type: str) -> str:
        """Format info message for no resources found.

        Args:
            resource_type: Type of resource (plural form, e.g., "file instances")

        Returns:
            Formatted info message
        """
        return f"No {resource_type} configured"

    @staticmethod
    def use_command_hint(command: str, purpose: str) -> str:
        """Format a command usage hint.

        Args:
            command: Command to run
            purpose: Purpose of the command

        Returns:
            Formatted hint message
        """
        return f"Use '{command}' to {purpose}"


class FormattedMessages:
    """Formatted error messages for CLI (with Rich markup)."""

    @staticmethod
    def error(message: str) -> str:
        """Format as error with red color.

        Args:
            message: Error message

        Returns:
            Rich-formatted error message
        """
        return f"[{COLOR_ERROR}]Error:[/{COLOR_ERROR}] {message}"

    @staticmethod
    def warning(message: str) -> str:
        """Format as warning with yellow color.

        Args:
            message: Warning message

        Returns:
            Rich-formatted warning message
        """
        return f"[{COLOR_WARNING}]Warning:[/{COLOR_WARNING}] {message}"

    @staticmethod
    def success(message: str) -> str:
        """Format as success with green checkmark.

        Args:
            message: Success message

        Returns:
            Rich-formatted success message
        """
        return f"[{COLOR_SUCCESS}]+[/{COLOR_SUCCESS}] {message}"

    @staticmethod
    def info(message: str) -> str:
        """Format as info with blue color.

        Args:
            message: Info message

        Returns:
            Rich-formatted info message
        """
        return f"[{COLOR_INFO}]Info:[/{COLOR_INFO}] {message}"

    @staticmethod
    def highlight(text: str) -> str:
        """Highlight text in cyan.

        Args:
            text: Text to highlight

        Returns:
            Highlighted text
        """
        return f"[{COLOR_HIGHLIGHT}]{text}[/{COLOR_HIGHLIGHT}]"

    @staticmethod
    def dim(text: str) -> str:
        """Dim text for secondary information.

        Args:
            text: Text to dim

        Returns:
            Dimmed text
        """
        return f"[{COLOR_DIM}]{text}[/{COLOR_DIM}]"


# Convenience functions for common error patterns
def format_cli_error(message: str) -> str:
    """Format an error message for CLI output.

    Args:
        message: Error message

    Returns:
        Formatted error message with Rich markup
    """
    return FormattedMessages.error(message)


def format_cli_warning(message: str) -> str:
    """Format a warning message for CLI output.

    Args:
        message: Warning message

    Returns:
        Formatted warning message with Rich markup
    """
    return FormattedMessages.warning(message)


def format_cli_success(message: str) -> str:
    """Format a success message for CLI output.

    Args:
        message: Success message

    Returns:
        Formatted success message with Rich markup
    """
    return FormattedMessages.success(message)


def format_cli_info(message: str) -> str:
    """Format an info message for CLI output.

    Args:
        message: Info message

    Returns:
        Formatted info message with Rich markup
    """
    return FormattedMessages.info(message)


def map_severity(severity: MessageSeverity) -> str:
    """Map severity level to Textual notify severity.

    Args:
        severity: Message severity level

    Returns:
        Textual-compatible severity string
    """
    # Textual uses "error", "warning", "information"
    if severity == "success":
        return "information"
    return severity
