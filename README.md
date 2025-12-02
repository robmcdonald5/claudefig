# claudefig

[![PyPI version](https://badge.fury.io/py/claudefig.svg)](https://badge.fury.io/py/claudefig)
[![Python versions](https://img.shields.io/pypi/pyversions/claudefig.svg)](https://pypi.org/project/claudefig/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Status: Beta](https://img.shields.io/badge/Status-Beta-blue.svg)](https://github.com/robmcdonald5/claudefig)

Universal configuration manager for Claude Code projects with preset templates and interactive TUI.

**User Configuration Directory:**
- Windows: `C:\Users\{username}\.claudefig\`
- Linux: `/home/{username}/.claudefig/`
- macOS: `/Users/{username}/.claudefig/`

## Overview

**claudefig** helps you quickly onboard Claude Code to your repositories with a powerful preset and config CLI/TUI. Instead of manually creating or copying over configuration files for new projects, claudefig lets you use presets and dynamically updated project configs to generate pre-defined coding CLI workflows.

## Features

### Core Features
- **Preset System** - Choose from built-in templates or create your own
- **Repository Scanning** - Create presets from existing Claude Code configurations (`presets create-from-repo`)
- **Interactive TUI** - User-friendly terminal interface with preset wizard for managing configurations
- **File Instances** - Fine-grained control over which files to generate
- **Validation** - Automatic validation with helpful error/warning messages
- **Flexible Configuration** - Stored in `claudefig.toml` (project) or `~/.claudefig/` (global home directory)

### Interface Options

Both the TUI and CLI provide comprehensive functionality. Some features are interface-specific to leverage each interface's strengths:

- **TUI**: Interactive component browsing, visual file selection, preset wizard
- **CLI**: Scriptable commands, preset editing, file sync operations

See [FEATURE_PARITY.md](docs/FEATURE_PARITY.md) for a detailed comparison.

### Supported File Types

claudefig can generate and manage these Claude Code configuration files:

- **CLAUDE.md** (`~/.claudefig/components/claude_md/`)
- **Local Settings** (`~/.claudefig/components/settings_json_local/`)
- **Team Settings**(`~/.claudefig/components/settings_json/`)
- **Slash Commands** (`~/.claudefig/components/commands/`)
- **Sub-Agents** (`~/.claudefig/components/agents/`)
- **Hooks** (`~/.claudefig/components/hooks/`)
- **Skills** (`~/.claudefig/components/skills/`)
- **Output Styles** (`~/.claudefig/components/output_styles/`)
- **Status Line** (`~/.claudefig/components/statusline/`)
- **MCP Servers** (`~/.claudefig/components/mcp/`)
- **Plugins** (`~/.claudefig/components/plugins/`)
- **.gitignore** (`~/.claudefig/components/gitignore/`)

### Preset System

**Presets** are reusable templates that are a saved state of an existing project config setup:

- **Built-in Presets** - Built in preset(s) that come with claudefig from the presets lib package
- **User Presets** - Create and store your own custom presets in `~/.claudefig/presets/`; [Presets Guide](docs/PRESETS_GUIDE.md) for tutorial on how to build properly
- **Preset Components** - Component(s) associated with a preset are stored in presets own components folder `~/.claudefig/presets/{preset_name}/components/`; both the TUI and CLI distinguish between global components and preset components via suffixes: `(g)` represents `~/.claudefig/components/` and `(p)` represents `~/.claudefig/presets/{preset_name}/components/`

### File Instance Management

**File Instances** combine a file type, preset, and target path:

- Create multiple instances of the same file type (e.g., multiple CLAUDE.md files)
- Define instance path(s) if applicable (e.g., CLAUDE.md or .gitignore files)
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
git clone https://github.com/robmcdonald5/claudefig.git
cd claudefig
pip install -e .
```

### For Development

```bash
git clone https://github.com/robmcdonald5/claudefig.git
cd claudefig
pip install -e ".[dev]"
pre-commit install
```

## Quick Start

### Option 1: Interactive TUI (Recommended)

Launch the interactive terminal interface:

```bash
claudefig
```

The TUI lets you:
- Browse and apply presets
- Create presets from existing repositories (Preset Wizard with component selection)
- Manage file instances (add, edit, enable/disable)
- Preview configurations before generating
- Navigate with keyboard shortcuts
- Initialize config and presets

### Option 2: Quick CLI Init

Apply the default preset and generate files:

```bash
claudefig init
```

This creates a basic Claude Code setup with default configurations

### Option 3: Custom CLI Usage

Customized workflows using the CLI:

[CLI Commands and Flags](docs/CLI_REFERENCE.md)

All claudefig inline features can be used directly by the CLI

### User Guides
- [Getting Started with Presets](docs/PRESETS_GUIDE.md) - Learn about the preset system
- [Customizing Your Configuration](docs/CONFIG_GUIDE.md) - All claudefig config options are defined here
- [CLI Reference](docs/CLI_REFERENCE.md) - Complete CLI reference

### Project Documentation
- [Installation Guide](#installation) - Installation instructions
- [Quick Start](#quick-start) - Get up and running quickly
- [Usage Examples](#usage) - Common workflows and examples
- [Architecture Documentation](docs/ARCHITECTURE.md) - System architecture and design patterns
- [MCP Security Guide](docs/MCP_SECURITY_GUIDE.md) - Security best practices for MCP servers
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute
- [Changelog](CHANGELOG.md) - Version history

## Requirements

- Python 3.10 or higher
- Click >= 8.0
- Rich >= 13.0

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- How to submit bug reports
- Development setup
- Code style guidelines
- Testing requirements

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built for use with [Claude Code](https://claude.com/claude-code), Anthropic's official CLI for Claude.

## Support

- [GitHub Issues](https://github.com/robmcdonald5/claudefig/issues) - Bug reports
- [GitHub Discussions](https://github.com/robmcdonald5/claudefig/discussions) - Questions and community support

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes to this project.
