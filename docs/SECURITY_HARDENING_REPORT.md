# Security Hardening Report

**AICluster v1.4 â€” Enterprise Packaging & Native Windows Architecture**
**Date:** 2026-07-05
**Current Version:** v2.0.0 (4 CRITICAL, 5 HIGH resolved in v2.0.0)

---

## 1. Current Security Posture

### 1.1 v2.0.0 Remediation Status

| ID | Finding | Severity | v2.0.0 Status | Notes |
|----|---------|----------|---------------|-------|
| S-001 | JWT secret hardcoded | CRITICAL | FIXED | Auto-generated 32-byte random key on first run |
| S-002 | Default admin credentials | CRITICAL | FIXED | Random password generated on first run |
| S-003 | No auth on API endpoints | CRITICAL | FIXED | JWT required on all 131 endpoints |
| S-010 | Plugin upload RCE | CRITICAL | **NOT FIXED** | ZIP + importlib without validation |
| S-005 | CORS wildcard | HIGH | FIXED | Restricted to configured origins |
| S-007 | No rate limiting | HIGH | FIXED | Slowapi middleware, 100/min default |
| S-008 | WebSocket without auth | HIGH | FIXED | JWT + worker_secret required |
| S-009 | Worker no auth | HIGH | FIXED | Worker_secret required for registration |
| S-006 | Path traversal in workers | HIGH | FIXED | Path validation implemented |
| S-012 | SQL injection risk | HIGH | FIXED | Regex timeout + parameterized queries |
| S-004 | No HTTPS | HIGH | **NOT FIXED** | All traffic plain HTTP |
| S-011 | Worker no auth on API | MEDIUM | FIXED | Worker_secret implemented |

### 1.2 Remaining Vulnerabilities

| # | Finding | Severity | Category | Description |
|---|---------|----------|----------|-------------|
| V-001 | Plugin upload arbitrary code execution | CRITICAL | Plugin | ZIP upload + importlib without sandbox |
| V-002 | No HTTPS in default configuration | HIGH | Network | All traffic sent in plaintext |
| V-003 | Token stored in localStorage | MEDIUM | Auth | XSS vulnerability via localStorage |
| V-004 | Information disclosure in error messages | MEDIUM | Error Handling | Stack traces may leak to users |
| V-005 | No CSRF protection | LOW | Web | No CSRF tokens on API endpoints |
| V-006 | Weak JWT signing algorithm | LOW | Auth | HS256 only, no RSA/ECDSA support |
| V-007 | Plugin sandbox incomplete | MEDIUM | Plugin | Plugins run with full process permissions |
| V-008 | No input size limits on API | MEDIUM | API | Large payloads can exhaust memory |

---

## 2. Attack Surface Analysis

### 2.1 Attack Vectors

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    ATTACK SURFACE                           â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                            â”‚
â”‚  NETWORK (port 8000/8001)                                  â”‚
â”‚  â”œâ”€â”€ REST API (131 endpoints)                              â”‚
â”‚  â”‚   â”œâ”€â”€ Unauthenticated: /health, /docs, /redoc, /openapiâ”‚
â”‚  â”‚   â”œâ”€â”€ Authenticated: All others (JWT required)          â”‚
â”‚  â”‚   â””â”€â”€ Rate limited: 100/min default                     â”‚
â”‚  â”‚                                                         â”‚
â”‚  â”œâ”€â”€ WebSocket (/ws)                                       â”‚
â”‚  â”‚   â”œâ”€â”€ Requires JWT token in query params                â”‚
â”‚  â”‚   â””â”€â”€ Rate limited                                       â”‚
â”‚  â”‚                                                         â”‚
â”‚  â”œâ”€â”€ Static file serving (/static)                         â”‚
â”‚  â”‚   â””â”€â”€ Restricted to configured static directory         â”‚
â”‚  â”‚                                                         â”‚
â”‚  â””â”€â”€ Worker API (port 8001)                                â”‚
â”‚      â””â”€â”€ Health endpoint only (no sensitive operations)    â”‚
â”‚                                                            â”‚
â”‚  LOCAL (filesystem)                                        â”‚
â”‚  â”œâ”€â”€ Plugin directory                                      â”‚
â”‚  â”‚   â””â”€â”€ ZIP extraction â†’ importlib (RCE risk)            â”‚
â”‚  â”œâ”€â”€ Configuration files                                   â”‚
â”‚  â”‚   â””â”€â”€ Secrets in config/ (JWT key, admin password)      â”‚
â”‚  â”œâ”€â”€ Log files                                             â”‚
â”‚  â”‚   â””â”€â”€ Sensitive data may be logged                      â”‚
â”‚  â”œâ”€â”€ SQLite database                                       â”‚
â”‚  â”‚   â””â”€â”€ File permissions protect                          â”‚
â”‚  â””â”€â”€ Artifact storage                                      â”‚
â”‚      â””â”€â”€ File-based, no path traversal in v2.0.0           â”‚
â”‚                                                            â”‚
â”‚  API INPUT                                                 â”‚
â”‚  â”œâ”€â”€ Pydantic validation on all endpoints                  â”‚
â”‚  â”œâ”€â”€ Path traversal blocked in worker handlers             â”‚
â”‚  â””â”€â”€ SQL injection blocked (parameterized queries)         â”‚
â”‚                                                            â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 2.2 Trust Boundaries

