"""Test data factories using factory_boy and pytest-factoryboy.

These factories reduce test boilerplate by providing reusable object creation
with sensible defaults and easy customization.

Usage in tests:
    # Automatic fixtures (via pytest-factoryboy):
    def test_something(file_instance):
        # file_instance is automatically created with defaults
        assert file_instance.enabled is True

    # Factory methods (for custom values):
    def test_custom():
        instance = FileInstanceFactory(
            id="custom-id",
            path="custom-path.md",
        )
        assert instance.id == "custom-id"

    # Batch creation:
    def test_multiple():
        instances = FileInstanceFactory.create_batch(3)
        assert len(instances) == 3

Note on typing:
    factory-boy uses metaclass magic that conflicts with static type checkers.
    We use strategic type: ignore comments per community best practices.
    See: https://github.com/FactoryBoy/factory_boy/issues/468
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import factory
from factory.declarations import Dict, LazyAttribute, List, Sequence
from factory.faker import Faker

from claudefig.models import FileInstance, FileType, Preset, PresetDefinition, PresetSource

if TYPE_CHECKING:
    from pathlib import Path


class FileInstanceFactory(factory.Factory):  # type: ignore[misc]
    """Factory for creating FileInstance test objects.

    Provides sensible defaults for all required fields.

    Note:
        Factory class attributes are descriptors processed by metaclass,
        not actual typed attributes. Type annotations would confuse checkers.
    """

    class Meta:  # type: ignore[misc]
        model = FileInstance

    # Factory descriptors (no type annotations per factory-boy patterns)
    id = Sequence(lambda n: f"test-instance-{n}")
    type = FileType.CLAUDE_MD
    preset = "claude_md:default"
    enabled = True
    variables = Dict({})

    @LazyAttribute  # type: ignore[misc]
    def path(obj: Any) -> str:
        """Generate path based on file type.

        Args:
            obj: Factory instance being built.

        Returns:
            Path string appropriate for the file type.
        """
        type_paths = {
            FileType.CLAUDE_MD: "CLAUDE.md",
            FileType.GITIGNORE: ".gitignore",
            FileType.COMMANDS: ".claude/commands/example.md",
            FileType.AGENTS: ".claude/agents/example.md",
            FileType.HOOKS: ".claude/hooks/example.py",
            FileType.OUTPUT_STYLES: ".claude/output-styles/example.md",
            FileType.MCP: ".claude/mcp/example.json",
            FileType.SETTINGS_JSON: ".claude/settings.json",
            FileType.SETTINGS_LOCAL_JSON: ".claude/settings.local.json",
            FileType.STATUSLINE: ".claude/statusline.sh",
        }
        return type_paths.get(obj.type, "file.txt")

    @classmethod
    def create_dict(cls, *items: tuple[str, dict[str, Any]]) -> dict[str, FileInstance]:
        """Create dict of instances from (id, kwargs) tuples.

        Args:
            *items: Variable number of (id, kwargs_dict) tuples.

        Returns:
            Dict mapping IDs to FileInstance objects.

        Example:
            instances = FileInstanceFactory.create_dict(
                ("test-1", {}),
                ("test-2", {"enabled": False}),
                ("test-3", {"type": FileType.GITIGNORE}),
            )
        """
        return {item_id: cls(id=item_id, **kwargs) for item_id, kwargs in items}  # type: ignore[misc]

    @classmethod
    def disabled(cls, **kwargs: Any) -> FileInstance:
        """Create a disabled FileInstance.

        Args:
            **kwargs: Additional fields to override.

        Returns:
            FileInstance with enabled=False.

        Example:
            disabled = FileInstanceFactory.disabled(id="test-1")
        """
        return cls(enabled=False, **kwargs)  # type: ignore[return-value]

    @classmethod
    def gitignore(cls, **kwargs: Any) -> FileInstance:
        """Create a .gitignore FileInstance.

        Args:
            **kwargs: Additional fields to override.

        Returns:
            FileInstance configured for .gitignore files.

        Example:
            gitignore = FileInstanceFactory.gitignore(id="test-1")
        """
        defaults = {
            "type": FileType.GITIGNORE,
            "preset": "gitignore:python",
        }
        return cls(**{**defaults, **kwargs})  # type: ignore[return-value]


class PresetFactory(factory.Factory):  # type: ignore[misc]
    """Factory for creating Preset test objects.

    Provides sensible defaults for preset testing.

    Note:
        Factory class attributes are descriptors, not typed attributes.
    """

    class Meta:  # type: ignore[misc]
        model = Preset

    # Factory descriptors (no type annotations)
    name = Sequence(lambda n: f"test-preset-{n}")
    type = FileType.CLAUDE_MD
    description = Faker("sentence")
    source = PresetSource.USER
    template_path = None
    variables = Dict({})
    extends = None
    tags = List([])

    @LazyAttribute  # type: ignore[misc]
    def id(obj: Any) -> str:
        """Generate ID from type and name.

        Args:
            obj: Factory instance being built.

        Returns:
            Preset ID in format "type:name".
        """
        return f"{obj.type.value}:{obj.name}"


class PresetDefinitionFactory(factory.Factory):  # type: ignore[misc]
    """Factory for creating PresetDefinition test objects.

    Used for .claudefig.toml preset definition testing.

    Note:
        Factory class attributes are descriptors, not typed attributes.
    """

    class Meta:  # type: ignore[misc]
        model = PresetDefinition

    # Factory descriptors (no type annotations)
    id = Sequence(lambda n: f"preset-def-{n}")
    name = Sequence(lambda n: f"test-preset-{n}")
    description = Faker("sentence")
    version = "1.0.0"
    components = List([])
    variables = Dict({})
    settings = Dict({})
    gitignore_entries = List([])
