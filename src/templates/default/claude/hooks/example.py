#!/usr/bin/env python3
"""
Example hook script for Claude Code.

This hook runs before tool execution and can be used to validate,
log, or block tool calls based on custom logic.
"""

import json
import sys

# Read JSON input from stdin
data = json.load(sys.stdin)

# Extract tool information
tool_name = data.get("tool_name", "")
tool_input = data.get("tool_input", {})

# Example: Log the tool call
print(f"Hook triggered for tool: {tool_name}", file=sys.stderr)

# Exit codes:
# 0 = Allow tool execution
# 1 = Error (tool fails)
# 2 = Block tool execution (with feedback)

sys.exit(0)
