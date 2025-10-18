"""Modal screens for claudefig TUI."""

from .apply_preset import ApplyPresetScreen
from .core_files import CoreFilesScreen
from .create_preset import CreatePresetScreen
from .delete_preset import DeletePresetScreen
from .file_instance_edit import FileInstanceEditScreen
from .file_instances import FileInstancesScreen
from .overview import OverviewScreen
from .preset_details import PresetDetailsScreen
from .project_settings import ProjectSettingsScreen

__all__ = [
    "CreatePresetScreen",
    "ApplyPresetScreen",
    "DeletePresetScreen",
    "PresetDetailsScreen",
    "FileInstanceEditScreen",
    "OverviewScreen",
    "ProjectSettingsScreen",
    "CoreFilesScreen",
    "FileInstancesScreen",
]
