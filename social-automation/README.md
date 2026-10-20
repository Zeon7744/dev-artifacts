# 社交自动化工具集 (Social Automation Toolkit)

> 为开发项目打造的一站式社交媒体推广与运营工具集。

## 目录结构

```
social-automation/
├── config/
│   ├── __init__.py          # 配置包
│   └── platforms.json       # 平台配置（API 密钥、限流等）
├── base.py                  # 公共基础模块（HTTP客户端、重试、限流、日志）
├── content_poster.py        # 内容发布器
├── engagement_tracker.py    # 互动追踪器
├── follower_analytics.py    # 粉丝分析器
├── hashtag_research.py      # 标签研究器
├── post_scheduler.py        # 定时发布器
├── auto_responder.py        # 自动回复器
├── analytics_dashboard.py   # 数据分析面板
├── github_promoter.py       # GitHub 推广器
├── examples/
│   ├── example_posting.py   # 发布示例
│   ├── example_analytics.py # 分析示例
│   └── example_advanced.py  # 高级功能示例
├── tests/
│   └── test_automation.py   # 单元测试
├── data/                    # 运行时数据（自动生成）
└── README.md                # 本文件
```

## 快速开始

### 1. 配置平台凭证

编辑 `config/platforms.json`，填入各平台的 API 凭证：

```json
{
  "juejin": {
    "enabled": true,
    "credentials": { "cookie": "你的掘金 Cookie" }
  },
  "twitter": {
    "enabled": true,
    "credentials": { "bearer_token": "你的 Twitter Bearer Token" }
  },
  "github": {
    "enabled": true,
    "credentials": { "token": "ghp_xxxx" }
  }
}
```

### 2. 基本使用

```python
from config import load_config
from content_poster import ContentPoster
from auto_responder import AutoResponder
from analytics_dashboard import AnalyticsDashboard

config = load_config()

# 发布内容
poster = ContentPoster(config)
poster.post_to_platform("juejin", {
    "title": "我的新项目",
    "body": "这是一个很酷的项目...",
    "hashtags": ["开源", "AI"],
})

# 一键多平台发布
poster.post_to_all({"body": "新版本发布！"}, platforms=["weibo", "twitter"])

# 生成分析报告
dashboard = AnalyticsDashboard()
report = dashboard.generate_report("7d")
```

## 模块详解

### 1. Content Poster（内容发布器）

多平台统一发布，自动适配格式。

```python
# 接口
poster.post_to_platform(platform, content, schedule_time=None)
poster.post_to_all(content, platforms=None, schedule_time=None)
poster.execute_scheduled()  # 执行到期发布
```

**支持平台**: 掘金、知乎、微博、Twitter/X

**内容格式化**: 自动处理各平台字数限制、标签格式（#标签# vs #标签）、图片适配。

### 2. Engagement Tracker（互动追踪器）

追踪点赞、评论、转发，分析趋势。

```python
tracker = EngagementTracker(config)

# 追踪单条
stats = tracker.track_engagement("post_123", "juejin")

# 分析趋势
trend = tracker.get_trend("post_123", "juejin", hours=48)

# 找高互动内容
top = tracker.top_content(metric="likes", limit=5)

# 生成报告
report = tracker.generate_report(days=7)
```

### 3. Follower Analytics（粉丝分析器）

粉丝增长统计、画像分析、跨平台对比。

```python
fa = FollowerAnalytics(config)

# 分析粉丝
report = fa.analyze_followers("juejin", days=30, user_id="xxx")

# 跨平台对比
comparison = fa.compare_platforms(["juejin", "twitter"])
```

### 4. Hashtag Research（标签研究器）

热门标签发现、推荐、组合建议。

```python
hr = HashtagResearch(config)

# 研究标签
result = hr.research_hashtags("AI短剧", "weibo")
# result["recommended"] → 推荐标签列表
# result["combinations"] → 组合建议

# 批量研究
batch = hr.batch_research(["AI", "开源"], platforms=["juejin", "twitter"])
```

### 5. Post Scheduler（定时发布器）

内容日历管理、最佳时间建议。

```python
scheduler = PostScheduler()

# 查看建议发布时间
times = scheduler.suggest_best_time("juejin", days_ahead=7)

# 排期
scheduler.schedule_post({"body": "内容"}, "weibo", "2026-01-15T12:00:00")

# 查看日历
calendar = scheduler.get_calendar(days_ahead=30)
```

### 6. Auto Responder（自动回复器）

关键词触发回复、FAQ 自动回答。

```python
responder = AutoResponder(config)

# 配置规则
responder.add_rule("价格", "请查看官网定价~", platform="all")
responder.add_faq("怎么安装", "pip install xxx")

# 自动回复
responder.respond_to_comment("c_123", "这个多少钱？", platform="weibo")

# 批量处理
responder.process_comments_batch(comments_list, platform="weibo")
```

### 7. Analytics Dashboard（数据分析面板）

统一数据看板、趋势分析、CSV 导出。

```python
dashboard = AnalyticsDashboard()

# 生成综合报告
report = dashboard.generate_report(period="30d", platforms=["juejin", "weibo"])

# 导出 CSV
csv_path = dashboard.export_csv(report)
```

### 8. GitHub Promoter（GitHub 推广器）

Release 推广文案生成、贡献者感谢、Issue 响应。

```python
promoter = GitHubPromoter(config)

# 推广 Release（自动生成多平台文案）
promo = promoter.promote_release("Zeon7744/dev-artifacts")

# 感谢贡献者
promoter.thank_contributors("Zeon7744/dev-artifacts")

# 自动响应 Issues
promoter.respond_to_issues("Zeon7744/dev-artifacts")
```

## 运行测试

```bash
cd social-automation
python -m pytest tests/ -v
```

## 设计原则

| 原则 | 说明 |
|------|------|
| **统一接口** | 所有模块通过 config 加载凭证，接口风格一致 |
| **优雅重试** | 网络请求自动重试 3 次，指数退避 |
| **限流保护** | 令牌桶限流，防止触发平台封禁 |
| **数据持久化** | 运行数据存储在 `data/` 目录，JSON 格式 |
| **平台解耦** | 每个平台独立适配器，新增平台只需加一个类 |
| **无外部依赖** | 仅依赖 `requests`，无需数据库 |

## 扩展新平台

1. 在 `base.py` 同级创建 `xxx_client.py`
2. 继承 `BaseAPIClient`
3. 实现平台特定方法
4. 在对应模块的 `CLIENTS` / `PLATFORM_MAP` 中注册
5. 在 `config/platforms.json` 中添加配置

## License

MIT
