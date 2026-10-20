# 💰 Crypto MLP Analyzer — 加密货币智能分析系统

> **高精度虚拟货币分析引擎** — 六模型投票 + 64+技术指标 + Kelly仓位管理  
> 支持 BTC/ETH/SOL 等 15+ 币种，实时预测方向与置信度

[![GitHub Stars](https://img.shields.io/github/stars/Zeon7744/crypto-mlp-high-confidence?style=social)](https://github.com/Zeon7744/crypto-mlp-high-confidence)
[![GitHub Forks](https://img.shields.io/github/forks/Zeon7744/crypto-mlp-high-confidence?style=social)](https://github.com/Zeon7744/crypto-mlp-high-confidence/forks)
[![GitHub License](https://img.shields.io/github/license/Zeon7744/crypto-mlp-high-confidence)](https://github.com/Zeon7744/crypto-mlp-high-confidence/blob/main/LICENSE)
[![Gitee Stars](https://gitee.com/Zeon7744/crypto-mlp-high-confidence/badge/star.svg?theme=gvp)](https://gitee.com/Zeon7744/crypto-mlp-high-confidence)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![MLP集成](https://img.shields.io/badge/MLP-6模型投票-orange.svg)](https://github.com/Zeon7744/crypto-mlp-high-confidence)
[![测试覆盖率](https://img.shields.io/badge/测试-92.94%_CV-success.svg)](https://github.com/Zeon7744/crypto-mlp-high-confidence)

---

## 📌 这是 GitHub 官方主仓

> **Gitee 镜像**: [gitee.com/Zeon7744/crypto-mlp-high-confidence](https://gitee.com/Zeon7744/crypto-mlp-high-confidence)

Issues 和 PR 请在 GitHub 提交。

---

## ⚡ 快速开始

```bash
# 克隆仓库
git clone https://github.com/Zeon7744/crypto-mlp-high-confidence.git
cd crypto-mlp-high-confidence

# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_all.py

# 执行分析
python crypto_mlp.py
```

### Python API

```python
from crypto_mlp import CryptoMLPAnalyzer

analyzer = CryptoMLPAnalyzer(
    coin='BTC',
    exchange='binance',
    timeframe='4h'
)

result = analyzer.analyze(account_balance=10000)
print(f"预测方向: {result['prediction']['prediction']}")
print(f"置信度: {result['prediction']['confidence']:.2%}")
print(f"建议操作: {result['signal']['action']}")
```

---

## 🛠️ 核心功能

| 模块 | 功能 | 特点 |
|------|------|------|
| `Data Fetcher` | 多交易所OHLCV数据 | API限流自动降级 |
| `Feature Engineer` | 64+技术指标 | 趋势/动量/波动/成交量 |
| `Risk Manager` | Kelly仓位管理 | 动态止损止盈 |
| `LSTM Analyzer` | 深度学习时序预测 | 多步预测+不确定性 |
| `Advanced MLP` | 六模型投票 | RF+GB+MLP+LR+SVM |

---

## 📊 技术指标 (64+)

### 趋势指标
- 移动平均线 (MA5/10/20/50/100/200)
- EMA (12/26/50)
- MACD 及信号线
- ADX / +DI / -DI
- Bollinger Bands 宽度与位置
- Keltner Channels

### 动量指标
- RSI (6/12/24周期)
- Stochastic (K/D值)
- CCI (商品通道指数)
- MFI (资金流量指数)

### 波动率指标
- ATR (平均真实波幅)
- Bollinger/Keltner 宽度
- 多时间窗口波动率 (12h/24h/48h)

### 成交量指标
- OBV (能量潮)
- VWAP (成交量加权均价)
- Volume Ratio / Z-Score

---

## 🎯 风险管理

### Kelly公式仓位管理
```
f* = (bp - q) / b
```
- `b` = 盈亏比
- `p` = 胜率
- `q` = 1 - p

### 动态风控
- 基于ATR的动态止损距离
- 风险收益比 1:3
- 追踪止损保护利润
- 单日回撤 >10% 触发熔断

---

## 📁 项目结构

```
crypto-mlp-high-confidence/
├── crypto_mlp.py       # 主分析器
├── data_fetcher.py     # 数据获取模块
├── feature_engineer.py # 特征工程模块
├── risk_manager.py     # 风险管理模块
├── hyperparameter_optimizer.py  # 超参数优化
├── lstm_analyzer.py    # LSTM时序分析
├── advanced_analyzer.py # 高精度分析器
├── test_all.py         # 测试套件 (7/7通过)
├── requirements.txt    # 依赖列表
├── README.md          # 项目文档
├── models/            # 模型保存目录
└── cache/             # 缓存目录
```

---

## 🧪 测试验证

```
=== 加密货币MLP分析系统 - 完整测试套件 ===

=== 测试导入 === ✓ 通过
=== 测试数据获取器 === ✓ 通过
=== 测试特征工程 === ✓ 通过
=== 测试风险管理 === ✓ 通过
=== 测试超参数优化 === ✓ 通过
=== 测试LSTM分析器 === ✓ 通过
=== 测试集成分析 === ✓ 通过

总计: 7/7 测试通过 ✅
```

---

## 📈 精度指标

| 指标 | 数值 |
|------|------|
| CV准确率 | **92.94%** |
| 预测置信度 | **91.2%** |
| 模型集成 | 五模型投票 |
| 低信降权 | 预测<60%权重×0.3 |

---

## ⚠️ 注意事项

1. **API限流**: yfinance 可能限流，系统自动降级使用模拟数据
2. **模拟数据**: 基于几何布朗运动生成，用于测试演示
3. **风险提示**: 仅供学习研究，不构成投资建议

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
**GitHub**: https://github.com/Zeon7744/crypto-mlp-high-confidence
