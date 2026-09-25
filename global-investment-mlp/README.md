# 🌍 Global Investment MLP — 全球资本投资分析系统

> **多机构类型量化投资框架** — 公募/私募/VC/PE/主权基金全覆盖  
> 多因子模型 · VaR风险引擎 · 压力测试 · 资产配置建议

[![GitHub Stars](https://img.shields.io/github/stars/Zeon7744/global-investment-mlp?style=social)](https://github.com/Zeon7744/global-investment-mlp)
[![GitHub Forks](https://img.shields.io/github/forks/Zeon7744/global-investment-mlp?style=social)](https://github.com/Zeon7744/global-investment-mlp/forks)
[![GitHub License](https://img.shields.io/github/license/Zeon7744/global-investment-mlp)](https://github.com/Zeon7744/global-investment-mlp/blob/main/LICENSE)
[![Gitee Stars](https://gitee.com/Zeon7744/global-investment-mlp/badge/star.svg?theme=gvp)](https://gitee.com/Zeon7744/global-investment-mlp)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Test Coverage](https://img.shields.io/badge/测试-86%_coverage-success.svg)](https://github.com/Zeon7744/global-investment-mlp)

---

## 📌 这是 GitHub 官方主仓

> **Gitee 镜像**: [gitee.com/Zeon7744/global-investment-mlp](https://gitee.com/Zeon7744/global-investment-mlp)

Issues 和 PR 请在 GitHub 提交。

---

## ⚡ 快速开始

```bash
# 克隆仓库
git clone https://github.com/Zeon7744/global-investment-mlp.git
cd global-investment-mlp

# 安装依赖
pip install numpy pandas scikit-learn scipy yfinance

# 运行测试
python -m pytest test_*.py -v

# 执行分析
python main.py
```

### CLI 参数

```bash
python main.py \
  --markets US,CN,HK \
  --days 365 \
  --n-funds 10 \
  --n-assets 20 \
  --portfolio-value 10000000 \
  --factor-method ic_weighting \
  --regime expansion
```

---

## 🛠️ 核心功能

### 1. 多机构类型支持

| 机构类型 | 代表机构 | 策略特点 |
|----------|----------|----------|
| **对冲基金** | Bridgewater, Renaissance, Citadel | 多空套利、量化策略 |
| **风险投资(VC)** | Sequoia, a16z, Benchmark | 早期项目、高成长 |
| **私募股权(PE)** | Blackstone, KKR, Carlyle | 并购重组、杠杆收购 |
| **公募基金** | Vanguard, BlackRock | 被动指数、分散配置 |
| **主权基金** | Norway, Saudi PIB, GIC | 国家储备、长期持有 |
| **天使基金** | Y Combinator | 种子轮、初创企业 |

### 2. 多因子量化模型

- **8类因子体系**：价值、成长、动量、质量、低波动、流动性、宏观、另类数据
- **IC加权优化**：信息系数自适应权重
- **机器学习排名**：XGBoost/LightGBM排序
- **组合优化**：Mean-Variance / Risk Parity

### 3. 风险分析引擎

| 指标 | 说明 |
|------|------|
| VaR(95%) | 95%置信度下的最大损失 |
| CVaR | 条件风险价值（期望损失） |
| 夏普比率 | 风险调整收益 |
| 最大回撤 | 历史最大亏损幅度 |
| IC均值 | 因子信息系数 |
| 多空收益 | 长短线差收益 |

### 4. 压力测试情景

- 📉 2008年金融危机
- 🦠 2020年新冠疫情
- 📈 利率缓慢上升
- 🚀 突然加息周期
- 📊 经济衰退模拟

---

## 📁 项目结构

```
global-investment-mlp/
├── core_analyzer.py      # 核心分析引擎
├── multi_factor_model.py # 多因子量化模型
├── risk_analytics.py     # 风险分析引擎
├── data_fetcher.py       # 数据获取器
├── report_generator.py   # 报告生成器
├── main.py               # 主程序入口
├── data/                 # 数据目录
│   └── cache/           # 缓存
├── models/               # 模型保存
├── reports/              # 报告输出
└── docs/                 # 文档
```

---

## 📊 输出报告

分析完成后自动生成：

| 文件 | 格式 | 内容 |
|------|------|------|
| `reports/investment_report_*.html` | HTML | 完整可视化报告 |
| `reports/summary_*.json` | JSON | 结构化数据摘要 |

---

## 🔬 技术架构

```
data_source (yfinance/API)
    ↓
feature_engine (因子提取)
    ↓
multi_factor_model (IC加权优化)
    ↓
risk_analytics (VaR/CVaR计算)
    ↓
report_generator (HTML/JSON输出)
```

---

## ⚠️ 注意事项

- 本系统仅供研究学习使用
- 不构成投资建议
- 投资有风险，决策需谨慎

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License

---

**开发者**: Zeon7744  
**最后更新**: 2026-09-25  
**GitHub**: https://github.com/Zeon7744/global-investment-mlp
