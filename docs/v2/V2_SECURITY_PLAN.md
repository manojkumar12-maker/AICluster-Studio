# v2.0 Security Plan

**AICluster v2.0 â€” Native Desktop Edition | Phase 11**
**Date:** 2026-07-05
**Status:** Analysis Only â€” No Implementation

---

## 1. v2.0 Attack Surface

### 1.1 New Attack Vectors Introduced by v2.0

| # | Vector | Component | Risk | Description |
|---|--------|-----------|------|-------------|
| V2-01 | Launcher IPC | Studio (Tauri commands) | Medium | React frontend can invoke any Tauri command; must validate inputs |
| V2-02 | Process management | Launcher (Rust sidecar) | Medium | Launcher starts EXEs with arguments; argument injection risk |
| V2-03 | Role config | `config/role.json` | Low | File write from wizard; JSON injection risk |
| V2-04 | System tray | Studio | Low | Tray menu actions; cosmetic only |
| V2-05 | Auto-start | Registry | Low | Writes to HKCU\Software\Microsoft\Windows\CurrentVersion\Run |
| V2-06 | Updates | `updates/` directory | Medium | Update file download; must verify signature |
| V2-07 | Firewall config | Installer | Low | netsh commands; run only during install |
| V2-08 | File associations | Registry | Low | `.aicluster` file handler registration |
| V2-09 | Deep links | Protocol handler | Medium | `aicluster://` URIs; URI parsing injection risk |
| V2-10 | Encrypted secrets | `config/secrets.enc` | Medium | AES-256-GCM encryption; key management |

### 1.2 Complete Attack Surface (v2.0)

```
NETWORK PORTS:
  :8000  (Master REST API)     â”€â”€ JWT required, rate limited
  :8000  (Master WebSocket)    â”€â”€ JWT required
  :8001  (Worker)              â”€â”€ Localhost only (health endpoint)
  :3000  (Web Dashboard)       â”€â”€ Localhost only

LOCAL IPC:
  Tauri Commands (React â†” Rust)  â”€â”€ WebView trust boundary
  std::process::Command (launch) â”€â”€ Argument injection risk

FILESYSTEM:
  config/role.json          â”€â”€ Low sensitivity
  config/secrets.enc        â”€â”€ HIGH SENSITIVITY (encrypted)
  data/aicluster.db         â”€â”€ HIGH SENSITIVITY (contains user data)
  data/secret.key           â”€â”€ HIGH SENSITIVITY (JWT signing key)
  logs/*.log                â”€â”€ Medium (may contain URLs, not passwords)
  plugins/*                 â”€â”€ HIGH (code execution)
  updates/*                 â”€â”€ Medium (code execution if unsigned)

REGISTRY:
  HKCU\...\Run\AICluster Studio  â”€â”€ Low
  HKCR\.aicluster                 â”€â”€ Low
  HKCR\aicluster://               â”€â”€ Low

EXTERNAL:
  LLM Provider APIs (Ollama, llama.cpp, OpenAI)  â”€â”€ Localhost only
  Update server (future)                          â”€â”€ HTTPS required
```

---

## 2. Risk Assessment

### 2.1 New v2.0 Risks

| ID | Finding | Severity | Component | Description |
|----|---------|----------|-----------|-------------|
| V2-01 | **Tauri command input validation** | High | Launcher | React frontend sends arbitrary args to `start_process`; must whitelist valid EXEs |
| V2-02 | **Update download without signature** | High | Updates | Downloaded update files must be cryptographically verified before execution |
| V2-03 | **Role config write from unprivileged context** | Medium | Wizard | Wizard runs as user; can write `role.json`; must validate JSON structure |
| V2-04 | **Deep link URI injection** | Medium | Protocol | `aicluster://` URIs could contain path traversal; must validate |
| V2-05 | **Encrypted secret key storage** | Medium | Config | `secrets.enc` key must be derived, not stored alongside ciphertext |
| V2-06 | **Plugin loading from user-writable dir** | Medium | Plugins | `plugins/` is user-writable; plugins execute as the app user |
| V2-07 | **Process argument injection** | Medium | Launcher | `CreateProcess` with user-influenced arguments must escape properly |
| V2-08 | **Log injection** | Low | Logs | Log file writes from user-influenced data; newline injection risk |

