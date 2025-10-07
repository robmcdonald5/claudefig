"""Tests for component.py - ComponentMetadata and ComponentLoader."""

from __future__ import annotations

import sys

import pytest

from claudefig.component import ComponentLoader, ComponentMetadata

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class TestComponentMetadata:
    """Test ComponentMetadata class."""

    def test_parse_valid_component(
        self, create_test_component, sample_component_toml, temp_component_dir
    ):
        """Test parsing a valid component.toml with all fields."""
        component_path = create_test_component(
            "languages",
            "test",
            sample_component_toml,
            {"content.md": "# Test\nTest content"},
        )

        # Load component using ComponentLoader to parse TOML
        with open(component_path / "component.toml", "rb") as f:
            toml_data = tomllib.load(f)

        metadata = ComponentMetadata(component_path, toml_data)

        assert metadata.name == "test-component"
        assert metadata.type == "language"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test component for unit tests"
        assert metadata.priority == 100
        assert metadata.section == "Test Section"
        assert metadata.user_editable is True
        assert metadata.requires == []
        assert metadata.recommends == []
        assert metadata.conflicts == []
        assert metadata.claude_md_files == ["content.md"]
        assert metadata.settings_files == []
        assert metadata.contributing_files == []
        assert "test_var" in metadata.variables
        assert metadata.variables["test_var"]["type"] == "string"
        assert metadata.variables["test_var"]["default"] == "test_value"

    def test_parse_minimal_component(self, create_test_component):
        """Test parsing component.toml with minimal fields (uses defaults)."""
        minimal_toml = """[component]
name = "minimal"
"""
        component_path = create_test_component("general", "minimal", minimal_toml)

        with open(component_path / "component.toml", "rb") as f:
            toml_data = tomllib.load(f)

        metadata = ComponentMetadata(component_path, toml_data)

        assert metadata.name == "minimal"
        assert metadata.type == "unknown"  # default
        assert metadata.version == "1.0.0"  # default
        assert metadata.description == ""  # default
        assert metadata.priority == 100  # default
        assert metadata.section == "minimal"  # defaults to name
        assert metadata.user_editable is False  # default
        assert metadata.requires == []
        assert metadata.recommends == []
        assert metadata.conflicts == []
        assert metadata.claude_md_files == []
        assert metadata.settings_files == []
        assert metadata.contributing_files == []
        assert metadata.variables == {}

    def test_parse_component_with_dependencies(self, create_test_component):
        """Test parsing component with dependencies."""
        toml_with_deps = """[component]
name = "with-deps"

[component.dependencies]
requires = ["general/base", "languages/python"]
recommends = ["frameworks/fastapi"]
conflicts = ["languages/javascript"]
"""
        component_path = create_test_component(
            "frameworks", "with-deps", toml_with_deps
        )

        with open(component_path / "component.toml", "rb") as f:
            toml_data = tomllib.load(f)

        metadata = ComponentMetadata(component_path, toml_data)

        assert metadata.requires == ["general/base", "languages/python"]
        assert metadata.recommends == ["frameworks/fastapi"]
        assert metadata.conflicts == ["languages/javascript"]

    def test_malformed_toml(self, create_test_component):
        """Test that malformed TOML raises appropriate error."""
        malformed_toml = "[component\nname = unclosed"

        component_path = create_test_component("general", "malformed", malformed_toml)

        with pytest.raises(Exception):  # Should raise TOML parsing error
            with open(component_path / "component.toml", "rb") as f:
                tomllib.load(f)

    def test_get_file_paths_claude_md(
        self, create_test_component, sample_component_toml
    ):
        """Test get_file_paths for claude_md files."""
        component_path = create_test_component(
            "languages",
            "test",
            sample_component_toml,
            {"content.md": "# Test"},
        )

        with open(component_path / "component.toml", "rb") as f:
            toml_data = tomllib.load(f)

        metadata = ComponentMetadata(component_path, toml_data)
        claude_md_paths = metadata.get_file_paths("claude_md")

        assert len(claude_md_paths) == 1
        assert claude_md_paths[0].name == "content.md"
        assert claude_md_paths[0].exists()

    def test_get_file_paths_settings(self, create_test_component):
        """Test get_file_paths for settings files."""
        toml_with_settings = """[component]
name = "with-settings"

[component.files]
settings = ["settings.json", "config.yaml"]
"""
        component_path = create_test_component(
            "general",
            "with-settings",
            toml_with_settings,
            {
                "settings.json": '{"key": "value"}',
                "config.yaml": "key: value",
            },
        )

        with open(component_path / "component.toml", "rb") as f:
            toml_data = tomllib.load(f)

        metadata = ComponentMetadata(component_path, toml_data)
        settings_paths = metadata.get_file_paths("settings")

        assert len(settings_paths) == 2
        assert any(p.name == "settings.json" for p in settings_paths)
        assert any(p.name == "config.yaml" for p in settings_paths)

    def test_get_file_paths_invalid_type(
        self, create_test_component, sample_component_toml
    ):
        """Test get_file_paths with invalid file type returns empty list."""
        component_path = create_test_component(
            "languages",
            "test",
            sample_component_toml,
            {"content.md": "# Test"},
        )

        with open(component_path / "component.toml", "rb") as f:
            toml_data = tomllib.load(f)

        metadata = ComponentMetadata(component_path, toml_data)

        # Invalid file type should return empty list
        invalid_paths = metadata.get_file_paths("invalid_type")
        assert invalid_paths == []


