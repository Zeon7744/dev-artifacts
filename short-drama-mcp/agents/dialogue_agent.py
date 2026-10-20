#!/usr/bin/env python3
"""对话生成 Agent

生成符合角色性格的短剧对话，控制长度 ≤15 字，添加情绪标记，避免禁止字符。
整合现有 dialogue_optimizer 工具。
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from .base import BaseAgent, AgentConfig

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
try:
    from dialogue_optimizer import (
        optimize_dialogue as _tool_optimize,
        extract_dialogues as _tool_extract,
    )
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


# ── Prompt 模板 ──────────────────────────────────────────────

DIALOGUE_SYSTEM = """你是一位短剧对话大师。你的对话风格：
1. 每句对话 ≤15 字（严格限制！）
2. 一句话一个情绪，绝不拖泥带水
3. 绝对禁止使用"耀"和"曜"字
4. 对话要有张力：短句制造紧张，省略号制造悬念
5. 不同角色说话风格必须明显不同
6. 动作描写用括号包裹：（冷笑）（转身离开）
7. 每段对话前后加动作/表情标记

短剧对话核心技巧：
- 能用 5 个字说完的绝不用 10 个字
- 多用反问、短句、断句
- 情绪转换要快，一场戏可以有 3 次情绪翻转
- 打脸台词要狠、准、短"""

DIALOGUE_GENERATE_PROMPT = """请为以下场景生成对话。

## 场景信息
{scene_description}

## 出场角色
{characters_info}

## 情绪基调
{mood}

## 本场景目标
{scene_goal}

请生成对话，以 JSON 格式输出：

```json
{{
  "scene_id": "场景编号",
  "location": "场景地点",
  "time": "时间",
  "dialogue_lines": [
    {{
      "character": "角色名",
      "emotion": "情绪（愤怒/冷淡/嘲讽/心动/震惊/悲伤/开心）",
      "action": "动作描写（可选）",
      "dialogue": "台词内容（≤15字！）",
      "subtext": "潜台词（可选）"
    }}
  ],
  "scene_beat": "本场景节拍（开场/冲突升级/高潮/转折/收尾）",
  "tension_level": 7
}}
```

注意：
- 每句台词严格 ≤15 字！
- 情绪标记必须明确
- 动作描写要具体（如"握紧拳头"而不是"生气"）
- 至少 {min_lines} 句对话"""

DIALOGUE_OPTIMIZE_PROMPT = """请优化以下对话，使其更符合短剧规范。

## 原始对话
{dialogue_text}

## 角色设定
{characters_info}

## 优化要求
1. 超长对话（>15字）必须拆分为多句或精简
2. 添加情绪标记和动作标记
3. 增强对话张力和冲突感
4. 保持角色语言风格一致
5. 禁止使用"耀"和"曜"字

