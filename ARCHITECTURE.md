## Architecture

### System Overview

claudefig v2.0 uses a **preset-based architecture** with **file instances** as the core abstraction:

```
┌─────────────────────────────────────────────────────────────┐
│                         claudefig                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐      ┌──────────────┐      ┌─────────────┐  │
│  │   TUI    │◄────►│     Core     │◄────►│     CLI     │  │
│  │ (Textual)│      │   Managers   │      │   (Click)   │  │
│  └──────────┘      └──────────────┘      └─────────────┘  │
│                           │                                │
│                           ▼                                │
│              ┌────────────────────────┐                    │
│              │   Preset Manager       │                    │
│              │   - Built-in presets   │                    │
│              │   - User presets       │                    │
│              │   - Project presets    │                    │
│              └────────────────────────┘                    │
│                           │                                │
│                           ▼                                │
│              ┌────────────────────────┐                    │
│              │ File Instance Manager  │                    │
│              │   - Add/Remove/Update  │                    │
│              │   - Enable/Disable     │                    │
│              │   - Validation         │                    │
│              └────────────────────────┘                    │
│                           │                                │
│                           ▼                                │
│              ┌────────────────────────┐                    │
│              │    Initializer         │                    │
│              │   - File generation    │                    │
│              │   - Template rendering │                    │
│              └────────────────────────┘                    │
│                           │                                │
│                           ▼                                │
│              ┌────────────────────────┐                    │
│              │    Configuration       │                    │
│              │   (.claudefig.toml)    │                    │
│              └────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Preset System (`preset_manager.py`)

**Purpose:** Manage reusable templates for different file types.

**Key Classes:**
- `Preset` (dataclass) - Represents a template
- `PresetManager` - CRUD operations for presets
- `PresetSource` (enum) - Built-in, user, or project

**Location Hierarchy:**
1. Built-in presets (internal to package)
2. User presets (`~/.claudefig/presets/`)
3. Project presets (`.claudefig/presets/`)

**Preset ID Format:** `{file_type}:{preset_name}`
- Example: `claude_md:backend`, `settings_json:default`

**Features:**
- Variable substitution
- Template inheritance (extends)
- Tags for discovery
- Multi-file presets (for directories)

#### 2. File Instance System (`file_instance_manager.py`, `models.py`)

**Purpose:** Manage individual files to be generated.

**Key Classes:**
- `FileInstance` (dataclass) - Represents a file to generate
- `FileInstanceManager` - CRUD operations
- `FileType` (enum) - Supported file types

**File Instance Structure:**
```python
FileInstance(
    id="claude_md-backend",           # Unique identifier
    type=FileType.CLAUDE_MD,          # What type of file
    preset="claude_md:backend",       # Which preset to use
    path="CLAUDE.md",                 # Where to create it
    enabled=True,                     # Is it active?
    variables={"project_name": "..."}  # Preset variable overrides
)
```

**Supported File Types (10 total):**
- `claude_md` - CLAUDE.md project instructions
- `settings_json` - Team settings (.claude/settings.json)
- `settings_local_json` - Personal settings (.claude/settings.local.json)
- `gitignore` - Git ignore entries
- `commands` - Slash commands directory
- `agents` - Custom agents directory
- `hooks` - Hook scripts directory
- `output_styles` - Output styles directory
- `statusline` - Status line script
- `mcp` - MCP server configs directory

**Features:**
- Multiple instances per file type (except single-instance types)
- Enable/disable without deletion
- Path conflict detection
- Preset existence validation

#### 3. Configuration System (`config.py`)

**Purpose:** Store and manage .claudefig.toml configuration.

**Schema Version:** 2.0 (breaking change from 1.x)

**Config Structure:**
```toml
[claudefig]
version = "2.0"
schema_version = "2.0"

[init]
overwrite_existing = false

[[files]]  # Array of file instances
id = "claude_md-default"
type = "claude_md"
preset = "claude_md:default"
path = "CLAUDE.md"
enabled = true

