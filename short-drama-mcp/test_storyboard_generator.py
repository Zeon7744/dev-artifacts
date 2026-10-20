#!/usr/bin/env python3
"""
分镜生成器单元测试
"""

import unittest
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from storyboard_generator import (
    extract_dialogues,
    analyze_scene_content,
    detect_mood,
    extract_characters,
    estimate_duration,
    generate_shot_list,
    split_script_by_episodes,
    generate_storyboard,
    save_storyboard
)


class TestExtractDialogues(unittest.TestCase):
    """测试对话提取功能"""
    
    def test_extracts_dialogues(self):
        """测试提取引号中的对话"""
        content = '''第1集：重生
场景：豪华办公室
"你居然敢背叛我！"小明愤怒地说。
"对不起，我有苦衷。"小红低头回应。
'''
        dialogues = extract_dialogues(content)
        self.assertEqual(len(dialogues), 2)
        self.assertIn("你居然敢背叛我！", [d['content'] for d in dialogues])
    
    def test_returns_empty_for_no_dialogue(self):
        """测试无对话时返回空列表"""
        content = "纯叙述文本，没有任何对话内容。"
        dialogues = extract_dialogues(content)
        self.assertEqual(len(dialogues), 0)
    
    def test_handles_empty_content(self):
        """测试空内容"""
        dialogues = extract_dialogues("")
        self.assertEqual(len(dialogues), 0)
    
    def test_dialogue_length(self):
        """测试对话长度计算"""
        content = '"这是一个很长的对话内容"'
        dialogues = extract_dialogues(content)
        self.assertEqual(len(dialogues), 1)
        # 中文字符长度为11
        self.assertEqual(dialogues[0]['length'], 11)


class TestDetectMood(unittest.TestCase):
    """测试情绪检测功能"""
    
    def test_detects_tense_mood(self):
        """测试紧张情绪检测"""
        content = "气氛紧张，他紧张地握紧拳头，眼神中透露着紧张"
        mood = detect_mood(content)
        self.assertEqual(mood, "紧张")
    
    def test_detects_romantic_mood(self):
        """测试浪漫情绪检测"""
        content = "温馨的夜晚，他们深情对视，心跳加速"
        mood = detect_mood(content)
        self.assertIn(mood, ["温馨", "浪漫"])
    
    def test_returns_neutral_for_empty(self):
        """测试空内容返回中性"""
        mood = detect_mood("")
        self.assertEqual(mood, "中性")
    
    def test_detects_anger(self):
        """测试愤怒情绪检测"""
        content = "他愤怒地摔门而出，满脸怒容"
        mood = detect_mood(content)
        self.assertEqual(mood, "愤怒")


class TestExtractCharacters(unittest.TestCase):
    """测试角色提取功能"""
    
    def test_extracts_family_roles(self):
        """测试家庭角色提取"""
        content = "爸爸严厉地看着儿子，妈妈在一旁担忧"
        characters = extract_characters(content)
        self.assertIn("爸爸", characters)
        self.assertIn("儿子", characters)
    
    def test_extracts_business_roles(self):
        """测试职场角色提取"""
        content = "总裁走进办公室，秘书跟在后面"
        characters = extract_characters(content)
        self.assertIn("总裁", characters)
        self.assertIn("秘书", characters)
    
    def test_returns_empty_for_no_roles(self):
        """测试无角色时返回空列表"""
        content = "只是普通的叙述，没有任何角色称呼"
        characters = extract_characters(content)
        self.assertEqual(len(characters), 0)


class TestEstimateDuration(unittest.TestCase):
    """测试时长估算功能"""
    
    def test_basic_calculation(self):
        """测试基础时长计算"""
        actions = ["这个动作描述了很长的一段情节内容"]
        dialogues = [{"content": "你好", "length": 2}]
        duration = estimate_duration(actions, dialogues)
        self.assertGreater(duration, 0)
    
    def test_minimum_duration(self):
        """测试最小时长为5秒"""
        duration = estimate_duration([], [])
        self.assertEqual(duration, 5)
    
    def test_dialogue_time(self):
        """测试对话时长计算"""
        actions = []
        dialogues = [{"content": "这是一个很长的对话内容用于测试", "length": 15}]
        duration = estimate_duration(actions, dialogues)
        self.assertGreaterEqual(duration, 5)


class TestGenerateShotList(unittest.TestCase):
    """测试镜头列表生成功能"""
    
    def test_generates_shots(self):
        """测试生成镜头列表"""
        scene = {
            "scene_num": 1,
            "actions": ["他站起来"],
            "dialogues": [{"content": "你好", "length": 2, "context": "测试上下文"}],
            "mood": "中性",
            "characters": ["主角"],
            "estimated_duration": 10
        }
        shots = generate_shot_list(scene)
        self.assertGreater(len(shots), 0)
    
    def test_shot_structure(self):
        """测试镜头结构"""
        scene = {
            "scene_num": 1,
            "actions": [],
            "dialogues": [],
            "mood": "紧张",
            "characters": [],
            "estimated_duration": 10
        }
        shots = generate_shot_list(scene)
        
        for shot in shots:
            self.assertIn("shot_num", shot)
            self.assertIn("type", shot)
            self.assertIn("duration", shot)
    
    def test_opening_shot(self):
        """测试开场镜头"""
        scene = {"scene_num": 1, "actions": [], "dialogues": [], "mood": "中性", "characters": [], "estimated_duration": 10}
        shots = generate_shot_list(scene)
        self.assertIn("开场", shots[0]['description'])


class TestSplitScriptByEpisodes(unittest.TestCase):
    """测试剧本按集拆分功能"""
    
    def test_splits_by_episode_header(self):
        """测试按集标题拆分"""
        content = '''## 第1集：重生
这是第一集的内容

## 第2集：觉醒
这是第二集的内容
'''
        episodes = split_script_by_episodes(content)
        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0][0], 1)
        self.assertEqual(episodes[1][0], 2)
    
    def test_returns_empty_for_invalid_format(self):
        """测试无效格式返回空列表"""
        content = "普通文本，没有集标题格式"
        episodes = split_script_by_episodes(content)
        self.assertEqual(len(episodes), 0)


class TestGenerateStoryBoard(unittest.TestCase):
    """测试分镜生成主功能"""
    
    def test_generates_storyboard(self):
        """测试生成分镜脚本"""
        # 创建临时剧本文件
        with TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "test_script.md"
            script_path.write_text('''## 第1集：重生
场景：豪华办公室

"你居然敢背叛我！"小明愤怒地说。
"对不起，我有苦衷。"小红低头回应。
''')
            
            result = generate_storyboard(str(script_path))
            self.assertNotIn("error", result)
            self.assertIn("episodes", result)
            self.assertIn("total_episodes", result)
    
    def test_handles_missing_file(self):
        """测试处理缺失文件"""
        result = generate_storyboard("/nonexistent/path/script.md")
        self.assertIn("error", result)


class TestSaveStoryboard(unittest.TestCase):
    """测试分镜保存功能"""
    
    def test_saves_to_file(self):
        """测试保存到文件"""
        storyboard = {
            "title": "测试剧本",
            "episodes": [],
            "total_shots": 0,
            "total_duration": 0
        }
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            saved_path = save_storyboard(storyboard, str(output_path))
            
            self.assertTrue(Path(saved_path).exists())
            
            with open(saved_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.assertEqual(data['title'], "测试剧本")


if __name__ == '__main__':
    unittest.main()
