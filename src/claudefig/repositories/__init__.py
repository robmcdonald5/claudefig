"""Repository layer for data persistence abstraction.

This module provides abstract interfaces and concrete implementations for
data access, following the Repository pattern to separate business logic
from storage concerns.
"""

from claudefig.repositories.base import (
    AbstractConfigRepository,
    AbstractPresetRepository,
)
from claudefig.repositories.config_repository import (
    FakeConfigRepository,
    TomlConfigRepository,
)
from claudefig.repositories.preset_repository import (
    FakePresetRepository,
    TomlPresetRepository,
)

__all__ = [
    "AbstractConfigRepository",
    "AbstractPresetRepository",
    "TomlConfigRepository",
    "FakeConfigRepository",
    "TomlPresetRepository",
    "FakePresetRepository",
]
