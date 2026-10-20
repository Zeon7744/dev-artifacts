"""
内容发布器 - 多平台统一发布接口
支持平台: 掘金、知乎、微博、Twitter/X
"""
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from base import BaseAPIClient, retry, setup_logger, save_json, load_json

logger = setup_logger("content_poster")


# ── 平台适配器 ────────────────────────────────────────

class JuejinClient(BaseAPIClient):
    """掘金内容发布"""

    def _headers(self):
        h = super()._headers()
        cookie = self.config.get("credentials", {}).get("cookie", "")
        if cookie:
            h["Cookie"] = cookie
        return h

    def publish_article(self, title: str, content: str, tags: list = None, category: str = "") -> dict:
        """发布文章到掘金"""
        url = f"{self.api_base}/content_api/v1/article/publish"
        payload = {
            "title": title,
            "mark_content": content,
            "category_id": self._resolve_category(category),
            "tag_ids": tags or [],
            "brief": content[:100],
        }
        result = self.post(url, json=payload)
        logger.info(f"掘金文章已发布: {title}")
        return {"platform": "juejin", "title": title, "response": result, "timestamp": datetime.now().isoformat()}

    @staticmethod
    def _resolve_category(name: str) -> str:
        cats = {"后端": "6809637769959178254", "前端": "6809637767543250954", "AI": "6809637773935419400"}
        return cats.get(name, "6809637769959178254")


