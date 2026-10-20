#!/usr/bin/env python3
"""短剧创作 MCP 服务器 v2.0

集成剧本校验、爽点统计、集纲生成等创作工具
+ 全新 Agent 系统（剧情/角色/对话/格式化/质量/趋势/SEO）
MCP 2026-07-28 规范（无状态）
"""

import json
import sys
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("警告: mcp 包未安装，请运行: pip install mcp")

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "tools"))
sys.path.insert(0, str(SCRIPT_DIR / "agents"))

# 原有工具
from tools.format_checker import check_markdown_file, scan_files, CheckResult
from tools.stats_analyzer import analyze_content, classify_content
from tools.classifier import classify_content as classify_file
from tools.shuang_analyzer import count_shuang_points
from tools.platform_checker import check_platform_compliance, PLATFORM_RULES
from tools.outline_generator import generate_episode_outline
from tools.character_creator import create_character_profile, create_character_set
from tools.dialogue_optimizer import optimize_dialogue, check_dialogue_quality

# 新 Agent 系统
from agents.base import AgentConfig
from agents.plot_agent import PlotAgent
from agents.character_agent import CharacterAgent
from agents.dialogue_agent import DialogueAgent
from agents.script_agent import ScriptAgent
from agents.quality_agent import QualityAgent
from agents.trend_agent import TrendAgent
from agents.seo_agent import SeoAgent

if MCP_AVAILABLE:
    mcp = FastMCP("short-drama-creator")
else:
    mcp = None


# ── Agent 单例（延迟初始化） ──────────────────────────────

_agents = {}

def _get_agent(agent_class):
    name = agent_class.__name__
    if name not in _agents:
        config = AgentConfig(
            api_key=__import__("os").getenv("OPENAI_API_KEY", ""),
        )
        _agents[name] = agent_class(config)
    return _agents[name]


# ══════════════════════════════════════════════════════════
# 原有工具（保持不变）
# ══════════════════════════════════════════════════════════

@mcp.tool()
def list_tools() -> str:
    """列出所有可用工具及功能说明"""
    tools = [
        {"name": "check_script_format", "description": "校验剧本格式", "params": ["filepath", "strict_mode"]},
        {"name": "count_shuang_points", "description": "统计爽点密度", "params": ["filepath"]},
        {"name": "generate_episode_outline", "description": "生成集纲", "params": ["novel_content", "total_episodes", "genre"]},
        {"name": "check_platform_compliance", "description": "平台合规检查", "params": ["filepath"]},
        {"name": "classify_content", "description": "内容分类", "params": ["filepath"]},
        {"name": "create_character_profile", "description": "角色设定生成", "params": ["name", "role_type", "genre"]},
        {"name": "optimize_dialogue", "description": "对话优化", "params": ["filepath"]},
        # 新增 Agent 工具
        {"name": "agent_generate_plot", "description": "🤖 AI生成剧情方案", "params": ["novel_input", "genre", "episode_count"]},
        {"name": "agent_create_characters", "description": "🤖 AI设计角色方案", "params": ["story_summary", "genre", "character_count"]},
        {"name": "agent_generate_dialogue", "description": "🤖 AI生成场景对话", "params": ["scene_json", "characters_json", "mood"]},
        {"name": "agent_format_script", "description": "🤖 AI格式化剧本", "params": ["content", "format_type", "episode_count"]},
        {"name": "agent_check_quality", "description": "🤖 AI质量审查", "params": ["script_content"]},
        {"name": "agent_analyze_trends", "description": "🤖 AI趋势分析", "params": ["platform", "genre"]},
        {"name": "agent_optimize_seo", "description": "🤖 AI SEO优化", "params": ["title", "description", "tags", "genre"]},
    ]
    return json.dumps(tools, ensure_ascii=False, indent=2)


