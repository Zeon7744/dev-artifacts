# Dev-Artifacts — 通用开发成果库

> 存放经过验证的可复用工具、脚本和项目。
[![GitHub](https://img.shields.io/github/stars/Zeon7744/dev-artifacts?style=social)](https://github.com/Zeon7744/dev-artifacts)
[![Gitee](https://gitee.com/Zeon7744/dev-artifacts/badge/star.svg)](https://gitee.com/Zeon7744/dev-artifacts)
[![爱发电](https://img.shields.io/badge/%E7%88%B1%E5%8F%91%E7%94%B5-%E6%94%AF%E6%8C%81-brightgreen)](https://ifdian.net/a/Zeon7744)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/Zeon7744/dev-artifacts/releases)
[![GitHub stars](https://img.shields.io/github/stars/Zeon7744/dev-artifacts?style=social)](https://github.com/Zeon7744/dev-artifacts)
[![GitHub forks](https://img.shields.io/github/forks/Zeon7744/dev-artifacts?style=social)](https://github.com/Zeon7744/dev-artifacts/forks)

---

## 目录结构

```
dev-artifacts/
├── .mcp.json                 # MCP Server 配置
├── mcp_server.py             # 主 MCP Server（通用工具）
├── cli.py                    # 命令行入口
├── tools.py                  # 核心工具函数库
│
├── agents/                   # AI Agent 系统
│   ├── base_agent.py         # Agent 基类
│   ├── orchestrator.py       # 编排器（多 Agent 协作）
│   ├── analyst_agent.py      # 分析师 Agent
│   ├── reporter_agent.py     # 报告生成 Agent
│   └── watcher_agent.py      # 监控 Agent
│
├── api_gateway/              # API 网关（订阅/支付/Webhook）
│   ├── gateway.py
│   ├── subscription.py
│   └── webhook.py
│
├── crypto-mlp/               # 加密货币 MLP 分析系统
│   ├── crypto_mlp.py         # MLP 核心模型
│   ├── lstm_analyzer.py      # LSTM 时序分析
│   ├── feature_engineer.py   # 特征工程
│   ├── risk_manager.py       # 风险管理
│   └── test_all.py           # 测试套件
│
├── commodity-mlp/            # 大宗商品 MLP 分析系统
│   └── ...
│
├── global-investment-mlp/    # 全球投资基金分析
│   ├── core_analyzer.py
│   ├── multi_factor_model.py
│   └── risk_analytics.py
│
├── financial-news-mcp/       # 金融新闻 MCP
│   └── ...
│
├── short-drama-mcp/          # 短剧创作 MCP（与 awesome-ai-short-drama 联动）
│   ├── tools/                # 短剧工具集
│   │   ├── character_creator.py    # 角色生成
│   │   ├── dialogue_optimizer.py   # 对话优化
│   │   ├── storyboard_generator.py # 分镜生成
│   │   └── format_checker.py       # 格式校验
│   └── test_*.py             # 测试用例
│
├── smart-community/          # 智能社区平台（实验性）
│   ├── backend/              # FastAPI 后端
│   ├── frontend/             # React + Tailwind 前端
│   └── docker-compose.yml    # Docker 部署
│
└── reports/                  # 分析报告输出目录
```

---

## MCP Server

### 配置

```json
{
  "mcpServers": {
    "dev-artifacts": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```

### 功能模块

| 模块 | 说明 |
|------|------|
| **Agent 系统** | 多 Agent 编排，支持分析师、报告生成、监控等角色协作 |
| **API 网关** | 统一 API 入口，支持订阅管理和 Webhook 通知 |
| **crypto-mlp** | 加密货币 MLP 预测模型（CV 准确率 92.94%） |
| **commodity-mlp** | 大宗商品 MLP 预测模型 |
| **investment-mcp** | 全球投资分析 MCP（多因子模型） |
| **financial-news-mcp** | 金融新闻 MCP（实时资讯聚合） |
| **short-drama-mcp** | 短剧创作 MCP（角色/对话/分镜生成） |
| **smart-community** | 智能社区平台（RAG + 工作流引擎） |

---

## 快速开始

### 安装依赖

```bash
pip install -e ".[mcp]"
```

### 运行 MCP Server

```bash
python mcp_server.py
```

### 运行 CLI

```bash
python cli.py --help
```

---

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest crypto-mlp/test_all.py -v
```

---

## 独立项目

以下模块可作为独立项目使用：

- [crypto-mlp-high-confidence](../crypto-mlp-high-confidence) — 加密货币预测系统（独立完整版）
- [awesome-ai-short-drama](../awesome-ai-short-drama) — AI 短剧创作资源库
- [baibai](../baibai) — Vibe Coding 工具集（CLI + MCP）

---

## 许可证

MIT License
