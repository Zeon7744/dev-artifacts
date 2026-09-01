#!/usr/bin/env python3
"""
分镜生成器 - 根据剧本内容生成视频分镜脚本
支持短剧/影视风格的场景拆分和镜头描述
"""

import re
import json
from typing import List, Dict, Tuple
from pathlib import Path
from datetime import datetime


# 镜头类型定义
SHOT_TYPES = {
    "特写": {"code": "CU", "description": "聚焦人物面部或细节"},
    "近景": {"code": "MS", "description": "人物胸部以上画面"},
    "中景": {"code": "MID", "description": "人物全身或环境结合"},
    "远景": {"code": "LS", "description": "大环境或人物在环境中"},
    "全景": {"code": "ELS", "description": "完整场景展现"},
    "主观镜头": {"code": "POV", "description": "角色视角"},
    "俯拍": {"code": "BT", "description": "从上往下拍摄"},
    "仰拍": {"code": "WT", "description": "从下往上拍摄"}
}

# 运镜类型
CAMERA_MOVES = {
    "固定": {"code": "FIX", "description": "镜头静止"},
    "推镜": {"code": "IN", "description": "镜头向前推进"},
    "拉镜": {"code": "OUT", "description": "镜头向后拉远"},
    "摇镜": {"code": "PAN", "description": "水平旋转拍摄"},
    "移镜": {"code": "TRD", "description": "横向移动拍摄"},
    "跟镜": {"code": "FOL", "description": "跟随主体移动"},
    "手持": {"code": "HAND", "description": "手持拍摄，有晃动感"}
}

# 情绪标签
MOOD_TAGS = [
    "紧张", "悬疑", "欢快", "悲伤", "浪漫", "愤怒", "恐惧", "温馨",
    "激烈", "平静", "神秘", "震撼", "感动", "搞笑", "虐心", "甜蜜"
]


def extract_dialogues(content: str) -> List[Dict]:
    """提取剧本中的对话"""
    dialogues = []
    
    # 匹配对话格式："对话内容"
    pattern = r'"([^"]+)"'
    matches = list(re.finditer(pattern, content))
    
    for match in matches:
        dialogue = match.group(1).strip()
        if dialogue and len(dialogue) > 0:
            # 查找对话所在行号
            line_num = content[:match.start()].count('\n') + 1
            
            # 查找上下文（动作描述）
            context_start = max(0, match.start() - 100)
            context_end = min(len(content), match.end() + 100)
            context = content[context_start:context_end].strip()
            
            dialogues.append({
                "line": line_num,
                "content": dialogue,
                "length": len(dialogue),
                "context": context[:80] + "..." if len(context) > 80 else context
            })
    
    return dialogues


def analyze_scene_content(content: str, scene_num: int) -> Dict:
    """分析单场景内容"""
    # 提取动作描述（括号内容）
    actions = re.findall(r'\(([^)]+)\)', content)
    
    # 提取对话
    dialogues = extract_dialogues(content)
    
    # 识别情绪
    mood = detect_mood(content)
    
    # 识别角色
    characters = extract_characters(content)
    
    # 估算时长
    estimated_duration = estimate_duration(actions, dialogues)
    
    return {
        "scene_num": scene_num,
        "actions": actions,
        "dialogues": dialogues,
        "mood": mood,
        "characters": characters,
        "estimated_duration": estimated_duration,
        "word_count": len(re.sub(r'\s+', '', content))
    }


def detect_mood(content: str) -> str:
    """检测场景情绪"""
    mood_scores = {}
    
    for mood in MOOD_TAGS:
        count = len(re.findall(mood, content))
        if count > 0:
            mood_scores[mood] = count
    
    if not mood_scores:
        return "中性"
    
    return max(mood_scores, key=mood_scores.get)


def extract_characters(content: str) -> List[str]:
    """提取场景中出现的角色"""
    characters = set()
    
    # 常见角色称呼
    role_patterns = [
        r'(总裁|老板|先生|小姐|夫人|少爷|千金)',
        r'(老公|老婆|夫君|娘子)',
        r'(爸爸|妈妈|儿子|女儿|哥哥|姐姐|弟弟|妹妹)',
        r'(师父|师尊|师傅)',
        r'(保镖|助理|秘书|管家)',
        r'(龙|凤|帝|皇|仙|神)',
        r'(你|我|他|她)'
    ]
    
    for pattern in role_patterns:
        matches = re.findall(pattern, content)
        characters.update(matches)
    
    return list(characters)[:5]  # 最多返回5个角色


def estimate_duration(actions: List[str], dialogues: List[Dict]) -> int:
    """估算场景时长（秒）"""
    # 动作描述：每10字约1秒
    action_time = sum(len(a) for a in actions) // 10
    
    # 对话：每字约0.3秒
    dialogue_time = sum(d['length'] * 0.3 for d in dialogues)
    
    # 基础时长：每场景至少5秒
    base_time = 5
    
    return max(base_time, int(action_time + dialogue_time))


