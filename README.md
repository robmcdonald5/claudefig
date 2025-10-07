# claudefig

[![PyPI version](https://badge.fury.io/py/claudefig.svg)](https://badge.fury.io/py/claudefig)
[![Python versions](https://img.shields.io/pypi/pyversions/claudefig.svg)](https://pypi.org/project/claudefig/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Universal config CLI tool for setting up Claude Code repositories in an organized fashion.

## Overview

**claudefig** is a command-line tool designed to help developers quickly set up and configure repositories for use with Claude Code. It provides templates, configurations, and best practices for organizing your Claude Code projects with proper documentation, MCP servers, scripts, and settings.

## Features

- Initialize Claude Code configuration files (.md, .mcp)
- Generate project documentation templates
- Set up organized directory structures
- Configure Claude Code settings
- Manage MCP server configurations
- Create custom scripts and workflows

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

```bash
# Initialize Claude Code configuration
claudefig init

# Show current configuration
claudefig show

# Add a new template
claudefig add-template <template-name>

# List available templates
claudefig list-templates
```

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