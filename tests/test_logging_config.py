"""Tests for logging configuration."""

import logging
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from claudefig.logging_config import (
    BACKUP_COUNT,
    DEFAULT_LOG_DIR,
    MAX_LOG_SIZE,
    ClaudefigLogger,
    get_logger,
    set_quiet,
    set_verbose,
    setup_logging,
)


@pytest.fixture(autouse=True)
def reset_logger_singleton():
    """Reset the logger singleton between tests."""
    # Store original state
    original_instance = ClaudefigLogger._instance  # type: ignore[attr-defined]
    original_initialized = ClaudefigLogger._initialized  # type: ignore[attr-defined]

    # Reset for test
    ClaudefigLogger._instance = None  # type: ignore[attr-defined]
    ClaudefigLogger._initialized = False  # type: ignore[attr-defined]

    yield

    # Restore original state
    ClaudefigLogger._instance = original_instance  # type: ignore[attr-defined]
    ClaudefigLogger._initialized = original_initialized  # type: ignore[attr-defined]


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


class TestClaudefigLoggerSingleton:
    """Tests for ClaudefigLogger singleton pattern."""

    def test_singleton_returns_same_instance(self):
        """Test that multiple calls return the same instance."""
        logger1 = ClaudefigLogger()
        logger2 = ClaudefigLogger()

        assert logger1 is logger2

    def test_singleton_initialized_once(self):
        """Test that initialization only happens once."""
        logger1 = ClaudefigLogger()
        initial_log_dir = logger1.log_dir

        logger2 = ClaudefigLogger()

        # Should be same instance with same attributes
        assert logger2.log_dir == initial_log_dir

    def test_initialized_flag_set(self):
        """Test that _initialized flag is set after init."""
        logger = ClaudefigLogger()

        # Check instance attribute, not class attribute
        # (Python creates instance attribute in __init__)
        assert logger._initialized is True  # type: ignore[attr-defined]


class TestClaudefigLoggerInit:
    """Tests for ClaudefigLogger initialization."""

    def test_init_sets_default_log_dir(self):
        """Test that default log directory is set."""
        logger = ClaudefigLogger()

        assert logger.log_dir == DEFAULT_LOG_DIR

    def test_init_creates_logger(self):
        """Test that logger is created."""
        logger = ClaudefigLogger()

        assert logger.logger is not None
        assert logger.logger.name == "claudefig"

    def test_init_sets_logger_level_to_debug(self):
        """Test that logger captures all levels."""
        logger = ClaudefigLogger()

        assert logger.logger.level == logging.DEBUG

    def test_init_disables_propagation(self):
        """Test that logger doesn't propagate to root."""
        logger = ClaudefigLogger()

        assert logger.logger.propagate is False

    def test_init_handlers_none(self):
        """Test that handlers are initially None."""
        logger = ClaudefigLogger()

        assert logger._file_handler is None  # type: ignore[attr-defined]
        assert logger._console_handler is None  # type: ignore[attr-defined]


class TestClaudefigLoggerSetup:
    """Tests for setup method."""

    def test_setup_with_defaults(self, temp_log_dir):
        """Test setup with default parameters."""
        logger = ClaudefigLogger()
        logger.setup(log_dir=temp_log_dir)

        assert len(logger.logger.handlers) >= 1  # At least console handler
        assert temp_log_dir / "claudefig.log" in temp_log_dir.glob("*.log")

    def test_setup_custom_log_dir(self, tmp_path):
        """Test setup with custom log directory."""
        custom_dir = tmp_path / "custom_logs"

        logger = ClaudefigLogger()
        logger.setup(log_dir=custom_dir)

        assert logger.log_dir == custom_dir
        assert custom_dir.exists()

    def test_setup_custom_console_level(self, temp_log_dir):
        """Test setup with custom console log level."""
        logger = ClaudefigLogger()
        logger.setup(log_dir=temp_log_dir, console_level=logging.DEBUG)

        assert logger._console_handler.level == logging.DEBUG  # type: ignore[attr-defined]

    def test_setup_custom_file_level(self, temp_log_dir):
        """Test setup with custom file log level."""
        logger = ClaudefigLogger()
        logger.setup(log_dir=temp_log_dir, file_level=logging.DEBUG)

        assert logger._file_handler is not None  # type: ignore[attr-defined]
        assert logger._file_handler.level == logging.DEBUG  # type: ignore[attr-defined]

    def test_setup_disable_file_logging(self, temp_log_dir):
        """Test setup with file logging disabled."""
        logger = ClaudefigLogger()
        logger.setup(log_dir=temp_log_dir, enable_file_logging=False)

        assert logger._file_handler is None  # type: ignore[attr-defined]
        assert logger._console_handler is not None  # type: ignore[attr-defined]

    def test_setup_clears_existing_handlers(self, temp_log_dir):
        """Test that setup clears existing handlers."""
        logger = ClaudefigLogger()

        # First setup
        logger.setup(log_dir=temp_log_dir)
        handler_count_1 = len(logger.logger.handlers)

        # Second setup
        logger.setup(log_dir=temp_log_dir)
        handler_count_2 = len(logger.logger.handlers)

        # Should have same number of handlers, not double
        assert handler_count_1 == handler_count_2