```
[External Network]
       â”‚
       â”‚ HTTPS (target)
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Master Server   â”‚â”€â”€â”€â”€ â”‚  Web Frontend   â”‚
â”‚  (port 8000)     â”‚     â”‚  (port 3000)    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â”‚ HTTP (LAN)
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Worker Agent   â”‚
â”‚  (port 8001)    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

Trust zones:
  [GREEN]  Master + Frontend on same machine (trusted)
  [AMBER]  Workers on network (semi-trusted, authenticated)
  [RED]    External network (untrusted, not connected by default)
```

---

## 3. Hardening Actions

### 3.1 Critical: Fix Plugin Upload RCE (V-001)

```python
# backend/app/plugins/installer.py â€” Proposed fix

import zipfile
import tempfile
import os
import hashlib
from pathlib import Path

class PluginInstaller:
    """Secure plugin installer with sandbox extraction."""
    
    ALLOWED_EXTENSIONS = {'.py', '.json', '.md', '.txt', '.yaml', '.yml'}
    MAX_PLUGIN_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_FILE_SIZE = 10 * 1024 * 1024     # 10 MB per file
    
    def install(self, zip_path: Path) -> dict:
        # 1. Validate file size
        if zip_path.stat().st_size > self.MAX_PLUGIN_SIZE:
            raise ValueError("Plugin exceeds maximum size")
        
        # 2. Extract to temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Validate all entries before extraction
                for entry in zf.infolist():
                    self._validate_entry(entry)
                zf.extractall(tmpdir)
            
            # 3. Validate manifest
            manifest_path = Path(tmpdir) / "plugin.json"
            if not manifest_path.exists():
                raise ValueError("Missing plugin.json manifest")
            
            # 4. Validate plugin structure
            self._validate_plugin_structure(Path(tmpdir))
            
            # 5. Security scan (optional, future)
            # self._scan_for_threats(Path(tmpdir))
            
            # 6. Copy to plugins directory with validation
            plugin_id = self._load_and_validate_manifest(manifest_path)
            dest = PLUGINS_DIR / plugin_id
            if dest.exists():
                raise ValueError(f"Plugin {plugin_id} already installed")
            
            # Copy with file extension whitelist
            for f in Path(tmpdir).rglob("*"):
                if f.is_file() and f.suffix in self.ALLOWED_EXTENSIONS:
                    rel = f.relative_to(tmpdir)
                    target = dest / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    # Read and write to avoid symlink attacks
                    target.write_bytes(f.read_bytes())
            
            # 7. Verify checksum
            self._generate_checksum(dest)
        
        return {"plugin_id": plugin_id, "status": "installed"}
    
    def _validate_entry(self, entry: zipfile.ZipInfo):
        """Prevent zip slip path traversal."""
        if entry.file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {entry.filename}")
        # Normalize path and check for traversal
        path = Path(entry.filename).resolve()
        if ".." in entry.filename or path.is_absolute():
            raise ValueError(f"Invalid path: {entry.filename}")
        # Reject symlinks
        if entry.external_attr >> 16 & 0o120000:  # S_ISLNK
            raise ValueError(f"Symlinks not allowed: {entry.filename}")
```

