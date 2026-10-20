"""
社交自动化工具集 - 单元测试
"""
import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from base import RateLimiter, setup_logger, save_json, load_json
from content_poster import ContentPoster, ContentFormatter
from engagement_tracker import EngagementTracker
from follower_analytics import FollowerAnalytics
from hashtag_research import HashtagResearch
from post_scheduler import PostScheduler, BEST_POSTING_TIMES
from auto_responder import AutoResponder
from analytics_dashboard import AnalyticsDashboard
from github_promoter import GitHubPromoter, GitHubClient


class TestBase(unittest.TestCase):
    def test_rate_limiter(self):
        rl = RateLimiter(calls_per_minute=600)
        rl.wait()
        rl.wait()  # 第二次应几乎无延迟

    def test_logger(self):
        logger = setup_logger("test", "DEBUG")
        self.assertEqual(logger.name, "test")

    def test_save_load_json(self):
        data = {"key": "value", "list": [1, 2, 3]}
        save_json("test_temp.json", data)
        loaded = load_json("test_temp.json")
        self.assertEqual(loaded["key"], "value")
        os.remove("data/test_temp.json")

    def test_load_json_default(self):
        result = load_json("nonexistent.json", default={"empty": True})
        self.assertTrue(result["empty"])


class TestContentFormatter(unittest.TestCase):
    def test_for_juejin(self):
        content = {"title": "Test", "body": "Hello world", "hashtags": ["AI"], "category": "AI"}
        result = ContentFormatter.for_juejin(content)
        self.assertEqual(result["title"], "Test")
        self.assertEqual(result["tags"], ["AI"])

    def test_for_weibo(self):
        content = {"body": "Test content", "hashtags": ["AI", "code"]}
        result = ContentFormatter.for_weibo(content)
        self.assertIn("#AI#", result["text"])
        self.assertIn("#code#", result["text"])

    def test_for_twitter(self):
        content = {"body": "Short text", "hashtags": ["AI", "dev", "code", "extra"]}
        result = ContentFormatter.for_twitter(content)
        self.assertLessEqual(len(result["text"]), 280)
        # 只取前3个 hashtag
        self.assertIn("#AI", result["text"])
        self.assertNotIn("#extra", result["text"])


class TestContentPoster(unittest.TestCase):
    def setUp(self):
        self.config = {
            "juejin": {"enabled": True, "api_base": "https://api.juejin.cn", "credentials": {}, "rate_limit": 5},
            "twitter": {"enabled": True, "api_base": "https://api.twitter.com/2", "credentials": {}, "rate_limit": 5},
        }
        self.poster = ContentPoster(self.config)

    def test_unsupported_platform(self):
        with self.assertRaises(ValueError):
            self.poster.post_to_platform("unknown_platform", {"body": "test"})

    def test_schedule_post(self):
        result = self.poster.post_to_platform("juejin", {"body": "test"}, schedule_time="2030-01-01T00:00:00")
        self.assertEqual(result["status"], "scheduled")

    def test_get_scheduled_posts(self):
        self.poster.post_to_platform("juejin", {"body": "test2"}, schedule_time="2030-06-01T00:00:00")
        posts = self.poster.get_scheduled_posts()
        self.assertGreater(len(posts), 0)


class TestAutoResponder(unittest.TestCase):
    def setUp(self):
        self.config = {"weibo": {"enabled": True}, "twitter": {"enabled": True}}
        self.responder = AutoResponder(self.config)

    def test_add_rule(self):
        rule = self.responder.add_rule("测试关键词", "测试回复", platform="weibo")
        self.assertEqual(rule["keyword"], "测试关键词")
        self.assertTrue(rule["enabled"])

    def test_match_rule(self):
        self.responder.add_rule("价格", "请查看官网", platform="all")
        matched = self.responder._match_rule("这个价格是多少？", "weibo")
        self.assertIsNotNone(matched)
        self.assertEqual(matched["response"], "请查看官网")

    def test_match_rule_no_match(self):
        self.responder.rules = []
        matched = self.responder._match_rule("随便聊聊", "weibo")
        self.assertIsNone(matched)

    def test_add_faq(self):
        self.responder.add_faq("怎么安装", "pip install xxx")
        self.assertIn("怎么安装", self.responder.faq)

    def test_match_faq(self):
        self.responder.add_faq("支持哪些语言", "Python 和 TypeScript")
        answer = self.responder._match_faq("你们支持哪些语言？")
        self.assertEqual(answer, "Python 和 TypeScript")

    def test_priority_ordering(self):
        self.responder.add_rule("test", "low", priority=1)
        self.responder.add_rule("test", "high", priority=10)
        self.assertEqual(self.responder.rules[0]["priority"], 10)


class TestPostScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = PostScheduler()

    def test_schedule_post(self):
        entry = self.scheduler.schedule_post({"body": "test"}, "weibo", "2030-01-01T10:00:00")
        self.assertEqual(entry["status"], "pending")
        self.assertIn("id", entry)

    def test_suggest_best_time(self):
        times = self.scheduler.suggest_best_time("juejin", days_ahead=3)
        self.assertGreater(len(times), 0)
        self.assertIn("datetime", times[0])

    def test_cancel_schedule(self):
        entry = self.scheduler.schedule_post({"body": "cancel me"}, "weibo", "2030-01-01T10:00:00")
        result = self.scheduler.cancel_schedule(entry["id"])
        self.assertEqual(result["status"], "cancelled")

    def test_best_times_exist(self):
        for platform in ["juejin", "zhihu", "weibo", "twitter"]:
            self.assertIn(platform, BEST_POSTING_TIMES)


class TestAnalyticsDashboard(unittest.TestCase):
    def setUp(self):
        self.dashboard = AnalyticsDashboard(data_dir="./data")

    def test_generate_empty_report(self):
        report = self.dashboard.generate_report("7d")
        self.assertIn("report_id", report)
        self.assertIn("summary", report)
        self.assertIn("period", report)

    def test_export_csv(self):
        report = self.dashboard.generate_report("7d")
        csv_path = self.dashboard.export_csv(report, filename="test_export.csv")
        self.assertTrue(os.path.exists(csv_path))
        os.remove(csv_path)


class TestGitHubPromoter(unittest.TestCase):
    def test_generate_promo_content(self):
        config = {"github": {"enabled": True, "api_base": "https://api.github.com", "credentials": {"token": ""}, "rate_limit": 30}}
        promoter = GitHubPromoter(config)
        release_info = {"tag": "v1.0.0", "name": "First Release", "body": "Initial release", "url": "https://github.com/test/repo/releases/v1.0.0"}
        promo = promoter._generate_release_promo("test", "repo", release_info)
        self.assertIn("twitter", promo)
        self.assertIn("weibo", promo)
        self.assertIn("v1.0.0", promo["twitter"])


class TestEngagementTracker(unittest.TestCase):
    def test_init(self):
        config = {"juejin": {"enabled": True, "api_base": "", "credentials": {}, "rate_limit": 5}}
        tracker = EngagementTracker(config)
        self.assertIsNotNone(tracker)


class TestFollowerAnalytics(unittest.TestCase):
    def test_init(self):
        config = {"juejin": {"enabled": True, "api_base": "", "credentials": {}, "rate_limit": 5}}
        fa = FollowerAnalytics(config)
        self.assertIsNotNone(fa)


class TestHashtagResearch(unittest.TestCase):
    def test_recommend(self):
        config = {}
        hr = HashtagResearch(config)
        tags = [{"name": "AI短剧", "count": 100}, {"name": "Python", "count": 500}, {"name": "AI工具", "count": 200}]
        recommended = hr._recommend(tags, "AI")
        # AI短剧 relevance=2 -> score=200, Python relevance=1 -> score=500, AI工具 relevance=2 -> score=400
        # 按 score 降序: Python(500) > AI工具(400) > AI短剧(200)
        self.assertEqual(recommended[0]["name"], "Python")

    def test_suggest_combinations(self):
        config = {}
        hr = HashtagResearch(config)
        tags = [{"name": "AI", "score": 100}, {"name": "Python", "score": 80}, {"name": "Code", "score": 60}]
        combos = hr._suggest_combinations(tags)
        self.assertGreater(len(combos), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
