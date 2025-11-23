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

from pathlib import Path
from typing import TYPE_CHECKING, Any

import factory
from factory.declarations import Dict, LazyAttribute, List, Sequence
from factory.faker import Faker

from claudefig.models import (
    ComponentDiscoveryResult,
    DiscoveredComponent,
    FileInstance,
    FileType,
    Preset,
    PresetDefinition,
    PresetSource,
)

if TYPE_CHECKING:
    pass


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
    def path(obj: Any) -> str:  # noqa: N805
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
            FileType.PLUGINS: ".claude/plugins/example-plugin.json",
            FileType.SKILLS: ".claude/skills/example-skill.md",
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
    def id(obj: Any) -> str:  # noqa: N805
        """Generate ID from type and name.

        Args:
            obj: Factory instance being built.

        Returns:
            Preset ID in format "type:name".
        """
        return f"{obj.type.value}:{obj.name}"


class PresetDefinitionFactory(factory.Factory):  # type: ignore[misc]
    """Factory for creating PresetDefinition test objects.

    Used for claudefig.toml preset definition testing.

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


class DiscoveredComponentFactory(factory.Factory):  # type: ignore[misc]
    """Factory for creating DiscoveredComponent test objects.

    Used for testing component discovery functionality.

    Note:
        Factory class attributes are descriptors, not typed attributes.
        The path must be absolute and relative_path must be relative.
    """

    class Meta:  # type: ignore[misc]
        model = DiscoveredComponent

    # Factory descriptors (no type annotations)
    name = Sequence(lambda n: f"component-{n}")
    type = FileType.CLAUDE_MD
    parent_folder = "."
    is_duplicate = False
    duplicate_paths = List([])

    @LazyAttribute  # type: ignore[misc]
    def path(obj: Any) -> Path:  # noqa: N805
        """Generate absolute path based on file type.

        Args:
            obj: Factory instance being built.

        Returns:
            Absolute path for the component.
        """
        import tempfile
        from pathlib import Path

        # Generate a temp path that's absolute
        type_filenames = {
            FileType.CLAUDE_MD: "CLAUDE.md",
            FileType.GITIGNORE: ".gitignore",
            FileType.COMMANDS: "command.md",
            FileType.AGENTS: "agent.md",
            FileType.HOOKS: "hook.py",
            FileType.OUTPUT_STYLES: "style.md",
            FileType.MCP: "mcp.json",
            FileType.PLUGINS: "plugin.json",
            FileType.SKILLS: "skill.md",
            FileType.SETTINGS_JSON: "settings.json",
            FileType.SETTINGS_LOCAL_JSON: "settings.local.json",
            FileType.STATUSLINE: "statusline.sh",
        }
        filename = type_filenames.get(obj.type, "file.txt")
        return Path(tempfile.gettempdir()) / filename

    @LazyAttribute  # type: ignore[misc]
    def relative_path(obj: Any) -> Path:  # noqa: N805
        """Generate relative path based on file type.

        Args:
            obj: Factory instance being built.

        Returns:
            Relative path for the component.
        """
        from pathlib import Path

        type_paths = {
            FileType.CLAUDE_MD: "CLAUDE.md",
            FileType.GITIGNORE: ".gitignore",
            FileType.COMMANDS: ".claude/commands/command.md",
            FileType.AGENTS: ".claude/agents/agent.md",
            FileType.HOOKS: ".claude/hooks/hook.py",
            FileType.OUTPUT_STYLES: ".claude/output-styles/style.md",
            FileType.MCP: ".claude/mcp/mcp.json",
            FileType.PLUGINS: ".claude/plugins/plugin.json",
            FileType.SKILLS: ".claude/skills/skill.md",
            FileType.SETTINGS_JSON: ".claude/settings.json",
            FileType.SETTINGS_LOCAL_JSON: ".claude/settings.local.json",
            FileType.STATUSLINE: ".claude/statusline.sh",
        }
        return Path(type_paths.get(obj.type, "file.txt"))

    @classmethod
    def claude_md(cls, **kwargs: Any) -> DiscoveredComponent:
        """Create a CLAUDE.md DiscoveredComponent.

        Args:
            **kwargs: Additional fields to override.

        Returns:
            DiscoveredComponent configured for CLAUDE.md.
        """
        defaults = {
            "type": FileType.CLAUDE_MD,
            "name": "CLAUDE",
        }
        return cls(**{**defaults, **kwargs})  # type: ignore[return-value]

    @classmethod
    def gitignore(cls, **kwargs: Any) -> DiscoveredComponent:
        """Create a .gitignore DiscoveredComponent.

        Args:
            **kwargs: Additional fields to override.

        Returns:
            DiscoveredComponent configured for .gitignore.
        """
        defaults = {
            "type": FileType.GITIGNORE,
            "name": "gitignore",
        }
        return cls(**{**defaults, **kwargs})  # type: ignore[return-value]


class ComponentDiscoveryResultFactory(factory.Factory):  # type: ignore[misc]
    """Factory for creating ComponentDiscoveryResult test objects.

    Used for testing component discovery results.

    Note:
        Factory class attributes are descriptors, not typed attributes.
    """

    class Meta:  # type: ignore[misc]
        model = ComponentDiscoveryResult

    # Factory descriptors (no type annotations)
    components = List([])
    warnings = List([])
    scan_time_ms = 0.0

    @LazyAttribute  # type: ignore[misc]
    def total_found(obj: Any) -> int:  # noqa: N805
        """Calculate total_found from components list.

        Args:
            obj: Factory instance being built.

        Returns:
            Number of components in the list.
        """
        return len(obj.components)

    @classmethod
    def with_components(
        cls, components: list[DiscoveredComponent], **kwargs: Any
    ) -> ComponentDiscoveryResult:
        """Create result with specific components.

        Args:
            components: List of discovered components.
            **kwargs: Additional fields to override.

        Returns:
            ComponentDiscoveryResult with the given components.
        """
        return cls(
            components=components,
            total_found=len(components),
            **kwargs,
        )  # type: ignore[return-value]

    @classmethod
    def empty(cls, **kwargs: Any) -> ComponentDiscoveryResult:
        """Create an empty discovery result.

        Args:
            **kwargs: Additional fields to override.

        Returns:
            ComponentDiscoveryResult with no components.
        """
        return cls(
            components=[],
            total_found=0,
            **kwargs,
        )  # type: ignore[return-value]

    @classmethod
    def with_warnings(
        cls, warnings: list[str], **kwargs: Any
    ) -> ComponentDiscoveryResult:
        """Create result with warnings.

        Args:
            warnings: List of warning messages.
            **kwargs: Additional fields to override.

        Returns:
            ComponentDiscoveryResult with the given warnings.
        """
        return cls(warnings=warnings, **kwargs)  # type: ignore[return-value]
