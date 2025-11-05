# Test Factory Usage Guide

## Overview

This project uses `factory-boy` and `pytest-factoryboy` to streamline test data creation. Factories provide sensible defaults while allowing easy customization, reducing boilerplate and improving test maintainability.

## Available Factories

### FileInstanceFactory

Creates `FileInstance` objects with reasonable defaults.

**Defaults:**
- `id`: Sequential (`test-instance-0`, `test-instance-1`, ...)
- `type`: `FileType.CLAUDE_MD`
- `preset`: `"claude_md:default"`
- `path`: Auto-generated based on file type
- `enabled`: `True`
- `variables`: `{}`

**Basic Usage:**

```python
from tests.factories import FileInstanceFactory

# Create with defaults
instance = FileInstanceFactory()

# Override specific fields
instance = FileInstanceFactory(
    id="custom-id",
    type=FileType.GITIGNORE,
    enabled=False,
)

# Create multiple instances
instances = FileInstanceFactory.create_batch(5)
```

**Helper Methods:**

```python
# Create dictionary of instances
instances = FileInstanceFactory.create_dict(
    ("test-1", {}),
    ("test-2", {"enabled": False}),
    ("test-3", {"type": FileType.GITIGNORE}),
)
# Result: {"test-1": FileInstance(...), "test-2": FileInstance(...), ...}

# Create disabled instance
disabled = FileInstanceFactory.disabled(id="test-1")

# Create gitignore instance
gitignore = FileInstanceFactory.gitignore(id="test-1")
```

### PresetFactory

Creates `Preset` objects with reasonable defaults.

**Defaults:**
- `id`: Auto-generated as `"{type}:{name}"`
- `name`: Sequential (`test-preset-0`, `test-preset-1`, ...)
- `type`: `FileType.CLAUDE_MD`
- `description`: Random sentence (via Faker)
- `source`: `PresetSource.USER`
- `template_path`: `None`
- `variables`: `{}`
- `extends`: `None`
- `tags`: `[]`

**Usage:**

```python
from tests.factories import PresetFactory

# Create with defaults
preset = PresetFactory()
# preset.id == "claude_md:test-preset-0" (auto-generated)

# Override fields
preset = PresetFactory(
    name="my-preset",
    type=FileType.GITIGNORE,
    source=PresetSource.BUILT_IN,
)
# preset.id == "gitignore:my-preset"

# With template and variables
preset = PresetFactory(
    name="templated",
    template_path=Path("/path/to/template.md"),
    variables={"name": "World"},
)
```

### PresetDefinitionFactory

Creates `PresetDefinition` objects for `claudefig.toml` (preset definition) testing.

**Defaults:**
- `id`: Sequential (`preset-def-0`, `preset-def-1`, ...)
- `name`: Sequential (`test-preset-0`, `test-preset-1`, ...)
- `description`: Random sentence
- `version`: `"1.0.0"`
- `components`: `[]`
- `variables`: `{}`
- `settings`: `{}`
- `gitignore_entries`: `[]`

**Usage:**

```python
from tests.factories import PresetDefinitionFactory
from claudefig.models import ComponentReference

preset_def = PresetDefinitionFactory(
    name="my-preset",
    version="2.0.0",
    components=[
        ComponentReference(
            type="claude_md",
            name="default",
            path="CLAUDE.md",
        )
    ],
)
```

## Common Patterns

### Pattern 1: Simple Object Creation

```python
# Before (manual)
instance = FileInstance(
    id="test-1",
    type=FileType.CLAUDE_MD,
    preset="claude_md:default",
    path="CLAUDE.md",
    enabled=True,
    variables={},
)

# After (factory) - only specify what's different from defaults
instance = FileInstanceFactory(id="test-1")
```

### Pattern 2: Creating Dictionaries of Instances

```python
# Before (manual)
instances = {
    "test-1": FileInstance(
        id="test-1",
        type=FileType.CLAUDE_MD,
        preset="claude_md:default",
        path="CLAUDE.md",
        enabled=True,
    ),
    "test-2": FileInstance(
        id="test-2",
        type=FileType.GITIGNORE,
        preset="gitignore:python",
        path=".gitignore",
        enabled=True,
    ),
}

# After (factory helper)
instances = FileInstanceFactory.create_dict(
    ("test-1", {}),
    ("test-2", {"type": FileType.GITIGNORE, "preset": "gitignore:python"}),
)
```

### Pattern 3: Type Annotations for Dictionaries

When creating dictionaries, add explicit type annotations for Pylance:

```python
# Correct - with type annotation
instances: dict[str, FileInstance] = FileInstanceFactory.create_dict(
    ("test-1", {}),
)

# Also correct - with type annotation
instances: dict[str, FileInstance] = {"test-1": instance}
```

### Pattern 4: Testing with Inheritance

```python
grandparent = PresetFactory(
    name="grandparent",
    variables={"gp_var": "gp_value"},
)
parent = PresetFactory(
    name="parent",
    variables={"p_var": "p_value"},
    extends=grandparent.id,
)
child = PresetFactory(
    name="child",
    variables={"c_var": "c_value"},
    extends=parent.id,
)
```

### Pattern 5: Removing Default Values

Only specify values that differ from factory defaults:

```python
# Remove these (they're factory defaults):
# - type=FileType.CLAUDE_MD
# - source=PresetSource.USER
# - enabled=True
# - variables={}

# Keep these (they're non-default or important for the test):
# - source=PresetSource.BUILT_IN
# - template_path=some_path
# - specific variable values
```

### Pattern 6: When NOT to Use Factories

Avoid factories when testing:
- Model constructors themselves
- Object validation/edge cases
- `__repr__` or `__str__` methods
- Scenarios requiring explicit field verification

```python
# Correct - testing constructor validation
def test_file_instance_validation():
    # Use manual construction to test validation
    with pytest.raises(ValueError):
        FileInstance(id="", type=FileType.CLAUDE_MD)
```

## Pytest Fixtures

Factories are automatically registered as pytest fixtures via `pytest-factoryboy`:

```python
# Automatic fixture injection
def test_with_fixture(file_instance, preset):
    # file_instance and preset are automatically created
    assert file_instance.enabled is True
    assert preset.source == PresetSource.USER
```

Available fixtures:
- `file_instance` → `FileInstanceFactory()`
- `preset` → `PresetFactory()`
- `preset_definition` → `PresetDefinitionFactory()`

## Type Checking Notes

Factory-boy uses metaclass magic that conflicts with static type checkers. The project uses strategic `# type: ignore` comments per community best practices.

When writing tests:
- Factory attribute definitions in `factories.py` have `# type: ignore[misc]` comments
- Return values from helper methods may need `# type: ignore[return-value]`
- Dictionary creations in tests need explicit type annotations

## Reference

**Factory Implementations:** `tests/factories.py`
**Fixture Registration:** `tests/conftest.py`
**Factory-boy Documentation:** https://factoryboy.readthedocs.io/
