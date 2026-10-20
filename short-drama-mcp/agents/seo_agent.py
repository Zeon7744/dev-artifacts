#!/usr/bin/env python3
"""SEO 优化 Agent

生成标题、优化标签、关键词分析、封面建议。
"""

import json
from typing import Dict, List, Optional
from .base import BaseAgent, AgentConfig


# ── Prompt 模板 ──────────────────────────────────────────────

SEO_SYSTEM = """你是一位短剧平台 SEO 优化专家。你精通：
1. 短剧平台搜索算法（红果、快手、抖音）
2. 标题点击率优化（CTR）
3. 标签权重和热度平衡
4. 封面设计对点击率的影响
5. 关键词布局和搜索流量捕获

核心原则：
- 标题：12-20字，包含核心冲突+悬念+情绪词
- 标签：3-5个，热度+精准度平衡
- 封面：高对比度+人物表情+文字点缀
- 简介：50-100字，前20字抓眼球"""

SEO_OPTIMIZE_PROMPT = """请为以下短剧进行 SEO 优化。

## 基本信息
- 原始标题：{title}
- 题材类型：{genre}
- 故事简介：{description}
- 当前标签：{tags}

请输出 JSON 格式的优化方案：

```json
{{
  "title_options": [
    {{
      "title": "优化标题",
      "ctr_estimate": "预估点击率评级（高/中/低）",
      "strategy": "策略说明（悬念型/冲突型/情感型）",
      "keywords": ["核心关键词"]
    }}
  ],
  "recommended_tags": [
    {{"tag": "标签", "heat": "热度（高/中/低）", "relevance": "相关度"}}
  ],
  "description_options": [
    {{
      "text": "优化后简介（50-100字）",
      "hook_position": "钩子在第X字",
      "keywords_included": ["嵌入的关键词"]
    }}
  ],
  "cover_suggestions": {{
    "style": "封面风格建议",
    "text_overlay": "封面文字建议",
    "color_scheme": "配色方案",
    "character_focus": "角色焦点建议",
    "emotion": "封面情绪"
  }},
  "keyword_analysis": {{
    "primary_keywords": ["主关键词"],
    "secondary_keywords": ["长尾关键词"],
    "search_volume_estimate": "搜索量预估",
    "competition_level": "竞争程度"
  }},
  "platform_specific": {{
    "hongguo": {{"title": "红果标题", "tags": ["标签"]}},
    "kuaishou": {{"title": "快手标题", "tags": ["标签"]}}
  }}
}}
```"""

TITLE_GENERATE_PROMPT = """请为以下短剧生成多个标题选项。

## 故事概要
{story_summary}

## 题材
{genre}

## 核心冲突
{core_conflict}

请生成 5-8 个标题，以 JSON 格式输出：

```json
{{
  "titles": [
    {{
      "title": "标题（12-20字）",
      "type": "类型（悬念/冲突/反转/情感/身份）",
      "hook": "钩子说明",
      "ctr_score": 0,
      "keywords": ["关键词"]
    }}
  ],
  "best_pick": "推荐首选标题",
  "reason": "推荐理由"
}}
```

标题规则：
1. 12-20字
2. 包含身份反转/冲突/悬念元素
3. 情绪词打头（震惊/逆袭/复仇...）
4. 让人想点进去看"然后呢？"
5. 禁止使用"耀"和"曜"字"""


class SeoAgent(BaseAgent):
    """SEO 优化 Agent"""

    def optimize_seo(
        self,
        title: str = "",
        description: str = "",
        tags: Optional[List[str]] = None,
        genre: str = "都市",
    ) -> Dict:
        """全面 SEO 优化
        
        Args:
            title: 原始标题
            description: 故事简介
            tags: 当前标签
            genre: 题材类型
        
        Returns:
            SEO 优化方案
        """
        self.clear_logs()
        self._log(f"[SeoAgent] SEO 优化: {title or '未命名'}")

        prompt = SEO_OPTIMIZE_PROMPT.format(
            title=title or "（未提供）",
            genre=genre,
            description=description[:500] or "（未提供）",
            tags=", ".join(tags) if tags else "（未提供）",
        )

        result = self.call_llm_json(SEO_SYSTEM, prompt, temperature=0.7)
        self._log(f"[SeoAgent] 优化完成: {len(result.get('title_options', []))} 个标题选项")
        return result

    def generate_titles(
        self,
        story_summary: str,
        genre: str = "都市",
        core_conflict: str = "",
    ) -> Dict:
        """生成标题选项
        
        Args:
            story_summary: 故事概要
            genre: 题材
            core_conflict: 核心冲突
        
        Returns:
            标题选项列表
        """
        self.clear_logs()
        prompt = TITLE_GENERATE_PROMPT.format(
            story_summary=story_summary[:1000],
            genre=genre,
            core_conflict=core_conflict or "（未指定）",
        )
        result = self.call_llm_json(SEO_SYSTEM, prompt, temperature=0.85)

        # 检查禁止字符
        titles = result.get("titles", [])
        for t in titles:
            title_text = t.get("title", "")
            forbidden = self.check_forbidden_chars(title_text)
            if forbidden:
                t["_warning"] = f"包含禁止字符: {[f['char'] for f in forbidden]}"

        return result

    def analyze_keywords(self, content: str, genre: str = "都市") -> Dict:
        """关键词分析
        
        Args:
            content: 剧本/简介内容
            genre: 题材
        
        Returns:
            关键词分析结果
        """
        self.clear_logs()
        system = SEO_SYSTEM
        prompt = f"""请分析以下内容的关键词布局。

## 内容
{content[:3000]}

## 题材
{genre}

以 JSON 格式输出：
```json
{{
  "extracted_keywords": [
    {{"keyword": "关键词", "frequency": 0, "weight": "高/中/低"}}
  ],
  "missing_keywords": ["应该添加的关键词"],
  "keyword_density": "关键词密度评估",
  "seo_score": 0,
  "suggestions": ["优化建议"]
}}
```"""
        return self.call_llm_json(system, prompt, temperature=0.3)

    def generate_cover_brief(
        self,
        title: str,
        genre: str,
        characters: Optional[List[Dict]] = None,
    ) -> Dict:
        """生成封面设计需求文档
        
        Args:
            title: 剧名
            genre: 题材
            characters: 主要角色
        
        Returns:
            封面设计 brief
        """
        self.clear_logs()
        chars_desc = ""
        if characters:
            chars_desc = ", ".join(
                f"{c.get('name', '')}({c.get('appearance', '')})"
                for c in characters[:3]
            )

        system = SEO_SYSTEM
        prompt = f"""请为以下短剧设计封面方案。

- 剧名: {title}
- 题材: {genre}
- 主要角色: {chars_desc or '未指定'}

以 JSON 格式输出封面设计方案：
```json
{{
  "design_options": [
    {{
      "style": "设计风格",
      "composition": "构图说明",
      "main_visual": "主视觉元素",
      "text_overlay": "封面文字",
      "color_palette": ["主色", "辅色", "强调色"],
      "emotion": "传达情绪",
      "reference_style": "参考风格"
    }}
  ],
  "best_pick": "推荐方案编号",
  "platform_adaptations": {{
    "hongguo": "红果平台适配建议",
    "kuaishou": "快手平台适配建议"
  }}
}}
```"""
        return self.call_llm_json(system, prompt, temperature=0.7)


if __name__ == "__main__":
    agent = SeoAgent()
    print("SeoAgent 模块加载成功")
