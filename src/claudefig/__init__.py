"""claudefig - Universal config CLI tool for Claude Code repository setup."""

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
