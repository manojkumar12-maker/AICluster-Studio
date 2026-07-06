# SECURITY REVIEW â€” AICluster v2.0.0

## Scope

This security review covers the AICluster platform codebase at version 1.3.0. The review examines all subsystems: backend API, worker agent, frontend, master control center, worker control center, shared protocols, plugin system, and build infrastructure.

## Rating Scale

| Rating | Definition |
|--------|------------|
| CRITICAL | Immediate exploitation risk. Remote code execution, authentication bypass, data exfiltration. Must fix before production. |
| HIGH | Significant risk. Privilege escalation, sensitive data exposure, denial of service. Should fix urgently. |
| MEDIUM | Moderate risk. Limited impact, requires specific conditions, defense in depth. Fix in normal cycle. |
| LOW | Minor risk. Low impact, difficult to exploit, informational. Fix when convenient. |

---

## Finding 1: JWT Secret Key Hardcoded in Source

**File**: `backend/app/config.py:14`
**Rating**: CRITICAL
**CVE Pattern**: CWE-798 (Use of Hardcoded Credentials)

The JWT signing secret is hardcoded as `"aicluster-secret-key-change-in-production"`. This value is a well-known string published in the README and source code. An attacker who knows the secret can forge arbitrary JWT tokens, impersonate any user (including admin), and gain full access to the API.

The `Settings` class reads from a `.env` file, but the default value in the class definition means that if `.env` is missing or does not contain `SECRET_KEY`, the hardcoded fallback is used without any warning.

**Evidence**:
```python
# backend/app/config.py:14
secret_key: str = "aicluster-secret-key-change-in-production"
```

**Impact**: Complete authentication bypass. Any network attacker who can reach the API can forge admin tokens.

**Recommendation**:
1. Remove the default value â€” require `SECRET_KEY` to be explicitly set in the environment
2. Add a startup validation that warns if the default key is detected
3. Generate a strong random key on first startup if none is configured
4. Implement key rotation support

---

## Finding 2: Default Admin Credentials

**File**: `backend/app/services/auth.py:44-55`
**Rating**: CRITICAL
**CVE Pattern**: CWE-798 (Use of Hardcoded Credentials)

The default admin account uses credentials `admin` / `admin123`, which are documented in the README. This combination is trivially guessable and will be the first thing an attacker tries.

**Evidence**:
```python
# backend/app/services/auth.py:49-52
admin = User(
    username="admin",
    hashed_password=pwd_context.hash("admin123"),
    role="admin",
)
```

**Impact**: Immediate admin access if the login endpoint is exposed and the default password has not been changed.

**Recommendation**:
1. Force password change on first login
2. Generate a random initial password and print it to the console during first startup
3. Implement password complexity requirements
4. Add rate limiting to the login endpoint (see Finding 7)

---

## Finding 3: CORS Misconfiguration

**File**: `backend/app/main.py:69-75`
**Rating**: HIGH
**CVE Pattern**: CWE-942 (Permissive Cross-domain Policy with Untrusted Domains)

The CORS middleware permits requests from origins specified in `settings.get_cors_origins_list()`. By default, this allows `http://localhost:3000`. However, the middleware also sets `allow_credentials=True`, which combined with a permissive origin list could allow credential theft. While the current default is restrictive, the configuration accepts comma-separated origins from the `CORS_ORIGINS` environment variable, which could be set to `*` by an administrator.

**Evidence**:
```python
# backend/app/main.py:69-75
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# backend/app/config.py:33-34
def get_cors_origins_list(self) -> list[str]:
    return [o.strip() for o in self.cors_origins.split(",")]
```

**Impact**: If CORS_ORIGINS is misconfigured to include `*`, any website can make credentialed requests to the AICluster API. An attacker who tricks an authenticated admin user into visiting a malicious site can exfiltrate cluster data.

**Recommendation**:
1. Validate that CORS_ORIGINS does not contain `*` when `allow_credentials=True`
2. Add a warning when permissive CORS is detected
3. Consider restricting `allow_methods` to only the HTTP methods actually used

---

## Finding 4: Path Traversal in Worker Handlers

**Files**: 
- `worker/app/executor/handlers/dir_scan.py:8`
- `worker/app/executor/handlers/hash_file.py:8`
- `worker/app/executor/handlers/count_files.py:8`
**Rating**: HIGH
**CVE Pattern**: CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)

