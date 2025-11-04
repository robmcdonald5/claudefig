# Adding New File Type Components

This guide provides a complete checklist for adding new file type components to claudefig. Follow each section to ensure full TUI/CLI parity and proper integration.

## Overview

A "component" in claudefig represents a file type that can be managed through the TUI and CLI. Components can be:
- **Single-instance**: Only one per project (e.g., settings.json, statusline.sh)
- **Multi-instance**: Multiple allowed (e.g., commands, agents, plugins)
- **File-based**: Single file (e.g., CLAUDE.md, settings.json)
- **Directory-based**: Folder with multiple files (e.g., commands/, agents/, plugins/)

## Required Changes Checklist

### 1. Core Models & Type Definitions

#### `src/claudefig/models.py`
Add new enum value to `FileType` class:
```python
class FileType(Enum):
    ...
    NEW_TYPE = "new_type"  # Use snake_case
```

Update all FileType properties:
```python
# In display_name property
self.NEW_TYPE: "Display Name",

# In default_path property
self.NEW_TYPE: ".claude/new-type/",  # or specific file path

# In is_directory property (if directory-based)
directory_types = {
    ...
    self.NEW_TYPE,
}

# In supports_multiple (if single-instance only)
single_instance_types = {
    ...
    self.NEW_TYPE,  # Add here if single-instance
}

# In append_mode (if should append to existing files)
append_mode_types = {
    ...
    self.NEW_TYPE,  # Add here if append mode needed
}
```

### 2. User Configuration & Structure

#### `src/claudefig/user_config.py`
Add to `component_types` list in `initialize_user_directory()`:
```python
component_types = [
    ...
    "new_type",  # Must match FileType enum value
]
```

#### `src/claudefig/services/structure_validator.py`
Add to `required_dirs` list in `validate_user_directory()`:
```python
required_dirs = [
    ...
    "components/new_type",
]
```

### 3. Preset Repository Integration

#### `src/claudefig/repositories/preset_repository.py`

**Add to filename map** in `_get_component_filename()`:
```python
filename_map = {
    ...
    FileType.NEW_TYPE: "example-file.ext",  # Expected filename in component folder
}
```

**Add preset definition** in `_load_builtin_presets()`:
```python
builtin_presets = [
    ...
    # New Type preset
    Preset(
        id="new_type:default",
        type=FileType.NEW_TYPE,
        name="Default",
        description="Description of this component type",
        source=PresetSource.BUILT_IN,
        tags=["standard", "examples"],
    ),
]
```

### 4. TUI Integration

#### `src/claudefig/tui/screens/file_instances.py`

**Add to all_file_types list** in `compose()`:
```python
all_file_types = [
    ...
    FileType.NEW_TYPE,
]
```

**Add to type_dirs mapping** (appears twice in file):
```python
type_dirs = {
    ...
    FileType.NEW_TYPE: "new_type",
}
```

#### `src/claudefig/tui/screens/overview.py`

**Add to type_priority** in `_file_sort_key()`:
```python
type_priority = {
    ...
    FileType.NEW_TYPE: 12,  # Choose appropriate priority number
}
```

### 5. Component Examples & Preset Definition

#### Create component folder structure:
```
src/presets/default/components/new_type/default/
├── example-file.ext
└── (other files as needed)
```

**Important**:
- Each component type should have ONE variant named `default/`
- Place example/template files inside the default folder
- Filename must match what's in `filename_map`

#### Update preset definition file:
**`src/presets/default/.claudefig.toml`**
```toml
[[components]]
type = "new_type"
name = "default"
path = ".claude/new-type/"  # or specific file path
enabled = false  # or true if should be enabled by default
```

### 6. Special Initialization Logic (Optional)

#### `src/claudefig/initializer.py`

For most components, no changes needed. The `_generate_directory_from_instance()` method handles directory-based components automatically.

**Only modify if:**
- Custom generation logic required
- Special file permissions needed (like statusline)
- Post-processing steps required

### 7. Validation Logic (Optional)

#### `src/claudefig/services/validation_service.py`

**Only needed for complex validation:**
```python
def validate_new_type_component(
    component_path: Path, ...
) -> ValidationResult:
    """Validate specific requirements for new component type."""
    result = ValidationResult(valid=True)
    # Custom validation logic
    return result
```

Then integrate in `file_instance_service.py`:
```python
# In validate_instance()
if instance.type == FileType.NEW_TYPE:
    custom_result = validate_new_type_component(...)
    # Merge results
```

### 8. Tests

#### `tests/test_models.py`

**Update FileType enum tests**:
```python
# In test_all_file_types_exist
expected_types = [
    ...
    "NEW_TYPE",
]

# In test_file_type_values
assert FileType.NEW_TYPE.value == "new_type"

# In test_display_name_property
assert FileType.NEW_TYPE.display_name == "Display Name"

# In test_default_path_property
assert FileType.NEW_TYPE.default_path == ".claude/new-type/"

# In test_supports_multiple_property
assert FileType.NEW_TYPE.supports_multiple  # or not, depending on type

# In test_is_directory_property (if directory-based)
assert FileType.NEW_TYPE.is_directory
```

#### `tests/factories.py`

**Add to type_paths mapping**:
```python
type_paths = {
    ...
    FileType.NEW_TYPE: ".claude/new-type/example.ext",
}
```

### 9. Documentation

#### `docs/CLI_REFERENCE.md`

**Add to Valid File Types list**:
```markdown
**Valid File Types:**
- ...
- `new_type` - Description of new component
```

## Verification Checklist

After implementing, verify:

- [ ] FileType enum includes new type
- [ ] All FileType properties updated (display_name, default_path, is_directory, etc.)
- [ ] Component directories created in user_config.py
- [ ] Structure validator includes component directory
- [ ] Preset definition exists in preset repository
- [ ] Filename mapping added
- [ ] TUI file_instances.py includes type (2 locations)
- [ ] TUI overview.py includes type priority
- [ ] Component folder created with default variant
- [ ] Preset .claudefig.toml includes component entry
- [ ] All tests updated and passing
- [ ] CLI documentation updated
- [ ] Clean up: Delete `~/.claudefig/` and test end-to-end
- [ ] Verify component appears in TUI dropdown
- [ ] Verify component generates correctly when toggled on
- [ ] Verify component validates correctly

## Common Pitfalls

1. **Forgetting type_dirs mapping**: Appears in TWO places in file_instances.py
2. **Mismatched names**: Ensure "new_type" (snake_case) used consistently
3. **Missing default variant**: Component folders must have `default/` subfolder
4. **Preset not registered**: Must add to both filename_map AND builtin_presets
5. **Tests incomplete**: Update ALL FileType tests, not just some

## Testing Your Changes

```bash
# 1. Clean slate
rm -rf ~/.claudefig
rm -rf sandbox/.claudefig.toml sandbox/.claude

# 2. Reinstall
pip install -e .

# 3. Run tests
pytest tests/test_models.py::TestFileTypeEnum -v

# 4. Test TUI
cd sandbox
claudefig

# 5. Verify:
# - New component appears in File Instances
# - Component dropdown shows "default" option
# - Toggling on generates files correctly
# - Component appears in overview
```

## Example: Adding "Plugins" Component

See `PLUGINS_SKILLS_IMPLEMENTATION.md` for a complete example of adding the Plugins and Skills components, including all changes made and issues encountered.

## Questions?

- Review existing components (e.g., COMMANDS, AGENTS) as reference implementations
- Check `models.py` FileType enum for current component list
- Examine `src/presets/default/components/` for component structure examples
