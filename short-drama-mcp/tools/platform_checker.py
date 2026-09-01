#!/usr/bin/env python3
"""
平台合规检查器 - 检查短剧是否符合红果平台投稿规范
"""

import re
import json
from pathlib import Path
from typing import Dict, List


# 红果平台投稿规范
PLATFORM_RULES = {
    "title_format": r'##\s*第\d+集[：:]\s*.+',
    "ending_format": r'第\d+集完',
    "dialogue_max_length": 15,
    "shuang_min_per_episode": 3,
    "word_min_per_episode": 500,
    "forbidden_chars": ['耀', '曜'],
    "forbidden_brackets": ['【', '】'],
    "forbidden_content": ['军事', '系统文', '迷信'],
    "required_structure": ["角色表", "集纲"]
}


def check_title_format(content: str) -> Dict:
    """检查标题格式"""
    issues = []
    matches = re.findall(r'##\s+(.+)', content, re.MULTILINE)
    
    valid_titles = []
    invalid_titles = []
    
    for title in matches:
        if re.match(r'第\d+集[：:]\s*.+', title):
            valid_titles.append(title.strip())
        elif '角色' in title or '集纲' in title:
            valid_titles.append(title.strip())
        else:
            invalid_titles.append(title.strip())
    
    if invalid_titles:
        issues.append(f"标题格式不规范: {invalid_titles[:3]}")
    
    return {
        "valid_titles": valid_titles,
        "invalid_titles": invalid_titles,
        "issues": issues,
        "passed": len(invalid_titles) == 0
    }


def check_ending_format(content: str) -> Dict:
    """检查结尾格式"""
    endings = re.findall(r'第\d+集完', content)
    return {
        "endings_found": len(endings),
        "passed": len(endings) > 0
    }


def check_dialogue_length(content: str) -> Dict:
    """检查对话长度"""
    dialogues = re.findall(r'"([^"]+)"', content)
    long_dialogues = [d for d in dialogues if len(d) > PLATFORM_RULES['dialogue_max_length']]
    
    return {
        "total_dialogues": len(dialogues),
        "long_dialogues": len(long_dialogues),
        "max_length_found": max([len(d) for d in dialogues]) if dialogues else 0,
        "passed": len(long_dialogues) == 0
    }


def check_forbidden_elements(content: str) -> Dict:
    """检查禁止元素"""
    issues = []
    
    # 检查禁止字符
    for char in PLATFORM_RULES['forbidden_chars']:
        if char in content:
            issues.append(f"包含禁止字符: '{char}'")
    
    # 检查禁止括号
    for bracket in PLATFORM_RULES['forbidden_brackets']:
        if bracket in content:
            issues.append(f"包含禁止括号: '{bracket}'")
    
    return {
        "issues": issues,
        "passed": len(issues) == 0
    }


def check_shuang_density(filepath: str) -> Dict:
    """检查爽点密度"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        from tools.shuang_analyzer import parse_episodes, analyze_episode
        episodes = parse_episodes(content)
        
        episode_checks = []
        all_pass = True
        
        for ep_num, ep_content in episodes:
            result = analyze_episode(ep_content, ep_num)
            if not result['meets_minimum'] or not result['meets_word_count']:
                all_pass = False
            episode_checks.append({
                "episode": ep_num,
                "shuang_count": result['shuang_count'],
                "word_count": result['words'],
                "pass": result['meets_minimum'] and result['meets_word_count']
            })
        
        return {
            "episodes": episode_checks,
            "all_pass": all_pass
        }
    except Exception as e:
        return {"error": str(e), "all_pass": False}


def check_platform_compliance(filepath: str) -> Dict:
    """全面检查平台合规性"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        name = Path(filepath).stem
        
        # 执行各项检查
        title_check = check_title_format(content)
        ending_check = check_ending_format(content)
        dialogue_check = check_dialogue_length(content)
        forbidden_check = check_forbidden_elements(content)
        shuang_check = check_shuang_density(filepath)
        
        # 计算总分
        checks = [
            title_check['passed'],
            ending_check['passed'],
            dialogue_check['passed'],
            forbidden_check['passed'],
            shuang_check.get('all_pass', False)
        ]
        score = sum(checks) / len(checks) * 100
        
        # 汇总问题
        all_issues = []
        all_issues.extend(title_check['issues'])
        all_issues.extend(forbidden_check['issues'])
        if not dialogue_check['passed']:
            all_issues.append(f"存在 {dialogue_check['long_dialogues']} 处超长对话")
        if not shuang_check.get('all_pass', True):
            failing_eps = [e for e in shuang_check.get('episodes', []) if not e.get('pass', True)]
            if failing_eps:
                all_issues.append(f"{len(failing_eps)} 集未达爽点/字数标准")
        
        return {
            "file": name,
            "score": round(score, 1),
            "checks": {
                "title_format": title_check,
                "ending_format": ending_check,
                "dialogue_length": dialogue_check,
                "forbidden_elements": forbidden_check,
                "shuang_density": shuang_check
            },
            "issues": all_issues,
            "passed": score >= 80,
            "recommendation": (
                "✅ 符合红果平台投稿规范" 
                if score >= 80 
                else "⚠️ 需要修改后方可投稿"
            )
        }
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        result = check_platform_compliance(sys.argv[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法: python platform_checker.py <filepath>")
