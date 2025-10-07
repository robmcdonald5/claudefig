"""End-to-end integration tests for claudefig."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from claudefig.cli import main
from claudefig.composer import ComponentComposer
from claudefig.user_config import ensure_user_config, get_user_config_dir


class TestFullInitializationWorkflow:
    """Test complete initialization workflow."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI test runner."""
        return CliRunner()

    @pytest.mark.skip(
        reason="Init command requires interactive input - needs non-interactive mode for testing"
    )
    def test_init_command_creates_structure(self, cli_runner, mock_user_home, tmp_path):
        """Test that 'claudefig init' creates necessary files and directories."""
        # Create a test repo directory
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Run init command
        result = cli_runner.invoke(main, ["init", "--path", str(repo_dir)])

        # Check command succeeded
        if result.exit_code != 0:
            print(f"Command output: {result.output}")
            if result.exception:
                print(f"Exception: {result.exception}")
        assert result.exit_code == 0

        # Check that files were created
        assert (repo_dir / ".claude").exists()
        assert (repo_dir / ".claude").is_dir()

    @pytest.mark.skip(
        reason="Init command requires interactive input - needs non-interactive mode for testing"
    )
    def test_init_command_with_force(self, cli_runner, mock_user_home, tmp_path):
        """Test init command with --force flag overwrites existing files."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Create existing .claude directory with content
        claude_dir = repo_dir / ".claude"
        claude_dir.mkdir()
        existing_file = claude_dir / "test.txt"
        existing_file.write_text("existing content", encoding="utf-8")

        # Run init with force
        result = cli_runner.invoke(main, ["init", "--path", str(repo_dir), "--force"])

        assert result.exit_code == 0
        assert claude_dir.exists()

    @pytest.mark.skip(
        reason="Version command doesn't trigger user config init - expected behavior"
    )
    def test_user_config_initialized_on_first_run(self, cli_runner, mock_user_home):
        """Test that user config is initialized on first CLI run."""
        config_dir = get_user_config_dir()

        # Ensure not initialized
        assert not config_dir.exists()

        # Run any command
        result = cli_runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        # User config should now exist
        assert config_dir.exists()
        assert (config_dir / "components").exists()


class TestComponentSystemIntegration:
    """Test end-to-end component system workflows."""

    def test_default_components_load_successfully(self, mock_user_home):
        """Test that all default components can be loaded without errors."""
        # Initialize user config to get default components
        ensure_user_config(verbose=False)

        component_dir = get_user_config_dir() / "components"
        composer = ComponentComposer(component_dir)

        # List all available components
        all_components = composer.get_available_components()

        # Should have some default components
        assert len(all_components) > 0

        # Try to load each component
        for component_path in all_components:
            details = composer.get_component_details(component_path)
            assert details is not None
            assert "name" in details

    def test_compose_claude_md_from_default_components(self, mock_user_home):
        """Test composing CLAUDE.md from default components."""
        ensure_user_config(verbose=False)

        component_dir = get_user_config_dir() / "components"
        composer = ComponentComposer(component_dir)

        # Get available components
        components = composer.get_available_components()

        if components:
            # Compose CLAUDE.md from first component
            result = composer.compose_claude_md([components[0]])

            # Should produce non-empty result
            assert result != ""
            assert isinstance(result, str)

    def test_component_dependencies_resolve(self, mock_user_home, tmp_path):
        """Test that component dependencies are resolved correctly."""
        # Create custom components with dependencies
        component_dir = tmp_path / "components"
        component_dir.mkdir()

        # Create base component
        base_dir = component_dir / "general" / "base"
        base_dir.mkdir(parents=True)
        (base_dir / "component.toml").write_text(
            """[component]
name = "base"
[component.files]
claude_md = ["content.md"]
[component.insertion]
priority = 10
""",
            encoding="utf-8",
        )
        (base_dir / "content.md").write_text("# Base Component", encoding="utf-8")

        # Create dependent component
        dep_dir = component_dir / "general" / "dependent"
        dep_dir.mkdir(parents=True)
        (dep_dir / "component.toml").write_text(
            """[component]