### 3.2 High: Add HTTPS Support (V-002)

```python
# backend/app/main.py â€” Optional HTTPS support

import ssl

def create_ssl_context(cert_path: Path, key_path: Path) -> ssl.SSLContext:
    """Create SSL context with modern TLS configuration."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    
    # Only TLS 1.3 ciphers
    context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM")
    
    context.load_cert_chain(cert_path, key_path)
    context.load_verify_locations(cert_path)
    context.verify_mode = ssl.CERT_REQUIRED
    
    return context

# In uvicorn.run():
# if settings.use_https and settings.cert_path and settings.key_path:
#     uvicorn.run(
#         app,
#         host=host,
#         port=port,
#         ssl_certfile=settings.cert_path,
#         ssl_keyfile=settings.key_path,
#         ssl_version=ssl.PROTOCOL_TLS_SERVER,
#     )
```

### 3.3 Medium: Secure Token Storage (V-003)

```typescript
// frontend/src/stores/auth.ts â€” Move from localStorage to sessionStorage
// or use Tauri's secure storage plugin

// Before (v2.0.0):
// export const useAuthStore = create<AuthState>()(
//   persist(
//     (set) => ({ ... }),
//     { name: 'aicluster-auth' }  // localStorage by default
//   )
// );

// After (v1.4):
import { StoreApi } from 'zustand';

// Use sessionStorage (cleared on tab close):
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({ ... }),
    { 
      name: 'aicluster-auth',
      storage: createJSONStorage(() => sessionStorage)  // More secure than localStorage
    }
  )
);

// For even better security in Tauri, use the secure store plugin:
// import { Store } from 'tauri-plugin-store';
// const store = new Store('.secrets.dat');
// await store.set('token', jwtToken);
```

### 3.4 Medium: Error Message Sanitization (V-004)

```python
# backend/app/middleware/error_handler.py â€” New middleware

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        # Log full traceback internally
        logger.error("Unhandled exception: %s", traceback.format_exc())
        
        # Return sanitized error to user
        if settings.debug:
            # Development: show details
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(exc),
                    "traceback": traceback.format_exc().split("\n")
                }
            )
        else:
            # Production: hide internals
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
```

### 3.5 Medium: Input Size Limits (V-008)

```python
# backend/app/config.py â€” Add input size limits

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Input size limits
    max_request_body_size: int = 10 * 1024 * 1024  # 10 MB
    max_plugin_size: int = 50 * 1024 * 1024        # 50 MB
    max_artifact_size: int = 100 * 1024 * 1024     # 100 MB
    max_chat_message_length: int = 100000          # 100k chars
    max_batch_operations: int = 1000               # Max items per batch

# Apply in FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    max_request_size=settings.max_request_body_size,  # Add this
)
```

---

## 4. Configuration Security

### 4.1 Secret Storage

```yaml
# config/secrets.yaml â€” Encrypted secrets file (AES-256-GCM)

# This file is encrypted at rest.
# Decrypted by the launcher on startup using a key derived from
# Windows DPAPI (CryptProtectData).

secrets:
  jwt_secret: "AIClusterGenerated32ByteSecretKey!"
  admin_password_hash: "$2b$12$..."  # bcrypt hash
  worker_secret: "worker-shared-secret"
  db_encryption_key: "encryption-key-for-sensitive-db-fields"
```

### 4.2 Configuration Loading Chain

```
1. Compiled defaults (in EXE, read-only)
        â”‚
2. config/default.yaml (shipped with app, read-only)
        â”‚
3. config/production.yaml (admin-configured, user-writable)
        â”‚
4. config/secrets.enc (encrypted, auto-generated)
        â”‚
5. Environment variables (overrides everything)
```

### 4.3 Least Privilege Configuration

