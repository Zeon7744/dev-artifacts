#!/usr/bin/env python3
"""短剧创作 Agent 系统测试

覆盖：
1. BaseAgent 基础功能
2. 各 Agent 独立测试（mock LLM）
3. 工作流编排测试
4. 集成测试（需要 API Key）
"""

import json
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.base import BaseAgent, AgentConfig
from agents.plot_agent import PlotAgent
from agents.character_agent import CharacterAgent
from agents.dialogue_agent import DialogueAgent
from agents.script_agent import ScriptAgent
from agents.quality_agent import QualityAgent
from agents.trend_agent import TrendAgent
from agents.seo_agent import SeoAgent
from workflows.orchestrator import WorkflowOrchestrator, WorkflowResult


# ══════════════════════════════════════════════════════════════
# BaseAgent 测试
# ══════════════════════════════════════════════════════════════

class TestBaseAgent:
    """BaseAgent 基础功能测试"""

    def test_init_default(self):
        agent = BaseAgent()
        assert agent.config.model == "gpt-4o-mini"
        assert agent.config.max_retries == 3
        assert agent.config.temperature == 0.8

    def test_init_custom_config(self):
        config = AgentConfig(model="gpt-4o", temperature=0.5, max_retries=2)
        agent = BaseAgent(config)
        assert agent.config.model == "gpt-4o"
        assert agent.config.temperature == 0.5

    def test_forbidden_chars_detection(self):
        agent = BaseAgent()
        text = "他的光芒耀眼，曜日高照"
        issues = agent.check_forbidden_chars(text)
        assert len(issues) == 2
        chars = [i["char"] for i in issues]
        assert "耀" in chars
        assert "曜" in chars

    def test_forbidden_chars_clean(self):
        agent = BaseAgent()
        text = "这是一段正常的文本"
        issues = agent.check_forbidden_chars(text)
        assert len(issues) == 0

    def test_dialogue_length_check(self):
        agent = BaseAgent()
        text = '他说："你好"，她又说："这是一段超过十五个字的长对话内容测试"'
        issues = agent.check_dialogue_length(text, max_len=15)
        assert len(issues) == 1
        assert issues[0]["length"] > 15

    def test_dialogue_length_ok(self):
        agent = BaseAgent()
        text = '他说："你好啊"'
        issues = agent.check_dialogue_length(text, max_len=15)
        assert len(issues) == 0

    def test_parse_json_direct(self):
        agent = BaseAgent()
        result = agent._parse_json('{"key": "value", "num": 42}')
        assert result["key"] == "value"
        assert result["num"] == 42

    def test_parse_json_code_block(self):
        agent = BaseAgent()
        text = '这是一些文字\n```json\n{"name": "test"}\n```\n后续文字'
        result = agent._parse_json(text)
        assert result["name"] == "test"

    def test_parse_json_embedded(self):
        agent = BaseAgent()
        text = '前面文字 {"data": [1,2,3]} 后面文字'
        result = agent._parse_json(text)
        assert result["data"] == [1, 2, 3]

    def test_parse_json_failure(self):
        agent = BaseAgent()
        with pytest.raises(ValueError, match="无法从 LLM 输出中解析 JSON"):
            agent._parse_json("这不是 JSON")

    def test_logging(self):
        agent = BaseAgent()
        agent._log("test message 1")
        agent._log("test message 2")
        logs = agent.get_logs()
        assert len(logs) == 2
        assert "test message 1" in logs

        agent.clear_logs()
        assert len(agent.get_logs()) == 0


# ══════════════════════════════════════════════════════════════
# Agent 独立测试（Mock LLM）
# ══════════════════════════════════════════════════════════════

def _mock_llm_json_response(data):
    """创建 mock LLM JSON 响应"""
    return json.dumps(data, ensure_ascii=False)


