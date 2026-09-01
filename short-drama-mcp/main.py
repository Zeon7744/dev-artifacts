#!/usr/bin/env python3
"""
短剧创作 MCP 服务器
集成剧本校验、爽点统计、大纲生成等创作工具
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

from tools.format_checker import check_markdown_file, scan_files, CheckResult
from tools.stats_analyzer import analyze_content, classify_content
from tools.classifier import classify_content as classify_file
from tools.shuang_analyzer import count_shuang_points, get_shuang_details
from tools.platform_checker import check_platform_compliance, PLATFORM_RULES
from tools.outline_generator import generate_episode_outline

mcp = FastMCP("short-drama-creator")


@mcp.tool()
def list_tools() -> str:
    """列出所有可用工具及其功能说明
    
    Returns:
        JSON 格式的工具列表
    """
    tools = [
        {
            "name": "check_script_format",
            "description": "校验剧本格式：检查禁止字符（耀/曜）、括号规范（【】）、标题格式、对话字数限制",
            "params": ["filepath", "strict_mode"]
        },
        {
            "name": "count_shuang_points",
            "description": "统计爽点密度：分析剧本中的爽点数量和分布，计算每集爽点密度",
            "params": ["filepath"]
        },
        {
            "name": "generate_episode_outline",
            "description": "根据小说生成集纲：分析小说内容，生成符合短剧规范的集数大纲",
            "params": ["novel_content", "total_episodes", "genre"]
        },
        {
            "name": "check_platform_compliance",
            "description": "检查红果平台投稿规范：验证对话长度、爽点数量、禁止元素等",
            "params": ["filepath"]
        },
        {
            "name": "classify_content",
            "description": "内容分类：自动识别短剧剧本、短篇小说、教程文档等类型",
            "params": ["filepath"]
        }
    ]
    return json.dumps(tools, ensure_ascii=False, indent=2)


@mcp.tool()
def check_script_format(filepath: str, strict_mode: bool = False) -> str:
    """校验剧本格式是否符合规范
    
    检查项：
    - 禁止字符：耀、曜
    - 禁止括号：【、】
    - 标题格式：第X集：集名
    - 结尾格式：第X集完
    - 对话长度：≤15字
    - 章节完整性
    
    Args:
        filepath: 剧本文件路径
        strict_mode: 严格模式（额外检查对话字数）
    
    Returns:
        JSON 格式的校验结果，包含 score、issues、summary
    """
    try:
        result = check_markdown_file(filepath)
        
        # 扩展检查
        issues = list(result.issues)
        
        if strict_mode:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查对话长度
            dialogues = [d for d in content.split('\n') if '"' in d]
            long_dialogues = []
            for d in dialogues:
                # 提取引号内的对话
                import re
                matches = re.findall(r'"([^"]+)"', d)
                for match in matches:
                    if len(match) > 15:
                        long_dialogues.append({
                            "dialogue": match[:30] + "..." if len(match) > 30 else match,
                            "length": len(match)
                        })
            
            if long_dialogues:
                issues.append(f"发现 {len(long_dialogues)} 处超长对话（>15字）")
        
        # 计算最终分数
        score = max(0, 100 - len(issues) * 15)
        
        output = {
            "file": result.name,
            "score": score,
            "total_chars": result.total_chars,
            "sections": result.items,
            "issues": issues,
            "passed": score >= 80,
            "recommendation": "可通过" if score >= 80 else "需修改" if score >= 60 else "不合格"
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def count_shuang_points(filepath: str) -> str:
    """统计爽点密度
    
    分析剧本中的爽点元素：
    - 打脸反转
    - 实力展现
    - 危机解除
    - 身份揭露
    
    Args:
        filepath: 剧本文件路径
    
    Returns:
        JSON 格式的统计结果，包含总爽点数、每集详情、密度分析
    """
    try:
        result = count_shuang_points(filepath)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def generate_episode_outline(novel_content: str, total_episodes: int = 10, genre: str = "玄幻重生") -> str:
    """根据小说生成集纲大纲
    
    分析小说内容，按照短剧规范生成集数大纲：
    - 每集标题格式：第X集：集名
    - 核心情节提炼
    - 爽点/甜点设计建议
    
    Args:
        novel_content: 小说原文内容
        total_episodes: 目标集数（默认10集）
        genre: 题材类型（默认玄幻重生）
    
    Returns:
        JSON 格式的集纲大纲，包含每集的标题、情节、爽点建议
    """
    try:
        result = generate_episode_outline(novel_content, total_episodes, genre)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def check_platform_compliance(filepath: str) -> str:
    """检查红果短剧平台投稿规范
    
    检查项：
    - 标题格式：第X集：集名
    - 结尾格式：第X集完
    - 对话长度：≤15字
    - 爽点密度：≥3爽点/集
    - 禁止元素：军事、系统文、迷信内容
    - 最低字数：每集≥500字
    
    Args:
        filepath: 剧本文件路径
    
    Returns:
        JSON 格式的合规检查结果，包含各项检测结果和总体结论
    """
    try:
        result = check_platform_compliance(filepath)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def classify_content(filepath: str) -> str:
    """内容分类 - 自动识别文件类型
    
    分类类型：
    - 短剧剧本
    - 短篇小说
    - 教程文档
    - 工具脚本
    - 配置文件
    - 其他
    
    Args:
        filepath: 文件路径
    
    Returns:
        JSON 格式的分类结果，包含类型、置信度、匹配关键词
    """
    try:
        result = classify_file(filepath)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def run_server():
    """运行 MCP 服务器"""
    if not MCP_AVAILABLE:
        print("错误: 请先安装 mcp 包: pip install mcp")
        sys.exit(1)
    
    print(f"🎬 短剧创作 MCP 服务器启动...")
    print(f"📍 工具数量: 5")
    print(f"   - check_script_format: 剧本格式校验")
    print(f"   - count_shuang_points: 爽点统计")
    print(f"   - generate_episode_outline: 集纲生成")
    print(f"   - check_platform_compliance: 平台合规检查")
    print(f"   - classify_content: 内容分类")
    print("-" * 50)
    
    mcp.run()


if __name__ == "__main__":
    run_server()