class TestComponentLoader:
    """Test ComponentLoader class."""

    @pytest.fixture
    def loader(self, temp_component_dir):
        """Create ComponentLoader with temp component directory."""
        return ComponentLoader(temp_component_dir)

    def test_load_component_valid(
        self, loader, create_test_component, sample_component_toml
    ):
        """Test loading a valid component."""
        create_test_component(
            "languages",
            "python",
            sample_component_toml,
            {"content.md": "# Python"},
        )

        metadata = loader.load_component("languages/python")

        assert metadata is not None
        assert metadata.name == "test-component"

    def test_load_component_not_found(self, loader):
        """Test loading non-existent component returns None."""
        metadata = loader.load_component("nonexistent/component")
        assert metadata is None

    def test_list_all_components(
        self, loader, create_test_component, sample_component_toml
    ):
        """Test listing all components."""
        create_test_component("general", "comp1", sample_component_toml)
        create_test_component("languages", "comp2", sample_component_toml)
        create_test_component("frameworks", "comp3", sample_component_toml)

        components = loader.list_components()

        assert len(components) == 3
        assert "general/comp1" in components
        assert "languages/comp2" in components
        assert "frameworks/comp3" in components

    def test_list_components_by_category(
        self, loader, create_test_component, sample_component_toml
    ):
        """Test listing components filtered by category."""
        create_test_component("general", "comp1", sample_component_toml)
        create_test_component("languages", "comp2", sample_component_toml)
        create_test_component("languages", "comp3", sample_component_toml)

        languages = loader.list_components(category="languages")

        assert len(languages) == 2
        assert "languages/comp2" in languages
        assert "languages/comp3" in languages
        assert "general/comp1" not in languages

    def test_resolve_dependencies_single_component(
        self, loader, create_test_component, sample_component_toml
    ):
        """Test dependency resolution with single component."""
        create_test_component(
            "general",
            "simple",
            sample_component_toml,
            {"content.md": "# Simple"},
        )

        resolved = loader.resolve_dependencies(["general/simple"])

        assert len(resolved) == 1
        assert resolved[0].name == "test-component"

    def test_resolve_dependencies_with_requires(
        self, loader, create_test_component, sample_component_toml
    ):
        """Test dependency resolution with requires chain."""
        # Create base component
        base_toml = """[component]
name = "base"
[component.insertion]
priority = 10
"""
        create_test_component("general", "base", base_toml, {"content.md": "# Base"})

        # Create component that requires base
        requires_toml = """[component]
name = "requires-base"
[component.dependencies]
requires = ["general/base"]
[component.insertion]
priority = 20
"""
        create_test_component(
            "general", "requires-base", requires_toml, {"content.md": "# Requires"}
        )

        resolved = loader.resolve_dependencies(["general/requires-base"])

        assert len(resolved) == 2
        # Should be sorted by priority: base (10) then requires-base (20)
        assert resolved[0].name == "base"
        assert resolved[1].name == "requires-base"

    def test_resolve_dependencies_missing_required(self, loader, create_test_component):
        """Test that missing required dependency raises ValueError."""
        requires_missing_toml = """[component]
name = "requires-missing"
[component.dependencies]
requires = ["nonexistent/component"]
"""
        create_test_component("general", "requires-missing", requires_missing_toml)

        with pytest.raises(ValueError, match="Component not found"):
            loader.resolve_dependencies(["general/requires-missing"])

    def test_resolve_dependencies_with_recommends(
        self, loader, create_test_component, sample_component_toml
    ):
        """Test that missing recommended dependency does not fail."""
        recommends_missing_toml = """[component]
name = "recommends-missing"
[component.dependencies]
recommends = ["nonexistent/component"]
"""
        create_test_component("general", "recommends-missing", recommends_missing_toml)

        # Should not raise error, just skip missing recommended
        resolved = loader.resolve_dependencies(["general/recommends-missing"])

        assert len(resolved) == 1
        assert resolved[0].name == "recommends-missing"

    def test_resolve_dependencies_conflict_detection(
        self, loader, create_test_component
    ):
        """Test that conflicting components raise ValueError."""
        conflict1_toml = """[component]
name = "conflict1"
[component.dependencies]
conflicts = ["conflict2"]
"""
        conflict2_toml = """[component]
name = "conflict2"
"""
        create_test_component("general", "conflict1", conflict1_toml)
        create_test_component("general", "conflict2", conflict2_toml)

        with pytest.raises(ValueError, match="conflicts with"):
            loader.resolve_dependencies(["general/conflict1", "general/conflict2"])

    def test_priority_based_sorting(self, loader, create_test_component):
        """Test that components are sorted by priority."""
        low_priority_toml = """[component]
name = "low"
[component.insertion]
priority = 100
"""
        high_priority_toml = """[component]
name = "high"
[component.insertion]
priority = 10
"""
        mid_priority_toml = """[component]
name = "mid"
[component.insertion]
priority = 50
"""

        create_test_component("general", "low", low_priority_toml)
        create_test_component("general", "high", high_priority_toml)
        create_test_component("general", "mid", mid_priority_toml)

        resolved = loader.resolve_dependencies(
            ["general/low", "general/high", "general/mid"]
        )

        assert len(resolved) == 3
        assert resolved[0].name == "high"  # priority 10
        assert resolved[1].name == "mid"  # priority 50
        assert resolved[2].name == "low"  # priority 100

    def test_get_component_info(
        self, loader, create_test_component, sample_component_toml
    ):
        """Test get_component_info returns correct metadata."""
        create_test_component(
            "languages",
            "python",
            sample_component_toml,
            {"content.md": "# Python"},
        )

        info = loader.get_component_info("languages/python")

        assert info is not None
        assert info["name"] == "test-component"
        assert info["type"] == "language"
        assert info["version"] == "1.0.0"
        assert info["priority"] == 100
        assert "test_var" in info["variables"]