The `dir_scan`, `hash_file`, and `count_files` handlers accept a `directory` or `filepath` parameter from the job payload and pass it directly to `os.walk()` or `open()` without any path validation, sanitization, or restriction. A malicious job could specify `..` or absolute paths to read arbitrary files on the worker machine.

**Evidence**:
```python
# worker/app/executor/handlers/dir_scan.py:8-9
directory = payload.get("directory", ".")
results = []
# ...
for root, dirs, files in os.walk(directory):
```

```python
# worker/app/executor/handlers/hash_file.py:8-9
filepath = payload.get("filepath", "")
# ...
with open(filepath, "rb") as f:
```

**Impact**: Any machine that can submit jobs to the cluster can read arbitrary files from any worker machine. This includes sensitive documents, configuration files, credentials, and source code.

**Recommendation**:
1. Use `os.path.abspath()` and validate the resolved path is within an allowed base directory
2. Restrict file system access to a designated workspace directory per worker
3. Implement path allowlisting in the worker configuration
4. Add path traversal pattern detection and rejection

---

## Finding 5: No Authentication on Most API Endpoints

**Files**: All files in `backend/app/api/v1/*.py`
**Rating**: CRITICAL
**CVE Pattern**: CWE-306 (Missing Authentication for Critical Function)

The `get_current_user` dependency is defined in `backend/app/services/auth.py:64-98` but is NOT used on any API endpoint. All endpoints in `workers.py`, `jobs.py`, `dashboard.py`, `health.py`, `logs.py`, `workflows.py`, `repositories.py`, `ai.py`, `agents.py`, `engineering.py`, `production.py`, `plugins.py`, `studio.py`, and `audit/api.py` accept requests without authentication.

The only protected functionality is the login endpoint itself, which obviously must be public.

**Evidence**: Grep for `get_current_user` across all API route files shows zero usages.

**Impact**: Any machine on the network (or any origin, depending on CORS config) can:
- Register and remove workers
- Submit and cancel jobs
- View all system logs and audit data
- Access repository code and symbols
- Execute AI prompts
- Install and remove plugins
- Create, modify, and delete workflows
- Access and modify all engineering plans

**Recommendation**:
1. Add `get_current_user` dependency to all endpoints immediately
2. Consider a global authentication middleware that blocks unauthenticated requests by default
3. Implement role-based access control (admin, developer, viewer)

---

## Finding 6: JWT Token Stored in localStorage

**File**: `frontend/src/stores/auth-store.ts`
**Rating**: MEDIUM
**CVE Pattern**: CWE-312 (Cleartext Storage of Sensitive Information)

The frontend stores the JWT access token in browser localStorage. This is a common pattern but is vulnerable to XSS attacks. If an attacker injects JavaScript into the frontend (via a compromised dependency, XSS in a plugin, or a malicious prompt response), they can exfiltrate the token.

**Evidence**: Zustand persist middleware stores the auth state (including token) in localStorage.

**Impact**: Token theft via XSS leads to account takeover. The attacker can use the stolen token to access the API.

**Recommendation**:
1. Use HttpOnly cookies for token storage instead of localStorage
2. If localStorage must be used, implement token encryption
3. Add Content Security Policy headers to mitigate XSS
4. Implement short token expiry with refresh tokens

---

## Finding 7: No Rate Limiting

**File**: `backend/app/main.py`
**Rating**: HIGH
**CVE Pattern**: CWE-799 (Improper Control of Interaction Frequency)

There is no rate limiting middleware configured anywhere in the application. The login endpoint is particularly vulnerable â€” an attacker can attempt unlimited password guesses against the admin account without any throttling.

**Evidence**: No rate limiting imports or middleware in `main.py` or `config.py`. The PROJECT_STATE.md mentions "Rate limiting on API endpoints" as a completed feature, but no rate limiting implementation exists in the codebase.

**Impact**: Brute force password attacks, API abuse, resource exhaustion DoS.

**Recommendation**:
1. Implement rate limiting on the login endpoint (5 attempts per IP per minute)
2. Add per-endpoint rate limiting (100 requests/minute for read endpoints, 20 for write endpoints)
3. Consider slowapi or a custom rate limiter
4. Add IP-based blocking after repeated violations

---

## Finding 8: WebSocket Without Authentication

**File**: `backend/app/main.py:80-96`
**Rating**: HIGH
**CVE Pattern**: CWE-306 (Missing Authentication for Critical Function)