@mcp.tool()
def check_script_format(filepath: str, strict_mode: bool = False) -> str:
    """校验剧本格式是否符合规范"""
    try:
        result = check_markdown_file(filepath)
        issues = list(result.issues)
        if strict_mode:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            import re
            dialogues = re.findall(r'"([^"]+)"', content)
            long_dialogues = [d for d in dialogues if len(d) > 15]
            if long_dialogues:
                issues.append(f"发现 {len(long_dialogues)} 处超长对话（>15字）")
        score = max(0, 100 - len(issues) * 15)
        output = {
            "file": result.name, "score": score, "total_chars": result.total_chars,
            "sections": result.items, "issues": issues,
            "passed": score >= 80,
            "recommendation": "可通过" if score >= 80 else "需修改" if score >= 60 else "不合格"
        }
        return json.dumps(output, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def count_shuang_points_tool(filepath: str) -> str:
    """统计爽点密度"""
    try:
        result = count_shuang_points(filepath)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def generate_episode_outline_tool(novel_content: str, total_episodes: int = 10, genre: str = "玄幻重生") -> str:
    """根据小说生成集纲大纲"""
    try:
        result = generate_episode_outline(novel_content, total_episodes, genre)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def check_platform_compliance_tool(filepath: str) -> str:
    """检查红果短剧平台投稿规范"""
    try:
        result = check_platform_compliance(filepath)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def classify_content_tool(filepath: str) -> str:
    """内容分类"""
    try:
        result = classify_file(filepath)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def create_character_profile_tool(name: str, role_type: str = "protagonist", genre: str = "玄幻重生") -> str:
    """生成角色设定档案"""
    try:
        result = create_character_profile(name, role_type, genre)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def optimize_dialogue_tool(filepath: str) -> str:
    """优化剧本对话质量"""
    try:
        result = check_dialogue_quality(filepath)
        return result
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ══════════════════════════════════════════════════════════
# 新增 Agent 工具
# ══════════════════════════════════════════════════════════

@mcp.tool()
def agent_generate_plot(novel_input: str, genre: str = "都市甜宠", episode_count: int = 8) -> str:
    """🤖 AI 生成剧情方案
    
    基于小说/大纲生成完整剧情，包含分集概要、爽点设计、反转安排。
    
    Args:
        novel_input: 小说原文/大纲/故事梗概
        genre: 题材类型（都市甜宠/玄幻重生/都市逆袭/悬疑推理/豪门恩怨）
        episode_count: 目标集数（默认8集）
    
    Returns:
        JSON 格式的完整剧情方案
    """
    try:
        agent = _get_agent(PlotAgent)
        result = agent.generate_plot(novel_input, genre, episode_count)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def agent_create_characters(story_summary: str, genre: str = "都市甜宠", character_count: int = 5) -> str:
    """🤖 AI 设计角色方案
    
    生成完整角色组：性格、关系网、成长弧线、标志性台词。
    
    Args:
        story_summary: 故事梗概
        genre: 题材类型
        character_count: 角色数量（默认5个）
    
    Returns:
        JSON 格式的完整角色方案
    """
    try:
        agent = _get_agent(CharacterAgent)
        result = agent.create_characters(story_summary, genre, character_count)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def agent_generate_dialogue(scene_json: str, characters_json: str, mood: str = "紧张") -> str:
    """🤖 AI 生成场景对话
    
    根据场景和角色生成对话，自动控制在15字以内。
    
    Args:
        scene_json: 场景描述 JSON（含 location, description, events）
        characters_json: 角色列表 JSON
        mood: 情绪基调（紧张/甜蜜/悲伤/搞笑）
    
    Returns:
        JSON 格式的对话方案
    """
    try:
        scene = json.loads(scene_json)
        characters = json.loads(characters_json)
        agent = _get_agent(DialogueAgent)
        result = agent.generate_dialogue(scene, characters, mood)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def agent_format_script(content: str, format_type: str = "standard", episode_count: int = 8) -> str:
    """🤖 AI 格式化剧本
    
    将草稿转化为标准短剧剧本格式。
    
    Args:
        content: 原始剧本内容
        format_type: 格式类型（standard/compact/detailed）
        episode_count: 目标集数
    
    Returns:
        JSON 格式的格式化结果
    """
    try:
        agent = _get_agent(ScriptAgent)
        result = agent.format_script(content, format_type, episode_count)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def agent_check_quality(script_content: str) -> str:
    """🤖 AI 质量审查
    
    全面检查剧本质量：格式、爽点密度、禁止字符、对话长度等。
    
    Args:
        script_content: 剧本内容文本
    
    Returns:
        JSON 格式的质量审查报告
    """
    try:
        agent = _get_agent(QualityAgent)
        result = agent.check_quality(script_content)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def agent_analyze_trends(platform: str = "红果短剧", genre: str = "都市甜宠") -> str:
    """🤖 AI 趋势分析
    
    分析平台热门元素、受众画像、竞品对比。
    
    Args:
        platform: 目标平台
        genre: 题材类型
    
    Returns:
        JSON 格式的趋势分析报告
    """
    try:
        agent = _get_agent(TrendAgent)
        result = agent.analyze_trends(platform, genre)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def agent_optimize_seo(title: str = "", description: str = "", tags: str = "", genre: str = "都市") -> str:
    """🤖 AI SEO 优化
    
    生成标题选项、优化标签、关键词分析、封面建议。
    
    Args:
        title: 原始标题
        description: 故事简介
        tags: 当前标签（逗号分隔）
        genre: 题材类型
    
    Returns:
        JSON 格式的 SEO 优化方案
    """
    try:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
        agent = _get_agent(SeoAgent)
        result = agent.optimize_seo(title, description, tag_list, genre)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def run_server():
    """运行 MCP 服务器"""
    if not MCP_AVAILABLE:
        print("错误: 请先安装 mcp 包: pip install mcp")
        sys.exit(1)
    
    print(f"🎬 短剧创作 MCP 服务器 v2.0 启动...")
    print(f"📍 工具数量: 15")
    print(f"   ── 基础工具（8个）──")
    print(f"   - check_script_format: 剧本格式校验")
    print(f"   - count_shuang_points: 爽点统计")
    print(f"   - generate_episode_outline: 集纲生成")
    print(f"   - check_platform_compliance: 平台合规检查")
    print(f"   - classify_content: 内容分类")
    print(f"   - create_character_profile: 角色设定生成")
    print(f"   - optimize_dialogue: 对话质量优化")
    print(f"   ── AI Agent（7个）──")
    print(f"   - agent_generate_plot: 🤖 剧情生成")
    print(f"   - agent_create_characters: 🤖 角色设计")
    print(f"   - agent_generate_dialogue: 🤖 对话生成")
    print(f"   - agent_format_script: 🤖 剧本格式化")
    print(f"   - agent_check_quality: 🤖 质量审查")
    print(f"   - agent_analyze_trends: 🤖 趋势分析")
    print(f"   - agent_optimize_seo: 🤖 SEO优化")
    print("-" * 50)
    
    mcp.run()


if __name__ == "__main__":
    run_server()
