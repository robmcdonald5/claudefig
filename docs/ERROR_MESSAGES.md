# Error Message Standardization

This document describes the standardized error messaging system used throughout claudefig.

## Overview

All error messages in claudefig use the centralized `ErrorMessages` class from `claudefig.error_messages` to ensure consistent formatting, terminology, and color schemes across both CLI and TUI interfaces.

## Core Principles

1. **Consistency**: Same error type always uses same format and wording
2. **Clarity**: Error messages clearly state what went wrong and resource identifiers
3. **Helpfulness**: Where applicable, provide hints for resolution
4. **Terminology**: Use consistent terms (e.g., "file instance" not "instance")

## Module Structure

The `claudefig.error_messages` module provides:

### `ErrorMessages` Class

Static methods that return standardized error message strings:

- `not_found(resource_type, identifier)` - For missing resources
- `invalid_type(type_name, value, valid_options)` - For invalid enum/type values
- `validation_failed(details)` - For validation errors
- `operation_failed(operation, details)` - For operation failures
- `empty_value(field_name)` - For required fields left empty
- `file_exists(path)` - For file already exists errors
- `config_file_not_found(path)` - For missing .claudefig.toml
- `failed_to_perform(action, resource_type, identifier)` - For action failures
- `success(action, resource_type, identifier)` - For success messages
- `no_changes_made()` - Warning for no-op operations
- `partial_failure(total, failed)` - For partial failures
- `no_resources(resource_type)` - Info message for empty lists
- `use_command_hint(command, purpose)` - Usage hints

### `FormattedMessages` Class

Formats messages for CLI with Rich markup:

- `error(message)` - Red "[Error:]" prefix
- `warning(message)` - Yellow "[Warning:]" prefix
- `success(message)` - Green "[+]" prefix
- `info(message)` - Blue "[Info:]" prefix
- `highlight(text)` - Cyan highlighting
- `dim(text)` - Dimmed secondary information

### Convenience Functions

- `format_cli_error(message)` - Shorthand for CLI errors
- `format_cli_warning(message)` - Shorthand for CLI warnings
- `format_cli_success(message)` - Shorthand for CLI success
- `format_cli_info(message)` - Shorthand for CLI info

## Usage Examples

### CLI Usage

```python
from claudefig.error_messages import ErrorMessages, format_cli_error, format_cli_warning

# Not found error
if not preset:
    console.print(format_cli_warning(ErrorMessages.not_found("preset", preset_id)))

# Invalid type error
try:
    file_type = FileType(value)
except ValueError:
    valid_types = [ft.value for ft in FileType]
    console.print(format_cli_error(
        ErrorMessages.invalid_type("file type", value, valid_types)
    ))

# Operation failed error
except Exception as e:
    console.print(format_cli_error(
        ErrorMessages.operation_failed("initialization", str(e))
    ))

# Config file not found
if not config_path.exists():
    console.print(format_cli_error(
        ErrorMessages.config_file_not_found(str(repo_path))
    ))
```

### TUI Usage

```python
from claudefig.error_messages import ErrorMessages

# Not found error
if not instance:
    self.notify(ErrorMessages.not_found("file instance", instance_id), severity="error")

# Validation error
if result.has_errors:
    error_msg = "\n".join(result.errors)
    self.notify(ErrorMessages.validation_failed(error_msg), severity="error")

# Empty value error
if not path:
    self.notify(ErrorMessages.empty_value("path"), severity="error")

# Operation failed error
except Exception as e:
    self.notify(ErrorMessages.operation_failed("saving instance", str(e)), severity="error")
```

## Standardized Terminology

Use these consistent terms throughout error messages:

| Concept | Standard Term |
|---------|---------------|
| FileInstance object | "file instance" |
| Preset object | "preset" |
| Global template | "template" |
| File type enum | "file type" |
| Configuration file | ".claudefig.toml" or "config file" |
| Initialize operation | "initialization" |
| Synchronize operation | "synchronizing files" |
| Validate operation | "validation" |

## Color Scheme

All CLI messages use Rich markup colors:

- **Error**: `[red]` - Critical failures
- **Warning**: `[yellow]` - Non-critical issues, not found items
- **Success**: `[green]` - Successful operations
- **Info**: `[blue]` - Informational messages
- **Highlight**: `[cyan]` - Important identifiers (instance IDs, paths, etc.)
- **Dim**: `[dim]` - Secondary/helper text

## Message Patterns

### Not Found Pattern

**Format**: `"{resource_type.capitalize()} not found: {identifier}"`

**Examples**:
- "File instance not found: claude_md-default"
- "Preset not found: claude_md:custom"
- "Template not found: my-template"

### Invalid Type Pattern

**Format**: `"Invalid {type_name}: {value} (valid: {options})"`

**Examples**:
- "Invalid file type: foo (valid: claude_md, settings_json, ...)"

### Operation Failed Pattern

**Format**: `"Error during {operation}: {details}"`

**Examples**:
- "Error during initialization: Permission denied"
- "Error during saving instance: Validation failed"

### Empty Value Pattern

**Format**: `"{field_name.capitalize()} cannot be empty"`

**Examples**:
- "Path cannot be empty"
- "Preset selection cannot be empty"

### Validation Failed Pattern

**Format**: `"Validation failed: {details}"` or `"Validation failed"` (if no details)

**Examples**:
- "Validation failed: Instance 'foo' already exists"
- "Validation failed"

## Migration Guide

When updating existing code to use standardized messages:

### Step 1: Add Import

```python
from claudefig.error_messages import ErrorMessages, format_cli_error
```

### Step 2: Replace Error Messages

**Before**:
```python
console.print(f"[red]Error adding file instance:[/red] {e}")
```

**After**:
```python
console.print(format_cli_error(ErrorMessages.operation_failed("adding file instance", str(e))))
```

**Before**:
```python
self.notify(f"Instance not found: {instance_id}", severity="error")
```

**After**:
```python
self.notify(ErrorMessages.not_found("file instance", instance_id), severity="error")
```

### Step 3: Use Consistent Terminology

Ensure you're using standard terms from the terminology table above.

## Testing

When writing tests that check error messages:

```python
# Test the error message content
result = ErrorMessages.not_found("preset", "claude_md:test")
assert "Preset not found: claude_md:test" in result

# Test CLI formatting
formatted = format_cli_error(ErrorMessages.operation_failed("test", "details"))
assert "[red]Error:[/red]" in formatted
assert "Error during test: details" in formatted
```

## Future Enhancements

Potential additions to the error message system:

1. **Localization Support**: Add translation keys for internationalization
2. **Error Codes**: Add structured error codes for programmatic error handling
3. **Context Information**: Include file/line information for debugging
4. **Suggestions**: Add automatic suggestion generation for common errors
5. **Logging Integration**: Automatic logging of all error messages