### 2.2 Existing v2.0.0 Risks (Carried Forward)

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| V-001 | Plugin upload arbitrary code execution | CRITICAL | NOT FIXED â€” must fix in v2.0 |
| V-002 | No HTTPS in default configuration | HIGH | NOT FIXED â€” v2.0 should default to HTTPS with self-signed cert |
| V-003 | Token in localStorage (web dashboard) | MEDIUM | Carried forward |
| V-004 | Information disclosure in error messages | MEDIUM | Carried forward |
| V-008 | No input size limits on API | MEDIUM | Carried forward |
| V-010 | Plugin sandbox incomplete | MEDIUM | Carried forward |

---

## 3. Security Hardening Recommendations

### 3.1 Critical â€” Fix Plugin Upload RCE

See SECURITY_HARDENING_REPORT.md Â§3.1 for detailed fix.

### 3.2 High â€” Tauri Command Input Validation

```rust
// studio/src-tauri/src/launcher/process.rs

const ALLOWED_EXECUTABLES: &[&str] = &[
    "AIClusterRuntime.exe --mode master",
    "AIClusterRuntime.exe --mode worker",
    "aicluster.exe",
];

pub async fn start_process(
    executable: String,
    args: Vec<String>,
) -> Result<u32, String> {
    // Validate executable name
    let exe_name = Path::new(&executable)
        .file_name()
        .ok_or("Invalid executable path")?
        .to_str()
        .ok_or("Non-UTF8 executable name")?;
    
    if !ALLOWED_EXECUTABLES.contains(&exe_name) {
        return Err(format!("Forbidden executable: {}", exe_name));
    }
    
    // Validate path traversal
    let resolved = std::fs::canonicalize(&executable)
        .map_err(|e| format!("Cannot resolve path: {}", e))?;
    
    // Must be within the runtime directory
    let runtime_dir = std::env::current_exe()?
        .parent()
        .ok_or("Cannot find app directory")?
        .join("runtime")
        .canonicalize()?;
    
    if !resolved.starts_with(&runtime_dir) {
        return Err("Executable must be in runtime/ directory".into());
    }
    
    // Validate arguments: no shell metacharacters
    for arg in &args {
        if arg.contains(&['|', '&', ';', '$', '>', '<', '`', '\n', '\r'][..]) {
            return Err("Invalid characters in argument".into());
        }
    }
    
    // Safe to launch
    let child = Command::new(&resolved)
        .args(&args)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .creation_flags(CREATE_NO_WINDOW)
        .spawn()
        .map_err(|e| format!("Failed to start process: {}", e))?;
    
    Ok(child.id())
}
```

### 3.3 High â€” Update Verification

```rust
// studio/src-tauri/src/launcher/updates.rs

pub struct UpdatePackage {
    pub version: String,
    pub installer_path: PathBuf,
    pub signature: Vec<u8>,
    pub public_key: Vec<u8>,
}

impl UpdatePackage {
    pub fn verify(&self) -> Result<(), String> {
        // Verify signature using embedded public key
        let installer_bytes = std::fs::read(&self.installer_path)
            .map_err(|e| format!("Cannot read installer: {}", e))?;
        
        use ring::signature::{UnparsedPublicKey, ED25519};
        
        let public_key = UnparsedPublicKey::new(&ED25519, &self.public_key);
        public_key.verify(&installer_bytes, &self.signature)
            .map_err(|_| "Signature verification failed".to_string())?;
        
        // Verify version is newer than current
        let current = env!("CARGO_PKG_VERSION");
        if self.version <= current {
            return Err(format!(
                "Update version {} is not newer than current {}",
                self.version, current
            ));
        }
        
        Ok(())
    }
}
```

### 3.4 Medium â€” Secure Secret Storage

```rust
// studio/src-tauri/src/launcher/secrets.rs

use aes_gcm::{
    Aes256Gcm, Key, Nonce,
    aead::{Aead, KeyInit, OsRng},
};
use windows::Win32::Security::Cryptography::*;

