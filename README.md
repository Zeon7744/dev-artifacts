# Dev-Artifacts - 开发成果库

> 通用开发成品仓库 — 存放经过验证的可复用工具、脚本和项目

这里是我开发成果的中心仓库，包含可复用的工具、命令行工具、自动化脚本等开发成品。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## 📦 当前项目

### MLP 金融分析器

基于机器学习的金融分析工具 — 技术指标 + MLP预测 + 可视化

**核心功能：**
- 实时数据获取（yfinance）
- 技术指标计算（MA/RSI/MACD/布林带）
- MLP预测模型（分类+回归）
- 投资建议生成
- CLI命令行 + Web界面 + MCP集成

**快速开始：**
```bash
git clone https://github.com/Zeon7744/dev-artifacts.git
cd dev-artifacts
pip install -e .
ml-finance AAPL
```

详见 [README.md](README.md) 了解完整使用方式。

---

## 🏗️ 项目结构

```
dev-artifacts/
├── tools.py              # 金融分析器核心实现
├── cli.py                # CLI 入口
├── mcp_server.py         # MCP Server
├── web.html              # Web 可视化界面
├── pyproject.toml        # 项目配置
└── README.md             # 使用说明
```

未来将持续添加更多开发成果。

---

## 🎯 仓库定位

这是**通用开发成果库**，不是单一垂直项目的仓库。

包含：
- ✅ 经过验证的可复用工具
- ✅ 命令行工具（CLI）
- ✅ 自动化脚本
- ✅ 可独立部署的项目

不包含：
- ❌ 短剧内容（去 [awesome-ai-short-drama](https://github.com/Zeon7744/awesome-ai-short-drama)）
- ❌ Vibe Coding 工具库（去 [baibai](https://github.com/Zeon7744/baibai)）

---

## 📋 相关仓库

| 仓库 | 定位 |
|------|------|
| [baibai](https://github.com/Zeon7744/baibai) | Vibe Coding 通用工具库 |
| [awesome-ai-short-drama](https://github.com/Zeon7744/awesome-ai-short-drama) | AI 短剧创作全链路 |
| [dev-artifacts](https://github.com/Zeon7744/dev-artifacts) | 开发成果成品库 |

---

## ⚠️ 免责声明

本仓库中的金融分析工具仅供学习和研究使用，不构成任何投资建议。金融市场有风险，投资需谨慎。

---

## 📄 许可证

MIT License

---

*由 [Zeon7744](https://github.com/Zeon7744) 维护*  
*开发成果 · 可复用 · 经得起验证*
