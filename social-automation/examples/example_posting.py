"""
使用示例 - 内容发布
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import load_config
from content_poster import ContentPoster

config = load_config()
poster = ContentPoster(config)

# ── 示例 1: 发布到单个平台 ───────────────────────────
content = {
    "title": "AI短剧制作入门指南",
    "body": "本文将从零开始介绍如何使用AI工具制作短剧，包括剧本生成、画面合成、配音等全流程。",
    "hashtags": ["AI短剧", "AIGC", "内容创作"],
    "category": "AI",
}

# 发布到掘金
# result = poster.post_to_platform("juejin", content)
# print(result)

# ── 示例 2: 一键发布到所有平台 ───────────────────────
# results = poster.post_to_all(content, platforms=["juejin", "zhihu", "weibo", "twitter"])
# for r in results:
#     print(f"[{r['platform']}] {r.get('status', 'ok')}")

# ── 示例 3: 定时发布 ─────────────────────────────────
# poster.post_to_platform("weibo", content, schedule_time="2026-01-15T10:00:00")
# poster.post_to_platform("twitter", content, schedule_time="2026-01-15T14:00:00")

# ── 示例 4: 查看和执排期 ────────────────────────────
# scheduled = poster.get_scheduled_posts()
# print(f"待发布: {len(scheduled)} 条")
# poster.execute_scheduled()

# ── 示例 5: 查看发布历史 ────────────────────────────
# history = poster.get_post_history(10)
# for h in history:
#     print(f"[{h.get('platform')}] {h.get('title', h.get('text_preview', ''))}")

print("示例脚本加载完成，取消注释以执行实际操作。")
