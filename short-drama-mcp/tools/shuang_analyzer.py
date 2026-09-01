#!/usr/bin/env python3
"""
爽点分析器 - 统计短剧剧本中的爽点密度和分布
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple


# 爽点关键词分类
SHUANG_PATTERNS = {
    "打脸反转": [
        "冷笑", "怒", "杀", "废", "滚", "找死", "放肆", "你敢", "呵", "竟敢", 
        "居然", "废物", "配", "也不配", "区区", "卑微", "蝼蚁", "颤抖", "跪下",
        "道歉", "求饶", "后悔", "震惊", "不可能", "这怎么可能", "瞳孔收缩"
    ],
    "实力展现": [
        "一剑", "一击", "轰", "震", "崩", "碎", "灭", "秒杀", "碾压", "碾压",
        "无敌", "恐怖", "强悍", "强大", "威压", "气势", "爆发", "觉醒", "突破"
    ],
    "危机解除": [
        "救", "护", "挡", "护住", "安然", "无恙", "化险为夷", "转危为安",
        "化解", "平息", "镇压", "终结", "落幕", "尘埃落定"
    ],
    "身份揭露": [
        "原来", "竟然是", "居然是", "竟是", "身份", "真实", "隐藏", "暴露",
        "揭露", "公布", "真相", "揭晓", "认出来", "认出", "震惊全场"
    ],
    "逆袭翻盘": [
        "逆袭", "翻盘", "反转", "绝地", "反击", "反杀", "反攻", "逆袭",
        "绝境", "绝路", "柳暗花明", "峰回路转", "东山再起"
    ],
    "情感满足": [
        "心动", "温柔", "宠", "宠溺", "偏爱", "独宠", "心疼", "眷恋",
        "缱绻", "深情", "执着", "守护", "陪伴", "不离不弃"
    ]
}

# 甜点关键词
TIANDIAN_PATTERNS = [
    "笑", "甜", "暖", "温馨", "默契", "对视", "牵手", "拥抱", "依靠",
    "羞涩", "脸红", "心跳", "柔情", "宠溺", "偏爱", "专属"
]


def analyze_episode(content: str, ep_num: int) -> Dict:
    """分析单集内容的爽点和甜点"""
    shuang_count = 0
    shuang_types = {}
    tiandian_count = 0
    
    for category, keywords in SHUANG_PATTERNS.items():
        count = 0
        for kw in keywords:
            count += len(re.findall(re.escape(kw), content))
        if count > 0:
            shuang_types[category] = count
            shuang_count += count
    
    for kw in TIANDIAN_PATTERNS:
        tiandian_count += len(re.findall(kw, content))
    
    # 计算字数
    words = len(re.sub(r'\s+', '', content))
    
    return {
        "episode": ep_num,
        "words": words,
        "shuang_count": shuang_count,
        "shuang_types": shuang_types,
        "tiandian_count": tiandian_count,
        "meets_minimum": shuang_count >= 3,
        "meets_word_count": words >= 500
    }


def parse_episodes(content: str) -> List[Tuple[int, str]]:
    """解析剧本中的各集内容"""
    episodes = []
    
    # 匹配第X集：集名 的格式
    pattern = r'##\s*第(\d+)集[：:]\s*(.+?)(?=\n##\s*第|\Z)'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    for i, match in enumerate(matches):
        ep_num = int(match.group(1))
        # 获取该集的内容（到下一集或结尾）
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        ep_content = content[start:end].strip()
        episodes.append((ep_num, ep_content))
    
    return episodes


def count_shuang_points(filepath: str) -> Dict:
    """统计剧本的爽点密度"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        name = Path(filepath).stem
        
        # 解析各集
        episodes = parse_episodes(content)
        
        if not episodes:
            # 尝试按 ## 分隔
            sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
            episodes = [(i+1, s) for i, s in enumerate(sections[1:]) if s.strip()]
        
        # 分析每集
        episode_results = []
        total_shuang = 0
        total_tiandian = 0
        total_words = 0
        
        for ep_num, ep_content in episodes:
            result = analyze_episode(ep_content, ep_num)
            episode_results.append(result)
            total_shuang += result['shuang_count']
            total_tiandian += result['tiandian_count']
            total_words += result['words']
        
        # 计算密度
        ep_count = len(episode_results)
        avg_shuang = total_shuang / ep_count if ep_count > 0 else 0
        avg_tiandian = total_tiandian / ep_count if ep_count > 0 else 0
        
        # 总体评估
        all_meet_minimum = all(e['meets_minimum'] for e in episode_results)
        all_meet_words = all(e['meets_word_count'] for e in episode_results)
        
        return {
            "file": name,
            "total_episodes": ep_count,
            "total_shuang_points": total_shuang,
            "total_tiandian": total_tiandian,
            "total_words": total_words,
            "avg_shuang_per_episode": round(avg_shuang, 2),
            "avg_tiandian_per_episode": round(avg_tiandian, 2),
            "meets_platform_standard": all_meet_minimum and all_meet_words,
            "episodes": episode_results,
            "recommendation": (
                "✅ 符合平台标准（≥3爽点/集，≥500字/集）" 
                if all_meet_minimum and all_meet_words 
                else "⚠️ 需优化：部分集数未达到标准"
            )
        }
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == '__main__':
    if len(sys.argv) > 1:
        result = count_shuang_points(sys.argv[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法: python shuang_analyzer.py <filepath>")
