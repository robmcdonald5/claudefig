# claudefig CLI Commands

Complete reference for all `claudefig` commands and flags.

---

## Table of Contents

- [Global Options](#global-options)
- [Commands](#commands)
  - [init](#init)
  - [show](#show)
  - [list-templates](#list-templates)
  - [add-template](#add-template)

---

## Global Options

These options work with any command:

### `--version`

Display the current version of claudefig and exit.

```bash
claudefig --version
```

**Output:**
```
claudefig, version 0.1.dev
```

### `--help`

Display help information for claudefig or a specific command.

```bash
# General help
claudefig --help

# Command-specific help
claudefig init --help
claudefig show --help
```

---

## Commands

### `init`

Initialize Claude Code configuration in a repository.

**Description:**
Creates the necessary files and directory structure for Claude Code integration in your repository. This includes:
- `.claude/` directory
- `CLAUDE.md` configuration file
- `CONTRIBUTING.md` template
- `claudefig.toml` configuration file

**Usage:**
```bash
claudefig init [OPTIONS]
```

**Options:**

#### `--path DIRECTORY`

Specify the repository path to initialize (default: current directory).

- **Type:** Directory path
- **Default:** `.` (current directory)
- **Required:** No

**Examples:**
```bash
# Initialize current directory
claudefig init

# Initialize specific directory
claudefig init --path /path/to/repo

# Initialize relative path
claudefig init --path ../my-project
```

#### `--force`

Overwrite existing configuration files without prompting.

- **Type:** Flag (boolean)
- **Default:** `False`
- **Required:** No

**Examples:**
```bash
# Force overwrite existing files
claudefig init --force

# Combine with --path
claudefig init --path /path/to/repo --force
```

**Behavior:**
- If the target directory is not a git repository, claudefig will prompt you to continue
- Creates `.claude/` directory if it doesn't exist
- Copies template files based on configuration settings
- Skips existing files unless `--force` is specified
- Creates `claudefig.toml` if it doesn't exist (never overwrites)

**Exit Codes:**
- `0` - Success
- `1` - Initialization failed or was cancelled

---

### `show`

Display the current Claude Code configuration settings.

**Description:**
Shows the active configuration, including settings from `claudefig.toml` or default values if no config file exists.

**Usage:**
```bash
claudefig show
```

**Options:**
None

**Example Output:**
```
Current Configuration:

Config file: /path/to/repo/claudefig.toml

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Setting                      ┃ Value   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ Template Source              │ default │
│ Create CLAUDE.md             │ True    │
│ Create CONTRIBUTING.md       │ True    │
│ Create Settings              │ False   │
└──────────────────────────────┴─────────┘
```

**Configuration Keys Shown:**
- **Template Source:** Which template set to use (`default`, `minimal`, custom)
- **Create CLAUDE.md:** Whether to create CLAUDE.md file
- **Create CONTRIBUTING.md:** Whether to create CONTRIBUTING.md file
- **Create Settings:** Whether to create settings.json in `.claude/`
- **Custom Template Dir:** Path to custom templates (if configured)

---

### `list-templates`

List all available templates.

**Description:**
Displays all template sets available for use with `claudefig init`. This includes both built-in templates and custom templates (if a custom template directory is configured).

**Usage:**
```bash
claudefig list-templates
```

**Options:**
None

**Example Output:**
```
Available Templates:

  • default
  • minimal
  • python-ml
```

**Notes:**
- Built-in templates are always available
- Custom templates are loaded from the directory specified in `claudefig.toml` under `custom.template_dir`
- If no templates are found, displays: "No templates found"

---

### `add-template`

Add a new template to the repository.

**Description:**
Adds a new template set to your local template collection.

**Status:** 🚧 **Not yet implemented** - This command is planned for a future release.

**Usage:**
```bash
claudefig add-template TEMPLATE_NAME
```

**Arguments:**

#### `TEMPLATE_NAME`

Name of the template to add.

- **Type:** String
- **Required:** Yes
- **Position:** First argument

**Example (planned):**
```bash
claudefig add-template my-custom-template
```

**Current Behavior:**
Displays "Implementation in progress..." message.

---

## Configuration File

Commands respect settings in `claudefig.toml`. See the config file documentation for available options.

**Example `claudefig.toml`:**
```toml
[claudefig]
template_source = "default"

[init]
create_claude_md = true
create_contributing = true
create_settings = false

[custom]
# template_dir = "/path/to/custom/templates"
```

---

## Exit Codes

All commands use standard exit codes:

- `0` - Success
- `1` - Error or user cancellation

---

## Getting Help

For additional help:

- Run `claudefig --help` for command overview
- Run `claudefig COMMAND --help` for command-specific help
- Check the repository documentation at [GitHub](https://github.com/yourusername/claudefig)
