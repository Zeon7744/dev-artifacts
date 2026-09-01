# 全球资本投资分析系统 (Global Investment MLP)

一个全面的多机构类型投资分析平台，支持公募基金、对冲基金、VC、PE、天使基金等全球资本的分析与配置建议。

## 🚀 核心功能

### 1. 多机构类型支持
- **对冲基金** - Bridgewater, Renaissance, Citadel等
- **风险投资(VC)** - Sequoia, a16z, Benchmark等
- **私募股权(PE)** - Blackstone, KKR, Carlyle等
- **公募基金** - Vanguard, BlackRock等
- **主权财富基金** - Norway, Saudi PIB, GIC等
- **天使投资基金** - Y Combinator等

### 2. 投资热点分析
- 实时检测全球投资热点赛道
- 多时间窗口动量评分
- 行业轮动预测
- 风险调整收益评估

### 3. 多因子量化模型
- 8类因子体系：价值、成长、动量、质量、低波动、流动性、宏观、另类数据
- IC加权优化
- 机器学习排名
- 组合优化

### 4. 风险分析引擎
- VaR/CVaR计算
- 历史压力测试（2008危机、COVID、加息周期等）
- 相关性分析
- 风险预警系统

### 5. 资产配置建议
- 基于风险偏好的配置建议
- 动态权重调整
- 市场周期适配

## 📊 系统架构

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

## 🔧 安装依赖

```bash
pip install numpy pandas scikit-learn scipy yfinance
```

## 📈 快速开始

### 基本分析
```bash
python main.py
```

### 自定义参数
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

### 运行测试
```bash
python -m pytest test_*.py -v
```

## 📋 输出报告

分析完成后将生成：
- `reports/investment_report_YYYYMMDD_HHMMSS.html` - 完整HTML报告
- `reports/summary_YYYYMMDD.json` - JSON摘要

## 🎯 核心指标

| 指标 | 说明 |
|------|------|
| VaR(95%) | 95%置信度下的最大损失 |
| CVaR | 条件风险价值 |
| 夏普比率 | 风险调整收益 |
| 最大回撤 | 历史最大亏损 |
| IC均值 | 因子信息系数 |
| 多空收益 | 长短线差 |

## 📊 压力测试情景

- 2008年金融危机
- 2020年新冠疫情
- 利率缓慢上升
- 突然加息
- 经济衰退

## 🔮 未来规划

- [ ] 接入真实基金数据库
- [ ] 添加另类数据支持
- [ ] 实现实时数据推送
- [ ] 增加可视化Dashboard
- [ ] 支持Python API集成
- [ ] 添加机器学习预测模块

## 📄 许可证

MIT License

## 👥 作者

Global Investment MLP Team

---

*免责声明：本系统仅供研究学习使用，不构成投资建议。投资有风险，决策需谨慎。*
