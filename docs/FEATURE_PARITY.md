# TUI/CLI Feature Parity Matrix

**Purpose:** Track feature parity between TUI and CLI interfaces as required by CLAUDE.md.

**Last Updated:** 2025-01-30

## Parity Requirement

Per CLAUDE.md line 36-37:
> Every feature that can be performed in the TUI must also be available via CLI commands, and vice versa.

## Feature Categories

### 1. Project Initialization

| Feature | TUI | CLI | Notes |
|---------|-----|-----|-------|
| Initialize project with default preset | ✓ (Initialize Panel) | ✓ (`init`) | Full parity |
| Initialize with force overwrite | ✓ (Initialize Panel checkbox) | ✓ (`init --force`) | Full parity |
| Initialize with custom path | ✓ (Initialize Panel path selector) | ✓ (`init --path`) | Full parity |

**Status:** ✅ Full Parity

### 2. File Instance Management

| Feature | TUI | CLI | Notes |
|---------|-----|-----|-------|
| List all file instances | ✓ (File Instances Screen) | ✓ (`files list`) | Full parity |
| List only enabled instances | ✓ (File Instances Screen filter) | ✓ (`files list --enabled`) | Full parity |
| Add new file instance | ✓ (File Instances Screen + button) | ✓ (`files add`) | Full parity |
| Remove file instance | ✓ (File Instances Screen - button) | ✓ (`files remove`) | Full parity |
| Enable file instance | ✓ (File Instances Screen toggle) | ✓ (`files enable`) | Full parity |
| Disable file instance | ✓ (File Instances Screen toggle) | ✓ (`files disable`) | Full parity |
| Reorder file instances | ✓ (File Instances Screen ↑↓) | ❌ | **TUI-only** |
| Edit component file | ✓ (File Instances Screen edit) | ❌ | **TUI-only** |

**Status:** ⚠️ **Partial Parity** - TUI has 2 features not in CLI

### 3. Preset Management

| Feature | TUI | CLI | Notes |
|---------|-----|-----|-------|
| List available presets | ✓ (Presets Panel) | ✓ (`presets list`) | Full parity |
| Filter presets by type | ✓ (Presets Panel dropdown) | ✓ (`presets list --type`) | Full parity |
| Show preset details | ✓ (Presets Panel selection) | ✓ (`presets show`) | Full parity |
| Create new preset | ❌ | ✓ (`presets create`) | **CLI-only** |
| Edit preset | ❌ | ✓ (`presets edit`) | **CLI-only** |
| Delete preset | ❌ | ✓ (`presets delete`) | **CLI-only** |
| Open presets directory | ❌ | ✓ (`presets open`) | **CLI-only** |
| Apply preset to add file instance | ✓ (Presets Panel apply) | ✓ (via `files add --preset`) | Full parity |

**Status:** ⚠️ **Partial Parity** - CLI has 4 features not in TUI

### 4. Template Management

| Feature | TUI | CLI | Notes |
|---------|-----|-----|-------|
| List global templates | ❌ | ✓ (`templates list`) | **CLI-only** |
| List with validation | ❌ | ✓ (`templates list --validate`) | **CLI-only** |
| Show template details | ❌ | ✓ (`templates show`) | **CLI-only** |
| Save current project as template | ❌ | ✓ (`templates save`) | **CLI-only** |
| Apply template to project | ❌ | ✓ (`templates apply`) | **CLI-only** |
| Edit template | ❌ | ✓ (`templates edit`) | **CLI-only** |
| Delete template | ❌ | ✓ (`templates delete`) | **CLI-only** |

**Status:** ❌ **No Parity** - All template features are CLI-only

### 5. Configuration Management

| Feature | TUI | CLI | Notes |
|---------|-----|-----|-------|
| View current configuration | ✓ (Overview Screen) | ✓ (`config show`) | Full parity |
| Get specific config value | ❌ | ✓ (`config get`) | **CLI-only** |
| Set config value | ✓ (Project Settings Screen) | ✓ (`config set`) | Partial parity |
| List all config values | ❌ | ✓ (`config list`) | **CLI-only** |
| Validate configuration | ✓ (Overview Screen) | ✓ (`config validate`) | Full parity |
| Edit project settings | ✓ (Project Settings Screen) | ✓ (via `config set`) | Full parity |

