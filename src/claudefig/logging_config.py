"""Logging configuration for claudefig.

Provides centralized logging setup with file output to ~/.claudefig/logs/
and console output with configurable verbosity levels.
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from claudefig.utils.platform import is_windows, secure_mkdir

# Default log directory
DEFAULT_LOG_DIR = Path.home() / ".claudefig" / "logs"

# Log format strings
CONSOLE_FORMAT = "%(message)s"
FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log file settings
DEFAULT_LOG_FILE = "claudefig.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Keep 5 backup log files


class ClaudefigLogger:
    """Centralized logger for claudefig with file and console handlers."""

    _instance: Optional["ClaudefigLogger"] = None
    _initialized: bool = False

    def __new__(cls) -> "ClaudefigLogger":
        """Singleton pattern to ensure only one logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the logger (only once)."""
        if self._initialized:
            return

        self.log_dir = DEFAULT_LOG_DIR
        self.logger = logging.getLogger("claudefig")
        self.logger.setLevel(logging.DEBUG)  # Capture all levels
        self.logger.propagate = False  # Don't propagate to root logger

        # Track handlers to avoid duplicates
        self._file_handler: RotatingFileHandler | None = None
        self._console_handler: logging.StreamHandler | None = None

        self._initialized = True

    def setup(
        self,
        log_dir: Path | None = None,
        console_level: int = logging.WARNING,
        file_level: int = logging.INFO,
        enable_file_logging: bool = True,
    ) -> None:
        """Setup logging handlers.

        Args:
            log_dir: Directory for log files (default: ~/.claudefig/logs/)
            console_level: Log level for console output (default: WARNING)
            file_level: Log level for file output (default: INFO)
            enable_file_logging: Whether to enable file logging (default: True)
        """
        # Set log directory
        if log_dir:
            self.log_dir = log_dir

        # Remove existing handlers
        self.logger.handlers.clear()
        self._file_handler = None
        self._console_handler = None

        # Setup file handler
        if enable_file_logging:
            self._setup_file_handler(file_level)

        # Setup console handler
        self._setup_console_handler(console_level)

    def _setup_file_handler(self, level: int) -> None:
        """Setup rotating file handler.

        Args:
            level: Log level for file output
        """
        try:
            # Ensure log directory exists with secure permissions (0o700 on Unix)
            secure_mkdir(self.log_dir)

            # Create rotating file handler
            log_file = self.log_dir / DEFAULT_LOG_FILE
            self._file_handler = RotatingFileHandler(
                log_file,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
            self._file_handler.setLevel(level)

            # Set restrictive log file permissions on Unix (0o600)
            if not is_windows() and log_file.exists():
                import contextlib

                with contextlib.suppress(OSError):
                    log_file.chmod(0o600)

            # Set formatter
            formatter = logging.Formatter(FILE_FORMAT, datefmt=FILE_DATE_FORMAT)
            self._file_handler.setFormatter(formatter)

            # Add to logger
            self.logger.addHandler(self._file_handler)

            # Log setup success
            self.logger.info(
                f"Logging initialized - File: {log_file} (level: {logging.getLevelName(level)})"
            )

        except (OSError, PermissionError) as e:
            # If we can't create log file, just use console
            print(f"Warning: Could not setup file logging: {e}", file=sys.stderr)

    def _setup_console_handler(self, level: int) -> None:
        """Setup console handler.

        Args:
            level: Log level for console output
        """
        self._console_handler = logging.StreamHandler(sys.stderr)
        self._console_handler.setLevel(level)

        # Use simple format for console (no timestamps)
        formatter = logging.Formatter(CONSOLE_FORMAT)
        self._console_handler.setFormatter(formatter)

        # Add to logger
        self.logger.addHandler(self._console_handler)

    def set_console_level(self, level: int) -> None:
        """Change console logging level.

        Args:
            level: New log level (e.g., logging.DEBUG, logging.INFO)
        """
        if self._console_handler:
            self._console_handler.setLevel(level)

    def set_file_level(self, level: int) -> None:
        """Change file logging level.

        Args:
            level: New log level (e.g., logging.DEBUG, logging.INFO)
        """
        if self._file_handler:
            self._file_handler.setLevel(level)

    def get_logger(self, name: str | None = None) -> logging.Logger:
        """Get a logger instance.

        Args:
            name: Optional logger name (will be prefixed with 'claudefig.')

        Returns:
            Logger instance
        """
        if name:
            return logging.getLogger(f"claudefig.{name}")
        return self.logger

    def disable_file_logging(self) -> None:
        """Disable file logging (remove file handler)."""
        if self._file_handler:
            self.logger.removeHandler(self._file_handler)
            self._file_handler = None

    def enable_file_logging(self, level: int = logging.INFO) -> None:
        """Enable file logging.

        Args:
            level: Log level for file output (default: INFO)
        """
        if not self._file_handler:
            self._setup_file_handler(level)

    def get_log_files(self) -> list[Path]:
        """Get list of log files in the log directory.

        Returns:
            List of log file paths, sorted by modification time (newest first)
        """
        if not self.log_dir.exists():
            return []

        log_files = list(self.log_dir.glob("*.log*"))
        # Sort by modification time, newest first
        log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return log_files

    def clear_old_logs(self, days: int = 30) -> int:
        """Clear log files older than specified days.

        Args:
            days: Number of days to keep (default: 30)

        Returns:
            Number of log files deleted
        """
        if not self.log_dir.exists():
            return 0

        now = datetime.now()
        deleted_count = 0

        for log_file in self.log_dir.glob("*.log*"):
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                age_days = (now - mtime).days

                if age_days > days:
                    log_file.unlink()
                    deleted_count += 1
                    self.logger.debug(
                        f"Deleted old log file: {log_file.name} (age: {age_days} days)"
                    )

            except (OSError, PermissionError) as e:
                self.logger.warning(f"Failed to delete log file {log_file}: {e}")

        if deleted_count > 0:
            self.logger.info(f"Cleared {deleted_count} old log file(s)")

        return deleted_count


# Global logger instance
_logger_instance: ClaudefigLogger | None = None


def setup_logging(
    log_dir: Path | None = None,
    console_level: int = logging.WARNING,
    file_level: int = logging.INFO,
    enable_file_logging: bool = True,
) -> ClaudefigLogger:
    """Setup claudefig logging.

    Args:
        log_dir: Directory for log files (default: ~/.claudefig/logs/)
        console_level: Log level for console output (default: WARNING)
        file_level: Log level for file output (default: INFO)
        enable_file_logging: Whether to enable file logging (default: True)

    Returns:
        ClaudefigLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ClaudefigLogger()

    _logger_instance.setup(
        log_dir=log_dir,
        console_level=console_level,
        file_level=file_level,
        enable_file_logging=enable_file_logging,
    )

    return _logger_instance


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance.

    Automatically sets up logging if not already initialized.

    Args:
        name: Optional logger name (will be prefixed with 'claudefig.')

    Returns:
        Logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ClaudefigLogger()
        # Use default setup with file logging disabled initially
        # (will be enabled when CLI/TUI starts)
        _logger_instance.setup(enable_file_logging=False)

    return _logger_instance.get_logger(name)


def set_verbose(verbose: bool = True) -> None:
    """Set verbose mode (console logging to DEBUG level).

    Args:
        verbose: Whether to enable verbose mode
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ClaudefigLogger()
        _logger_instance.setup()

    level = logging.DEBUG if verbose else logging.WARNING
    _logger_instance.set_console_level(level)


def set_quiet(quiet: bool = True) -> None:
    """Set quiet mode (console logging to ERROR level only).

    Args:
        quiet: Whether to enable quiet mode
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ClaudefigLogger()
        _logger_instance.setup()

    level = logging.ERROR if quiet else logging.WARNING
    _logger_instance.set_console_level(level)
