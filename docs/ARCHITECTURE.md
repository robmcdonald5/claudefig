# Architecture

## Table of Contents

- [System Overview](#system-overview)
- [Core Components](#core-components)
  - [1. Preset System (`preset_manager.py`)](#1-preset-system-preset_managerpy)
  - [2. File Instance System (`file_instance_manager.py`, `models.py`)](#2-file-instance-system-file_instance_managerpy-modelspy)
  - [3. Configuration System (`config.py`)](#3-configuration-system-configpy)
  - [4. TUI Interface (`tui/`)](#4-tui-interface-tui)
  - [5. CLI Interface (`cli.py`)](#5-cli-interface-clipy)
  - [6. Initializer (`initializer.py`)](#6-initializer-initializerpy)
  - [File Type Enum vs Strings?](#file-type-enum-vs-strings)
  - [Validation Strategy](#validation-strategy)
- [Data Flow](#data-flow)
- [State Synchronization Pattern (CRITICAL)](#state-synchronization-pattern-critical)
  - [The Correct Pattern](#the-correct-pattern)
  - [Common Operations](#common-operations)
  - [Why This Pattern?](#why-this-pattern)
  - [Antipatterns (DO NOT DO THIS)](#antipatterns-do-not-do-this)
  - [Implementation Guidelines](#implementation-guidelines)
  - [Real-World Examples](#real-world-examples)
- [TUI Architecture Patterns and Design Philosophy](#tui-architecture-patterns-and-design-philosophy)
  - [Base Classes and Inheritance](#base-classes-and-inheritance)
  - [Screen Lifecycle and Refresh Pattern](#screen-lifecycle-and-refresh-pattern)
  - [Widget Composition vs Inheritance](#widget-composition-vs-inheritance)
  - [Navigation Architecture](#navigation-architecture)
  - [State Management Strategy](#state-management-strategy)
  - [Code Organization Principles](#code-organization-principles)
- [Summary](#summary)
  - [Design Philosophy](#design-philosophy)

## System Overview

claudefig uses a **preset-based architecture** with **file instances** as the core abstraction:

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
│              │   (claudefig.toml)     │                    │
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
2. Presets location (`~/.claudefig/presets/`)

**Preset ID Format:** `{file_type}:{preset_name}`
- Example: `claude_md:backend`, `settings_json:default`

**Features:**
- Variable substitution
- Template inheritance (extends)
- Tags for discovery
- Multi-file presets (for directories)

**Architecture Note (2025):**
- Preset system migrated from JSON metadata files to directory-based structure
- Each preset is now a directory containing component files directly
- No separate `.json` metadata required - structure is self-describing
- Improved component discovery with dual-source support (global + preset-specific)

#### 2. File Instance System (`file_instance_manager.py`, `models.py`)

**Purpose:** Manage individual files to be generated.

**Key Classes:**
- `FileInstance` (dataclass) - Represents a file to generate
- `FileInstanceManager` - CRUD operations
- `FileType` (enum) - Supported file types

**Component Architecture:**
All component types are now **folder-based** (unified architecture as of v2.1):
- Each component is a directory containing template files
- No JSON metadata files required
- Consistent discovery pattern across all file types

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

**Supported File Types (12 total):**
- `claude_md`
- `settings_json`
- `settings_local_json`
- `gitignore`
- `commands`
- `agents`
- `hooks`
- `skills`
- `output_styles`
- `statusline`
- `plugins`
- `mcp`

**Features:**
- Multiple instances per file type (except single-instance types)
- Enable/disable without deletion
- Path conflict detection
- Preset existence validation
- **Dual-source component discovery** - Components can be sourced from:
  - Global: `~/.claudefig/components/{type}/`
  - Preset-specific: `~/.claudefig/presets/{preset_name}/components/{type}/`
  - Visual indicators: `(g)` for global, `(p)` for preset components

#### 3. Configuration System (`config.py`)

**Purpose:** Store and manage claudefig.toml configuration.

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
1. `claudefig.toml` in current directory (project config)
2. `~/.claudefig/config.toml` in home directory (user defaults)
3. Default config (hardcoded fallback)

#### 3.5 Component Discovery Service (`services/component_discovery_service.py`)

**Purpose:** Scan repositories to discover existing Claude Code components for preset creation.

**Added:** v1.2.0 (2025-11)

**Key Classes:**
- `ComponentDiscoveryService` - Main service for scanning repositories
- `DiscoveredComponent` - Represents a found component with metadata
- `DiscoveryResult` - Contains all discovered components and scan metrics

**Discovery Patterns:**
The service uses `rglob` (recursive glob) to scan for components:

| Component Type | Scan Pattern |
|----------------|--------------|
| CLAUDE.md | `**/CLAUDE.md`, `**/CLAUDE_*.md` |
| .gitignore | `.gitignore` |
| Settings | `.claude/settings.json`, `.claude/settings.local.json` |
| Slash Commands | `.claude/commands/*.md` |
| Sub-Agents | `.claude/agents/*.md` |
| Hooks | `.claude/hooks/*.py` |
| Output Styles | `.claude/output-styles/*.md` |
| Status Line | `.claude/statusline.sh` |
| MCP Configs | `.claude/mcp/*.json`, `.mcp.json` |
| Plugins | `.claude/plugins/*` |
| Skills | `.claude/skills/*` |

**Features:**
- Recursive scanning with configurable depth limits
- Duplicate name detection with automatic disambiguation
- Path validation and sanitization
- Scan timing metrics for performance monitoring
- Warning collection for ambiguous or problematic components

**Usage Flow:**
```
Repository Path → ComponentDiscoveryService.discover_components()
                          ↓
                  DiscoveryResult
                  ├── components: List[DiscoveredComponent]
                  ├── total_found: int
                  ├── scan_time_ms: float
                  ├── warnings: List[str]
                  └── has_warnings: bool
                          ↓
                  ConfigTemplateManager.create_preset_from_discovery()
                          ↓
                  New Preset in ~/.claudefig/presets/
```

**Integration Points:**
- TUI: Preset Wizard uses this for interactive component selection
- CLI: `presets create-from-repo` command uses this for batch scanning
- ConfigTemplateManager: Receives discovered components for preset creation

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
│   ├── file_instances.py     # All file instance management (single and multi)
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

**Architecture Note (2025):**
- The previously separate "Core Files" screen has been merged into the unified "File Instances" screen
- This consolidation provides a single location for managing all file types with a tabbed interface
- Both multi-instance types (CLAUDE.md, commands, etc.) and single-instance types (settings.json, statusline) are now managed in one screen
- Improved UX with consistent navigation and reduced cognitive load

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
self.refresh(recompose=True)
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
┌───────────────────────────────────────────────────┐
│         Config Panel Grid                         │
│  ┌──────────────────────┐  ┌───────────────────┐  │
│  │   Project Overview   │  │   Init Settings   │  │
│  └──────────────────────┘  └───────────────────┘  │
│  ┌──────────────────────┐                         │
│  │   File Instances     │                         │
│  └──────────────────────┘                         │
└───────────────────────────────────────────────────┘
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
Config.load() from claudefig.toml
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
3. `claudefig.toml` file (on disk)

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

**Disk (claudefig.toml)** provides:
- Persistent storage across sessions
- Human-readable configuration
- Version control friendly format

These layers serve different purposes and must be explicitly synchronized. This design provides flexibility (in-memory operations are fast) while maintaining data integrity (changes are persisted).

#### Antipatterns (DO NOT DO THIS)

**Only updating manager:**
```python
self.instance_manager.add_instance(instance)
# MISSING: No sync to config!
# Result: Changes lost on next app launch
```

**Only updating config:**
```python
self.config.add_file_instance(instance.to_dict())
self.config.save()
# MISSING: Manager not updated!
# Result: UI shows stale data until refresh
```

**Partial sync:**
```python
self.instance_manager.enable_instance(instance_id)
self.config.save()  # Config still has old data!
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

**TUI - File Instances Screen (unified for all file types):**

The `FileInstancesScreen` manages both multi-instance and single-instance file types in a single tabbed interface:

```python
class FileInstancesScreen(BaseScreen, SystemUtilityMixin):
    def __init__(self, config_data, config_repo, instances_dict, **kwargs):
        super().__init__(**kwargs)
        self.config_data = config_data
        self.config_repo = config_repo
        self.instances_dict = instances_dict

    def on_compact_single_instance_control_toggle_changed(self, event):
        # Handle single-instance types (settings.json, statusline, etc.)
        if enabled and not instances:
            new_instance = FileInstance(...)
            file_instance_service.add_instance(self.instances_dict, new_instance, ...)
            self.sync_instances_to_config()

    def _toggle_instance(self, instance_id: str):
        # Handle multi-instance types (CLAUDE.md, commands, etc.)
        instance = file_instance_service.get_instance(self.instances_dict, instance_id)
        instance.enabled = not instance.enabled
        file_instance_service.update_instance(self.instances_dict, instance, ...)

        self.sync_instances_to_config()

        status = "enabled" if instance.enabled else "disabled"
        self.notify(f"{instance.type.display_name} instance {status}")

        self.refresh(recompose=True)
```

**CLI - Enable Instance (manual pattern):**

The CLI doesn't use mixins, so it follows the manual three-step pattern:

```python
def enable_instance(instance_id: str):
    if instance_manager.enable_instance(instance_id):
        # Manual sync in CLI code
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

**Modern Approach (Recommended):**
```python
def after_data_change(self):
    self.refresh(recompose=True)
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
- Small, focused widgets (`FileInstanceItem`, `OverlayDropdown`)
- Screens compose widgets together
- Widgets use reactive attributes and button events for communication

**Example:**
```python
# FileInstanceItem uses reactive attributes for smooth updates
class FileInstanceItem(Container):
    is_enabled = reactive(True, init=False)
    file_path = reactive("", init=False)

# Parent screen handles button presses
def on_button_pressed(self, event: Button.Pressed):
    if event.button.id.startswith("toggle-"):
        instance_id = event.button.id.replace("toggle-", "")
        self._toggle_instance(instance_id)
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
- Screens: `*Screen` (e.g., `OverviewScreen`, `FileInstancesScreen`)
- Panels: `*Panel` (e.g., `ConfigPanel`, `PresetsPanel`)
- Widgets: Descriptive noun (e.g., `FileInstanceItem`, `OverlayDropdown`)
- Mixins: `*Mixin` (e.g., `BackButtonMixin`, `FileInstanceMixin`)

**CSS Class Conventions:**
- Screen-level: `screen-*` (e.g., `screen-title`, `screen-footer`)
- Dialog-level: `dialog-*` (e.g., `dialog-header`, `dialog-actions`)
- Panel-level: `panel-*` (e.g., `panel-title`, `panel-subtitle`)
- Component-level: Component-specific (e.g., `instance-enabled`, `preset-name`)

**Non-Goals:**

- **Over-abstraction:** Don't create base classes for 1-2 users
- **Framework Fighting:** Don't work against Textual patterns
- **Premature Optimization:** Profile before optimizing
- **Feature Creep:** Keep TUI focused on config management

---

## Summary

### Design Philosophy

The architecture prioritizes:

1. **Explicit over Implicit** - State synchronization is explicit and visible
2. **Composition over Inheritance** - Widgets compose, base classes provide structure
3. **Framework Alignment** - Works with Textual patterns, not against them
4. **Progressive Enhancement** - Start simple, add complexity only when needed
5. **Developer Empathy** - Make the right thing easy, wrong thing hard

---

**Last Updated:** 2025-11-21
**Schema Version:** 2.0
**TUI Architecture Version:** 3 (Base Classes + Mixins)
**Services Version:** 1.2.0 (Component Discovery)