**Status:** ⚠️ **Partial Parity** - CLI has 2 dot-notation features not in TUI

### 6. Validation & Overview

| Feature | TUI | CLI | Notes |
|---------|-----|-----|-------|
| View project health status | ✓ (Overview Screen) | ❌ | **TUI-only** |
| View statistics | ✓ (Overview Screen) | ❌ | **TUI-only** |
| Validate configuration | ✓ (Overview Screen) | ✓ (`config validate`) | Full parity |
| View validation errors/warnings | ✓ (Overview Screen) | ✓ (validation output) | Full parity |

**Status:** ⚠️ **Partial Parity** - TUI has overview features, CLI has validation

## Summary

### Overall Parity Status: ⚠️ INCOMPLETE

| Category | TUI-Only Features | CLI-Only Features | Parity Status |
|----------|-------------------|-------------------|---------------|
| Project Initialization | 0 | 0 | ✅ Full |
| File Instance Management | 2 | 0 | ⚠️ Partial |
| Preset Management | 0 | 4 | ⚠️ Partial |
| Template Management | 0 | 7 | ❌ None |
| Configuration | 0 | 2 | ⚠️ Partial |
| Validation & Overview | 2 | 0 | ⚠️ Partial |
| **TOTAL** | **4** | **13** | **⚠️ Incomplete** |

### Critical Gaps

**High Priority (violates CLAUDE.md requirement):**

1. **Template Management** - Entire feature set missing from TUI
   - Users cannot manage templates through TUI
   - Templates are only accessible via CLI

2. **Preset CRUD** - Create/Edit/Delete missing from TUI
   - Users can only browse and apply presets in TUI
   - Cannot create or modify presets without CLI

**Medium Priority (usability gaps):**

3. **File Instance Reordering** - CLI cannot reorder instances
   - TUI has ↑↓ buttons for reordering
   - CLI would need `files reorder` or `files move` command

4. **Component File Editing** - CLI cannot directly edit component files
   - TUI can open component files in system editor
   - CLI would need `files edit` command or integration with editor

**Low Priority (nice-to-have):**

5. **Overview/Statistics** - CLI has no equivalent to TUI Overview Screen
   - Could add `claudefig status` or `claudefig overview` command
   - Or enhance `config show` to include health metrics

6. **Config Dot-Notation** - TUI uses screens instead of key paths
   - TUI approach is more user-friendly for discovery
   - CLI `config get/set` is more scriptable
   - Both approaches are valid for different use cases

## Recommendations

### Phase 1: Add Template Management to TUI (HIGH PRIORITY)

Add template management screens to TUI:
- Templates Panel (parallel to Presets Panel)
- Template Details Screen
- Create/Edit/Delete Template Screens

Estimated effort: 8-12 hours

### Phase 2: Add Preset CRUD to TUI (HIGH PRIORITY)

Enhance Presets Panel with:
- Create Preset button/screen
- Edit Preset action
- Delete Preset action

Estimated effort: 6-8 hours

### Phase 3: Add Reordering to CLI (MEDIUM PRIORITY)

Add `files reorder` or `files move` command:
```bash
claudefig files move <instance-id> --position <index>
claudefig files move <instance-id> --up
claudefig files move <instance-id> --down
```

Estimated effort: 2-3 hours

### Phase 4: Add File Editing to CLI (MEDIUM PRIORITY)

Add `files edit` command:
```bash
claudefig files edit <instance-id>  # Opens component file in $EDITOR
```

Estimated effort: 1-2 hours

### Total Estimated Effort to Achieve Full Parity

**17-25 hours** of development work

## Decision Log

### 2025-01-30: Initial Parity Assessment

- Created feature parity matrix
- Identified 17 feature gaps (4 TUI-only, 13 CLI-only)
- Prioritized template and preset management as high priority
- Template management is most critical gap (7 features CLI-only)

---

**Note:** This matrix should be updated whenever new features are added to either interface.