[custom]
template_dir = ""
presets_dir = ""
```

**Key Methods:**
- `get(key)` - Dot-notation key access
- `set(key, value)` - Dot-notation key setting
- `get_file_instances()` - Get file instance array
- `add_file_instance(instance)` - Add instance to config

**Search Path:**
1. `.claudefig.toml` in current directory (project config)
2. `~/.claudefig.toml` in home directory (user defaults)
3. Default config (hardcoded fallback)

#### 4. TUI Interface (`tui/`)

**Purpose:** Interactive terminal user interface using Textual framework.

The TUI is organized into a modular, layered architecture with clear separation of concerns:

```
tui/
├── app.py                    # Main application entry point
├── base/                     # Reusable base classes and mixins
│   ├── modal_screen.py       # Base class for modal dialogs
│   └── mixins.py             # Common functionality mixins
├── panels/                   # Content panels for main sections
│   ├── config_panel.py       # Configuration management menu
│   ├── initialize_panel.py   # Project initialization
│   ├── presets_panel.py      # Preset browsing and management
│   └── content_panel.py      # Dynamic panel orchestrator
├── screens/                  # Full-screen views
│   ├── overview.py           # Project health and statistics
│   ├── core_files.py         # Single-instance file management
│   ├── file_instances.py     # Multi-instance file management
│   ├── project_settings.py   # Initialization settings
│   ├── file_instance_edit.py # Add/edit file instance modal
│   ├── apply_preset.py       # Preset application modal
│   ├── create_preset.py      # Preset creation modal
│   └── preset_details.py     # Preset details modal
└── widgets/                  # Reusable UI components
    ├── compact_single_instance.py  # Inline file control
    ├── file_instance_item.py       # File instance display card
    └── overlay_dropdown.py         # Collapsible overlay sections
```

**Architecture Layers:**

1. **Application Layer** (`app.py`, `content_panel.py`)
   - Main application container with navigation
   - Panel orchestration and routing
   - Global keyboard shortcuts and state

2. **Base Layer** (`base/`)
   - `BaseModalScreen` - Standard modal dialog pattern
   - `BackButtonMixin` - Consistent back navigation
   - `FileInstanceMixin` - State synchronization helper

3. **Panel Layer** (`panels/`)
   - Container views for main menu sections
   - Initialize, Presets, and Config panels
   - Panel-to-screen navigation

4. **Screen Layer** (`screens/`)
   - Full-screen views pushed onto screen stack
   - Config management screens (overview, settings, etc.)
   - Modal dialogs for user input

5. **Widget Layer** (`widgets/`)
   - Reusable components used across screens
   - Custom controls and display elements

**Key Design Patterns:**

**1. Modal Dialog Pattern (BaseModalScreen):**
All modal dialogs inherit from `BaseModalScreen` which provides:
- Standard escape/backspace/left/right navigation
- Consistent layout (header → content → actions)
- Template methods for customization (`compose_title()`, `compose_content()`, `compose_actions()`)

```python
class MyModalScreen(BaseModalScreen):
    def compose_title(self) -> str:
        return "My Modal"

    def compose_content(self) -> ComposeResult:
        yield Label("Content goes here")

    def compose_actions(self) -> ComposeResult:
        yield Button("OK", id="btn-ok", variant="primary")
        yield Button("Cancel", id="btn-cancel")
```

**2. Mixin Pattern for Shared Functionality:**

**BackButtonMixin** - Provides standard back button behavior:
```python
class MyScreen(Screen, BackButtonMixin):
    def compose(self) -> ComposeResult:
        # ... screen content
        yield from self.compose_back_button()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self.handle_back_button(event):
            return
        # ... other button handling
```

**FileInstanceMixin** - Simplifies state synchronization:
```python
class MyScreen(Screen, FileInstanceMixin):
    def some_handler(self):
        self.instance_manager.add_instance(instance)
        self.sync_instances_to_config()  # Handles both config update and save
