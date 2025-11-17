# Customizing Your Configuration

## Table of Contents

- [Configuration File Structure](#configuration-file-structure)
  - [Location](#location)
  - [Basic Structure](#basic-structure)
  - [Configuration Sections](#configuration-sections)
- [File Instances](#file-instances)
  - [Anatomy of a File Instance](#anatomy-of-a-file-instance)
  - [File Types](#file-types)
  - [Multiple Instances](#multiple-instances)
  - [Enabling and Disabling Instances](#enabling-and-disabling-instances)
  - [Variable Overrides](#variable-overrides)
- [Configuration Management](#configuration-management)
  - [Viewing Configuration](#viewing-configuration)
  - [Modifying Configuration](#modifying-configuration)
  - [Exporting Configuration](#exporting-configuration)
  - [Importing Configuration](#importing-configuration)
- [Workflow Patterns](#workflow-patterns)
  - [Pattern 1: Minimal Setup](#pattern-1-minimal-setup)
  - [Pattern 2: Full-Featured Setup](#pattern-2-full-featured-setup)
  - [Pattern 3: Multi-Context Setup](#pattern-3-multi-context-setup)
  - [Pattern 4: Staged Rollout](#pattern-4-staged-rollout)
- [Advanced Configuration](#advanced-configuration)
  - [Custom Preset Directories](#custom-preset-directories)
  - [Template Variables Everywhere](#template-variables-everywhere)
  - [Conditional Generation](#conditional-generation)
  - [Path Templates](#path-templates)
  - [Hook Integration](#hook-integration)
- [Validation and Error Handling](#validation-and-error-handling)
  - [Validation Levels](#validation-levels)
  - [Common Validation Errors](#common-validation-errors)
  - [Recovery from Corruption](#recovery-from-corruption)
- [Troubleshooting](#troubleshooting)
  - [Config Not Found](#config-not-found)
  - [Changes Not Applying](#changes-not-applying)
  - [Invalid TOML Syntax](#invalid-toml-syntax)
  - [Preset Variables Not Working](#preset-variables-not-working)

## Configuration File Structure

claudefig stores its configuration in `claudefig.toml` using the TOML format. This file defines which files to generate and how to generate them.

### Location

Configuration files are searched in this order:

1. **Project config**: `claudefig.toml` in current directory (highest priority)
2. **User config**: `~/.claudefig/config.toml` in home directory (fallback)

Most projects should use a project config checked into git.

### Basic Structure

```toml
[claudefig]
version = "2.0"
schema_version = "2.0"

[init]
overwrite_existing = false

[[files]]
id = "claude_md-default"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true

[[files]]
id = "settings_json-default"
type = "settings_json"
preset = "settings_json:default"
path = ".claude/settings.json"
enabled = true

[custom]
template_dir = ""
presets_dir = ""
```

### Configuration Sections

#### `[claudefig]`

Metadata about the configuration file:

```toml
[claudefig]
version = "2.0"           # claudefig version that created this config
schema_version = "2.0"    # Configuration schema version
```

#### `[init]`

Settings for the `claudefig init` command:

```toml
[init]
overwrite_existing = false  # If true, overwrite files without prompting
```

#### `[[files]]`

Array of file instances (see [File Instances](#file-instances) below).

#### `[custom]`

Custom paths for advanced usage:

```toml
[custom]
template_dir = ""    # Custom template directory (advanced)
presets_dir = ""     # Custom presets directory (advanced)
```

## File Instances

**File instances** are the core of claudefig's configuration. Each instance represents a specific file that will be generated.

### Anatomy of a File Instance

```toml
[[files]]
id = "claude_md-backend"              # Unique identifier
type = "claude_md"                    # File type (see File Types below)
preset = "claude_md:backend"          # Preset to use
path = "CLAUDE.md"                    # Where to generate the file
enabled = true                        # Whether this instance is active

[files.variables]                     # Optional: Override preset variables
project_name = "My Backend API"
framework = "FastAPI"
```

### File Types

claudefig supports these file types:

| Type | Description | Default Path |
|------|-------------|--------------|
| `claude_md` | CLAUDE.md project instructions | `CLAUDE.md` |
| `settings_json` | Team settings | `.claude/settings.json` |
| `settings_local_json` | Personal settings | `.claude/settings.local.json` |
| `gitignore` | Git ignore entries | `.gitignore` |
| `commands` | Slash commands (directory) | `.claude/commands/` |
| `agents` | Custom agents (directory) | `.claude/agents/` |
| `hooks` | Hook scripts (directory) | `.claude/hooks/` |
| `output_styles` | Output styles (directory) | `.claude/output-styles/` |
| `statusline` | Status line script | `.claude/statusline.sh` |
| `mcp` | MCP server configs (directory) | `.claude/mcp/` |

### Multiple Instances

Most file types support multiple instances, allowing you to create multiple files of the same type:

```toml
[[files]]
id = "claude_md-main"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true

[[files]]
id = "claude_md-backend"
type = "claude_md"
preset = "claude_md:backend"
path = "docs/BACKEND.md"
enabled = true

[[files]]
id = "claude_md-frontend"
type = "claude_md"
preset = "claude_md:frontend"
path = "docs/FRONTEND.md"
enabled = true
```

**Single-instance types** (only one allowed):
- `settings_local_json` - Personal settings should be one file
- `statusline` - Only one status line script

### Enabling and Disabling Instances

Disable instances without deleting them:

```toml
[[files]]
id = "claude_md-experimental"
type = "claude_md"
preset = "claude_md:experimental"
path = "EXPERIMENTAL.md"
enabled = false  # Skipped during generation
```

**CLI commands:**

```bash
# Disable an instance
claudefig files disable claude_md-experimental

# Enable it later
claudefig files enable claude_md-experimental
```

**TUI method:**
- Select instance in Files panel
- Press `Space` to toggle enabled/disabled

### Variable Overrides

Override preset variables per instance:

```toml
[[files]]
id = "claude_md-api"
type = "claude_md"
preset = "claude_md:backend"
path = "API.md"
enabled = true

[files.variables]
project_name = "REST API Service"
framework = "FastAPI"
database = "PostgreSQL"
test_framework = "pytest"
coverage_threshold = 90
```

This allows you to use the same preset with different values for different files.

## Configuration Management

### Viewing Configuration

```bash
# View entire configuration
claudefig config show

# View as JSON
claudefig config show --format json

# Get a specific value
claudefig config get init.overwrite_existing
claudefig config get claudefig.version
```

**TUI method:**
- Launch `claudefig interactive`
- Press `c` to view current config

### Modifying Configuration

```bash
# Set a value
claudefig config set init.overwrite_existing true

# Set nested values
claudefig config set custom.template_dir "/path/to/templates"
```

**Note:** Most configuration is managed through file instances, not direct config editing.

### Exporting Configuration

```bash
# Export to file
claudefig config export > backup.toml

# Export for sharing
claudefig config export --minimal > team-config.toml
```

### Importing Configuration

```bash
# Import from file
claudefig config import team-config.toml

# Merge with existing
claudefig config import --merge team-config.toml
```

## Workflow Patterns

### Pattern 1: Minimal Setup

Only create essential files:

```toml
[[files]]
id = "claude_md-minimal"
type = "claude_md"
preset = "claude_md:minimal"
path = "CLAUDE.md"
enabled = true

[[files]]
id = "gitignore-default"
type = "gitignore"
preset = "gitignore:default"
path = ".gitignore"
enabled = true
```

```bash
claudefig init
```

### Pattern 2: Full-Featured Setup

Create comprehensive configuration:

```toml
[[files]]
id = "claude_md-full"
type = "claude_md"
preset = "claude_md:full"
path = "CLAUDE.md"
enabled = true

[[files]]
id = "settings_json-default"
type = "settings_json"
preset = "settings_json:default"
path = ".claude/settings.json"
enabled = true

[[files]]
id = "settings_local_json-default"
type = "settings_local_json"
preset = "settings_local_json:default"
path = ".claude/settings.local.json"
enabled = true

[[files]]
id = "commands-default"
type = "commands"
preset = "commands:default"
path = ".claude/commands/"
enabled = true

[[files]]
id = "agents-default"
type = "agents"
preset = "agents:default"
path = ".claude/agents/"
enabled = true

[[files]]
id = "gitignore-default"
type = "gitignore"
preset = "gitignore:default"
path = ".gitignore"
enabled = true
```

### Pattern 3: Multi-Context Setup

Different CLAUDE.md files for different contexts:

```toml
# Main project overview
[[files]]
id = "claude_md-main"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true

# Backend-specific context
[[files]]
id = "claude_md-backend"
type = "claude_md"
preset = "claude_md:backend"
path = "backend/CLAUDE_BACKEND.md"
enabled = true

# Frontend-specific context
[[files]]
id = "claude_md-frontend"
type = "claude_md"
preset = "claude_md:frontend"
path = "frontend/CLAUDE_FRONTEND.md"
enabled = true

# Testing guidelines
[[files]]
id = "claude_md-testing"
type = "claude_md"
preset = "claude_md:testing"
path = "tests/CLAUDE_TESTING.md"
enabled = true
```

### Pattern 4: Staged Rollout

Enable features incrementally:

**Week 1:** Basic setup

```bash
claudefig files add --type claude_md --preset claude_md:default --path CLAUDE.md
claudefig files add --type gitignore --preset gitignore:default --path .gitignore
claudefig init
```

**Week 2:** Add settings

```bash
claudefig files add --type settings_json --preset settings_json:default --path .claude/settings.json
claudefig init --force
```

**Week 3:** Add commands and agents

```bash
claudefig files add --type commands --preset commands:default --path .claude/commands/
claudefig files add --type agents --preset agents:default --path .claude/agents/
claudefig init --force
```

## Advanced Configuration

### Custom Preset Directories

Point claudefig to custom preset locations:

```toml
[custom]
presets_dir = "/path/to/company-presets"
```

This adds an additional preset source. Useful for company-wide preset repositories.

### Template Variables Everywhere

Define global template variables:

```toml
[template_defaults]
company = "ACME Corp"
license = "MIT"
author = "Engineering Team"
```

All file instances inherit these unless overridden.

### Conditional Generation

Use enabled flag programmatically:

```bash
# Enable backend files in backend-only mode
if [ "$PROJECT_TYPE" = "backend" ]; then
  claudefig files enable claude_md-backend
  claudefig files disable claude_md-frontend
fi

claudefig init --force
```

### Path Templates

Use variables in paths:

```toml
[[files]]
id = "claude_md-service"
type = "claude_md"
preset = "claude_md:backend"
path = "services/{service_name}/CLAUDE.md"
enabled = true

[files.variables]
service_name = "auth-service"
```

Path becomes: `services/auth-service/CLAUDE.md`

### Hook Integration

Trigger claudefig from git hooks:

`.git/hooks/post-checkout`

```bash
#!/bin/bash
# Auto-update Claude Code files after checkout
claudefig init --force --quiet
```

## Validation and Error Handling

### Validation Levels

claudefig performs multiple validation checks:

1. **Schema Validation** - TOML structure is valid
2. **Instance Validation** - File instances are valid
3. **Preset Validation** - Referenced presets exist
4. **Path Validation** - Paths are safe and valid
5. **Conflict Detection** - No path conflicts

### Common Validation Errors

#### Invalid Preset Reference

**Error:** `Preset 'claude_md:nonexistent' not found`

**Fix:**

```bash
# List available presets
claudefig presets list --type claude_md

# Update instance to use valid preset
claudefig files update claude_md-main --preset claude_md:default
```

#### Path Conflict

**Warning:** `Path 'CLAUDE.md' is already used by instance 'claude_md-other'`

**Fix:** Use different paths for different instances

```toml
# Before (conflict)
[[files]]
id = "claude_md-main"
path = "CLAUDE.md"

[[files]]
id = "claude_md-backend"
path = "CLAUDE.md"  # Conflict!

# After (resolved)
[[files]]
id = "claude_md-main"
path = "CLAUDE.md"

[[files]]
id = "claude_md-backend"
path = "docs/BACKEND.md"
```

#### Multiple Instances of Single-Instance Type

**Error:** `File type 'statusline' does not support multiple instances`

**Fix:** Disable or remove extra instances

```bash
claudefig files disable statusline-extra
```

### Recovery from Corruption

If `claudefig.toml` becomes corrupted:

```bash
# Backup corrupted file
mv claudefig.toml claudefig.toml.backup

# Create fresh config
claudefig init --reset

# Manually re-add instances or restore from backup
```

## Troubleshooting

### Config Not Found

**Issue:** claudefig doesn't find your config

**Solution:** Ensure `claudefig.toml` is in current directory or home directory

```bash
# Check current directory
ls -la claudefig.toml

# Check home directory
ls -la ~/.claudefig/config.toml
```

### Changes Not Applying

**Issue:** Modified config but files don't change

**Solution:** Force regeneration

```bash
claudefig init --force
```

### Invalid TOML Syntax

**Issue:** Config file has syntax errors

**Solution:** Validate TOML

```bash
# Use online validator: https://www.toml-lint.com/
# Or use a TOML validator tool
toml-validator claudefig.toml
```

### Preset Variables Not Working

**Issue:** Variables show as `{variable_name}` in generated files

**Solution:** Check variable definition and usage

```toml
# Ensure variables are defined
[files.variables]
variable_name = "value"

# Ensure template uses correct syntax
# In template: {variable_name}
```
