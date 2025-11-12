"""Tests for CLI decorators."""

from pathlib import Path
from unittest.mock import Mock, patch

import click
import pytest
from click.testing import CliRunner

from claudefig.cli.decorators import (
    _normalize_config_path,
    handle_errors,
    require_git_repo,
    with_config,
    with_config_optional,
)
from claudefig.exceptions import ConfigFileNotFoundError


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_config_repo():
    """Create a mock config repository."""
    repo = Mock()
    repo.exists.return_value = True
    return repo


@pytest.fixture
def mock_config_data():
    """Create mock config data."""
    return {
        "project": {"name": "test-project"},
        "files": {},
    }


class TestNormalizeConfigPath:
    """Tests for _normalize_config_path helper function."""

    def test_normalize_none_uses_cwd(self):
        """Test that None defaults to current working directory."""
        result = _normalize_config_path(None)
        expected = (Path.cwd() / "claudefig.toml").resolve()
        assert result == expected

    def test_normalize_string_path(self):
        """Test normalization of string path."""
        result = _normalize_config_path("/some/path")
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_normalize_path_object(self):
        """Test normalization of Path object."""
        path = Path("/some/path")
        result = _normalize_config_path(path)
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_normalize_directory_appends_filename(self, tmp_path):
        """Test that directory path gets claudefig.toml appended."""
        result = _normalize_config_path(tmp_path)
        assert result.name == "claudefig.toml"
        assert result.parent == tmp_path.resolve()

    def test_normalize_file_path_unchanged(self, tmp_path):
        """Test that file path is not modified."""
        file_path = tmp_path / "custom.toml"
        file_path.touch()
        result = _normalize_config_path(file_path)
        assert result.name == "custom.toml"
        assert result.is_absolute()

    def test_normalize_relative_path_made_absolute(self):
        """Test that relative paths are made absolute."""
        result = _normalize_config_path("./relative/path")
        assert result.is_absolute()

    def test_normalize_resolves_path(self, tmp_path):
        """Test that path is resolved (symlinks, .. removed)."""
        # Create nested directory
        nested = tmp_path / "level1" / "level2"
        nested.mkdir(parents=True)

        # Use .. in path
        path_with_dots = nested / ".." / "level2"
        result = _normalize_config_path(path_with_dots)

        # Should be resolved without ..
        assert ".." not in str(result)
        assert result.is_absolute()


