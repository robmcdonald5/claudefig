"""Component system for modular configuration generation."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class ComponentMetadata:
    """Metadata for a single component."""

    def __init__(self, component_dir: Path, metadata: Dict[str, Any]):
        """Initialize component metadata.

        Args:
            component_dir: Directory containing the component.
            metadata: Parsed component.toml data.
        """
        self.component_dir = component_dir
        self._metadata = metadata

        # Extract key fields
        component_info = metadata.get("component", {})
        self.name = component_info.get("name", component_dir.name)
        self.type = component_info.get("type", "unknown")
        self.version = component_info.get("version", "1.0.0")
        self.description = component_info.get("description", "")

        # Metadata
        meta = component_info.get("metadata", {})
        self.author = meta.get("author", "")
        self.license = meta.get("license", "")
        self.tags = meta.get("tags", [])

        # Dependencies
        deps = component_info.get("dependencies", {})
        self.requires = deps.get("requires", [])
        self.recommends = deps.get("recommends", [])
        self.conflicts = deps.get("conflicts", [])

        # Files this component contributes
        files = component_info.get("files", {})
        self.claude_md_files = files.get("claude_md", [])
        self.settings_files = files.get("settings", [])
        self.contributing_files = files.get("contributing", [])

        # Template variables
        self.variables = component_info.get("variables", {})

        # Insertion configuration
        insertion = component_info.get("insertion", {})
        self.section = insertion.get("section", self.name)
        self.priority = insertion.get("priority", 100)
        self.user_editable = insertion.get("user_editable", False)

    def get_file_paths(self, file_type: str = "claude_md") -> List[Path]:
        """Get full paths to component files.

        Args:
            file_type: Type of files to retrieve (claude_md, settings, contributing).

        Returns:
            List of Path objects to component content files.
        """
        if file_type == "claude_md":
            file_list = self.claude_md_files
        elif file_type == "settings":
            file_list = self.settings_files
        elif file_type == "contributing":
            file_list = self.contributing_files
        else:
            return []

        return [self.component_dir / filename for filename in file_list]

    def __repr__(self) -> str:
        """String representation of component metadata."""
        return f"ComponentMetadata(name={self.name}, type={self.type}, version={self.version})"


class ComponentLoader:
    """Loads and manages components."""

    def __init__(self, component_base_dir: Path):
        """Initialize component loader.

        Args:
            component_base_dir: Base directory containing components (e.g., ~/.claudefig/components/).
        """
        self.component_base_dir = component_base_dir

    def load_component(self, component_path: str) -> Optional[ComponentMetadata]:
        """Load a single component by path.

        Args:
            component_path: Relative path to component (e.g., "languages/python").

        Returns:
            ComponentMetadata if found and valid, None otherwise.
        """
        component_dir = self.component_base_dir / component_path

        if not component_dir.exists():
            return None

        metadata_file = component_dir / "component.toml"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "rb") as f:
                metadata = tomllib.load(f)
            return ComponentMetadata(component_dir, metadata)
        except Exception as e:
            print(f"Error loading component {component_path}: {e}")
            return None

    def list_components(self, category: Optional[str] = None) -> List[str]:
        """List all available components.

        Args:
            category: Optional category to filter by (general, languages, frameworks, etc.).

        Returns:
            List of component paths (e.g., ["languages/python", "frameworks/django"]).
        """
        if not self.component_base_dir.exists():
            return []

        components = []

        # If category specified, only search that subdirectory
        if category:
            search_dir = self.component_base_dir / category
            if not search_dir.exists():
                return []
            search_dirs = [search_dir]
            prefix = category
        else:
            # Search all category directories
            search_dirs = [
                d for d in self.component_base_dir.iterdir() if d.is_dir()
            ]
            prefix = ""

        for category_dir in search_dirs:
            # Each subdirectory is a component
            for component_dir in category_dir.iterdir():
                if component_dir.is_dir() and (component_dir / "component.toml").exists():
                    if prefix:
                        component_path = f"{prefix}/{component_dir.name}"
                    else:
                        component_path = f"{category_dir.name}/{component_dir.name}"
                    components.append(component_path)

        return sorted(components)

    def resolve_dependencies(
        self, component_paths: List[str]
    ) -> List[ComponentMetadata]:
        """Resolve component dependencies and return sorted list.

        Args:
            component_paths: List of component paths to load.

        Returns:
            List of ComponentMetadata objects sorted by priority.

        Raises:
            ValueError: If there are dependency conflicts.
        """
        resolved: List[ComponentMetadata] = []
        visited: set[str] = set()

        def resolve_recursive(path: str):
            if path in visited:
                return

            component = self.load_component(path)
            if not component:
                raise ValueError(f"Component not found: {path}")

            visited.add(path)

            # Resolve required dependencies first
            for dep in component.requires:
                resolve_recursive(dep)

            # Add recommended dependencies (optional)
            for rec in component.recommends:
                if rec not in visited:
                    try:
                        resolve_recursive(rec)
                    except ValueError:
                        # Recommended dependencies are optional
                        pass

            resolved.append(component)

        # Resolve all requested components
        for path in component_paths:
            resolve_recursive(path)

        # Check for conflicts
        for i, comp1 in enumerate(resolved):
            for comp2 in resolved[i + 1 :]:
                if comp2.name in comp1.conflicts:
                    raise ValueError(
                        f"Conflict: {comp1.name} conflicts with {comp2.name}"
                    )

        # Sort by priority (lower priority = inserted first)
        resolved.sort(key=lambda c: c.priority)

        return resolved

    def get_component_info(self, component_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a component.

        Args:
            component_path: Path to component (e.g., "languages/python").

        Returns:
            Dictionary with component information, or None if not found.
        """
        component = self.load_component(component_path)
        if not component:
            return None

        return {
            "name": component.name,
            "type": component.type,
            "version": component.version,
            "description": component.description,
            "author": component.author,
            "license": component.license,
            "tags": component.tags,
            "requires": component.requires,
            "recommends": component.recommends,
            "conflicts": component.conflicts,
            "files": {
                "claude_md": component.claude_md_files,
                "settings": component.settings_files,
                "contributing": component.contributing_files,
            },
            "variables": component.variables,
            "section": component.section,
            "priority": component.priority,
        }