The WebSocket endpoint at `/ws` accepts connections from any client without any authentication. There is no token validation, no origin check beyond the client IP, and no authentication handshake. Any client on the network can:

- Receive all real-time cluster updates (worker registrations, job progress, dashboard metrics)
- Send arbitrary messages (though processing is limited to "ping" text)

**Evidence**:
```python
# backend/app/main.py:80-96
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # No authentication check
```

**Impact**: Information disclosure â€” an attacker can monitor all cluster activity in real time. This reveals cluster topology, worker status, job submissions and completion, and potentially sensitive data.

**Recommendation**:
1. Require a valid JWT token as a query parameter on WebSocket connection (`/ws?token=...`)
2. Validate the token before accepting the connection
3. Reject connections without valid tokens with close code 4001

---

## Finding 9: Information Disclosure via Error Messages

**Files**: Multiple API route files
**Rating**: MEDIUM
**CVE Pattern**: CWE-209 (Generation of Error Message Containing Sensitive Information)

Several API endpoints return detailed error messages that leak internal implementation details:

- `backend/app/api/v1/workers.py:37`: `raise HTTPException(status_code=500, detail=str(e))` â€” leaks raw exception messages
- `backend/app/api/v1/workers.py:63`: `raise HTTPException(status_code=404, detail=str(e))` â€” leaks "Worker X not found" which can be used for enumeration
- `backend/app/api/v1/plugins.py:37`: Returns validation error details that may reveal file paths
- `backend/app/api/v1/repositories.py:43`: Returns full repository path (may leak internal file system structure)

**Evidence**:
```python
# backend/app/api/v1/workers.py:36-37
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

**Impact**: Attackers can enumerate valid worker/job IDs, discover file system structure, and learn about internal implementation details.

**Recommendation**:
1. Return generic error messages to clients ("Internal server error")
2. Log detailed errors server-side instead of returning them to the client
3. Implement a consistent error response format that separates user-safe and debug information

---

## Finding 10: Plugin Upload RCE Risk

**File**: `backend/app/api/v1/plugins.py:53-66`
**Rating**: CRITICAL
**CVE Pattern**: CWE-434 (Unrestricted Upload of File with Dangerous Type)

The plugin upload endpoint accepts a ZIP file and extracts it to the plugins directory. The extracted Python files are then loaded and executed via `importlib.import_module()`. There is no validation of the ZIP contents before extraction â€” an attacker can upload a ZIP containing arbitrary Python code that will be executed on the master server.

Additionally, the `PluginLoader.load_plugin()` method at `plugins/loader/service.py:22-24` inserts the plugin directory into `sys.path` and imports the entry point module, executing any code in that module.

**Evidence**:
```python
# backend/app/api/v1/plugins.py:53-66
async def upload_plugin(file: UploadFile = File(...)):
    plugin_dir = PLUGINS_DIR / file.filename.replace(".zip", "")
    plugin_dir.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    with zipfile.ZipFile(BytesIO(content)) as zf:
        zf.extractall(str(plugin_dir))
    # No validation of extracted content
```

```python
# backend/app/plugins/loader/service.py:22-28
sys.path.insert(0, str(plugin_path))
module = importlib.import_module(manifest.entry_point.replace(".py", ""))
if hasattr(module, "Plugin"):
    plugin_class = getattr(module, "Plugin")
    instance = plugin_class()
```

**Impact**: Complete remote code execution on the master server. An attacker who can reach the plugin upload endpoint can execute arbitrary Python code with the full privileges of the AICluster process.

**Recommendation**:
1. Add authentication to the plugin upload endpoint (see Finding 5)
2. Validate ZIP contents before extraction (check for path traversal, check file types)
3. Extract to a temporary directory first for validation
4. Implement plugin signing with cryptographic verification
5. Run plugins in a sandboxed environment (subprocess with restricted permissions)
6. Add plugin size limits

---

## Finding 11: Worker Registration Without Authentication

**Files**: 
- `backend/app/api/v1/workers.py:22-37`
- `worker/app/services/registrar.py:20-47`
**Rating**: MEDIUM
**CVE Pattern**: CWE-306 (Missing Authentication for Critical Function)

Any machine on the network can register as a worker by sending a POST request to `/api/v1/workers/register`. The worker registration endpoint accepts name, hostname, and IP address without any authentication token or API key.

The worker HTTP client (worker/app/utils/http_client.py) sends no authentication headers.

**Evidence**:
```python
# backend/app/api/v1/workers.py:22-23
@router.post("/workers/register", response_model=WorkerRegisterResponse)
async def register_worker(data: WorkerRegisterRequest, db: AsyncSession = Depends(get_db)):
    # No authentication
