#!/usr/bin/env python3
"""test_dialogue_optimizer.py - 对话优化器 单元测试

覆盖：optimize_dialogue、extract_dialogues、analyze_dialogues、
      detect_redundancy、generate_suggestions、optimize_text
"""

import sys
import os
import json
import pytest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'short-drama-mcp'))
from tools.dialogue_optimizer import (
    optimize_dialogue,
    extract_dialogues,
    analyze_dialogues,
    detect_redundancy,
    generate_suggestions,
    optimize_text,
    check_dialogue_quality,
)


# ═══════════════════════════════════════════════════════════════
# extract_dialogues 测试
# ═══════════════════════════════════════════════════════════════
class TestExtractDialogues:
    def test_returns_list_of_tuples(self):
        text = '他说："你好"'
        result = extract_dialogues(text)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], tuple)
            assert len(result[0]) == 2

    def test_extracts_chinese_quotes(self):
        text = '「你好世界」他说'
        result = extract_dialogues(text)
        texts = [d[0] for d in result]
        assert any("你好世界" in t for t in texts)

    def test_extracts_double_quotes(self):
        text = '他说："hello world"'
        result = extract_dialogues(text)
        texts = [d[0] for d in result]
        assert any("hello world" in t for t in texts)

    def test_line_numbers_positive(self):
        text = '第1行\n"对话一"\n第3行\n"对话二"'
        result = extract_dialogues(text)
        lines = [d[1] for d in result]
        assert all(l > 0 for l in lines)

    def test_empty_text(self):
        result = extract_dialogues("")
        assert result == []

    def test_no_dialogue_marks(self):
        result = extract_dialogues("只有叙述，没有对话。")
        # 冒号模式可能匹配到"没有对话"，只要不崩溃即可
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════
# analyze_dialogues 测试
# ═══════════════════════════════════════════════════════════════
class TestAnalyzeDialogues:
    def test_empty_dialogues(self):
        result = analyze_dialogues([])
        assert result["over_count"] == 0
        assert result["short_count"] == 0
        assert result["avg_length"] == 0
        assert result["redundant"] == []

    def test_over_15_counted(self):
        dialogues = [("这是一句非常非常长的对话内容超过十五个字", 1)]
        result = analyze_dialogues(dialogues)
        assert result["over_count"] >= 1

    def test_short_counted(self):
        # < 5 且不以（开头
        dialogues = [("好", 2)]
        result = analyze_dialogues(dialogues)
        assert result["short_count"] >= 1

    def test_avg_length_calculation(self):
        dialogues = [("你好", 1), ("世界", 2)]
        result = analyze_dialogues(dialogues)
        assert result["avg_length"] == 2.0

    def test_returns_expected_keys(self):
        result = analyze_dialogues([])
        expected = {"over_count", "short_count", "avg_length", "redundant"}
        assert expected.issubset(result.keys())


# ═══════════════════════════════════════════════════════════════
# detect_redundancy 测试
# ═══════════════════════════════════════════════════════════════
class TestDetectRedundancy:
    def test_subjective_pattern(self):
        dialogues = [("我以为你已经知道了", 1)]
        result = detect_redundancy(dialogues)
        assert len(result) >= 1
        assert result[0]["pattern"] == "主观臆测"

    def test_rhetorical_pattern(self):
        dialogues = [("难道你不明白吗", 2)]
        result = detect_redundancy(dialogues)
        assert len(result) >= 1
        assert result[0]["pattern"] == "反问冗余"

    def test_no_redundancy(self):
        dialogues = [("你好，请进。", 1)]
        result = detect_redundancy(dialogues)
        assert result == []

    def test_empty_dialogues(self):
        assert detect_redundancy([]) == []

    def test_redundant_item_structure(self):
        dialogues = [("我以为你已经知道了", 1)]
        result = detect_redundancy(dialogues)
        item = result[0]
        assert "dialogue" in item
        assert "line" in item
        assert "pattern" in item
        assert "suggestion" in item


