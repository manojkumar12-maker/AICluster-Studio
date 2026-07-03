import httpx
import json
import logging
from typing import AsyncIterator

from .interface import ModelProvider

logger = logging.getLogger(__name__)


class OllamaProvider(ModelProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3-coder"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._loaded = False

    async def load(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    for m in models:
                        if self.model in m.get("name", ""):
                            self._loaded = True
                            logger.info(f"Ollama model found: {self.model}")
                            return True
                    logger.warning(f"Model {self.model} not found in Ollama")
                    return False
                return False
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False

    async def unload(self) -> bool:
        self._loaded = False
        return True

    async def generate(self, prompt: str, system_prompt: str | None = None,
                       max_tokens: int = 4096, temperature: float = 0.7) -> str:
        payload = {
            "model": self.model, "prompt": prompt, "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        if system_prompt:
            payload["system"] = system_prompt
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            logger.error(f"Ollama generate failed: {resp.status_code}")
            return ""

    async def stream(self, prompt: str, system_prompt: str | None = None,
                     max_tokens: int = 4096, temperature: float = 0.7) -> AsyncIterator[str]:
        payload = {
            "model": self.model, "prompt": prompt, "stream": True,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        if system_prompt:
            payload["system"] = system_prompt
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue

    async def token_count(self, text: str) -> int:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self.base_url}/api/embed", json={"model": self.model, "input": text})
                if resp.status_code == 200:
                    data = resp.json()
                    return len(data.get("embeddings", [[]])[0]) if data.get("embeddings") else len(text) // 4
        except Exception:
            pass
        return len(text) // 4 + 1

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def configuration(self) -> dict:
        return {"base_url": self.base_url, "model": self.model, "type": "ollama"}

    def capabilities(self) -> dict:
        return {"streaming": True, "tool_calling": False, "max_context": 32768, "provider": "ollama"}