class TestSetupFileHandler:
    """Tests for _setup_file_handler method."""

    def test_setup_file_handler_creates_directory(self, tmp_path):
        """Test that file handler creates log directory."""
        log_dir = tmp_path / "new_logs"

        logger = ClaudefigLogger()
        logger.log_dir = log_dir
        logger._setup_file_handler(logging.INFO)

        assert log_dir.exists()

    def test_setup_file_handler_creates_log_file(self, temp_log_dir):
        """Test that file handler creates log file."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger._setup_file_handler(logging.INFO)

        # File might not exist until first log message
        assert logger._file_handler is not None  # type: ignore[attr-defined]

    def test_setup_file_handler_rotating(self, temp_log_dir):
        """Test that file handler is RotatingFileHandler."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger._setup_file_handler(logging.INFO)

        from logging.handlers import RotatingFileHandler

        assert isinstance(logger._file_handler, RotatingFileHandler)  # type: ignore[attr-defined]

    def test_setup_file_handler_max_bytes(self, temp_log_dir):
        """Test that rotating handler has correct max bytes."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger._setup_file_handler(logging.INFO)

        assert logger._file_handler.maxBytes == MAX_LOG_SIZE  # type: ignore[attr-defined]

    def test_setup_file_handler_backup_count(self, temp_log_dir):
        """Test that rotating handler has correct backup count."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger._setup_file_handler(logging.INFO)

        assert logger._file_handler.backupCount == BACKUP_COUNT  # type: ignore[attr-defined]

    def test_setup_file_handler_permission_error(self, temp_log_dir):
        """Test handling permission error when creating log file."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir

        # Mock RotatingFileHandler to raise PermissionError
        with patch(
            "claudefig.logging_config.RotatingFileHandler",
            side_effect=PermissionError("No permission"),
        ):
            # Should not raise, just print warning
            logger._setup_file_handler(logging.INFO)

        # File handler should not be set
        assert logger._file_handler is None  # type: ignore[attr-defined]

    def test_setup_file_handler_adds_to_logger(self, temp_log_dir):
        """Test that file handler is added to logger."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger._setup_file_handler(logging.INFO)

        assert logger._file_handler in logger.logger.handlers  # type: ignore[attr-defined]


class TestSetupConsoleHandler:
    """Tests for _setup_console_handler method."""

    def test_setup_console_handler_creates_handler(self):
        """Test that console handler is created."""
        logger = ClaudefigLogger()
        logger._setup_console_handler(logging.WARNING)

        assert logger._console_handler is not None  # type: ignore[attr-defined]

    def test_setup_console_handler_uses_stderr(self):
        """Test that console handler outputs to stderr."""
        logger = ClaudefigLogger()
        logger._setup_console_handler(logging.WARNING)

        assert logger._console_handler.stream is sys.stderr  # type: ignore[attr-defined]

    def test_setup_console_handler_sets_level(self):
        """Test that console handler has correct level."""
        logger = ClaudefigLogger()
        logger._setup_console_handler(logging.ERROR)

        assert logger._console_handler.level == logging.ERROR  # type: ignore[attr-defined]

    def test_setup_console_handler_adds_to_logger(self):
        """Test that console handler is added to logger."""
        logger = ClaudefigLogger()
        logger._setup_console_handler(logging.WARNING)

        assert logger._console_handler in logger.logger.handlers  # type: ignore[attr-defined]


