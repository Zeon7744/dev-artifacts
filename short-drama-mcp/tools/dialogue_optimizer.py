#!/usr/bin/env python3
"""对话优化工具
检查对话长度、检测冗余、提供精简建议
"""

import re
import json
from typing import List, Dict, Tuple


def optimize_dialogue(content: str, filepath: str = None) -> Dict:
    """
    优化剧本对话
    
    Args:
        content: 剧本内容或文件路径
        filepath: 文件路径（如果content是路径）
    
    Returns:
        JSON格式的优化报告
    """
    # 读取内容
    if filepath:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = content
    
    # 提取对话
    dialogues = extract_dialogues(text)
    
    # 分析对话
    analysis = analyze_dialogues(dialogues)
    
    # 生成优化建议
    suggestions = generate_suggestions(analysis)
    
    return {
        "total_dialogues": len(dialogues),
        "dialogues_over_15": analysis["over_count"],
        "dialogues_under_5": analysis["short_count"],
        "average_length": analysis["avg_length"],
        "redundant_patterns": analysis["redundant"],
        "suggestions": suggestions,
        "optimized_text": optimize_text(text, dialogues, suggestions)
    }


def extract_dialogues(text: str) -> List[Tuple[str, int]]:
    """
    提取所有对话
    
    Returns:
        [(对话内容, 行号), ...]
    """
    dialogues = []
    lines = text.split('\n')
    
    # 匹配各种对话格式
    patterns = [
        r'"([^"]+)"',           # 中文引号
        r'"([^"]+)"',           # 英文引号
        r'「([^」]+)」',        # 日式引号
        r'：(.+?)(?:\n|$)',    # 冒号后对话
    ]
    
    for line_num, line in enumerate(lines, 1):
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                # 过滤掉非对话内容（如动作描述）
                if len(match.strip()) > 0 and not match.startswith('（'):
                    dialogues.append((match.strip(), line_num))
                break
    
    return dialogues


def analyze_dialogues(dialogues: List[Tuple[str, int]]) -> Dict:
    """分析对话质量"""
    if not dialogues:
        return {
            "over_count": 0,
            "short_count": 0,
            "avg_length": 0,
            "redundant": []
        }
    
    lengths = [len(d[0]) for d in dialogues]
    
    # 超长对话
    over_15 = [(d, line) for d, line in dialogues if len(d) > 15]
    
    # 过短对话（可能是动作）
    under_5 = [(d, line) for d, line in dialogues if len(d) < 5 and not d.startswith('（')]
    
    # 检测冗余模式
    redundant = detect_redundancy(dialogues)
    
    return {
        "over_count": len(over_15),
        "short_count": len(under_5),
        "avg_length": sum(lengths) / len(lengths) if lengths else 0,
        "redundant": redundant,
        "over_15_details": [{"dialogue": d, "line": line, "length": len(d)} 
                           for d, line in over_15]
    }


def detect_redundancy(dialogues: List[Tuple[str, int]]) -> List[Dict]:
    """检测冗余对话模式"""
    redundant_patterns = []
    
    # 常见冗余模式
    patterns = [
        (r'我以为.*已经', '主观臆测'),
        (r'难道.*吗', '反问冗余'),
        (r'毕竟.*的', '解释冗余'),
        (r'其实.*是', '揭示冗余'),
    ]
    
    for dialogue, line in dialogues:
        for pattern, desc in patterns:
            if re.search(pattern, dialogue):
                redundant_patterns.append({
                    "dialogue": dialogue,
                    "line": line,
                    "pattern": desc,
                    "suggestion": f"精简{desc}部分"
                })
                break
    
    return redundant_patterns


def generate_suggestions(analysis: Dict) -> List[str]:
    """生成优化建议"""
    suggestions = []
    
    if analysis["over_count"] > 0:
        suggestions.append(
            f"发现 {analysis['over_count']} 处超长对话（>15字），需精简"
        )
    
    if analysis["avg_length"] > 12:
        suggestions.append(
            f"平均对话长度 {analysis['avg_length']:.1f} 字，建议控制在10字以内"
        )
    
    if analysis["redundant"]:
        suggestions.append(
            f"发现 {len(analysis['redundant'])} 处冗余表达，建议删除修饰词"
        )
    
    if not suggestions:
        suggestions.append("对话质量良好，符合规范")
    
    return suggestions


def optimize_text(text: str, dialogues: List[Tuple[str, int]], suggestions: List[str]) -> str:
    """生成优化后的文本"""
    optimized = text
    
    # 简单优化：去除明显冗余
    redundant_phrases = [
        (r'我认为.*', ''),
        (r'我觉得.*', ''),
        (r'其实.*', ''),
    ]
    
    for pattern, replacement in redundant_phrases:
        optimized = re.sub(pattern, replacement, optimized)
    
    # 截断超长对话
    for dialogue, line in dialogues:
        if len(dialogue) > 15:
            # 找到对话在原文件中的位置并截断
            lines = optimized.split('\n')
            if line <= len(lines):
                line_content = lines[line - 1]
                # 只截断引号内的内容
                match = re.search(r'"([^"]+)"', line_content)
                if match:
                    long_dialogue = match.group(1)
                    if len(long_dialogue) > 15:
                        # 取前15字
                        short_dialogue = long_dialogue[:15]
                        new_line = line_content.replace(f'"{long_dialogue}"', f'"{short_dialogue}"')
                        lines[line - 1] = new_line
                optimized = '\n'.join(lines)
    
    return optimized


def check_dialogue_quality(filepath: str) -> str:
    """
    检查剧本对话质量（主入口）
    
    Args:
        filepath: 剧本文件路径
    
    Returns:
        JSON格式的质检报告
    """
    result = optimize_dialogue(content="", filepath=filepath)
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(f"检查文件: {filepath}")
        result = check_dialogue_quality(filepath)
        print(result)
    else:
        # 测试示例
        test_content = '''第1集：重生

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
        
        print("=== 对话质检测试 ===\n")
        result = optimize_dialogue(content=test_content)
        print(json.dumps(result, ensure_ascii=False, indent=2))