class ZhihuClient(BaseAPIClient):
    """知乎内容发布"""

    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("access_token", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def publish_article(self, title: str, content: str, topic_ids: list = None) -> dict:
        """发布知乎文章"""
        url = f"{self.api_base}/articles"
        payload = {
            "title": title,
            "content": content,
            "delta_time": 0,
        }
        if topic_ids:
            payload["topic_url_tokens"] = topic_ids
        result = self.post(url, json=payload)
        logger.info(f"知乎文章已发布: {title}")
        return {"platform": "zhihu", "title": title, "response": result, "timestamp": datetime.now().isoformat()}

    def publish_answer(self, question_id: str, content: str) -> dict:
        """回答知乎问题"""
        url = f"{self.api_base}/questions/{question_id}/answers"
        result = self.post(url, json={"content": content})
        return {"platform": "zhihu", "question_id": question_id, "response": result}


class WeiboClient(BaseAPIClient):
    """微博内容发布"""

    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("access_token", "")
        if token:
            h["Authorization"] = f"OAuth {token}"
        return h

    def post_status(self, text: str, image_url: str = None) -> dict:
        """发布微博"""
        url = f"{self.api_base}/statuses/share.json"
        data = {"status": text}
        if image_url:
            data["pic"] = image_url
        result = self.post(url, data=data)
        logger.info(f"微博已发布: {text[:30]}...")
        return {"platform": "weibo", "text_preview": text[:50], "response": result, "timestamp": datetime.now().isoformat()}


class TwitterClient(BaseAPIClient):
    """Twitter/X 内容发布"""

    def _headers(self):
        h = super()._headers()
        creds = self.config.get("credentials", {})
        token = creds.get("bearer_token") or creds.get("access_token", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def post_tweet(self, text: str, reply_to: str = None) -> dict:
        """发推"""
        url = f"{self.api_base}/tweets"
        payload = {"text": text[:280]}
        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}
        result = self.post(url, json=payload)
        logger.info(f"推文已发布: {text[:30]}...")
        return {"platform": "twitter", "text_preview": text[:50], "response": result, "timestamp": datetime.now().isoformat()}


# ── 内容格式化 ────────────────────────────────────────

class ContentFormatter:
    """多平台内容适配"""

    @staticmethod
    def for_juejin(content: dict) -> dict:
        return {
            "title": content.get("title", ""),
            "content": content.get("body", content.get("content", "")),
            "tags": content.get("hashtags", []),
            "category": content.get("category", ""),
        }

    @staticmethod
    def for_zhihu(content: dict) -> dict:
        return {
            "title": content.get("title", ""),
            "content": content.get("body", content.get("content", "")),
            "topic_ids": content.get("topic_ids", []),
        }

    @staticmethod
    def for_weibo(content: dict) -> dict:
        text = content.get("body", content.get("content", ""))
        hashtags = content.get("hashtags", [])
        tag_str = " ".join(f"#{t}#" for t in hashtags[:5])
        full = f"{tag_str} {text}" if tag_str else text
        return {"text": full[:2000], "image_url": content.get("image_url")}

    @staticmethod
    def for_twitter(content: dict) -> dict:
        text = content.get("body", content.get("content", ""))
        hashtags = content.get("hashtags", [])
        tag_str = " ".join(f"#{t}" for t in hashtags[:3])
        full = f"{text}\n\n{tag_str}" if tag_str else text
        return {"text": full[:280]}


# ── 发布调度器 ────────────────────────────────────────

class ContentPoster:
    """统一内容发布入口"""

    PLATFORM_MAP = {
        "juejin": JuejinClient,
        "zhihu": ZhihuClient,
        "weibo": WeiboClient,
        "twitter": TwitterClient,
    }

    def __init__(self, config: dict):
        self.config = config
        self.formatter = ContentFormatter()
        self.history: list = load_json("post_history.json", [])
        self._clients: Dict[str, BaseAPIClient] = {}

    def _get_client(self, platform: str) -> BaseAPIClient:
        if platform not in self._clients:
            cls = self.PLATFORM_MAP.get(platform)
            if not cls:
                raise ValueError(f"不支持的平台: {platform}，可选: {list(self.PLATFORM_MAP.keys())}")
            pconf = self.config.get(platform, {})
            if not pconf.get("enabled", False):
                raise ValueError(f"平台 {platform} 未启用")
            self._clients[platform] = cls(platform, pconf)
        return self._clients[platform]

    # ── 核心接口 ─────────────────────────────────────
    def post_to_platform(self, platform: str, content: dict, schedule_time: str = None) -> dict:
        """
        统一发布接口
        platform:     目标平台名
        content:      内容字典 {title, body, hashtags, image_url, ...}
        schedule_time: ISO格式时间字符串，None则立即发布
        """
        if schedule_time:
            return self._schedule(platform, content, schedule_time)
        return self._publish_now(platform, content)

    def post_to_all(self, content: dict, platforms: list = None, schedule_time: str = None) -> list:
        """批量发布到多个平台"""
        targets = platforms or list(self.PLATFORM_MAP.keys())
        results = []
        for p in targets:
            try:
                r = self.post_to_platform(p, content, schedule_time)
                results.append(r)
            except Exception as e:
                logger.error(f"发布到 {p} 失败: {e}")
                results.append({"platform": p, "status": "error", "error": str(e)})
        self._save_history(results)
        return results

    # ── 内部方法 ──────────────────────────────────────
    def _publish_now(self, platform: str, content: dict) -> dict:
        client = self._get_client(platform)
        if platform == "juejin":
            fmt = self.formatter.for_juejin(content)
            return client.publish_article(**fmt)
        elif platform == "zhihu":
            fmt = self.formatter.for_zhihu(content)
            return client.publish_article(**fmt)
        elif platform == "weibo":
            fmt = self.formatter.for_weibo(content)
            return client.post_status(**fmt)
        elif platform == "twitter":
            fmt = self.formatter.for_twitter(content)
            return client.post_tweet(**fmt)

    def _schedule(self, platform: str, content: dict, schedule_time: str) -> dict:
        scheduled = load_json("scheduled_posts.json", [])
        entry = {
            "platform": platform,
            "content": content,
            "scheduled_time": schedule_time,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
        scheduled.append(entry)
        save_json("scheduled_posts.json", scheduled)
        logger.info(f"已排期到 {platform} @ {schedule_time}")
        return {"platform": platform, "status": "scheduled", "scheduled_time": schedule_time}

    def _save_history(self, results: list):
        self.history.extend(results)
        save_json("post_history.json", self.history)

    def get_post_history(self, limit: int = 20) -> list:
        return self.history[-limit:]

    def get_scheduled_posts(self) -> list:
        return load_json("scheduled_posts.json", [])

    def execute_scheduled(self) -> list:
        """执行所有到期定时发布"""
        scheduled = self.get_scheduled_posts()
        now = datetime.now().isoformat()
        executed = []
        remaining = []
        for entry in scheduled:
            if entry["status"] == "pending" and entry["scheduled_time"] <= now:
                try:
                    r = self._publish_now(entry["platform"], entry["content"])
                    entry["status"] = "published"
                    executed.append(r)
                except Exception as e:
                    entry["status"] = "failed"
                    logger.error(f"定时发布失败: {e}")
            else:
                remaining.append(entry)
        save_json("scheduled_posts.json", remaining)
        return executed


# ── CLI 入口 ──────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from config import load_config
    cfg = load_config()
    poster = ContentPoster(cfg)

    if len(sys.argv) > 1 and sys.argv[1] == "run_scheduled":
        results = poster.execute_scheduled()
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "history":
        print(json.dumps(poster.get_post_history(), ensure_ascii=False, indent=2))
    else:
        print("用法: python content_poster.py [run_scheduled|history]")
        print("或在代码中调用: poster.post_to_platform('twitter', {'body': 'Hello'})")