class TestSetConsoleLevel:
    """Tests for set_console_level method."""

    def test_set_console_level_changes_level(self, temp_log_dir):
        """Test changing console log level."""
        logger = ClaudefigLogger()
        logger.setup(log_dir=temp_log_dir)

        logger.set_console_level(logging.DEBUG)

        assert logger._console_handler.level == logging.DEBUG  # type: ignore[attr-defined]

    def test_set_console_level_no_handler(self):
        """Test setting level when no console handler exists."""
        logger = ClaudefigLogger()
        # No setup called, no handlers

        # Should not raise
        logger.set_console_level(logging.DEBUG)


class TestSetFileLevel:
    """Tests for set_file_level method."""

    def test_set_file_level_changes_level(self, temp_log_dir):
        """Test changing file log level."""
        logger = ClaudefigLogger()
        logger.setup(log_dir=temp_log_dir)

        logger.set_file_level(logging.DEBUG)

        assert logger._file_handler.level == logging.DEBUG  # type: ignore[attr-defined]

    def test_set_file_level_no_handler(self):
        """Test setting level when no file handler exists."""
        logger = ClaudefigLogger()
        logger.setup(enable_file_logging=False)

        # Should not raise
        logger.set_file_level(logging.DEBUG)


class TestGetLoggerMethod:
    """Tests for get_logger method."""

    def test_get_logger_root(self):
        """Test getting root claudefig logger."""
        logger = ClaudefigLogger()

        result = logger.get_logger()

        assert result.name == "claudefig"
        assert result is logger.logger

    def test_get_logger_named(self):
        """Test getting named logger."""
        logger = ClaudefigLogger()

        result = logger.get_logger("test_module")

        assert result.name == "claudefig.test_module"

    def test_get_logger_multiple_names(self):
        """Test getting multiple named loggers."""
        logger = ClaudefigLogger()

        result1 = logger.get_logger("module1")
        result2 = logger.get_logger("module2")

        assert result1.name == "claudefig.module1"
        assert result2.name == "claudefig.module2"
        assert result1 is not result2


class TestEnableDisableFileLogging:
    """Tests for enable_file_logging and disable_file_logging."""

    def test_disable_file_logging(self, temp_log_dir):
        """Test disabling file logging."""
        logger = ClaudefigLogger()
        logger.setup(log_dir=temp_log_dir)

        logger.disable_file_logging()

        assert logger._file_handler is None  # type: ignore[attr-defined]
        assert logger._file_handler not in logger.logger.handlers  # type: ignore[attr-defined]

    def test_enable_file_logging(self, temp_log_dir):
        """Test enabling file logging."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger.setup(enable_file_logging=False)

        logger.enable_file_logging()

        assert logger._file_handler is not None  # type: ignore[attr-defined]
        assert logger._file_handler in logger.logger.handlers  # type: ignore[attr-defined]

    def test_enable_file_logging_custom_level(self, temp_log_dir):
        """Test enabling file logging with custom level."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger.setup(enable_file_logging=False)

        logger.enable_file_logging(level=logging.DEBUG)

        assert logger._file_handler.level == logging.DEBUG  # type: ignore[attr-defined]

    def test_disable_when_already_disabled(self, temp_log_dir):
        """Test disabling file logging when already disabled."""
        logger = ClaudefigLogger()
        logger.setup(log_dir=temp_log_dir, enable_file_logging=False)

        # Should not raise
        logger.disable_file_logging()

    def test_enable_when_already_enabled(self, temp_log_dir):
        """Test enabling file logging when already enabled."""
        logger = ClaudefigLogger()
        logger.setup(log_dir=temp_log_dir)

        # Should not create duplicate handler
        logger.enable_file_logging()

        # Still only one file handler
        file_handlers = [h for h in logger.logger.handlers if h == logger._file_handler]  # type: ignore[attr-defined]
        assert len(file_handlers) == 1