pub struct SecretsManager {
    key: [u8; 32],
}

impl SecretsManager {
    /// Initialize secrets manager.
    /// Derives encryption key from Windows DPAPI + machine-specific data.
    pub fn new() -> Result<Self, String> {
        // Use DPAPI to protect the encryption key
        let key_material = Self::derive_key_from_system()?;
        
        Ok(Self {
            key: key_material,
        })
    }
    
    fn derive_key_from_system() -> Result<[u8; 32], String> {
        // Combine multiple entropy sources
        let mut entropy = Vec::new();
        
        // 1. Machine SID
        entropy.extend_from_slice(
            &Self::get_machine_sid().map_err(|e| e.to_string())?.as_bytes()
        );
        
        // 2. Volume serial number
        entropy.extend_from_slice(
            &Self::get_volume_serial().map_err(|e| e.to_string())?.to_le_bytes()
        );
        
        // 3. Random salt
        let mut salt = [0u8; 16];
        OsRng.fill(&mut salt);
        entropy.extend_from_slice(&salt);
        
        // 4. DPAPI-encrypt the entropy (system-bound)
        let protected = unsafe {
            let mut data = DATA_BLOB {
                cbData: entropy.len() as u32,
                pbData: entropy.as_mut_ptr(),
            };
            let mut out = DATA_BLOB::default();
            CryptProtectData(
                &data,
                null(),
                None,
                None,
                None,
                CRYPTPROTECT_LOCAL_MACHINE,
                &mut out,
            )?;
            std::slice::from_raw_parts(out.pbData, out.cbData as usize)
        };
        
        // Hash to 32 bytes
        use sha2::{Sha256, Digest};
        let hash = Sha256::digest(protected);
        
        Ok(hash.into())
    }
    
    pub fn encrypt_file(&self, path: &Path, plaintext: &[u8]) -> Result<(), String> {
        let cipher = Aes256Gcm::new_from_slice(&self.key)
            .map_err(|e| format!("Cipher init failed: {}", e))?;
        
        let nonce = Aes256Gcm::generate_nonce(&mut OsRng);
        let ciphertext = cipher
            .encrypt(&nonce, plaintext)
            .map_err(|e| format!("Encryption failed: {}", e))?;
        
        // Format: [nonce (12 bytes)][ciphertext]
        let mut output = Vec::with_capacity(12 + ciphertext.len());
        output.extend_from_slice(&nonce);
        output.extend_from_slice(&ciphertext);
        
        std::fs::write(path, output)
            .map_err(|e| format!("Write failed: {}", e))
    }
    
    pub fn decrypt_file(&self, path: &Path) -> Result<Vec<u8>, String> {
        let data = std::fs::read(path)
            .map_err(|e| format!("Read failed: {}", e))?;
        
        if data.len() < 12 {
            return Err("Invalid encrypted file".into());
        }
        
        let (nonce_bytes, ciphertext) = data.split_at(12);
        let nonce = Nonce::from_slice(nonce_bytes);
        
        let cipher = Aes256Gcm::new_from_slice(&self.key)
            .map_err(|e| format!("Cipher init failed: {}", e))?;
        
        cipher
            .decrypt(nonce, ciphertext)
            .map_err(|_| "Decryption failed (tampered or wrong key)".into())
    }
}
```

### 3.5 Medium â€” Deep Link URI Validation

```rust
// studio/src-tauri/src/launcher/deeplink.rs

pub fn handle_deep_link(uri: &str) -> Result<DeepLinkAction, String> {
    // Parse the URI
    let parsed = url::Url::parse(uri)
        .map_err(|e| format!("Invalid URI: {}", e))?;
    
    // Must be aicluster:// scheme
    if parsed.scheme() != "aicluster" {
        return Err("Invalid scheme".into());
    }
    
    // Validate host (action)
    let action = parsed.host_str()
        .ok_or("Missing action")?;
    
    // Parse query parameters safely
    let params: std::collections::HashMap<_, _> = parsed.query_pairs().collect();
    
    match action {
        "dashboard" => Ok(DeepLinkAction::OpenDashboard),
        "chat" => Ok(DeepLinkAction::OpenChat),
        "workflows" => Ok(DeepLinkAction::OpenWorkflows),
        "settings" => Ok(DeepLinkAction::OpenSettings),
        "repository" => {
            let id = params.get("id")
                .ok_or("Missing repository id")?;
            // Validate id is UUID
            uuid::Uuid::parse_str(id)
                .map_err(|_| "Invalid repository id".into())?;
            Ok(DeepLinkAction::OpenRepository(id.to_string()))
        }
        _ => Err(format!("Unknown action: {}", action)),
    }
}
```

### 3.6 Medium â€” Process Watchdog Security

```rust
// Ensure watchdog can't be abused

