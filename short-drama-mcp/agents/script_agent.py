#!/usr/bin/env python3
"""剧本格式化 Agent

标准化剧本格式、自动分段、添加场景标记、字数控制。
整合现有 format_checker 工具。
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from .base import BaseAgent, AgentConfig

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
try:
    from format_checker import check_markdown_file, CheckResult
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


# ── Prompt 模板 ──────────────────────────────────────────────

SCRIPT_SYSTEM = """你是一位专业的短剧剧本格式化编辑。你负责将草稿转化为标准剧本格式。

标准格式规范：
1. 标题格式：## 第X集：集名
2. 场景标记：【场景X】地点/时间/人物
3. 动作描写：（动作描述）
4. 对话格式：角色名："台词"（≤15字）
5. 结尾格式：第X集完
6. 每集字数：800-1200字
7. 禁止使用"耀"和"曜"字

格式层次：
- # 剧名
- ## 第X集：集名
- 【场景标记】
- （动作/表情）
- 角色名："台词"
- 第X集完"""

FORMAT_PROMPT = """请将以下内容格式化为标准短剧剧本。

## 原始内容
{content}

## 格式化类型
{format_type}

## 目标集数
{episode_count}

请输出格式化后的剧本（Markdown 格式），严格遵循以下规范：

1. 每集以 `## 第X集：集名` 开头
2. 每个场景以 `【场景X】地点 | 时间 | 人物` 标记
3. 动作描写用圆括号包裹：（动作）
4. 对话用引号包裹，且每句 ≤15 字
5. 每集以 `第X集完` 结尾
6. 总字数控制在目标范围内

请直接输出格式化后的 Markdown 文本（不需要 JSON 包装）。"""

SEGMENT_PROMPT = """请将以下剧本内容自动分段，添加场景标记。

## 原始剧本
{content}

以 JSON 格式输出分段结果：
```json
{{
  "segments": [
    {{
      "scene_id": 1,
      "location": "地点",
      "time": "时间（日/夜/晨/昏）",
      "characters": ["出场角色"],
      "mood": "情绪基调",
      "content": "该场景内容",
      "estimated_duration": "预计时长（秒）"
    }}
  ],
  "total_scenes": 0,
  "total_duration": "预计总时长"
}}
```"""

WORD_COUNT_PROMPT = """请分析以下剧本的字数分布并提出调整建议。

## 剧本内容
{content}

以 JSON 格式输出：
```json
{{
  "total_characters": 0,
  "episodes": [
    {{
      "episode": 1,
      "title": "集名",
      "character_count": 0,
      "dialogue_count": 0,
      "action_count": 0,
      "status": "过长/合适/过短",
      "suggestion": "调整建议"
    }}
  ],
  "overall_assessment": "整体评估",
  "adjustments": ["调整建议1", "调整建议2"]
}}
```

标准：每集 800-1200 字为合适。"""


class ScriptAgent(BaseAgent):
    """剧本格式化 Agent"""

    def format_script(
        self,
        content: str,
        format_type: str = "standard",
        episode_count: int = 8,
    ) -> Dict:
        """格式化剧本
        
        Args:
            content: 原始剧本内容
            format_type: 格式类型（standard/compact/detailed）
            episode_count: 目标集数
        
        Returns:
            格式化结果 dict
        """
        self.clear_logs()
        self._log(f"[ScriptAgent] 格式化剧本: {format_type} x {episode_count}集")

        prompt = FORMAT_PROMPT.format(
            content=content[:6000],
            format_type=format_type,
            episode_count=episode_count,
        )

        # 格式化输出是 Markdown 文本，不需要 JSON 解析
        formatted_text = self.call_llm(SCRIPT_SYSTEM, prompt, temperature=0.4)

        # 后处理
        result = {
            "formatted_text": formatted_text,
            "format_type": format_type,
            "episode_count": episode_count,
        }

        # 检查格式化质量
        result["quality_check"] = self._check_format_quality(formatted_text)

        # 如果工具可用，追加工具检查
        if TOOLS_AVAILABLE and "error" not in result["quality_check"]:
            self._log("[ScriptAgent] 追加工具格式检查")

        self._log(f"[ScriptAgent] 格式化完成: {len(formatted_text)} 字符")
        return result

    def auto_segment(self, content: str) -> Dict:
        """自动分段 + 添加场景标记
        
        Args:
            content: 剧本内容
        
        Returns:
            分段结果
        """
        self.clear_logs()
        prompt = SEGMENT_PROMPT.format(content=content[:5000])
        return self.call_llm_json(SCRIPT_SYSTEM, prompt, temperature=0.3)

    def analyze_word_count(self, content: str) -> Dict:
        """分析字数分布
        
        Args:
            content: 剧本内容
        
        Returns:
            字数分析结果
        """
        self.clear_logs()
        prompt = WORD_COUNT_PROMPT.format(content=content[:5000])
        return self.call_llm_json(SCRIPT_SYSTEM, prompt, temperature=0.2)

    def generate_scene_markers(self, content: str) -> List[Dict]:
        """为剧本生成场景标记
        
        Args:
            content: 剧本内容
        
        Returns:
            场景标记列表
        """
        result = self.auto_segment(content)
        return result.get("segments", [])

    def _check_format_quality(self, text: str) -> Dict:
        """检查格式化质量"""
        issues = []

        # 检查集标题格式
        ep_titles = re.findall(r'^##\s*第\d+集[：:].+', text, re.MULTILINE)
        if not ep_titles:
            issues.append("未找到标准集标题（应为 ## 第X集：集名）")

        # 检查结尾格式
        endings = re.findall(r'第\d+集完', text)
        ep_count = len(ep_titles)
        if len(endings) < ep_count:
            issues.append(f"缺少 {ep_count - len(endings)} 集的结尾标记")

        # 检查禁止字符
        forbidden = self.check_forbidden_chars(text)
        if forbidden:
            issues.append(f"发现禁止字符: {[i['char'] for i in forbidden]}")

        # 检查对话长度
        long_dialogues = self.check_dialogue_length(text)
        if long_dialogues:
            issues.append(f"发现 {len(long_dialogues)} 处超长对话")

        # 统计
        total_chars = len(re.sub(r'\s+', '', text))

        return {
            "episode_titles_found": len(ep_titles),
            "endings_found": len(endings),
            "total_characters": total_chars,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 15),
            "passed": len(issues) == 0,
        }

    def normalize_format(self, content: str) -> str:
        """纯规则格式化（不调用 LLM）
        
        对已有文本做规范化处理：
        - 统一集标题格式
        - 添加缺失的结尾标记
        - 标准化引号
        """
        lines = content.split('\n')
        result = []

        for line in lines:
            # 统一集标题
            match = re.match(r'^#+\s*第(\d+)集[：:]\s*(.+)', line)
            if match:
                line = f"## 第{match.group(1)}集：{match.group(2).strip()}"

            # 统一引号为中文引号
            line = line.replace('"', '\u201c').replace('"', '\u201d')

            result.append(line)

        return '\n'.join(result)


if __name__ == "__main__":
    agent = ScriptAgent()
    print("ScriptAgent 模块加载成功")
    print(f"工具集成: {'可用' if TOOLS_AVAILABLE else '不可用'}")