def generate_shot_list(scene: Dict) -> List[Dict]:
    """为场景生成镜头列表"""
    shots = []
    shot_type_keys = list(SHOT_TYPES.keys())
    camera_move_keys = list(CAMERA_MOVES.keys())
    
    # 根据内容生成不同镜头
    dialogues = scene.get('dialogues', [])
    actions = scene.get('actions', [])
    
    # 开场镜头
    shots.append({
        "shot_num": 1,
        "type": "远景",
        "camera": "固定",
        "description": f"场景{scene['scene_num']}开场，展现整体环境",
        "duration": 3,
        "notes": "建立空间关系"
    })
    
    # 根据对话生成镜头
    for i, dialogue in enumerate(dialogues[:5]):  # 最多处理5句对话
        shot_type = shot_type_keys[i % len(shot_type_keys)]
        camera_move = camera_move_keys[i % len(camera_move_keys)]
        
        shots.append({
            "shot_num": len(shots) + 1,
            "type": shot_type,
            "camera": camera_move,
            "content": dialogue['content'],
            "duration": max(2, dialogue['length'] // 3),
            "notes": f"台词{len(shots)}：{dialogue['context'][:30]}"
        })
    
    # 根据动作生成镜头
    for action in actions[:3]:  # 最多处理3个动作
        shot_type = shot_type_keys[(len(shots)) % len(shot_type_keys)]
        camera_move = camera_move_keys[(len(shots)) % len(camera_move_keys)]
        
        shots.append({
            "shot_num": len(shots) + 1,
            "type": shot_type,
            "camera": camera_move,
            "action": action,
            "duration": max(2, len(action) // 5),
            "notes": f"动作：{action[:30]}"
        })
    
    # 结尾镜头
    shots.append({
        "shot_num": len(shots) + 1,
        "type": "远景",
        "camera": "拉镜",
        "description": f"场景{scene['scene_num']}收尾",
        "duration": 2,
        "notes": "情绪过渡"
    })
    
    return shots


def split_script_by_episodes(content: str) -> List[Tuple[int, str]]:
    """按集拆分剧本"""
    episodes = []
    
    # 匹配第X集：集名 的格式
    pattern = r'##\s*第(\d+)集[：:]\s*(.+?)(?=\n##\s*第\d+集|\Z)'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    for match in matches:
        ep_num = int(match.group(1))
        ep_content = match.group(2).strip()
        episodes.append((ep_num, ep_content))
    
    return episodes


def generate_storyboard(filepath: str) -> Dict:
    """生成分镜脚本
    
    Args:
        filepath: 剧本文件路径
    
    Returns:
        JSON 格式的分镜脚本
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        filename = Path(filepath).stem
        total_start = datetime.now()
        
        # 按集拆分
        episodes = split_script_by_episodes(content)
        
        if not episodes:
            # 尝试按 ## 分隔
            sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
            episodes = [(i+1, s) for i, s in enumerate(sections[1:]) if s.strip()]
        
        # 生成分镜
        storyboard = {
            "title": filename,
            "generated_at": total_start.isoformat(),
            "total_episodes": len(episodes),
            "episodes": []
        }
        
        total_shots = 0
        total_duration = 0
        
        for ep_num, ep_content in episodes:
            # 分析场景
            scenes = re.split(r'\n\n+', ep_content)
            scenes = [s.strip() for s in scenes if len(s.strip()) > 20]
            
            episode_shots = []
            episode_duration = 0
            
            for scene_num, scene_content in enumerate(scenes[:10], 1):  # 每集最多10个场景
                scene_info = analyze_scene_content(scene_content, scene_num)
                shots = generate_shot_list(scene_info)
                
                episode_shots.extend(shots)
                episode_duration += sum(s['duration'] for s in shots)
                total_shots += len(shots)
            
            storyboard['episodes'].append({
                "episode": ep_num,
                "title": f"第{ep_num}集",
                "scenes": len(scenes),
                "shots": len(episode_shots),
                "duration": episode_duration,
                "shots_detail": episode_shots
            })
        
        storyboard['total_shots'] = total_shots
        storyboard['total_duration'] = total_duration
        storyboard['stats'] = {
            "avg_shots_per_episode": round(total_shots / len(episodes), 1) if episodes else 0,
            "avg_duration_per_episode": round(total_duration / len(episodes), 1) if episodes else 0,
            "total_runtime_minutes": round(total_duration / 60, 1)
        }
        
        return storyboard
        
    except Exception as e:
        return {"error": str(e)}


def save_storyboard(storyboard: Dict, output_path: str = None) -> str:
    """保存分镜脚本到文件"""
    if output_path is None:
        output_path = f"data/storyboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(storyboard, f, ensure_ascii=False, indent=2)
    
    return output_path


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        result = generate_storyboard(filepath)
        
        # 输出到文件
        if 'error' in result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            output_path = save_storyboard(result)
            print(f"✅ 分镜脚本已生成: {output_path}")
            print(f"📊 统计:")
            print(f"   总集数: {result['total_episodes']}")
            print(f"   总镜头: {result['total_shots']}")
            print(f"   总时长: {result['total_duration']}秒 ({result['stats']['total_runtime_minutes']}分钟)")
            print(f"\n各集详情:")
            for ep in result['episodes']:
                print(f"   第{ep['episode']}集: {ep['shots']}镜头, {ep['duration']}秒")
    else:
        print("用法: python storyboard_generator.py <script_file>")
