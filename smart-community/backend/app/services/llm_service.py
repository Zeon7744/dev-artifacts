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
        from ..core.config import settings
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
        from ..core.config import settings
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

    async def generate_stream(
        self,
        prompt: str,
        provider: str = "auto",
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ):
        """流式生成文本（async generator，逐 token yield）。

        - Ollama: /api/chat stream=true，逐行解析 message.content
        - OpenAI: /v1/chat/completions stream=true，SSE data: 行解析 delta.content
        - 全部失败: yield 降级提示文本（保持流式接口语义一致）
        """
        if provider == "auto":
            provider = self._select_provider()

        try:
            if provider == "ollama":
                async for chunk in self._stream_ollama(prompt, model, max_tokens, temperature, system_prompt):
                    yield chunk
            elif provider == "openai":
                async for chunk in self._stream_openai(prompt, model, max_tokens, temperature, system_prompt):
                    yield chunk
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except Exception as e:
            logger.warning(f"LLM stream failed ({provider}): {e}")
            self._circuit_breaker[provider] = self._circuit_breaker.get(provider, 0) + 1
            fallback = (
                f"[本地LLM未就绪] 已收到你的消息：{prompt[:200]}。"
                "请启动 Ollama 或配置 OPENAI_API_KEY 后获得 AI 流式回复。"
            )
            # 降级文本也按小块吐出，前端打字机体验一致
            for i in range(0, len(fallback), 12):
                yield fallback[i : i + 12]
                await asyncio.sleep(0.02)

    async def _stream_ollama(self, prompt, model, max_tokens, temperature, system_prompt):
        import json

        from ..core.config import settings

        base_url = settings.OLLAMA_BASE_URL
        model = model or settings.OLLAMA_MODEL
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {"num_predict": max_tokens, "temperature": temperature},
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = data.get("message", {}).get("content", "")
                    if content:
                        self._circuit_breaker["ollama"] = 0
                        yield content
                    if data.get("done"):
                        break

    async def _stream_openai(self, prompt, model, max_tokens, temperature, system_prompt):
        import json

        from ..core.config import settings

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        model = model or settings.OPENAI_MODEL
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip() or not line.startswith("data:"):
                        continue
                    payload = line[len("data:") :].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        self._circuit_breaker["openai"] = 0
                        yield delta

    async def health_check(self) -> Dict[str, bool]:
        """检查各provider可用性"""
        results = {}

        # Ollama
        try:
            from ..core.config import settings
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                results["ollama"] = resp.status_code == 200
        except Exception:
            results["ollama"] = False

        # OpenAI
        from ..core.config import settings
        results["openai"] = bool(settings.OPENAI_API_KEY)

        return results
