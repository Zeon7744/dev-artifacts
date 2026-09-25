#!/usr/bin/env python3
"""Agent 基类 - 统一的 LLM 调用、重试、输出解析"""

import os
import json
import time
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class AgentConfig:
    """Agent 配置"""
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.8
    max_tokens: int = 4096
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 60

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY", "")


class BaseAgent:
    """Agent 基类
    
    提供：
    - LLM API 调用（OpenAI 兼容格式）
    - 自动重试 + 指数退避
    - JSON 输出解析（含修复）
    - 禁止字符检测（耀/曜）
    - 对话长度校验（≤15字）
    - 统一日志输出
    """

    # 全局禁止字符
    FORBIDDEN_CHARS = ["耀", "曜"]

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self._client = None
        self._logs: List[str] = []

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def _get_client(self):
        """懒加载 OpenAI 客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "请安装 openai: pip install openai>=1.0.0"
                )
            if not self.config.api_key:
                raise ValueError(
                    "未配置 API Key，请设置 OPENAI_API_KEY 环境变量或传入 AgentConfig"
                )
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        return self._client

    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """调用 LLM 并返回文本
        
        包含重试 + 指数退避。
        """
        client = self._get_client()
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        last_error = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                self._log(f"[{self.name}] 调用 LLM (attempt {attempt})")
                resp = client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temp,
                    max_tokens=tokens,
                )
                content = resp.choices[0].message.content or ""
                self._log(f"[{self.name}] 返回 {len(content)} 字符")
                return content.strip()
            except Exception as e:
                last_error = e
                self._log(f"[{self.name}] 失败: {e}")
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** (attempt - 1))
                    self._log(f"[{self.name}] {delay}s 后重试...")
                    time.sleep(delay)

        raise RuntimeError(
            f"{self.name} LLM 调用失败（{self.config.max_retries} 次重试后）: {last_error}"
        )

    def call_llm_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict:
        """调用 LLM 并解析 JSON 输出
        
        自动修复常见的 JSON 格式问题。
        """
        raw = self.call_llm(system_prompt, user_prompt, temperature, max_tokens)
        return self._parse_json(raw)

    def _parse_json(self, text: str) -> Dict:
        """从 LLM 输出中提取并解析 JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 代码块
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取 { ... } 或 [ ... ]
        for start_char, end_char in [('{', '}'), ('[', ']')]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    continue

        raise ValueError(f"无法从 LLM 输出中解析 JSON:\n{text[:500]}...")

    def check_forbidden_chars(self, text: str) -> List[Dict]:
        """检测禁止字符（耀/曜）"""
        issues = []
        for char in self.FORBIDDEN_CHARS:
            positions = [i for i, c in enumerate(text) if c == char]
            if positions:
                issues.append({
                    "char": char,
                    "count": len(positions),
                    "positions": positions[:10],  # 最多报10个位置
                })
        return issues

    def check_dialogue_length(self, text: str, max_len: int = 15) -> List[Dict]:
        """检测超长对话"""
        issues = []
        dialogues = re.findall(r'["\u201c]([^"\u201d]+)["\u201d]', text)
        for d in dialogues:
            if len(d) > max_len:
                issues.append({
                    "dialogue": d,
                    "length": len(d),
                    "max_allowed": max_len,
                    "suggestion": d[:max_len],
                })
        return issues

    def _log(self, msg: str):
        """记录日志"""
        self._logs.append(msg)
        print(msg)

    def get_logs(self) -> List[str]:
        """获取日志"""
        return list(self._logs)

    def clear_logs(self):
        """清空日志"""
        self._logs.clear()
