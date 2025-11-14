# HTTP MCP Server with OAuth 2.1

## Transport Type: HTTP

This template demonstrates an MCP server accessed via HTTP with OAuth 2.1 authentication.

## Use Cases

- **Cloud-based services** with OAuth authentication
- **Remote API integrations** requiring secure auth flows
- **Production deployments** of MCP-enabled services
- **Third-party services** supporting MCP protocol over HTTP
- **Multi-tenant applications** with user-specific access

## Configuration Example

```json
{
  "type": "http",
  "url": "${MCP_SERVICE_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_ACCESS_TOKEN}"
  },
  "transport": {
    "type": "http"
  }
}
```

## OAuth 2.1 with PKCE (Recommended)

As of the 2025 MCP specification, **OAuth 2.1 with PKCE is mandatory** for authentication flows.

### What is PKCE?

**PKCE** (Proof Key for Code Exchange) is a security extension that protects against authorization code interception attacks. It's required for all OAuth flows in MCP.

### OAuth 2.1 Flow

1. **Authorization Request** - User initiates login
2. **Code Verifier Generated** - Client creates random code_verifier
3. **Code Challenge Sent** - SHA256 hash of verifier sent to auth server
4. **User Authenticates** - User logs in and approves access
5. **Authorization Code Returned** - Server returns temporary code
6. **Token Exchange** - Client exchanges code + verifier for access token
7. **Access Token Stored** - Short-lived token stored securely

### Security Requirements

Per MCP 2025 specification:

**REQUIRED:**
- OAuth 2.1 with PKCE for all authentication
- Short-lived access tokens (1-24 hours)
- Token refresh flows for extended sessions
- HTTPS for all HTTP transport

**PROHIBITED:**
- Session-based authentication (deprecated)
- Long-lived tokens without refresh
- Hardcoded credentials in config files
- Pass-through token patterns

## Setting Up OAuth

### Step 1: Service Registration

Register your application with the MCP service provider:

```bash
# Example: Registering with a service
curl -X POST https://mcp.service.com/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "My Application",
    "redirect_uris": ["http://localhost:8080/callback"],
    "grant_types": ["authorization_code", "refresh_token"],
    "token_endpoint_auth_method": "none"
  }'
```

You'll receive:
- `client_id` - Your application identifier
- `authorization_endpoint` - Where to send users for login
- `token_endpoint` - Where to exchange codes for tokens

### Step 2: Initial Authentication

Most MCP services provide a CLI tool or web flow:

```bash
# Example: Service-provided auth flow
service-mcp-cli auth login

# Or manual OAuth flow
# 1. Open: https://mcp.service.com/oauth/authorize?
#          client_id=YOUR_CLIENT_ID&
#          response_type=code&
#          redirect_uri=http://localhost:8080/callback&
#          code_challenge=BASE64URL(SHA256(code_verifier))&
#          code_challenge_method=S256

# 2. After login, exchange code for token:
curl -X POST https://mcp.service.com/oauth/token \
  -d "grant_type=authorization_code" \
  -d "code=AUTH_CODE_FROM_REDIRECT" \
  -d "redirect_uri=http://localhost:8080/callback" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "code_verifier=ORIGINAL_CODE_VERIFIER"
```

### Step 3: Store Access Token Securely

**Recommended Storage Options:**

1. **System Keychain (Most Secure)**
   ```bash
   # macOS
   security add-generic-password \
     -a $USER \
     -s "mcp-service-token" \
     -w "your_access_token"

   # Linux (gnome-keyring)
   secret-tool store \
     --label="MCP Service Token" \
     service mcp-service \
     token access

   # Windows (Credential Manager via PowerShell)
   $credential = New-Object System.Management.Automation.PSCredential(
     "mcp-service",
     (ConvertTo-SecureString "your_access_token" -AsPlainText -Force)
   )
   ```

2. **Environment Variable (Development Only)**
   ```bash
   # Add to your shell profile (~/.bashrc, ~/.zshrc)
   export MCP_ACCESS_TOKEN="your_access_token"
   export MCP_SERVICE_URL="https://mcp.service.com/v1"
   ```

3. **Secure Configuration File (Encrypted)**
   ```bash
   # Store in encrypted config (ensure it's in .gitignore)
   echo "MCP_ACCESS_TOKEN=your_token" >> ~/.mcp-secrets
   chmod 600 ~/.mcp-secrets
   ```

### Step 4: Configure claudefig

