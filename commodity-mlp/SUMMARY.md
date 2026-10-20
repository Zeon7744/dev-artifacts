# 大宗商品MLP投资分析工具 - 项目总结

## 项目概述
基于深度神经网络（MLP）的大宗商品投资预测工具，使用13个技术指标作为特征，预测未来5日价格走势。

## 技术栈
- **语言**: Python 3.8+
- **机器学习**: scikit-learn (MLPClassifier)
- **数据处理**: pandas, numpy
- **Web框架**: Flask
- **数据源**: yfinance (模拟数据 + 真实数据接口)

## 项目结构
```
commodity-mlp/
├── data_fetcher.py      # 数据获取模块（模拟+真实数据）
├── feature_engineering.py  # 特征工程（13个技术指标）
├── mlp_model.py         # MLP模型训练与预测
├── cli.py               # 命令行工具
├── app_web.py           # Flask Web界面
├── requirements.txt     # Python依赖
├── README.md            # 详细文档
├── .gitignore           # Git忽略规则
├── models/              # 训练好的模型存储
└── reports/             # 分析报告输出
```

## 功能特性
1. **多商品支持**: 黄金(GC=F)、原油(CL=F)、白银(SI=F)、铜(HG=F)、天然气(NG=F)
2. **特征工程**: 13个技术指标（RSI、MACD、布林带、移动平均线等）
3. **MLP模型**: 三层隐藏层(128-64-32)，准确率约77-80%
4. **CLI工具**: 命令行批量分析和报告生成
5. **Web界面**: Flask交互式可视化
6. **特征重要性**: 识别关键预测因子

## 测试结果
| 商品 | 测试准确率 | F1分数 | 预测信号 | 置信度 |
|------|-----------|--------|----------|--------|
| GC=F | 77.71% | 0.7244 | 看跌 | 100.0% |
| CL=F | 79.62% | 0.7895 | 看跌 | 99.9% |
| SI=F | 79.62% | 0.7895 | 看跌 | 99.9% |
| HG=F | 79.62% | 0.7895 | 看跌 | 99.9% |
| NG=F | 79.62% | 0.7895 | 看跌 | 99.9% |

## 使用方法

### 命令行
```bash
# 分析单个商品
python cli.py --symbols GC=F

# 分析所有商品
python cli.py --all --save-model

# 使用真实数据
python cli.py --symbols GC=F --real-data
```

### Python API
```python
from data_fetcher import CommodityDataFetcher
from feature_engineering import FeatureEngineer
from mlp_model import CommodityMLPModel

# 获取数据
fetcher = CommodityDataFetcher()
df = fetcher.generate_simulated_data('GC=F', days=800)

# 提取特征
engineer = FeatureEngineer()
features = engineer.extract_features(df)
target = df['Target'].iloc[:len(features)]

# 训练模型
model = CommodityMLPModel()
metrics = model.train(features, target)

# 预测
prediction = model.predict(features.tail(1))
```

## GitHub仓库
https://github.com/Zeon7744/dev-artifacts/tree/main/commodity-mlp

## 仓库标签
- ml-finance
- python
- cli-tools
- dev-artifacts

## 风险声明
⚠️ 本工具仅供学习和研究使用，不构成任何投资建议。金融市场存在风险，过去表现不代表未来结果。

---
生成时间: 2026-09-01
