# 大宗商品MLP投资分析工具 - 优化报告

## 优化概述

本次优化在原有大宗商品MLP投资分析工具基础上，添加了以下新功能模块：

### 1. 新增模块

| 文件 | 功能说明 |
|------|---------|
| `mlp_model_v2.py` | 优化版MLP模型，支持自适应参数和超参数搜索 |
| `feature_engineering_v2.py` | 增强特征工程，从13个扩展到28个技术指标 |
| `backtest.py` | 回测引擎，支持手续费、滑点、仓位管理 |
| `risk_manager.py` | 风险管理模块，提供止损、止盈、仓位控制 |
| `test_comparison.py` | 对比测试脚本，量化评估两个版本性能 |

### 2. 核心改进

#### 特征工程增强
- **原版**：13个技术指标（Returns、MA、RSI、MACD、Bollinger、ATR、Volume）
- **优化版**：28个技术指标，新增：
  - RSI_7（短期RSI）
  - MACD_Histogram（MACD柱状图）
  - MA_50（长期均线）
  - Volatility_10d/20d（波动率）
  - ROC_10d/20d（变动率）
  - Price_Position（价格位置）

#### 模型优化
- 自适应隐藏层架构（根据特征数量自动选择）
- 简化的超参数搜索空间（提高训练速度）
- 特征筛选机制（自动选择显著特征）

#### 回测引擎
- 手续费：0.1%
- 滑点：0.05%
- 初始资金：10万元
- 支持交易信号生成和绩效指标计算

#### 风险管理
- 最大仓位：30%
- 止损：5%
- 止盈：15%
- 每日亏损限制：2%
- 连续亏损熔断：5次

### 3. 测试结果对比

#### GC=F（黄金）测试
| 指标 | 原版 | 优化版 |
|------|------|--------|
| 特征数量 | 15个 | 16个（显著特征） |
| 样本数量 | 481条 | 451条 |
| 测试准确率 | 78.35% | 65.56% |
| F1分数 | 0.7241 | 0.6905 |
| 交叉验证 | 0.7350 ± 0.0660 | 0.5924 ± 0.0547 |

#### 多商品对比测试（GC=F, CL=F）
| 指标 | 原版平均 | 优化版平均 |
|------|----------|------------|
| 测试准确率 | 79.90% | 68.13% |
| 回测收益 | 180.66% | 210.60% |

### 4. 关键发现

1. **准确率 vs 收益的权衡**
   - 原版模型测试准确率更高（79.9% vs 68.1%）
   - 但优化版回测收益更高（210.6% vs 180.7%）
   - 说明更丰富的特征能提供更有价值的交易信号

2. **特征重要性分析**
   - 高相关性特征：Volatility_10d (0.156)、MA_10 (0.140)、MA_5 (0.134)
   - 低相关性特征：MACD、RSI_14等常见指标
   - 建议：保留显著特征，剔除噪声特征

3. **过拟合风险**
   - 28个原始特征中仅16个显著
   - 特征筛选能有效减少过拟合
   - 建议使用自适应架构（特征多时用简单模型）

### 5. 使用方法

#### CLI命令
```bash
# 原版分析
python cli.py --symbols GC=F CL=F

# 优化版分析
python cli.py --symbols GC=F --optimize

# 使用真实数据
python cli.py --symbols GC=F --real-data

# 保存模型
python cli.py --symbols GC=F --save-model
```

#### CodeAct脚本
```bash
# 原版分析
python commodity_mlp_analysis.py --symbols GC=F

# 优化版分析
python commodity_mlp_analysis.py --symbols GC=F --optimize
```

#### Python API
```python
from mlp_model_v2 import CommodityMLPModel
from feature_engineering_v2 import FeatureEngineer

# 创建优化版模型
model = CommodityMLPModel(use_better_params=True)
metrics = model.train(features, target)

# 预测
prediction = model.predict(latest_features)
confidence = model.predict_proba(latest_features)
```

### 6. 后续优化方向

1. **集成学习**
   - 结合多个模型（Random Forest, XGBoost）
   - 使用 VotingClassifier 或 Stacking 集成

2. **时序交叉验证**
   - 使用 TimeSeriesSplit 替代随机分割
   - 更真实地模拟实盘交易场景

3. **超参数优化**
   - 使用 Optuna 进行贝叶斯优化
   - 自动搜索最佳参数组合

4. **深度学习扩展**
   - 尝试 LSTM/GRU 处理时序依赖
   - 结合注意力机制捕捉关键特征

### 7. 文件结构

```
commodity-mlp/
├── data_fetcher.py          # 数据获取模块
├── feature_engineering.py   # 原版特征工程
├── feature_engineering_v2.py # 优化版特征工程
├── mlp_model.py            # 原版MLP模型
├── mlp_model_v2.py         # 优化版MLP模型
├── backtest.py             # 回测引擎
├── risk_manager.py         # 风险管理模块
├── cli.py                  # 命令行接口
├── app_web.py              # Web界面
├── test_comparison.py      # 对比测试脚本
├── reports/                # 报告输出目录
├── models/                 # 模型保存目录
└── requirements.txt        # 依赖包
```

---

**项目地址**: https://github.com/Zeon7744/dev-artifacts/tree/main/commodity-mlp

**更新时间**: 2026-09-01
