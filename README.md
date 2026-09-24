# 金融期货基金全球新闻MCP v3.0

基于MCP 2026-07-28规范构建的高真实性财经新闻采集与分析平台。

[![Gitee stars](https://gitee.com/Zeon7744/dev-artifacts/badge/star.svg?theme=gvp)](https://gitee.com/Zeon7744/dev-artifacts)
[![GitHub Stars](https://img.shields.io/github/stars/Zeon7744/dev-artifacts?style=social)](https://github.com/Zeon7744/dev-artifacts)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 三平台同步

| 平台 | 链接 |
|------|------|
| **Gitee** (主站) | [gitee.com/Zeon7744/dev-artifacts](https://gitee.com/Zeon7744/dev-artifacts) |
| GitHub | [github.com/Zeon7744/dev-artifacts](https://github.com/Zeon7744/dev-artifacts) |
| GitCode | [gitcode.com/Zeon7744/dev-artifacts](https://gitcode.com/Zeon7744/dev-artifacts) |

---

## 核心能力

| 能力 | 描述 | 关键指标 |
|------|------|----------|
| **全球数据采集** | Reuters/Bloomberg/CNBC/东方财富/同花顺等多源RSS聚合 | 实时性<5min，覆盖率>95% |
| **情感分析** | BERT中文财经模型 + 规则引擎双模式 | 准确率>85%，响应<100ms |
| **趋势预测** | 技术面+基本面融合预测 | 多因子加权，置信度量化 |
| **投资建议** | 个性化资产配置与风控建议 | 风险偏好适配，止损位计算 |
| **数据验证** | 来源权威性+事实核查双重验证 | 可信度评分，风险提示 |
| **RAG知识库** | 语义搜索 + 金融报告解析 | 支持PDF/Markdown/JSON |
| **Agent工作流** | 分析师/监控/报告编排 | 串行/并行工作流 |
| **本地LLM** | Ollama + OpenAI双Provider | 支持熔断器降级 |

---

## 项目架构

```
dev-artifacts/
├── financial-news-mcp/     # 财经新闻MCP (v3.0)
├── short-drama-mcp/        # 短剧创作MCP
├── investment-mcp/         # 投资分析MCP
├── commodity-mlp/          # 大宗商品预测
├── crypto-mlp/             # 加密货币预测
├── global-investment-mlp/  # 全球投资分析
├── smart-community/        # 智能社区Docker部署
├── agents/                 # Agent系统
├── api_gateway/            # API网关
└── docs/                   # 文档
```

---

## 快速开始

### 安装

```bash
git clone https://gitee.com/Zeon7744/dev-artifacts.git
cd dev-artifacts
pip install -e .
```

### 运行测试

```bash
pytest tests/ -v --cov=tools --cov-report=html
```

---

## 相关项目

| 项目 | 链接 |
|------|------|
| [awesome-ai-short-drama](https://gitee.com/Zeon7744/awesome-ai-short-drama) | AI短剧资源库 |
| [baibai](https://gitee.com/Zeon7744/baibai) | Vibe Coding工具库 |
| crypto-mlp-high-confidence | 加密货币MLP预测（独立仓库） |
| global-investment-mlp | 量化投资框架（独立仓库） |

---

## 真实性保障机制

### 1. 多层数据验证
```
原始数据 → 来源权威性评分 → 标题风险分析 → 事实核查 → 可信度输出
```

### 2. 交叉验证
- 同一新闻事件至少2个权威源交叉验证
- 冲突信息标记为"待核实"
- 低可信度新闻降低权重

### 3. 时效性控制
- 超过30天的新闻自动标记过期
- 发布时间和采集时间双重校验
- 实时数据源优先

---

## License

MIT

---

<div align="center">

**由 [Zeon7744](https://gitee.com/Zeon7744) 维护**

*开发成果 · 可复用 · 经得起验证*

</div>