```

**Impact**: An attacker can register fake workers, poll for jobs (receiving job payloads), submit fake results, and disrupt the cluster's scheduling decisions.

**Recommendation**:
1. Implement worker API key authentication (pre-shared key per worker)
2. Validate worker IP addresses against subnet allowlist
3. Require worker registration approval for untrusted networks

---

## Finding 12: No CSRF Protection

**Rating**: MEDIUM
**CVE Pattern**: CWE-352 (Cross-Site Request Forgery)

There is no CSRF protection on any API endpoint. While the frontend uses JWT tokens stored in localStorage (which are not automatically sent with requests), any authenticated request from a browser context could be vulnerable if an attacker tricks a user into making a request.

CORS restrictions mitigate this for browser-based attacks, but they do not protect native API clients.

**Impact**: Limited â€” CORS mitigates browser-based CSRF risks. However, native applications and non-browser HTTP clients are not protected.

**Recommendation**:
1. Add CSRF tokens for browser-based authentication flows
2. Use SameSite cookies for token storage
3. Implement anti-replay mechanisms (nonce) for critical operations

---

## Finding 13: Weak Cipher Configuration

**File**: `backend/app/config.py:15`
**Rating**: LOW
**CVE Pattern**: CWE-326 (Inadequate Encryption Strength)

The JWT algorithm is configured as `HS256`, which is acceptable, but there is no support for stronger algorithms (HS384, HS512) or asymmetric signing (RS256, ES256). Additionally, the `python-jose` library used for JWT operations has slower maintenance compared to alternatives like `PyJWT`.

**Evidence**:
```python
# backend/app/config.py:15
algorithm: str = "HS256"
```

**Impact**: Low â€” HS256 is still secure when used with a strong, random key. The real risk is the hardcoded secret (Finding 1), not the algorithm choice.

**Recommendation**:
1. Consider supporting RS256 for token signing
2. Migrate from python-jose to PyJWT for better maintenance

---

## Finding 14: Sensitive Data in Logs

**File**: `backend/app/audit/middleware.py:36-46`
**Rating**: MEDIUM
**CVE Pattern**: CWE-532 (Insertion of Sensitive Information into Log File)

The audit middleware logs request information including safe headers. However, the middleware explicitly logs `request.client.host` (client IP address) and the complete request path. If sensitive data is passed in URL query parameters, it will be written to the audit log.

**Evidence**:
```python
# backend/app/audit/middleware.py:38-39
"ip_address": request.client.host if request.client else None,
# ... 
"path": path,
```

**Impact**: If sensitive parameters are passed in URLs (e.g., tokens, API keys), they will be logged in plaintext.

**Recommendation**:
1. Sanitize URL query parameters for sensitive patterns before logging
2. Add a configurable list of parameter names to redact
3. Consider masking URL paths that contain UUIDs

---

## Finding 15: SQL Injection Risk in Search Service

**File**: `backend/app/repository/search/service.py:77-81`
**Rating**: MEDIUM
**CVE Pattern**: CWE-89 (Improper Neutralization of Special Elements used in an SQL Command)

The regex-based text search compiles user input into a regex pattern and uses it to search file contents. While this does not directly inject SQL, the `ILIKE` queries used elsewhere could be vulnerable if user input is not properly sanitized. Additionally, the search service opens arbitrary files on the file system for text search, which could be used for information disclosure.

**Evidence**:
```python
# backend/app/repository/search/service.py:61
pattern = re.compile(query, re.IGNORECASE) if regex else None
# ...
# backend/app/repository/search/service.py:77-78
if regex and pattern:
    if pattern.search(line):
