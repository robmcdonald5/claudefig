# Adding New File Type Components

This guide provides a complete checklist for adding new file type components to claudefig. Follow each section to ensure full TUI/CLI parity and proper integration.

## Table of Contents

- [Overview](#overview)
- [Required Changes Checklist](#required-changes-checklist)
  - [1. Core Models & Type Definitions](#1-core-models--type-definitions)
  - [2. User Configuration & Structure](#2-user-configuration--structure)
  - [3. Preset Repository Integration](#3-preset-repository-integration)
  - [4. TUI Integration](#4-tui-integration)
  - [5. Component Examples & Preset Definition](#5-component-examples--preset-definition)
  - [6. Special Initialization Logic (Optional)](#6-special-initialization-logic-optional)
  - [7. Validation Logic (Optional)](#7-validation-logic-optional)
  - [8. Tests](#8-tests)
  - [9. Documentation](#9-documentation)
- [Verification Checklist](#verification-checklist)
- [Common Pitfalls](#common-pitfalls)
- [Testing Your Changes](#testing-your-changes)
- [Example: Adding "Plugins" Component](#example-adding-plugins-component)
- [Special Case: MCP (Model Context Protocol) Configuration](#special-case-mcp-model-context-protocol-configuration)
  - [Available Transport Types](#available-transport-types)
  - [Template Variants](#template-variants)
  - [Configuration File Patterns](#configuration-file-patterns)
  - [Transport Validation](#transport-validation)
  - [Security Best Practices](#security-best-practices)
  - [Setup Command Usage](#setup-command-usage)
  - [Common Issues & Troubleshooting](#common-issues--troubleshooting)
  - [Migration Guide: API Key to OAuth](#migration-guide-api-key-to-oauth)
  - [Performance Considerations](#performance-considerations)
  - [Additional Resources](#additional-resources)

## Overview

A "component" in claudefig represents a file type that can be managed through the TUI and CLI. Components can be:
- **Single-instance**: Only one per project (e.g., settings.json, statusline.sh)
- **Multi-instance**: Multiple allowed (e.g., commands, agents, plugins)
- **File-based**: Single file (e.g., CLAUDE.md, settings.json)
- **Directory-based**: Folder with multiple files (e.g., commands/, agents/, plugins/)

## Required Changes Checklist

### 1. Core Models & Type Definitions

#### `src/claudefig/models.py`
Add new enum value to `FileType` class:
```python
class FileType(Enum):
    ...
    NEW_TYPE = "new_type"  # Use snake_case
```

Update all FileType properties:
```python
# In display_name property
self.NEW_TYPE: "Display Name",

# In default_path property
self.NEW_TYPE: ".claude/new-type/",  # or specific file path

# In is_directory property (if directory-based)
directory_types = {
    ...
    self.NEW_TYPE,
}

# In supports_multiple (if single-instance only)
single_instance_types = {
    ...
    self.NEW_TYPE,  # Add here if single-instance
}

# In append_mode (if should append to existing files)
append_mode_types = {
    ...
    self.NEW_TYPE,  # Add here if append mode needed
}
```

### 2. User Configuration & Structure

#### `src/claudefig/user_config.py`
Add to `component_types` list in `initialize_user_directory()`:
```python
component_types = [
    ...
    "new_type",  # Must match FileType enum value
]
```

#### `src/claudefig/services/structure_validator.py`
Add to `required_dirs` list in `validate_user_directory()`:
```python
required_dirs = [
    ...
    "components/new_type",
]
```

### 3. Preset Repository Integration

#### `src/claudefig/repositories/preset_repository.py`

**Add to filename map** in `_get_component_filename()`:
```python
filename_map = {
    ...
    FileType.NEW_TYPE: "example-file.ext",  # Expected filename in component folder
}
```

**Add preset definition** in `_load_builtin_presets()`:
```python
builtin_presets = [
    ...
    # New Type preset
    Preset(
        id="new_type:default",
        type=FileType.NEW_TYPE,
        name="Default",
        description="Description of this component type",
        source=PresetSource.BUILT_IN,
        tags=["standard", "examples"],
    ),
]
```

### 4. TUI Integration

#### `src/claudefig/tui/screens/file_instances.py`

**Add to all_file_types list** in `compose()`:
```python
all_file_types = [
    ...
    FileType.NEW_TYPE,
]
```

**Add to type_dirs mapping** (appears twice in file):
```python
type_dirs = {
    ...
    FileType.NEW_TYPE: "new_type",
}
```

#### `src/claudefig/tui/screens/overview.py`

**Add to type_priority** in `_file_sort_key()`:
```python
type_priority = {
    ...
    FileType.NEW_TYPE: 12,  # Choose appropriate priority number
}
```

### 5. Component Examples & Preset Definition

#### Create component folder structure:
```
src/presets/default/components/new_type/default/
├── example-file.ext
└── (other files as needed)
```

**Important**:
- Each component type should have ONE variant named `default/`
- Place example/template files inside the default folder
- Filename must match what's in `filename_map`

#### Update preset definition file:
**`src/presets/default/claudefig.toml`**
```toml
[[components]]
type = "new_type"
name = "default"
path = ".claude/new-type/"  # or specific file path
enabled = false  # or true if should be enabled by default
```

### 6. Special Initialization Logic (Optional)

#### `src/claudefig/initializer.py`

For most components, no changes needed. The `_generate_directory_from_instance()` method handles directory-based components automatically.

**Only modify if:**
- Custom generation logic required
- Special file permissions needed (like statusline)
- Post-processing steps required

### 7. Validation Logic (Optional)

#### `src/claudefig/services/validation_service.py`

**Only needed for complex validation:**
```python
def validate_new_type_component(
    component_path: Path, ...
) -> ValidationResult:
    """Validate specific requirements for new component type."""
    result = ValidationResult(valid=True)
    # Custom validation logic
    return result
```

Then integrate in `file_instance_service.py`:
```python
# In validate_instance()
if instance.type == FileType.NEW_TYPE:
    custom_result = validate_new_type_component(...)
    # Merge results
```

### 8. Tests

#### `tests/test_models.py`

**Update FileType enum tests**:
```python
# In test_all_file_types_exist
expected_types = [
    ...
    "NEW_TYPE",
]

# In test_file_type_values
assert FileType.NEW_TYPE.value == "new_type"

# In test_display_name_property
assert FileType.NEW_TYPE.display_name == "Display Name"

# In test_default_path_property
assert FileType.NEW_TYPE.default_path == ".claude/new-type/"

# In test_supports_multiple_property
assert FileType.NEW_TYPE.supports_multiple  # or not, depending on type

# In test_is_directory_property (if directory-based)
assert FileType.NEW_TYPE.is_directory
```

#### `tests/factories.py`

**Add to type_paths mapping**:
```python
type_paths = {
    ...
    FileType.NEW_TYPE: ".claude/new-type/example.ext",
}
```

### 9. Documentation

#### `docs/CLI_REFERENCE.md`

**Add to Valid File Types list**:
```markdown
**Valid File Types:**
- ...
- `new_type` - Description of new component
```

## Verification Checklist

After implementing, verify:

- [ ] FileType enum includes new type
- [ ] All FileType properties updated (display_name, default_path, is_directory, etc.)
- [ ] Component directories created in user_config.py
- [ ] Structure validator includes component directory
- [ ] Preset definition exists in preset repository
- [ ] Filename mapping added
- [ ] TUI file_instances.py includes type (2 locations)
- [ ] TUI overview.py includes type priority
- [ ] Component folder created with default variant
- [ ] Preset claudefig.toml includes component entry
- [ ] All tests updated and passing
- [ ] CLI documentation updated
- [ ] Clean up: Delete `~/.claudefig/` and test end-to-end
- [ ] Verify component appears in TUI dropdown
- [ ] Verify component generates correctly when toggled on
- [ ] Verify component validates correctly

## Common Pitfalls

1. **Forgetting type_dirs mapping**: Appears in TWO places in file_instances.py
2. **Mismatched names**: Ensure "new_type" (snake_case) used consistently
3. **Missing default variant**: Component folders must have `default/` subfolder
4. **Preset not registered**: Must add to both filename_map AND builtin_presets
5. **Tests incomplete**: Update ALL FileType tests, not just some

## Testing Your Changes

```bash
# 1. Clean slate
rm -rf ~/.claudefig
rm -rf sandbox/claudefig.toml sandbox/.claude

# 2. Reinstall
pip install -e .

# 3. Run tests
pytest tests/test_models.py::TestFileTypeEnum -v

# 4. Test TUI
cd sandbox
claudefig

# 5. Verify:
# - New component appears in File Instances
# - Component dropdown shows "default" option
# - Toggling on generates files correctly
# - Component appears in overview
```

## Example: Adding "Plugins" Component

See `PLUGINS_SKILLS_IMPLEMENTATION.md` for a complete example of adding the Plugins and Skills components, including all changes made and issues encountered.

---

## Special Case: MCP (Model Context Protocol) Configuration

MCP servers are a unique component type in claudefig with special configuration requirements and multiple transport options. This section covers MCP-specific setup considerations.

### Available Transport Types

claudefig supports three MCP transport types, each with specific use cases:

1. **STDIO** - Local command-line tools
2. **HTTP** - Remote cloud services (recommended for production)
3. **SSE** - Server-Sent Events (deprecated, use HTTP instead)

### Template Variants

MCP components have three preset variants in `src/presets/default/components/mcp/`:

#### 1. `stdio-local/` - Local Development Tools

**Use for:**
- npm/npx packages (e.g., `@modelcontextprotocol/server-github`)
- Local command-line utilities
- Development and testing
- Filesystem operations

**Config structure:**
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

**Key features:**
- Subprocess management
- STDIO communication
- Environment variable injection
- No network requirements

#### 2. `http-oauth/` - Cloud Services with OAuth 2.1

**Use for:**
- Services requiring OAuth authentication
- Production cloud deployments
- Third-party integrations
- User-specific access requirements

**Config structure:**
```json
{
  "type": "http",
  "url": "${MCP_SERVICE_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_ACCESS_TOKEN}"
  },
  "transport": {
    "type": "http"
  }
}
```

**OAuth 2.1 Requirements (per 2025 MCP spec):**
- **MANDATORY**: OAuth 2.1 with PKCE (Proof Key for Code Exchange)
- **PROHIBITED**: Session-based authentication
- **REQUIRED**: Short-lived access tokens (1-24 hours)
- **REQUIRED**: HTTPS for all HTTP transport
- **RECOMMENDED**: Token refresh flows

**OAuth Setup Flow:**
1. Register application with service provider
2. Obtain client_id and authorization endpoints
3. Perform PKCE-enabled OAuth flow
4. Store access token securely (system keychain recommended)
5. Configure token refresh mechanism

See `http-oauth/README.md` for complete OAuth setup instructions.

#### 3. `http-apikey/` - Cloud Services with API Keys

**Use for:**
- Services without OAuth support
- Machine-to-machine authentication
- Internal APIs
- Development/staging environments

**Config structure:**
```json
{
  "type": "http",
  "url": "${MCP_API_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_API_KEY}",
    "Content-Type": "application/json"
  },
  "transport": {
    "type": "http"
  }
}
```

**Security requirements:**
- Store API keys in system keychain or encrypted storage
- Use environment variables, never hardcode
- Rotate keys regularly (90 days minimum)
- Different keys for dev/staging/production

See `http-apikey/README.md` for API key management best practices.

### Configuration File Patterns

claudefig supports **two MCP configuration patterns**:

#### Pattern 1: Standard `.mcp.json` (Project Root)
```bash
project/
├── .mcp.json           # Standard Claude Code pattern
├── .claude/
└── ...
```

Used for simple, single-server configurations. Follows official Claude Code conventions.

#### Pattern 2: Multiple Configs in `.claude/mcp/`
```bash
project/
├── .claude/
│   └── mcp/
│       ├── github.json      # Multiple server configs
│       ├── notion.json
│       └── custom-api.json
└── ...
```

Used for projects with multiple MCP servers. Allows organizing different services separately.

**Detection Order:**
1. Checks for `.mcp.json` first
2. Then checks `.claude/mcp/*.json`
3. Both can coexist (all files processed)

### Transport Validation

The `setup_mcp_servers()` method automatically validates:

1. **JSON Syntax** - Ensures valid JSON format
2. **Transport Type** - Validates against allowed types (stdio, http, sse)
3. **Required Fields**:
   - HTTP: Must have `url` field
   - STDIO: Must have `command` field
   - SSE: Shows deprecation warning
4. **Security Checks**:
   - Warns about HTTP (non-HTTPS) usage
   - Detects hardcoded credentials in headers
   - Validates environment variable substitution

**Example validation errors:**
```python
# Missing URL for HTTP
ValueError: HTTP transport requires 'url' field. Example: "url": "${MCP_SERVICE_URL}"

# Invalid transport type
ValueError: Invalid transport type 'websocket'. Must be one of: stdio, http, sse

# Security warning
Warning: github.json may contain hardcoded credentials in header 'Authorization'.
Use environment variables: "${VAR_NAME}"
```

### Security Best Practices

#### Environment Variables (ALWAYS Required)

**DO:**
```json
{
  "env": {
    "API_KEY": "${MY_API_KEY}",
    "TOKEN": "${SERVICE_TOKEN}"
  }
}
```

**DON'T:**
```json
{
  "env": {
    "API_KEY": "sk_live_abc123..."  // NEVER hardcode!
  }
}
```

#### Credential Storage Options

**1. System Keychain (Most Secure)**
```bash
# macOS
security add-generic-password -a $USER -s "mcp-token" -w "token_value"

# Linux
secret-tool store --label="MCP Token" service mcp token access

# Windows
# Use Credential Manager GUI or PowerShell
```

**2. Environment Variables (Development)**
```bash
# Add to shell profile (~/.bashrc, ~/.zshrc)
export GITHUB_TOKEN="your_token"
export MCP_API_KEY="your_key"
```

**3. .env Files (Project-Level)**
```bash
# Create .env (ensure in .gitignore!)
echo "MCP_API_KEY=..." >> .env
chmod 600 .env
```

#### OAuth Token Management

For OAuth-based MCPs:

1. **Token Expiration**: Set 1-24 hour expiration
2. **Token Refresh**: Implement refresh token flow
3. **Token Storage**: Use system keychain, not files
4. **Token Rotation**: Automate or set calendar reminders
5. **Token Revocation**: Revoke when no longer needed

### Setup Command Usage

```bash
# Basic setup
claudefig setup-mcp

# With specific path
claudefig setup-mcp --path /path/to/project

# What it does:
# 1. Finds .mcp.json or .claude/mcp/*.json files
# 2. Validates JSON syntax and transport config
# 3. Checks for security issues
# 4. Runs: claude mcp add-json <name> <config>
# 5. Reports success/failure for each server
```

**Output example:**
```
Setting up MCP servers...
Sources: .claude/mcp/ (3 files)

Running: claude mcp add-json github ...
+ Added MCP server: github

Running: claude mcp add-json notion ...
Warning: notion.json uses HTTP (not HTTPS). Consider using HTTPS for production.
+ Added MCP server: notion

Added 2 MCP server(s)
```

### Common Issues & Troubleshooting

#### Issue: "Invalid transport type"
**Cause**: Typo or unsupported transport type
**Fix**: Use `stdio`, `http`, or `sse` only

#### Issue: "HTTP transport requires 'url' field"
**Cause**: Missing required field for HTTP transport
**Fix**: Add `"url": "${MCP_SERVICE_URL}"` to config

#### Issue: "May contain hardcoded credentials"
**Cause**: Credential value doesn't use environment variable
**Fix**: Replace literal values with `${VAR_NAME}` syntax

#### Issue: OAuth token expired
**Cause**: Access token exceeded expiration time
**Fix**: Refresh token using service's refresh flow

#### Issue: Environment variable not expanding
**Cause**: Variable not set in environment
**Fix**:
```bash
# Verify variable is set
echo $MCP_API_KEY

# If empty, export it
export MCP_API_KEY="your_key"
```

### Migration Guide: API Key to OAuth

When a service adds OAuth support:

1. **Obtain OAuth credentials** from service provider
2. **Switch template variant**:
   ```bash
   # Before (API key)
   cp http-apikey/config.json .claude/mcp/service.json

   # After (OAuth)
   cp http-oauth/config.json .claude/mcp/service.json
   ```
3. **Update environment variables**:
   ```bash
   # Old
   export MCP_API_KEY="sk_..."

   # New
   export MCP_ACCESS_TOKEN="oauth_token_..."
   export MCP_SERVICE_URL="https://..."
   ```
4. **Re-run setup**: `claudefig setup-mcp`
5. **Revoke old API key** once confirmed working

### Performance Considerations

#### Connection Pooling (HTTP Transport)
```json
{
  "type": "http",
  "url": "${MCP_SERVICE_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_ACCESS_TOKEN}",
    "Connection": "keep-alive"
  },
  "transport": {
    "type": "http",
    "keepAlive": true,
    "maxConnections": 10
  }
}
```

#### Timeout Configuration
```json
{
  "transport": {
    "type": "http",
    "timeout": 30000  // milliseconds
  }
}
```

#### Caching Strategy
- Cache tool/resource lists: 5-15 minutes TTL
- Cache resource content: 1-5 minutes TTL
- Invalidate cache on write operations

### Additional Resources

**Component READMEs:**
- `src/presets/default/components/mcp/stdio-local/README.md` - STDIO setup guide
- `src/presets/default/components/mcp/http-oauth/README.md` - OAuth 2.1 complete guide
- `src/presets/default/components/mcp/http-apikey/README.md` - API key management

**Documentation:**
- `docs/MCP_SECURITY_GUIDE.md` - Comprehensive security best practices
- [MCP Specification 2025](https://spec.modelcontextprotocol.io/)
- [OAuth 2.1 Specification](https://oauth.net/2.1/)

**Code Reference:**
- `src/claudefig/initializer.py:582` - `setup_mcp_servers()` method
- `src/claudefig/initializer.py:687` - `_validate_mcp_transport()` method
