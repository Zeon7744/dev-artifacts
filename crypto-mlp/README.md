# Crypto MLP Analyzer - 加密货币智能分析系统

一个高精度的全球虚拟货币MLP分析系统，集成真实买卖数据规划、风险管理和整体智能分析功能。

## 🚀 系统特性

### 核心模块

| 模块 | 功能 |
|------|------|
| **Data Fetcher** | 支持Binance等交易所API获取OHLCV数据，API限流时自动降级使用模拟数据 |
| **Feature Engineer** | 64+技术指标：趋势、动量、波动率、成交量指标 |
| **Risk Manager** | Kelly公式仓位管理、动态止损止盈、多层熔断机制 |
| **Hyperparameter Optimizer** | Optuna贝叶斯超参数搜索，自动优化模型参数 |
| **LSTM Analyzer** | 深度学习时序预测，支持多步预测和不确定性量化 |
| **Crypto MLP** | 主分析器，集成所有模块的完整分析流程 |

### 支持币种

BTC, ETH, BNB, SOL, XRP, ADA, DOGE, MATIC, AVAX, DOT, LINK, UNI, LTC, ATOM, FIL

## 📊 特征工程 (64+ 特征)

### 趋势指标
- 移动平均线 (MA5, MA10, MA20, MA50, MA100, MA200)
- 指数移动平均 (EMA12, EMA26, EMA50)
- MACD及其信号线、柱状图
- ADX、+DI、-DI
- Bollinger Bands宽度与位置
- Keltner Channels

### 动量指标
- RSI (6, 12, 24周期)
- Stochastic (K, D值)
- CCI (商品通道指数)
- MFI (资金流量指数)

### 波动率指标
- ATR (平均真实波幅)
- Bollinger Bands宽度
- Keltner Channels宽度
- 多时间窗口波动率 (12h, 24h, 48h)

### 成交量指标
- OBV (能量潮)
- VWAP (成交量加权平均价)
- Volume Ratio
- Volume Z-Score

## 🎯 使用方法

### 快速开始

```bash
cd crypto-mlp
pip install -r requirements.txt
python test_all.py  # 运行测试
python crypto_mlp.py  # 运行完整分析
```

### 使用示例

```python
from crypto_mlp import CryptoMLPAnalyzer

# 创建分析器
analyzer = CryptoMLPAnalyzer(
    coin='BTC',
    exchange='binance',
    timeframe='4h'
)

# 运行分析
result = analyzer.analyze(account_balance=10000)

print(f"预测方向: {result['prediction']['prediction']}")
print(f"置信度: {result['prediction']['confidence']:.2%}")
print(f"建议操作: {result['signal']['action']}")
print(f"风险等级: {result['risk_metrics']['risk_level']}")
```

### LSTM时序分析

```python
from lstm_analyzer import CryptoLSTMAnalyzer

lstm = CryptoLSTMAnalyzer(
    coin='BTC',
    timeframe='4h',
    lookback=60,      # 历史窗口
    forecast_horizon=24  # 预测步长
)

# 获取预测结果
forecast = lstm.get_forecast(df, features)
print(f"未来24小时预测: {forecast['forecast_next_24h']}")
print(f"95%置信区间: [{forecast['uncertainty']['ci_95_lower']}, {forecast['uncertainty']['ci_95_upper']}]")
```

## 📈 风险管理

### Kelly公式仓位管理
```
f* = (bp - q) / b
其中:
  b = 盈亏比
  p = 胜率
  q = 1 - p
```

### 动态止损止盈
- 基于ATR的动态止损距离
- 风险收益比 1:3
- 追踪止损保护利润

### 熔断机制
- 单日回撤超过10%触发熔断
- 熔断后1小时内不交易
- 保护账户免受极端波动影响

## 🔬 模型架构

### MLP集成模型
- 5个MLP模型投票决策
- 隐藏层: (100, 50)
- 激活函数: ReLU
- 优化器: Adam
- 时序交叉验证 (5折)

### LSTM深度学习模型
- 三层LSTM架构 (128→64→32)
- Dropout正则化 (0.2)
- 早停机制
- 学习率自适应调整

## 📁 项目结构

```
crypto-mlp/
├── crypto_mlp.py       # 主分析器
├── data_fetcher.py     # 数据获取模块
├── feature_engineer.py # 特征工程模块
├── risk_manager.py     # 风险管理模块
├── hyperparameter_optimizer.py  # 超参数优化
├── lstm_analyzer.py    # LSTM时序分析
├── test_all.py         # 测试套件
├── requirements.txt    # 依赖列表
├── README.md          # 项目文档
├── models/            # 模型保存目录
│   └── model_BTC_4h.pkl
└── cache/             # 缓存目录
```

## 🧪 测试结果

```
=== 加密货币MLP分析系统 - 完整测试套件 ===

=== 测试导入 === ✓ 通过
=== 测试数据获取器 === ✓ 通过
=== 测试特征工程 === ✓ 通过
=== 测试风险管理 === ✓ 通过
=== 测试超参数优化 === ✓ 通过
=== 测试LSTM分析器 === ✓ 通过
=== 测试集成分析 === ✓ 通过

总计: 7/7 测试通过 🎉
```

## ⚠️ 注意事项

1. **API限流**: yfinance API可能限流，系统会自动降级使用模拟数据
2. **模拟数据**: 模拟数据基于几何布朗运动生成，用于测试和演示
3. **真实数据**: 当API限流解除后，可使用真实数据重新训练验证准确率
4. **风险提示**: 本系统仅供学习和研究使用，不构成投资建议

## 📄 许可证

MIT License

---

**开发者**: Zeon7744  
**最后更新**: 2026-09-01  
**GitHub**: https://github.com/Zeon7744/dev-artifacts