class TestGetLogFiles:
    """Tests for get_log_files method."""

    def test_get_log_files_empty_directory(self, temp_log_dir):
        """Test getting log files from empty directory."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir

        result = logger.get_log_files()

        assert result == []

    def test_get_log_files_returns_list(self, temp_log_dir):
        """Test that get_log_files returns a list."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir

        # Create some log files
        (temp_log_dir / "test1.log").write_text("log1")
        (temp_log_dir / "test2.log").write_text("log2")

        result = logger.get_log_files()

        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_log_files_sorted_by_time(self, temp_log_dir):
        """Test that log files are sorted by modification time."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir

        # Create files with different times
        old_file = temp_log_dir / "old.log"
        old_file.write_text("old")

        new_file = temp_log_dir / "new.log"
        new_file.write_text("new")

        # Modify new_file to have newer timestamp
        import time

        time.sleep(0.01)
        new_file.touch()

        result = logger.get_log_files()

        # Newest should be first
        assert result[0].name == "new.log"
        assert result[1].name == "old.log"

    def test_get_log_files_nonexistent_directory(self, tmp_path):
        """Test getting log files when directory doesn't exist."""
        logger = ClaudefigLogger()
        logger.log_dir = tmp_path / "nonexistent"

        result = logger.get_log_files()

        assert result == []

    def test_get_log_files_includes_rotated(self, temp_log_dir):
        """Test that rotated log files are included."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir

        # Create main and rotated log files
        (temp_log_dir / "claudefig.log").write_text("current")
        (temp_log_dir / "claudefig.log.1").write_text("backup1")
        (temp_log_dir / "claudefig.log.2").write_text("backup2")

        result = logger.get_log_files()

        assert len(result) == 3


class TestClearOldLogs:
    """Tests for clear_old_logs method."""

    def test_clear_old_logs_deletes_old_files(self, temp_log_dir):
        """Test that old log files are deleted."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger.setup(log_dir=temp_log_dir)

        # Create old log file
        old_file = temp_log_dir / "old.log"
        old_file.write_text("old log")

        # Set modification time to 40 days ago
        old_time = (datetime.now() - timedelta(days=40)).timestamp()
        import os

        os.utime(old_file, (old_time, old_time))

        count = logger.clear_old_logs(days=30)

        assert count == 1
        assert not old_file.exists()

    def test_clear_old_logs_preserves_new_files(self, temp_log_dir):
        """Test that new log files are preserved."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger.setup(log_dir=temp_log_dir)

        # Create new log file
        new_file = temp_log_dir / "new.log"
        new_file.write_text("new log")

        count = logger.clear_old_logs(days=30)

        assert count == 0
        assert new_file.exists()

    def test_clear_old_logs_returns_count(self, temp_log_dir):
        """Test that clear_old_logs returns deleted count."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger.setup(log_dir=temp_log_dir)

        # Create multiple old files
        for i in range(3):
            old_file = temp_log_dir / f"old{i}.log"
            old_file.write_text(f"old log {i}")

            old_time = (datetime.now() - timedelta(days=40)).timestamp()
            import os

            os.utime(old_file, (old_time, old_time))

        count = logger.clear_old_logs(days=30)

        assert count == 3

    def test_clear_old_logs_nonexistent_directory(self, tmp_path):
        """Test clearing logs when directory doesn't exist."""
        logger = ClaudefigLogger()
        logger.log_dir = tmp_path / "nonexistent"

        count = logger.clear_old_logs(days=30)

        assert count == 0

    def test_clear_old_logs_custom_days(self, temp_log_dir):
        """Test clearing logs with custom days parameter."""
        logger = ClaudefigLogger()
        logger.log_dir = temp_log_dir
        logger.setup(log_dir=temp_log_dir)

        # Create file 10 days old
        old_file = temp_log_dir / "old.log"
        old_file.write_text("old")

        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        import os

        os.utime(old_file, (old_time, old_time))

        # Should delete with days=5, but not with days=15
        count1 = logger.clear_old_logs(days=15)
        assert count1 == 0
        assert old_file.exists()

        count2 = logger.clear_old_logs(days=5)
        assert count2 == 1
        assert not old_file.exists()