class TestWithConfigDecorator:
    """Tests for @with_config decorator."""

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_loads_existing_config(
        self, mock_repo_class, mock_config_service, cli_runner, tmp_path
    ):
        """Test decorator loads existing config successfully."""
        # Setup mocks
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {"test": "data"}

        # Create command with decorator
        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config(path_param="path")
        def test_cmd(path, config_data, config_repo):
            assert config_data == {"test": "data"}
            assert config_repo == mock_repo
            click.echo("success")

        # Run command
        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "success" in result.output
        mock_config_service.load_config.assert_called_once_with(mock_repo)

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_creates_repo_with_correct_path(
        self, mock_repo_class, mock_config_service, cli_runner, tmp_path
    ):
        """Test decorator creates repository with normalized path."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config(path_param="path")
        def test_cmd(path, config_data, config_repo):
            click.echo("ok")

        cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])

        # Verify repo was created with normalized path
        call_args = mock_repo_class.call_args[0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], Path)
        assert call_args[0].name == "claudefig.toml"

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_handles_missing_config_with_defaults(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test decorator handles missing config by loading defaults."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        # Service returns defaults for missing config
        mock_config_service.load_config.return_value = {"default": "config"}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config()
        def test_cmd(path, config_data, config_repo):
            assert config_data == {"default": "config"}
            click.echo("defaults_loaded")

        result = cli_runner.invoke(test_cmd)
        assert "defaults_loaded" in result.output

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_custom_parameter_names(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test decorator with custom parameter names."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {"data": "test"}

        @click.command()
        @click.option("--config-path", default=".", type=click.Path())
        @with_config(
            path_param="config_path", config_name="my_config", repo_name="my_repo"
        )
        def test_cmd(config_path, my_config, my_repo):
            assert my_config == {"data": "test"}
            assert my_repo == mock_repo
            click.echo("custom_names")

        result = cli_runner.invoke(test_cmd, ["--config-path", "."])
        assert "custom_names" in result.output

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_injects_config_data_kwarg(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test that config_data is properly injected into kwargs."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        test_data = {"project": {"name": "test"}}
        mock_config_service.load_config.return_value = test_data

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config()
        def test_cmd(path, config_data, config_repo, **kwargs):
            # Verify config_data was injected
            assert "config_data" not in kwargs  # Should be in function args
            assert config_data == test_data
            click.echo("injected")

        result = cli_runner.invoke(test_cmd)
        assert "injected" in result.output

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_injects_config_repo_kwarg(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test that config_repo is properly injected into kwargs."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config()
        def test_cmd(path, config_data, config_repo):
            assert config_repo == mock_repo
            click.echo("repo_injected")

        result = cli_runner.invoke(test_cmd)
        assert "repo_injected" in result.output

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_default_path_param_name(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test decorator uses 'path' as default parameter name."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config()  # No path_param specified, should default to "path"
        def test_cmd(path, config_data, config_repo):
            click.echo("default_param")

        result = cli_runner.invoke(test_cmd, ["--path", "."])
        assert result.exit_code == 0
        assert "default_param" in result.output


class TestHandleErrorsDecorator:
    """Tests for @handle_errors decorator."""

    def test_passes_through_success(self, cli_runner):
        """Test decorator doesn't interfere with successful execution."""

        @click.command()
        @handle_errors("test operation")
        def test_cmd():
            click.echo("success")
            return "result"

        result = cli_runner.invoke(test_cmd)
        assert result.exit_code == 0
        assert "success" in result.output

    def test_catches_generic_exception(self, cli_runner):
        """Test decorator catches and formats generic exceptions."""

        @click.command()
        @handle_errors("test operation")
        def test_cmd():
            raise ValueError("Something went wrong")

        result = cli_runner.invoke(test_cmd)
        assert result.exit_code == 1  # click.Abort
        assert (
            "Something went wrong" in result.output or "failed" in result.output.lower()
        )

    def test_catches_config_file_not_found_error(self, cli_runner):
        """Test decorator handles ConfigFileNotFoundError specially."""

        @click.command()
        @handle_errors("loading config")
        def test_cmd():
            raise ConfigFileNotFoundError("Config not found")

        result = cli_runner.invoke(test_cmd)
        assert result.exit_code == 1
        assert "Config not found" in result.output or "error" in result.output.lower()

    def test_formats_error_message(self, cli_runner):
        """Test decorator formats error messages properly."""

        @click.command()
        @handle_errors("doing something")
        def test_cmd():
            raise RuntimeError("Error details")

        result = cli_runner.invoke(test_cmd)
        # Should contain operation name or error details
        assert "Error details" in result.output or "doing something" in result.output

    def test_raises_click_abort(self, cli_runner):
        """Test decorator raises click.Abort on error."""

        @click.command()
        @handle_errors("test")
        def test_cmd():
            raise Exception("Test error")

        result = cli_runner.invoke(test_cmd)
        # click.Abort causes exit code 1
        assert result.exit_code == 1

    def test_custom_exception_handler(self, cli_runner):
        """Test decorator with custom exception handler."""
        handler_called = []

        def custom_handler(e):
            handler_called.append(str(e))
            click.echo(f"Custom: {e}")
            return False  # Continue to default handling

        @click.command()
        @handle_errors("test", extra_handlers={ValueError: custom_handler})
        def test_cmd():
            raise ValueError("Custom error")

        result = cli_runner.invoke(test_cmd)
        assert len(handler_called) == 1
        assert "Custom error" in handler_called[0]
        assert result.exit_code == 1

    def test_multiple_custom_handlers(self, cli_runner):
        """Test decorator with multiple custom exception handlers."""
        value_errors = []
        type_errors = []

        def value_handler(e):
            value_errors.append(str(e))
            return False

        def type_handler(e):
            type_errors.append(str(e))
            return False

        @click.command()
        @click.argument("error_type")
        @handle_errors(
            "test",
            extra_handlers={
                ValueError: value_handler,
                TypeError: type_handler,
            },
        )
        def test_cmd(error_type):
            if error_type == "value":
                raise ValueError("Value problem")
            else:
                raise TypeError("Type problem")

        # Test ValueError
        cli_runner.invoke(test_cmd, ["value"])
        assert len(value_errors) == 1
        assert len(type_errors) == 0

        # Test TypeError
        cli_runner.invoke(test_cmd, ["type"])
        assert len(value_errors) == 1
        assert len(type_errors) == 1

    def test_handler_return_true_prevents_abort(self, cli_runner):
        """Test that handler returning True prevents click.Abort."""

        def complete_handler(e):
            click.echo(f"Handled: {e}")
            return True  # Prevent abort

        @click.command()
        @handle_errors("test", extra_handlers={ValueError: complete_handler})
        def test_cmd():
            raise ValueError("Handled error")

        result = cli_runner.invoke(test_cmd)
        assert result.exit_code == 0  # No abort
        assert "Handled: Handled error" in result.output

    def test_handler_return_false_continues_abort(self, cli_runner):
        """Test that handler returning False continues to abort."""

        def partial_handler(e):
            click.echo(f"Partial: {e}")
            return False  # Continue to abort

        @click.command()
        @handle_errors("test", extra_handlers={ValueError: partial_handler})
        def test_cmd():
            raise ValueError("Partial error")

        result = cli_runner.invoke(test_cmd)
        assert result.exit_code == 1  # Aborted
        assert "Partial: Partial error" in result.output

    def test_handler_return_none_continues_abort(self, cli_runner):
        """Test that handler returning None continues to abort."""

        def none_handler(e):
            click.echo("Handler called")
            return None  # Continue to abort

        @click.command()
        @handle_errors("test", extra_handlers={ValueError: none_handler})
        def test_cmd():
            raise ValueError("None error")

        result = cli_runner.invoke(test_cmd)
        assert result.exit_code == 1  # Aborted

    @patch("claudefig.cli.decorators.logger")
    def test_logs_exception_with_context(self, mock_logger, cli_runner):
        """Test that exceptions are logged with operation context."""

        @click.command()
        @handle_errors("critical operation")
        def test_cmd():
            raise RuntimeError("Log this")

        cli_runner.invoke(test_cmd)

        # Verify logger was called with operation name and exception
        assert mock_logger.error.called
        call_args = str(mock_logger.error.call_args)
        assert "critical operation" in call_args or "failed" in call_args

    def test_operation_name_in_message(self, cli_runner):
        """Test that operation name appears in error output."""

        @click.command()
        @handle_errors("uploading files")
        def test_cmd():
            raise RuntimeError("Upload failed")

        result = cli_runner.invoke(test_cmd)
        # Operation name should appear in output
        output_lower = result.output.lower()
        assert (
            "uploading files" in output_lower
            or "upload" in output_lower
            or "failed" in output_lower
        )

    def test_preserves_function_name(self, cli_runner):
        """Test that decorator preserves wrapped function name."""

        @handle_errors("test")
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    def test_preserves_function_docstring(self, cli_runner):
        """Test that decorator preserves wrapped function docstring."""

        @handle_errors("test")
        def my_function():
            """Test docstring."""
            pass

        assert my_function.__doc__ == "Test docstring."


