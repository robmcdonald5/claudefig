"""Custom Click parameter types for CLI commands.

This module provides reusable Click ParamType implementations for
validating and converting CLI arguments.
"""

import click

from claudefig.models import FileType


class FileTypeParamType(click.ParamType):
    """Click parameter type for FileType enum validation.

    Converts string input to FileType enum with consistent error messages.

    Example:
        @click.argument("file_type", type=FILE_TYPE)
        def my_command(file_type: FileType):
            # file_type is already a FileType enum
            pass
    """

    name = "file_type"

    def convert(
        self,
        value: str | FileType,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> FileType:
        """Convert string value to FileType enum.

        Args:
            value: String value or FileType enum
            param: Click parameter (for error context)
            ctx: Click context

        Returns:
            FileType enum value

        Raises:
            click.BadParameter: If value is not a valid FileType
        """
        if isinstance(value, FileType):
            return value

        try:
            return FileType(value)
        except ValueError:
            valid_types = [ft.value for ft in FileType]
            self.fail(
                f"Invalid file type: '{value}'. Valid types: {', '.join(valid_types)}",
                param,
                ctx,
            )


# Singleton instance for convenience
FILE_TYPE = FileTypeParamType()