class TestPlotAgent:
    """PlotAgent 测试"""

    def test_init(self):
        agent = PlotAgent()
        assert agent.name == "PlotAgent"

    @patch.object(PlotAgent, 'call_llm_json')
    def test_generate_plot(self, mock_llm):
        mock_llm.return_value = {
            "title": "逆袭人生",
            "genre": "都市逆袭",
            "logline": "他失去一切后以助理身份归来",
            "total_episodes": 3,
            "episodes": [
                {
                    "episode": 1,
                    "title": "归来",
                    "summary": "主角回到城市",
                    "shuang_points": [
                        {"type": "打脸", "description": "打脸前台"},
                        {"type": "反转", "description": "身份暗示"},
                        {"type": "危机", "description": "被刁难"},
                    ],
                    "tiandian": [{"type": "心动", "description": "偶遇前妻"}],
                },
                {
                    "episode": 2,
                    "title": "试探",
                    "summary": "暗中调查",
                    "shuang_points": [
                        {"type": "打脸", "description": "展现能力"},
                        {"type": "反转", "description": "发现线索"},
                        {"type": "逆袭", "description": "化解危机"},
                    ],
                    "tiandian": [],
                },
                {
                    "episode": 3,
                    "title": "反击",
                    "summary": "开始复仇",
                    "shuang_points": [
                        {"type": "打脸", "description": "当众揭穿"},
                        {"type": "反转", "description": "身份揭露"},
                        {"type": "逆袭", "description": "重掌公司"},
                    ],
                    "tiandian": [{"type": "甜蜜", "description": "复合暗示"}],
                },
            ],
        }

        agent = PlotAgent()
        result = agent.generate_plot(
            novel_input="失去一切的商界传奇重新归来",
            genre="都市逆袭",
            episode_count=3,
        )

        assert result["title"] == "逆袭人生"
        assert len(result["episodes"]) == 3
        mock_llm.assert_called_once()

    @patch.object(PlotAgent, 'call_llm_json')
    def test_generate_story_arc(self, mock_llm):
        mock_llm.return_value = {
            "genre": "都市",
            "theme": "复仇",
            "three_act_structure": {
                "act1_setup": {"episodes": "1-2"},
                "act2_confrontation": {"episodes": "3-5"},
                "act3_resolution": {"episodes": "6-8"},
            },
        }
        agent = PlotAgent()
        result = agent.generate_story_arc("都市", "复仇")
        assert "three_act_structure" in result


class TestCharacterAgent:
    """CharacterAgent 测试"""

    @patch.object(CharacterAgent, 'call_llm_json')
    def test_create_characters(self, mock_llm):
        mock_llm.return_value = {
            "characters": [
                {
                    "name": "顾寒声",
                    "role_type": "protagonist",
                    "personality": "冷静果断",
                    "motivation": "复仇",
                    "catchphrase": "我回来了",
                },
                {
                    "name": "林婉清",
                    "role_type": "love_interest",
                    "personality": "坚韧善良",
                    "motivation": "守护公司",
                    "catchphrase": "我不需要帮助",
                },
            ],
        }
        agent = CharacterAgent()
        result = agent.create_characters(
            story_summary="商界传奇复仇归来",
            genre="都市逆袭",
        )
        assert len(result["characters"]) == 2
        assert result["characters"][0]["name"] == "顾寒声"

    def test_validate_characters_catches_issues(self):
        agent = CharacterAgent()
        result = {
            "characters": [
                {"name": "测试角色", "role_type": "protagonist", "personality": "", "motivation": ""},
            ]
        }
        validated = agent._validate_characters(result)
        # 应该有缺少字段的警告（在日志中）
        logs = agent.get_logs()
        assert any("缺少" in log for log in logs)


class TestDialogueAgent:
    """DialogueAgent 测试"""

    @patch.object(DialogueAgent, 'call_llm_json')
    def test_generate_dialogue(self, mock_llm):
        mock_llm.return_value = {
            "scene_id": "s1",
            "location": "公司大堂",
            "dialogue_lines": [
                {"character": "主角", "emotion": "冷淡", "dialogue": "我来了"},
                {"character": "前台", "emotion": "轻蔑", "dialogue": "你也配？"},
                {"character": "主角", "emotion": "冷笑", "dialogue": "看着。"},
            ],
        }
        agent = DialogueAgent()
        result = agent.generate_dialogue(
            scene={"location": "公司大堂", "description": "主角第一天上班"},
            characters=[
                {"name": "主角", "personality": "冷静", "speech_style": "冷淡简洁"},
            ],
        )
        assert len(result["dialogue_lines"]) == 3

    def test_enforce_dialogue_limits(self):
        agent = DialogueAgent()
        result = {
            "dialogue_lines": [
                {"dialogue": "你好"},  # 短对话，OK
                {"dialogue": "这是一段超过十五个字的非常非常长的对话内容"},  # 超长
            ]
        }
        fixed = agent._enforce_dialogue_limits(result, max_len=15)
        assert len(fixed["dialogue_lines"][1]["dialogue"]) <= 15


class TestScriptAgent:
    """ScriptAgent 测试"""

    def test_normalize_format(self):
        agent = ScriptAgent()
        content = '# 测试剧\n# 第1集：归来\n"你好"\n'
        normalized = agent.normalize_format(content)
        assert "## 第1集：归来" in normalized

    def test_check_format_quality(self):
        agent = ScriptAgent()
        text = """## 第1集：归来

"你好"

第1集完"""
        result = agent._check_format_quality(text)
        assert result["episode_titles_found"] == 1
        assert result["endings_found"] == 1
        assert result["passed"]

    def test_check_format_quality_missing_elements(self):
        agent = ScriptAgent()
        text = "只有一些文字，没有格式"
        result = agent._check_format_quality(text)
        assert result["passed"] is False
        assert len(result["issues"]) > 0