class TestSetupLoggingFunction:
    """Tests for setup_logging global function."""

    def test_setup_logging_returns_logger(self, temp_log_dir):
        """Test that setup_logging returns ClaudefigLogger."""
        result = setup_logging(log_dir=temp_log_dir)

        assert isinstance(result, ClaudefigLogger)

    def test_setup_logging_creates_instance(self):
        """Test that setup_logging creates global instance."""
        from claudefig import logging_config

        setup_logging(enable_file_logging=False)

        assert logging_config._logger_instance is not None  # type: ignore[attr-defined]

    def test_setup_logging_configures_logger(self, temp_log_dir):
        """Test that setup_logging configures the logger."""
        logger = setup_logging(
            log_dir=temp_log_dir,
            console_level=logging.DEBUG,
            file_level=logging.INFO,
        )

        assert logger._console_handler.level == logging.DEBUG  # type: ignore[attr-defined]


class TestGetLoggerFunction:
    """Tests for get_logger global function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        result = get_logger()

        assert isinstance(result, logging.Logger)

    def test_get_logger_auto_initializes(self):
        """Test that get_logger auto-initializes if needed."""
        from claudefig import logging_config

        logging_config._logger_instance = None  # type: ignore[attr-defined]

        result = get_logger()

        assert logging_config._logger_instance is not None  # type: ignore[attr-defined]
        assert isinstance(result, logging.Logger)

    def test_get_logger_named(self):
        """Test getting named logger."""
        result = get_logger("test_module")

        assert result.name == "claudefig.test_module"

    def test_get_logger_without_file_logging(self):
        """Test that get_logger disables file logging by default."""
        from claudefig import logging_config

        logging_config._logger_instance = None  # type: ignore[attr-defined]

        get_logger()

        assert logging_config._logger_instance._file_handler is None  # type: ignore[attr-defined]


class TestSetVerboseFunction:
    """Tests for set_verbose global function."""

    def test_set_verbose_enables_debug(self, temp_log_dir):
        """Test that verbose mode enables DEBUG level."""
        setup_logging(log_dir=temp_log_dir)

        set_verbose(True)

        from claudefig import logging_config

        assert logging_config._logger_instance._console_handler.level == logging.DEBUG  # type: ignore[attr-defined]

    def test_set_verbose_disables_debug(self, temp_log_dir):
        """Test that verbose=False sets WARNING level."""
        setup_logging(log_dir=temp_log_dir)

        set_verbose(False)

        from claudefig import logging_config

        assert logging_config._logger_instance._console_handler.level == logging.WARNING  # type: ignore[attr-defined]

    def test_set_verbose_auto_initializes(self):
        """Test that set_verbose auto-initializes if needed."""
        from claudefig import logging_config

        logging_config._logger_instance = None  # type: ignore[attr-defined]

        set_verbose(True)

        assert logging_config._logger_instance is not None  # type: ignore[attr-defined]


class TestSetQuietFunction:
    """Tests for set_quiet global function."""

    def test_set_quiet_enables_error_only(self, temp_log_dir):
        """Test that quiet mode enables ERROR level only."""
        setup_logging(log_dir=temp_log_dir)

        set_quiet(True)

        from claudefig import logging_config

        assert logging_config._logger_instance._console_handler.level == logging.ERROR  # type: ignore[attr-defined]

    def test_set_quiet_restores_warning(self, temp_log_dir):
        """Test that quiet=False restores WARNING level."""
        setup_logging(log_dir=temp_log_dir)

        set_quiet(False)

        from claudefig import logging_config

        assert logging_config._logger_instance._console_handler.level == logging.WARNING  # type: ignore[attr-defined]

    def test_set_quiet_auto_initializes(self):
        """Test that set_quiet auto-initializes if needed."""
        from claudefig import logging_config

        logging_config._logger_instance = None  # type: ignore[attr-defined]

        set_quiet(True)

        assert logging_config._logger_instance is not None  # type: ignore[attr-defined]
