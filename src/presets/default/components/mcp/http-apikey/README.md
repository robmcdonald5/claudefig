# HTTP MCP Server with API Key Authentication

## Transport Type: HTTP

This template demonstrates an MCP server accessed via HTTP with API key authentication.

## Use Cases

- **Cloud services** with API key authentication
- **Internal APIs** requiring simple token auth
- **Development/staging** environments
- **Services without OAuth support** (legacy or simple APIs)
- **Machine-to-machine** communication

## Configuration Example

```json
{
  "type": "http",
  "url": "${MCP_API_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_API_KEY}",
    "Content-Type": "application/json"
  },
  "transport": {
    "type": "http"
  }
}
```

## API Key vs OAuth: When to Use Which

### Use API Keys When:

- Service doesn't support OAuth
- Simple machine-to-machine auth is sufficient
- You control both client and server
- Development/internal tools
- Rate limits are per-key, not per-user

### Use OAuth When:

- Service requires OAuth (mandatory per 2025 MCP spec)
- User-specific access needed
- Third-party service integration
- Delegated authorization required
- Audit trails need user attribution

**Note:** While API keys are simpler, OAuth 2.1 with PKCE is the recommended standard for MCP services. Use API keys only when OAuth isn't available.

## Setting Up API Key Authentication

### Step 1: Generate API Key

Most services provide a dashboard or CLI to generate keys:

```bash
# Example: Service-provided key generation
service-cli api-key create \
  --name "claudefig-mcp" \
  --scopes "mcp:read,mcp:write"

# Returns:
# API Key: mcp_sk_live_abc123def456...
# Secret:  Do not share! Store securely.
```

### Step 2: Store API Key Securely

**Option 1: System Keychain (Recommended)**

```bash
# macOS
security add-generic-password \
  -a $USER \
  -s "mcp-api-key" \
  -w "mcp_sk_live_abc123..."

# Then retrieve in shell profile:
export MCP_API_KEY=$(security find-generic-password \
  -a $USER -s "mcp-api-key" -w)

# Linux (gnome-keyring)
secret-tool store \
  --label="MCP API Key" \
  service mcp-api \
  key api-key

# Retrieve:
export MCP_API_KEY=$(secret-tool lookup service mcp-api key api-key)

# Windows (Credential Manager)
# Use Windows Credential Manager GUI or PowerShell:
cmdkey /add:"mcp-api-key" /user:"api" /pass:"mcp_sk_live_abc123..."
```

**Option 2: Environment Variables (Development)**

```bash
# Add to shell profile (~/.bashrc, ~/.zshrc, ~/.config/fish/config.fish)
export MCP_API_URL="https://api.service.com/mcp/v1"
export MCP_API_KEY="mcp_sk_live_abc123..."

# Source the file
source ~/.bashrc
```

**Option 3: .env File (Project-Level)**

```bash
# Create .env file (ensure it's in .gitignore!)
cat > .env << 'EOF'
MCP_API_URL=https://api.service.com/mcp/v1
MCP_API_KEY=mcp_sk_live_abc123...
EOF

# Set restrictive permissions
chmod 600 .env

# Load in shell
export $(cat .env | xargs)
```

### Step 3: Configure claudefig

```bash
# Ensure environment variables are set
echo $MCP_API_KEY  # Should output your key

# Copy template
cp http-apikey/config.json .claude/mcp/my-api-service.json

# Customize if needed (edit my-api-service.json)

# Register with Claude Code
claudefig setup-mcp

# Verify
claude mcp list
```

## Security Best Practices

### DO

- Store API keys in system keychain or encrypted storage
- Use different keys for dev/staging/production
- Rotate keys regularly (every 90 days minimum)
- Scope keys to minimum necessary permissions
- Monitor key usage for anomalies
- Revoke compromised keys immediately
- Use HTTPS for all HTTP transport

### DON'T

- Commit API keys to version control
- Hardcode keys in configuration files
- Share keys between team members
- Use production keys in development
- Log API keys in application logs
- Send keys over unencrypted channels
- Reuse keys across multiple services

### Key Rotation

Establish a regular rotation schedule:

```bash
# 1. Generate new key
new_key=$(service-cli api-key create --name "claudefig-mcp-2024-q1")

# 2. Update environment variable
export MCP_API_KEY="$new_key"

# 3. Update keychain
security add-generic-password \
  -a $USER \
  -s "mcp-api-key" \
  -w "$new_key" \
  -U  # Update existing

# 4. Test with new key
claudefig setup-mcp

# 5. Verify functionality
claude mcp list

# 6. Revoke old key (after confirmation)
service-cli api-key revoke --key-id old_key_id
```

## Custom Headers

Many services require additional headers:

```json
{
  "type": "http",
  "url": "${MCP_API_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_API_KEY}",
    "Content-Type": "application/json",
    "X-API-Version": "2025-01-01",
    "X-Client-ID": "${CLIENT_ID}",
    "User-Agent": "claudefig-mcp/1.0"
  },
  "transport": {
    "type": "http"
  }
}
```

### Common Header Patterns