```

**3. Screen Refresh Pattern:**
Screens use Textual's built-in `refresh(recompose=True)` instead of manual screen stack manipulation:
```python
# After modifying data
self.instance_manager.update_instance(instance)
self.sync_instances_to_config()
self.refresh(recompose=True)  # Triggers compose() to re-render with new data
```

**Main Application Flow:**

```
┌─────────────────────────────────────────────────┐
│             MainScreen (app.py)                 │
│  ┌───────────────┐  ┌───────────────────────┐  │
│  │  Menu Panel   │  │   Content Panel       │  │
│  │               │  │  (Dynamic)            │  │
│  │ • Initialize  │  │                       │  │
│  │ • Presets     │──► InitializePanel       │  │
│  │ • Config      │  │ PresetsPanel          │  │
│  │ • Exit        │  │ ConfigPanel           │  │
│  └───────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────┘
                    │
                    │ push_screen()
                    ▼
┌─────────────────────────────────────────────────┐
│         Config Panel Grid (4 buttons)           │
│  ┌───────────────┐  ┌───────────────────────┐  │
│  │   Overview    │  │   Init Settings       │  │
│  └───────────────┘  └───────────────────────┘  │
│  ┌───────────────┐  ┌───────────────────────┐  │
│  │  Core Files   │  │   File Instances      │  │
│  └───────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────┘
                    │
                    │ push_screen()
                    ▼
