import httpx
import json
import logging
from typing import AsyncIterator
from datetime import datetime

from .interface import ModelProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(ModelProvider):
    def __init__(self, base_url: str = "http://localhost:8000/v1", model: str = "default",
                 api_key: str = "", max_context: int = 32768):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.max_context = max_context
        self._loaded = False

    async def load(self) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                if resp.status_code == 200:
                    models = resp.json().get("data", [])
                    for m in models:
                        if self.model in m.get("id", ""):
                            self._loaded = True
                            logger.info(f"OpenAI-compatible model found: {self.model}")
                            return True
                    logger.warning(f"Model {self.model} not found in provider")
                    return False
                return False
        except Exception as e:
            logger.error(f"OpenAI-compatible connection failed: {e}")
            return False

    async def unload(self) -> bool:
        self._loaded = False
        return True

    async def generate(self, prompt: str, system_prompt: str | None = None,
                       max_tokens: int = 4096, temperature: float = 0.7) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            if resp.status_code == 200:
                choices = resp.json().get("choices", [])
                return choices[0].get("message", {}).get("content", "") if choices else ""
            logger.error(f"OpenAI generate failed: {resp.status_code}")
            return ""

    async def stream(self, prompt: str, system_prompt: str | None = None,
                     max_tokens: int = 4096, temperature: float = 0.7) -> AsyncIterator[str]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model, "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature, "stream": True,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", f"{self.base_url}/chat/completions", json=payload, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def token_count(self, text: str) -> int:
        try:
            payload = {"model": self.model, "input": text}
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self.base_url}/tokenize", json=payload, headers=headers)
                if resp.status_code == 200:
                    return len(resp.json().get("tokens", []))
        except Exception:
            pass
        try:
            return len(text) // 4 + 1
        except Exception:
            return len(text)

    async def health(self) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                return resp.status_code == 200
        except Exception:
            return False

    def configuration(self) -> dict:
        return {"base_url": self.base_url, "model": self.model, "type": "openai-compatible"}

    def capabilities(self) -> dict:
        return {"streaming": True, "tool_calling": True, "max_context": self.max_context, "provider": "openai-compatible"}
