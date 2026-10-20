#!/usr/bin/env python3
"""趋势分析 Agent

分析热门元素、预测市场趋势、竞品对比、受众画像。
"""

import json
from typing import Dict, List, Optional
from .base import BaseAgent, AgentConfig


# ── Prompt 模板 ──────────────────────────────────────────────

TREND_SYSTEM = """你是一位短剧市场分析专家，精通红果短剧、快手短剧、抖音短剧等平台的运营数据和用户偏好。

你的分析基于：
1. 平台热门榜单数据（题材、标签、播放量）
2. 用户画像（年龄、性别、观看时段、完播率）
3. 爆款要素拆解（钩子、反转、节奏）
4. 季节性/节日性趋势
5. 政策风向（平台审核重点）"""

TREND_ANALYZE_PROMPT = """请分析 {platform} 平台 {genre} 题材的短剧市场趋势。

以 JSON 格式输出：

```json
{{
  "platform": "{platform}",
  "genre": "{genre}",
  "analysis_date": "分析日期",
  "market_overview": {{
    "market_size": "市场规模描述",
    "growth_trend": "增长趋势",
    "competition_level": "竞争激烈程度（高/中/低）",
    "saturation": "饱和程度"
  }},
  "hot_elements": {{
    "popular_themes": ["热门主题1", "热门主题2"],
    "popular_settings": ["热门设定1", "热门设定2"],
    "popular_character_types": ["热门角色类型"],
    "popular_conflict_types": ["热门冲突类型"],
    "emerging_trends": ["新兴趋势1", "新兴趋势2"]
  }},
  "audience_profile": {{
    "primary_age": "主力年龄段",
    "gender_ratio": "男女比例",
    "peak_hours": ["高峰时段"],
    "avg_watch_duration": "平均观看时长",
    "completion_rate": "预估完播率"
  }},
  "competitive_analysis": {{
    "top_works": [
      {{"title": "作品名", "views": "播放量", "key_strength": "核心优势"}}
    ],
    "gap_opportunities": ["差异化机会1", "差异化机会2"]
  }},
  "recommendations": {{
    "suggested_themes": ["推荐主题"],
    "suggested_hooks": ["推荐钩子类型"],
    "suggested_twists": ["推荐反转方式"],
    "avoid": ["应避免的元素"],
    "timing": "最佳发布时机"
  }}
}}
```"""

COMPETITIVE_PROMPT = """请对比分析以下短剧作品。

## 作品列表
{works_info}

以 JSON 格式输出竞品分析报告：
```json
{{
  "comparison": [
    {{
      "title": "作品名",
      "genre": "题材",
      "strengths": ["优势"],
      "weaknesses": ["劣势"],
      "shuang_density": "爽点密度评估",
      "audience_feedback": "受众反馈分析",
      "commercial_potential": "商业潜力评级"
    }}
  ],
  "market_positioning": "市场定位建议",
  "differentiation": "差异化策略",
  "opportunity_matrix": {{
    "high_potential_low_competition": ["蓝海方向"],
    "high_potential_high_competition": ["红海方向"]
  }}
}}
```"""


class TrendAgent(BaseAgent):
    """趋势分析 Agent"""

    def analyze_trends(
        self,
        platform: str = "红果短剧",
        genre: str = "都市甜宠",
    ) -> Dict:
        """分析平台趋势
        
        Args:
            platform: 目标平台
            genre: 题材类型
        
        Returns:
            趋势分析报告
        """
        self.clear_logs()
        self._log(f"[TrendAgent] 分析趋势: {platform} / {genre}")

        prompt = TREND_ANALYZE_PROMPT.format(platform=platform, genre=genre)
        result = self.call_llm_json(TREND_SYSTEM, prompt, temperature=0.7)

        self._log(f"[TrendAgent] 分析完成")
        return result

    def competitive_analysis(
        self,
        works: List[Dict],
    ) -> Dict:
        """竞品对比分析
        
        Args:
            works: 作品列表，每个 dict 含 title, genre, description 等
        
        Returns:
            竞品分析报告
        """
        self.clear_logs()
        works_info = json.dumps(works, ensure_ascii=False, indent=2)[:3000]
        prompt = COMPETITIVE_PROMPT.format(works_info=works_info)
        return self.call_llm_json(TREND_SYSTEM, prompt, temperature=0.6)

    def genre_recommendation(self, goals: Optional[Dict] = None) -> Dict:
        """根据目标推荐最佳题材
        
        Args:
            goals: 目标参数（如 target_audience, expected_views 等）
        
        Returns:
            题材推荐报告
        """
        self.clear_logs()
        system = TREND_SYSTEM
        goals_str = json.dumps(goals or {}, ensure_ascii=False)
        prompt = f"""基于当前市场趋势，为以下创作目标推荐最佳题材方向。

## 创作目标
{goals_str}

以 JSON 格式输出：
```json
{{
  "recommended_genres": [
    {{
      "genre": "题材名",
      "score": 0,
      "reason": "推荐理由",
      "market_potential": "市场潜力",
      "competition": "竞争程度",
      "target_audience": "目标受众",
      "estimated_completion_rate": "预估完播率"
    }}
  ],
  "emerging_opportunities": ["新兴机会"],
  "risk_warning": ["风险提醒"]
}}
```"""
        return self.call_llm_json(system, prompt, temperature=0.7)


if __name__ == "__main__":
    agent = TrendAgent()
    print("TrendAgent 模块加载成功")