```yaml
# config/default.yaml â€” v1.4 Hardened defaults

security:
  authentication:
    enabled: true                    # JWT required on all endpoints
    jwt_algorithm: HS256             # HMAC-SHA256
    jwt_expiry_minutes: 60           # Token expires after 1 hour
    session_expiry_hours: 24         # Session max lifetime
  
  rate_limiting:
    enabled: true                    # Rate limiting active
    default_limit: "100/minute"      # 100 requests per minute
    login_limit: "10/minute"         # 10 login attempts per minute
    worker_limit: "200/minute"       # Workers get higher limit
  
  network:
    bind_address: "127.0.0.1"        # Localhost only by default
    cors_origins: []                 # No CORS by default (same-origin)
    https_only: false                # HTTPS disabled until cert configured
    require_client_cert: false       # mTLS disabled by default
  
  plugins:
    enabled: true                    # Plugin system enabled
    sandbox_enabled: true            # Sandbox isolation
    max_plugin_size_mb: 50           # Max plugin size
    allow_unsigned: false            # Require signed plugins
    allowed_hooks: []                # All hooks allowed (empty = all)
  
  logging:
    level: "info"                    # Production log level
    log_request_bodies: false        # Don't log sensitive data
    log_headers: false               # Don't log request headers
    log_query_params: false          # Don't log query parameters
    sanitize_fields:                 # Fields to mask in logs
      - "password"
      - "token"
      - "authorization"
      - "secret"
      - "key"
```

---

## 5. Binary Protection

### 5.1 Build Hardening

```python
# build/config.py â€” Release build configuration

class ReleaseConfig:
    """Hardened release configuration for v1.4."""
    
    # PyInstaller options
    strip_binaries: bool = True           # Strip debug symbols
    upx: bool = False                     # UPX compression (disable for AV compat)
    console: bool = False                 # No console window (GUI mode)
    disable_windowed_traceback: bool = True  # Don't show tracebacks in GUI
    
    # Code signing
    sign_enabled: bool = True             # Authenticode signing
    sign_algorithm: str = "SHA256"        # Modern hash algorithm
    timestamp_server: str = "http://timestamp.digicert.com"
    
    # Version info (embedded in PE)
    company_name: str = "AICluster"
    file_description: str = "AICluster - Offline AI Cluster Platform"
    legal_copyright: str = "Copyright (c) 2026 AICluster"
    product_name: str = "AICluster"
```

### 5.2 Release Hardening Checklist

```markdown
## Release Hardening Checklist â€” v1.4.0

### Pre-Build
- [ ] All `.env` files removed from source
- [ ] All debug/development configurations removed
- [ ] All test files excluded from release package
- [ ] All documentation assets verified for sensitive info
- [ ] Source code reviewed for hardcoded secrets

### Build
- [ ] PyInstaller: `--strip` enabled (debug symbols removed)
- [ ] PyInstaller: `--windowed` (no console window)
- [ ] PyInstaller: `--disable-windowed-traceback`
- [ ] All executables are valid PE32+ binaries
- [ ] UPX compression disabled (AV compatibility)
- [ ] Version metadata embedded in all EXEs

### Signing
- [ ] Authenticode signature applied to all EXEs
- [ ] SHA-256 digest algorithm used
- [ ] RFC 3161 timestamp included
- [ ] Signature verified with `signtool verify /pa /all`

### Post-Build
- [ ] All EXEs scanned with Windows Defender
- [ ] All EXEs scanned with VirusTotal (optional)
- [ ] No internal paths exposed in binaries
- [ ] No PDB/debug files shipped
- [ ] No source code files in release package
- [ ] Checksums generated and GPG-signed

### Verification
- [ ] Clean install on Windows 10 22H2
- [ ] Clean install on Windows 11 24H2
- [ ] Upgrade from v2.0.0
- [ ] Repair install
- [ ] Uninstall (complete removal)
- [ ] No leftover files after uninstall
- [ ] All 98 tests pass
```

---

## 6. Logging Security

### 6.1 Sensitive Data Redaction