以 JSON 格式输出：
```json
{{
  "original_issues": [
    {{"line": "原始台词", "issue": "问题描述", "fix": "修复方案"}}
  ],
  "optimized_lines": [
    {{
      "character": "角色名",
      "emotion": "情绪",
      "action": "动作",
      "dialogue": "优化后台词（≤15字）"
    }}
  ],
  "stats": {{
    "original_avg_length": 0,
    "optimized_avg_length": 0,
    "issues_fixed": 0
  }}
}}
```"""


class DialogueAgent(BaseAgent):
    """对话生成 Agent"""

    def generate_dialogue(
        self,
        scene: Dict,
        characters: List[Dict],
        mood: str = "紧张",
        scene_goal: str = "推动剧情",
        min_lines: int = 8,
    ) -> Dict:
        """为场景生成对话
        
        Args:
            scene: 场景描述 dict（含 location, time, description, events）
            characters: 角色列表
            mood: 情绪基调
            scene_goal: 本场景目标
            min_lines: 最少对话行数
        
        Returns:
            对话方案 dict
        """
        self.clear_logs()
        self._log(f"[DialogueAgent] 生成对话: {scene.get('location', '未知场景')}")

        # 构建角色信息
        chars_info = self._format_characters(characters)

        scene_desc = self._format_scene(scene)

        prompt = DIALOGUE_GENERATE_PROMPT.format(
            scene_description=scene_desc,
            characters_info=chars_info,
            mood=mood,
            scene_goal=scene_goal,
            min_lines=min_lines,
        )

        result = self.call_llm_json(DIALOGUE_SYSTEM, prompt, temperature=0.85)

        # 后处理：严格检查对话长度
        result = self._enforce_dialogue_limits(result)
        self._log(f"[DialogueAgent] 生成 {len(result.get('dialogue_lines', []))} 句对话")
        return result

    def optimize_dialogue(
        self,
        dialogue_text: str,
        characters: Optional[List[Dict]] = None,
    ) -> Dict:
        """优化已有对话
        
        Args:
            dialogue_text: 原始对话文本
            characters: 角色设定（可选）
        
        Returns:
            优化报告
        """
        self.clear_logs()
        chars_info = self._format_characters(characters) if characters else "（未提供角色设定）"

        prompt = DIALOGUE_OPTIMIZE_PROMPT.format(
            dialogue_text=dialogue_text[:4000],
            characters_info=chars_info,
        )

        result = self.call_llm_json(DIALOGUE_SYSTEM, prompt, temperature=0.6)

        # 如果工具可用，追加工具分析
        if TOOLS_AVAILABLE:
            try:
                tool_result = _tool_optimize(content=dialogue_text)
                result["tool_analysis"] = tool_result
            except Exception as e:
                self._log(f"[DialogueAgent] 工具分析跳过: {e}")

        return result

    def batch_generate_dialogues(
        self,
        scenes: List[Dict],
        characters: List[Dict],
    ) -> List[Dict]:
        """批量生成多个场景的对话
        
        Args:
            scenes: 场景列表
            characters: 角色列表
        
        Returns:
            对话结果列表
        """
        results = []
        for i, scene in enumerate(scenes):
            self._log(f"[DialogueAgent] 处理场景 {i+1}/{len(scenes)}")
            mood = scene.get("mood", "紧张")
            goal = scene.get("goal", "推动剧情")
            result = self.generate_dialogue(scene, characters, mood, goal)
            results.append(result)
        return results

    def _format_characters(self, characters: List[Dict]) -> str:
        """格式化角色信息给 prompt"""
        if not characters:
            return "（未提供角色信息）"

        lines = []
        for c in characters:
            name = c.get("name", "未知")
            personality = c.get("personality", "")
            speech = c.get("speech_style", "")
            lines.append(f"- {name}: 性格{personality}，说话风格{speech}")
        return "\n".join(lines)

    def _format_scene(self, scene: Dict) -> str:
        """格式化场景信息"""
        parts = []
        if scene.get("location"):
            parts.append(f"地点: {scene['location']}")
        if scene.get("time"):
            parts.append(f"时间: {scene['time']}")
        if scene.get("description"):
            parts.append(f"描述: {scene['description']}")
        if scene.get("events"):
            events = scene["events"] if isinstance(scene["events"], list) else [scene["events"]]
            parts.append(f"事件: {', '.join(str(e) for e in events)}")
        return "\n".join(parts) if parts else "（场景信息未提供）"

    def _enforce_dialogue_limits(self, result: Dict, max_len: int = 15) -> Dict:
        """强制对话长度限制"""
        lines = result.get("dialogue_lines", [])
        fixed_count = 0

        for line in lines:
            dialogue = line.get("dialogue", "")
            if len(dialogue) > max_len:
                # 尝试截断到合理位置
                truncated = dialogue[:max_len]
                # 尝试在标点处截断
                for punct in ["！", "。", "？", "，", "…"]:
                    idx = truncated.rfind(punct)
                    if idx > max_len // 2:
                        truncated = truncated[:idx + 1]
                        break
                line["dialogue"] = truncated
                line["_truncated"] = True
                fixed_count += 1

        if fixed_count > 0:
            self._log(f"[DialogueAgent] 截断 {fixed_count} 句超长对话")
            result["_stats"] = {"truncated_lines": fixed_count}

        # 检查禁止字符
        all_text = json.dumps(lines, ensure_ascii=False)
        forbidden = self.check_forbidden_chars(all_text)
        if forbidden:
            self._log(f"[DialogueAgent] 禁止字符: {forbidden}")
            result["_forbidden_chars"] = forbidden

        return result


if __name__ == "__main__":
    agent = DialogueAgent()
    print("DialogueAgent 模块加载成功")
    print(f"工具集成: {'可用' if TOOLS_AVAILABLE else '不可用'}")
