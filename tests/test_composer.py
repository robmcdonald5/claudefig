"""Tests for composer.py - ComponentComposer."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from claudefig.composer import ComponentComposer

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class TestComponentComposer:
    """Test ComponentComposer class."""

    @pytest.fixture
    def composer(self, temp_component_dir):
        """Create ComponentComposer with temp component directory."""
        return ComponentComposer(temp_component_dir)

    @pytest.fixture
    def setup_test_components(self, create_test_component):
        """Setup standard test components for testing."""
        # Create simple component
        simple_toml = """[component]
name = "simple"
[component.files]
claude_md = ["content.md"]
[component.insertion]
section = "Simple Section"
priority = 10
"""
        create_test_component(
            "general",
            "simple",
            simple_toml,
            {"content.md": "# Simple Component\n\nThis is simple."}
        )

        # Create component with variables
        vars_toml = """[component]
name = "with-vars"
[component.files]
claude_md = ["content.md"]
[component.variables]
name = { type = "string", default = "DefaultName" }
enabled = { type = "boolean", default = true }
[component.insertion]
section = "Variables Section"
priority = 20
"""
        create_test_component(
            "languages",
            "with-vars",
            vars_toml,
            {"content.md": "# {{ name }}\n\nEnabled: {% if enabled %}Yes{% else %}No{% endif %}"}
        )

        # Create component with settings
        settings_toml = """[component]
name = "with-settings"
[component.files]
settings = ["settings.json"]
[component.insertion]
section = "Settings Section"
priority = 30
"""
        create_test_component(
            "frameworks",
            "with-settings",
            settings_toml,
            {"settings.json": '{"framework": "test"}'}
        )

        # Create component with contributing
        contributing_toml = """[component]
name = "with-contributing"
[component.files]
contributing = ["contributing.md"]
[component.insertion]
section = "Contributing Section"
priority = 40
"""
        create_test_component(
            "general",
            "with-contributing",
            contributing_toml,
            {"contributing.md": "# How to Contribute\n\nPlease submit PRs."}
        )

    def test_compose_claude_md_single_component(
        self, composer, create_test_component
    ):
        """Test composing CLAUDE.md with single component."""
        toml = """[component]
name = "test"
[component.files]
claude_md = ["content.md"]
[component.insertion]
section = "Test"
priority = 10
"""
        create_test_component(
            "general", "test", toml, {"content.md": "# Test Content"}
        )

        result = composer.compose_claude_md(["general/test"])

        assert "# Test Content" in result

    def test_compose_claude_md_multiple_components(
        self, composer, setup_test_components
    ):
        """Test composing CLAUDE.md with multiple components."""
        result = composer.compose_claude_md([
            "general/simple",
            "languages/with-vars"
        ])

        # Should have both components in priority order
        assert "# Simple Component" in result
        assert "# DefaultName" in result  # Using default variable
        assert result.index("# Simple Component") < result.index("# DefaultName")  # Priority order

    def test_compose_claude_md_with_variables(
        self, composer, setup_test_components
    ):
        """Test composing with variable overrides."""
        result = composer.compose_claude_md(
            ["languages/with-vars"],
            variables={"name": "CustomName", "enabled": False}
        )

        assert "# CustomName" in result
        assert "Enabled: No" in result

    def test_compose_claude_md_with_toc(
        self, composer, setup_test_components
    ):
        """Test composing with table of contents."""
        result = composer.compose_claude_md(
            ["general/simple", "languages/with-vars"],
            include_toc=True
        )

        # Should have TOC
        assert "# Table of Contents" in result
        assert "[Simple Section]" in result
        assert "[Variables Section]" in result
        assert "---" in result

    def test_compose_claude_md_with_dependencies(
        self, composer, create_test_component
    ):
        """Test composing with component dependencies."""
        # Create base component
        base_toml = """[component]
name = "base"
[component.files]
claude_md = ["content.md"]
[component.insertion]
section = "Base"
priority = 10
"""
        create_test_component(
            "general", "base", base_toml, {"content.md": "# Base"}
        )

        # Create dependent component
        dep_toml = """[component]
name = "dependent"
[component.dependencies]
requires = ["general/base"]
[component.files]
claude_md = ["content.md"]
[component.insertion]
section = "Dependent"
priority = 20
"""
        create_test_component(
            "general", "dependent", dep_toml, {"content.md": "# Dependent"}
        )

        result = composer.compose_claude_md(["general/dependent"])

        # Should include both components
        assert "# Base" in result
        assert "# Dependent" in result

    def test_compose_claude_md_dependency_error(
        self, composer, create_test_component
    ):
        """Test that dependency resolution errors are raised."""
        # Create component with missing dependency
        toml = """[component]
