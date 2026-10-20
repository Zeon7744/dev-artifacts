"""
互动追踪器 - 追踪点赞、评论、转发，分析趋势
"""
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional

from base import BaseAPIClient, retry, setup_logger, save_json, load_json

logger = setup_logger("engagement_tracker")


# ── 平台互动采集 ──────────────────────────────────────

class JuejinEngagement(BaseAPIClient):
    def get_article_stats(self, article_id: str) -> dict:
        url = f"{self.api_base}/content_api/v1/article/detail"
        result = self.post(url, json={"article_id": article_id})
        info = result.get("data", {}).get("article_info", {})
        return {
            "likes": int(info.get("digg_count", 0)),
            "comments": int(info.get("comment_count", 0)),
            "views": int(info.get("view_count", 0)),
            "collects": int(info.get("collect_count", 0)),
        }


class ZhihuEngagement(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("access_token", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def get_article_stats(self, article_id: str) -> dict:
        url = f"{self.api_base}/articles/{article_id}"
        result = self.get(url)
        return {
            "likes": result.get("voteup_count", 0),
            "comments": result.get("comment_count", 0),
            "views": result.get("visit_count", 0),
        }


class WeiboEngagement(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("access_token", "")
        if token:
            h["Authorization"] = f"OAuth {token}"
        return h

    def get_post_stats(self, post_id: str) -> dict:
        url = f"{self.api_base}/statuses/show.json"
        result = self.get(url, params={"id": post_id})
        return {
            "likes": result.get("attitudes_count", 0),
            "comments": result.get("comments_count", 0),
            "reposts": result.get("reposts_count", 0),
        }


class TwitterEngagement(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("bearer_token", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def get_tweet_stats(self, tweet_id: str) -> dict:
        url = f"{self.api_base}/tweets/{tweet_id}"
        result = self.get(url, params={"tweet.fields": "public_metrics"})
        metrics = result.get("data", {}).get("public_metrics", {})
        return {
            "likes": metrics.get("like_count", 0),
            "comments": metrics.get("reply_count", 0),
            "reposts": metrics.get("retweet_count", 0),
            "quotes": metrics.get("quote_count", 0),
        }


# ── 核心追踪器 ────────────────────────────────────────

class EngagementTracker:
    """统一互动追踪"""

    CLIENTS = {
        "juejin": JuejinEngagement,
        "zhihu": ZhihuEngagement,
        "weibo": WeiboEngagement,
        "twitter": TwitterEngagement,
    }

    def __init__(self, config: dict):
        self.config = config
        self._clients: Dict[str, BaseAPIClient] = {}
        self.snapshots: list = load_json("engagement_snapshots.json", [])

    def _get_client(self, platform: str) -> BaseAPIClient:
        if platform not in self._clients:
            cls = self.CLIENTS.get(platform)
            if not cls:
                raise ValueError(f"不支持平台: {platform}")
            pconf = self.config.get(platform, {})
            self._clients[platform] = cls(platform, pconf)
        return self._clients[platform]

    def track_engagement(self, post_id: str, platform: str) -> dict:
        """追踪单篇内容互动数据"""
        client = self._get_client(platform)
        if platform == "weibo":
            stats = client.get_post_stats(post_id)
        elif platform == "twitter":
            stats = client.get_tweet_stats(post_id)
        else:
            stats = client.get_article_stats(post_id)

        snapshot = {
            "post_id": post_id,
            "platform": platform,
            "stats": stats,
            "timestamp": datetime.now().isoformat(),
        }
        self.snapshots.append(snapshot)
        save_json("engagement_snapshots.json", self.snapshots)
        logger.info(f"[{platform}] {post_id}: {stats}")
        return snapshot

    def track_multiple(self, posts: list) -> list:
        """批量追踪多条内容"""
        results = []
        for p in posts:
            try:
                r = self.track_engagement(p["post_id"], p["platform"])
                results.append(r)
            except Exception as e:
                logger.error(f"追踪失败 {p}: {e}")
                results.append({"error": str(e), **p})
        return results

    def get_trend(self, post_id: str, platform: str, hours: int = 24) -> dict:
        """分析某条内容的互动趋势"""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        relevant = [
            s for s in self.snapshots
            if s["post_id"] == post_id and s["platform"] == platform and s["timestamp"] >= cutoff
        ]
        if not relevant:
            return {"post_id": post_id, "platform": platform, "trend": "no_data"}

        first, last = relevant[0], relevant[-1]
        delta = {k: last["stats"].get(k, 0) - first["stats"].get(k, 0) for k in last["stats"]}
        return {
            "post_id": post_id,
            "platform": platform,
            "data_points": len(relevant),
            "period_hours": hours,
            "growth": delta,
            "latest": last["stats"],
        }

    def top_content(self, platform: str = None, metric: str = "likes", limit: int = 10) -> list:
        """识别高互动内容"""
        filtered = self.snapshots
        if platform:
            filtered = [s for s in filtered if s["platform"] == platform]
        # 取每个 post_id 最新快照
        latest: Dict[str, dict] = {}
        for s in sorted(filtered, key=lambda x: x["timestamp"]):
            key = f"{s['platform']}:{s['post_id']}"
            latest[key] = s
        ranked = sorted(latest.values(), key=lambda s: s["stats"].get(metric, 0), reverse=True)
        return ranked[:limit]

    def generate_report(self, days: int = 7, platforms: list = None) -> dict:
        """生成互动报告"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        data = [s for s in self.snapshots if s["timestamp"] >= cutoff]
        if platforms:
            data = [s for s in data if s["platform"] in platforms]

        by_platform = defaultdict(lambda: {"posts": set(), "total_likes": 0, "total_comments": 0, "total_reposts": 0, "total_views": 0})
        for s in data:
            p = by_platform[s["platform"]]
            p["posts"].add(s["post_id"])
            p["total_likes"] += s["stats"].get("likes", 0)
            p["total_comments"] += s["stats"].get("comments", 0)
            p["total_reposts"] += s["stats"].get("reposts", 0)
            p["total_views"] += s["stats"].get("views", 0)

        summary = {}
        for plat, stats in by_platform.items():
            summary[plat] = {
                "posts_tracked": len(stats["posts"]),
                "total_likes": stats["total_likes"],
                "total_comments": stats["total_comments"],
                "total_reposts": stats["total_reposts"],
                "total_views": stats["total_views"],
            }

        report = {
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "platforms": summary,
            "top_liked": self.top_content(metric="likes", limit=5),
        }
        save_json("engagement_report.json", report)
        return report


if __name__ == "__main__":
    from config import load_config
    cfg = load_config()
    tracker = EngagementTracker(cfg)
    print("互动追踪器就绪。通过代码调用 track_engagement() 或 generate_report()。")
