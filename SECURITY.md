# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 2.0.x | ✅ Active support |
| 1.3.x | ⚠️ Security fixes only |
| < 1.3.0 | ❌ End of life |

## Reporting a Vulnerability

AICluster takes security seriously. We appreciate responsible disclosure.

### Process

1. **Do not open a public issue.** Email security@aicluster.local with:
   - Detailed description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

2. You will receive an acknowledgment within **48 hours**.

3. We will investigate and provide an initial assessment within **5 business days**.

4. Once a fix is developed, we will coordinate a release timeline with you.

### Response Timeline

| Timeframe | Action |
|---|---|
| 48 hours | Acknowledgment of receipt |
| 5 days | Initial triage and severity assessment |
| 14 days | Fix in progress or mitigation plan shared |
| 30 days | Patch released or advisory published |

### Scope

Security issues in the following areas are in scope:
- Authentication bypass
- JWT forgery
- SQL injection
- Path traversal
- Worker spoofing
- Privilege escalation
- Plugin sandbox escape
- Sensitive data exposure
- API abuse / rate limiting bypass

### Out of Scope
- Social engineering attacks
- Physical access attacks
- DoS attacks (without novel technique)
- Issues in third-party dependencies (report upstream)

## Security Architecture

AICluster v2.0.0 includes:

- **JWT Authentication**: HS256 with auto-generated 32-byte random secret key stored in `data/secret.key`
- **Password Hashing**: bcrypt with random salt via passlib
- **Rate Limiting**: 100 requests/minute on login endpoint (SlowAPI)
- **CORS Enforcement**: Restricted to configured origins
- **Worker Authentication**: JWT or shared secret key
- **Plugin Isolation**: Sandboxed execution with permission model
- **SQL Injection Prevention**: SQLAlchemy parameterized queries throughout
- **Secret Key Generation**: `secrets.token_hex(32)` on first run, persisted to `data/secret.key`

## Best Practices for Deployers

1. **Change the default password** immediately after first login (`admin`/`admin`)
2. **Set `AICLUSTER_ADMIN_PASSWORD`** environment variable for automated deployments
3. **Restrict network access** to the master server port (8000) within LAN only
4. **Enable Windows Firewall** rules (offered during installation)
5. **Keep AICluster updated** to the latest version
6. **Review worker registrations** periodically for unauthorized nodes
7. **Use the standalone installer** rather than manual Python setup for production
8. **Do not expose the API** to the public internet
9. **Audit logs regularly** via `/api/v1/audit/logs`
10. **Run AICluster without elevated privileges** unless required for hardware access
