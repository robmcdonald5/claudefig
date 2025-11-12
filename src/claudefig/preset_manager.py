"""Preset management for claudefig.

This module provides a simplified PresetManager facade that delegates to:
- TomlPresetRepository for data access
- preset_service for business logic

This is a thin coordinator layer for backward compatibility.
"""

from pathlib import Path
from typing import Any

from claudefig.models import FileType, Preset, PresetSource, ValidationResult
from claudefig.repositories import TomlPresetRepository
from claudefig.services import preset_service


class PresetManager:
    """Manages presets for file generation (facade over repository/service layers).

    Presets can come from three sources:
    1. Built-in: Shipped with claudefig package
    2. User: Stored in ~/.claudefig/presets/
    3. Project: Stored in .claudefig/presets/ (gitignored)

    This class is a thin facade that delegates to:
    - TomlPresetRepository for data storage/loading
    - preset_service for business logic
    """

    def __init__(
        self,
        user_presets_dir: Path | None = None,
        project_presets_dir: Path | None = None,
    ):
        """Initialize preset manager.

        Args:
            user_presets_dir: Path to user presets directory (default: ~/.claudefig/presets/)
            project_presets_dir: Path to project presets directory (default: .claudefig/presets/)
        """
        # Initialize repository with directory paths
        self._repo = TomlPresetRepository(
            user_presets_dir=user_presets_dir,
            project_presets_dir=project_presets_dir,
        )

        # Expose directory paths for backward compatibility
        self.user_presets_dir = self._repo.user_presets_dir
        self.project_presets_dir = self._repo.project_presets_dir

    @property
    def _preset_cache(self) -> dict[str, Preset]:
        """Access repository's internal cache (for backward compatibility with tests)."""
        return self._repo._preset_cache

    @property
    def _cache_loaded(self) -> bool:
        """Check if repository cache is loaded (for backward compatibility with tests)."""
        return self._repo._cache_loaded

    def list_presets(
        self,
        file_type: FileType | None = None,
        source: PresetSource | None = None,
    ) -> list[Preset]:
        """List available presets.

        Args:
            file_type: Optional file type filter
            source: Optional source filter

        Returns:
            List of available presets
        """
        # Delegate to service layer (which uses repository)
        return preset_service.list_presets(
            repo=self._repo,
            file_type=file_type.value if file_type else None,
            source=source,
        )

    def get_preset(self, preset_id: str) -> Preset | None:
        """Get a specific preset by ID.

        Args:
            preset_id: Preset ID in format "{file_type}:{preset_name}"

        Returns:
            Preset if found, None otherwise
        """
        # Delegate to service layer
        return preset_service.get_preset(repo=self._repo, preset_id=preset_id)

    def add_preset(
        self, preset: Preset, source: PresetSource = PresetSource.USER
    ) -> Preset:
        """Add a new preset.

        Args:
            preset: Preset to add
            source: Where to store the preset (USER or PROJECT)

        Returns:
            The created preset

        Raises:
            ValueError: If preset already exists or source is BUILT_IN
        """
        # Delegate to service layer
        return preset_service.create_preset(
            repo=self._repo, preset=preset, source=source
        )

    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset.

        Args:
            preset_id: ID of preset to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete a built-in preset
        """
        # Delegate to service layer (with backward-compatible return value)
        try:
            preset_service.delete_preset(repo=self._repo, preset_id=preset_id)
            return True
        except FileNotFoundError:
            return False

    def render_preset(
        self, preset: Preset, variables: dict[str, Any] | None = None
    ) -> str:
        """Render a preset with variables.

        Args:
            preset: Preset to render
            variables: Variables to use for rendering (overrides preset defaults)

        Returns:
            Rendered content

        Raises:
            FileNotFoundError: If preset template file not found
            IOError: If template cannot be read
        """
        # Delegate to service layer
        return preset_service.render_preset(
            repo=self._repo, preset=preset, variables=variables
        )

    def extract_template_variables(self, template_content: str) -> set[str]:
        """Extract variable placeholders from template content.

        Args:
            template_content: Template content to analyze

        Returns:
            Set of variable names found in the template
        """
        # Delegate to service layer
        return preset_service.extract_template_variables(template_content)

    def validate_template_variables(
        self, preset: Preset, variables: dict[str, Any] | None = None
    ) -> ValidationResult:
        """Validate template variables for a preset.

        Args:
            preset: Preset to validate
            variables: Variables that will be provided during rendering

        Returns:
            ValidationResult with any errors or warnings
        """
        # Delegate to service layer
        return preset_service.validate_preset_variables(
            repo=self._repo, preset=preset, variables=variables
        )

    def get_preset_by_name(
        self, file_type: FileType, preset_name: str
    ) -> Preset | None:
        """Get a preset by file type and preset name.

        Args:
            file_type: Type of file
            preset_name: Name of preset (without file_type prefix)

        Returns:
            Preset if found, None otherwise
        """
        preset_id = f"{file_type.value}:{preset_name}"
        return self.get_preset(preset_id)

    def clear_cache(self) -> None:
        """Clear the preset cache to force reload."""
        # Delegate to repository
        self._repo.clear_cache()

    def get_load_errors(self) -> list[str]:
        """Get any errors that occurred during preset loading.

        Returns:
            List of error messages from preset loading failures
        """
        # Delegate to repository
        return self._repo.get_load_errors()

    def check_circular_dependency(
        self, preset_id: str, visited: set[str] | None = None
    ) -> None:
        """Check for circular dependencies in preset inheritance chain.

        Args:
            preset_id: ID of preset to check
            visited: Set of already visited preset IDs (used for recursion)

        Raises:
            CircularDependencyError: If circular dependency is detected
        """
        # This method is preserved for backward compatibility
        # but circular dependency checking is now done in the repository layer
        # during preset loading
        if visited is None:
            visited = set()

        if preset_id in visited:
            # Circular dependency detected
            from claudefig.exceptions import CircularDependencyError

            cycle_path = list(visited) + [preset_id]
            raise CircularDependencyError(cycle_path)

        # Get the preset
        preset = self.get_preset(preset_id)
        if not preset or not preset.extends:
            # No inheritance or preset not found - no circular dependency
            return

        # Add current preset to visited set
        visited.add(preset_id)

        # Check the parent preset recursively
        self.check_circular_dependency(preset.extends, visited)

    def validate_preset_inheritance(self) -> list[str]:
        """Validate all preset inheritance chains for circular dependencies.

        Returns:
            List of error messages for any circular dependencies found
        """
        # Delegate to repository - this is already done during loading
        # This method is preserved for backward compatibility
        return self._repo.get_load_errors()

    def resolve_preset_variables(self, preset: Preset) -> dict[str, Any]:
        """Resolve preset variables including inherited values.

        Args:
            preset: Preset to resolve variables for

        Returns:
            Dictionary of resolved variables (parent + child, child overrides parent)

        Raises:
            CircularDependencyError: If circular dependency is detected
        """
        # Delegate to service layer
        return preset_service.resolve_preset_variables(repo=self._repo, preset=preset)
