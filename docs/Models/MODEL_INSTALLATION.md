# AICluster — Model Installation & Configuration Guide

**Version:** 1.2.1  
**Last Updated:** 2026-07-03  
**Applies to:** AICluster Master v1.2.x, Worker v1.2.x

---

## Table of Contents

1. [Overview](#1-overview)
2. [Ollama Setup](#2-ollama-setup)
3. [Supported Model Families](#3-supported-model-families)
4. [Model Installation Guides](#4-model-installation-guides)
5. [How Workers Detect Models](#5-how-workers-detect-models)
6. [How the Master Discovers Providers](#6-how-the-master-discovers-providers)
7. [Model Sharing Across the Cluster](#7-model-sharing-across-the-cluster)
8. [Model Paths and Storage](#8-model-paths-and-storage)
9. [Resource Limits](#9-resource-limits)
10. [Recommended Models by Hardware](#10-recommended-models-by-hardware)
11. [Worker Model Strategy](#11-worker-model-strategy)
12. [Configuration Reference](#12-configuration-reference)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Overview

AICluster supports three LLM provider backends for AI inference:

| Provider | Type | Use Case |
|----------|------|----------|
| **Ollama** | Local HTTP server | Primary provider. Easy install, broad model support, GPU acceleration via CUDA. |
| **llama.cpp** | Local HTTP server | Lightweight, CPU-first. Best for CPU-only machines. |
| **OpenAI-Compatible** | HTTP endpoint | Works with vLLM, LM Studio, NVIDIA NIM, or any OpenAI API proxy. |

All providers are accessed over HTTP on localhost or the LAN. There is no direct GPU access from Python — inference runs in a separate server process (Ollama, llama.cpp server, etc.) and AICluster communicates via REST.

The architecture is intentionally provider-agnostic. The `ModelProvider` abstract base class in `backend/app/ai/providers/interface.py` defines seven methods: `load`, `unload`, `generate`, `stream`, `token_count`, `health`, and `configuration`/`capabilities`. Each provider implements these methods against its respective API.

Three concrete implementations exist:

- **OllamaProvider** (`backend/app/ai/providers/ollama.py`): Talks to Ollama's `/api/generate` and `/api/tags` endpoints.
- **LlamaCppProvider** (`backend/app/ai/providers/llamacpp.py`): Talks to llama.cpp server's `/completion` and `/health` endpoints.
- **OpenAICompatibleProvider** (`backend/app/ai/providers/openai_compat.py`): Talks to any OpenAI-compatible `/chat/completions` and `/models` endpoints.

All three are registered in the `ModelRegistry` at startup (see `backend/app/api/v1/ai.py:239-242`):

```python
ModelRegistry.register_provider("ollama", OllamaProvider)
ModelRegistry.register_provider("llama.cpp", LlamaCppProvider)
ModelRegistry.register_provider("openai-compatible", OpenAICompatibleProvider)
```

---

## 2. Ollama Setup

Ollama is the recommended provider for AICluster. It provides the broadest model support, automatic GPU detection, and a simple API.

### 2.1 Install Ollama

**Windows:**
1. Download the installer from [https://ollama.com/download](https://ollama.com/download)
2. Run the installer (adds Ollama to PATH, installs as a Windows service)
3. Verify installation: `ollama --version`
4. The Ollama service runs at `http://localhost:11434` by default

**Linux (Master PC only, if applicable):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2.2 Configure Ollama for AICluster

Ollama works out of the box. No special configuration is needed. However, for production clusters consider:

**Set the model directory (optional):**
```powershell
# Windows: set environment variable before starting Ollama
setx OLLAMA_MODELS "D:\AICluster\models"
```
Then restart the Ollama service. This is important for shared model directories (see Section 7).

**Configure GPU access:**
- Ollama auto-detects NVIDIA GPUs via CUDA
- For AMD GPUs on Windows, use the DirectML build: `ollama serve --dml`
- For CPU-only, no configuration needed

**Configure concurrent loads (advanced):**
```powershell
setx OLLAMA_NUM_PARALLEL 4
setx OLLAMA_MAX_LOADED_MODELS 2
```

### 2.3 Test Ollama Connection

```powershell
curl http://localhost:11434/api/tags
```

Expected response: `{"models": [...]}` (may be empty if no models pulled yet).

---

## 3. Supported Model Families

AICluster has built-in task routing for these model families:

| Family | Default Model | Task | Provider |
|--------|---------------|------|----------|
| **DeepSeek** | `deepseek-coder` | Architecture review, code generation | OpenAI-compatible (or Ollama) |
| **Qwen** | `qwen3-coder` | Code generation, default task | Ollama |
| **Gemma** | `gemma3` | Documentation writing | Ollama |
| **Phi** | `phi-3` | Summarization, light tasks | llama.cpp |
| **Llama** | `llama3.1` | General purpose | Ollama |

These are configured in `TASK_ROUTING` in `backend/app/ai/routing/router.py`:

```python
TASK_ROUTING = {
    "code_generation":       {"provider": "ollama", "model": "qwen3-coder", "priority": 1},
    "architecture_review":   {"provider": "openai-compatible", "model": "deepseek-coder", "priority": 2},
    "documentation":         {"provider": "ollama", "model": "gemma3", "priority": 3},
    "summarization":         {"provider": "llama.cpp", "model": "phi-3", "priority": 4},
    "default":               {"provider": "ollama", "model": "qwen3-coder", "priority": 5},
}
```

---

## 4. Model Installation Guides

### 4.1 Pulling Models via Ollama

```powershell
# Qwen Coder (default, ~4.1 GB for 7B Q4)
ollama pull qwen3-coder

# DeepSeek Coder (~3.5 GB for 6.7B Q4)
ollama pull deepseek-coder

# Gemma 3 (~3.3 GB for 7B Q4)
ollama pull gemma3

# Llama 3.1 (~4.7 GB for 8B Q4)
ollama pull llama3.1

# Phi-3 Mini (~2.2 GB for 3.8B Q4)
ollama pull phi-3

# Smaller models for low-RAM machines
ollama pull qwen3-coder:1.5b   # ~1.1 GB
ollama pull phi-3:mini         # ~2.2 GB
ollama pull gemma3:2b          # ~1.6 GB
```

### 4.2 Pulling Models for llama.cpp

```powershell
# Download GGUF files from Hugging Face
# Example: Phi-3 Mini (CPU-friendly)
curl -L -o models/phi-3-mini.Q4_K_M.gguf ^
  https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct.Q4_K_M.gguf

# Start llama.cpp server
llama-server.exe -m models/phi-3-mini.Q4_K_M.gguf --port 8080 --host 0.0.0.0
```

### 4.3 Configuring OpenAI-Compatible Providers

For LM Studio, vLLM, or NVIDIA NIM:

```python
# Via AICluster API
POST /api/v1/ai/models/register
{
    "name": "deepseek-coder",
    "provider": "openai-compatible",
    "context_window": 32768,
    "config": {
        "base_url": "http://192.168.1.100:8000/v1",
        "api_key": "optional-key",
        "model": "deepseek-coder"
    }
}
```

---

## 5. How Workers Detect Models

Workers do NOT directly detect or load AI models. The worker service (`worker/app/`) is a general-purpose compute agent. It executes jobs dispatched by the master — file scanning, hashing, counting, echo, sleep — not LLM inference.

Model inference runs exclusively on the **master PC** (or any machine running the AI provider server). When the master's AI runtime needs to generate text, it:

1. Selects a provider via `ModelRouter.select_provider()` in `backend/app/ai/routing/router.py`
2. Looks up a loaded provider instance in `ModelRegistry._instances`
3. If no instance is loaded, instantiates a provider class (e.g., `OllamaProvider(model="qwen3-coder")`)
4. Calls `provider.generate()` or `provider.stream()` over HTTP to the local Ollama/llama.cpp/OpenAI server

The provider's `load()` method checks if the model is available:

```python
# OllamaProvider.load() - backend/app/ai/providers/ollama.py:17
async def load(self) -> bool:
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(f"{self.base_url}/api/tags")
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            for m in models:
                if self.model in m.get("name", ""):
                    self._loaded = True
                    return True
            return False
```

If the model is not found, the master logs a warning and falls back to the next available provider.

---

## 6. How the Master Discovers Providers

Provider discovery happens through the `ModelRegistry` class (`backend/app/ai/registry/service.py:9`). The registry is a global singleton with class-level dictionaries:

```python
class ModelRegistry:
    _providers: dict[str, type[ModelProvider]] = {}    # registered provider classes
    _instances: dict[str, ModelProvider] = {}           # loaded provider instances
```

**Registration flow:**

1. On first API call to `/api/v1/ai/chat/llm` or `/api/v1/ai/runtime/status`, the backend calls `ModelRegistry.register_provider()` for all three providers (ollama, llama.cpp, openai-compatible) — see `backend/app/api/v1/ai.py:239-242`.

2. When a model is requested, `ModelRouter.select_provider()` in `backend/app/ai/routing/router.py` tries:
   - First: the preferred provider for the task type (from `TASK_ROUTING`)
   - Second: any loaded instance (fallback chain)
   - Third: a clear error message

3. The `/api/v1/ai/runtime/status` endpoint exposes all registered providers and loaded instances:

```json
GET /api/v1/ai/runtime/status
{
    "registered_providers": ["ollama", "llama.cpp", "openai-compatible"],
    "loaded_instances": ["ollama"],
    "profiles": ["fast", "balanced", "maximum_quality", "offline_low_ram", "custom"]
}
```

4. Health checks are provider-specific:
   - Ollama: `GET /api/tags` must return 200
   - llama.cpp: `GET /health` must return 200
   - OpenAI-compatible: `GET /models` must return 200

Discovery is **not automatic across the network**. The master only checks localhost by default. For remote providers, users must configure the provider's `base_url` to point at the remote machine.

---

## 7. Model Sharing Across the Cluster

Since workers do not run models directly, "model sharing" in AICluster means making model files available to the master PC's provider (Ollama/llama.cpp).

### 7.1 Single Master Model Store (Default)

All models are stored on the master PC. Workers never need model files. This is the simplest and most common configuration:

```
Master PC: C:\Users\<user>\.ollama\models\  (or custom OLLAMA_MODELS path)
Worker PCs: No model storage needed
```

### 7.2 Network Share for Multiple Masters (Enterprise)

If you run multiple masters or want to avoid re-downloading:

```
\\nas\models\ollama\    # Network share
  ├── blobs/            # Ollama model blobs
  └── manifests/        # Ollama manifests

# On each master PC:
setx OLLAMA_MODELS "\\nas\models\ollama"
```

Then restart Ollama. All masters share the same model files. Note: Ollama must have read/write access to the network share.

### 7.3 Distributed Provider Strategy (Advanced)

For very large models that exceed the master's RAM, you can run inference servers on worker PCs and configure AICluster's OpenAI-compatible provider to point at them:

```
Master PC (light inference only)
    │
    ├── Worker PC 1: llama-server.exe --host 0.0.0.0 --port 8080 -m deepseek-coder-33b.Q4.gguf
    │   └── Master connects via OpenAI-compatible provider at http://192.168.1.101:8080/v1
    │
    └── Worker PC 2: ollama serve (runs gemma3:7b)
        └── Master connects via Ollama provider at http://192.168.1.102:11434
```

This is configured through the `OpenAICompatibleProvider` by setting `base_url` to the remote worker's address.

---

## 8. Model Paths and Storage

### 8.1 Default Ollama Model Paths

| OS | Default Path | Custom Env Var |
|----|-------------|----------------|
| Windows | `C:\Users\<user>\.ollama\models` | `OLLAMA_MODELS` |
| Linux | `~/.ollama/models` | `OLLAMA_MODELS` |
| macOS | `~/.ollama/models` | `OLLAMA_MODELS` |

The `models/` directory at the AICluster project root (`AICluster/models/.gitkeep`) is a placeholder for users to symlink or mount model storage. It is not used by Ollama directly.

### 8.2 Model Storage Sizes

| Model | Quantization | Size | RAM Needed |
|-------|-------------|------|------------|
| qwen3-coder:1.5b | Q4 | ~1.1 GB | 2 GB |
| phi-3:mini | Q4 | ~2.2 GB | 4 GB |
| gemma3:2b | Q4 | ~1.6 GB | 2 GB |
| qwen3-coder:7b | Q4 | ~4.1 GB | 6 GB |
| deepseek-coder:6.7b | Q4 | ~3.5 GB | 6 GB |
| llama3.1:8b | Q4 | ~4.7 GB | 8 GB |
| gemma3:7b | Q4 | ~3.3 GB | 6 GB |
| qwen3-coder:14b | Q4 | ~8.2 GB | 12 GB |
| deepseek-coder:33b | Q4 | ~19 GB | 24 GB |

### 8.3 AICluster's models/ Directory

The `AICluster/models/` directory is reserved for:
- Symlinks to network model stores
- GGUF files for llama.cpp (if used)
- Custom model scripts or configuration

The build system and installer ignore this directory. It is purely for user convenience.

---

## 9. Resource Limits

### 9.1 Worker Resource Limits

Workers enforce strict resource limits to prevent impact on office users:

```yaml
# config/default.yaml
workers:
  default_cpu_limit: 25         # 25% CPU maximum
  default_ram_limit_gb: 8       # 8 GB RAM maximum
```

These are enforced by `worker/app/services/monitor.py` using `psutil` for system monitoring. The worker runs at `BELOW_NORMAL` process priority.

Resource limits are **not applied to AI model servers** (Ollama, llama.cpp). Model servers run as separate processes and are not managed by AICluster's worker resource governor. If you run a model server on a worker PC, its resource usage is independent of the AICluster worker's limits.

### 9.2 Master Resource Limits for AI

The master PC running model inference should have:

| Model Size | Recommended RAM | Recommended CPU | GPU Benefit |
|-----------|----------------|----------------|-------------|
| 1-3B params | 8 GB | Any 4+ cores | Minimal |
| 7-8B params | 16 GB | 8+ cores | Significant (3-5x speedup) |
| 13-14B params | 32 GB | 8+ cores | Critical (runs on CPU only) |
| 30-33B params | 64 GB | 16+ cores | Required for interactive use |

### 9.3 Configuring Ollama Resource Limits

```powershell
# Limit Ollama CPU threads
setx OLLAMA_NUM_THREADS 8

# Limit Ollama GPU layers (if using GPU)
# In Ollama's service config or via model modfile
```

---

## 10. Recommended Models by Hardware

### 10.1 8 GB RAM Systems

These will run one small model at a time. Use quantized 1-3B models.

| Model | Quality | RAM Free | Recommended For |
|-------|---------|----------|-----------------|
| qwen3-coder:1.5b | Low | ~6 GB | Code generation, chat |
| phi-3:mini | Medium | ~5 GB | Summarization, light tasks |
| gemma3:2b | Low | ~6 GB | Documentation |

Strategy: Run Ollama with `OLLAMA_MAX_LOADED_MODELS=1`. Use only one provider.

### 10.2 16 GB RAM Systems

The sweet spot for office desktops. Can run 7B models comfortably.

| Model | Quality | RAM Free | Recommended For |
|-------|---------|----------|-----------------|
| qwen3-coder:7b | High | ~10 GB | Code generation (default) |
| deepseek-coder:6.7b | High | ~11 GB | Architecture review |
| gemma3:7b | High | ~11 GB | Documentation |
| llama3.1:8b | High | ~10 GB | General purpose |

Strategy: Load 1-2 models. Keep Ollama running with 7B as default.

### 10.3 32 GB RAM Systems

Can run 7B models with large context or 14B models.

| Model | Quality | RAM Free | Recommended For |
|-------|---------|----------|-----------------|
| qwen3-coder:14b | Very High | ~20 GB | Complex code generation |
| deepseek-coder:33b (Q4) | Very High | ~8 GB | Architecture (tight) |
| Any 7B model | High | ~24 GB | All tasks with large context |
| Multiple 7B models | High | ~16 GB | Full task routing |

Strategy: Enable full task routing. Load all three providers. Use `OLLAMA_MAX_LOADED_MODELS=3`.

### 10.4 64 GB RAM Systems

Enterprise-grade inference. Can run 33B models or multiple 7-14B models.

| Model | Quality | RAM Free | Recommended For |
|-------|---------|----------|-----------------|
| deepseek-coder:33b | Excellent | ~40 GB | Top-tier architecture review |
| qwen3-coder:14b | Very High | ~48 GB | Primary code generation |
| Multiple 7B models | High | ~40 GB | All task routing |
| llama3.1:70b (Q4) | Excellent | ~0+ GB | Requires GPU |

Strategy: Full task routing, maximum quality profile, large context windows.

### 10.5 CPU-Only Systems

All models run on CPU. Expect 5-20 tokens/second for 7B models depending on CPU.

| CPU | Model Speed (7B Q4) | Recommended Model |
|-----|-------------------|-------------------|
| Intel Core i5 (6 cores) | ~5 tok/s | qwen3-coder:1.5b or phi-3:mini |
| Intel Core i7 (8 cores) | ~10 tok/s | qwen3-coder:7b |
| Intel Core i9 / Ultra 9 (16+ cores) | ~15 tok/s | Any 7B model |
| AMD Ryzen 7 (8 cores) | ~12 tok/s | Any 7B model |
| AMD Ryzen 9 (16 cores) | ~18 tok/s | Any 7-14B model |

For CPU-only, llama.cpp with Q4_K_M quantization often performs better than Ollama. Use the LlamaCppProvider.

### 10.6 GPU Systems (NVIDIA RTX)

GPU acceleration dramatically improves inference speed.

| GPU | VRAM | Max Model Size | Speed (7B Q4) |
|-----|------|---------------|---------------|
| RTX 3050 | 6 GB | 3B Q4 | ~30 tok/s |
| RTX 3060 | 12 GB | 7B Q4 | ~50 tok/s |
| RTX 4060 | 8 GB | 7B Q4 | ~55 tok/s |
| RTX 4070 | 12 GB | 13B Q4 | ~65 tok/s |
| RTX 4080 | 16 GB | 13B Q4 | ~80 tok/s |
| RTX 4090 | 24 GB | 33B Q4 | ~100 tok/s |

To enable GPU with Ollama:
```powershell
# Ollama auto-detects CUDA. Verify:
ollama run qwen3-coder
# If GPU is working, you'll see "llm_load_tensors: offloading 22 layers to GPU"
```

To enable GPU with llama.cpp:
```powershell
llama-server.exe -m model.gguf -ngl 999  # Offload all layers to GPU
```

---

## 11. Worker Model Strategy

AICluster does **not** run LLM inference on workers. The architecture is:

```
Master PC ── runs Ollama/llama.cpp server ── runs AI inference
Worker PC ── runs general-purpose job handlers (echo, sleep, dir_scan, hash_file, count_files)
```

However, there are three strategies for deploying model inference across the cluster:

### 11.1 Strategy A: Every Worker Has Its Own Model (Distributed Inference)

Each worker PC also runs an Ollama or llama.cpp server. The master's `ModelRouter` is configured to use remote OpenAI-compatible endpoints pointing at worker machines.

**Pros:**
- Scales inference capacity with each added worker
- No single point of inference failure
- Workers with GPUs contribute their GPU to the cluster

**Cons:**
- Model files stored on every worker (storage waste if many workers)
- Network latency for every inference call
- Worker PC users may notice inference resource usage

**Configuration:**
```python
# In TASK_ROUTING, point at remote workers
TASK_ROUTING["code_generation"] = {
    "provider": "openai-compatible",
    "model": "qwen3-coder",
    "base_url": "http://192.168.1.101:11434/v1"  # Worker 1's Ollama
}
```

**Best for:** Homogeneous clusters with GPUs on every machine.

### 11.2 Strategy B: Master-Only Model (Centralized Inference)

Only the master PC runs models. Workers are pure compute agents.

**Pros:**
- Simple to manage — one machine with models
- Workers have zero inference overhead
- Model files stored once
- Predictable resource usage

**Cons:**
- Single point of inference failure
- Master PC must have sufficient RAM/GPU for all models
- Inference does not scale with cluster size

**Configuration:**
```yaml
# AICluster default. No special configuration needed.
# Master runs Ollama at localhost:11434.
# Workers only do file operations.
```

**Best for:** Most deployments. Simple, reliable, predictable.

### 11.3 Strategy C: Hybrid (Master + GPU Workers)

The master runs small models (1-3B) for quick tasks. GPU-equipped workers run large models (7B+) via remote inference.

**Pros:**
- Best of both worlds — fast local inference for simple tasks, powerful remote inference for complex tasks
- GPU workers contribute meaningfully
- Master stays responsive under load

**Cons:**
- Two inference paths to maintain
- Requires careful task routing
- Network dependency for complex tasks

**Configuration:**
```python
# Master uses Ollama for fast tasks
TASK_ROUTING["summarization"] = {
    "provider": "ollama",
    "model": "phi-3",
    "base_url": "http://localhost:11434"
}

# GPU Worker handles complex tasks
TASK_ROUTING["code_generation"] = {
    "provider": "openai-compatible",
    "model": "deepseek-coder",
    "base_url": "http://192.168.1.101:8080/v1"
}
```

**Best for:** Mixed hardware clusters. Workers with GPUs run big models; CPU-only workers are pure compute.

### 11.4 Recommendation

| Cluster Size | Worker Hardware | Strategy |
|-------------|----------------|----------|
| 2-5 machines | CPU-only | **B (Master-only)** — Master runs Ollama with 7B model |
| 2-5 machines | Mixed (1 GPU) | **C (Hybrid)** — GPU worker runs 13B+ model, master runs 7B |
| 5-20 machines | CPU-only | **B (Master-only)** — Use a dedicated master with 32 GB+ RAM |
| 5-20 machines | All have GPUs | **A (Distributed)** — Each worker contributes its GPU |
| 20+ machines | Mixed | **C (Hybrid)** — Combine GPU workers and master inference |

---

## 12. Configuration Reference

### 12.1 Provider Configuration (Backend)

Configuration is stored in `AIModel` database records and passed via the AI API.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | str | — | Model name (e.g., "qwen3-coder") |
| `provider` | str | — | Provider type: "ollama", "llama.cpp", "openai-compatible" |
| `model_type` | str | "chat" | Model type for routing |
| `context_window` | int | 4096 | Maximum context window |
| `capabilities` | dict | {} | Streaming, tool calling, etc. |
| `config.base_url` | str | Varies | Provider HTTP endpoint |
| `config.api_key` | str | "" | API key for OpenAI-compatible providers |

### 12.2 Profile Configuration

Defined in `backend/app/ai/routing/router.py:17`:

| Profile | max_tokens | temperature | Use Case |
|---------|-----------|-------------|----------|
| `fast` | 1024 | 0.3 | Quick responses, low latency |
| `balanced` | 4096 | 0.5 | Default, general purpose |
| `maximum_quality` | 8192 | 0.7 | Complex reasoning, long outputs |
| `offline_low_ram` | 512 | 0.3 | Minimized memory usage |
| `custom` | 4096 | 0.5 | User-configurable |

### 12.3 Task Routing Configuration

Defined in `backend/app/ai/routing/router.py:9`:

| Task Type | Provider | Model | Priority |
|-----------|----------|-------|----------|
| `code_generation` | ollama | qwen3-coder | 1 |
| `architecture_review` | openai-compatible | deepseek-coder | 2 |
| `documentation` | ollama | gemma3 | 3 |
| `summarization` | llama.cpp | phi-3 | 4 |
| `default` | ollama | qwen3-coder | 5 |

---

## 13. Troubleshooting

### 13.1 "Model not found" Error

**Symptom:** `OllamaProvider.load()` returns False and the provider skips to fallback.

**Causes:**
- Ollama is not running: `ollama serve`
- Model not pulled: `ollama pull qwen3-coder`
- Wrong base_url: check `http://localhost:11434/api/tags`
- Network firewall blocking port 11434

**Fix:**
```powershell
ollama list              # Verify model is installed
ollama pull qwen3-coder  # Pull if missing
curl http://localhost:11434/api/tags  # Verify API is responding
```

### 13.2 Out of Memory

**Symptom:** Ollama crashes or inference fails with "Killed" or "Error: exit status 0xc0000005".

**Causes:**
- Model quant too large for available RAM
- Multiple models loaded simultaneously
- System has insufficient swap space

**Fix:**
- Use a smaller quantization (Q4 instead of Q8)
- Reduce `OLLAMA_MAX_LOADED_MODELS`
- Increase system swap
- Use the `offline_low_ram` profile
- Switch to a smaller model (e.g., 1.5B instead of 7B)

### 13.3 Provider Connection Refused

**Symptom:** `httpx.ConnectError` in master logs.

**Causes:**
- Provider server (Ollama/llama.cpp) not started
- Wrong port configured
- Firewall blocking connections

**Fix:**
```powershell
# Check if Ollama is running
Get-Process ollama*
netstat -an | findstr :11434

# Start Ollama if not running
ollama serve

# Check llama.cpp
Get-Process llama-server*
netstat -an | findstr :8080
```

### 13.4 Slow Inference on Workers

If using Strategy A or C (distributed inference on workers):

**Causes:**
- Worker CPU throttling (25% limit) also throttles the Ollama process
- Network latency between master and worker
- Worker PC is actively being used

**Fix:**
- Install Ollama on the worker as a system service (not managed by AICluster worker)
- Use a dedicated inference worker without AICluster worker limits
- Run inference on the master for latency-sensitive tasks
- Ensure worker and master are on the same LAN switch, not WiFi
