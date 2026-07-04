# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.3.x   | ✅ Active development |
| 1.2.x   | ✅ Security patches |
| 1.1.x   | ✅ Security patches |
| 1.0.x   | ❌ End of life |
| < 1.0   | ❌ End of life |

## Reporting a Vulnerability

If you discover a security vulnerability in AICluster, please report it by emailing:

**manoj.spoffice.kri@gmail.com**

Do **not** report security vulnerabilities via public GitHub issues.

### What to include

- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Potential impact
- Any suggested fix (if known)

### Response timeline

| Timeframe | Action |
|-----------|--------|
| 24 hours  | Acknowledgment of receipt |
| 72 hours  | Initial triage and severity assessment |
| 7 days    | Fix in progress or mitigation plan shared |
| 14 days   | Patch released or detailed advisory published |

## Security Response Process

1. **Report received** — triage team acknowledges within 24 hours
2. **Assessment** — vulnerability is classified by severity (Critical, High, Medium, Low)
3. **Fix development** — a patch is developed and reviewed internally
4. **Patch release** — fix is published as a patch release for all supported versions
5. **Disclosure** — advisory is published after users have had reasonable time to update

## Recommended Security Practices

- Change the default `admin` password immediately after installation
- Run AICluster on a trusted local network — do not expose the API to the internet
- Use environment variables or a secrets manager for `SECRET_KEY` and database credentials
- Enable HTTPS in production using a reverse proxy (e.g., nginx, Caddy)
- Restrict API access via firewall rules to known worker and dashboard IPs
- Regularly audit audit logs (`/api/v1/audit/logs`) for suspicious activity
- Keep all dependencies updated — run `pip-audit` and `npm audit` regularly
- Do not run AICluster with elevated/administrator privileges unless required
- Configure rate limiting to mitigate brute-force attacks on authentication endpoints
- Review plugin manifests before installation — plugins have access to system APIs
