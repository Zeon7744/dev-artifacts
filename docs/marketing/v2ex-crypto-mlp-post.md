# 我用五模型投票做了个加密货币预测引擎，CV 准确率 92.94%

> 开源地址：[Zeon7744/crypto-mlp-high-confidence](https://github.com/Zeon7744/crypto-mlp-high-confidence)
> 互动演示：[GitHub Pages](https://zeon7744.github.io/crypto-mlp-high-confidence/)

---

## 为什么做这个项目？

最近在研究加密货币市场的预测模型，发现单模型预测往往不稳定——涨的时候准，跌的时候就翻车。于是我想：能不能让多个模型"投票"，取最共识的结果？

经过三个月的摸索，做出了这个五模型集成投票系统。

---

## 技术方案

### 五模型架构

```
┌──────────────────────────────────────────────────────┐
│              集成预测引擎（五人委员会）                  │
├──────────┬──────────┬──────────┬──────────┬──────────┤
│ RF       │ GB       │ MLP      │ LR       │ SVM      │
│ 权重0.30 │ 权重0.25 │ 权重0.20 │ 权重0.15 │ 权重0.03 │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘
     │          │          │          │          │
     └──────────┴──────────┴──────────┴──────────┘
                        │
                        ▼
              最终决策 + 置信度评估
```

**模型选择理由：**
- **RF（随机森林）** — 对特征交互敏感，表现稳定
- **GB（梯度提升）** — 顺序优化，提升弱学习器
- **MLP（神经网络）** — 非线性拟合能力强
- **LR（逻辑回归）** — 可解释性好，作为基准
- **SVM（支持向量机）** — 高维空间分类，但本次表现不佳

### 特征工程（64+ 维度）

从 OHLCV 数据和订单簿中提取：
- **技术指标**：RSI、MACD、布林带、ATR、KDJ、OBV、MFI
- **量价关系**：成交量变化率、价格偏离度、资金流入流出
- **波动率特征**：24h 波动率、波动率 Z-Score、波动率聚集检测
- **时序特征**：滞后特征、滚动统计量

### 风控模块

- **Kelly 公式仓位管理** — 根据胜率动态计算最优仓位
- **三级熔断机制** — 5%/10%/连续3次止损触发不同级别保护
- **自适应权重** — 根据市场波动率自动调整各模型权重

---

## 实验结果

### 模型性能对比（交叉验证）

| 模型 | CV 准确率 | Test 准确率 | 预测方向 | 权重 |
|------|-----------|-------------|---------|------|
| Random Forest | **92.94%** | 86.70% | 94.5% DOWN | 0.30 |
| Logistic Regression | **92.94%** | 78.20% | 98.9% DOWN | 0.15 |
| Gradient Boosting | 90.22% | 82.10% | 100% DOWN | 0.25 |
| MLP Neural Net | 84.34% | 75.80% | 99.9% DOWN | 0.20 |
| SVM | 50.59% | 51.30% | 51.3% UP | 0.03 |

### 集成投票结果

- **最终准确率**：92.94%（CV）/ 86.70%（Test）
- **预测概率**：91.2% DOWN
- **Top 特征**：volatility_24h(0.011)、target(0.831)、vol_zscore(0.008)、OBV(0.009)

---

## 预测模拟器

我还在 GitHub Pages 上做了一个**交互式预测模拟器**，你可以拖动滑块模拟不同市场条件下各模型的预测结果：

👉 [点击体验预测模拟器](https://zeon7744.github.io/crypto-mlp-high-confidence/)

模拟条件包括：
- 24h 波动率
- 成交量变化率
- RSI 相对强弱
- 价格偏离度
- MACD 信号强度
- OBV 能量潮

---

## 快速开始

```bash
git clone https://github.com/Zeon7744/crypto-mlp-high-confidence.git
cd crypto-mlp-high-confidence
pip install -r requirements.txt
python advanced_analyzer.py
```

### Python API 调用

```python
from advanced_analyzer import CryptoAdvancedAnalyzer

analyzer = CryptoAdvancedAnalyzer(coin='BTC', timeframe='4h')
result = analyzer.analyze(account_balance=10000)

print(f"预测方向: {result['prediction']['prediction'].upper()}")
print(f"置信度: {result['prediction']['confidence']:.1%}")
print(f"建议仓位: {result['risk']['position_size']:.1f}%")
```

---

## 三平台同步

| 平台 | 链接 |
|------|------|
| GitHub（主仓库） | [github.com](https://github.com/Zeon7744/crypto-mlp-high-confidence) |
| Gitee | [gitee.com](https://gitee.com/Zeon7744/crypto-mlp-high-confidence) |
| GitCode | [gitcode.com](https://gitcode.com/Zeon7744/crypto-mlp-high-confidence) |

GitHub Actions 自动同步，保证三端一致。

---

## 注意事项

⚠️ **本项目的预测模型仅用于学术研究和算法验证，不构成任何投资建议。**
加密货币市场风险极高，历史回测表现不代表未来收益。请理性投资，风险自担。

---

## 相关链接

- [完整报告](https://github.com/Zeon7744/crypto-mlp-high-confidence/blob/main/REPORT.md)
- [预测模拟器](https://zeon7744.github.io/crypto-mlp-high-confidence/)
- [相关项目：baibai MCP 工具库](https://github.com/Zeon7744/baibai)
- [相关项目：global-investment-mlp 量化投资框架](https://github.com/Zeon7744/global-investment-mlp)

---

*如果觉得有帮助，欢迎 Star ⭐！有问题或建议请提 Issue。*
