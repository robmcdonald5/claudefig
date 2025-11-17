# MCP Security Guide

Comprehensive security best practices for configuring and managing Model Context Protocol (MCP) servers with claudefig.

## Table of Contents

- [Security Principles](#security-principles)
- [OAuth 2.1 with PKCE](#oauth-21-with-pkce)
  - [Why OAuth 2.1?](#why-oauth-21)
  - [PKCE Flow Explained](#pkce-flow-explained)
  - [Implementation Example](#implementation-example)
  - [Security Considerations](#security-considerations)
  - [Token Refresh Flow](#token-refresh-flow)
- [Credential Management](#credential-management)
  - [System Keychain Integration](#system-keychain-integration)
  - [Environment Variables](#environment-variables)
  - [Credential Rotation](#credential-rotation)
- [Transport Security](#transport-security)
  - [HTTPS Requirements](#https-requirements)
  - [Certificate Validation](#certificate-validation)
  - [TLS Configuration](#tls-configuration)
- [Configuration Hardening](#configuration-hardening)
  - [Environment Variable Enforcement](#environment-variable-enforcement)
  - [Restricting File Permissions](#restricting-file-permissions)
  - [Audit Logging](#audit-logging)
- [Token Lifecycle](#token-lifecycle)
  - [Token Expiration](#token-expiration)
  - [Token Refresh](#token-refresh)
  - [Token Rotation](#token-rotation)
  - [Token Revocation](#token-revocation)
- [Common Vulnerabilities](#common-vulnerabilities)
  - [Hardcoded Credentials](#hardcoded-credentials)
  - [Insecure Token Storage](#insecure-token-storage)
  - [Missing HTTPS](#missing-https)
  - [Excessive Token Lifetime](#excessive-token-lifetime)
  - [Insufficient Scope](#insufficient-scope)

## Security Principles

### Zero Trust Approach

Assume all credentials can be compromised. Design systems with:

- **Short-lived tokens** - Minimize impact window
- **Principle of least privilege** - Grant minimum necessary permissions
- **Defense in depth** - Multiple security layers
- **Audit trails** - Log all authentication attempts

### Security Hierarchy (Most to Least Secure)

1. **OAuth 2.1 with PKCE + System Keychain** - Production standard
2. **OAuth 2.1 with PKCE + Environment Variables** - Acceptable for dev
3. **API Keys + System Keychain** - When OAuth unavailable
4. **API Keys + Environment Variables** - Development only
5. **Hardcoded credentials** - NEVER acceptable

---

## OAuth 2.1 with PKCE

### Why OAuth 2.1?

Per the **2025 MCP specification**, OAuth 2.1 with PKCE is **mandatory** for MCP servers that require authentication.

**Key improvements over OAuth 2.0:**
- PKCE required for all clients (not just public clients)
- No implicit flow (removed due to security flaws)
- Refresh token rotation enforced
- Redirect URI must be exact match (no wildcards)

### PKCE Flow Explained

**PKCE** (Proof Key for Code Exchange, RFC 7636) prevents authorization code interception attacks.

#### Step-by-Step Process

**1. Generate Code Verifier**
```python
import secrets
import hashlib
import base64

# Generate random 43-128 character string
code_verifier = base64.urlsafe_b64encode(
    secrets.token_bytes(32)
).decode('utf-8').rstrip('=')
```

**2. Create Code Challenge**
```python
# SHA256 hash of verifier
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode('utf-8')).digest()
).decode('utf-8').rstrip('=')
```

**3. Authorization Request**
```
GET https://auth.service.com/oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=http://localhost:8080/callback&
  code_challenge=BASE64URL(SHA256(code_verifier))&
  code_challenge_method=S256&
  scope=mcp:read+mcp:write&
  state=RANDOM_STATE_STRING
```

**4. User Authenticates**
- User logs in to service
- Approves requested scopes
- Redirected back with authorization code

**5. Token Exchange**
```bash
POST https://auth.service.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTHORIZATION_CODE&
redirect_uri=http://localhost:8080/callback&
client_id=YOUR_CLIENT_ID&
code_verifier=ORIGINAL_CODE_VERIFIER
```

**6. Response**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "fdb8fdbecf1d03ce5e6125c067d86...",
  "scope": "mcp:read mcp:write"
}
```

### Security Benefits of PKCE

1. **Prevents Code Interception**
   - Attacker can't use stolen authorization code
   - Requires knowledge of original code_verifier

2. **No Client Secret Required**
   - Safe for native/mobile apps
   - Reduces secret exposure risk

3. **Dynamic Per-Request Protection**
   - Each flow uses unique verifier
   - Replay attacks prevented

### OAuth Implementation Checklist

- [ ] Use OAuth 2.1 specification (not 2.0)
- [ ] Implement PKCE for all flows
- [ ] Use S256 code challenge method (SHA256)
- [ ] Generate cryptographically random code_verifier (32+ bytes)
- [ ] Validate state parameter on callback
- [ ] Use exact redirect URI matching
- [ ] Request minimum necessary scopes
- [ ] Implement refresh token rotation
- [ ] Store tokens in system keychain
- [ ] Set token expiration to 1-24 hours
- [ ] Implement token revocation on logout
- [ ] Use HTTPS for all endpoints

---

## Credential Management

### System Keychain Integration (Recommended)

#### macOS (Keychain Access)

**Store Credential:**
```bash
# Add to keychain
security add-generic-password \
  -a "$USER" \
  -s "mcp-service-token" \
  -w "your_access_token_here" \
  -U  # Update if exists

# With label
security add-generic-password \
  -a "$USER" \
  -s "mcp-service-token" \
  -l "MCP Service Access Token" \
  -w "your_access_token_here"
```

**Retrieve Credential:**
```bash
# Get token
token=$(security find-generic-password \
  -a "$USER" \
  -s "mcp-service-token" \
  -w)

# Export for session
export MCP_ACCESS_TOKEN="$token"
```

**Delete Credential:**
```bash
security delete-generic-password \
  -a "$USER" \
  -s "mcp-service-token"
```

#### Linux (gnome-keyring / Secret Service)

**Store Credential:**
```bash
# Using secret-tool (libsecret)
secret-tool store \
  --label="MCP Service Token" \
  service mcp-service \
  account production \
  token access
# Then enter token when prompted
```

**Retrieve Credential:**
```bash
# Get token
token=$(secret-tool lookup \
  service mcp-service \
  account production \
  token access)

export MCP_ACCESS_TOKEN="$token"
```

**Delete Credential:**
```bash
secret-tool clear \
  service mcp-service \
  account production \
  token access
```

#### Windows (Credential Manager)

**Store Credential (PowerShell):**
```powershell
# Create credential object
$password = ConvertTo-SecureString "your_token" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential(
    "mcp-service",
    $password
)

# Store in Credential Manager
# Requires CredentialManager module: Install-Module -Name CredentialManager
New-StoredCredential -Target "mcp-service-token" -UserName "user" -Password "your_token" -Type Generic -Persist LocalMachine
```

**Retrieve Credential (PowerShell):**
```powershell
# Get credential
$cred = Get-StoredCredential -Target "mcp-service-token"
$token = $cred.GetNetworkCredential().Password

# Export to environment
$env:MCP_ACCESS_TOKEN = $token
```

**Or use GUI:**
1. Open Control Panel → Credential Manager
2. Click "Add a generic credential"
3. Internet or network address: `mcp-service-token`
4. User name: `user`
5. Password: `your_token`

### Environment Variables (Development Only)

**Setting Variables:**

```bash
# ~/.bashrc or ~/.zshrc
export MCP_SERVICE_URL="https://mcp.service.com/v1"
export MCP_ACCESS_TOKEN="your_token_here"

# Or in .env file (ensure in .gitignore!)
MCP_SERVICE_URL=https://mcp.service.com/v1
MCP_ACCESS_TOKEN=your_token_here
```

**Security Considerations:**

- ✓ Better than hardcoded credentials
- ✓ Easy for development/testing
- ✗ Visible in process environment
- ✗ May leak in error messages
- ✗ Persists in shell history if set manually

**Mitigation:**

```bash
# Read from file instead of setting directly
export MCP_ACCESS_TOKEN=$(cat ~/.mcp-secrets/token)

# Or use keychain retrieval
export MCP_ACCESS_TOKEN=$(security find-generic-password -a $USER -s mcp-token -w)
```

### .env Files

**Setup:**

```bash
# Create .env file
cat > .env << 'EOF'
MCP_SERVICE_URL=https://mcp.service.com/v1
MCP_ACCESS_TOKEN=your_token_here
MCP_API_KEY=your_api_key
EOF

# Set restrictive permissions
chmod 600 .env

# Add to .gitignore
echo ".env" >> .gitignore
```

**Loading:**

```bash
# In shell
export $(cat .env | xargs)

# Or using direnv (recommended)
# Install: https://direnv.net
echo "export $(cat .env | xargs)" > .envrc
direnv allow
```

**Security Considerations:**

- ✓ Project-specific credentials
- ✓ Easy to manage
- ✗ Must ensure .gitignore is correct
- ✗ Can be accidentally committed
- ✗ Readable by anyone with file access

---

## Transport Security

### HTTPS Requirement

**MANDATORY** for production HTTP transport:

```json
{
  "type": "http",
  "url": "https://mcp.service.com/v1",  // ✓ HTTPS
  "headers": {
    "Authorization": "Bearer ${TOKEN}"
  }
}
```

**NEVER in production:**

```json
{
  "url": "http://mcp.service.com/v1"  // ✗ Unencrypted!
}
```

**Exception:** localhost development only

```json
{
  "url": "http://localhost:8080/mcp"  // ✓ Acceptable for local dev
}
```

### Certificate Validation

Ensure TLS certificate validation is enabled:

```json
{
  "type": "http",
  "url": "https://mcp.service.com/v1",
  "transport": {
    "type": "http",
    "rejectUnauthorized": true  // Verify certificates
  }
}
```

**NEVER disable certificate validation in production:**

```json
{
  "rejectUnauthorized": false  // ✗ Security vulnerability!
}
```

### Custom CA Certificates

For internal/self-signed certificates:

```bash
# Set system CA bundle
export NODE_EXTRA_CA_CERTS=/path/to/ca-bundle.crt

# Or specify in config
{
  "transport": {
    "type": "http",
    "ca": "${CA_CERT_PATH}"
  }
}
```

---

## Configuration Hardening

### Environment Variable Substitution

**ALWAYS use environment variables for secrets:**

```json
{
  "env": {
    "API_KEY": "${MY_API_KEY}",        // ✓ Secure
    "TOKEN": "${SERVICE_TOKEN}",        // ✓ Secure
    "SECRET": "${CLIENT_SECRET}"        // ✓ Secure
  }
}
```

**NEVER hardcode credentials:**

```json
{
  "env": {
    "API_KEY": "sk_live_abc123...",    // ✗ DANGEROUS!
    "TOKEN": "Bearer eyJhbGc..."       // ✗ DANGEROUS!
  }
}
```

### Validation Warnings

claudefig automatically detects common security issues:

```bash
# Hardcoded credential detection
Warning: config.json may contain hardcoded credentials in header 'Authorization'.
Use environment variables: "${VAR_NAME}"

# HTTP (non-HTTPS) detection
Warning: config.json uses HTTP (not HTTPS). Consider using HTTPS for production.
```

**Act on these warnings immediately!**

### File Permissions

Restrict access to configuration files:

```bash
# MCP config files
chmod 600 .claude/mcp/*.json
chmod 600 .mcp.json

# Secret files
chmod 600 .env
chmod 600 ~/.mcp-secrets/*

# Directories
chmod 700 .claude/mcp/
chmod 700 ~/.mcp-secrets/
```

### .gitignore Protection

**Essential entries:**

```gitignore
# MCP Secrets
.env
.mcp.json
.claude/mcp/*.json

# Credential files
*-secrets/
*.key
*.pem
*.p12

# Backup files (may contain secrets)
*.backup
*.bak
*~
```

**Verify nothing sensitive is tracked:**

```bash
# Check for tracked secrets
git grep -i "sk_live_"
git grep -i "api_key"
git grep -i "token"
git grep -i "secret"

# Check staged files
git diff --cached
```

---

## Token Lifecycle

### Token Expiration

**Set appropriate expiration:**

| Token Type | Recommended TTL | Maximum TTL |
|------------|-----------------|-------------|
| Access Token | 1 hour | 24 hours |
| Refresh Token | 30 days | 90 days |
| API Key | 90 days | 1 year |

**Implementation:**

```json
{
  "access_token": "eyJhbGc...",
  "expires_in": 3600,          // 1 hour in seconds
  "refresh_token": "fdb8fd..."
}
```

### Token Refresh

**Automatic refresh before expiration:**

```python
import time

def get_valid_token():
    """Get token, refreshing if necessary."""
    # Check expiration
    if time.time() >= token_expiry - 300:  # 5 min buffer
        # Refresh token
        response = requests.post(
            "https://auth.service.com/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id
            }
        )
        # Update stored tokens
        update_keychain(response.json())

    return get_current_token()
```

### Token Rotation

**Refresh token rotation (OAuth 2.1 requirement):**

```python
# Server returns new refresh token with each refresh
{
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token",  // Replaces old one
  "expires_in": 3600
}

# Old refresh token is invalidated
```

**API key rotation schedule:**

```bash
# Set calendar reminders
# Day 0: Generate new key
curl -X POST https://api.service.com/keys \
  -H "Authorization: Bearer ${OLD_KEY}"

# Day 1-7: Test new key in dev/staging
export MCP_API_KEY_NEW="new_key"

# Day 7: Deploy new key to production
export MCP_API_KEY="new_key"

# Day 14: Revoke old key
curl -X DELETE https://api.service.com/keys/old_key_id \
  -H "Authorization: Bearer ${NEW_KEY}"
```

### Token Revocation

**Immediate revocation when:**

- User logs out
- Token compromised
- Service access no longer needed
- User account deleted

**Implementation:**

```bash
# OAuth token revocation
curl -X POST https://auth.service.com/oauth/revoke \
  -d "token=${ACCESS_TOKEN}" \
  -d "client_id=${CLIENT_ID}"

# API key revocation
curl -X DELETE https://api.service.com/keys/${KEY_ID} \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"

# Remove from keychain
security delete-generic-password -a $USER -s mcp-token
```

---

## Common Vulnerabilities

### 1. Hardcoded Credentials

**Vulnerable:**

```json
{
  "headers": {
    "Authorization": "Bearer sk_live_abc123..."
  }
}
```

**Secure:**

```json
{
  "headers": {
    "Authorization": "Bearer ${MCP_ACCESS_TOKEN}"
  }
}
```

### 2. Committed Secrets

**Prevention:**

```bash
# Use git-secrets
git clone https://github.com/awslabs/git-secrets
cd git-secrets && make install
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add 'sk_live_[a-zA-Z0-9]+'
git secrets --add 'mcp_[a-zA-Z0-9]+'

# Scan repository
git secrets --scan
```

### 3. Insufficient Token Expiration

**Vulnerable:**

```json
{
  "expires_in": 31536000  // 1 year - too long!
}
```

**Secure:**

```json
{
  "expires_in": 3600  // 1 hour - appropriate
}
```

### 4. Missing TLS/HTTPS

**Vulnerable:**

```json
{
  "url": "http://api.service.com/mcp"  // Unencrypted!
}
```

**Secure:**

```json
{
  "url": "https://api.service.com/mcp"  // Encrypted
}
```

### 5. Token Leakage in Logs

**Vulnerable:**

```python
logging.info(f"Using token: {access_token}")  # Logs token!
```

**Secure:**

```python
logging.info(f"Using token: {access_token[:8]}...")  # Only prefix
# Or better: don't log tokens at all
logging.info("Authenticating with access token")
```

### 6. Overprivileged Scopes

**Vulnerable:**

```
scope=admin+full_access+delete  // Requesting too much!
```

**Secure:**

```
scope=mcp:read+mcp:write  // Minimum necessary
```

---

## Additional Resources

### Official Specifications

- [MCP Specification 2025](https://spec.modelcontextprotocol.io/)
- [OAuth 2.1 Draft](https://oauth.net/2.1/)
- [RFC 7636: PKCE](https://tools.ietf.org/html/rfc7636)
- [RFC 6749: OAuth 2.0](https://tools.ietf.org/html/rfc6749)

### Security Best Practices

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [OAuth Security Best Practices](https://oauth.net/2/oauth-best-practice/)
- [NIST Digital Identity Guidelines](https://pages.nist.gov/800-63-3/)

### Tools

- [git-secrets](https://github.com/awslabs/git-secrets) - Prevent committing secrets
- [truffleHog](https://github.com/trufflesecurity/truffleHog) - Find committed secrets
- [direnv](https://direnv.net/) - Environment variable management
- [1Password CLI](https://developer.1password.com/docs/cli/) - Secret management

### claudefig Documentation

- `ADDING_NEW_COMPONENTS.md` - MCP configuration guide
- `src/presets/default/components/mcp/http-oauth/README.md` - OAuth setup
- `src/presets/default/components/mcp/http-apikey/README.md` - API key management
- `src/presets/default/components/mcp/stdio-local/README.md` - STDIO setup

---

**Never commit credentials, even in "test" or "example" code!**
