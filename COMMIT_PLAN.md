# Commit Plan

This document outlines the proposed commits for the current changes.

---

## Commit 1: feat(mcp): add automatic MCP server registration and HTTP transport support

### Files:
- `src/claudefig/initializer.py`
- `src/claudefig/cli/main.py`

### Message:
```
feat(mcp): add automatic MCP server registration and HTTP transport support

- Add automatic MCP setup during initialization (both TUI and CLI)
- Implement transport validation for STDIO, HTTP, and SSE
- Add security checks for hardcoded credentials and non-HTTPS usage
- Support dual configuration patterns (.mcp.json and .claude/mcp/*.json)
- Add _auto_setup_mcp_servers() method for non-fatal registration
- Add _validate_mcp_transport() method with required field validation
- Enhanced setup-mcp CLI command with detailed help documentation
- Auto-setup runs when MCP file instances are enabled during init

Breaking changes: None (backward compatible)
```

---

## Commit 2: feat(mcp): add HTTP OAuth and API key transport template variants

### Files:
- `src/presets/default/components/mcp/stdio-local/` (renamed from default/)
- `src/presets/default/components/mcp/http-oauth/` (new)
- `src/presets/default/components/mcp/http-apikey/` (new)
- `src/presets/default/components/mcp/default/config.json` (deleted)

### Message:
```
feat(mcp): add HTTP OAuth and API key transport template variants

- Rename mcp/default/ to mcp/stdio-local/ for clarity
- Add mcp/http-oauth/ variant with OAuth 2.1 PKCE template
- Add mcp/http-apikey/ variant for API key authentication
- Include comprehensive README.md in each variant with:
  - Use cases and configuration examples
  - OAuth 2.1 setup instructions (http-oauth)
  - API key best practices (http-apikey)
  - Security guidelines and troubleshooting
- Support for both local (STDIO) and cloud (HTTP) MCP servers

Templates support environment variable substitution for secure credential management.
```

---

## Commit 3: feat(mcp): add preset definitions for new MCP transport variants

### Files:
- `src/claudefig/repositories/preset_repository.py`
- `src/presets/default/claudefig.toml`

### Message:
```
feat(mcp): add preset definitions for new MCP transport variants

- Add mcp:stdio-local preset (local command-line tools)
- Add mcp:http-oauth preset (cloud services with OAuth 2.1)
- Add mcp:http-apikey preset (cloud services with API keys)
- Add mcp:default alias for backward compatibility → stdio-local
- Update default preset config to use stdio-local component name
- Implement alias mapping in _resolve_builtin_component()

Preserves backward compatibility while supporting new transport types.
```

---

## Commit 4: test(mcp): add comprehensive test coverage for MCP functionality

### Files:
- `tests/test_initializer.py`

### Message:
```
test(mcp): add comprehensive test coverage for MCP functionality

Add 17 new tests covering:
- Dual configuration pattern support (.mcp.json and .claude/mcp/*.json)
- Transport validation (STDIO, HTTP, SSE)
- Required field validation per transport type
- Invalid transport type error handling
- Security warnings (non-HTTPS, hardcoded credentials)
- SSE deprecation warnings
- Error handling for malformed JSON

All tests passing. Ensures robust MCP setup and validation.
```

---

## Commit 5: docs(mcp): add comprehensive MCP security guide and update documentation

### Files:
- `docs/MCP_SECURITY_GUIDE.md` (new)
- `docs/ADDING_NEW_COMPONENTS.md`
- `docs/CLI_REFERENCE.md`
- `docs/FEATURE_PARITY.md`

### Message:
```
docs(mcp): add comprehensive MCP security guide and update documentation

MCP_SECURITY_GUIDE.md (new 600-line guide):
- OAuth 2.1 with PKCE implementation guide
- Credential management best practices
- System keychain integration (macOS/Linux/Windows)
- Transport security requirements
- Token lifecycle management
- Common vulnerabilities and fixes
- Compliance checklist

ADDING_NEW_COMPONENTS.md:
- Add 370-line MCP special case section
- Document three template variants (stdio-local, http-oauth, http-apikey)
- Configuration file patterns and validation
- Security best practices and troubleshooting
- Migration guides and performance considerations

CLI_REFERENCE.md:
- Enhanced setup-mcp command documentation
- Add note about automatic registration in v1.1.0
- Document dual configuration pattern support
- Update Example 9 with all three MCP preset variants

FEATURE_PARITY.md:
- Add MCP Management category (✅ Near Full Parity)
- Document auto-setup implementation in decision log
- Update summary table with MCP status
- Update last modified date to 2025-11-14
```

---

## Commit 6: docs: add table of contents to all documentation files

### Files:
- `docs/ADDING_NEW_COMPONENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/CLI_REFERENCE.md`
- `docs/CONFIG_GUIDE.md`
- `docs/ERROR_MESSAGES.md`
- `docs/FACTORY_USAGE.md`
- `docs/FEATURE_PARITY.md`
- `docs/MCP_SECURITY_GUIDE.md`
- `docs/PRESETS_GUIDE.md`

### Message:
```
docs: add table of contents to all documentation files

Add comprehensive TOCs to all 9 documentation files for improved navigation:

- ADDING_NEW_COMPONENTS.md: 33 entries covering implementation checklist
- ARCHITECTURE.md: 30 entries + fix title level (## → #)
- CLI_REFERENCE.md: Already had TOC (6 entries, kept as-is)
- CONFIG_GUIDE.md: 24 entries covering configuration management
- ERROR_MESSAGES.md: 16 entries for error standardization system
- FACTORY_USAGE.md: 11 entries covering test factory patterns
- FEATURE_PARITY.md: 14 entries tracking TUI/CLI parity
- MCP_SECURITY_GUIDE.md: 36 entries covering security best practices
- PRESETS_GUIDE.md: 29 entries for preset system guide

Unified style standards:
- Dash format (-) for all TOC entries (no numbering)
- 2-space indentation for nested items
- No horizontal rules before/after TOC
- Consistent placement after title and intro text
- Blank line separation for readability

All documentation now follows professional, consistent navigation structure.
```

---

## Commit Summary

**Total commits:** 6

**Breakdown:**
1. Core MCP auto-setup and validation (2 files)
2. MCP transport templates (4 paths: 1 deleted, 3 new directories)
3. MCP preset definitions (2 files)
4. MCP test coverage (1 file)
5. MCP documentation (4 files, 1 new)
6. Documentation TOC additions (9 files)

**Statistics:**
- Total files modified: 13
- Total files created: 4 (MCP_SECURITY_GUIDE.md + 3 template directories)
- Total files deleted: 1 (old default/config.json)
- Documentation added: ~1000+ lines
- Tests added: 17 new test cases

**Feature status:**
- ✅ MCP auto-setup (v1.1.0)
- ✅ HTTP transport support (OAuth 2.1 + API key)
- ✅ Transport validation and security warnings
- ✅ Dual configuration pattern support
- ✅ Backward compatibility maintained
- ✅ Comprehensive documentation
- ✅ Full test coverage