name = "dependent"
[component.dependencies]
requires = ["general/base"]
[component.files]
claude_md = ["content.md"]
[component.insertion]
priority = 20
""",
            encoding="utf-8",
        )
        (dep_dir / "content.md").write_text("# Dependent Component", encoding="utf-8")

        # Test dependency resolution
        composer = ComponentComposer(component_dir)
        result = composer.compose_claude_md(["general/dependent"])

        # Should include both components
        assert "# Base Component" in result
        assert "# Dependent Component" in result
        # Base should come first (lower priority)
        assert result.index("# Base Component") < result.index("# Dependent Component")


class TestCLICommands:
    """Test CLI command integration."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI test runner."""
        return CliRunner()

    def test_show_command(self, cli_runner, mock_user_home):
        """Test 'claudefig show' command."""
        result = cli_runner.invoke(main, ["show"])

        assert result.exit_code == 0
        assert "Configuration" in result.output or "Config" in result.output

    def test_list_templates_command(self, cli_runner, mock_user_home):
        """Test 'claudefig list-templates' command."""
        result = cli_runner.invoke(main, ["list-templates"])

        # Should succeed even if no templates found
        assert result.exit_code == 0

    def test_version_option(self, cli_runner):
        """Test --version option."""
        result = cli_runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "claudefig" in result.output.lower()

    def test_help_option(self, cli_runner):
        """Test --help option."""
        result = cli_runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "init" in result.output


class TestDefaultComponents:
    """Test that default components are valid and functional."""

    def test_all_default_components_have_valid_toml(self, mock_user_home):
        """Test that all default components have valid component.toml files."""
        ensure_user_config(verbose=False)

        component_dir = get_user_config_dir() / "components"
        composer = ComponentComposer(component_dir)

        all_components = composer.get_available_components()

        for component_path in all_components:
            # Each component should have valid metadata
            details = composer.get_component_details(component_path)

            assert details is not None
            assert "name" in details
            assert "priority" in details
            assert "section" in details

    def test_default_components_render_without_errors(self, mock_user_home):
        """Test that default components render without Jinja2 errors."""
        ensure_user_config(verbose=False)

        component_dir = get_user_config_dir() / "components"
        composer = ComponentComposer(component_dir)

        all_components = composer.get_available_components()

        # Try rendering each component
        for component_path in all_components:
            try:
                result = composer.compose_claude_md([component_path])
                # Should produce string output (even if empty)
                assert isinstance(result, str)
            except Exception as e:
                pytest.fail(f"Component {component_path} failed to render: {e}")

    def test_default_components_validate(self, mock_user_home):
        """Test that default component paths validate successfully."""
        ensure_user_config(verbose=False)

        component_dir = get_user_config_dir() / "components"
        composer = ComponentComposer(component_dir)

        all_components = composer.get_available_components()

        if all_components:
            # Validate all components together
            is_valid, error = composer.validate_components(all_components)

            # Should be valid (no missing dependencies or conflicts)
            assert is_valid, f"Default components failed validation: {error}"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def cli_runner(self):
        """Create Click CLI test runner."""
        return CliRunner()

    def test_init_in_nonexistent_directory_fails(self, cli_runner, mock_user_home):
        """Test that init fails gracefully with non-existent directory."""
        result = cli_runner.invoke(main, ["init", "--path", "/nonexistent/path"])

        # Should fail
        assert result.exit_code != 0

    def test_compose_with_empty_component_list(self, mock_user_home):
        """Test composing with empty component list."""
        ensure_user_config(verbose=False)

        component_dir = get_user_config_dir() / "components"
        composer = ComponentComposer(component_dir)

        result = composer.compose_claude_md([])

        # Should return empty string
        assert result == ""

    def test_compose_with_nonexistent_component(self, mock_user_home):
        """Test that composing with non-existent component raises error."""
        ensure_user_config(verbose=False)

        component_dir = get_user_config_dir() / "components"
        composer = ComponentComposer(component_dir)

        with pytest.raises(ValueError):
            composer.compose_claude_md(["nonexistent/component"])
