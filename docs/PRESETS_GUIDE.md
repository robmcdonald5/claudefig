# Getting Started with Presets

## What Are Presets?

**Presets** are reusable templates for Claude Code configuration files. Instead of manually creating CLAUDE.md files, settings, commands, or other configurations from scratch, you can choose from pre-built templates or create your own.

Each preset is specific to a **file type** (like `claude_md`, `settings_json`, `commands`) and provides a starting point with best practices, common patterns, or specialized configurations.

## Understanding the Preset System

### Preset ID Format

Presets use a two-part identifier:

```
{file_type}:{preset_name}
```

**Examples:**
- `claude_md:default` - Default CLAUDE.md template
- `claude_md:backend` - Backend-focused CLAUDE.md template
- `settings_json:default` - Default settings.json template
- `commands:default` - Default slash commands

### Preset Sources

Presets can come from three sources:

1. **Built-in Presets** (`built-in`)
   - Shipped with claudefig
   - Cannot be modified
   - Always available
   - Location: Internal to claudefig package

2. **User Presets** (`user`)
   - Personal presets stored in your home directory
   - Available across all projects
   - Location: `~/.claudefig/presets/`

3. **Project Presets** (`project`)
   - Project-specific presets
   - Shared with team via git
   - Location: `.claudefig/presets/` in your repository

## Using Built-in Presets

### Listing Available Presets

View all available presets:

```bash
# List all presets
claudefig presets list

# List presets for a specific file type
claudefig presets list --type claude_md
```

**TUI Method:**
- Launch `claudefig interactive`
- Browse the Presets panel (left side)
- Filter by file type using the dropdown

### Viewing Preset Details

```bash
# Show detailed information about a preset
claudefig presets show claude_md:default

# View preset template content
claudefig presets show claude_md:backend --full
```

### Applying Presets

When you apply a preset, claudefig creates a **file instance** - a specific file that will be generated during initialization.

**CLI Method:**

```bash
# Apply a preset (creates a file instance)
claudefig presets apply claude_md:default

# Apply to a custom path
claudefig presets apply claude_md:backend --path docs/BACKEND.md
```

**TUI Method:**
- Select a preset in the Presets panel
- Press `Enter` or click "Apply Preset"
- Confirm the path and settings
- The file instance appears in the Files panel

## Built-in Presets Reference

### CLAUDE.md Presets

| Preset ID | Description |
|-----------|-------------|
| `claude_md:default` | General-purpose project instructions |
| `claude_md:minimal` | Minimal template with basic structure |
| `claude_md:backend` | Backend development focus (APIs, databases, testing) |
| `claude_md:frontend` | Frontend development focus (React, components, styling) |
| `claude_md:full` | Comprehensive template with all sections |

### Settings Presets

| Preset ID | Description |
|-----------|-------------|
| `settings_json:default` | Standard team settings |
| `settings_json:minimal` | Minimal configuration |
| `settings_local_json:default` | Personal project settings |

### Directory-based Presets

| Preset ID | Description |
|-----------|-------------|
| `commands:default` | Example slash commands |
| `agents:default` | Example custom agents |
| `hooks:default` | Example pre/post hooks |
| `output_styles:default` | Example output styles |
| `mcp:default` | Example MCP server configs |

### Special Presets

| Preset ID | Description |
|-----------|-------------|
| `gitignore:default` | Claude Code .gitignore entries |
| `statusline:default` | Example status line script |

## Creating Custom Presets

**Note:** As of 2025, claudefig uses a directory-based preset architecture. Each preset is a complete directory structure containing components and metadata.

### User Presets (Global)

Create presets that are available across all your projects:

1. **Create preset directory structure:**

```bash
mkdir -p ~/.claudefig/presets/my-preset/components/claude_md/default
```

2. **Create preset definition file:**

`~/.claudefig/presets/my-preset/claudefig.toml`

```toml
[preset]
name = "my-preset"
description = "My personalized preset with custom configurations"
version = "1.0.0"

[[components]]
type = "claude_md"
name = "default"
path = "CLAUDE.md"
enabled = true

[components.variables]
project_name = "MyProject"
author = "Your Name"
```

3. **Create component template file:**

`~/.claudefig/presets/my-preset/components/claude_md/default/CLAUDE.md`

```markdown
# {project_name}

Author: {author}

## Project Overview

[Your custom content here]

## Development Guidelines

[Your custom guidelines here]
```

4. **Use your preset:**

```bash
claudefig presets list --source user
claudefig presets apply claude_md:my-preset
```

### Project Presets (Team-Shared)

Create presets specific to your project that can be shared via git:

1. **Create project preset directory structure:**

```bash
mkdir -p .claudefig/presets/team-standard/components/claude_md/default
```

2. **Create preset definition:**

`.claudefig/presets/team-standard/claudefig.toml`

```toml
[preset]
name = "team-standard"
description = "Our team's standard CLAUDE.md template"
version = "1.0.0"

[[components]]
type = "claude_md"
name = "default"
path = "CLAUDE.md"
enabled = true

[components.variables]
team_name = "Engineering Team"
repo_url = "https://github.com/yourorg/yourrepo"
```

3. **Create component template:**

`.claudefig/presets/team-standard/components/claude_md/default/CLAUDE.md`

```markdown
# Project: {team_name}

Repository: {repo_url}

[Team-specific content]
```

4. **Commit to git:**

```bash
git add .claudefig/presets/
git commit -m "Add team preset"
```

Team members will automatically see this preset when they run claudefig.

## Preset Variables