| Header | Purpose | Example |
|--------|---------|---------|
| `Authorization` | API key/token | `Bearer ${API_KEY}` |
| `X-API-Key` | Alternative auth | `${API_KEY}` |
| `X-API-Version` | API version pinning | `2025-01-01` |
| `Content-Type` | Request format | `application/json` |
| `Accept` | Response format | `application/json` |
| `User-Agent` | Client identification | `claudefig-mcp/1.0` |
| `X-Request-ID` | Request tracking | `${UUID}` |

## Multiple Authentication Methods

Some services support multiple auth methods:

```json
{
  "type": "http",
  "url": "${MCP_API_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_API_KEY}",
    "X-API-Key": "${SECONDARY_API_KEY}",
    "X-Client-Secret": "${CLIENT_SECRET}"
  },
  "transport": {
    "type": "http"
  }
}
```

**Note:** Only include what the service requires. Extra headers may cause errors.

## Rate Limiting

API key services often have rate limits. Handle them gracefully:

### Common Rate Limit Headers

Services may return these headers:
- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets

### Handling Rate Limits

```json
{
  "type": "http",
  "url": "${MCP_API_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_API_KEY}"
  },
  "transport": {
    "type": "http",
    "retryOnRateLimit": true,
    "maxRetries": 3,
    "retryDelay": 1000
  }
}
```

### Best Practices

- **Respect rate limits** - Don't hammer the API
- **Implement backoff** - Exponential backoff on 429 responses
- **Cache responses** - Reduce unnecessary requests
- **Batch operations** - When supported by the API

## Environment-Specific Configuration

Use different keys for different environments:

```bash
# Development
export MCP_API_URL="https://dev-api.service.com/mcp"
export MCP_API_KEY="mcp_sk_dev_abc123..."

# Staging
export MCP_API_URL="https://staging-api.service.com/mcp"
export MCP_API_KEY="mcp_sk_staging_def456..."

# Production
export MCP_API_URL="https://api.service.com/mcp"
export MCP_API_KEY="mcp_sk_live_ghi789..."
```

Create separate config files if needed:

```bash
# .claude/mcp/my-service-dev.json
# .claude/mcp/my-service-staging.json
# .claude/mcp/my-service-prod.json
```

## Common API Key MCP Services

| Service | Auth Header | Key Format |
|---------|------------|------------|
| OpenAI | `Authorization: Bearer sk-...` | `sk-*` |
| Anthropic | `x-api-key: sk-ant-...` | `sk-ant-*` |
| Stripe | `Authorization: Bearer sk_live_...` | `sk_live_*` / `sk_test_*` |
| SendGrid | `Authorization: Bearer SG....` | `SG.*` |
| Twilio | `Authorization: Basic Base64(SID:Token)` | Account SID + Auth Token |

## Troubleshooting

**401 Unauthorized:**
- Verify API key is correct
- Check key hasn't expired or been revoked
- Ensure key has necessary scopes/permissions
- Confirm Authorization header format

**403 Forbidden:**
- Key may lack required permissions
- IP whitelist may be blocking requests
- Service may require additional headers

**429 Too Many Requests:**
- You've hit rate limit
- Wait for rate limit reset
- Consider implementing request throttling

**Environment variable not expanding:**
```bash
# Debug: Check if variable is set
echo $MCP_API_KEY

# Debug: Try absolute value temporarily
# Replace ${MCP_API_KEY} with actual key for testing
# Then switch back to ${MCP_API_KEY} for production
```

## Migration to OAuth

If the service adds OAuth support later, migration is straightforward:

1. **Obtain OAuth credentials** following service docs
2. **Switch template** from `http-apikey` to `http-oauth`
3. **Update environment variables** (URL and token)
4. **Re-run setup:** `claudefig setup-mcp`
5. **Revoke old API key** once confirmed working

## When to Use HTTP vs STDIO

**Use HTTP for:**
- Remote cloud services (with API keys)
- Production deployments
- Services requiring network access
- Multi-tenant scenarios

**Use STDIO for:**
- Local development tools
- npm packages
- Filesystem operations
- Tools without network requirements

See `stdio-local` or `http-oauth` variants for alternative transports.

## Performance Optimization

### Connection Persistence

```json
{
  "type": "http",
  "url": "${MCP_API_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_API_KEY}",
    "Connection": "keep-alive"
  },
  "transport": {
    "type": "http",
    "keepAlive": true
  }
}
```

### Request Timeout

```json
{
  "type": "http",
  "url": "${MCP_API_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_API_KEY}"
  },
  "transport": {
    "type": "http",
    "timeout": 30000
  }
}
```

### Compression

```json
{
  "type": "http",
  "url": "${MCP_API_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_API_KEY}",
    "Accept-Encoding": "gzip, deflate"
  },
  "transport": {
    "type": "http"
  }
}
```

## Additional Resources

- [MCP Specification 2025](https://spec.modelcontextprotocol.io/)
- [HTTP Authentication Best Practices](https://tools.ietf.org/html/rfc7235)
- [API Security Checklist](https://github.com/shieldfy/API-Security-Checklist)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