name = "broken"
[component.dependencies]
requires = ["nonexistent/component"]
[component.files]
claude_md = ["content.md"]
"""
        create_test_component("general", "broken", toml, {"content.md": "# Broken"})

        with pytest.raises(ValueError):
            composer.compose_claude_md(["general/broken"])

    def test_compose_claude_md_no_components(self, composer):
        """Test composing with empty component list returns empty string."""
        result = composer.compose_claude_md([])
        assert result == ""

    def test_compose_settings_json(
        self, composer, setup_test_components
    ):
        """Test composing settings.json."""
        result = composer.compose_settings_json(["frameworks/with-settings"])

        assert '{"framework": "test"}' in result

    def test_compose_settings_json_no_settings(
        self, composer, setup_test_components
    ):
        """Test composing settings with no settings files returns '{}'."""
        result = composer.compose_settings_json(["general/simple"])

        assert result == "{}"

    def test_compose_settings_json_multiple(
        self, composer, create_test_component, setup_test_components
    ):
        """Test composing settings from multiple components."""
        # Create another component with settings
        toml = """[component]
name = "more-settings"
[component.files]
settings = ["settings.json"]
"""
        create_test_component(
            "general", "more-settings", toml,
            {"settings.json": '{"another": "setting"}'}
        )

        result = composer.compose_settings_json([
            "frameworks/with-settings",
            "general/more-settings"
        ])

        assert '{"framework": "test"}' in result
        assert '{"another": "setting"}' in result

    def test_compose_contributing_md(
        self, composer, setup_test_components
    ):
        """Test composing CONTRIBUTING.md."""
        result = composer.compose_contributing_md(["general/with-contributing"])

        assert "# How to Contribute" in result
        assert "Please submit PRs" in result

    def test_compose_contributing_md_no_contributing(
        self, composer, setup_test_components
    ):
        """Test composing contributing with no contributing files."""
        result = composer.compose_contributing_md(["general/simple"])

        assert result == ""

    def test_merge_variables_with_defaults(self, composer):
        """Test _merge_variables extracts defaults correctly."""
        component_vars = {
            "var1": {"type": "string", "default": "default_value"},
            "var2": {"type": "boolean", "default": True},
        }
        provided_vars = {}

        merged = composer._merge_variables(component_vars, provided_vars)

        assert merged["var1"] == "default_value"
        assert merged["var2"] is True

    def test_merge_variables_with_overrides(self, composer):
        """Test _merge_variables overrides defaults with provided values."""
        component_vars = {
            "var1": {"type": "string", "default": "default_value"},
            "var2": {"type": "boolean", "default": True},
        }
        provided_vars = {
            "var1": "custom_value",
            "var2": False,
        }

        merged = composer._merge_variables(component_vars, provided_vars)

        assert merged["var1"] == "custom_value"
        assert merged["var2"] is False

    def test_merge_variables_simple_values(self, composer):
        """Test _merge_variables handles simple (non-dict) values."""
        component_vars = {
            "simple_var": "simple_value"
        }
        provided_vars = {}

        merged = composer._merge_variables(component_vars, provided_vars)

        assert merged["simple_var"] == "simple_value"

    def test_get_available_components(
        self, composer, setup_test_components
    ):
        """Test getting list of available components."""
        components = composer.get_available_components()

        assert "general/simple" in components
        assert "languages/with-vars" in components
        assert "frameworks/with-settings" in components
        assert "general/with-contributing" in components

    def test_get_available_components_by_category(
        self, composer, setup_test_components
    ):
        """Test getting components filtered by category."""
        general_comps = composer.get_available_components(category="general")

        assert "general/simple" in general_comps
        assert "general/with-contributing" in general_comps
        assert "languages/with-vars" not in general_comps
        assert "frameworks/with-settings" not in general_comps

    def test_get_component_details(
        self, composer, setup_test_components
    ):
        """Test getting detailed component information."""
        details = composer.get_component_details("general/simple")

        assert details is not None
        assert details["name"] == "simple"
        assert details["type"] == "unknown"
        assert details["priority"] == 10
        assert details["section"] == "Simple Section"

    def test_get_component_details_not_found(self, composer):
        """Test getting details for non-existent component returns None."""
        details = composer.get_component_details("nonexistent/component")
        assert details is None

    def test_validate_components_valid(
        self, composer, setup_test_components
    ):
        """Test validating valid component paths."""
        is_valid, error = composer.validate_components([
            "general/simple",
            "languages/with-vars"
        ])

        assert is_valid is True
        assert error == ""

    def test_validate_components_invalid(
        self, composer, create_test_component
    ):
        """Test validating invalid component paths."""
        # Create component with missing dependency
        toml = """[component]
name = "broken"
[component.dependencies]
requires = ["nonexistent/component"]
"""
        create_test_component("general", "broken", toml)

        is_valid, error = composer.validate_components(["general/broken"])

        assert is_valid is False
        assert error != ""
        assert "Component not found" in error

    def test_compose_rendering_failure_warning(
        self, composer, create_test_component, capsys
    ):
        """Test that rendering failures produce warnings but don't crash."""
        # Create component with invalid Jinja2 template
        toml = """[component]
name = "bad-template"
[component.files]
claude_md = ["content.md"]
[component.insertion]
section = "Bad Template"
priority = 10
"""
        create_test_component(
            "general", "bad-template", toml,
            {"content.md": "{{ unclosed_variable"}
        )

        # Should not crash, just warn
        result = composer.compose_claude_md(["general/bad-template"])

        # Should return empty since rendering failed
        assert result == ""

        # Check warning was printed (from renderer, not composer)
        captured = capsys.readouterr()
        assert "Warning: Skipping" in captured.out
