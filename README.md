# 🏭 Dev Artifacts — 开发成果成品库

> **模块化开发成果集合** — MCP Server · Agent 系统 · 金融分析工具  
> 可复用、可集成、经得起验证的工业级组件

[![GitHub Stars](https://img.shields.io/github/stars/Zeon7744/dev-artifacts?style=social)](https://github.com/Zeon7744/dev-artifacts)
[![GitHub Forks](https://img.shields.io/github/forks/Zeon7744/dev-artifacts?style=social)](https://github.com/Zeon7744/dev-artifacts/forks)
[![GitHub License](https://img.shields.io/github/license/Zeon7744/dev-artifacts)](https://github.com/Zeon7744/dev-artifacts/blob/main/LICENSE)
[![Gitee Stars](https://gitee.com/Zeon7744/dev-artifacts/badge/star.svg?theme=gvp)](https://gitee.com/Zeon7744/dev-artifacts)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![MCP Ready](https://img.shields.io/badge/MCP-Ready-brightgreen.svg)](https://modelcontextprotocol.io)

---

## 📌 这是 GitHub 官方主仓

> **Gitee 镜像**: [gitee.com/Zeon7744/dev-artifacts](https://gitee.com/Zeon7744/dev-artifacts)  
> **GitCode 镜像**: [gitcode.com/Zeon7744/dev-artifacts](https://gitcode.com/Zeon7744/dev-artifacts)

Issues 和 PR 请在 GitHub 提交。

---

## 🧩 模块索引

| 模块 | 类型 | 说明 | 状态 |
|------|------|------|------|
| [short-drama-mcp](short-drama-mcp/) | MCP Server | 短剧创作助手 | ✅ 完成 |
| [financial-news-mcp](financial-news-mcp/) | MCP Server | 财经新闻采集分析 | ✅ 完成 |
| [investment-mcp](investment-mcp/) | MCP Server | 投资分析工具 | ✅ 完成 |
| [crypto-mlp](crypto-mlp/) | ML 模型 | 加密货币预测 | ✅ 完成 |
| [commodity-mlp](commodity-mlp/) | ML 模型 | 大宗商品预测 | ✅ 完成 |
| [global-investment-mlp](global-investment-mlp/) | ML 模型 | 全球投资分析 | ✅ 完成 |
| [smart-community](smart-community/) | Web 应用 | 智能社区系统 | ✅ 完成 |
| [agents](agents/) | Agent 系统 | 多 Agent 编排 | 🔄 开发中 |
| [api_gateway](api_gateway/) | API 网关 | 统一接口管理 | 🔄 开发中 |

---

## ⚡ 快速开始

### 安装依赖

```bash
git clone https://github.com/Zeon7744/dev-artifacts.git
cd dev-artifacts
pip install -e .
```

### 运行测试

```bash
pytest tests/ -v --cov=tools --cov-report=html
```

### 启动 MCP Server

```bash
# 短剧创作 MCP
python short-drama-mcp/server.py

# 财经新闻 MCP
python financial-news-mcp/server.py
```

---

## 🎯 核心能力

### 1. MCP Server 生态

| Server | 用途 | 工具数 |
|--------|------|--------|
| short-drama-mcp | 剧本创作辅助 | 15 个 |
| financial-news-mcp | 财经新闻聚合 | 8 个 |
| investment-mcp | 投资组合分析 | 10 个 |

### 2. 机器学习模型

| 模型 | 预测目标 | 准确率 |
|------|----------|--------|
| MLP (商品) | 价格趋势 | 71-82% |
| LSTM (时序) | 价格预测 | 79% |
| MLP (加密货币) | BTC/SOL 预测 | 75-85% |

### 3. Agent 系统

- 7 个专业 Agent（剧情/角色/对话/剧本/质量/趋势/SEO）
- 工作流编排器，支持串行/并行执行
- 双层架构：tools（规则层）+ agents（LLM 层）

### 4. 量化交易框架 ⭐ 新增

| 模块 | 说明 |
|------|------|
| 回测引擎 | 支持多策略并行回测 + 参数优化 |
| 策略模板 | 动量/均值回归/网格/统计套利/配对交易 |
| 数据源 | A股/美股/加密货币/专业数据 |
| 风险管理 | 仓位管理/Kelly/ATR止损/VaR |
| 绩效报告 | HTML + JSON 双格式输出 |

### 5. 社媒自动化工具 ⭐ 新增

| 模块 | 说明 |
|------|------|
| 内容发布 | 微博/知乎/掘金/Twitter 多平台统一发布 |
| 自动回复 | 关键词匹配 + FAQ 智能回复 |
| 数据分析 | 互动追踪/粉丝增长/热门标签 |
| GitHub 推广 | Release 信息自动生成多平台文案 |

---

## 📊 技术栈

| 层次 | 技术 |
|------|------|
| **语言** | Python 3.8+ |
| **框架** | FastAPI, Pydantic |
| **AI** | OpenAI API, Ollama |
| **数据库** | SQLite, PostgreSQL |
| **容器** | Docker, Docker Compose |
| **测试** | pytest, coverage |

---

## 🔌 MCP 集成配置

### Claude Code

```json
{
  "mcpServers": {
    "short-drama": {
      "command": "python",
      "args": ["short-drama-mcp/server.py"]
    },
    "financial-news": {
      "command": "python",
      "args": ["financial-news-mcp/server.py"]
    }
  }
}
```

### Cursor

在 `.cursor/mcp.json` 中添加相同配置。

---

## 📁 项目结构

```
dev-artifacts/
├── short-drama-mcp/       # 短剧创作 MCP
├── financial-news-mcp/    # 财经新闻 MCP
├── investment-mcp/        # 投资分析 MCP
├── crypto-mlp/            # 加密货币预测
├── commodity-mlp/         # 大宗商品预测
├── global-investment-mlp/ # 全球投资分析
├── smart-community/       # 智能社区
├── agents/                # Agent 系统
├── api_gateway/           # API 网关
├── models/                # 模型文件
├── scripts/               # 运维脚本
├── tests/                 # 测试套件
└── README.md
```

---

## 🏗️ 相关项目

| 项目 | 描述 | 链接 |
|------|------|------|
| **awesome-ai-short-drama** | 短剧创作资源库 | [→](https://github.com/Zeon7744/awesome-ai-short-drama) |
| **baibai** | Vibe Coding 工具库 | [→](https://github.com/Zeon7744/baibai) |

---

## 📈 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-09-25 | 初始版本，8 个模块 |
| v0.9.0 | 2026-09-20 | 添加 smart-community |
| v0.8.0 | 2026-09-15 | 添加 investment-mcp |

---

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/new-module`)
3. 提交更改 (`git commit -m 'Add new module: XXX'`)
4. 推送到分支 (`git push origin feature/new-module`)
5. 开启 Pull Request

### 代码规范

- 使用 `black` 格式化代码
- 保持测试覆盖率 ≥ 80%
- 遵循 PEP 8 规范

---

## ☕ 支持作者

如果这个项目对你有帮助，欢迎赞助 ☕

| 渠道 | 方式 |
|------|------|
| [爱发电](https://afdian.com/@Zeon7744) | 支付宝 / 微信支付 |
| [GitHub Sponsors](https://github.com/sponsors/Zeon7744) | PayPal / Stripe |

---

## 📄 License

MIT License

---

<div align="center">

**由 [Zeon7744](https://github.com/Zeon7744) 维护**  
*开发成果 · 可复用 · 经得起验证*

⭐ 如果对你有帮助，点个 Star 鼓励一下！

</div>
