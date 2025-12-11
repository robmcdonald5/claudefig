# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-12-11

### Changed
- **TUI exception handling** - Converted 31 empty `except: pass` blocks to `contextlib.suppress()` for improved code clarity and Pythonic style
- **Default preset cleanup** - Removed example placeholder components from default preset for cleaner initial setup

### Fixed
- **Service layer logging** - Added debug-level logging to silent exception handlers in `user_config.py` and `structure_validator.py` for improved troubleshooting
- **Test unused variable** - Converted unused variable in `test_tui_app.py` to assertion for code quality
- **Type error** - Fixed mypy type error in `create_preset_wizard.py` button focus logic

### Security
- **CodeQL compliance** - Addressed all 42 CodeQL findings (34 empty except blocks, 1 unused variable, service layer exception handling)

## [1.0.0] - 2025-12-01

### Added
- **Repository-based preset creation** - New `presets create-from-repo` CLI command and TUI Preset Wizard for creating presets from existing repository configurations
- **Component Discovery Service** - New service using rglob patterns to scan repositories for Claude Code components (CLAUDE.md, commands, agents, hooks, MCP configs, plugins, skills, etc.)
- **TUI Preset Wizard** - Multi-step interactive wizard with checkbox-based component selection for granular preset creation
- **MCP HTTP transport variants** - Added `mcp:http-oauth` and `mcp:http-apikey` preset variants for cloud service integration
- **Path sanitization and validation** - Security improvements preventing directory traversal and validating paths remain within repository boundaries
- Plugins and Skills file type support with full TUI/CLI integration
- Dual-source component discovery (global `~/.claudefig/components/` and preset-specific `~/.claudefig/presets/{preset}/components/`)
- Structure validation and auto-healing system for user configuration
- Factory-boy infrastructure for test data generation
- Cross-platform OS integration improvements for Windows/Linux/macOS compatibility
- BaseModalScreen and navigation mixins for consistent TUI behavior
- Base navigation classes (BaseNavigablePanel, BaseScreen) for unified keyboard shortcuts
- Comprehensive error message standardization system
- Visual indicators for component sources: `(g)` for global, `(p)` for preset components
- Test coverage for TUI widgets (FileInstanceItem, error messages, component validation)

### Changed
- **BREAKING:** Config filename from `.claudefig.toml` to `claudefig.toml` (no dot prefix) for better visibility
- Preset system completely refactored to directory-based structure (removed JSON metadata files)
- Component discovery migrated from custom file traversal to `rglob` patterns for improved performance and consistency
- CLI refactored into logical command hierarchy with improved organization
- TUI: Core Files functionality merged into unified File Instances screen with tabbed interface
- Directory structure: Renamed `src/templates/` to `src/presets/` for clarity
- File instance management now uses service layer pattern for better separation of concerns
- TUI navigation improved with dynamic scrolling and auto-scroll behavior
- Screen refresh pattern updated to use `refresh(recompose=True)` instead of screen stack manipulation

### Deprecated
- Old preset metadata JSON files (replaced by directory-based structure)
- Separate Core Files screen in TUI (merged into File Instances screen)

### Removed
- Dead code and unused utilities throughout codebase
- Obsolete preset discovery patterns
- Skipped tests for deleted preset types

### Fixed
- Cross-platform test compatibility for Windows/Linux/macOS
- Python 3.10 tomllib import compatibility issues
- Directory component generation rewritten to use unified component system
- Plugin component reference validation
- TUI navigation and scrolling issues (character limit UI shifting, vertical nav wrapping)
- Focus restoration in PresetsPanel and MainScreen navigation logic
- Preset component path resolution in tests
- Mock assertions for cross-platform compatibility in test suite


## [0.1.0] - 2025-11-07

### Added
- Initial release
- Basic `claudefig init` command
- Configuration file templates
- MIT License

[1.0.1]: https://github.com/robmcdonald5/claudefig/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/robmcdonald5/claudefig/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/robmcdonald5/claudefig/releases/tag/v0.1.0
