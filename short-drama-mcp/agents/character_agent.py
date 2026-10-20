#!/usr/bin/env python3
"""角色设计 Agent

生成角色设定、人物关系、成长弧线，并进行一致性检查。
整合现有 character_creator 工具 + LLM 增强。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from .base import BaseAgent, AgentConfig

# 复用现有工具
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
try:
    from character_creator import (
        create_character_profile as _tool_create_profile,
        create_character_set as _tool_create_set,
    )
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


# ── Prompt 模板 ──────────────────────────────────────────────

CHARACTER_SYSTEM = """你是一位资深短剧角色设计师。你创建的角色必须：
1. 性格鲜明，有记忆点（一句话能描述清楚）
2. 关系网紧密，每个角色都与主角有核心冲突或情感连接
3. 成长弧线明确（从 A 状态变化到 B 状态）
4. 对话风格各异（能仅凭台词区分角色）
5. 禁止使用"耀"和"曜"字

短剧角色特殊性：
- 主角通常有隐藏身份或逆袭设定
- 反派要够可恨，打脸才爽
- 配角要有功能性（助攻/信息/搞笑）"""

CHARACTER_CREATE_PROMPT = """请为以下短剧设计完整角色方案。

## 故事概要
{story_summary}

## 题材类型
{genre}

## 要求
设计一组角色（至少 {character_count} 个），以 JSON 格式输出：

```json
{{
  "characters": [
    {{
      "name": "角色姓名",
      "role_type": "protagonist/antagonist/love_interest/mentor/ally/comic_relief",
      "age": "年龄/年龄段",
      "identity": "表面身份",
      "true_identity": "真实身份（如有隐藏）",
      "personality": "性格特点（3个关键词）",
      "appearance": "外貌描写（20字内）",
      "background": "背景故事（30字内）",
      "motivation": "核心动机",
      "flaw": "致命弱点",
      "secret": "隐藏秘密",
      "arc": "成长弧线: 从__到__",
      "relationship_map": {{
        "主角": "关系描述",
        "其他角色": "关系描述"
      }},
      "speech_style": "说话风格（如：冷淡/傲娇/阴阳怪气）",
      "catchphrase": "标志性台词（≤15字）",
      "key_moments": ["关键时刻1", "关键时刻2"]
    }}
  ],
  "relationship_web": {{
    "description": "整体关系网络描述",
    "conflicts": [
      {{"from": "角色A", "to": "角色B", "type": "冲突类型", "description": "..."}}
    ],
    "alliances": [
      {{"from": "角色A", "to": "角色B", "type": "同盟类型"}}
    ]
  }}
}}
```"""

CHARACTER_CONSISTENCY_PROMPT = """请检查以下角色设定的一致性。

## 角色列表
{characters_json}

## 剧情概要
{story_summary}

请检查以下维度并输出 JSON：

```json
{{
  "overall_score": 85,
  "issues": [
    {{
      "type": "矛盾/缺失/冲突",
      "severity": "高/中/低",
      "characters": ["角色A", "角色B"],
      "description": "具体问题描述",
      "suggestion": "修复建议"
    }}
  ],
  "strengths": ["优势1", "优势2"],
  "suggestions": ["优化建议1", "优化建议2"]
}}
```

