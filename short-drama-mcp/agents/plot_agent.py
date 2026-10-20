#!/usr/bin/env python3
"""剧情生成 Agent

基于小说/大纲生成短剧剧情，设计冲突反转、爽点甜点，保持故事连贯性。
"""

import json
from typing import Dict, List, Optional
from .base import BaseAgent, AgentConfig


# ── Prompt 模板 ──────────────────────────────────────────────

PLOT_SYSTEM = """你是一位顶级短剧编剧，专精红果短剧平台爆款剧本。

核心规则：
1. 每集至少 3 个爽点 + 1 个甜点
2. 对话简短有力，每句 ≤15 字
3. 绝对禁止使用"耀"和"曜"这两个字
4. 冲突密集，反转不断，节奏紧凑
5. 第一集必须有强钩子（30秒内抓住观众）
6. 每集结尾设置悬念，驱动下一集

你的任务是根据输入材料生成完整的剧情大纲和分集剧情。"""

PLOT_GENERATE_PROMPT = """请基于以下材料生成短剧剧情方案。

## 输入材料
{novel_input}

## 基本信息
- 题材类型：{genre}
- 目标集数：{episode_count} 集
- 每集目标字数：约 800-1200 字

## 要求
请生成完整的剧情方案，以 JSON 格式输出：

```json
{{
  "title": "剧名",
  "genre": "{genre}",
  "logline": "一句话概括故事（30字内）",
  "theme": "核心主题",
  "total_episodes": {episode_count},
  "structure": {{
    "setup_episodes": [1, 2],
    "rising_action_episodes": [3, 4, 5],
    "climax_episodes": [6, 7],
    "resolution_episodes": [8]
  }},
  "episodes": [
    {{
      "episode": 1,
      "title": "集名",
      "summary": "本集概要（50字内）",
      "opening_hook": "开场钩子",
      "conflicts": ["冲突1", "冲突2"],
      "shuang_points": [
        {{"type": "打脸反转", "description": "具体描述"}}
      ],
      "tiandian": [
        {{"type": "情感满足", "description": "具体描述"}}
      ],
      "cliffhanger": "集末悬念",
      "key_scenes": ["场景1", "场景2", "场景3"]
    }}
  ]
}}
```

确保：
- 爽点分布均匀，每集 ≥3 个
- 反转至少每 2 集出现一次大反转
- 第一集钩子要强力（身份揭露/危机/逆袭）
- 每集结尾悬念要勾人"""

PLOT_CONTINUE_PROMPT = """继续发展以下剧情，从第 {start_episode} 集开始。

## 已有剧情概要
{previous_summary}

## 已有角色
{characters}

## 要求
- 保持与前文连贯
- 逐步升级冲突
- 每集保持 ≥3 爽点 + 1 甜点
- 输出 JSON 格式的剧集列表"""


class PlotAgent(BaseAgent):
    """剧情生成 Agent"""

    def generate_plot(
        self,
        novel_input: str,
        genre: str = "都市甜宠",
        episode_count: int = 8,
        previous_context: Optional[Dict] = None,
    ) -> Dict:
        """生成剧情方案
        
        Args:
            novel_input: 小说原文 / 大纲 / 故事梗概
            genre: 题材类型
            episode_count: 目标集数
            previous_context: 已有剧情上下文（续写时使用）
        
        Returns:
            完整的剧情方案 dict
        """
        self.clear_logs()
        self._log(f"[PlotAgent] 开始生成剧情: {genre} x {episode_count}集")

        # 截断过长的输入（避免超 token）
        truncated_input = novel_input[:6000] if len(novel_input) > 6000 else novel_input

        if previous_context:
            return self._continue_plot(truncated_input, previous_context, genre, episode_count)

        prompt = PLOT_GENERATE_PROMPT.format(
            novel_input=truncated_input,
            genre=genre,
            episode_count=episode_count,
        )

        result = self.call_llm_json(PLOT_SYSTEM, prompt, temperature=0.85)

        # 后处理验证
        result = self._validate_plot(result, episode_count)
        self._log(f"[PlotAgent] 生成完成: {result.get('title', '未命名')}")
        return result

    def _continue_plot(
        self,
        novel_input: str,
        context: Dict,
        genre: str,
        episode_count: int,
    ) -> Dict:
        """续写剧情"""
        prev_summary = json.dumps(
            context.get("episodes", []),
            ensure_ascii=False, indent=2
        )[:3000]
        chars = json.dumps(
            context.get("characters", []),
            ensure_ascii=False, indent=2
        )[:1500]

        prompt = PLOT_CONTINUE_PROMPT.format(
            start_episode=context.get("total_episodes", 0) + 1,
            previous_summary=prev_summary,
            characters=chars,
        )
        prompt += f"\n\n题材: {genre}\n目标集数: {episode_count}\n\n请以 JSON 格式输出新剧集列表。"

        result = self.call_llm_json(PLOT_SYSTEM, prompt, temperature=0.85)
        return result

    def _validate_plot(self, plot: Dict, expected_episodes: int) -> Dict:
        """验证剧情方案完整性"""
        # 确保有 episodes 列表
        if "episodes" not in plot:
            plot["episodes"] = []

        # 检查每集爽点数
        for ep in plot.get("episodes", []):
            sp_count = len(ep.get("shuang_points", []))
            if sp_count < 3:
                self._log(
                    f"[PlotAgent] 警告: 第{ep.get('episode', '?')}集 "
                    f"仅 {sp_count} 个爽点（需≥3）"
                )

        # 检查集数
        actual = len(plot.get("episodes", []))
        if actual < expected_episodes:
            self._log(
                f"[PlotAgent] 警告: 期望 {expected_episodes} 集，实际 {actual} 集"
            )

        return plot

    def generate_story_arc(self, genre: str, theme: str) -> Dict:
        """生成故事弧线模板
        
        Args:
            genre: 题材
            theme: 主题
        
        Returns:
            故事弧线结构
        """
        system = PLOT_SYSTEM
        prompt = f"""请为以下短剧生成故事弧线：
- 题材: {genre}
- 主题: {theme}

以 JSON 格式输出：
```json
{{
  "genre": "{genre}",
  "theme": "{theme}",
  "three_act_structure": {{
    "act1_setup": {{"episodes": "1-2", "description": "...", "key_events": ["..."]}},
    "act2_confrontation": {{"episodes": "3-6", "description": "...", "key_events": ["..."]}},
    "act3_resolution": {{"episodes": "7-8", "description": "...", "key_events": ["..."]}}
  }},
  "emotional_curve": ["紧张", "甜蜜", "危机", "反转", "高潮", "温暖"],
  "twist_points": [
    {{"episode": 3, "twist": "..."}},
    {{"episode": 6, "twist": "..."}}
  ]
}}
```"""
        return self.call_llm_json(system, prompt, temperature=0.8)


if __name__ == "__main__":
    agent = PlotAgent()
    print("PlotAgent 模块加载成功")
    print(f"禁止字符: {agent.FORBIDDEN_CHARS}")
