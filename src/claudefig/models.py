"""Core data models for claudefig file instance and preset system."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class FileType(Enum):
    """Supported file types for configuration generation."""

    CLAUDE_MD = "claude_md"
    SETTINGS_JSON = "settings_json"
    SETTINGS_LOCAL_JSON = "settings_local_json"
    GITIGNORE = "gitignore"
    COMMANDS = "commands"
    AGENTS = "agents"
    HOOKS = "hooks"
    OUTPUT_STYLES = "output_styles"
    STATUSLINE = "statusline"
    MCP = "mcp"

    @property
    def display_name(self) -> str:
        """Get human-readable display name for the file type."""
        display_names = {
            self.CLAUDE_MD: "CLAUDE.md",
            self.SETTINGS_JSON: "Settings (settings.json)",
            self.SETTINGS_LOCAL_JSON: "Local Settings (settings.local.json)",
            self.GITIGNORE: ".gitignore",
            self.COMMANDS: "Slash Commands",
            self.AGENTS: "Sub-Agents",
            self.HOOKS: "Hooks",
            self.OUTPUT_STYLES: "Output Styles",
            self.STATUSLINE: "Status Line",
            self.MCP: "MCP Servers",
        }
        return display_names.get(self, self.value)

    @property
    def default_path(self) -> str:
        """Get the default path for this file type."""
        default_paths = {
            self.CLAUDE_MD: "CLAUDE.md",
            self.SETTINGS_JSON: ".claude/settings.json",
            self.SETTINGS_LOCAL_JSON: ".claude/settings.local.json",
            self.GITIGNORE: ".gitignore",
            self.COMMANDS: ".claude/commands/",
            self.AGENTS: ".claude/agents/",
            self.HOOKS: ".claude/hooks/",
            self.OUTPUT_STYLES: ".claude/output-styles/",
            self.STATUSLINE: ".claude/statusline.sh",
            self.MCP: ".claude/mcp/",
        }
        return default_paths.get(self, "")

    @property
    def supports_multiple(self) -> bool:
        """Check if this file type supports multiple instances."""
        # Most types support multiple instances, except these:
        single_instance_types = {
            self.SETTINGS_LOCAL_JSON,  # Typically only one per project
            self.STATUSLINE,  # Only one statusline script
        }
        return self not in single_instance_types

    @property
    def is_directory(self) -> bool:
        """Check if this file type represents a directory."""
        directory_types = {
            self.COMMANDS,
            self.AGENTS,
            self.HOOKS,
            self.OUTPUT_STYLES,
            self.MCP,
        }
        return self in directory_types

    @property
    def append_mode(self) -> bool:
        """Check if this file type should append to existing files."""
        # .gitignore should append, not replace
        return self == self.GITIGNORE


class PresetSource(Enum):
    """Source of a preset."""

    BUILT_IN = "built-in"
    USER = "user"
    PROJECT = "project"


@dataclass
class Preset:
    """Represents a template preset for a file type.

    Presets define reusable templates/variants for different file types.
    For example: "default", "backend-focused", "minimal" for CLAUDE.md files.
    """

    id: str  # Unique identifier, format: "{file_type}:{name}"
    type: FileType  # What file type this preset is for
    name: str  # Display name (e.g., "Backend Focused")
    description: str  # Description of what this preset provides
    source: PresetSource  # Where this preset comes from
    template_path: Optional[Path] = None  # Path to template file (for user/project presets)
    variables: dict[str, Any] = field(
        default_factory=dict
    )  # Template variables with defaults
    extends: Optional[str] = None  # ID of preset to extend/inherit from
    tags: list[str] = field(default_factory=list)  # Tags for discovery (e.g., ["backend", "python"])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Preset":
        """Create a Preset from a dictionary.

        Args:
            data: Dictionary representation of a preset

        Returns:
            Preset instance
        """
        return cls(
            id=data["id"],
            type=FileType(data["type"]),
            name=data["name"],
            description=data.get("description", ""),
            source=PresetSource(data.get("source", "built-in")),
            template_path=Path(data["template_path"])
            if data.get("template_path")
            else None,
            variables=data.get("variables", {}),
            extends=data.get("extends"),
            tags=data.get("tags", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert preset to dictionary format.

        Returns:
            Dictionary representation of the preset
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "template_path": str(self.template_path) if self.template_path else None,
            "variables": self.variables,
            "extends": self.extends,
            "tags": self.tags,
        }

    def __repr__(self) -> str:
        """String representation of preset."""
        return f"Preset(id={self.id}, name={self.name}, source={self.source.value})"


@dataclass
class FileInstance:
    """Represents a file instance to be generated.

    A file instance is a specific file that will be created during initialization,
    combining a file type, preset, and target path.
    """

    id: str  # Unique identifier for this instance
    type: FileType  # What type of file this is
    preset: str  # ID of preset to use (format: "{file_type}:{preset_name}")
    path: str  # Relative path where file should be generated
    enabled: bool = True  # Whether this instance is active
    variables: dict[str, Any] = field(
        default_factory=dict
    )  # Override preset variables

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileInstance":
        """Create a FileInstance from a dictionary.

        Args:
            data: Dictionary representation of a file instance

        Returns:
            FileInstance instance
        """
        return cls(
            id=data["id"],
            type=FileType(data["type"]),
            preset=data["preset"],
            path=data["path"],
            enabled=data.get("enabled", True),
            variables=data.get("variables", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert file instance to dictionary format.

        Returns:
            Dictionary representation of the file instance
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "preset": self.preset,
            "path": self.path,
            "enabled": self.enabled,
            "variables": self.variables,
        }

    @classmethod
    def create_default(
        cls, file_type: FileType, preset_name: str = "default"
    ) -> "FileInstance":
        """Create a file instance with default settings.

        Args:
            file_type: Type of file to create
            preset_name: Name of preset to use (default: "default")

        Returns:
            FileInstance with default path and settings
        """
        instance_id = f"{file_type.value}-{preset_name}"
        preset_id = f"{file_type.value}:{preset_name}"

        return cls(
            id=instance_id,
            type=file_type,
            preset=preset_id,
            path=file_type.default_path,
            enabled=True,
            variables={},
        )

    def __repr__(self) -> str:
        """String representation of file instance."""
        status = "enabled" if self.enabled else "disabled"
        return f"FileInstance(id={self.id}, type={self.type.value}, path={self.path}, {status})"


@dataclass
class ValidationResult:
    """Result of validating a file instance."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if validation has any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has any warnings."""
        return len(self.warnings) > 0

    def add_error(self, message: str) -> None:
        """Add an error message.

        Args:
            message: Error message to add
        """
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message.

        Args:
            message: Warning message to add
        """
        self.warnings.append(message)

    def __repr__(self) -> str:
        """String representation of validation result."""
        if self.valid:
            return "ValidationResult(valid=True)"
        return f"ValidationResult(valid=False, errors={len(self.errors)}, warnings={len(self.warnings)})"
