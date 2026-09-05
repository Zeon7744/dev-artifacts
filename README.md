# dev-artifacts

> 开发工具箱 — MCP Server 集成 · 金融新闻 · 投资分析 · 加密货币预测

[![GitHub Stars](https://img.shields.io/github/stars/Zeon7744/dev-artifacts?style=social)](https://github.com/Zeon7744/dev-artifacts)
[![Gitee stars](https://gitee.com/Zeon7744/dev-artifacts/badge/star.svg?theme=gvp)](https://gitee.com/Zeon7744/dev-artifacts)
[![GitCode stars](https://gitcode.com/Zeon7744/dev-artifacts/stars/badge)](https://gitcode.com/Zeon7744/dev-artifacts)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-v0.1.0-blue)](https://github.com/Zeon7744/dev-artifacts/releases/tag/v0.1.0)

## 在线演示

- [GitHub Pages](https://zeon7744.github.io/dev-artifacts/)

## 简介

**开发工具箱**，集成多个 MCP Server 和 Agent 系统，涵盖金融新闻、短剧创作、投资分析、加密货币预测等场景。

## 模块索引

> 注意：以下模块已有独立仓库，推荐使用独立版本以获取最新功能。

| 模块 | 描述 | 独立仓库 |
|------|------|----------|
| `crypto-mlp/` | 加密货币 MLP 预测引擎 | [crypto-mlp-high-confidence](https://github.com/Zeon7744/crypto-mlp-high-confidence) |
| `global-investment-mlp/` | 量化投资框架 | [global-investment-mlp](https://github.com/Zeon7744/global-investment-mlp) |
| `financial-news-mcp/` | 财经新闻 MCP | [dev-artifacts](此仓库) |
| `short-drama-mcp/` | 短剧创作 MCP | [dev-artifacts](此仓库) |
| `investment-mcp/` | 投资分析 MCP | [dev-artifacts](此仓库) |
| `commodity-mlp/` | 大宗商品预测 | [dev-artifacts](此仓库) |

## 核心组件

### Agents 系统
- `analyst_agent.py` — 分析师智能体
- `orchestrator.py` — 编排器智能体
- `reporter_agent.py` — 报告生成智能体
- `watcher_agent.py` — 监控智能体

### API 网关
- `api_gateway/gateway.py` — 统一 API 网关
- `api_gateway/subscription.py` — 订阅管理
- `api_gateway/webhook.py` — Webhook 处理

### Smart Community
- `smart-community/` — Docker 化部署方案
- `Dockerfile.backend` / `Dockerfile.frontend`

## 快速开始

```bash
git clone https://github.com/Zeon7744/dev-artifacts.git
cd dev-artifacts
pip install -e .
```

## 多平台镜像

| 平台 | 链接 |
|------|------|
| GitHub (主仓库) | [GitHub](https://github.com/Zeon7744/dev-artifacts) |
| Gitee | [Gitee](https://gitee.com/Zeon7744/dev-artifacts) |
| GitCode | [GitCode](https://gitcode.com/Zeon7744/dev-artifacts) |

## 赞助与支持

| 平台 | 链接 | 支付方式 |
|------|------|----------|
| ☕ **爱发电** | [afdian.com/@Zeon7744](https://afdian.com/@Zeon7744) | 支付宝 / 微信支付 |
| 🌍 **GitHub Sponsors** | [github.com/sponsors/Zeon7744](https://github.com/sponsors/Zeon7744) | PayPal / Stripe |

### 赞助档位

| 档位 | 价格 | 权益 |
|------|------|------|
| ☕ 请喝咖啡 | ¥18/月 | 感谢支持 |
| 🍺 请喝啤酒 | ¥58/月 | 优先回复 Issue |
| 🎁 项目赞助 | ¥188/月 | 定制功能需求 |

## 相关项目

- [baibai](https://github.com/Zeon7744/baibai) — MCP 基础工具库
- [crypto-mlp-high-confidence](https://github.com/Zeon7744/crypto-mlp-high-confidence) — 加密货币预测
- [global-investment-mlp](https://github.com/Zeon7744/global-investment-mlp) — 量化投资框架
- [awesome-ai-short-drama](https://github.com/Zeon7744/awesome-ai-short-drama) — AI 短剧资源

## 贡献

欢迎提交 Issue 和 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

*由 [Zeon7744](https://github.com/Zeon7744) 维护 · 开发工具箱 · 三平台同步*
