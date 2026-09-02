"""
LLM 服务 - 统一多Provider调用
支持：Ollama(本地) / OpenAI / 自动降级
"""
import asyncio
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class LLMService:
    """统一的LLM调用服务"""

    def __init__(self):
        self._circuit_breaker: Dict[str, int] = {}  # provider -> fail_count
        self._max_failures = 3

    async def generate(
        self,
        prompt: str,
        provider: str = "auto",
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """生成文本 - 自动选择provider"""
        if provider == "auto":
            provider = self._select_provider()

        if provider == "ollama":
            return await self._call_ollama(prompt, model, max_tokens, temperature, system_prompt)
        elif provider == "openai":
            return await self._call_openai(prompt, model, max_tokens, temperature, system_prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _select_provider(self) -> str:
        """选择可用的provider（优先本地）"""
        for provider in ["ollama", "openai"]:
            if self._circuit_breaker.get(provider, 0) < self._max_failures:
                return provider
        return "ollama"  # fallback

    async def _call_ollama(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
    ) -> str:
        """调用 Ollama 本地模型"""
        from .config import settings
        base_url = settings.OLLAMA_BASE_URL
        model = model or settings.OLLAMA_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                        },
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                self._circuit_breaker["ollama"] = 0
                return data.get("message", {}).get("content", "")
        except Exception as e:
            self._circuit_breaker["ollama"] = self._circuit_breaker.get("ollama", 0) + 1
            logger.error(f"Ollama failed: {e}")
            raise

    async def _call_openai(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
    ) -> str:
        """调用 OpenAI API"""
        from .config import settings
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        model = model or settings.OPENAI_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                self._circuit_breaker["openai"] = 0
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            self._circuit_breaker["openai"] = self._circuit_breaker.get("openai", 0) + 1
            logger.error(f"OpenAI failed: {e}")
            raise

    async def health_check(self) -> Dict[str, bool]:
        """检查各provider可用性"""
        results = {}

        # Ollama
        try:
            from .config import settings
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                results["ollama"] = resp.status_code == 200
        except Exception:
            results["ollama"] = False

        # OpenAI
        from .config import settings
        results["openai"] = bool(settings.OPENAI_API_KEY)

        return results