```python
# backend/app/logging_config.py â€” Enhanced with redaction

import re
from typing import List

SENSITIVE_FIELDS: List[str] = [
    "password", "token", "authorization", "secret", "key",
    "jwt", "credential", "api_key", "passwd", "access_token",
    "refresh_token", "session_id", "cookie"
]

SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r'(?i)(password|secret|token|key)\s*[:=]\s*["\']?[^"\'&\s]+'),
    re.compile(r'(?i)(authorization|bearer)\s+\S+'),
    re.compile(r'(?i)(api[_-]?key)\s*[:=]\s*\S+'),
]

def sanitize_log_message(message: str) -> str:
    """Redact sensitive data from log messages."""
    for pattern in SENSITIVE_PATTERNS:
        message = pattern.sub(r'\1: [REDACTED]', message)
    return message

class SanitizedFileHandler(RotatingFileHandler):
    """Log handler that redacts sensitive data."""
    
    def emit(self, record: logging.LogRecord) -> None:
        original = record.msg
        record.msg = sanitize_log_message(record.msg)
        try:
            super().emit(record)
        finally:
            record.msg = original  # Restore for other handlers
```

### 6.2 Secure Audit Logging

```python
# backend/app/audit/service.py â€” Ensure no secrets in audit logs

class AuditService:
    
    SENSITIVE_PATHS = [
        "/api/v1/auth/login",
        "/api/v1/auth/token",
        "/api/v1/workers/register",
    ]
    
    SENSITIVE_HEADERS = [
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
        "x-session-id",
    ]
    
    async def log_event(self, event: AuditEvent):
        # Mask sensitive fields before storing
        if event.path in self.SENSITIVE_PATHS:
            event.request_body = "[REDACTED]"
            event.response_body = "[REDACTED]"
        
        # Mask sensitive headers
        if event.request_headers:
            event.request_headers = {
                k: "[REDACTED]" if k.lower() in self.SENSITIVE_HEADERS else v
                for k, v in event.request_headers.items()
            }
        
        # Store to database
        async with self.get_session() as session:
            session.add(event.to_model())
            await session.commit()
```

---

## 7. Security Documentation

### 7.1 New Documents

| Document | Location | Purpose |
|----------|----------|---------|
| `SECURITY_HARDENING.md` | `docs/Security/SECURITY_HARDENING.md` | This report |
| `SECURITY.md` | Root + `docs/Security/SECURITY.md` | Security policy |
| `SECURITY_REVIEW.md` | `docs/Audit/SECURITY_REVIEW.md` | Updated security review |
| `THREAT_MODEL.md` | `docs/Security/THREAT_MODEL.md` | Threat model document |
| `RELEASE_HARDENING.md` | `docs/Security/RELEASE_HARDENING.md` | Build hardening checklist |

---

## 8. Ongoing Security Maintenance

### 8.1 Dependency Scanning

```yaml
# .github/workflows/security.yml â€” New workflow

name: Security Scan
on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday
  push:
    branches: [main, develop]

jobs:
  dependency-scan:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt safety
      - name: Safety scan
        run: safety check -r backend/requirements.txt
      - name: Bandit SAST
        run: pip install bandit && bandit -r backend/app/ -f json -o bandit-report.json
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            safety-report.json
            bandit-report.json
```

### 8.2 Secret Scanning

Pre-commit hook to prevent committing secrets:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

---

## 9. Success Criteria

- [ ] Plugin upload RCE vulnerability fixed (V-001)
- [ ] HTTPS support added with TLS 1.3 (V-002)
- [ ] Token storage moved to sessionStorage/Tauri secure store (V-003)
- [ ] Error messages sanitized in production mode (V-004)
- [ ] Input size limits enforced on all endpoints (V-008)
- [ ] Secrets encrypted at rest in configuration
- [ ] Log messages redact sensitive data
- [ ] All audit paths/headers sanitized
- [ ] Executables stripped of debug symbols
- [ ] Code signing configured and verified
- [ ] Dependency scanning in CI
- [ ] Secret scanning pre-commit hook configured
- [ ] Release hardening checklist documented
- [ ] All 98 existing tests pass
