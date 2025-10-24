"""Utility functions for claudefig.

DEPRECATED: This module is deprecated. Import from claudefig.utils instead.

For backwards compatibility, this module re-exports functions from the new
utils package structure:
- claudefig.utils.paths
- claudefig.utils.platform
"""

import warnings

# Import from new structure for backwards compatibility
from claudefig.utils.paths import ensure_directory, is_git_repository  # noqa: F401

# Warn users to update their imports
warnings.warn(
    "claudefig.utils is deprecated. Import from claudefig.utils.paths or "
    "claudefig.utils.platform instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["ensure_directory", "is_git_repository"]
