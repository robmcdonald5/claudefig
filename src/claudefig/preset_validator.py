"""Preset validation for claudefig."""

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from claudefig.models import FileType, ValidationResult


class PresetValidator:
    """Validates preset configuration files.

    Provides validation for individual preset files and batch validation
    for entire directories of presets.
    """

    def __init__(self, global_presets_dir: Path):
        """Initialize preset validator.

        Args:
            global_presets_dir: Path to global presets directory
        """
        self.global_presets_dir = global_presets_dir

    def validate_preset_config(self, preset_path: Path) -> ValidationResult:
        """Validate a preset configuration file.

        Args:
            preset_path: Path to preset .toml file

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(valid=True)

        if not preset_path.exists():
            result.add_error(f"Preset file not found: {preset_path}")
            return result

        try:
            with open(preset_path, "rb") as f:
                data = tomllib.load(f)

            # Check required top-level keys
            if "claudefig" not in data:
                result.add_error("Missing required section: [claudefig]")

            if "files" not in data:
                result.add_error("Missing required section: [[files]]")

            # Validate claudefig section
            if "claudefig" in data:
                claudefig = data["claudefig"]
                if "version" not in claudefig:
                    result.add_warning("Missing 'version' in [claudefig] section")
                if "schema_version" not in claudefig:
                    result.add_warning(
                        "Missing 'schema_version' in [claudefig] section"
                    )

            # Validate files section
            if "files" in data:
                files = data["files"]
                if not isinstance(files, list):
                    result.add_error("'files' must be an array of file instances")
                else:
                    for idx, file_inst in enumerate(files):
                        # Check required fields
                        required_fields = ["id", "type", "preset", "path"]
                        for field in required_fields:
                            if field not in file_inst:
                                result.add_error(
                                    f"File instance {idx}: missing required field '{field}'"
                                )

                        # Validate file type
                        if "type" in file_inst:
                            try:
                                FileType(file_inst["type"])
                            except ValueError:
                                result.add_error(
                                    f"File instance {idx}: invalid file type '{file_inst.get('type')}'"
                                )

                        # Check for duplicate IDs
                        ids_seen = set()
                        inst_id = file_inst.get("id")
                        if inst_id:
                            if inst_id in ids_seen:
                                result.add_error(
                                    f"File instance {idx}: duplicate ID '{inst_id}'"
                                )
                            ids_seen.add(inst_id)

        except tomllib.TOMLDecodeError as e:
            result.add_error(f"Invalid TOML syntax: {e}")
        except Exception as e:
            result.add_error(f"Validation error: {e}")

        return result

    def validate_all_presets(self) -> dict[str, ValidationResult]:
        """Validate all global presets.

        Returns:
            Dictionary mapping preset names to validation results
        """
        results: dict[str, ValidationResult] = {}
        if not self.global_presets_dir.exists():
            return results

        # Look for directory-based presets with claudefig.toml files inside
        for preset_dir in self.global_presets_dir.iterdir():
            if not preset_dir.is_dir():
                continue

            preset_file = preset_dir / "claudefig.toml"
            if not preset_file.exists():
                continue

            preset_name = preset_dir.name
            results[preset_name] = self.validate_preset_config(preset_file)

        return results

    def get_validation_summary(self) -> dict:
        """Get a summary of preset validation status.

        Returns:
            Dictionary with validation summary stats
        """
        validation_results = self.validate_all_presets()

        summary = {
            "total": len(validation_results),
            "valid": sum(1 for r in validation_results.values() if r.valid),
            "invalid": sum(1 for r in validation_results.values() if not r.valid),
            "warnings": sum(
                1 for r in validation_results.values() if r.has_warnings and r.valid
            ),
            "results": validation_results,
        }

        return summary