pub struct Watchdog {
    restart_counts: HashMap<String, u32>,
    max_restarts: u32,           // 3 per service
    cooldown_period: Duration,   // 60 seconds after max restarts
}

impl Watchdog {
    pub fn should_restart(&mut self, service: &str) -> bool {
        let count = self.restart_counts.entry(service.to_string()).or_insert(0);
        
        if *count < self.max_restarts {
            *count += 1;
            true
        } else {
            // Enter cooldown
            false
        }
    }
    
    pub fn reset_count(&mut self, service: &str) {
        self.restart_counts.insert(service.to_string(), 0);
    }
}
```

---

## 4. Security Documentation

### 4.1 v2.0 Security Documents

| Document | Location | Purpose |
|----------|----------|---------|
| `SECURITY.md` | Root | Security policy (vulnerability disclosure) |
| `SECURITY_HARDENING.md` | `docs/Security/` | v1.4 hardening report |
| `V2_SECURITY_PLAN.md` | `docs/v2/` | This document |
| `THREAT_MODEL.md` | `docs/Security/` | Full threat model |
| `RELEASE_HARDENING.md` | `docs/Security/` | Build hardening checklist |

---

## 5. Security Testing

### 5.1 v2.0 Security Test Plan

```powershell
# Security verification script
$failures = @()

# 1. Plugin upload â€” attempt path traversal
Write-Host "Test: Plugin path traversal..."
$result = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/plugins/install" `
    -Method POST `
    -Form @{
        file = Get-Item -Path "test-plugins/malicious.zip"
    }
if ($result.StatusCode -eq 200) {
    $failures += "FAIL: Plugin upload accepted malicious ZIP"
}

# 2. Tauri command injection
Write-Host "Test: Tauri command injection..."
# Attempt to launch notepad.exe via launcher
$result = Invoke-TauriCommand -Command "start_process" -Args @{
    executable = "../../Windows/System32/notepad.exe"
}
if ($result -ne "Forbidden executable") {
    $failures += "FAIL: Launcher allowed forbidden executable"
}

# 3. Deep link injection
Write-Host "Test: Deep link injection..."
$result = Invoke-TauriCommand -Command "handle_deep_link" -Args @{
    uri = "aicluster://repository?id=../../../etc/passwd"
}
if ($result -ne "Invalid repository id") {
    $failures += "FAIL: Deep link allowed path traversal"
}

# 4. Role config injection
Write-Host "Test: Role config injection..."
$result = Invoke-TauriCommand -Command "set_role" -Args @{
    role = "'; DROP TABLE users; --"
}
if ($result -eq "ok") {
    $failures += "FAIL: Role config allowed injection"
}

if ($failures.Count -eq 0) {
    Write-Host "All security tests passed!" -ForegroundColor Green
} else {
    $failures | ForEach-Object { Write-Host $_ -ForegroundColor Red }
}
```

---

## 6. Success Criteria

- [ ] Plugin upload RCE fixed (CRITICAL)
- [ ] Tauri command input validation implemented (HIGH)
- [ ] Update signature verification implemented (HIGH)
- [ ] Deep link URI validation implemented (MEDIUM)
- [ ] Encrypted secret storage implemented (MEDIUM)
- [ ] Process whitelist enforced in launcher (MEDIUM)
- [ ] Log injection prevented (LOW)
- [ ] No plaintext secrets in configuration files
- [ ] All Tauri commands validate inputs
- [ ] All IPC boundaries documented
- [ ] Security test suite passes
- [ ] Existing v2.0.0 security fixes preserved
