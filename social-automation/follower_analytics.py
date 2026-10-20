"""
粉丝分析器 - 粉丝增长、画像、活跃度分析
"""
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

from base import BaseAPIClient, setup_logger, save_json, load_json

logger = setup_logger("follower_analytics")


class JuejinFollowers(BaseAPIClient):
    def get_user_stats(self, user_id: str = "") -> dict:
        url = f"{self.api_base}/user_api/v1/user/get"
        result = self.get(url, params={"user_id": user_id})
        data = result.get("data", {})
        return {"followers": data.get("follower_count", 0), "following": data.get("followee_count", 0), "articles": data.get("post_article_count", 0)}


class ZhihuFollowers(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("access_token", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def get_user_stats(self) -> dict:
        url = f"{self.api_base}/people/me"
        result = self.get(url)
        return {"followers": result.get("follower_count", 0), "following": result.get("following_count", 0), "answers": result.get("answer_count", 0)}


class WeiboFollowers(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("access_token", "")
        if token:
            h["Authorization"] = f"OAuth {token}"
        return h

    def get_user_stats(self, uid: str) -> dict:
        url = f"{self.api_base}/users/show.json"
        result = self.get(url, params={"uid": uid})
        return {"followers": result.get("followers_count", 0), "following": result.get("friends_count", 0), "statuses": result.get("statuses_count", 0)}


class TwitterFollowers(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("bearer_token", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def get_user_stats(self, username: str) -> dict:
        url = f"{self.api_base}/users/by/username/{username}"
        result = self.get(url, params={"user.fields": "public_metrics"})
        metrics = result.get("data", {}).get("public_metrics", {})
        return {"followers": metrics.get("followers_count", 0), "following": metrics.get("following_count", 0), "tweets": metrics.get("tweet_count", 0)}


class FollowerAnalytics:
    """粉丝分析主入口"""

    CLIENTS = {
        "juejin": JuejinFollowers,
        "zhihu": ZhihuFollowers,
        "weibo": WeiboFollowers,
        "twitter": TwitterFollowers,
    }

    def __init__(self, config: dict):
        self.config = config
        self.snapshots: list = load_json("follower_snapshots.json", [])

    def analyze_followers(self, platform: str, days: int = 30, **kwargs) -> dict:
        """
        分析粉丝数据
        platform: 平台名
        days: 分析周期
        **kwargs: 平台特定参数 (user_id, uid, username)
        """
        client = self.CLIENTS.get(platform)
        if not client:
            raise ValueError(f"不支持平台: {platform}")

        pconf = self.config.get(platform, {})
        c = client(platform, pconf)
        current = c.get_user_stats(**{k: v for k, v in kwargs.items() if v})

        snapshot = {"platform": platform, "stats": current, "timestamp": datetime.now().isoformat()}
        self.snapshots.append(snapshot)
        save_json("follower_snapshots.json", self.snapshots)

        growth = self._calc_growth(platform, days)
        report = {
            "platform": platform,
            "current": current,
            "growth": growth,
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
        }
        logger.info(f"[{platform}] 粉丝分析完成: {current}")
        return report

    def _calc_growth(self, platform: str, days: int) -> dict:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        records = [s for s in self.snapshots if s["platform"] == platform and s["timestamp"] >= cutoff]
        if len(records) < 2:
            return {"status": "insufficient_data", "snapshots": len(records)}

        first, last = records[0]["stats"], records[-1]["stats"]
        follower_delta = last.get("followers", 0) - first.get("followers", 0)
        return {
            "follower_delta": follower_delta,
            "first_snapshot": records[0]["timestamp"],
            "last_snapshot": records[-1]["timestamp"],
            "total_snapshots": len(records),
            "avg_daily_growth": round(follower_delta / max(days, 1), 2),
        }

    def compare_platforms(self, platforms: list = None) -> dict:
        """跨平台粉丝对比"""
        targets = platforms or list(self.CLIENTS.keys())
        result = {}
        for p in targets:
            records = [s for s in self.snapshots if s["platform"] == p]
            if records:
                result[p] = records[-1]["stats"]
            else:
                result[p] = {"status": "no_data"}
        return {"compared_at": datetime.now().isoformat(), "platforms": result}

    def activity_analysis(self, platform: str) -> dict:
        """活跃度分析"""
        records = [s for s in self.snapshots if s["platform"] == platform]
        if not records:
            return {"platform": platform, "status": "no_data"}
        return {
            "platform": platform,
            "total_snapshots": len(records),
            "first_record": records[0]["timestamp"],
            "last_record": records[-1]["timestamp"],
            "latest_stats": records[-1]["stats"],
        }


if __name__ == "__main__":
    from config import load_config
    cfg = load_config()
    fa = FollowerAnalytics(cfg)
    print("粉丝分析器就绪。调用 analyze_followers(platform, days) 获取报告。")
