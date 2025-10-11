# CLI Reference

Complete command-line reference for claudefig.

## Table of Contents

- [Global Options](#global-options)
- [Main Commands](#main-commands)
- [Config Commands](#config-commands)
- [Files Commands](#files-commands)
- [Presets Commands](#presets-commands)
- [Examples](#examples)

## Global Options

### Version

Display claudefig version:

```bash
claudefig --version
```

### Help

Show help for any command:

```bash
claudefig --help
claudefig config --help
claudefig files --help
```

## Main Commands

### `claudefig`

Launch interactive TUI mode (default behavior):

```bash
claudefig
# Equivalent to: claudefig interactive
```

**Description:** When run without arguments, launches the interactive TUI for managing presets and file instances.

### `claudefig init`

Initialize Claude Code configuration in a repository.

**Usage:**

```bash
claudefig init [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path to initialize | Current directory |
| `--force` | Overwrite existing files | False |

**Examples:**

```bash
# Initialize current directory
claudefig init

# Initialize specific directory
claudefig init --path /path/to/repo

# Force overwrite existing files
claudefig init --force

# Combine options
claudefig init --path ../my-project --force
```

**What it does:**

1. Loads configuration from `.claudefig.toml`
2. Generates all enabled file instances
3. Creates `.claude/` directory structure
4. Applies presets to generate files
5. Updates `.gitignore` if configured

### `claudefig interactive`

Launch interactive TUI mode.

**Usage:**

```bash
claudefig interactive
```

**Features:**

- Browse and apply presets
- Manage file instances
- Toggle instances enabled/disabled
- Preview configurations
- Keyboard navigation

**Keyboard Shortcuts:**

| Key | Action |
|-----|--------|
| `ctrl+p` | Focus presets panel |
| `ctrl+f` | Focus files panel |
| `ctrl+a` | Add new file instance |
| `ctrl+g` | Generate files |
| `ctrl+q` | Quit |
| `enter` | Apply preset or edit instance |
| `space` | Toggle instance enabled/disabled |

### `claudefig show`

Show current configuration.

**Usage:**

```bash
claudefig show
```

**Example Output:**

```
Current Configuration:

Config file: /path/to/project/.claudefig.toml

┌────────────────────────────┬────────────┐
│ Setting                    │ Value      │
├────────────────────────────┼────────────┤
│ Template Source            │ built-in   │
│ Create CLAUDE.md           │ True       │
│ Create Settings            │ True       │
│ Update .gitignore          │ True       │
└────────────────────────────┴────────────┘
```

### `claudefig setup-mcp`

Set up MCP servers from `.claude/mcp/` directory.

**Usage:**

```bash
claudefig setup-mcp [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |

**Examples:**

```bash
# Setup MCP servers in current directory
claudefig setup-mcp

# Setup in specific directory
claudefig setup-mcp --path /path/to/repo
```

**What it does:**

1. Scans `.claude/mcp/` for JSON files
2. Runs `claude mcp add-json` for each file
3. Configures MCP servers with Claude Code

**Requirements:**

- Claude Code CLI must be installed
- `claude` command must be in PATH

## Config Commands

Manage claudefig configuration settings.

### `claudefig config list`

List all configuration settings.

**Usage:**

```bash
claudefig config list [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |

**Example:**

```bash
claudefig config list
```

**Example Output:**

```
Configuration from: /path/to/.claudefig.toml

┌─────────────────────────────┬─────────┐
│ Setting                     │ Value   │
├─────────────────────────────┼─────────┤
│ Claudefig                   │         │
│   version                   │ 2.0     │
│   schema_version            │ 2.0     │
│ Init                        │         │
│   overwrite_existing        │ False   │
└─────────────────────────────┴─────────┘
```

### `claudefig config get`

Get a specific configuration value.

**Usage:**

```bash
claudefig config get KEY [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `KEY` | Configuration key in dot notation |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |

**Examples:**

```bash
# Get a specific value
claudefig config get init.overwrite_existing

# Get nested value
claudefig config get claudefig.version

# From specific directory
claudefig config get init.overwrite_existing --path /path/to/repo
```

**Output:**

```
init.overwrite_existing: False
```

### `claudefig config set`

Set a configuration value.

**Usage:**

```bash
claudefig config set KEY VALUE [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `KEY` | Configuration key in dot notation |
| `VALUE` | Value to set |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |

**Value Types:**

- Boolean: Use `true` or `false`
- Integer: Use digits `42`
- String: Any other value

**Examples:**

```bash
# Set boolean
claudefig config set init.overwrite_existing true

# Set string
claudefig config set custom.template_dir "/path/to/templates"

# Set integer
claudefig config set custom.max_files 100
```

**Output:**

```
✓ Set init.overwrite_existing = True
Config saved to: /path/to/.claudefig.toml
```

## Files Commands

Manage file instances (files to be generated).

### `claudefig files list`

List all configured file instances.

**Usage:**

```bash
claudefig files list [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |
| `--type TYPE` | Filter by file type | None (show all) |
| `--enabled-only` | Show only enabled instances | False (show all) |

**Examples:**

```bash
# List all instances
claudefig files list

# List only CLAUDE.md instances
claudefig files list --type claude_md

# List only enabled instances
claudefig files list --enabled-only

# Combine filters
claudefig files list --type settings_json --enabled-only

# From specific directory
claudefig files list --path /path/to/repo
```

**Example Output:**

```
File Instances (4)

CLAUDE.md
  ✓ claude_md-default
      Path: CLAUDE.md
      Preset: claude_md:default
  - claude_md-backend
      Path: docs/BACKEND.md
      Preset: claude_md:backend

Settings (settings.json)
  ✓ settings_json-default
      Path: .claude/settings.json
      Preset: settings_json:default
```

Legend:
- `✓` = Enabled
- `-` = Disabled

### `claudefig files add`

Add a new file instance.

**Usage:**

```bash
claudefig files add FILE_TYPE [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `FILE_TYPE` | Type of file (e.g., `claude_md`, `settings_json`) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--preset NAME` | Preset name to use | `default` |
| `--path-target PATH` | Target path for the file | File type default |
| `--disabled` | Create instance as disabled | False (enabled) |
| `--repo-path PATH` | Repository path | Current directory |

**Valid File Types:**

- `claude_md` - CLAUDE.md files
- `settings_json` - Team settings
- `settings_local_json` - Personal settings
- `gitignore` - .gitignore entries
- `commands` - Slash commands
- `agents` - Custom agents
- `hooks` - Hook scripts
- `output_styles` - Output styles
- `statusline` - Status line script
- `mcp` - MCP server configs

**Examples:**

```bash
# Add with defaults
claudefig files add claude_md

# Add with specific preset
claudefig files add claude_md --preset backend

# Add with custom path
claudefig files add claude_md --preset frontend --path-target docs/FRONTEND.md

# Add as disabled
claudefig files add hooks --disabled

# Full example
claudefig files add claude_md \
  --preset backend \
  --path-target backend/CLAUDE.md \
  --repo-path /path/to/repo
```

**Output:**

```
✓ Added file instance: claude_md-backend
  Type: CLAUDE.md
  Preset: claude_md:backend
  Path: backend/CLAUDE.md
  Enabled: True

Config saved to: /path/to/.claudefig.toml
```

### `claudefig files remove`

Remove a file instance.

**Usage:**

```bash
claudefig files remove INSTANCE_ID [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `INSTANCE_ID` | ID of the instance to remove |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |

**Examples:**

```bash
# Remove an instance
claudefig files remove claude_md-backend

# From specific directory
claudefig files remove claude_md-backend --path /path/to/repo
```

**Output:**

```
✓ Removed file instance: claude_md-backend
Config saved to: /path/to/.claudefig.toml
```

### `claudefig files enable`

Enable a file instance.

**Usage:**

```bash
claudefig files enable INSTANCE_ID [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `INSTANCE_ID` | ID of the instance to enable |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |

**Examples:**

```bash
# Enable an instance
claudefig files enable claude_md-backend

# From specific directory
claudefig files enable claude_md-backend --path /path/to/repo
```

**Output:**

```
✓ Enabled file instance: claude_md-backend
Config saved to: /path/to/.claudefig.toml
```

### `claudefig files disable`

Disable a file instance.

**Usage:**

```bash
claudefig files disable INSTANCE_ID [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `INSTANCE_ID` | ID of the instance to disable |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |

**Examples:**

```bash
# Disable an instance
claudefig files disable claude_md-experimental

# From specific directory
claudefig files disable claude_md-experimental --path /path/to/repo
```

**Output:**

```
✓ Disabled file instance: claude_md-experimental
Config saved to: /path/to/.claudefig.toml
```

## Presets Commands

Manage presets (templates for file types).

### `claudefig presets list`

List available presets.

**Usage:**

```bash
claudefig presets list [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--type TYPE` | Filter by file type | None (show all) |

**Examples:**

```bash
# List all presets
claudefig presets list

# List CLAUDE.md presets only
claudefig presets list --type claude_md

# List settings presets
claudefig presets list --type settings_json
```

**Example Output:**

```
Available Presets (12)

CLAUDE.md
  - Default [built-in]
      ID: claude_md:default
      General-purpose project instructions
  - Minimal [built-in]
      ID: claude_md:minimal
      Minimal template with basic structure
  - Backend Focused [built-in]
      ID: claude_md:backend
      Backend development focus
  - Frontend Focused [built-in]
      ID: claude_md:frontend
      Frontend development focus

Settings (settings.json)
  - Default [built-in]
      ID: settings_json:default
      Standard team settings
```

### `claudefig presets show`

Show detailed information about a preset.

**Usage:**

```bash
claudefig presets show PRESET_ID
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PRESET_ID` | Preset ID in format `file_type:preset_name` |

**Examples:**

```bash
# Show CLAUDE.md default preset
claudefig presets show claude_md:default

# Show backend preset
claudefig presets show claude_md:backend

# Show settings preset
claudefig presets show settings_json:default
```

**Example Output:**

```
Preset Details

ID:          claude_md:backend
Name:        Backend Focused
Type:        CLAUDE.md
Source:      built-in
Description: Backend development focus with API, database, and testing guidelines

Variables:
  • project_name: Backend Project
  • language: Python
  • framework: FastAPI
  • database: PostgreSQL
```

## Examples

### Example 1: Basic Project Setup

Initialize a new project with default configuration:

```bash
# Step 1: Initialize (creates default config)
claudefig init

# Step 2: View what was created
claudefig files list
```

### Example 2: Custom Backend Project

Set up a backend project with custom files:

```bash
# Add backend-focused CLAUDE.md
claudefig files add claude_md --preset backend --path-target CLAUDE.md

# Add team settings
claudefig files add settings_json --preset default

# Add MCP configs
claudefig files add mcp --preset default

# Generate all files
claudefig init --force

# View configuration
claudefig files list
```

### Example 3: Multi-Context Setup

Create separate CLAUDE.md files for different parts of the codebase:

```bash
# Main project context
claudefig files add claude_md --preset default --path-target CLAUDE.md

# Backend context
claudefig files add claude_md --preset backend --path-target backend/CLAUDE_BACKEND.md

# Frontend context
claudefig files add claude_md --preset frontend --path-target frontend/CLAUDE_FRONTEND.md

# Testing guidelines
claudefig files add claude_md --preset minimal --path-target tests/CLAUDE_TESTING.md

# Generate all
claudefig init --force
```

### Example 4: Incremental Adoption

Add features over time:

```bash
# Week 1: Basic setup
claudefig files add claude_md --preset default
claudefig init

# Week 2: Add settings
claudefig files add settings_json --preset default
claudefig init --force

# Week 3: Add commands and agents
claudefig files add commands --preset default
claudefig files add agents --preset default
claudefig init --force

# Week 4: Add hooks
claudefig files add hooks --preset default
claudefig init --force
```

### Example 5: Enable/Disable Features

Toggle features without deleting them:

```bash
# Temporarily disable experimental features
claudefig files disable claude_md-experimental
claudefig files disable agents-custom

# Generate without experimental features
claudefig init --force

# Re-enable later
claudefig files enable claude_md-experimental
claudefig files enable agents-custom

# Generate with all features
claudefig init --force
```

### Example 6: Browse and Apply Presets

Explore available presets:

```bash
# List all presets
claudefig presets list

# View details of a preset
claudefig presets show claude_md:backend

# Apply it if you like it
claudefig files add claude_md --preset backend

# Generate
claudefig init
```

### Example 7: Configuration Management

Manage configuration values:

```bash
# View all settings
claudefig config list

# Check specific setting
claudefig config get init.overwrite_existing

# Enable force mode by default
claudefig config set init.overwrite_existing true

# Verify change
claudefig config get init.overwrite_existing
```

### Example 8: Team Workflow

Share configuration with team:

```bash
# Developer 1: Create team config
claudefig files add claude_md --preset backend
claudefig files add settings_json --preset default
claudefig files add commands --preset default

# Commit configuration
git add .claudefig.toml
git commit -m "Add claudefig configuration"
git push

# Developer 2: Use team config
git pull
claudefig files list  # See team configuration
claudefig init        # Generate files
```

### Example 9: MCP Server Setup

Configure MCP servers:

```bash
# Add MCP preset
claudefig files add mcp --preset default

# Generate MCP config files
claudefig init --force

# Edit MCP configs in .claude/mcp/
# (Add your API keys, configure servers, etc.)

# Set up MCP servers with Claude Code
claudefig setup-mcp
```

### Example 10: Working with Multiple Projects

Manage different projects:

```bash
# Project 1: Backend API
cd ~/projects/backend-api
claudefig files add claude_md --preset backend
claudefig init

# Project 2: Frontend App
cd ~/projects/frontend-app
claudefig files add claude_md --preset frontend
claudefig init

# Project 3: Full-stack
cd ~/projects/fullstack
claudefig files add claude_md --preset default --path-target CLAUDE.md
claudefig files add claude_md --preset backend --path-target backend/CLAUDE.md
claudefig files add claude_md --preset frontend --path-target frontend/CLAUDE.md
claudefig init
```

## Tips and Tricks

### Tip 1: Use TUI for Discovery

The interactive TUI is great for exploring:

```bash
# Launch TUI
claudefig interactive

# Browse presets, view descriptions
# Try different configurations
# Preview before committing
```

### Tip 2: Dry Run with Disabled Instances

Test configurations without generating files:

```bash
# Add instance as disabled
claudefig files add claude_md --preset experimental --disabled

# Review configuration
claudefig files list

# Enable when ready
claudefig files enable claude_md-experimental
claudefig init --force
```

### Tip 3: Scripting with claudefig

Use claudefig in scripts:

```bash
#!/bin/bash
# setup-claude.sh - Automated claudefig setup

# Add configuration
claudefig files add claude_md --preset "$PROJECT_TYPE"
claudefig files add settings_json --preset default

# Generate files
claudefig init --force

echo "Claude Code setup complete!"
```

### Tip 4: Backup Configuration

Save your configuration:

```bash
# Backup
cp .claudefig.toml .claudefig.toml.backup

# Restore if needed
cp .claudefig.toml.backup .claudefig.toml
```

### Tip 5: Quick Instance Listing

Create aliases for common commands:

```bash
# In your .bashrc or .zshrc
alias cf='claudefig'
alias cfl='claudefig files list'
alias cfi='claudefig init --force'
alias cft='claudefig interactive'
```

Then use:

```bash
cfl              # List files
cft              # Launch TUI
cfi              # Force init
```

## Exit Codes

claudefig uses standard Unix exit codes:

- `0` - Success
- `1` - General error
- `2` - Command-line usage error

Check exit codes in scripts:

```bash
if claudefig init; then
  echo "Initialization successful"
else
  echo "Initialization failed"
  exit 1
fi
```

## Environment Variables

claudefig respects these environment variables:

- `HOME` - User home directory (for `~/.claudefig/`)
- `PWD` - Current working directory

## Troubleshooting

### Command Not Found

**Error:** `claudefig: command not found`

**Solution:**

```bash
# Install claudefig
pip install claudefig

# Verify installation
claudefig --version

# Check PATH
which claudefig
```

### Config File Not Found

**Error:** Configuration not loading

**Solution:**

```bash
# Check for config file
ls -la .claudefig.toml

# Create if missing
claudefig init

# Use specific path
claudefig --path /path/to/project init
```

### Invalid File Type

**Error:** `Invalid file type: xyz`

**Solution:**

```bash
# List valid types
claudefig presets list

# Valid types:
# claude_md, settings_json, settings_local_json, gitignore,
# commands, agents, hooks, output_styles, statusline, mcp
```

### Preset Not Found

**Error:** `Preset 'claude_md:xyz' not found`

**Solution:**

```bash
# List available presets for type
claudefig presets list --type claude_md

# Use a valid preset ID
claudefig files add claude_md --preset default
```

## See Also

- [Getting Started with Presets](PRESETS_GUIDE.md)
- [Customizing Your Configuration](CONFIG_GUIDE.md)
- [README](../README.md)
