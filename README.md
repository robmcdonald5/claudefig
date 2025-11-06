# claudefig

[![PyPI version](https://badge.fury.io/py/claudefig.svg)](https://badge.fury.io/py/claudefig)
[![Python versions](https://img.shields.io/pypi/pyversions/claudefig.svg)](https://pypi.org/project/claudefig/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Universal configuration manager for Claude Code projects with preset templates and interactive TUI.

**User Configuration Directory:**
- Windows: `C:\Users\{username}\.claudefig\`
- macOS/Linux: `~/.claudefig/`

## Overview

**claudefig** helps you set up and manage Claude Code repositories with a powerful preset system and interactive terminal UI. Instead of manually creating configuration files, use presets to generate best-practice templates for CLAUDE.md files, settings, slash commands, agents, hooks, and more.

## Features

### Core Features
- **Preset System** - Choose from built-in templates or create your own
- **Interactive TUI** - User-friendly terminal interface for managing configurations
- **File Instances** - Fine-grained control over which files to generate
- **CLI & TUI Parity** - Every feature available in both interfaces
- **Validation** - Automatic validation with helpful error messages
- **Flexible Configuration** - Stored in `claudefig.toml` (project) or `~/.claudefig/config.toml` (user home) with full TOML support

### Supported File Types

claudefig can generate and manage these Claude Code configuration files:

- **CLAUDE.md** - Project instructions and context for Claude Code
- **Settings** (`settings.json`, `settings.local.json`) - Team and personal settings
- **Slash Commands** (`commands/`) - Custom command definitions
- **Sub-Agents** (`agents/`) - Custom AI sub-agents for specialized tasks
- **Hooks** (`hooks/`) - Pre/post tool execution scripts
- **Output Styles** (`output-styles/`) - Custom Claude Code behavior profiles
- **Status Line** (`statusline.sh`) - Custom status bar script
- **MCP Servers** (`mcp/`) - Model Context Protocol configurations
- **.gitignore** - Auto-managed Claude Code exclusions

### Preset System

**Presets** are reusable templates for different file types:

- **Built-in Presets** - Default, minimal, full, backend-focused, frontend-focused variants
- **User Presets** - Create custom presets in `~/.claudefig/presets/`
- **Project Presets** - Project-specific presets in `.claudefig/presets/`
- **Preset Variables** - Customizable template variables
- **Preset Inheritance** - Extend existing presets

### File Instance Management

**File Instances** combine a file type, preset, and target path:

- Create multiple instances of the same file type (e.g., multiple CLAUDE.md files)
- Enable/disable instances without deleting them
- Override preset variables per instance
- Full validation with conflict detection

## Installation

### From PyPI (Recommended)

```bash
pip install claudefig
```

### From Source

```bash
git clone https://github.com/yourusername/claudefig.git
cd claudefig
pip install -e .
```

### For Development

```bash
git clone https://github.com/yourusername/claudefig.git
cd claudefig
pip install -e ".[dev]"
pre-commit install
```

## Quick Start

### Option 1: Interactive TUI (Recommended)

Launch the interactive terminal interface:

```bash
claudefig interactive
```

The TUI lets you:
- Browse and apply presets
- Manage file instances (add, edit, enable/disable)
- Preview configurations before generating
- Navigate with keyboard shortcuts

### Option 2: Quick Init

Apply the default preset and generate files:

```bash
claudefig init
```

This creates a basic Claude Code setup with default configurations.

## Usage

### Interactive TUI

The easiest way to manage claudefig is through the interactive TUI:

```bash
claudefig interactive
```

**TUI Features:**
- **Presets Panel** - Browse and apply presets for different file types
- **Files Panel** - View, add, edit, and toggle file instances
- **Keyboard Shortcuts** -
  - `ctrl+p` - Focus presets panel
  - `ctrl+f` - Focus files panel
  - `ctrl+a` - Add new file instance
  - `ctrl+g` - Generate files
  - `ctrl+q` - Quit
  - `enter` - Apply preset or edit instance
  - `space` - Toggle instance enabled/disabled

### CLI Commands

#### Initialization

```bash
# Initialize repository with default preset
claudefig init

# Initialize with custom path
claudefig init --path /path/to/repo

# Force overwrite existing files
claudefig init --force
```

#### Preset Management

```bash
# List available presets
claudefig presets list

# List presets for specific file type
claudefig presets list --type claude_md

# Show preset details
claudefig presets show claude_md:default

# Create a new preset
claudefig presets create my_preset --type claude_md --description "My custom preset"

# Create a preset from a template file
claudefig presets create my_preset --type claude_md --template /path/to/template.md

# Edit a preset in your default editor
claudefig presets edit claude_md:my_preset

# Delete a preset (with confirmation)
claudefig presets delete claude_md:my_preset

# Delete without confirmation
claudefig presets delete claude_md:my_preset --force

# Open presets directory in file explorer
claudefig presets open
```

#### File Instance Management

```bash
# List all file instances
claudefig files list

# List only enabled instances
claudefig files list --enabled

# Add a new file instance
claudefig files add --type claude_md --preset claude_md:default --path CLAUDE.md

# Enable/disable an instance
claudefig files enable <instance-id>
claudefig files disable <instance-id>

# Remove an instance
claudefig files remove <instance-id>
```

#### Preset Management

```bash
# List all available presets
claudefig presets list

# List with validation status
claudefig presets list --validate

# Show preset details
claudefig presets show default

# Save current project as a preset
claudefig presets create my_preset --description "My project preset"

# Apply a preset to current project
claudefig presets apply default

# Edit a preset in your default editor
claudefig presets edit my_preset

# Delete a preset (with confirmation)
claudefig presets delete my_preset
```

#### Configuration

```bash
# View current configuration
claudefig config show

# Get a specific value
claudefig config get init.overwrite_existing

# Set a value
claudefig config set init.overwrite_existing true
```

### Workflow Examples

#### Example 1: Basic Setup

```bash
# Launch TUI and configure interactively
claudefig interactive

# Or use CLI to apply default preset and generate
claudefig init
```

#### Example 2: Custom Multi-File Setup

```bash
# Add multiple CLAUDE.md files for different contexts
claudefig files add --type claude_md --preset claude_md:backend --path CLAUDE.md
claudefig files add --type claude_md --preset claude_md:frontend --path docs/FRONTEND.md

# Add settings
claudefig files add --type settings_json --preset settings_json:default --path .claude/settings.json

# Add custom commands
claudefig files add --type commands --preset commands:default --path .claude/commands/

# Generate all enabled files
claudefig init --force
```

#### Example 3: Creating Custom Presets

```bash
# Create a custom preset from a template file
claudefig presets create my_backend --type claude_md --template backend_template.md \
  --description "Backend-focused CLAUDE.md template"

# Edit the preset to customize it
claudefig presets edit claude_md:my_backend

# List all presets to verify
claudefig presets list --type claude_md

# Apply your custom preset
claudefig files add --type claude_md --preset claude_md:my_backend --path CLAUDE.md

# Generate the file
claudefig init
```

#### Example 4: Managing Global Presets

```bash
# Save current project configuration as a reusable preset
claudefig presets create my_fastapi_project --description "FastAPI backend preset"

# List all presets
claudefig presets list

# Apply preset to a new project
cd /path/to/new/project
claudefig presets apply my_fastapi_project

# Edit preset to update it
claudefig presets edit my_fastapi_project
```

For detailed usage instructions, run:

```bash
claudefig --help
```

## Documentation

### User Guides
- [Getting Started with Presets](docs/PRESETS_GUIDE.md) - Learn about the preset system
- [Customizing Your Configuration](docs/CONFIG_GUIDE.md) - Advanced configuration options
- [CLI Reference](docs/CLI_REFERENCE.md) - Complete command-line reference

### Project Documentation
- [Installation Guide](#installation) - Installation instructions
- [Quick Start](#quick-start) - Get up and running quickly
- [Usage Examples](#usage) - Common workflows and examples
- [Architecture Documentation](ARCHITECTURE.md) - System architecture and design patterns
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute
- [Changelog](CHANGELOG.md) - Version history

## Requirements

- Python 3.10 or higher
- Click >= 8.0
- Rich >= 13.0

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- How to submit bug reports
- How to propose new features
- Development setup
- Code style guidelines
- Testing requirements

Please also review our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built for use with [Claude Code](https://claude.com/claude-code), Anthropic's official CLI for Claude.

## Support

- [GitHub Issues](https://github.com/yourusername/claudefig/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/yourusername/claudefig/discussions) - Questions and community support

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes to this project.