#!/usr/bin/env python3
"""角色设定生成器
生成短剧角色卡片
"""

import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class CharacterProfile:
    """角色档案"""
    name: str
    identity: str  # 身份/职业
    personality: str  # 性格特点
    appearance: str  # 外貌特征
    motivation: str  # 动机/目标
    secret: str  # 秘密/隐藏身份
    relationships: Dict[str, str]  # 人物关系
    catchphrase: str  # 标志性台词
    arc: str  # 角色成长弧光


def create_character_profile(
    name: str,
    role_type: str = "protagonist",
    genre: str = "玄幻重生",
    base_profile: Optional[Dict] = None
) -> Dict:
    """
    生成角色设定
    
    Args:
        name: 角色姓名
        role_type: 角色类型 (protagonist/antagonist/support)
        genre: 题材类型
        base_profile: 基础设定（可选）
    
    Returns:
        JSON格式的角色档案
    """
    
    # 默认角色模板
    templates = {
        "protagonist": {
            "identity": "隐藏身份的强者",
            "personality": "冷静、果断、护短",
            "appearance": "外表普通，眼神锐利",
            "motivation": "复仇/守护/找回身份",
            "secret": "真实身份远超反派想象",
            "catchphrase": "你以为你是谁？",
            "arc": "从隐忍到爆发"
        },
        "antagonist": {
            "identity": "势利眼的高位者",
            "personality": "傲慢、刻薄、欺软怕硬",
            "appearance": "精致打扮，眼神轻蔑",
            "motivation": "维护地位/争夺利益",
            "secret": "有自己的难处或弱点",
            "catchphrase": "你配吗？",
            "arc": "从嚣张到被打脸"
        },
        "support": {
            "identity": "关键辅助角色",
            "personality": "忠诚、机智、幽默",
            "appearance": "朴实或可爱",
            "motivation": "帮助主角/完成使命",
            "secret": "可能有隐藏能力",
            "catchphrase": "放心，有我在",
            "arc": "从平凡到关键时刻挺身"
        }
    }
    
    # 根据题材调整
    genre_modifiers = {
        "玄幻重生": {
            "identity": "重生强者/隐藏修为",
            "motivation": "弥补前世遗憾/复仇"
        },
        "都市异能": {
            "identity": "异能者/隐形富豪",
            "motivation": "保护家人/掌控命运"
        },
        "豪门恩怨": {
            "identity": "被逐 heirs/替身",
            "motivation": "证明价值/夺回家产"
        }
    }
    
    # 合并设定
    profile = templates.get(role_type, templates["protagonist"]).copy()
    if genre in genre_modifiers:
        profile.update(genre_modifiers[genre])
    if base_profile:
        profile.update(base_profile)
    
    # 生成关系网
    relationships = generate_relationships(name, role_type, genre)
    profile["relationships"] = relationships
    
    # 创建角色对象
    char = CharacterProfile(
        name=name,
        **profile
    )
    
    return asdict(char)


def generate_relationships(
    name: str,
    role_type: str,
    genre: str
) -> Dict[str, str]:
    """生成人物关系网"""
    
    relationships = {
        "father": "神秘/缺席/或隐藏身份",
        "mother": "关爱/或有所隐瞒",
        "rival": "竞争对手/或前世仇人",
        "ally": "忠诚伙伴/或关键盟友",
        "love_interest": "命中注定/或利益关系"
    }
    
    # 根据角色类型调整
    if role_type == "protagonist":
        relationships.update({
            "mentor": "指导者/或前世记忆",
            "betrayed_by": "被信任之人背叛"
        })
    elif role_type == "antagonist":
        relationships.update({
            "master": "背后靠山",
            "subordinate": "狐假虎威的爪牙"
        })
    
    return relationships


def create_character_set(
    story_summary: str,
    character_count: int = 5
) -> List[Dict]:
    """
    为故事创建完整角色组
    
    Args:
        story_summary: 故事梗概
        character_count: 角色数量
    
    Returns:
        角色列表
    """
    # 解析故事关键词
    keywords = extract_keywords(story_summary)
    
    # 确定角色类型
    role_distribution = determine_roles(keywords, character_count)
    
    # 生成角色
    characters = []
    for i, role in enumerate(role_distribution):
        name = generate_name(i, role, keywords)
        profile = create_character_profile(
            name=name,
            role_type=role,
            genre=keywords.get("genre", "都市")
        )
        characters.append(profile)
    
    return characters


def extract_keywords(story_summary: str) -> Dict:
    """从故事梗概提取关键词"""
    keywords = {
        "genre": "都市",
        "themes": [],
        "elements": []
    }
    
    # 题材识别
    genre_keywords = {
        "玄幻": ["重生", "修为", "战神", "修仙"],
        "都市": ["总裁", "豪门", "秘书", "赘婿"],
        "异能": ["异能", "医术", "武功"],
        "悬疑": ["凶手", "真相", "阴谋"]
    }
    
    for genre, kw_list in genre_keywords.items():
        if any(kw in story_summary for kw in kw_list):
            keywords["genre"] = genre
            break
    
    return keywords


def determine_roles(keywords: Dict, count: int) -> List[str]:
    """确定角色类型分布"""
    roles = []
    
    # 固定配置
    roles.append("protagonist")
    roles.append("antagonist")
    
    # 补充辅助角色
    while len(roles) < count:
        roles.append("support")
    
    return roles[:count]


def generate_name(index: int, role: str, keywords: Dict) -> str:
    """生成角色姓名"""
    names = {
        "protagonist": ["顾寒声", "萧墨白", "陆沉渊", "沈暮寒", "霍凛"],
        "antagonist": ["赵天霸", "王富贵", "李势利", "张傲天", "孙少峰"],
        "support": ["陈小萌", "李大壮", "王小丫", "刘小萌", "周小芸"]
    }
    
    name_list = names.get(role, names["support"])
    return name_list[index % len(name_list)]


if __name__ == "__main__":
    # 测试示例
    print("=== 角色设定生成器测试 ===\n")
    
    # 单个角色
    profile = create_character_profile(
        name="顾寒声",
        role_type="protagonist",
        genre="玄幻重生"
    )
    print("【主角设定】")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # 反派角色
    antagonist = create_character_profile(
        name="赵天霸",
        role_type="antagonist",
        genre="都市"
    )
    print("【反派设定】")
    print(json.dumps(antagonist, ensure_ascii=False, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # 完整角色组
    story = "重生归来，他要复仇，揭开豪门秘密"
    characters = create_character_set(story, character_count=5)
    print("【完整角色组】")
    for i, char in enumerate(characters):
        print(f"\n角色{i+1}: {char['name']} ({char['identity']})")
