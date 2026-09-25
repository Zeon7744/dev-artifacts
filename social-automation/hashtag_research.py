"""
标签研究器 - 热门标签发现、推荐、组合建议
"""
import json
from datetime import datetime
from collections import Counter
from typing import List, Dict

from base import BaseAPIClient, setup_logger, save_json, load_json, retry

logger = setup_logger("hashtag_research")


class JuejinTags(BaseAPIClient):
    def get_hot_tags(self, category_id: str = "") -> list:
        url = f"{self.api_base}/tag_api/v1/query_hot_tag"
        result = self.post(url, json={"category_id": category_id})
        return [{"name": t.get("tag_name"), "id": t.get("id"), "count": t.get("on_article_count", 0)}
                for t in result.get("data", [])]


class ZhihuTags(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("access_token", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def search_topics(self, query: str) -> list:
        url = f"{self.api_base}/search_v3"
        result = self.get(url, params={"q": query, "t": "topic"})
        return [{"name": t.get("name"), "id": t.get("id"), "followers": t.get("follower_count", 0)}
                for t in result.get("data", [])]


class WeiboTags(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("access_token", "")
        if token:
            h["Authorization"] = f"OAuth {token}"
        return h

    def get_hot_search(self) -> list:
        url = f"{self.api_base}/search/hot.json"
        result = self.get(url)
        return [{"name": t.get("word", ""), "hot_score": t.get("num", 0)}
                for t in result.get("data", {}).get("hots", [])]


class TwitterTags(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("bearer_token", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def get_trends(self, woeid: int = 1) -> list:
        url = f"https://api.twitter.com/1.1/trends/place.json"
        result = self.get(url, params={"id": woeid})
        if isinstance(result, list) and result:
            return [{"name": t.get("name"), "volume": t.get("tweet_volume", 0)}
                    for t in result[0].get("trends", [])]
        return []


class HashtagResearch:
    """标签研究主入口"""

    CLIENTS = {
        "juejin": JuejinTags,
        "zhihu": ZhihuTags,
        "weibo": WeiboTags,
        "twitter": TwitterTags,
    }

    def __init__(self, config: dict):
        self.config = config

    def research_hashtags(self, topic: str, platform: str) -> dict:
        """
        研究标签
        topic: 主题/关键词
        platform: 目标平台
        """
        client_cls = self.CLIENTS.get(platform)
        if not client_cls:
            raise ValueError(f"不支持平台: {platform}，可选: {list(self.CLIENTS.keys())}")

        pconf = self.config.get(platform, {})
        client = client_cls(platform, pconf)

        if platform == "juejin":
            tags = client.get_hot_tags()
        elif platform == "zhihu":
            tags = client.search_topics(topic)
        elif platform == "weibo":
            tags = client.get_hot_search()
        elif platform == "twitter":
            tags = client.get_trends()
        else:
            tags = []

        recommendations = self._recommend(tags, topic)
        combinations = self._suggest_combinations(recommendations)

        result = {
            "topic": topic,
            "platform": platform,
            "raw_tags": tags[:20],
            "recommended": recommendations,
            "combinations": combinations,
            "generated_at": datetime.now().isoformat(),
        }
        logger.info(f"[{platform}] 标签研究完成: {topic} -> {len(recommendations)} 推荐")
        return result

    def _recommend(self, tags: list, topic: str) -> list:
        """基于关键词筛选和排序标签"""
        topic_lower = topic.lower()
        scored = []
        for t in tags:
            name = t.get("name", "").lower()
            count = t.get("count", t.get("hot_score", t.get("volume", t.get("followers", 0))))
            relevance = 2 if topic_lower in name else 1
            score = count * relevance
            scored.append({**t, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:10]

    def _suggest_combinations(self, tags: list) -> list:
        """建议标签组合"""
        if not tags:
            return []
        combos = []
        # 高热 + 中热 + 垂直
        for i in range(min(3, len(tags))):
            combo = [tags[i]["name"]]
            for j in range(len(tags)):
                if i != j and len(combo) < 3:
                    combo.append(tags[j]["name"])
            if len(combo) >= 2:
                combos.append({"tags": combo, "strategy": "high_heat_mix"})
        return combos[:5]

    def batch_research(self, topics: list, platforms: list = None) -> dict:
        """批量研究多个主题的标签"""
        targets = platforms or list(self.CLIENTS.keys())
        results = {}
        for t in topics:
            results[t] = {}
            for p in targets:
                try:
                    results[t][p] = self.research_hashtags(t, p)
                except Exception as e:
                    logger.error(f"标签研究失败 {t}/{p}: {e}")
                    results[t][p] = {"error": str(e)}
        return results


if __name__ == "__main__":
    from config import load_config
    cfg = load_config()
    hr = HashtagResearch(cfg)
    print("标签研究器就绪。调用 research_hashtags(topic, platform) 获取推荐。")