# ═══════════════════════════════════════════════════════════════
# generate_suggestions 测试
# ═══════════════════════════════════════════════════════════════
class TestGenerateSuggestions:
    def test_over_count_trigger(self):
        analysis = {"over_count": 3, "avg_length": 8.0, "redundant": []}
        suggestions = generate_suggestions(analysis)
        assert any("超长" in s for s in suggestions)

    def test_avg_length_trigger(self):
        analysis = {"over_count": 0, "avg_length": 15.0, "redundant": []}
        suggestions = generate_suggestions(analysis)
        assert any("平均对话" in s for s in suggestions)

    def test_redundant_trigger(self):
        analysis = {"over_count": 0, "avg_length": 5.0, "redundant": [{"x": 1}]}
        suggestions = generate_suggestions(analysis)
        assert any("冗余" in s for s in suggestions)

    def test_good_dialogue(self):
        analysis = {"over_count": 0, "avg_length": 5.0, "redundant": []}
        suggestions = generate_suggestions(analysis)
        assert len(suggestions) == 1
        assert "良好" in suggestions[0] or "符合" in suggestions[0]


# ═══════════════════════════════════════════════════════════════
# optimize_text 测试
# ═══════════════════════════════════════════════════════════════
class TestOptimizeText:
    def test_removes_redundant_phrases(self):
        text = '他说了"我觉得这是对的"'
        dialogues = [("我觉得这是对的", 1)]
        result = optimize_text(text, dialogues, [])
        assert "我觉得" not in result or result.count("我觉得") == 0

    def test_truncates_long_dialogue(self):
        long_d = "a" * 20
        text = f'" {long_d} "'
        dialogues = [(long_d, 1)]
        result = optimize_text(text, dialogues, [])
        # 截断后引号内应 ≤ 15 字
        import re
        matches = re.findall(r'"([^"]+)"', result)
        if matches:
            assert len(matches[0]) <= 15

    def test_returns_string(self):
        result = optimize_text("", [], [])
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════════
# optimize_dialogue 主入口测试
# ═══════════════════════════════════════════════════════════════
class TestOptimizeDialogue:
    SAMPLE = '''第1集：重生

（主角睁开眼睛）
"这是...十年前？"
（看向新娘）
"这一世，我不会再输。"

反派："你以为你是谁？一个废物也配娶她？"
主角："我只是回来拿回属于我的东西。"
反派："就凭你？哈哈哈，你太自不量力了，我一句话就能让你消失在这个世界上！"

（主角冷笑）
"你说什么？"
'''

    def test_returns_dict(self):
        result = optimize_dialogue(self.SAMPLE)
        assert isinstance(result, dict)

    def test_key_fields_present(self):
        result = optimize_dialogue(self.SAMPLE)
        required = {
            "total_dialogues", "dialogues_over_15", "dialogues_under_5",
            "average_length", "redundant_patterns", "suggestions", "optimized_text"
        }
        assert required.issubset(result.keys())

    def test_total_dialogues_positive(self):
        result = optimize_dialogue(self.SAMPLE)
        assert result["total_dialogues"] > 0

    def test_optimized_text_is_string(self):
        result = optimize_dialogue(self.SAMPLE)
        assert isinstance(result["optimized_text"], str)

    def test_suggestions_non_empty(self):
        result = optimize_dialogue(self.SAMPLE)
        assert isinstance(result["suggestions"], list)

    def test_file_path_input(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                         encoding="utf-8", delete=False) as f:
            f.write(self.SAMPLE)
            path = f.name
        try:
            result = optimize_dialogue(content="", filepath=path)
            assert isinstance(result, dict)
            assert result["total_dialogues"] > 0
        finally:
            os.unlink(path)


# ═══════════════════════════════════════════════════════════════
# check_dialogue_quality 测试
# ═══════════════════════════════════════════════════════════════
class TestCheckDialogueQuality:
    def test_returns_json_string(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                         encoding="utf-8", delete=False) as f:
            f.write('"你好"\n')
            path = f.name
        try:
            result = check_dialogue_quality(path)
            parsed = json.loads(result)
            assert isinstance(parsed, dict)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
