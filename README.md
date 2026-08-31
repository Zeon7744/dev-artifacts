# Stock Analyzer - MLP精准金融分析工具

> 基于机器学习的股票分析工具 — 技术指标 + MLP预测 + 可视化

用 AI 做金融分析，从数据到决策，这一套就够了。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![MLP](https://img.shields.io/badge/MLP-Predictions-orange.svg)](https://scikit-learn.org/)

---

## 🚀 简介

**Stock Analyzer** 是一个基于 **MLP（多层感知器）** 的精准金融分析工具。

核心功能：
- **实时数据获取** — 支持 yfinance 获取全球股票数据
- **技术指标计算** — MA / RSI / MACD / 布林带 / 波动率
- **MLP 预测模型** — 分类器 + 回归器双模型
- **特征重要性分析** — 识别关键影响因素
- **投资建议生成** — 综合技术指标和 ML 预测
- **可视化图表** — 价格趋势、技术指标、预测对比

---

## 📦 安装

### 从源码安装（推荐）

```bash
git clone https://github.com/Zeon7744/stock-analyzer.git
cd stock-analyzer
pip install -e .
```

### 直接运行

```bash
# 无需安装，直接运行
python cli.py AAPL
```

### 依赖

- Python 3.8+
- yfinance (数据获取)
- pandas, numpy (数据处理)
- scikit-learn (MLP 模型)
- matplotlib (可视化)

---

## 🛠️ 命令行使用

### 基本用法

```bash
# 分析单只股票
stock-analyzer AAPL

# 指定分析周期
stock-analyzer AAPL --period 6m

# 保存报告到文件
stock-analyzer AAPL --output report.json

# 生成图表
stock-analyzer AAPL --charts

# JSON 格式输出
stock-analyzer AAPL --json
```

### 支持的市场

| 市场 | 示例代码 |
|------|---------|
| 美股 | AAPL, GOOGL, MSFT, TSLA |
| A股 | 000001.SZ, 600519.SH, 000858.SZ |
| 港股 | 0700.HK (腾讯) |
| ETF | SPY, QQQ, IVV |

---

## 🔌 MCP 集成

Stock Analyzer 支持 Model Context Protocol (MCP)，可以集成到各种 AI 助手：

### 暴露的工具

| 工具名 | 功能 |
|--------|------|
| `analyze_stock` | 分析股票，返回完整报告（含 MLP 预测） |
| `save_analysis_report` | 保存分析报告到文件 |
| `generate_stock_charts` | 生成股票分析图表 |
| `get_stock_price` | 获取实时价格信息 |
| `compare_stocks` | 比较多只股票的技术指标 |

### 配置 Claude Code

```json
{
  "mcpServers": {
    "stock-analyzer": {
      "command": "python",
      "args": ["-m", "mcp_server"]
    }
  }
}
```

### 配置 Cursor

在 `.cursor/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "stock-analyzer": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```

---

## 📊 Web 界面

提供基于 Chart.js 的交互式可视化界面。

直接打开 `web.html` 即可使用，无需部署。

功能：
- 实时价格展示
- 技术指标可视化
- MLP 预测结果对比
- 投资建议生成

---

## 🏗️ 项目结构

```
stock-analyzer/
├── tools.py              # 金融分析器核心实现
├── cli.py                # CLI 入口
├── mcp_server.py         # MCP 服务器
├── web.html              # Web 界面
├── pyproject.toml        # 项目配置
└── README.md             # 本文件
```

---

## 📈 输出示例

```json
{
  "symbol": "AAPL",
  "price": 178.50,
  "change_1d": 1.25,
  "indicators": {
    "RSI": 58.32,
    "MACD": 0.8542,
    "BB_position": 0.65
  },
  "ml_prediction": {
    "classifier_accuracy": 0.72,
    "expected_5d_return_pct": 1.85
  },
  "advice": {
    "operation": "买入",
    "risk_level": "中等"
  }
}
```

---

## 🎯 技术架构

### 数据层
- yfinance 获取历史行情
- pandas 进行数据清洗和预处理
- 特征工程：技术指标 + 时间特征

### 模型层
- **MLPClassifier**: 预测涨跌方向（分类任务）
- **MLPRegressor**: 预测收益率（回归任务）
- StandardScaler 标准化特征

### 应用层
- CLI 命令行工具
- MCP Server（AI 助手集成）
- Web 界面（Chart.js 可视化）

---

## ⚠️ 免责声明

> 本工具仅供学习和研究使用，不构成任何投资建议。金融市场有风险，投资需谨慎。作者不对任何投资损失负责。

---

## 📄 许可证

MIT License - 见 [LICENSE](LICENSE) 文件

---

## 🤝 相关项目

- [baibai](https://github.com/Zeon7744/baibai) - Vibe Coding 通用工具库
- [awesome-ai-short-drama](https://github.com/Zeon7744/awesome-ai-short-drama) - AI 短剧创作全链路
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance API
- [scikit-learn](https://scikit-learn.org/) - 机器学习框架

---

*由 [Zeon7744](https://github.com/Zeon7744) 维护*  
*MLP · 精准分析 · 智能决策*
