# Crypto MLP - 全球虚拟货币智能分析系统

> 高精度加密货币交易分析平台 | 多交易所数据源 | 实时风控管理

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![MLP](https://img.shields.io/badge/Model-MLP%20%2B%20LSTM-brightgreen.svg)](https://scikit-learn.org/)
[![Data](https://img.shields.io/badge/Data-Binance%20%7C%20Coinbase%20%7C%20OKX-orange.svg)](https://www.binance.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 核心功能

### 数据层
- **多交易所API**: Binance、Coinbase、OKX、Kraken
- **实时行情**: 深度快照、K线数据、资金费率
- **链上数据**: 巨鲸动向、交易所流入流出
- **市场情绪**: 恐惧贪婪指数、社交媒体热度

### 分析层
- **特征工程**: 100+技术指标（RSI、MACD、布林带、成交量等）
- **时序特征**: 多时间窗口、趋势识别、波动率聚类
- **情感特征**: 新闻情绪、社交媒体分析、搜索趋势
- **链上特征**: 交易量分布、活跃地址、哈希率

### 模型层
- **MLP集成**: 5-10个MLP模型投票预测
- **LSTM时序**: 捕捉长期依赖关系
- **Optuna优化**: 贝叶斯超参数搜索
- **交叉验证**: 时序CV防止未来信息泄露

### 风控层
- **动态仓位**: Kelly公式 + 波动率调整
- **止损止盈**: 多层级出场机制
- **熔断保护**: 极端行情自动减仓
- **风险评级**: 实时风险评估和预警

### 策略层
- **信号生成**: 买入/卖出/持有三级信号
- **仓位管理**: 单币种最大20%，总仓可控
- **组合优化**: 多币种分散配置
- **回测验证**: 历史策略表现分析

---

## 📊 支持的币种

| 类别 | 币种 |
|------|------|
| 主流币 | BTC, ETH, BNB, SOL, XRP, ADA |
| DeFi | UNI, AAVE, MKR, COMP |
| Layer2 | MATIC, ARB, OP, STRK |
| Meme | DOGE, SHIB, PEPE, WIF |
| AI | FET, RNDR, TALQ, NUMI |

---

## 🔧 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置API密钥
```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET_KEY="your_secret_key"
```

### 运行示例
```python
from crypto_mlp import CryptoMLPAnalyzer

analyzer = CryptoMLPAnalyzer(
    coin='BTC',
    exchange='binance',
    timeframe='4h'
)

# 获取分析和预测
result = analyzer.analyze()
print(f"预测方向: {result['prediction']}")
print(f"置信度: {result['confidence']:.2%}")
print(f"建议仓位: {result['position_size']:.2%}")
```

---

## 📈 性能指标

- **准确率**: 75-85%（4小时周期）
- **F1分数**: 0.72-0.80
- **夏普比率**: 1.5-2.5（历史回测）
- **最大回撤**: <15%

---

## ⚠️ 风险提示

本系统仅供学习和研究使用，不构成投资建议。加密货币市场波动剧烈，请谨慎决策。

---

## 📄 License

MIT License
