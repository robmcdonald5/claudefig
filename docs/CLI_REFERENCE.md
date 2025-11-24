# CLI Reference

Complete command-line reference for claudefig.

## Table of Contents

- [Global Options](#global-options)
- [Main Commands](#main-commands)
- [Config Commands](#config-commands)
- [Files Commands](#files-commands)
- [Components Commands](#components-commands)
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

1. Loads configuration from `claudefig.toml`
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

Config file: /path/to/project/claudefig.toml

┌────────────────────────────┬────────────┐
│ Setting                    │ Value      │
├────────────────────────────┼────────────┤
│ Template Source            │ built-in   │
│ Create CLAUDE.md           │ True       │
│ Create Settings            │ True       │
│ Update .gitignore          │ True       │
└────────────────────────────┴────────────┘
```

### `claudefig sync`

Regenerate files from current configuration.

**Usage:**

```bash
claudefig sync [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |
| `--force` | Overwrite existing files | False |

**Examples:**

```bash
# Sync files in current directory
claudefig sync

# Sync with force overwrite
claudefig sync --force

# Sync specific directory
claudefig sync --path /path/to/repo

# Combine options
claudefig sync --path ../my-project --force
```

**What it does:**

1. Reads `claudefig.toml` configuration
2. Regenerates all enabled file instances
3. Updates files based on current configuration
4. Useful after modifying config or updating presets

**When to use:**

- After editing `claudefig.toml` manually
- After changing file instance configurations
- After updating preset templates
- To refresh all generated files

### `claudefig validate`

Validate project configuration and file instances.

**Usage:**

```bash
claudefig validate [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Repository path | Current directory |

**Examples:**

```bash
# Validate current directory
claudefig validate

# Validate specific directory
claudefig validate --path /path/to/repo
```

**Example Output:**

```
Validating configuration in: /path/to/project

⚠ Found 2 warning(s):

  • claude_md-default: Template variable 'project_name' not set
  • settings_json-default: File does not exist at path

Health: ⚠ Warnings detected

Validated 5 enabled instance(s)
```

**What it checks:**

- Configuration file structure and syntax
- File instance definitions
- Preset references validity
- Path conflicts between instances
- Missing template variables
- File existence (for update mode)

**Exit codes:**

- `0` - All validations passed (green health)
- `0` - Warnings detected (yellow health)
- `1` - Errors detected (red health)

### `claudefig setup-mcp`

Set up MCP servers from configuration files.

**Note:** MCP servers are **automatically registered during `claudefig init`**. This command is mainly for manual re-registration or troubleshooting.

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

# Re-register after editing MCP configs
# Edit .claude/mcp/github.json
claudefig setup-mcp
```

**Configuration Patterns:**

Supports two configuration patterns (checks both):

1. **Standard `.mcp.json`** (project root)
   ```json
   {
     "command": "npx",
     "args": ["-y", "@modelcontextprotocol/server-github"],
     "env": {
       "GITHUB_TOKEN": "${GITHUB_TOKEN}"
     }
   }
   ```

2. **Multiple files in `.claude/mcp/`** (claudefig extended)
   ```
   .claude/mcp/
   ├── github.json
   ├── notion.json
   └── custom-api.json
   ```

**What it does:**

1. Finds configuration files (`.mcp.json` or `.claude/mcp/*.json`)
2. Validates JSON syntax
3. Validates transport type (stdio, http, sse)
4. Checks for security issues:
   - Warns about HTTP (non-HTTPS) usage
   - Detects hardcoded credentials
   - Validates required fields per transport type
5. Runs `claude mcp add-json <name> <config>` for each server
6. Reports success/failure for each registration

**Transport Types:**

- **STDIO**: Local command-line tools (npm packages)
- **HTTP**: Remote cloud services (OAuth 2.1 or API keys)
- **SSE**: Server-Sent Events (deprecated)

**Requirements:**

- Claude Code CLI must be installed
- `claude` command must be in PATH
- Valid MCP configuration file(s)

**See Also:**

- `docs/ADDING_NEW_COMPONENTS.md` - MCP configuration guide
- `docs/MCP_SECURITY_GUIDE.md` - Security best practices
- `src/presets/default/components/mcp/` - Template examples

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
Configuration from: /path/to/claudefig.toml

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
Config saved to: /path/to/claudefig.toml
```

### `claudefig config set-init`

Manage initialization settings.

**Usage:**

```bash
claudefig config set-init [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--overwrite/--no-overwrite` | Allow overwriting existing files during init | None |
| `--backup/--no-backup` | Create backup files before overwriting | None |
| `--path PATH` | Repository path | Current directory |

**Examples:**

```bash
# View current init settings
claudefig config set-init

# Enable overwriting files during init
claudefig config set-init --overwrite

# Disable overwriting
claudefig config set-init --no-overwrite

# Enable backup creation
claudefig config set-init --backup

# Disable backups
claudefig config set-init --no-backup

# Combine settings
claudefig config set-init --overwrite --no-backup

# From specific directory
claudefig config set-init --overwrite --path /path/to/repo
```

**Output (viewing settings):**

```
Current initialization settings:

Overwrite existing: False
Create backups:     True

Use --overwrite/--no-overwrite or --backup/--no-backup to change settings
```

**Output (changing settings):**

```
+ Updated initialization settings:
  overwrite_existing: enabled
  create_backup: disabled

Config saved to: /path/to/claudefig.toml
```

**What it controls:**

- **overwrite_existing**: Whether `claudefig init` and `sync` overwrite existing files
- **create_backup**: Whether to create `.bak` backups before overwriting files

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
| `--component NAME` | Component name to use (alternative to --preset) | None |
| `--path-target PATH` | Target path for the file | File type default |
| `--disabled` | Create instance as disabled | False (enabled) |
| `--repo-path PATH` | Repository path | Current directory |

**Note:** Use either `--preset` or `--component`, not both. If neither is provided, defaults to `default`.

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
- `mcp` - MCP server configs (3 variants: stdio-local, http-oauth, http-apikey)
- `plugins` - Claude Code Plugins
- `skills` - Claude Code Skills

**Examples:**

```bash
# Add with defaults
claudefig files add claude_md

# Add with specific preset
claudefig files add claude_md --preset backend

# Add with specific component
claudefig files add claude_md --component fastapi-backend

# Add with custom path
claudefig files add claude_md --preset frontend --path-target docs/FRONTEND.md

# Add component with custom path
claudefig files add claude_md --component react-frontend --path-target frontend/CLAUDE.md

# Add as disabled
claudefig files add hooks --disabled

# Full example with preset
claudefig files add claude_md \
  --preset backend \
  --path-target backend/CLAUDE.md \
  --repo-path /path/to/repo

# Full example with component
claudefig files add claude_md \
  --component fastapi-backend \
  --path-target api/CLAUDE.md \
  --repo-path /path/to/repo
```

**Output:**

```
✓ Added file instance: claude_md-backend
  Type: CLAUDE.md
  Preset: claude_md:backend
  Path: backend/CLAUDE.md
  Enabled: True

Config saved to: /path/to/claudefig.toml
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
Config saved to: /path/to/claudefig.toml
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
Config saved to: /path/to/claudefig.toml
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
Config saved to: /path/to/claudefig.toml
```

### `claudefig files edit`

Edit an existing file instance.

**Usage:**

```bash
claudefig files edit INSTANCE_ID [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `INSTANCE_ID` | ID of the instance to edit |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--preset NAME` | New preset to use | None (no change) |
| `--path-target PATH` | New target path for the file | None (no change) |
| `--enable/--disable` | Enable or disable the instance | None (no change) |
| `--repo-path PATH` | Repository path | Current directory |

**Examples:**

```bash
# Change preset
claudefig files edit claude_md-default --preset backend

# Change target path
claudefig files edit claude_md-default --path-target docs/CLAUDE.md

# Change enabled state
claudefig files edit claude_md-default --disable
claudefig files edit claude_md-default --enable

# Change multiple properties
claudefig files edit claude_md-default \
  --preset backend \
  --path-target backend/CLAUDE.md \
  --enable

# From specific directory
claudefig files edit claude_md-default --preset backend --repo-path /path/to/repo
```

**Output:**

```
+ Updated file instance: claude_md-default

Changes:
  preset: claude_md:default → claude_md:backend
  path: CLAUDE.md → backend/CLAUDE.md

Config saved to: /path/to/claudefig.toml
```

**Notes:**

- At least one option (`--preset`, `--path-target`, or `--enable/--disable`) must be provided
- Changes are validated before being saved
- The instance ID cannot be changed (remove and re-add instead)

## Components Commands

Discover and manage components.

Components are reusable content templates that can be added to file instances. Components can be global (available to all projects) or preset-specific.

### `claudefig components list`

List available components.

**Usage:**

```bash
claudefig components list [FILE_TYPE] [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `FILE_TYPE` | Optional file type filter (e.g., claude_md, settings_json) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--preset NAME` | Preset to search for components | default |

**Examples:**

```bash
# List all components
claudefig components list

# List CLAUDE.md components only
claudefig components list claude_md

# List components from specific preset
claudefig components list claude_md --preset my-preset
```

**Example Output:**

```
Available Components - claude_md (3)

Claude Md

  • default (preset)
  • fastapi-backend (global)
    FastAPI backend with PostgreSQL focus
  • react-frontend (global)
    React frontend development focus

Global: ~/.claudefig/components

Use 'claudefig components show <type> <name>' for details
```

**Component Sources:**

- **(preset)** - Component from preset-specific folder
- **(global)** - Component from global pool (`~/.claudefig/components/`)

### `claudefig components show`

Show detailed information about a component.

**Usage:**

```bash
claudefig components show FILE_TYPE COMPONENT_NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `FILE_TYPE` | Component type (e.g., claude_md) |
| `COMPONENT_NAME` | Name of the component |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--preset NAME` | Preset to search for components | default |

**Examples:**

```bash
# Show default component
claudefig components show claude_md default

# Show specific component
claudefig components show claude_md fastapi-backend
```

**Example Output:**

```
Component Details

Name:        fastapi-backend
Type:        claude_md
Source:      Global
Path:        ~/.claudefig/components/claude_md/fastapi-backend
Description: FastAPI backend with PostgreSQL, Redis, and testing best practices
Version:     1.0.0
Author:      claudefig
Tags:        fastapi, backend, api, python

Requires:
  • languages/python

Recommends:
  • general/testing-principles

Files:
  • content.md (8.2 KB)
  • component.toml (0.7 KB)
```

### `claudefig components open`

Open the components directory in file explorer.

**Usage:**

```bash
claudefig components open [FILE_TYPE]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `FILE_TYPE` | Optional file type to open specific type folder |

**Examples:**

```bash
# Open global components directory
claudefig components open

# Open claude_md components folder
claudefig components open claude_md
```

**Output:**

```
Opening components directory: ~/.claudefig/components/claude_md/

+ Opened in file manager
```

**Use cases:**

- Browse available components
- Manually create or modify components
- Copy components between machines
- Inspect component structure

### `claudefig components edit`

Edit a component's primary content file in your default editor.

**Usage:**

```bash
claudefig components edit FILE_TYPE COMPONENT_NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `FILE_TYPE` | Component type (e.g., claude_md) |
| `COMPONENT_NAME` | Name of the component |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--preset NAME` | Preset to search for components | default |

**Examples:**

```bash
# Edit a component
claudefig components edit claude_md fastapi-backend

# Edit preset-specific component
claudefig components edit claude_md default --preset my-preset
```

**Output:**

```
Opening component file: ~/.claudefig/components/claude_md/fastapi-backend/content.md

Opening content.md in editor...
+ Component file edited
```

**Notes:**

- Opens the primary content file (usually `content.md`)
- Uses `$EDITOR` environment variable or system default
- Changes to global components affect all projects

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

### `claudefig presets apply`

Apply a preset to a project.

**Usage:**

```bash
claudefig presets apply PRESET_NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PRESET_NAME` | Name of the preset to apply |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Project path to apply preset to | Current directory |

**Examples:**

```bash
# Apply a preset to current directory
claudefig presets apply my-fastapi-preset

# Apply to specific directory
claudefig presets apply backend-template --path /path/to/new-project
```

**Output:**

```
Applying preset 'my-fastapi-preset' to: /path/to/project

+ Preset 'my-fastapi-preset' applied successfully!
Created: /path/to/project/claudefig.toml
```

**What it does:**

1. Loads the preset configuration from `~/.claudefig/presets/{preset_name}/`
2. Creates `claudefig.toml` in the target directory
3. Copies all file instance definitions from the preset

**Note:** This will fail if `claudefig.toml` already exists in the target directory.

### `claudefig presets create`

Save current project config as a preset.

**Usage:**

```bash
claudefig presets create PRESET_NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PRESET_NAME` | Name for the new preset |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--description TEXT` | Description of the preset | Empty string |
| `--path PATH` | Project path to save config from | Current directory |

**Examples:**

```bash
# Create preset from current project
claudefig presets create my-fastapi-project

# Create with description
claudefig presets create my-fastapi-project \
  --description "FastAPI project with PostgreSQL and Redis"

# Create from specific directory
claudefig presets create backend-template --path /path/to/project
```

**Output:**

```
+ Created preset: my-fastapi-project
Location: ~/.claudefig/presets/my-fastapi-project/claudefig.toml
```

**What it does:**

1. Reads `claudefig.toml` from the project directory
2. Saves it to `~/.claudefig/presets/{preset_name}/claudefig.toml`
3. Preset becomes available globally for reuse

**Requirements:**

- Project must have a `claudefig.toml` file
- Run `claudefig init` first if the project doesn't have a config

### `claudefig presets create-from-repo`

Create a preset by scanning a repository for existing Claude Code components.

**Usage:**

```bash
claudefig presets create-from-repo PRESET_NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PRESET_NAME` | Name for the new preset |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--description`, `-d` | Description of the preset | Empty string |
| `--path`, `-p` | Repository path to scan | Current directory |

**Examples:**

```bash
# Create preset from current repository
claudefig presets create-from-repo my-project-preset

# Create with description
claudefig presets create-from-repo my-fastapi-preset \
  -d "FastAPI backend with existing Claude Code setup"

# Scan specific repository
claudefig presets create-from-repo legacy-setup --path /path/to/existing-repo
```

**Example Output:**

```
Scanning repository: /path/to/project

Found 5 components (scanned in 12.3ms)

┌────────────────────┬─────────────────┬───────────────────────────────┐
│ Component          │ Type            │ Path                          │
├────────────────────┼─────────────────┼───────────────────────────────┤
│ default            │ CLAUDE.md       │ CLAUDE.md                     │
│ backend            │ CLAUDE.md       │ backend/CLAUDE.md             │
│ review-pr          │ Slash Commands  │ .claude/commands/review-pr.md │
│ test-runner        │ Hooks           │ .claude/hooks/test-runner.py  │
│ github             │ MCP Servers     │ .claude/mcp/github.json       │
└────────────────────┴─────────────────┴───────────────────────────────┘

Creating preset 'my-project-preset' with all discovered components...

SUCCESS: Preset 'my-project-preset' created successfully!
Location: ~/.claudefig/presets/my-project-preset
Components: 5
```

**What it scans for:**

- `CLAUDE.md` files (anywhere in repository)
- `.gitignore` files
- `settings.json` / `settings.local.json` in `.claude/`
- Slash commands in `.claude/commands/`
- Sub-agents in `.claude/agents/`
- Hook scripts in `.claude/hooks/`
- Output styles in `.claude/output-styles/`
- Status line script (`.claude/statusline.sh`)
- MCP server configs in `.claude/mcp/`
- Plugins in `.claude/plugins/`
- Skills in `.claude/skills/`

**Notes:**

- This command includes **all** discovered components in the preset
- For interactive component selection, use the TUI: `claudefig interactive` → Presets → Create from Repo
- Duplicate component names are disambiguated using folder prefixes
- The preset is saved to `~/.claudefig/presets/{preset_name}/`

**Use cases:**

- Capture existing project setup as a reusable template
- Migrate manual Claude Code configurations to claudefig
- Share team configurations by exporting to presets
- Create backups of current configuration

### `claudefig presets delete`

Delete a preset.

**Usage:**

```bash
claudefig presets delete PRESET_NAME
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PRESET_NAME` | Name of the preset to delete |

**Examples:**

```bash
# Delete a preset (will prompt for confirmation)
claudefig presets delete my-old-preset
```

**Output:**

```
Are you sure you want to delete this preset? [y/N]: y
+ Deleted preset: my-old-preset
```

**Notes:**

- Requires confirmation before deleting
- Cannot delete built-in presets (like "default")
- Only deletes user-created presets from `~/.claudefig/presets/`

### `claudefig presets edit`

Edit a preset's TOML file in your default editor.

**Usage:**

```bash
claudefig presets edit PRESET_NAME
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PRESET_NAME` | Name of the preset to edit |

**Examples:**

```bash
# Edit a preset
claudefig presets edit my-preset

# Edit the default preset
claudefig presets edit default
```

**Output:**

```
Opening preset file: ~/.claudefig/presets/my-preset/claudefig.toml

Opening ~/.claudefig/presets/my-preset/claudefig.toml in editor...
+ Preset file edited
```

**What it does:**

1. Opens the preset's `claudefig.toml` file in your default editor
2. Uses `$EDITOR` environment variable if set, otherwise uses system default
3. Allows you to modify:
   - Preset metadata (name, description)
   - File instance definitions
   - Configuration settings

**Editor selection:**

- Unix/Linux/macOS: Uses `$EDITOR` or falls back to `xdg-open`
- Windows: Uses default `.toml` file association

**Warning:** Editing the "default" preset will affect all new projects that use it.

### `claudefig presets open`

Open the presets directory in file explorer.

**Usage:**

```bash
claudefig presets open
```

**Examples:**

```bash
# Open presets folder
claudefig presets open
```

**Output:**

```
Opening presets directory: ~/.claudefig/presets/

+ Opened in file manager
```

**What it does:**

1. Opens `~/.claudefig/presets/` in your system file manager
2. Allows you to browse, copy, or manually edit preset files

**File managers:**

- macOS: Opens in Finder
- Windows: Opens in File Explorer
- Linux: Opens in default file manager (Nautilus, Dolphin, etc.)

**Use cases:**

- Browse available presets
- Manually backup preset files
- Copy preset directories between machines
- Inspect preset structure

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
git add claudefig.toml
git commit -m "Add claudefig configuration"
git push

# Developer 2: Use team config
git pull
claudefig files list  # See team configuration
claudefig init        # Generate files
```

### Example 9: MCP Server Setup

Configure MCP servers with automatic registration:

```bash
# Option A: Local development tools (STDIO)
claudefig files add mcp --preset stdio-local
claudefig init  # Automatically registers MCP servers!

# Edit .claude/mcp/config.json
# Set GITHUB_TOKEN environment variable
export GITHUB_TOKEN="your_token"

# Option B: Cloud service with OAuth
claudefig files add mcp --preset http-oauth
claudefig init

# Edit .claude/mcp/config.json with OAuth token
# export MCP_ACCESS_TOKEN="your_oauth_token"
# export MCP_SERVICE_URL="https://api.service.com/mcp"

# Option C: Cloud service with API key
claudefig files add mcp --preset http-apikey
claudefig init

# Edit .claude/mcp/config.json
# export MCP_API_KEY="your_api_key"
# export MCP_API_URL="https://api.service.com/mcp"

# Manual re-registration (optional, if you edit configs later)
claudefig setup-mcp

# Verify MCP servers are registered
claude mcp list
```

**Available MCP Presets:**
- `mcp:stdio-local` - Local npm packages and command-line tools
- `mcp:http-oauth` - Cloud services with OAuth 2.1 authentication
- `mcp:http-apikey` - Cloud services with API key authentication

**See:** `docs/MCP_SECURITY_GUIDE.md` for security best practices

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
cp claudefig.toml claudefig.toml.backup

# Restore if needed
cp claudefig.toml.backup claudefig.toml
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
ls -la claudefig.toml

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
