import httpx
import json
import logging
from typing import AsyncIterator

from .interface import ModelProvider

logger = logging.getLogger(__name__)


class LlamaCppProvider(ModelProvider):
    def __init__(self, base_url: str = "http://localhost:8080", model: str = "default"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._loaded = False

    async def load(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/health")
                if resp.status_code == 200:
                    self._loaded = True
                    logger.info("llama.cpp server is healthy")
                    return True
                return False
        except Exception as e:
            logger.error(f"llama.cpp connection failed: {e}")
            return False

    async def unload(self) -> bool:
        self._loaded = False
        return True

    async def generate(self, prompt: str, system_prompt: str | None = None,
                       max_tokens: int = 4096, temperature: float = 0.7) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "prompt": full_prompt, "n_predict": max_tokens,
            "temperature": temperature, "stream": False,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/completion", json=payload)
            if resp.status_code == 200:
                return resp.json().get("content", "")
            logger.error(f"llama.cpp generate failed: {resp.status_code}")
            return ""

    async def stream(self, prompt: str, system_prompt: str | None = None,
                     max_tokens: int = 4096, temperature: float = 0.7) -> AsyncIterator[str]:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "prompt": full_prompt, "n_predict": max_tokens,
            "temperature": temperature, "stream": True,
        }
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", f"{self.base_url}/completion", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            content = data.get("content", "")
                            if content:
                                yield content
                            if data.get("stop"):
                                break
                        except json.JSONDecodeError:
                            continue

    async def token_count(self, text: str) -> int:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self.base_url}/tokenize", json={"content": text})
                if resp.status_code == 200:
                    return len(resp.json().get("tokens", []))
        except Exception:
            pass
        return len(text) // 4 + 1

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{self.base_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    def configuration(self) -> dict:
        return {"base_url": self.base_url, "model": self.model, "type": "llama.cpp"}

    def capabilities(self) -> dict:
        return {"streaming": True, "tool_calling": False, "max_context": 8192, "provider": "llama.cpp"}
