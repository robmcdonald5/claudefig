"""Core data models for claudefig file instance and preset system."""

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore[assignment]


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
    PLUGINS = "plugins"
    SKILLS = "skills"

    @property
    def display_name(self) -> str:
        """Get human-readable display name for the file type."""
        display_names = {
            self.CLAUDE_MD: "CLAUDE.md",
            self.SETTINGS_JSON: "settings.json",
            self.SETTINGS_LOCAL_JSON: "settings.local.json",
            self.GITIGNORE: ".gitignore",
            self.COMMANDS: "Slash Commands",
            self.AGENTS: "Sub-Agents",
            self.HOOKS: "Hooks",
            self.OUTPUT_STYLES: "Output Styles",
            self.STATUSLINE: "Status Line",
            self.MCP: "MCP Servers",
            self.PLUGINS: "Plugins",
            self.SKILLS: "Skills",
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
            self.PLUGINS: ".claude/plugins/",
            self.SKILLS: ".claude/skills/",
        }
        return default_paths.get(self, "")

    @property
    def supports_multiple(self) -> bool:
        """Check if this file type supports multiple instances."""
        # Most types support multiple instances, except these:
        single_instance_types = {
            self.SETTINGS_JSON,  # Only one settings.json per project
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
            self.PLUGINS,
            self.SKILLS,
        }
        return self in directory_types

    @property
    def append_mode(self) -> bool:
        """Check if this file type should append to existing files."""
        # .gitignore should append, not replace
        return self == self.GITIGNORE

    @property
    def path_customizable(self) -> bool:
        """Check if path can be customized (vs fixed location/directory)."""
        # Only CLAUDE.md and .gitignore allow custom paths
        customizable_types = {
            self.CLAUDE_MD,
            self.GITIGNORE,
        }
        return self in customizable_types


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
    template_path: Path | None = (
        None  # Path to template file (for user/project presets)
    )
    variables: dict[str, Any] = field(
        default_factory=dict
    )  # Template variables with defaults
    extends: str | None = None  # ID of preset to extend/inherit from
    tags: list[str] = field(
        default_factory=list
    )  # Tags for discovery (e.g., ["backend", "python"])

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
            Dictionary representation of the preset (filters out None values for TOML compatibility)
        """
        result: dict[str, Any] = {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "variables": self.variables,
        }

        # Only include template_path if not None (TOML doesn't support None)
        if self.template_path:
            result["template_path"] = str(self.template_path)

        # Only include extends if not None
        if self.extends:
            result["extends"] = self.extends

        # Only include tags if not empty
        if self.tags:
            result["tags"] = self.tags

        return result

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
    variables: dict[str, Any] = field(default_factory=dict)  # Override preset variables

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

    def get_component_name(self) -> str:
        """Extract component name from instance variables or preset.

        Component name extraction follows this priority:
        1. Check 'component_name' in variables dict
        2. Extract from preset field (format: "type:component_name")
        3. Return empty string if not found

        Returns:
            Component name string, or empty string if not found

        Examples:
            >>> instance.variables = {"component_name": "my-component"}
            >>> instance.get_component_name()
            'my-component'

            >>> instance.preset = "claude_md:default"
            >>> instance.get_component_name()
            'default'
        """
        # Priority 1: Check component_name in variables
        component_name = str(self.variables.get("component_name", ""))
        if component_name:
            return component_name

        # Priority 2: Extract from preset field
        if ":" in self.preset:
            return self.preset.split(":")[-1]

        # Priority 3: No component name found
        return ""


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


# ============================================================================
# Preset Definition Models
# ============================================================================


@dataclass
class PresetDefinition:
    """Preset definition from claudefig.toml file.

    Represents a complete preset configuration including metadata
    and component references.
    """

    name: str
    version: str
    description: str
    components: list["ComponentReference"]

    @classmethod
    def from_toml(cls, path: Path) -> "PresetDefinition":
        """Load preset definition from claudefig.toml file.

        Args:
            path: Path to claudefig.toml file

        Returns:
            PresetDefinition instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If TOML is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Preset definition not found: {path}")

        data = tomllib.loads(path.read_text(encoding="utf-8"))

        preset_data = data.get("preset", {})
        components_data = data.get("components", [])

        components = [ComponentReference.from_dict(c) for c in components_data]

        return cls(
            name=preset_data.get("name", ""),
            version=preset_data.get("version", "1.0.0"),
            description=preset_data.get("description", ""),
            components=components,
        )

    def to_toml(self, path: Path) -> None:
        """Save preset definition to claudefig.toml file.

        Args:
            path: Path where to save the file

        Raises:
            ImportError: If tomli_w is not installed
        """
        if tomli_w is None:
            raise ImportError("tomli_w is required for writing TOML files")

        data = {
            "preset": {
                "name": self.name,
                "version": self.version,
                "description": self.description,
            },
            "components": [c.to_dict() for c in self.components],
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tomli_w.dumps(data), encoding="utf-8")


