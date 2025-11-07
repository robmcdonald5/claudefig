"""Command modules for claudefig CLI.

This package contains all command group modules:
- config: Configuration management
- files: File instance management
- presets: Preset management (project-level configuration templates)
"""

from . import config, files, presets

__all__ = ["config", "files", "presets"]