┌─────────────────────────────────────────────────┐
│      Individual Screens (e.g. Overview)         │
│                                                 │
│  • Display data                                 │
│  • Handle user input                            │
│  • Push modal dialogs as needed                │
│  • Update state via mixins                      │
│  • Refresh view on changes                      │
└─────────────────────────────────────────────────┘
```

**State Management:**

Each screen maintains references to core managers:
- `self.config` - Configuration object for settings
- `self.instance_manager` - In-memory file instance CRUD
- `self.preset_manager` - Preset discovery and loading

State synchronization follows the three-layer pattern (see State Synchronization Pattern section), simplified by `FileInstanceMixin`.

**Navigation:**

- **Keyboard:** Arrow keys for directional navigation, Escape/Backspace for back
- **Screen Stack:** Textual's built-in screen stack (push/pop)
- **Focus Management:** Automatic focus on first interactive element
- **2D Navigation:** Config panel uses grid-based navigation

#### 5. CLI Interface (`cli.py`)

**Purpose:** Command-line interface using Click.

**Command Groups:**
- `claudefig` - Main entry point (launches TUI if no subcommand)
- `claudefig config` - Configuration management
- `claudefig files` - File instance management
- `claudefig presets` - Preset management

**Key Commands:**
- `init` - Initialize repository
- `interactive` - Launch TUI
- `config get/set/list` - Config management
- `files add/remove/enable/disable/list` - Instance management
- `presets list/show` - Preset browsing

#### 6. Initializer (`initializer.py`)

**Purpose:** Generate files based on configuration.

**Key Methods:**
- `initialize(repo_path, force)` - Main entry point
- `_create_file_from_instance(instance)` - Generate single file
- `_render_template(preset, variables)` - Template rendering

**File Generation Process:**
1. Load enabled file instances from config
2. For each instance:
   - Resolve preset
   - Merge preset variables with instance variables
   - Render template
   - Write to target path
3. Handle special cases (gitignore append, directory creation)

### Design Decisions

#### Why Presets + File Instances?

**Problem:** v1.x used feature flags (e.g., `create_settings=true`). This was:
- Inflexible (one size fits all)
- Limited to one file per type
- No customization without editing templates
- Hard to share configurations

**Solution:** Two-level system:
1. **Presets** = Reusable templates (what content)
2. **File Instances** = Specific files (where and with what values)

**Benefits:**
- Multiple files of same type (multiple CLAUDE.md files)
- Choose different templates per instance
- Override variables per instance
- Share presets independently of instances

#### Why Schema Version 2.0?

**Breaking Changes:**
- Removed feature flags (`claude.create_*`)
- Introduced `[[files]]` array
- Changed config structure significantly

**Migration Path:**
- Users can run `claudefig migrate v1-to-v2` (planned)
- Old configs won't break (fallback to defaults)
- Clear error messages

#### Why Textual for TUI?

**Alternatives Considered:**
- curses - Too low-level
- urwid - Less modern
- Rich (CLI only) - No interactivity

**Textual Chosen:**
- Modern Python async/await
- Rich integration (styling)
- Widget system
- Active development
- Good documentation

#### Why Click for CLI?

**Alternatives Considered:**
- argparse - Too verbose
- typer - Opinionated

**Click Chosen:**
- Industry standard
- Great documentation
- Nested command groups
- Easy option/argument handling

#### File Type Enum vs Strings?

**Choice:** Use `FileType` enum

**Reasoning:**
- Type safety (Pylance/mypy)
- Autocomplete in IDE
- Centralized display names
- Default path definitions
- Behavioral flags (is_directory, supports_multiple)

#### Validation Strategy

**Approach:** Multi-level validation

1. **Schema Level** - TOML structure valid
2. **Instance Level** - Each file instance valid
3. **Preset Level** - Referenced presets exist
4. **Path Level** - Paths are safe and valid
5. **Conflict Level** - No duplicate paths

**Returns:** `ValidationResult` with errors/warnings

**Benefits:**
- Fail early with clear messages
- Warnings don't block (e.g., path conflicts)
- User can fix issues before generation

### Key Files Reference

**Core System Files:**

| File | Purpose | LOC | Key Classes |
|------|---------|-----|-------------|
| `models.py` | Data models and enums | ~280 | FileType, Preset, FileInstance, ValidationResult |
| `config.py` | TOML config management | ~190 | Config |
| `preset_manager.py` | Preset CRUD operations | ~300 | PresetManager |
| `file_instance_manager.py` | Instance CRUD operations | ~350 | FileInstanceManager |
| `initializer.py` | File generation engine | ~250 | Initializer |
| `cli.py` | Command-line interface | ~750 | Click command groups |

**TUI Files:**

| File | Purpose | LOC | Key Classes |
|------|---------|-----|-------------|
| `tui/app.py` | Main application | ~300 | MainScreen |
| `tui/base/modal_screen.py` | Modal dialog base class | ~108 | BaseModalScreen |
| `tui/base/mixins.py` | Reusable functionality | ~115 | BackButtonMixin, FileInstanceMixin |
| `tui/panels/config_panel.py` | Config menu | ~208 | ConfigPanel |
| `tui/panels/presets_panel.py` | Preset browser | ~290 | PresetsPanel |
| `tui/panels/initialize_panel.py` | Project initialization | ~233 | InitializePanel |
| `tui/screens/overview.py` | Project overview | ~250 | OverviewScreen |
| `tui/screens/core_files.py` | Single-instance files | ~156 | CoreFilesScreen |
| `tui/screens/file_instances.py` | Multi-instance files | ~241 | FileInstancesScreen |
| `tui/screens/project_settings.py` | Init settings | ~97 | ProjectSettingsScreen |
| `tui/widgets/compact_single_instance.py` | Inline file control | ~216 | CompactSingleInstanceControl |
| `tui/widgets/file_instance_item.py` | File instance card | ~52 | FileInstanceItem |
| `tui/widgets/overlay_dropdown.py` | Collapsible section | ~213 | OverlayDropdown |

### Data Flow

**Adding a File Instance (TUI):**
```
User clicks "Add Instance"
    ↓
FileInstanceDialog shown
    ↓
User selects file type, preset, path
    ↓
ValidationResult = FileInstanceManager.validate_instance()
    ↓
If valid: FileInstanceManager.add_instance()
    ↓
Config.add_file_instance(instance.to_dict())
    ↓
Config.save()
    ↓
TUI refreshes FilesPanel
```

**Generating Files (CLI):**
```
$ claudefig init --force
    ↓
Config.load() from .claudefig.toml
    ↓
Initializer.initialize(repo_path, force=True)
    ↓
