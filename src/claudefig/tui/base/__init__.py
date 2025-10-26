"""Base classes and mixins for claudefig TUI."""

from .mixins import (
    BackButtonMixin,
    FileInstanceMixin,
    ScrollNavigationMixin,
    SystemUtilityMixin,
)
from .modal_screen import BaseModalScreen
from .navigation import (
    BaseHorizontalNavigablePanel,
    BaseNavigablePanel,
    BaseScreen,
)

__all__ = [
    "BaseHorizontalNavigablePanel",
    "BaseModalScreen",
    "BaseNavigablePanel",
    "BaseScreen",
    "BackButtonMixin",
    "FileInstanceMixin",
    "ScrollNavigationMixin",
    "SystemUtilityMixin",
]
