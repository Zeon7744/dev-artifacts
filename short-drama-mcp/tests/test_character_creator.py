#!/usr/bin/env python3
"""test_character_creator.py - 角色设定生成器 单元测试

覆盖：create_character_profile、create_character_set、
      extract_keywords、determine_roles、generate_name、
      generate_relationships
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.character_creator import (
    create_character_profile,
    create_character_set,
    extract_keywords,
    determine_roles,
    generate_name,
    generate_relationships,
    CharacterProfile,
)


# ═══════════════════════════════════════════════════════════════
# create_character_profile 测试
# ═══════════════════════════════════════════════════════════════
class TestCreateCharacterProfile:
    def test_returns_dict(self):
        result = create_character_profile("顾寒声", "protagonist", "玄幻重生")
        assert isinstance(result, dict)

    def test_required_fields_present(self):
        result = create_character_profile("测试名", "protagonist", "玄幻重生")
        required = {"name", "identity", "personality", "appearance",
                    "motivation", "secret", "relationships", "catchphrase", "arc"}
        assert required.issubset(result.keys())

    def test_name_appears_in_result(self):
        result = create_character_profile("顾寒声", "protagonist")
        assert result["name"] == "顾寒声"

    def test_role_type_affects_personality(self):
        p = create_character_profile("A", "protagonist")["personality"]
        a = create_character_profile("B", "antagonist")["personality"]
        s = create_character_profile("C", "support")["personality"]
        # 三种类型 personality 应各不相同
        assert len({p, a, s}) == 3

    def test_genre_modifies_motivation(self):
        urban = create_character_profile("X", "protagonist", "都市异能")["motivation"]
        xuanhuan = create_character_profile("Y", "protagonist", "玄幻重生")["motivation"]
        assert "复仇" in xuanhuan or "遗憾" in xuanhuan
        assert "保护" in urban or "命运" in urban

    def test_base_profile_overrides(self):
        base = {"personality": "自定义性格", "motivation": "自定义动机"}
        result = create_character_profile("Z", base_profile=base)
        assert result["personality"] == "自定义性格"
        assert result["motivation"] == "自定义动机"

    def test_unknown_role_type_defaults_to_protagonist(self):
        result = create_character_profile("Unknown", "unknown_role")
        assert result["name"] == "Unknown"
        # 不应抛出异常

    def test_relationships_is_dict(self):
        result = create_character_profile("Test", "protagonist")
        assert isinstance(result["relationships"], dict)

    def test_arc_contains_text(self):
        result = create_character_profile("Test", "protagonist")
        assert isinstance(result["arc"], str) and len(result["arc"]) > 0


# ═══════════════════════════════════════════════════════════════
# generate_relationships 测试
# ═══════════════════════════════════════════════════════════════
class TestGenerateRelationships:
    def test_all_role_keys_present(self):
        rels = generate_relationships("Hero", "protagonist", "玄幻重生")
        expected = {"father", "mother", "rival", "ally", "love_interest"}
        assert expected.issubset(rels.keys())

    def test_protagonist_has_mentor(self):
        rels = generate_relationships("Hero", "protagonist", "玄幻重生")
        assert "mentor" in rels

    def test_antagonist_has_master(self):
        rels = generate_relationships("Villain", "antagonist", "都市")
        assert "master" in rels
        assert "subordinate" in rels

    def test_support_role(self):
        rels = generate_relationships("Sidekick", "support", "都市")
        assert "father" in rels


# ═══════════════════════════════════════════════════════════════
# extract_keywords 测试
# ═══════════════════════════════════════════════════════════════
class TestExtractKeywords:
    def test_returns_dict(self):
        result = extract_keywords("重生之战神归来")
        assert isinstance(result, dict)

    def test_detects_xuanhuan(self):
        result = extract_keywords("重生归来，修为无敌的战神")
        assert result["genre"] == "玄幻"

    def test_detects_dushi(self):
        result = extract_keywords("总裁的豪门恩怨，秘书的隐秘身世")
        assert result["genre"] == "都市"

    def test_detects_yineng(self):
        result = extract_keywords("异能者隐藏身份，医术惊人")
        assert result["genre"] == "异能"

    def test_detects_xuan疑(self):
        result = extract_keywords("凶手是谁？背后阴谋渐渐浮出水面")
        assert result["genre"] == "悬疑"

    def test_fallback_to_dushi(self):
        result = extract_keywords("一个普通人的故事")
        assert result["genre"] == "都市"


# ═══════════════════════════════════════════════════════════════
# determine_roles 测试
# ═══════════════════════════════════════════════════════════════
class TestDetermineRoles:
    def test_minimum_two_roles(self):
        roles = determine_roles({}, 2)
        assert len(roles) == 2
        assert "protagonist" in roles
        assert "antagonist" in roles

    def test_expands_to_count(self):
        roles = determine_roles({}, 5)
        assert len(roles) == 5
        assert roles[0] == "protagonist"
        assert roles[1] == "antagonist"

    def test_first_is_protagonist(self):
        roles = determine_roles({}, 10)
        assert roles[0] == "protagonist"

    def test_second_is_antagonist(self):
        roles = determine_roles({}, 10)
        assert roles[1] == "antagonist"


# ═══════════════════════════════════════════════════════════════
# generate_name 测试
# ═══════════════════════════════════════════════════════════════
class TestGenerateName:
    def test_protagonist_names(self):
        name = generate_name(0, "protagonist", {})
        assert name in ["顾寒声", "萧墨白", "陆沉渊", "沈暮寒", "霍凛"]

    def test_antagonist_names(self):
        name = generate_name(0, "antagonist", {})
        assert name in ["赵天霸", "王富贵", "李势利", "张傲天", "孙少峰"]

    def test_support_names(self):
        name = generate_name(0, "support", {})
        assert name in ["陈小萌", "李大壮", "王小丫", "刘小萌", "周小芸"]

    def test_cycling_on_large_index(self):
        n1 = generate_name(0, "protagonist", {})
        n2 = generate_name(5, "protagonist", {})
        assert n1 == n2  # 循环取名字


# ═══════════════════════════════════════════════════════════════
# create_character_set 测试
# ═══════════════════════════════════════════════════════════════
class TestCreateCharacterSet:
    def test_returns_list(self):
        result = create_character_set("重生复仇故事", character_count=3)
        assert isinstance(result, list)

    def test_count_matches_request(self):
        chars = create_character_set("都市总裁复仇", character_count=5)
        assert len(chars) == 5

    def test_each_has_required_keys(self):
        chars = create_character_set("战神重生", character_count=3)
        required = {"name", "identity", "personality", "appearance",
                    "motivation", "secret", "relationships", "catchphrase", "arc"}
        for c in chars:
            assert required.issubset(c.keys())

    def test_first_is_protagonist(self):
        chars = create_character_set("故事梗概", character_count=4)
        assert chars[0]["name"] in ["顾寒声", "萧墨白", "陆沉渊", "沈暮寒", "霍凛"]

    def test_second_is_antagonist(self):
        chars = create_character_set("故事梗概", character_count=4)
        assert chars[1]["name"] in ["赵天霸", "王富贵", "李势利", "张傲天", "孙少峰"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