检查维度：
1. 角色性格是否自洽（行为与性格匹配）
2. 关系网是否合理（不矛盾）
3. 动机是否充分（支撑行为逻辑）
4. 是否有功能缺失（如缺少关键配角）
5. 角色是否可区分（不能太相似）"""


class CharacterAgent(BaseAgent):
    """角色设计 Agent"""

    def create_characters(
        self,
        story_summary: str,
        genre: str = "都市甜宠",
        character_count: int = 5,
    ) -> Dict:
        """生成角色方案
        
        Args:
            story_summary: 故事梗概
            genre: 题材类型
            character_count: 角色数量
        
        Returns:
            完整角色方案 dict
        """
        self.clear_logs()
        self._log(f"[CharacterAgent] 开始设计角色: {genre} x {character_count}个")

        prompt = CHARACTER_CREATE_PROMPT.format(
            story_summary=story_summary,
            genre=genre,
            character_count=character_count,
        )

        result = self.call_llm_json(CHARACTER_SYSTEM, prompt, temperature=0.85)

        # 合并工具生成的基础设定
        if TOOLS_AVAILABLE:
            result = self._merge_tool_profiles(result, genre)

        # 后处理
        result = self._validate_characters(result)
        self._log(f"[CharacterAgent] 设计完成: {len(result.get('characters', []))} 个角色")
        return result

    def _merge_tool_profiles(self, llm_result: Dict, genre: str) -> Dict:
        """合并工具生成的基础角色数据"""
        for char in llm_result.get("characters", []):
            role_type = char.get("role_type", "support")
            # 映射到工具的角色类型
            tool_type = "protagonist" if role_type == "protagonist" else \
                        "antagonist" if role_type == "antagonist" else "support"
            try:
                tool_profile = _tool_create_profile(
                    name=char["name"],
                    role_type=tool_type,
                    genre=genre,
                )
                # 工具数据作为补充，不覆盖 LLM 的创意内容
                if not char.get("appearance"):
                    char["appearance"] = tool_profile.get("appearance", "")
                if not char.get("catchphrase"):
                    char["catchphrase"] = tool_profile.get("catchphrase", "")
            except Exception as e:
                self._log(f"[CharacterAgent] 工具合并跳过: {e}")
        return llm_result

    def _validate_characters(self, result: Dict) -> Dict:
        """验证角色方案"""
        chars = result.get("characters", [])

        # 检查必需字段
        required = ["name", "role_type", "personality", "motivation"]
        for char in chars:
            for field in required:
                if field not in char or not char[field]:
                    self._log(f"[CharacterAgent] 警告: {char.get('name', '?')} 缺少 {field}")

        # 检查对话长度
        for char in chars:
            cp = char.get("catchphrase", "")
            if len(cp) > 15:
                self._log(
                    f"[CharacterAgent] 警告: {char['name']} 台词超长 "
                    f"({len(cp)}字): {cp}"
                )

        # 检查禁止字符
        full_text = json.dumps(chars, ensure_ascii=False)
        issues = self.check_forbidden_chars(full_text)
        if issues:
            self._log(f"[CharacterAgent] 禁止字符检测: {issues}")

        return result

    def check_consistency(
        self,
        characters: List[Dict],
        story_summary: str = "",
    ) -> Dict:
        """检查角色一致性
        
        Args:
            characters: 角色列表
            story_summary: 故事概要
        
        Returns:
            一致性检查报告
        """
        chars_json = json.dumps(characters, ensure_ascii=False, indent=2)
        prompt = CHARACTER_CONSISTENCY_PROMPT.format(
            characters_json=chars_json[:4000],
            story_summary=story_summary or "（未提供）",
        )
        return self.call_llm_json(CHARACTER_SYSTEM, prompt, temperature=0.3)

    def generate_character_arc(
        self,
        character: Dict,
        episode_count: int = 8,
    ) -> Dict:
        """为单个角色生成详细的成长弧线
        
        Args:
            character: 角色设定
            episode_count: 集数
        
        Returns:
            成长弧线详情
        """
        system = CHARACTER_SYSTEM
        char_json = json.dumps(character, ensure_ascii=False, indent=2)
        prompt = f"""请为以下角色设计详细的成长弧线：

## 角色设定
{char_json}

## 故事长度
{episode_count} 集

以 JSON 格式输出：
```json
{{
  "character_name": "{character.get('name', '')}",
  "arc_type": "逆袭型/觉醒型/救赎型/黑化型",
  "start_state": "初始状态描述",
  "end_state": "最终状态描述",
  "turning_points": [
    {{"episode": 1, "event": "...", "emotional_state": "..."}},
    {{"episode": 3, "event": "...", "emotional_state": "..."}},
    {{"episode": 6, "event": "...", "emotional_state": "..."}}
  ],
  "internal_conflict": "内心冲突",
  "external_pressure": "外部压力",
  "resolution": "如何解决内心冲突"
}}
```"""
        return self.call_llm_json(system, prompt, temperature=0.75)


if __name__ == "__main__":
    agent = CharacterAgent()
    print("CharacterAgent 模块加载成功")
    print(f"工具集成: {'可用' if TOOLS_AVAILABLE else '不可用'}")
