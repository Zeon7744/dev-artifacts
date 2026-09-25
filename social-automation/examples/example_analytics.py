"""
使用示例 - 互动追踪与分析
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import load_config
from engagement_tracker import EngagementTracker
from analytics_dashboard import AnalyticsDashboard

config = load_config()
tracker = EngagementTracker(config)
dashboard = AnalyticsDashboard()

# ── 示例 1: 追踪单条内容互动 ─────────────────────────
# stats = tracker.track_engagement("article_12345", "juejin")
# print(f"掘金文章互动: {stats}")

# ── 示例 2: 批量追踪 ─────────────────────────────────
# posts = [
#     {"post_id": "article_12345", "platform": "juejin"},
#     {"post_id": "tweet_67890", "platform": "twitter"},
# ]
# results = tracker.track_multiple(posts)

# ── 示例 3: 分析互动趋势 ─────────────────────────────
# trend = tracker.get_trend("article_12345", "juejin", hours=48)
# print(f"增长趋势: {trend}")

# ── 示例 4: 找出高互动内容 ───────────────────────────
# top = tracker.top_content(platform="juejin", metric="likes", limit=5)
# for item in top:
#     print(f"[{item['platform']}] {item['post_id']}: {item['stats']}")

# ── 示例 5: 生成互动报告 ─────────────────────────────
# report = tracker.generate_report(days=7, platforms=["juejin", "twitter"])
# print(json.dumps(report, ensure_ascii=False, indent=2))

# ── 示例 6: 综合分析面板 ─────────────────────────────
# report = dashboard.generate_report(period="30d", platforms=["juejin", "weibo"])
# csv_path = dashboard.export_csv(report)
# print(f"CSV 已导出: {csv_path}")

print("示例脚本加载完成，取消注释以执行实际操作。")