class TestQualityAgent:
    """QualityAgent 测试"""

    def test_quick_check_good(self):
        agent = QualityAgent()
        script = '## 第1集：归来\n\n"你好"\n"我回来了"\n\n第1集完\n'
        result = agent.quick_check(script)
        assert result["passed"]
        assert result["score"] >= 70

    def test_quick_check_forbidden_chars(self):
        agent = QualityAgent()
        script = '## 第1集：光耀\n\n"耀眼的光芒"\n\n第1集完\n'
        result = agent.quick_check(script)
        assert not result["passed"]
        assert any(i["type"] == "forbidden_chars" for i in result["issues"])

    def test_quick_check_long_dialogues(self):
        agent = QualityAgent()
        script = '## 第1集\n\n"这是一段超过十五个字的长对话内容测试"\n\n第1集完\n'
        result = agent.quick_check(script)
        assert any(i["type"] == "long_dialogue" for i in result["issues"])

    def test_analyze_dialogues(self):
        agent = QualityAgent()
        content = '他说："你好"，她又说："这是一段超过十五个字的长对话内容测试！"'
        stats = agent._analyze_dialogues(content)
        assert stats["total"] == 2
        assert stats["over_15_count"] == 1


class TestTrendAgent:
    """TrendAgent 测试"""

    @patch.object(TrendAgent, 'call_llm_json')
    def test_analyze_trends(self, mock_llm):
        mock_llm.return_value = {
            "platform": "红果短剧",
            "genre": "都市甜宠",
            "hot_elements": {
                "popular_themes": ["总裁", "替嫁"],
            },
            "audience_profile": {"primary_age": "18-35"},
        }
        agent = TrendAgent()
        result = agent.analyze_trends("红果短剧", "都市甜宠")
        assert "hot_elements" in result
        assert result["platform"] == "红果短剧"


class TestSeoAgent:
    """SeoAgent 测试"""

    @patch.object(SeoAgent, 'call_llm_json')
    def test_generate_titles(self, mock_llm):
        mock_llm.return_value = {
            "titles": [
                {"title": "总裁的隐婚助理", "type": "身份", "ctr_score": 8},
                {"title": "离婚后他逆袭归来", "type": "反转", "ctr_score": 9},
            ],
            "best_pick": "离婚后他逆袭归来",
        }
        agent = SeoAgent()
        result = agent.generate_titles(
            story_summary="商界传奇复仇归来",
            genre="都市逆袭",
        )
        assert len(result["titles"]) == 2
        assert result["best_pick"] == "离婚后他逆袭归来"


# ══════════════════════════════════════════════════════════════
# 工作流测试
# ══════════════════════════════════════════════════════════════

class TestWorkflowOrchestrator:
    """工作流编排器测试"""

    def test_init(self):
        orch = WorkflowOrchestrator()
        assert "PlotAgent" in orch._agents
        assert "CharacterAgent" in orch._agents
        assert len(orch._agents) == 7

    def test_get_agent(self):
        orch = WorkflowOrchestrator()
        agent = orch.get_agent("PlotAgent")
        assert isinstance(agent, PlotAgent)

    def test_get_agent_invalid(self):
        orch = WorkflowOrchestrator()
        with pytest.raises(ValueError, match="未知 Agent"):
            orch.get_agent("NonExistentAgent")

    def test_run_step_invalid(self):
        orch = WorkflowOrchestrator()
        with pytest.raises(ValueError, match="未知步骤"):
            orch.run_step("nonexistent", {})


class TestWorkflowResult:
    """WorkflowResult 测试"""

    def test_to_dict(self):
        result = WorkflowResult(
            workflow_id="test_001",
            status="success",
            started_at="2026-01-01T00:00:00",
            finished_at="2026-01-01T00:01:00",
        )
        d = result.to_dict()
        assert d["workflow_id"] == "test_001"
        assert d["status"] == "success"


# ══════════════════════════════════════════════════════════════
# 集成测试（需要 API Key）
# ══════════════════════════════════════════════════════════════

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="需要 OPENAI_API_KEY 环境变量"
)
class TestIntegration:
    """集成测试（真实调用 LLM）"""

    def test_plot_agent_real(self):
        agent = PlotAgent()
        result = agent.generate_plot(
            novel_input="一个失去记忆的战神回归都市",
            genre="都市逆袭",
            episode_count=3,
        )
        assert "episodes" in result
        assert len(result["episodes"]) > 0

    def test_quality_check_real(self):
        agent = QualityAgent()
        script = """## 第1集：归来

（主角走入公司）

"我回来了。"

（看向总裁办公室）

"这次不一样了。"

第1集完
"""
        result = agent.quick_check(script)
        assert result["passed"]


# ══════════════════════════════════════════════════════════════
# 运行
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
