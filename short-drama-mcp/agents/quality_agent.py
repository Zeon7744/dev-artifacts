#!/usr/bin/env python3
"""质量检查 Agent

综合检查剧本格式、爽点密度、禁止字符、对话长度，输出优化建议。
整合现有 format_checker + shuang_analyzer + platform_checker 工具。
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from .base import BaseAgent, AgentConfig

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
try:
    from format_checker import check_markdown_file
    from shuang_analyzer import count_shuang_points, analyze_episode, parse_episodes
    from platform_checker import check_platform_compliance
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


# ── Prompt 模板 ──────────────────────────────────────────────

QUALITY_SYSTEM = """你是一位短剧剧本质量审核专家。你的审查标准：

必检项（硬性指标）：
1. 禁止字符：绝对不能出现"耀"和"曜"
2. 对话长度：每句 ≤15 字
3. 爽点密度：每集 ≥3 个爽点
4. 甜点密度：每集 ≥1 个甜点
5. 每集字数：800-1200 字
6. 格式规范：集标题、场景标记、结尾格式

加分项（软性指标）：
1. 第一集钩子强度
2. 反转节奏（至少每2集一次大反转）
3. 角色辨识度
4. 情绪曲线完整度
5. 冲突升级合理性"""

QUALITY_CHECK_PROMPT = """请对以下剧本进行全面质量审查。

## 剧本内容
{script_content}

## 自动分析数据
{auto_analysis}

请综合以上信息，输出 JSON 格式的审查报告：

```json
{{
  "overall_score": 0,
  "grade": "S/A/B/C/D",
  "summary": "一句话总结",
  "dimensions": {{
    "format_compliance": {{"score": 0, "issues": [], "max": 20}},
    "dialogue_quality": {{"score": 0, "issues": [], "max": 20}},
    "shuang_density": {{"score": 0, "issues": [], "max": 20}},
    "story_structure": {{"score": 0, "issues": [], "max": 20}},
    "character_depth": {{"score": 0, "issues": [], "max": 20}}
  }},
  "critical_issues": [
    {{"severity": "致命/严重/一般", "description": "...", "location": "第X集", "fix": "..."}}
  ],
  "improvements": [
    {{"priority": "高/中/低", "category": "对话/剧情/角色/格式", "suggestion": "...", "impact": "提升X分"}}
  ],
  "highlights": ["亮点1", "亮点2"],
  "verdict": "通过/修改后通过/不合格"
}}
```"""


class QualityAgent(BaseAgent):
    """质量检查 Agent"""

    def check_quality(self, script_content: str) -> Dict:
        """全面质量检查
        
        Args:
            script_content: 剧本文本内容
        
        Returns:
            质量审查报告
        """
        self.clear_logs()
        self._log("[QualityAgent] 开始质量检查")

        # 第一步：自动分析（工具层）
        auto_analysis = self._auto_analyze(script_content)

        # 第二步：LLM 综合评审
        prompt = QUALITY_CHECK_PROMPT.format(
            script_content=script_content[:5000],
            auto_analysis=json.dumps(auto_analysis, ensure_ascii=False, indent=2)[:3000],
        )

        result = self.call_llm_json(QUALITY_SYSTEM, prompt, temperature=0.3)

        # 合并自动分析数据
        result["auto_analysis"] = auto_analysis

        # 确保禁止字符零容忍
        forbidden = self.check_forbidden_chars(script_content)
        if forbidden:
            result.setdefault("critical_issues", []).append({
                "severity": "致命",
                "description": f"发现禁止字符: {[f['char'] for f in forbidden]}",
                "location": "全文",
                "fix": "全局替换禁止字符",
            })
            result["overall_score"] = min(result.get("overall_score", 0), 30)
            result["verdict"] = "不合格"

        self._log(f"[QualityAgent] 检查完成: {result.get('grade', '?')}级 / {result.get('overall_score', '?')}分")
        return result

    def _auto_analyze(self, content: str) -> Dict:
        """自动分析（规则层，不调 LLM）"""
        result = {
            "char_count": len(re.sub(r'\s+', '', content)),
            "dialogue_stats": self._analyze_dialogues(content),
            "forbidden_chars": self.check_forbidden_chars(content),
        }

        # 如果有工具，追加分析
        if TOOLS_AVAILABLE:
            try:
                # 爽点分析（需要写入临时文件）
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                    f.write(content)
                    tmp_path = f.name
                shuang = count_shuang_points(tmp_path)
                result["shuang_analysis"] = shuang
                Path(tmp_path).unlink(missing_ok=True)
            except Exception as e:
                self._log(f"[QualityAgent] 爽点分析跳过: {e}")

            try:
                compliance = check_platform_compliance.__wrapped__(content) if hasattr(check_platform_compliance, '__wrapped__') else None
                if compliance:
                    result["platform_compliance"] = compliance
            except Exception:
                pass

        # 集数统计
        episodes = parse_episodes(content) if TOOLS_AVAILABLE else []
        result["episode_count"] = len(episodes)

        return result

    def _analyze_dialogues(self, content: str) -> Dict:
        """分析对话统计"""
        dialogues = re.findall(r'["\u201c]([^"\u201d]+)["\u201d]', content)
        if not dialogues:
            return {"total": 0, "avg_length": 0, "over_15_count": 0}

        lengths = [len(d) for d in dialogues]
        over_15 = [d for d in dialogues if len(d) > 15]

        return {
            "total": len(dialogues),
            "avg_length": round(sum(lengths) / len(lengths), 1),
            "max_length": max(lengths),
            "min_length": min(lengths),
            "over_15_count": len(over_15),
            "over_15_examples": over_15[:5],
        }

    def quick_check(self, script_content: str) -> Dict:
        """快速检查（仅规则层，不调 LLM）
        
        Args:
            script_content: 剧本文本
        
        Returns:
            快速检查结果
        """
        self.clear_logs()
        analysis = self._auto_analyze(script_content)

        issues = []

        # 禁止字符
        if analysis["forbidden_chars"]:
            issues.append({
                "severity": "致命",
                "type": "forbidden_chars",
                "detail": analysis["forbidden_chars"],
            })

        # 超长对话
        ds = analysis.get("dialogue_stats", {})
        if ds.get("over_15_count", 0) > 0:
            issues.append({
                "severity": "严重",
                "type": "long_dialogue",
                "count": ds["over_15_count"],
                "examples": ds.get("over_15_examples", [])[:3],
            })

        # 字数
        cc = analysis.get("char_count", 0)
        if cc < 500:
            issues.append({
                "severity": "一般",
                "type": "too_short",
                "char_count": cc,
            })

        score = 100
        for issue in issues:
            if issue["severity"] == "致命":
                score -= 40
            elif issue["severity"] == "严重":
                score -= 20
            else:
                score -= 5

        return {
            "score": max(0, score),
            "issues": issues,
            "stats": analysis,
            "passed": score >= 70 and not any(i["severity"] == "致命" for i in issues),
        }


if __name__ == "__main__":
    agent = QualityAgent()
    print("QualityAgent 模块加载成功")
    print(f"工具集成: {'可用' if TOOLS_AVAILABLE else '不可用'}")