For each enabled file instance:
    ↓
    PresetManager.get_preset(instance.preset)
        ↓
    Merge preset.variables + instance.variables
        ↓
    Render template with variables
        ↓
    Write to instance.path
    ↓
Success/Failure
```

### State Synchronization Pattern **CRITICAL**

**Problem:** The system maintains state in THREE places that must stay synchronized:
1. `FileInstanceManager` (in-memory instances)
2. `Config` (in-memory TOML data)
3. `.claudefig.toml` file (on disk)

**Critical Rule:** Whenever `FileInstanceManager` is modified, you **MUST** sync all three layers.

#### The Correct Pattern

```python
# After ANY modification to instance_manager:
# 1. Modify the instance_manager
self.instance_manager.add_instance(instance)  # or update, remove, enable, disable

# 2. Sync manager → config
self.config.set_file_instances(self.instance_manager.save_instances())

# 3. Sync config → disk
self.config.save()
```

#### Common Operations

**Adding an instance:**
```python
# 1. Add to manager
result = self.instance_manager.add_instance(new_instance)
if result.valid:
    # 2. Sync to config and save
    self.config.set_file_instances(self.instance_manager.save_instances())
    self.config.save()
    # 3. Optionally notify user
    self.notify(f"Added {instance.type.display_name} instance", severity="information")
```

**Updating an instance (enable/disable, preset change, etc):**
```python
# 1. Modify instance and update in manager
instance.enabled = new_value  # or instance.preset = new_preset
self.instance_manager.update_instance(instance)

# 2. Sync to config and save
self.config.set_file_instances(self.instance_manager.save_instances())
self.config.save()
```

**Removing an instance:**
```python
# 1. Remove from manager
if self.instance_manager.remove_instance(instance_id):
    # 2. Sync to config and save
    self.config.set_file_instances(self.instance_manager.save_instances())
    self.config.save()
```

#### Why This Pattern?

The three-layer architecture exists because each layer has a distinct purpose:

**FileInstanceManager** is optimized for:
- In-memory CRUD operations with validation
- Fast instance lookups by ID or type
- Business logic (conflict detection, preset validation)

**Config** is optimized for:
- TOML serialization and deserialization
- Dot-notation key access (`config.get("init.overwrite")`)
- File I/O with atomic writes

**Disk (.claudefig.toml)** provides:
- Persistent storage across sessions
- Human-readable configuration
- Version control friendly format

These layers serve different purposes and must be explicitly synchronized. This design provides flexibility (in-memory operations are fast) while maintaining data integrity (changes are persisted).

**Modern TUI Implementation:**

The TUI now uses `FileInstanceMixin` to simplify this pattern. Instead of three lines of boilerplate, screens can call a single method:

```python
# Old pattern (still works, but verbose):
self.instance_manager.add_instance(instance)
self.config.set_file_instances(self.instance_manager.save_instances())
self.config.save()

