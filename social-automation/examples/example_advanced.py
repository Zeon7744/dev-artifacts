"""
使用示例 - 自动回复、标签研究、GitHub 推广
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import load_config
from auto_responder import AutoResponder
from hashtag_research import HashtagResearch
from github_promoter import GitHubPromoter
from post_scheduler import PostScheduler
from follower_analytics import FollowerAnalytics

config = load_config()

# ═══════════════════════════════════════════════════════
# 自动回复
# ═══════════════════════════════════════════════════════
responder = AutoResponder(config)

# 配置规则
responder.add_rule("多少钱", "具体定价请查看我们的官网哦~", platform="all")
responder.add_rule("合作", "欢迎合作！请私信联系详谈 🤝", platform="all", priority=10)

# 配置 FAQ
responder.add_faq("项目用什么语言", "主要使用 Python，部分模块有 TypeScript 版本。")
responder.add_faq("怎么贡献代码", "Fork 仓库后提交 PR 即可，详见 CONTRIBUTING.md。")

# 处理评论
# result = responder.respond_to_comment("c_123", "这个项目多少钱？", platform="weibo")
# batch_result = responder.process_comments_batch(
#     [{"id": "c_1", "text": "怎么合作"}, {"id": "c_2", "text": "好项目"}],
#     platform="weibo"
# )

# ═══════════════════════════════════════════════════════
# 标签研究
# ═══════════════════════════════════════════════════════
researcher = HashtagResearch(config)

# 研究某主题的热门标签
# tags = researcher.research_hashtags("AI短剧", "weibo")
# print(f"推荐标签: {[t['name'] for t in tags['recommended']]}")
# print(f"组合建议: {tags['combinations']}")

# 批量研究
# batch = researcher.batch_research(["AI短剧", "AIGC", "开源"], platforms=["juejin", "twitter"])

# ═══════════════════════════════════════════════════════
# GitHub 推广
# ═══════════════════════════════════════════════════════
promoter = GitHubPromoter(config)

# 推广最新 Release
# promo = promoter.promote_release("Zeon7744/dev-artifacts")
# for platform, text in promo["promo_content"].items():
#     print(f"\n--- {platform} ---\n{text}")

# 感谢贡献者
# thanks = promoter.thank_contributors("Zeon7744/dev-artifacts")

# 响应 Issues
# responses = promoter.respond_to_issues("Zeon7744/dev-artifacts")

# ═══════════════════════════════════════════════════════
# 定时发布
# ═══════════════════════════════════════════════════════
scheduler = PostScheduler()

# 查看建议时间
# times = scheduler.suggest_best_time("juejin", days_ahead=3)
# for t in times:
#     print(f"{t['weekday']} {t['time']} ({t['day_type']})")

# 排期发布
# scheduler.schedule_post({"body": "新功能上线！"}, "weibo", "2026-01-15T12:00:00")

# ═══════════════════════════════════════════════════════
# 粉丝分析
# ═══════════════════════════════════════════════════════
analytics = FollowerAnalytics(config)

# 分析粉丝增长
# report = analytics.analyze_followers("juejin", days=30, user_id="your_user_id")
# print(f"粉丝变化: {report['growth']}")

# 跨平台对比
# comparison = analytics.compare_platforms()

print("所有示例加载完成，取消注释以执行实际操作。")
