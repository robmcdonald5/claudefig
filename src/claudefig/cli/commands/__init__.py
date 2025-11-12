"""Command modules for claudefig CLI.

This package contains all command group modules:
- components: Component discovery and management
- config: Configuration management
- files: File instance management
- presets: Preset management (project-level configuration templates)
"""

from . import components, config, files, presets

__all__ = ["components", "config", "files", "presets"]
