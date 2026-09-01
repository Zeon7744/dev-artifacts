#!/usr/bin/env python3
"""
集纲生成器 - 根据小说内容生成短剧集纲大纲
"""

import re
import json
from typing import List, Dict
from pathlib import Path


def extract_novel_structure(content: str) -> Dict:
    """提取小说结构信息"""
    # 提取标题
    title_match = re.search(r'#\s*《(.+?)》', content)
    title = title_match.group(1) if title_match else Path(content).stem if hasattr(content, 'stem') else '未命名'
    
    # 提取章节
    chapters = re.findall(r'第[一二三四五六七八九十百千\d]+[章回节]', content)
    chapter_count = len(chapters)
    
    # 估算总字数
    total_words = len(re.sub(r'\s+', '', content))
    
    return {
        "title": title,
        "chapter_count": chapter_count,
        "total_words": total_words,
        "avg_words_per_chapter": total_words // chapter_count if chapter_count > 0 else 0
    }


def generate_episode_titles(genre: str, total_episodes: int) -> List[str]:
    """根据题材生成集标题模板"""
    templates = {
        "玄幻重生": ["重生归来", "觉醒时刻", "第一剑", "复仇之路", "巅峰之战", "真相大白", "最终决战", "新的开始"],
        "都市异能": ["意外邂逅", "身份暴露", "危机降临", "能力觉醒", "反击开始", "真相揭露", "终极对决", "尘埃落定"],
        "都市甜宠": ["相遇", "心动", "暧昧", "表白", "波折", "误会", "和解", "结局"],
        "悬疑推理": ["案发现场", "线索浮现", "嫌疑人", "反转", "真相", "真相大白", "落幕"],
        "豪门恩怨": ["初遇", "身份", "冲突", "秘密", "真相", "报复", "和解", "结局"]
    }
    
    return templates.get(genre, templates["都市异能"])


def analyze_story_beats(content: str) -> List[Dict]:
    """分析故事关键节点"""
    beats = []
    
    # 寻找开头
    opening_patterns = ["开篇", "第一章", "第一集", "故事的开始", "那天"]
    for pattern in opening_patterns:
        if pattern in content[:500]:
            beats.append({"type": "opening", "position": "start", "keyword": pattern})
            break
    
    # 寻找冲突
    conflict_keywords = ["冲突", "争吵", "对峙", "矛盾", "对抗", "决斗", "战斗"]
    for kw in conflict_keywords:
        matches = [(m.start(), kw) for m in re.finditer(kw, content)]
        if matches:
            beats.append({"type": "conflict", "keyword": kw, "count": len(matches)})
    
    # 寻找高潮
    climax_keywords = ["高潮", "决战", "最终", "终极", "真相大白", "反转"]
    for kw in climax_keywords:
        if kw in content:
            beats.append({"type": "climax", "keyword": kw})
    
    # 寻找结局
    ending_keywords = ["结局", "完", "终章", "落幕", "尘埃落定"]
    for kw in ending_keywords:
        if kw in content[-500:]:
            beats.append({"type": "ending", "keyword": kw})
            break
    
    return beats


def generate_episode_outline(novel_content: str, total_episodes: int = 10, genre: str = "玄幻重生") -> Dict:
    """根据小说生成集纲大纲
    
    Args:
        novel_content: 小说原文内容（可以是文件路径或文本内容）
        total_episodes: 目标集数
        genre: 题材类型
    
    Returns:
        JSON 格式的集纲大纲
    """
    try:
        # 判断是否是文件路径
        if novel_content.endswith('.md') or novel_content.endswith('.txt'):
            with open(novel_content, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = novel_content
        
        # 提取小说结构
        structure = extract_novel_structure(content)
        
        # 分析故事节奏
        beats = analyze_story_beats(content)
        
        # 生成集标题
        episode_titles = generate_episode_titles(genre, total_episodes)
        
        # 规划集纲
        episodes = []
        words_per_episode = structure['total_words'] // total_episodes
        
        # 简单的节拍分配
        beat_positions = [
            {"type": "opening", "episodes": [0]},
            {"type": "conflict", "episodes": [2, 4, 6]},
            {"type": "climax", "episodes": [total_episodes // 2, total_episodes - 2]},
            {"type": "ending", "episodes": [total_episodes - 1]}
        ]
        
        for i in range(total_episodes):
            ep_beats = []
            for beat_cfg in beat_positions:
                if i in beat_cfg['episodes']:
                    ep_beats.append(beat_cfg['type'])
            
            episodes.append({
                "episode": i + 1,
                "title": episode_titles[i % len(episode_titles)] if i < len(episode_titles) else f"第{i+1}集",
                "estimated_words": words_per_episode,
                "key_beats": ep_beats,
                "suggestions": _generate_suggestions(i + 1, ep_beats, genre)
            })
        
        return {
            "novel_title": structure['title'],
            "genre": genre,
            "total_episodes": total_episodes,
            "total_words": structure['total_words'],
            "avg_words_per_episode": words_per_episode,
            "episodes": episodes,
            "created_at": __import__('datetime').datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}


def _generate_suggestions(episode_num: int, beats: List[str], genre: str) -> List[str]:
    """生成单集创作建议"""
    suggestions = []
    
    if 'opening' in beats:
        suggestions.append("开篇要吸引眼球，快速建立主角形象和世界观")
    
    if 'conflict' in beats:
        suggestions.append("设置冲突点，制造悬念和紧张感")
    
    if 'climax' in beats:
        suggestions.append("安排高潮情节，集中释放爽点")
    
    if 'ending' in beats:
        suggestions.append("收尾要有力，留下回味空间")
    
    if episode_num == 1:
        suggestions.append("第一集至关重要，建议包含：主角介绍+初始冲突+悬念钩子")
    
    if episode_num == 10:
        suggestions.append("最终集建议：总高潮+伏笔回收+开放式结局")
    
    return suggestions


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        episodes = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        genre = sys.argv[3] if len(sys.argv) > 3 else "玄幻重生"
        result = generate_episode_outline(filepath, episodes, genre)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法: python outline_generator.py <novel_file> [episodes] [genre]")
