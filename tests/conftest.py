"""Shared pytest fixtures for claudefig tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_factoryboy import register

# Import and register factories for automatic fixture creation
from tests.factories import FileInstanceFactory, PresetDefinitionFactory, PresetFactory

# Register factories as pytest fixtures
# This creates fixtures like: file_instance, preset, preset_definition
register(FileInstanceFactory)
register(PresetFactory)
register(PresetDefinitionFactory)


@pytest.fixture
def temp_component_dir(tmp_path: Path) -> Path:
    """Create temporary component directory with test components.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to temporary component directory.
    """
    component_dir = tmp_path / "components"
    component_dir.mkdir()
    return component_dir


@pytest.fixture
def sample_component_toml() -> str:
    """Sample valid component.toml content.

    Returns:
        TOML content as string.
    """
    return """[component]
name = "test-component"
type = "language"
version = "1.0.0"
description = "Test component for unit tests"

[component.metadata]
author = "Test Author"
license = "MIT"
tags = ["test", "example"]

[component.dependencies]
requires = []
recommends = []
conflicts = []

[component.files]
claude_md = ["content.md"]
settings = []
contributing = []

[component.variables]
test_var = { type = "string", default = "test_value" }

[component.insertion]
section = "Test Section"
priority = 100
user_editable = true
"""


@pytest.fixture
def mock_user_home(tmp_path: Path, monkeypatch):
    """Mock Path.home() to use temp directory.

    Args:
        tmp_path: Pytest temporary path fixture.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Mocked home directory path.
    """
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    return home_dir


@pytest.fixture
def create_test_component(temp_component_dir: Path):
    """Factory fixture to create test components.

    Args:
        temp_component_dir: Temporary component directory.

    Returns:
        Function to create test components.
    """

    def _create_component(
        category: str,
        name: str,
        toml_content: str,
        content_files: dict[str, str] | None = None,
    ) -> Path:
        """Create a test component with given configuration.

        Args:
            category: Component category (e.g., "languages").
            name: Component name (e.g., "python").
            toml_content: Content for component.toml.
            content_files: Optional dict of filename -> content.

        Returns:
            Path to created component directory.
        """
        component_path = temp_component_dir / category / name
        component_path.mkdir(parents=True, exist_ok=True)

        # Write component.toml
        (component_path / "component.toml").write_text(toml_content, encoding="utf-8")

        # Write content files if provided
        if content_files:
            for filename, content in content_files.items():
                (component_path / filename).write_text(content, encoding="utf-8")

        return component_path

    return _create_component


@pytest.fixture
def mock_config_for_tui(tmp_path: Path) -> Path:
    """Create a mock configuration for TUI testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to mock config file.
    """
    config_path = tmp_path / "claudefig.toml"
    config_path.write_text(
        """[claudefig]
schema_version = "2.0"
template_source = "built-in"

[[file_instances]]
id = "test-claude-md"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true
""",
        encoding="utf-8",
    )
    return config_path