@dataclass
class ComponentReference:
    """Reference to a component within a preset.

    Defines which component to use and where to place it.
    """

    type: str  # FileType (claude_md, gitignore, etc.)
    name: str  # Component name (default, standard, etc.)
    path: str  # Target path in project
    enabled: bool = True
    variables: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentReference":
        """Create from dict (from TOML)."""
        return cls(
            type=data.get("type", ""),
            name=data.get("name", ""),
            path=data.get("path", ""),
            enabled=data.get("enabled", True),
            variables=data.get("variables", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict (for TOML)."""
        result = {
            "type": self.type,
            "name": self.name,
            "path": self.path,
            "enabled": self.enabled,
        }
        if self.variables:
            result["variables"] = self.variables
        return result


@dataclass
class DiscoveredComponent:
    """Represents a component discovered during repository scanning.

    Used by the component discovery service to identify Claude Code
    components in a repository before creating a preset.
    """

    name: str  # Component name (using naming strategy)
    type: FileType  # Component type enum
    path: Path  # Full absolute path to file/directory
    relative_path: Path  # Path relative to repo root
    parent_folder: str  # Parent directory name
    is_duplicate: bool = False  # True if duplicate name detected
    # Use list for mutability during discovery, but document that it should
    # not be modified after creation
    duplicate_paths: list[Path] = field(
        default_factory=list
    )  # Other files with same name

    def __post_init__(self) -> None:
        """Validate component data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Component name cannot be empty")

        if not self.path.is_absolute():
            raise ValueError(f"path must be absolute: {self.path}")

        if self.relative_path.is_absolute():
            raise ValueError(f"relative_path must be relative: {self.relative_path}")

    def __repr__(self) -> str:
        """String representation of discovered component."""
        dup_indicator = " (duplicate)" if self.is_duplicate else ""
        return (
            f"DiscoveredComponent(name={self.name}, "
            f"type={self.type.value}, "
            f"path={self.relative_path}{dup_indicator})"
        )


@dataclass
class ComponentDiscoveryResult:
    """Result of component discovery scan.

    Contains all discovered components plus metadata about the scan
    including performance metrics and warnings.
    """

    components: list[DiscoveredComponent]  # All discovered components
    total_found: int  # Total number of components found
    warnings: list[str] = field(default_factory=list)  # Duplicate warnings, etc.
    scan_time_ms: float = 0.0  # Performance tracking in milliseconds

    @property
    def has_warnings(self) -> bool:
        """Check if scan produced any warnings."""
        return len(self.warnings) > 0

    def get_components_by_type(self, file_type: FileType) -> list[DiscoveredComponent]:
        """Get all components of a specific type.

        Args:
            file_type: FileType to filter by

        Returns:
            List of discovered components matching the type
        """
        return [c for c in self.components if c.type == file_type]

    def __repr__(self) -> str:
        """String representation of discovery result."""
        return (
            f"ComponentDiscoveryResult(found={self.total_found}, "
            f"warnings={len(self.warnings)}, "
            f"time={self.scan_time_ms:.1f}ms)"
        )
