"""Validation service layer for common validation utilities.

This module provides reusable validation functions that can be shared across
different services and modules.
"""

import re
from pathlib import Path
from typing import Any

from claudefig.models import ValidationResult


def validate_not_empty(value: str, field_name: str) -> ValidationResult:
    """Validate that a string value is not empty.

    Args:
        value: String value to validate.
        field_name: Name of field (for error messages).

    Returns:
        ValidationResult with error if empty.
    """
    result = ValidationResult(valid=True)

    if not value or not value.strip():
        result.add_error(f"{field_name} cannot be empty")

    return result


def validate_identifier(value: str, field_name: str) -> ValidationResult:
    """Validate that a string is a valid identifier (alphanumeric, _, -).

    Valid identifiers:
    - Start with letter or underscore
    - Contain only letters, numbers, underscores, hyphens
    - No spaces or special characters

    Args:
        value: String value to validate.
        field_name: Name of field (for error messages).

    Returns:
        ValidationResult with error if invalid.

    Example:
        >>> validate_identifier("my-preset_1", "preset name")
        ValidationResult(valid=True, errors=[], warnings=[])
        >>> validate_identifier("my preset!", "preset name")
        ValidationResult(valid=False, errors=['...'], warnings=[])
    """
    result = ValidationResult(valid=True)

    if not value:
        result.add_error(f"{field_name} cannot be empty")
        return result

    # Pattern: start with letter/underscore, then alphanumeric, _, -
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_-]*$"

    if not re.match(pattern, value):
        result.add_error(
            f"{field_name} must start with a letter or underscore and "
            f"contain only letters, numbers, underscores, and hyphens"
        )

    return result


def validate_path_safe(path: str, repo_root: Path) -> ValidationResult:
    """Validate that a path is safe (no directory traversal, stays in repo).

    Args:
        path: Path to validate (should be relative).
        repo_root: Repository root path.

    Returns:
        ValidationResult with errors if unsafe.
    """
    result = ValidationResult(valid=True)

    if not path:
        result.add_error("Path cannot be empty")
        return result

    try:
        path_obj = Path(path)

        # Reject absolute paths
        if path_obj.is_absolute():
            result.add_error("Path must be relative")

        # Reject parent directory references
        if ".." in path_obj.parts:
            result.add_error("Path cannot contain parent directory references (../)")

        # Ensure resolved path stays within repo
        full_path = (repo_root / path_obj).resolve()
        if not str(full_path).startswith(str(repo_root.resolve())):
            result.add_error("Path would escape repository root")

    except (ValueError, OSError) as e:
        result.add_error(f"Invalid path: {e}")

    return result


def validate_dict_structure(
    data: Any, required_keys: list[str], dict_name: str = "data"
) -> ValidationResult:
    """Validate that data is a dictionary with required keys.

    Args:
        data: Data to validate.
        required_keys: List of required key names.
        dict_name: Name of dictionary (for error messages).

    Returns:
        ValidationResult with errors if structure invalid.
    """
    result = ValidationResult(valid=True)

    if not isinstance(data, dict):
        result.add_error(f"{dict_name} must be a dictionary")
        return result

    for key in required_keys:
        if key not in data:
            result.add_error(f"{dict_name} missing required key: '{key}'")

    return result


def validate_type(
    value: Any, expected_type: type, field_name: str
) -> ValidationResult:
    """Validate that a value is of expected type.

    Args:
        value: Value to validate.
        expected_type: Expected Python type.
        field_name: Name of field (for error messages).

    Returns:
        ValidationResult with error if type mismatch.
    """
    result = ValidationResult(valid=True)

    if not isinstance(value, expected_type):
        result.add_error(
            f"{field_name} must be {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )

    return result


def validate_in_range(
    value: int | float, min_val: int | float, max_val: int | float, field_name: str
) -> ValidationResult:
    """Validate that a numeric value is within range.

    Args:
        value: Numeric value to validate.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        field_name: Name of field (for error messages).

    Returns:
        ValidationResult with error if out of range.
    """
    result = ValidationResult(valid=True)

    if value < min_val or value > max_val:
        result.add_error(
            f"{field_name} must be between {min_val} and {max_val}, got {value}"
        )

    return result


def validate_one_of(
    value: Any, allowed_values: list[Any], field_name: str
) -> ValidationResult:
    """Validate that a value is one of allowed values.

    Args:
        value: Value to validate.
        allowed_values: List of allowed values.
        field_name: Name of field (for error messages).

    Returns:
        ValidationResult with error if not in allowed values.
    """
    result = ValidationResult(valid=True)

    if value not in allowed_values:
        result.add_error(
            f"{field_name} must be one of {allowed_values}, got {value!r}"
        )

    return result


def validate_regex(value: str, pattern: str, field_name: str) -> ValidationResult:
    """Validate that a string matches a regex pattern.

    Args:
        value: String value to validate.
        pattern: Regular expression pattern.
        field_name: Name of field (for error messages).

    Returns:
        ValidationResult with error if pattern doesn't match.
    """
    result = ValidationResult(valid=True)

    if not re.match(pattern, value):
        result.add_error(f"{field_name} does not match required pattern: {pattern}")

    return result


def merge_validation_results(*results: ValidationResult) -> ValidationResult:
    """Merge multiple validation results into one.

    The merged result is valid only if ALL input results are valid.
    All errors and warnings are combined.

    Args:
        *results: ValidationResult objects to merge.

    Returns:
        Merged ValidationResult.

    Example:
        >>> result1 = ValidationResult(valid=True)
        >>> result2 = ValidationResult(valid=False)
        >>> result2.add_error("Error")
        >>> merged = merge_validation_results(result1, result2)
        >>> merged.valid
        False
        >>> len(merged.errors)
        1
    """
    merged = ValidationResult(valid=True)

    for result in results:
        if result.has_errors:
            for error in result.errors:
                merged.add_error(error)

        if result.has_warnings:
            for warning in result.warnings:
                merged.add_warning(warning)

    return merged


def validate_file_extension(
    path: str, allowed_extensions: list[str], field_name: str = "file"
) -> ValidationResult:
    """Validate that a file has an allowed extension.

    Args:
        path: File path to validate.
        allowed_extensions: List of allowed extensions (e.g., ['.md', '.txt']).
        field_name: Name of field (for error messages).

    Returns:
        ValidationResult with error if extension not allowed.
    """
    result = ValidationResult(valid=True)

    path_obj = Path(path)
    extension = path_obj.suffix.lower()

    if extension not in allowed_extensions:
        result.add_error(
            f"{field_name} must have one of these extensions: {', '.join(allowed_extensions)}, "
            f"got '{extension}'"
        )

    return result


def validate_no_conflicts(
    value: str,
    existing_values: list[str],
    field_name: str,
    case_sensitive: bool = True,
) -> ValidationResult:
    """Validate that a value doesn't conflict with existing values.

    Args:
        value: Value to validate.
        existing_values: List of existing values to check against.
        field_name: Name of field (for error messages).
        case_sensitive: Whether comparison should be case-sensitive.

    Returns:
        ValidationResult with error if conflict found.
    """
    result = ValidationResult(valid=True)

    compare_value = value if case_sensitive else value.lower()
    compare_existing = (
        existing_values
        if case_sensitive
        else [v.lower() for v in existing_values]
    )

    if compare_value in compare_existing:
        result.add_error(f"{field_name} '{value}' already exists")

    return result
