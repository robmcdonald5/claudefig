# claudefig

[![PyPI version](https://badge.fury.io/py/claudefig.svg)](https://badge.fury.io/py/claudefig)
[![Python versions](https://img.shields.io/pypi/pyversions/claudefig.svg)](https://pypi.org/project/claudefig/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Universal config CLI tool for setting up Claude Code repositories in an organized fashion.

## Overview

**claudefig** is a command-line tool designed to help developers quickly set up and configure repositories for use with Claude Code. It provides templates, configurations, and best practices for organizing your Claude Code projects with proper documentation, MCP servers, scripts, and settings.

## Features

### Core Features
- **Quick Initialization** - Set up Claude Code configuration in seconds
- **Organized Structure** - Create `.claude/` directory with best practices
- **Flexible Configuration** - Toggle features on/off via CLI or config file
- **Auto-gitignore** - Automatically update `.gitignore` with Claude Code files
- **Interactive TUI** - User-friendly text interface for configuration

### .claude/ Directory Features (Optional)

All features are **disabled by default** and can be enabled as needed:

- **Team Settings** (`settings.json`) - Shared permissions, hooks, and environment variables
- **Personal Settings** (`settings.local.json`) - Personal project-specific overrides
- **Slash Commands** (`commands/`) - Custom slash command definitions
- **Sub-Agents** (`agents/`) - Custom AI sub-agents for specialized tasks
- **Hooks** (`hooks/`) - Pre/post tool execution scripts for automation
- **Output Styles** (`output-styles/`) - Custom Claude Code behavior profiles
- **Status Line** (`statusline.sh`) - Custom status bar display script
- **MCP Servers** (`mcp/`) - Model Context Protocol server configurations

### Advanced Features
- **MCP Automation** - Auto-configure MCP servers with `claudefig setup-mcp`
- **Template System** - Community-driven templates (coming soon)
- **Config Management** - Get/set/list configuration via CLI
- **Incremental Adoption** - Enable only the features you need

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

Initialize a new Claude Code configuration in your repository:

```bash
claudefig init
```

This will create the necessary files and directory structure for Claude Code integration.

## Usage

### Basic Commands

```bash
# Initialize a repository with default settings
claudefig init

# Initialize with custom path
claudefig init --path /path/to/repo

# Force overwrite existing files
claudefig init --force

# Launch interactive TUI mode
claudefig interactive
```

### Configuration Management

Claudefig uses `.claudefig.toml` for configuration. You can manage settings via CLI:

```bash
# List all configuration settings
claudefig config list

# Get a specific setting
claudefig config get claude.create_settings

# Set a configuration value
claudefig config set claude.create_settings true
claudefig config set claude.create_hooks false
```

### .claude/ Directory Features

By default, claudefig creates an empty `.claude/` directory. You can enable optional features:

```bash
# Enable team-shared settings
claudefig config set claude.create_settings true

# Enable personal project settings
claudefig config set claude.create_settings_local true

# Enable custom slash commands
claudefig config set claude.create_commands true

# Enable custom sub-agents
claudefig config set claude.create_agents true

# Enable hook scripts
claudefig config set claude.create_hooks true

# Enable custom output styles
claudefig config set claude.create_output_styles true

# Enable custom status line
claudefig config set claude.create_statusline true

# Enable MCP server configs
claudefig config set claude.create_mcp true
```

After enabling features, re-run `claudefig init --force` to generate the files.

### MCP Server Setup

If you enable MCP server configs, claudefig will create `.claude/mcp/` with example configurations. To automatically set up these servers with Claude Code:

```bash
# Set up all MCP servers from .claude/mcp/
claudefig setup-mcp

# This runs 'claude mcp add-json' for each JSON file in .claude/mcp/
```

**MCP Workflow:**

1. Enable MCP feature:
   ```bash
   claudefig config set claude.create_mcp true
   claudefig init --force
   ```

2. Edit MCP configs in `.claude/mcp/`:
   ```bash
   # Rename example files and update with your credentials
   mv .claude/mcp/example-github.json .claude/mcp/github.json
   # Edit github.json to add your GITHUB_TOKEN
   ```

3. Set up MCP servers:
   ```bash
   claudefig setup-mcp
   ```

**Note:** Requires Claude Code CLI to be installed and in your PATH.

For detailed usage instructions, run:

```bash
claudefig --help
```

## Documentation

- [Installation Guide](https://github.com/yourusername/claudefig#installation)
- [Usage Examples](https://github.com/yourusername/claudefig#usage)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Requirements

- Python 3.9 or higher
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