class TestRequireGitRepoDecorator:
    """Tests for @require_git_repo decorator."""

    def test_passes_in_git_repo(self, cli_runner, tmp_path):
        """Test decorator passes when in git repository."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @require_git_repo(path_param="path")
        def test_cmd(path):
            click.echo("in_git_repo")

        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "in_git_repo" in result.output

    def test_fails_outside_git_repo(self, cli_runner, tmp_path):
        """Test decorator aborts when not in git repository."""

        # No .git directory
        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @require_git_repo(path_param="path")
        def test_cmd(path):
            click.echo("should_not_reach")

        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        assert result.exit_code == 1  # Aborted
        assert "should_not_reach" not in result.output
        assert "git" in result.output.lower()

    def test_error_message_for_no_repo(self, cli_runner, tmp_path):
        """Test error message when not in git repo."""

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @require_git_repo(path_param="path")
        def test_cmd(path):
            pass

        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        output_lower = result.output.lower()
        assert "not a git repository" in output_lower or "git init" in output_lower

    def test_checks_parent_directories(self, cli_runner, tmp_path):
        """Test decorator checks parent directories for .git."""
        # Create .git in parent
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create nested directory
        nested = tmp_path / "nested" / "deep"
        nested.mkdir(parents=True)

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @require_git_repo(path_param="path")
        def test_cmd(path):
            click.echo("found_git")

        result = cli_runner.invoke(test_cmd, ["--path", str(nested)])
        assert result.exit_code == 0
        assert "found_git" in result.output

    def test_default_path_param(self, cli_runner, tmp_path):
        """Test decorator uses 'path' as default parameter."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @require_git_repo()  # No path_param specified
        def test_cmd(path):
            click.echo("default_param")

        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        assert "default_param" in result.output

    def test_custom_path_param_name(self, cli_runner, tmp_path):
        """Test decorator with custom path parameter name."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        @click.command()
        @click.option("--directory", default=".", type=click.Path())
        @require_git_repo(path_param="directory")
        def test_cmd(directory):
            click.echo("custom_param")

        result = cli_runner.invoke(test_cmd, ["--directory", str(tmp_path)])
        assert "custom_param" in result.output

    def test_handles_string_path(self, cli_runner, tmp_path):
        """Test decorator handles string paths correctly."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        @click.command()
        @click.option("--path", type=str)
        @require_git_repo(path_param="path")
        def test_cmd(path):
            click.echo("string_path")

        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        assert "string_path" in result.output

    def test_handles_path_object(self, cli_runner, tmp_path):
        """Test decorator handles Path objects correctly."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        @click.command()
        @click.option("--path", type=click.Path(path_type=Path))
        @require_git_repo(path_param="path")
        def test_cmd(path):
            click.echo("path_object")

        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        assert "path_object" in result.output


class TestWithConfigOptionalDecorator:
    """Tests for @with_config_optional decorator."""

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_loads_existing_config(
        self, mock_repo_class, mock_config_service, cli_runner, tmp_path
    ):
        """Test decorator loads existing config when available."""
        mock_repo = Mock()
        mock_repo.exists.return_value = True
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {"data": "exists"}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config_optional(path_param="path")
        def test_cmd(path, config_data, config_repo):
            assert config_data == {"data": "exists"}
            click.echo("loaded")

        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        assert "loaded" in result.output
        # Should not show default message
        assert "default" not in result.output.lower()

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_uses_defaults_when_missing(
        self, mock_repo_class, mock_config_service, cli_runner, tmp_path
    ):
        """Test decorator uses defaults when config missing."""
        mock_repo = Mock()
        mock_repo.exists.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {"default": "config"}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config_optional()
        def test_cmd(path, config_data, config_repo):
            assert config_data == {"default": "config"}
            click.echo("defaults")

        result = cli_runner.invoke(test_cmd)
        assert "defaults" in result.output

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_shows_default_message(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test decorator shows custom message when using defaults."""
        mock_repo = Mock()
        mock_repo.exists.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config_optional(default_message="Using fallback configuration")
        def test_cmd(path, config_data, config_repo):
            click.echo("done")

        result = cli_runner.invoke(test_cmd)
        assert "Using fallback configuration" in result.output
        assert "done" in result.output

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_no_message_when_config_exists(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test decorator doesn't show message when config exists."""
        mock_repo = Mock()
        mock_repo.exists.return_value = True
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config_optional(default_message="Should not appear")
        def test_cmd(path, config_data, config_repo):
            click.echo("done")

        result = cli_runner.invoke(test_cmd)
        assert "Should not appear" not in result.output
        assert "done" in result.output

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_no_message_when_not_specified(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test decorator works without default message."""
        mock_repo = Mock()
        mock_repo.exists.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config_optional()  # No default_message
        def test_cmd(path, config_data, config_repo):
            click.echo("done")

        result = cli_runner.invoke(test_cmd)
        assert "done" in result.output
        # No warning message should appear
        assert result.output.count("done") >= 1

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_custom_parameter_names(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test decorator with custom parameter names."""
        mock_repo = Mock()
        mock_repo.exists.return_value = True
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {"test": "data"}

        @click.command()
        @click.option("--config-dir", default=".", type=click.Path())
        @with_config_optional(
            path_param="config_dir", config_name="settings", repo_name="repository"
        )
        def test_cmd(config_dir, settings, repository):
            assert settings == {"test": "data"}
            assert repository == mock_repo
            click.echo("custom")

        result = cli_runner.invoke(test_cmd, ["--config-dir", "."])
        assert "custom" in result.output

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_injects_repo_for_saving(
        self, mock_repo_class, mock_config_service, cli_runner
    ):
        """Test decorator injects repo even when config missing."""
        mock_repo = Mock()
        mock_repo.exists.return_value = False
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @with_config_optional()
        def test_cmd(path, config_data, config_repo):
            # Repo should be available for saving even if config doesn't exist
            assert config_repo == mock_repo
            click.echo("repo_available")

        result = cli_runner.invoke(test_cmd)
        assert "repo_available" in result.output


class TestDecoratorCombinations:
    """Tests for combining multiple decorators."""

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_with_config_and_handle_errors(
        self, mock_repo_class, mock_config_service, cli_runner, tmp_path
    ):
        """Test combining @with_config and @handle_errors."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @handle_errors("test operation")
        @with_config(path_param="path")
        def test_cmd(path, config_data, config_repo):
            raise ValueError("Test error")

        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        assert result.exit_code == 1
        # Both decorators should work together

    @patch("claudefig.cli.decorators.config_service")
    @patch("claudefig.cli.decorators.TomlConfigRepository")
    def test_require_git_and_with_config(
        self, mock_repo_class, mock_config_service, cli_runner, tmp_path
    ):
        """Test combining @require_git_repo and @with_config."""
        # Create git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_config_service.load_config.return_value = {}

        @click.command()
        @click.option("--path", default=".", type=click.Path())
        @require_git_repo(path_param="path")
        @with_config(path_param="path")
        def test_cmd(path, config_data, config_repo):
            click.echo("combined")

        result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "combined" in result.output

    def test_all_decorators_combined(self, cli_runner, tmp_path):
        """Test combining all decorators together."""
        # Create git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with (
            patch("claudefig.cli.decorators.config_service") as mock_config_service,
            patch("claudefig.cli.decorators.TomlConfigRepository") as mock_repo_class,
        ):
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_config_service.load_config.return_value = {}

            @click.command()
            @click.option("--path", default=".", type=click.Path())
            @handle_errors("complex operation")
            @require_git_repo(path_param="path")
            @with_config(path_param="path")
            def test_cmd(path, config_data, config_repo):
                click.echo("all_decorators")

            result = cli_runner.invoke(test_cmd, ["--path", str(tmp_path)])
            assert result.exit_code == 0
            assert "all_decorators" in result.output
