"""
数据分析面板 - 统一数据看板、多维度分析、趋势图表、导出报告
"""
import json
import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

from base import setup_logger, save_json, load_json

logger = setup_logger("analytics_dashboard")


class AnalyticsDashboard:
    """统一数据分析面板"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    @staticmethod
    def _load(filepath, default):
        if not os.path.exists(filepath):
            return default
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_report(self, period: str = "7d", platforms: list = None) -> dict:
        """
        生成综合分析报告
        period: 时间周期 (7d / 30d / 90d)
        platforms: 指定平台列表，None 则全部
        """
        days = int(period.rstrip("d"))
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # 加载各维度数据
        engagement = load_json(os.path.join(self.data_dir, "engagement_snapshots.json"), [])
        followers = load_json(os.path.join(self.data_dir, "follower_snapshots.json"), [])
        posts = load_json(os.path.join(self.data_dir, "post_history.json"), [])
        replies = load_json(os.path.join(self.data_dir, "reply_log.json"), [])

        # 过滤时间范围和平台
        if platforms:
            engagement = [e for e in engagement if e.get("platform") in platforms]
            followers = [f for f in followers if f.get("platform") in platforms]
            posts = [p for p in posts if p.get("platform") in platforms]

        eng_period = [e for e in engagement if e.get("timestamp", "") >= cutoff]
        fol_period = [f for f in followers if f.get("timestamp", "") >= cutoff]
        posts_period = [p for p in posts if p.get("timestamp", "") >= cutoff]
        replies_period = [r for r in replies if r.get("timestamp", "") >= cutoff]

        report = {
            "report_id": f"rpt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "platforms": platforms or ["all"],
            "summary": self._build_summary(eng_period, fol_period, posts_period, replies_period),
            "by_platform": self._build_platform_breakdown(eng_period, fol_period, posts_period),
            "trends": self._build_trends(eng_period, days),
            "top_content": self._find_top_content(eng_period),
        }

        report_path = os.path.join(self.data_dir, "analytics_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"报告生成完成: {report['report_id']}, 周期 {period}")
        return report

    def _build_summary(self, engagement, followers, posts, replies) -> dict:
        total_likes = sum(e.get("stats", {}).get("likes", 0) for e in engagement)
        total_comments = sum(e.get("stats", {}).get("comments", 0) for e in engagement)
        total_views = sum(e.get("stats", {}).get("views", 0) for e in engagement)
        total_reposts = sum(e.get("stats", {}).get("reposts", 0) for e in engagement)
        latest_followers = {}
        for f in followers:
            p = f.get("platform", "unknown")
            stats = f.get("stats", {})
            latest_followers[p] = stats.get("followers", 0)

        return {
            "total_engagements": len(engagement),
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_views": total_views,
            "total_reposts": total_reposts,
            "total_posts": len(posts),
            "total_auto_replies": len(replies),
            "total_followers": sum(latest_followers.values()),
            "followers_by_platform": latest_followers,
        }

    def _build_platform_breakdown(self, engagement, followers, posts) -> dict:
        platforms = defaultdict(lambda: {"likes": 0, "comments": 0, "views": 0, "posts": 0})
        for e in engagement:
            p = e.get("platform", "unknown")
            platforms[p]["likes"] += e.get("stats", {}).get("likes", 0)
            platforms[p]["comments"] += e.get("stats", {}).get("comments", 0)
            platforms[p]["views"] += e.get("stats", {}).get("views", 0)
        for post in posts:
            p = post.get("platform", "unknown")
            platforms[p]["posts"] += 1
        return dict(platforms)

    def _build_trends(self, engagement, days) -> dict:
        """按天聚合趋势"""
        daily = defaultdict(lambda: {"likes": 0, "comments": 0, "views": 0})
        for e in engagement:
            ts = e.get("timestamp", "")
            day = ts[:10] if len(ts) >= 10 else "unknown"
            daily[day]["likes"] += e.get("stats", {}).get("likes", 0)
            daily[day]["comments"] += e.get("stats", {}).get("comments", 0)
            daily[day]["views"] += e.get("stats", {}).get("views", 0)
        sorted_days = sorted(daily.keys())
        return {
            "daily": {d: daily[d] for d in sorted_days},
            "data_points": len(sorted_days),
        }

    def _find_top_content(self, engagement, metric="likes", limit=10) -> list:
        """找出最高互动内容"""
        latest = {}
        for e in sorted(engagement, key=lambda x: x.get("timestamp", "")):
            key = f"{e.get('platform')}:{e.get('post_id')}"
            latest[key] = e
        ranked = sorted(latest.values(), key=lambda x: x.get("stats", {}).get(metric, 0), reverse=True)
        return [{"post_id": r.get("post_id"), "platform": r.get("platform"), "likes": r.get("stats", {}).get("likes", 0), "comments": r.get("stats", {}).get("comments", 0)}
                for r in ranked[:limit]]

    def export_csv(self, report: dict = None, filename: str = None) -> str:
        """导出报告为 CSV"""
        if not report:
            report = self._load(os.path.join(self.data_dir, "analytics_report.json"), {})
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["指标", "数值"])
            summary = report.get("summary", {})
            for k, v in summary.items():
                writer.writerow([k, v])
        logger.info(f"CSV 导出完成: {filepath}")
        return filepath


if __name__ == "__main__":
    dash = AnalyticsDashboard()
    report = dash.generate_report("7d")
    print(json.dumps(report, ensure_ascii=False, indent=2))
