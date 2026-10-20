"""
自动回复器 - 评论区自动回复、关键词触发、FAQ 自动回答
"""
import re
import json
from datetime import datetime
from typing import Dict, List, Callable, Optional

from base import BaseAPIClient, setup_logger, save_json, load_json

logger = setup_logger("auto_responder")


class WeiboReply(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("access_token", "")
        if token:
            h["Authorization"] = f"OAuth {token}"
        return h

    def reply_comment(self, comment_id: str, text: str) -> dict:
        url = f"{self.api_base}/comments/reply.json"
        return self.post(url, data={"cid": comment_id, "comment": text})

    def get_comments(self, post_id: str, page: int = 1) -> list:
        url = f"{self.api_base}/comments/show.json"
        result = self.get(url, params={"id": post_id, "page": page})
        return result.get("comments", [])


class TwitterReply(BaseAPIClient):
    def _headers(self):
        h = super()._headers()
        token = self.config.get("credentials", {}).get("bearer_token", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def reply_tweet(self, tweet_id: str, text: str) -> dict:
        url = f"{self.api_base}/tweets"
        return self.post(url, json={"text": text, "reply": {"in_reply_to_tweet_id": tweet_id}})

    def get_mentions(self, since_id: str = None) -> list:
        url = f"{self.api_base}/users/me/mentions"
        params = {"tweet.fields": "created_at,author_id"}
        if since_id:
            params["since_id"] = since_id
        result = self.get(url, params=params)
        return result.get("data", [])


class AutoResponder:
    """自动回复管理器"""

    def __init__(self, config: dict):
        self.config = config
        self.rules: list = load_json("reply_rules.json", [])
        self.faq: dict = load_json("faq_database.json", {})
        self.reply_log: list = load_json("reply_log.json", [])
        self.stats = {"total_replies": 0, "by_platform": {}, "by_rule": {}}

    # ── 规则管理 ──────────────────────────────────────
    def add_rule(self, keyword: str, response: str, platform: str = "all", priority: int = 0) -> dict:
        """添加关键词触发规则"""
        rule = {
            "id": f"rule_{len(self.rules) + 1}",
            "keyword": keyword,
            "response": response,
            "platform": platform,
            "priority": priority,
            "enabled": True,
            "created_at": datetime.now().isoformat(),
        }
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r["priority"], reverse=True)
        save_json("reply_rules.json", self.rules)
        return rule

    def remove_rule(self, rule_id: str):
        self.rules = [r for r in self.rules if r["id"] != rule_id]
        save_json("reply_rules.json", self.rules)

    def add_faq(self, question: str, answer: str):
        """添加 FAQ"""
        self.faq[question.lower()] = answer
        save_json("faq_database.json", self.faq)

    # ── 核心接口 ──────────────────────────────────────
    def respond_to_comment(self, comment_id: str, content: str, platform: str = "weibo") -> dict:
        """
        对评论进行自动回复
        comment_id: 评论 ID
        content: 评论文本
        platform: 平台
        """
        # 1. 匹配关键词规则
        matched_rule = self._match_rule(content, platform)
        if matched_rule:
            response_text = matched_rule["response"]
            source = "rule"
        # 2. 匹配 FAQ
        else:
            faq_answer = self._match_faq(content)
            if faq_answer:
                response_text = faq_answer
                source = "faq"
            else:
                logger.info(f"无匹配规则，跳过评论: {content[:50]}")
                return {"status": "skipped", "reason": "no_match"}

        # 3. 发送回复
        try:
            self._send_reply(platform, comment_id, response_text)
            log_entry = {
                "comment_id": comment_id,
                "platform": platform,
                "original": content[:100],
                "response": response_text[:100],
                "source": source,
                "timestamp": datetime.now().isoformat(),
            }
            self.reply_log.append(log_entry)
            save_json("reply_log.json", self.reply_log)
            self.stats["total_replies"] += 1
            self.stats["by_platform"][platform] = self.stats["by_platform"].get(platform, 0) + 1
            logger.info(f"[{platform}] 已回复 {comment_id}: {response_text[:30]}...")
            return {"status": "replied", "source": source, "response": response_text}
        except Exception as e:
            logger.error(f"回复失败: {e}")
            return {"status": "error", "error": str(e)}

    def process_comments_batch(self, comments: list, platform: str) -> dict:
        """批量处理评论"""
        results = {"replied": 0, "skipped": 0, "errors": 0}
        for c in comments:
            cid = c.get("id", c.get("comment_id", ""))
            text = c.get("text", c.get("content", ""))
            r = self.respond_to_comment(cid, text, platform)
            if r["status"] == "replied":
                results["replied"] += 1
            elif r["status"] == "skipped":
                results["skipped"] += 1
            else:
                results["errors"] += 1
        return results

    # ── 内部方法 ──────────────────────────────────────
    def _match_rule(self, text: str, platform: str) -> Optional[dict]:
        text_lower = text.lower()
        for rule in self.rules:
            if not rule["enabled"]:
                continue
            if rule["platform"] != "all" and rule["platform"] != platform:
                continue
            if rule["keyword"].lower() in text_lower:
                return rule
        return None

    def _match_faq(self, text: str) -> Optional[str]:
        text_lower = text.lower().strip().rstrip("？?")
        # 精确匹配
        if text_lower in self.faq:
            return self.faq[text_lower]
        # 模糊匹配
        for q, a in self.faq.items():
            if q in text_lower or text_lower in q:
                return a
        return None

    def _send_reply(self, platform: str, comment_id: str, text: str):
        if platform == "weibo":
            client = WeiboReply("weibo", self.config.get("weibo", {}))
            client.reply_comment(comment_id, text)
        elif platform == "twitter":
            client = TwitterReply("twitter", self.config.get("twitter", {}))
            client.reply_tweet(comment_id, text)
        else:
            logger.warning(f"平台 {platform} 暂不支持自动回复")

    def get_quality_report(self) -> dict:
        """回复质量报告"""
        return {
            "total_replies": self.stats["total_replies"],
            "by_platform": self.stats["by_platform"],
            "total_rules": len(self.rules),
            "total_faq": len(self.faq),
            "recent_log": self.reply_log[-20:],
        }


if __name__ == "__main__":
    from config import load_config
    cfg = load_config()
    ar = AutoResponder(cfg)
    ar.add_rule("价格", "请关注我们的官网获取最新定价信息~")
    ar.add_faq("怎么联系你", "可以通过评论区留言或私信联系我们！")
    print("自动回复器就绪。调用 respond_to_comment(comment_id, content, platform) 开始回复。")
