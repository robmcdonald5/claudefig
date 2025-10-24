"""Service layer for business logic.

This module provides the service layer that encapsulates business logic,
separating it from UI (CLI/TUI) and data access (repositories).

The service layer enables:
- Code reuse between CLI and TUI
- Testability through dependency injection
- Clear separation of concerns (UI → Services → Repositories → Storage)
"""

from claudefig.services import (
    config_service,
    file_instance_service,
    preset_service,
    validation_service,
)

__all__ = [
    "config_service",
    "preset_service",
    "file_instance_service",
    "validation_service",
]