Variables allow you to customize preset templates without editing the template itself.

### Defining Variables

In your preset TOML file:

```toml
[variables]
project_name = "DefaultProject"  # Default value
author = "Unknown"
version = "1.0.0"
license = "MIT"
```

### Using Variables in Templates

Use `{variable_name}` syntax in your template:

```markdown
# {project_name} v{version}

Author: {author}
License: {license}
```

### Overriding Variables

When applying a preset:

```bash
# CLI method
claudefig presets apply claude_md:my-preset \
  --var project_name="MyAwesomeProject" \
  --var author="Jane Doe"
```

**TUI method:**
- Apply preset
- Edit the created file instance
- Override variables in the Variables section

Variables are also stored per file instance, allowing different instances of the same preset to have different values.

## Preset Inheritance

Create specialized presets by extending existing ones:

**Base preset:** `~/.claudefig/presets/claude_md/base.toml`

```toml
[preset]
id = "claude_md:base"
type = "claude_md"
name = "Base Template"
description = "Base template for all projects"
source = "user"

[variables]
company = "ACME Corp"
code_style = "PEP 8"
```

**Derived preset:** `~/.claudefig/presets/claude_md/backend.toml`

```toml
[preset]
id = "claude_md:backend-acme"
type = "claude_md"
name = "ACME Backend Template"
description = "Backend template with ACME standards"
source = "user"
extends = "claude_md:base"  # Inherit from base

[variables]
# Inherits company and code_style from base
framework = "FastAPI"
database = "PostgreSQL"
```

When a preset extends another:
- It inherits all variables (can override them)
- Template can reference parent template
- Chain multiple levels of inheritance

## Advanced Preset Techniques

### Conditional Content

Use variables to enable/disable sections:

```markdown
# {project_name}

{if backend}
## Backend Stack
- Framework: {backend_framework}
- Database: {database}
{endif}

{if frontend}
## Frontend Stack
- Framework: {frontend_framework}
- State: {state_management}
{endif}
```

### Multi-File Presets

Some preset types generate multiple files (like `commands:` or `agents:`):

```
~/.claudefig/presets/commands/my-commands/
├── my-commands.toml          # Preset metadata
├── review.md                 # /review command
├── test.md                   # /test command
└── deploy.md                 # /deploy command
```

When applied, all files in the directory are copied to the target path.

### Preset Tags

Tag presets for easier discovery:

```toml
[preset]
id = "claude_md:python-backend"
type = "claude_md"
name = "Python Backend"
description = "Python backend with FastAPI"
source = "user"
tags = ["python", "backend", "fastapi", "api"]
```

Search by tags:

```bash
claudefig presets list --tag python --tag backend
```

## Preset Best Practices

### 1. Use Descriptive Names

❌ Bad:
```
claude_md:template1
claude_md:test
```

✅ Good:
```
claude_md:python-backend-api
claude_md:react-frontend-spa
```

### 2. Provide Clear Descriptions

```toml
[preset]
description = "Backend API template with FastAPI, PostgreSQL, and comprehensive testing guidelines"
```

### 3. Set Sensible Default Variables

```toml
[variables]
python_version = "3.11"  # Use current stable version
test_framework = "pytest"  # Industry standard
```

### 4. Document Variables

Add comments in your TOML:

```toml
[variables]
# The Python version used in CI/CD
python_version = "3.11"

# Test framework (pytest, unittest, nose)
test_framework = "pytest"

# Code coverage threshold (0-100)
coverage_threshold = 80
```

### 5. Version Your Presets

For project presets, consider versioning:

```
.claudefig/presets/claude_md/
├── v1-standard.toml
├── v1-standard.md
├── v2-standard.toml
└── v2-standard.md
```

### 6. Share User Presets

Export your user presets to share with team:

```bash
# Export user presets
tar -czf my-presets.tar.gz ~/.claudefig/presets/

# Import on another machine
cd ~/.claudefig/
tar -xzf ~/Downloads/my-presets.tar.gz
```

Or store them in a git repository:

```bash
# Create a presets repository
cd ~/.claudefig/presets/
git init
git add .
git commit -m "Initial presets"
git remote add origin https://github.com/you/my-claudefig-presets.git
git push -u origin main
```

## Troubleshooting

### Preset Not Found

**Error:** `Preset 'claude_md:custom' not found`

**Solutions:**
1. Verify preset ID: `claudefig presets list`
2. Check preset file location (user: `~/.claudefig/presets/`, project: `.claudefig/presets/`)
3. Ensure TOML file has correct `id` field

### Invalid Preset Format

**Error:** `Failed to load preset: Invalid TOML`

**Solutions:**
1. Validate TOML syntax: Use online validator
2. Check required fields: `id`, `type`, `name`, `source`
3. Ensure `type` matches file type enum

### Variables Not Substituting

**Issue:** Template shows `{variable_name}` instead of value

**Solutions:**
1. Verify variable is defined in preset TOML `[variables]` section
2. Check spelling in template matches variable name exactly
3. Ensure curly braces are not escaped

### Preset Inheritance Not Working

**Issue:** Extended preset doesn't inherit variables

**Solutions:**
1. Verify parent preset exists: `claudefig presets show parent-id`
2. Check `extends` field uses full preset ID (e.g., `claude_md:parent`)
3. Ensure no circular inheritance (A extends B extends A)

## Next Steps

- Learn about [File Instances](CONFIG_GUIDE.md#file-instances)
- Explore [CLI Commands](CLI_REFERENCE.md)
- Read about [Configuration Management](CONFIG_GUIDE.md)