```bash
# Set environment variables
export MCP_SERVICE_URL="https://mcp.service.com/v1"
export MCP_ACCESS_TOKEN="your_access_token_here"

# Copy template
cp http-oauth/config.json .claude/mcp/my-service.json

# Edit if needed (e.g., add custom headers)
# Then register
claudefig setup-mcp
```

### Step 5: Token Refresh (Important!)

OAuth tokens expire. Most services provide refresh tokens:

```bash
# Manual refresh (if service doesn't auto-refresh)
curl -X POST https://mcp.service.com/oauth/token \
  -d "grant_type=refresh_token" \
  -d "refresh_token=YOUR_REFRESH_TOKEN" \
  -d "client_id=YOUR_CLIENT_ID"

# Update your environment variable with new access token
export MCP_ACCESS_TOKEN="new_access_token"
```

**Automation:**
- Some services auto-refresh tokens when they're about to expire
- Consider using a token management tool or script
- Set calendar reminders for manual refresh if needed

## Security Best Practices

### DO

- Use system keychain for token storage
- Set short token expiration (1-24 hours)
- Implement token refresh flows
- Use HTTPS for all HTTP transport
- Rotate tokens regularly
- Monitor token usage for anomalies
- Revoke tokens when no longer needed

### DON'T

- Hardcode tokens in config files
- Commit tokens to version control
- Share tokens between users
- Use tokens without expiration
- Store tokens in plaintext files
- Skip PKCE in OAuth flows
- Use HTTP (non-TLS) transport

## Custom Headers

You can add custom headers for API keys, tracing, etc.:

```json
{
  "type": "http",
  "url": "${MCP_SERVICE_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_ACCESS_TOKEN}",
    "X-API-Key": "${API_KEY}",
    "X-Request-ID": "${REQUEST_ID}",
    "User-Agent": "claudefig-mcp-client/1.0"
  },
  "transport": {
    "type": "http"
  }
}
```

## Common HTTP MCP Services

| Service | Auth Type | Documentation |
|---------|-----------|---------------|
| Notion | OAuth 2.1 | https://developers.notion.com |
| Slack | OAuth 2.0 | https://api.slack.com/authentication/oauth-v2 |
| GitHub (API) | OAuth Apps | https://docs.github.com/apps/oauth-apps |
| Google Services | OAuth 2.0 | https://developers.google.com/identity/protocols/oauth2 |

## Troubleshooting

**Token expired errors:**
- Refresh your access token using refresh_token grant
- Check token expiration time
- Verify system clock is accurate

**401 Unauthorized:**
- Confirm token is correctly set in environment
- Check Authorization header format
- Verify token hasn't been revoked

**Connection refused:**
- Verify service URL is correct
- Check network connectivity
- Ensure HTTPS certificate is valid

**CORS errors:**
- HTTP transport shouldn't have CORS issues (server-to-server)
- If seeing CORS, verify you're using HTTP transport, not browser-based

## When to Use HTTP vs STDIO

**Use HTTP for:**
- Remote cloud services
- Production deployments
- OAuth-authenticated services
- Multi-user/tenant scenarios
- Services requiring audit trails

**Use STDIO for:**
- Local development tools
- npm packages
- Filesystem operations
- Simple command-line utilities

See `stdio-local` or `http-apikey` variants for alternative transports.

## Performance Optimization

### Connection Pooling

For high-volume usage, configure connection pooling:

```json
{
  "type": "http",
  "url": "${MCP_SERVICE_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_ACCESS_TOKEN}",
    "Connection": "keep-alive"
  },
  "transport": {
    "type": "http",
    "keepAlive": true,
    "maxConnections": 10
  }
}
```

### Caching

Implement response caching for read-heavy operations:
- Cache tool/resource lists (TTL: 5-15 minutes)
- Cache resource content (TTL: 1-5 minutes)
- Invalidate cache on write operations

### Timeout Configuration

```json
{
  "type": "http",
  "url": "${MCP_SERVICE_URL}",
  "headers": {
    "Authorization": "Bearer ${MCP_ACCESS_TOKEN}"
  },
  "transport": {
    "type": "http",
    "timeout": 30000
  }
}
```

## Additional Resources

- [MCP Specification 2025](https://spec.modelcontextprotocol.io/)
- [OAuth 2.1 Specification](https://oauth.net/2.1/)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
- [OAuth Security Best Practices](https://oauth.net/2/oauth-best-practice/)
