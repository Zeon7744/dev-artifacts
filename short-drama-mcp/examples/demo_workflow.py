#!/usr/bin/env python3
"""完整工作流演示

演示如何使用短剧创作 Agent 系统从小说素材生成完整短剧剧本。

使用方式：
    # 设置 API Key
    export OPENAI_API_KEY="sk-..."

    # 运行完整工作流
    python examples/demo_workflow.py

    # 指定参数
    python examples/demo_workflow.py --genre "玄幻重生" --episodes 10

    # 单步执行（如只生成角色）
    python examples/demo_workflow.py --step character
"""

import sys
import json
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.base import AgentConfig
from agents.plot_agent import PlotAgent
from agents.character_agent import CharacterAgent
from agents.dialogue_agent import DialogueAgent
from agents.script_agent import ScriptAgent
from agents.quality_agent import QualityAgent
from agents.trend_agent import TrendAgent
from agents.seo_agent import SeoAgent
from workflows.orchestrator import WorkflowOrchestrator


# ── 示例素材 ──────────────────────────────────────────────────

SAMPLE_NOVEL = """
他曾经是商界传奇，一手建立了万亿帝国。
然而一场阴谋让他失去了所有——公司、妻子、甚至尊严。
三年后，他以一个普通助理的身份重新出现在前妻的公司。
所有人都以为他是个废物，没有人知道他的真实身份。
当他一步步揭开当年的真相，所有人都将为之颤抖。
"""


def demo_full_workflow():
    """演示完整工作流"""
    print("=" * 60)
    print("🎬 短剧创作 Agent 系统 - 完整工作流演示")
    print("=" * 60)

    # 初始化
    config = AgentConfig(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model="gpt-4o-mini",
    )
    orch = WorkflowOrchestrator(config)

    # 执行
    result = orch.run_full_workflow(
        novel_input=SAMPLE_NOVEL,
        genre="都市逆袭",
        episode_count=8,
    )

    # 输出报告
    print("\n" + "=" * 60)
    print("📊 工作流执行报告")
    print("=" * 60)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    # 保存结果
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "workflow_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存: {output_file}")

    return result


def demo_single_agent():
    """演示单个 Agent 使用"""
    print("\n" + "=" * 60)
    print("🔧 单 Agent 演示")
    print("=" * 60)

    config = AgentConfig(api_key=os.getenv("OPENAI_API_KEY", ""))

    # 1. 剧情生成
    print("\n--- PlotAgent ---")
    plot_agent = PlotAgent(config)
    plot = plot_agent.generate_plot(
        novel_input=SAMPLE_NOVEL,
        genre="都市逆袭",
        episode_count=8,
    )
    print(f"剧名: {plot.get('title', '未命名')}")
    print(f"集数: {len(plot.get('episodes', []))}")

    # 2. 角色设计
    print("\n--- CharacterAgent ---")
    char_agent = CharacterAgent(config)
    characters = char_agent.create_characters(
        story_summary=plot.get("logline", SAMPLE_NOVEL[:200]),
        genre="都市逆袭",
        character_count=5,
    )
    for c in characters.get("characters", []):
        print(f"  {c.get('name', '?')}: {c.get('identity', '?')}")

    # 3. 质量检查
    print("\n--- QualityAgent ---")
    quality_agent = QualityAgent(config)
    sample_script = """## 第1集：重生

（主角走进公司大门）

"三年了。"

（看向总裁办公室）

"这次，我不会再输。"

秘书："你就是新来的助理？"
主角："对。"
秘书："看你的样子也不像能干活的。"
主角："试试就知道了。"

第1集完
"""
    report = quality_agent.quick_check(sample_script)
    print(f"  分数: {report['score']}")
    print(f"  通过: {report['passed']}")


def demo_quality_pipeline():
    """演示质量检查流水线"""
    print("\n" + "=" * 60)
    print("🔍 质量检查流水线演示")
    print("=" * 60)

    config = AgentConfig(api_key=os.getenv("OPENAI_API_KEY", ""))
    quality = QualityAgent(config)

    # 测试用例1：合格剧本
    good_script = """## 第1集：归来

（夜，城市街头）

"我回来了。"

（主角看向高楼大厦）

"这座城市的每一寸土地，都是我一砖一瓦建起来的。"

（手机响）

"顾总，公司出事了！"
主角："说。"
"有人在转移资产！"
主角："我知道了。"

（冷笑）

"他们以为我死了？"

第1集完
"""
    result1 = quality.quick_check(good_script)
    print(f"\n✅ 合格剧本: {result1['score']}分 / 通过={result1['passed']}")

    # 测试用例2：含禁止字符
    bad_script = """## 第1集：光耀归来

"我的光芒无人能挡！"

第1集完
"""
    result2 = quality.quick_check(bad_script)
    print(f"\n❌ 禁止字符: {result2['score']}分 / 通过={result2['passed']}")
    for issue in result2.get("issues", []):
        print(f"  [{issue['severity']}] {issue['type']}")


def demo_seo_optimization():
    """演示 SEO 优化"""
    print("\n" + "=" * 60)
    print("📈 SEO 优化演示")
    print("=" * 60)

    config = AgentConfig(api_key=os.getenv("OPENAI_API_KEY", ""))
    seo = SeoAgent(config)

    result = seo.generate_titles(
        story_summary="他曾是商界传奇，失去一切后以助理身份回到前妻公司，一步步复仇逆袭",
        genre="都市逆袭",
        core_conflict="身份暴露 vs 隐藏复仇",
    )

    print("\n推荐标题:")
    for t in result.get("titles", [])[:5]:
        print(f"  [{t.get('type', '?')}] {t.get('title', '?')} (CTR: {t.get('ctr_score', '?')})")

    print(f"\n首选: {result.get('best_pick', '无')}")
    print(f"理由: {result.get('reason', '无')}")


def main():
    """主入口"""
    import argparse
    parser = argparse.ArgumentParser(description="短剧创作 Agent 演示")
    parser.add_argument("--step", choices=["full", "single", "quality", "seo"],
                       default="full", help="演示类型")
    parser.add_argument("--genre", default="都市逆袭", help="题材类型")
    parser.add_argument("--episodes", type=int, default=8, help="集数")
    args = parser.parse_args()

    demos = {
        "full": demo_full_workflow,
        "single": demo_single_agent,
        "quality": demo_quality_pipeline,
        "seo": demo_seo_optimization,
    }

    demos[args.step]()


if __name__ == "__main__":
    main()