# New pattern with mixin (recommended):
self.instance_manager.add_instance(instance)
self.sync_instances_to_config()  # Handles steps 2 and 3 automatically
```

The mixin ensures developers can't forget the synchronization steps while keeping the code clean and maintainable.

#### Antipatterns (DO NOT DO THIS)

❌ **Only updating manager:**
```python
self.instance_manager.add_instance(instance)
# MISSING: No sync to config!
# Result: Changes lost on next app launch
```

❌ **Only updating config:**
```python
self.config.add_file_instance(instance.to_dict())
self.config.save()
# MISSING: Manager not updated!
# Result: UI shows stale data until refresh
```

❌ **Partial sync:**
```python
self.instance_manager.enable_instance(instance_id)
self.config.save()  # ❌ Config still has old data!
# MISSING: self.config.set_file_instances(...)
```

#### Implementation Guidelines

When implementing features that modify file instances, developers must ensure proper state synchronization. Any code path that modifies the `FileInstanceManager` (through `add_instance()`, `update_instance()`, `remove_instance()`, or similar operations) must also update the `Config` and persist to disk.

**In TUI code**, use the `FileInstanceMixin`:
1. Inherit from both `Screen` and `FileInstanceMixin`
2. Pass `config` and `instance_manager` to `__init__`
3. After any manager modification, call `self.sync_instances_to_config()`

**In CLI code**, follow the manual pattern:
1. Modify the instance manager
2. Call `config.set_file_instances(instance_manager.save_instances())`
3. Call `config.save()`

This ensures changes are never lost and the UI always reflects the current state.

#### Real-World Examples

**TUI - Core Files Screen (with FileInstanceMixin):**

The `CoreFilesScreen` inherits from both `Screen` and `FileInstanceMixin`:

```python
class CoreFilesScreen(Screen, BackButtonMixin, FileInstanceMixin):
    def __init__(self, config, instance_manager, preset_manager, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.instance_manager = instance_manager
        self.preset_manager = preset_manager

    def on_compact_single_instance_control_toggle_changed(self, event):
        # ... create or find instance ...
        if enabled and not instance:
            new_instance = FileInstance(...)
            self.instance_manager.add_instance(new_instance)

            # ✅ Sync using mixin helper
            self.sync_instances_to_config()
```

**TUI - File Instances Screen (with FileInstanceMixin):**

```python
class FileInstancesScreen(Screen, BackButtonMixin, FileInstanceMixin):
    def _toggle_instance(self, instance_id: str):
        instance = self.instance_manager.get_instance(instance_id)
        instance.enabled = not instance.enabled
        self.instance_manager.update_instance(instance)

        # ✅ Sync using mixin helper
        self.sync_instances_to_config()

        status = "enabled" if instance.enabled else "disabled"
        self.notify(f"{instance.type.display_name} instance {status}")

        # ✅ Modern refresh pattern
        self.refresh(recompose=True)
```

**CLI - Enable Instance (manual pattern):**

The CLI doesn't use mixins, so it follows the manual three-step pattern:

```python
def enable_instance(instance_id: str):
    if instance_manager.enable_instance(instance_id):
        # ✅ Manual sync in CLI code
        cfg.set_file_instances(instance_manager.save_instances())
        cfg.save(config_path)
        console.print("[green]Enabled file instance[/green]")
```

These examples show the evolution from verbose manual synchronization to the cleaner mixin-based approach in the TUI, while maintaining the explicit pattern in CLI code where mixins aren't available.

---

### TUI Architecture Patterns and Design Philosophy

The TUI architecture follows several key principles to ensure maintainability, consistency, and developer productivity.

#### Base Classes and Inheritance

**Philosophy:** Reduce boilerplate and enforce consistency through inheritance.

The TUI uses a layered base class approach:

1. **BaseModalScreen** - All modal dialogs inherit from this base class
   - Provides standard BINDINGS for escape/backspace/left/right
   - Enforces consistent modal layout (header → content → actions)
   - Uses template method pattern for customization
   - Eliminates 15-20 lines of boilerplate per modal

2. **Mixins** - Composable functionality for screens
   - `BackButtonMixin` - Standard back button behavior (~10 lines saved per screen)
   - `FileInstanceMixin` - State synchronization helper (~6 lines saved per operation)
   - Multiple inheritance allows screens to pick needed functionality

**Design Rationale:**

- **DRY Principle:** Common patterns appear once in base classes
- **Pit of Success:** Developers can't forget critical steps (like state sync)
- **Consistency:** All modals behave the same, all screens have back buttons
- **Maintainability:** Fix bugs once in base class, all inheritors benefit

#### Screen Lifecycle and Refresh Pattern

**Traditional Approach (Antipattern):**
```python
def _refresh_screen(self):
    self.app.pop_screen()  # ❌ Destroys screen, loses focus
    self.app.push_screen(NewScreenInstance(...))  # ❌ Creates new instance
```

**Modern Approach (Recommended):**
```python
def after_data_change(self):
    self.refresh(recompose=True)  # ✅ Textual built-in, maintains state
```

**Benefits:**
- Preserves screen stack position
- Maintains focus state when possible
- Cleaner code (1 line vs 5 lines)
- Follows Textual framework best practices
- Better performance (no screen stack manipulation)

#### Widget Composition vs Inheritance

The TUI uses **composition over inheritance** for widgets:

**Approach:**
- Small, focused widgets (`FileInstanceItem`, `CompactSingleInstanceControl`)
- Screens compose widgets together
- Widgets communicate via Textual messages (events)

**Example:**
```python
# CompactSingleInstanceControl posts messages
self.post_message(self.ToggleChanged(file_type, enabled))

# Parent screen handles messages
def on_compact_single_instance_control_toggle_changed(self, event):
    # Handle toggle logic
    pass
```

**Benefits:**
- Loose coupling between components
- Widgets are reusable across screens
- Easy to test widgets in isolation
- Clear data flow (events bubble up)

#### Navigation Architecture

The TUI implements a hierarchical navigation model:

```
Main Menu → Panel → Screen → Modal
    ↓         ↓       ↓        ↓
  Fixed    Dynamic  Stack   Dialog
```

**Navigation Layers:**

1. **Main Menu** (Fixed)
   - Always visible on left
   - Initialize, Presets, Config, Exit
   - Switches content panel

2. **Content Panel** (Dynamic)
   - Changes based on menu selection
   - Initialize, Presets, or Config panel
   - Can push screens onto stack

3. **Screen Stack** (Push/Pop)
   - Full-screen views
   - Overview, Settings, Core Files, File Instances
   - Can push modal dialogs

4. **Modal Dialogs** (Overlay)
   - Add/Edit file instances
   - Apply presets
   - Create presets
   - Always dismissible with escape

**Navigation Patterns:**

- **Escape/Backspace:** Always goes back one level
- **Arrow Keys:** Navigate within current context
- **Enter:** Select/activate focused element
- **Screen Stack:** Managed by Textual, automatic cleanup

#### State Management Strategy

The TUI maintains state at multiple levels:

**1. Application State** (`app.py`)
- Current menu selection
- Current panel
- Screen stack

**2. Manager State** (passed to screens)
- `config` - Configuration object
- `instance_manager` - File instances
- `preset_manager` - Available presets

**3. Screen State** (local to each screen)
- UI state (expanded dropdowns, selected tab)
- Validation errors/warnings
- Temporary form data

**State Flow:**
```
User Action → Screen Handler → Manager Update → Config Sync → Disk Save
                                     ↓
                                Screen Refresh
```

#### Code Organization Principles

**File Organization:**
- `base/` - Shared infrastructure (never screen-specific)
- `panels/` - Top-level sections (visible in main menu)
- `screens/` - Full-screen views (pushed onto stack)
- `widgets/` - Reusable components (used by screens)

**Naming Conventions:**
- Screens: `*Screen` (e.g., `OverviewScreen`, `CoreFilesScreen`)
- Panels: `*Panel` (e.g., `ConfigPanel`, `PresetsPanel`)
- Widgets: Descriptive noun (e.g., `FileInstanceItem`, `OverlayDropdown`)
- Mixins: `*Mixin` (e.g., `BackButtonMixin`, `FileInstanceMixin`)

**CSS Class Conventions:**
- Screen-level: `screen-*` (e.g., `screen-title`, `screen-footer`)
- Dialog-level: `dialog-*` (e.g., `dialog-header`, `dialog-actions`)
- Panel-level: `panel-*` (e.g., `panel-title`, `panel-subtitle`)
- Component-level: Component-specific (e.g., `instance-enabled`, `preset-name`)

#### Architecture Evolution

The TUI architecture has evolved through several refactoring phases:

**Phase 1 - Initial Implementation:**
- Monolithic screen classes
- Duplicated modal code
- Manual state synchronization everywhere
- ~3,500 LOC

**Phase 2 - Component Extraction:**
- Split screens into panels
- Created reusable widgets
- Improved CSS organization
- ~3,200 LOC

**Phase 3 - Base Classes (Current):**
- Introduced `BaseModalScreen`
- Created mixins for common patterns
- Removed dead code (3 unused widgets)
- Standardized refresh pattern
- ~2,900 LOC with better architecture

**Metrics:**
- 17% code reduction from peak
- 4 modal screens now consistent
- 7 state sync locations simplified
- 0 instances of forgotten state sync

#### Future Architecture Considerations

**Potential Improvements:**

1. **Reactive State Management**
   - Consider `reactive` attributes for auto-refresh
   - Would reduce manual `refresh(recompose=True)` calls
   - More Textual-idiomatic approach

2. **Screen Factory Pattern**
   - Centralize screen creation logic
   - Ensure managers are always passed correctly
   - Reduce duplicate initialization code

3. **Command Pattern for Actions**
   - Encapsulate user actions (Add, Edit, Remove)
   - Easier undo/redo implementation
   - Better testing and logging

4. **Screen Caching**
   - Cache frequently visited screens
   - Faster navigation
   - Preserve scroll position

**Non-Goals:**

- **Over-abstraction:** Don't create base classes for 1-2 users
- **Framework Fighting:** Don't work against Textual patterns
- **Premature Optimization:** Profile before optimizing
- **Feature Creep:** Keep TUI focused on config management

---

### Testing Strategy

**Unit Tests:**
- Config get/set operations
- Preset manager CRUD
- File instance manager CRUD
- Validation logic
- Path safety checks

**Integration Tests:**
- Full init workflow
- TUI interactions (Textual testing)
- CLI command execution
- Config migration

**Test Files:**
- `tests/test_config.py`
- `tests/test_preset_manager.py`
- `tests/test_file_instance_manager.py`
- `tests/test_initializer.py`
- `tests/test_tui.py`
- `tests/test_cli.py`

---

## Summary

### Architecture Highlights

**claudefig v2.0** is built on a clean, modular architecture with clear separation of concerns:

1. **Two-Level Configuration System**
   - Presets define templates (what content)
   - File Instances define specific files (where and with what values)
   - Enables flexibility and reusability

2. **Three-Layer State Management**
   - FileInstanceManager (in-memory CRUD with validation)
   - Config (TOML serialization and dot-notation access)
   - .claudefig.toml (persistent disk storage)
   - Explicit synchronization ensures data integrity

3. **Dual Interface Design**
   - **TUI:** Interactive Textual-based interface with panels, screens, and modals
   - **CLI:** Command-line interface with Click for scripting and automation
   - Both interfaces share core managers for consistency

4. **Modern TUI Architecture**
   - Base classes reduce boilerplate and enforce consistency
   - Mixins provide composable functionality
   - Widget composition enables reusability
   - Hierarchical navigation with clear patterns

### Key Strengths

**Maintainability:**
- Clear file organization (base/, panels/, screens/, widgets/)
- Consistent naming conventions
- Well-documented patterns and antipatterns
- DRY principle applied through base classes

**Extensibility:**
- New file types easy to add (enum + templates)
- New presets require no code changes
- New screens follow established patterns
- Mixin pattern allows functionality composition

**User Experience:**
- TUI and CLI feature parity
- Real-time validation feedback
- Consistent keyboard navigation
- Helpful error messages

**Developer Experience:**
- Type safety with enums and dataclasses
- Template method pattern guides development
- Mixins prevent common mistakes
- Clear state flow

### Design Philosophy

The architecture prioritizes:

1. **Explicit over Implicit** - State synchronization is explicit and visible
2. **Composition over Inheritance** - Widgets compose, base classes provide structure
3. **Framework Alignment** - Works with Textual patterns, not against them
4. **Progressive Enhancement** - Start simple, add complexity only when needed
5. **Developer Empathy** - Make the right thing easy, wrong thing hard

### Version History

- **v1.x:** Feature flag-based configuration, single file per type
- **v2.0:** Preset + instance architecture, multiple files per type, TUI interface
- **v2.1 (current):** Refactored TUI with base classes, mixins, and consistent patterns

---

**Last Updated:** 2025-01-10
**Schema Version:** 2.0
**TUI Architecture Version:** 3 (Base Classes + Mixins)