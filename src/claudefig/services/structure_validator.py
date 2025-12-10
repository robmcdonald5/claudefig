"""Structure validation and auto-healing service for .claudefig directory.

This module provides validation and repair functionality for the user-level
.claudefig directory structure, ensuring all critical directories and preset
files exist and are intact.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from rich.console import Console

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

logger = logging.getLogger(__name__)
console = Console()


class StructureValidationResult:
    """Result of structure validation with repair actions taken."""

    def __init__(self):
        """Initialize validation result."""
        self.is_valid = True
        self.missing_dirs: list[Path] = []
        self.missing_files: list[Path] = []
        self.repaired_dirs: list[Path] = []
        self.repaired_files: list[Path] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    @property
    def needs_repair(self) -> bool:
        """Check if any repairs are needed."""
        return bool(self.missing_dirs or self.missing_files)

    @property
    def was_repaired(self) -> bool:
        """Check if any repairs were performed."""
        return bool(self.repaired_dirs or self.repaired_files)


def validate_user_directory(
    config_dir: Path, auto_heal: bool = True, verbose: bool = True
) -> StructureValidationResult:
    """Validate user-level .claudefig directory structure.

    Checks for all required directories and optionally repairs missing ones.

    Args:
        config_dir: Path to user config directory (.claudefig).
        auto_heal: If True, automatically create missing directories.
        verbose: If True, print progress messages.

    Returns:
        StructureValidationResult with validation status and repair actions.
    """
    result = StructureValidationResult()

    # Define required directory structure
    required_dirs = [
        "presets",
        "cache",
        "components",
        "components/claude_md",
        "components/gitignore",
        "components/commands",
        "components/agents",
        "components/hooks",
        "components/output_styles",
        "components/mcp",
        "components/plugins",
        "components/skills",
        "components/settings_json",
        "components/settings_local_json",
        "components/statusline",
    ]

    # Check main directory
    if not config_dir.exists():
        result.add_error(f"Config directory does not exist: {config_dir}")
        if auto_heal:
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
                result.repaired_dirs.append(config_dir)
                if verbose:
                    console.print(f"[green]+[/green] Created directory: {config_dir}")
            except Exception as e:
                result.add_error(f"Failed to create {config_dir}: {e}")
                return result

    # Check and repair required subdirectories
    for dir_name in required_dirs:
        dir_path = config_dir / dir_name
        if not dir_path.exists():
            result.missing_dirs.append(dir_path)
            if auto_heal:
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    result.repaired_dirs.append(dir_path)
                    if verbose:
                        console.print(f"[green]+[/green] Created directory: {dir_path}")
                except Exception as e:
                    result.add_error(f"Failed to create {dir_path}: {e}")

    # Check critical files
    config_file = config_dir / "config.toml"
    if not config_file.exists():
        result.missing_files.append(config_file)
        result.add_warning("User config file missing (will be created on next init)")

    return result


def validate_preset_integrity(
    preset_dir: Path, verbose: bool = False
) -> StructureValidationResult:
    """Validate that a preset directory has all expected component files.

    Checks if preset's claudefig.toml exists and all referenced components
    are present in the components/ directory.

    Args:
        preset_dir: Path to preset directory (e.g., ~/.claudefig/presets/default/).
        verbose: If True, print detailed validation info.

    Returns:
        StructureValidationResult with validation status.
    """
    result = StructureValidationResult()

    # Check preset directory exists
    if not preset_dir.exists():
        result.add_error(f"Preset directory does not exist: {preset_dir}")
        return result

    # Check for claudefig.toml
    toml_path = preset_dir / "claudefig.toml"
    if not toml_path.exists():
        result.add_error(f"Preset config not found: {toml_path}")
        return result

    # Load and validate components
    try:
        with open(toml_path, "rb") as f:
            preset_config = tomllib.load(f)

        # Check if components section exists
        components_config = preset_config.get("components", {})
        if not components_config:
            if verbose:
                console.print(
                    f"[yellow]Warning:[/yellow] No components defined in {toml_path}"
                )
            return result

        # Validate each component type
        components_dir = preset_dir / "components"
        if not components_dir.exists():
            result.add_error(f"Components directory missing: {components_dir}")
            return result

        # Handle both dictionary format and array format for components
        # Array format: [[components]] with type, name, path, enabled
        # Dict format: [components.type] with variants, required_files
        if isinstance(components_config, list):
            # Array format - validate each component entry
            for component in components_config:
                if not isinstance(component, dict):
                    continue
                comp_type = component.get("type")
                comp_name = component.get("name")
                if comp_type and comp_name:
                    variant_dir = components_dir / comp_type / comp_name
                    if not variant_dir.exists():
                        result.missing_dirs.append(variant_dir)
                        result.add_error(
                            f"Component variant missing: {comp_type}/{comp_name}"
                        )
            return result

        for component_type, config in components_config.items():
            if not isinstance(config, dict):
                continue

            variants = config.get("variants", [])
            required_files = config.get("required_files", [])

            # Check each variant
            for variant in variants:
                variant_dir = components_dir / component_type / variant
                if not variant_dir.exists():
                    result.missing_dirs.append(variant_dir)
                    result.add_error(
                        f"Component variant missing: {component_type}/{variant}"
                    )
                    continue

                # Check required files in variant
                for file_name in required_files:
                    file_path = variant_dir / file_name
                    if not file_path.exists():
                        result.missing_files.append(file_path)
                        result.add_error(
                            f"Component file missing: {component_type}/{variant}/{file_name}"
                        )

        if verbose and result.is_valid:
            total_components = sum(
                len(config.get("variants", []))
                for config in components_config.values()
                if isinstance(config, dict)
            )
            console.print(
                f"[green]✓[/green] Preset integrity validated ({total_components} components)"
            )

    except Exception as e:
        result.add_error(f"Failed to validate preset config: {e}")

    return result


def create_initialization_marker(config_dir: Path) -> bool:
    """Create a marker file to indicate successful initialization.

    Args:
        config_dir: Path to user config directory.

    Returns:
        True if marker created successfully, False otherwise.
    """
    marker_file = config_dir / ".initialized"
    try:
        marker_file.write_text(
            "This file indicates claudefig initialization completed successfully.\n"
            "Do not delete this file.\n",
            encoding="utf-8",
        )
        return True
    except Exception as e:
        logger.debug("Failed to write initialization marker %s: %s", marker_file, e)
        return False


def check_initialization_marker(config_dir: Path) -> bool:
    """Check if initialization marker exists.

    Args:
        config_dir: Path to user config directory.

    Returns:
        True if marker exists, False otherwise.
    """
    marker_file = config_dir / ".initialized"
    return marker_file.exists()
