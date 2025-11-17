# STDIO Local MCP Server

## Transport Type: STDIO

This template demonstrates a local MCP server running as a subprocess using STDIO transport.

## Use Cases

- **Local development tools** that run on your machine
- **npm/npx packages** that provide MCP servers
- **Testing and development** of MCP integrations
- **Command-line utilities** wrapped as MCP servers

## Configuration Example

```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

## How It Works

1. **Command Execution**: Runs the specified command as a subprocess
2. **STDIO Communication**: Communicates via standard input/output
3. **Environment Variables**: Injects environment variables at runtime
4. **Process Management**: Claude Code manages the subprocess lifecycle

## Security Best Practices

### Environment Variables

Always use environment variable substitution for sensitive data:
```json
"env": {
  "API_KEY": "${MY_API_KEY}",
  "TOKEN": "${SERVICE_TOKEN}"
}
```

**NEVER hardcode credentials:**
```json
// BAD - Never do this!
"env": {
  "API_KEY": "sk_live_abc123..."
}
```

### Credential Storage

For STDIO servers, store credentials in:
- **Environment variables** (export in your shell profile)
- **System keychain** (recommended for sensitive tokens)
- **.env files** (ensure they're in .gitignore)

## Common STDIO Servers

| Server | Package | Environment Variables |
|--------|---------|----------------------|
| GitHub | `@modelcontextprotocol/server-github` | `GITHUB_TOKEN` |
| Filesystem | `@modelcontextprotocol/server-filesystem` | None (paths only) |
| Postgres | `@modelcontextprotocol/server-postgres` | `DATABASE_URL` |
| Puppeteer | `@modelcontextprotocol/server-puppeteer` | None |

## Setup Instructions

1. **Set environment variable:**
   ```bash
   # Linux/macOS
   export GITHUB_TOKEN="your_token_here"

   # Windows (PowerShell)
   $env:GITHUB_TOKEN="your_token_here"
   ```

2. **Add config to project:**
   ```bash
   cp stdio-local/config.json .claude/mcp/github.json
   ```

3. **Register with Claude Code:**
   ```bash
   claudefig setup-mcp
   ```

4. **Verify installation:**
   ```bash
   claude mcp list
   ```

## Troubleshooting

**Server won't start:**
- Verify the command is in your PATH
- Check that npx/npm is installed
- Ensure environment variables are set in the same shell

**Permission errors:**
- On Unix systems, check execute permissions
- Verify the command can run standalone: `npx -y <package>`

**Environment variables not working:**
- Confirm variables are exported in your shell
- Try absolute paths instead of ${VAR} for testing
- Check spelling of environment variable names

## When to Use STDIO vs HTTP

**Use STDIO for:**
- Local development tools
- npm packages designed for STDIO
- Tools that need filesystem access
- Testing and experimentation

**Use HTTP for:**
- Remote cloud services
- Production deployments
- Multi-user scenarios
- Services requiring authentication flows (OAuth)

See `http-oauth` or `http-apikey` variants for HTTP transport examples.