```

**Impact**: An attacker could use regex-based search for ReDoS (Regular Expression Denial of Service) by providing a catastrophic backtracking pattern.

**Recommendation**:
1. Set a timeout for regex operations
2. Limit the length of search queries
3. Limit the number of files searched per request

---

## Finding 16: No HTTPS

**File**: `backend/app/config.py:10-11`
**Rating**: HIGH
**CVE Pattern**: CWE-319 (Cleartext Transmission of Sensitive Information)

The application runs on plain HTTP by default. All API traffic â€” including JWT tokens, job payloads, repository data, and AI prompts â€” is transmitted in cleartext over the network.

**Evidence**:
```python
# backend/app/config.py:10-11
host: str = "0.0.0.0"
port: int = 8000
```

**Impact**: On a LAN, an attacker with ARP spoofing or network access can intercept all cluster traffic, steal JWT tokens, read repository code, and inject malicious job payloads.

**Recommendation**:
1. Add HTTPS support with auto-generated self-signed certificates for LAN use
2. Consider using mkcert for local certificate authority
3. Document the HTTPS setup process
4. Add a configuration flag to require HTTPS

---

## Finding 17: No Input Validation on Several Endpoints

**Files**: Multiple API route files
**Rating**: MEDIUM
**CVE Pattern**: CWE-20 (Improper Input Validation)

Several endpoints accept free-form `dict` input without schema validation:

- `backend/app/api/v1/workflows.py:20`: `data: dict` â€” no schema, accepts arbitrary JSON
- `backend/app/api/v1/agents.py:20`: `data: dict` â€” no schema
- `backend/app/api/v1/engineering.py:21`: `data: dict` â€” no schema
- `backend/app/api/v1/ai.py:21`: `data: dict` â€” no schema, used for chat input
- `backend/app/api/v1/studio/layout.py`: `data: dict` â€” no schema

**Evidence**:
```python
# backend/app/api/v1/workflows.py:20
async def create_workflow(data: dict, db: AsyncSession = Depends(get_db)):
    engine = WorkflowEngine(db)
    wf = await engine.create_workflow(
        name=data.get("name", "Untitled"),  # No validation
```

**Impact**: Missing schema validation means type errors, injection attempts, and malformed data may not be caught before reaching the database or service layer.

**Recommendation**:
1. Create Pydantic schemas for all request bodies
2. Use FastAPI's automatic validation by declaring request body types
3. Validate fields that are used for database queries or file system operations

---

## Summary Table

| # | Finding | File | Rating |
|---|---------|------|--------|
| 1 | JWT secret hardcoded | config.py:14 | CRITICAL |
| 2 | Default admin credentials | services/auth.py:49-52 | CRITICAL |
| 5 | No auth on API endpoints | api/v1/*.py | CRITICAL |
| 10 | Plugin upload RCE | api/v1/plugins.py:53-66 | CRITICAL |
| 3 | CORS misconfiguration | main.py:69-75 | HIGH |
| 4 | Path traversal in workers | executor/handlers/*.py | HIGH |
| 7 | No rate limiting | main.py | HIGH |
| 8 | WebSocket without auth | main.py:80-96 | HIGH |
| 16 | No HTTPS | config.py:10-11 | HIGH |
| 6 | Token in localStorage | stores/auth-store.ts | MEDIUM |
| 9 | Information disclosure | api/v1/workers.py:37 | MEDIUM |
| 11 | Worker no auth | api/v1/workers.py:22 | MEDIUM |
| 14 | Sensitive data in logs | audit/middleware.py:38 | MEDIUM |
| 15 | SQL injection risk | repository/search/service.py | MEDIUM |
| 17 | No input validation | workflows.py, agents.py, etc. | MEDIUM |
| 13 | Weak cipher | config.py:15 | LOW |
| 12 | No CSRF | â€” | LOW |

## Overall Security Assessment

The AICluster codebase has 4 CRITICAL, 5 HIGH, 6 MEDIUM, and 2 LOW findings. The most urgent issues are:

1. **No authentication on API endpoints** â€” every endpoint is publicly accessible
2. **JWT secret is hardcoded** â€” tokens can be forged trivially
3. **Default admin credentials** â€” the default admin account uses well-known credentials
4. **Plugin upload RCE** â€” arbitrary code execution via ZIP upload

These findings indicate that the application has no effective access control in its current state. The JWT authentication system is architecturally well-designed but is never actually applied to endpoints. This represents a significant disconnect between the security architecture and its usage.

**Recommended immediate actions**:
1. Apply `get_current_user` to all API endpoints
2. Generate a random JWT secret on first startup
3. Force password change on first login
4. Add authentication to plugin upload endpoint
5. Add rate limiting to login endpoint

**Medium-term actions**:
1. Add HTTPS support
2. Implement WebSocket authentication
3. Add worker API key authentication
4. Add input validation to all dict-based endpoints
5. Implement path validation in worker handlers

**Long-term investments**:
1. Implement RBAC
2. Add CSRF protection
3. Implement plugin sandboxing
4. Add security scanning to CI pipeline
5. Conduct regular penetration testing
