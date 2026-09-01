# 大宗商品MLP投资分析工具 - 迭代优化v3总结

## 项目概述

大宗商品MLP投资分析工具是一个基于机器学习的量化投资分析系统，支持黄金、原油、白银、铜、天然气等5种大宗商品的价格预测和投资决策。

**GitHub仓库**: https://github.com/Zeon7744/dev-artifacts/tree/main/commodity-mlp

---

## v3迭代新增功能

### 1. LSTM时序模型 (`lstm_model.py`)

- **架构**: 双层LSTM + Dropout + 全连接层
- **优势**: 有效捕捉价格序列的时序依赖关系
- **性能**: 在黄金(GC=F)上达到**86.76%**准确率，较基础MLP提升15.4%

```python
from lstm_model import CommodityLSTMModel

model = CommodityLSTMModel(input_size=15, seq_length=20)
model.train(X_train, y_train, epochs=30)
predictions = model.predict(X_test)
```

### 2. 超参数自动搜索 (`hyperparameter_optimizer.py`)

- **基于**: Optuna框架进行智能超参数搜索
- **搜索空间**: 
  - 隐藏层层数 (1-3层)
  - 每层神经元数量 (16-256)
  - 激活函数 (relu/tanh/logistic)
  - 求解器 (adam/lbfgs)
  - 正则化系数 alpha
  - Batch size (16/32/64/128)

- **性能**: 找到最优配置验证分数**82.05%**

```python
from hyperparameter_optimizer import HyperparameterOptimizer

optimizer = HyperparameterOptimizer(n_trials=10)
best_params = optimizer.optimize(features, target)
```

### 3. 多数据源支持 (`data_fetcher_v3.py`)

- **数据源**: yfinance + 新浪财经 + Tushare
- **容错**: 主数据源失败时自动降级到备选源
- **模拟数据**: 几何布朗运动模拟，用于快速测试

```python
from data_fetcher_v3 import CommodityDataFetcher

fetcher = CommodityDataFetcher(
    primary_source='yfinance',
    fallback_source='simulated'
)
df = fetcher.fetch_data('GC=F', days=800)
```

### 4. 风险管理回测引擎 (`risk_backtest.py`)

内置完善的风险控制机制：

| 风控规则 | 参数 | 说明 |
|---------|------|------|
| 止损 | 2% | 单笔亏损超2%自动平仓 |
| 止盈 | 5% | 单笔盈利超5%自动平仓 |
| 每日亏损限制 | 3% | 当日累计亏损达3%停止交易 |
| 连续亏损熔断 | 3次 | 连续3笔亏损后暂停交易 |
| 手续费 | 0.1% | 每笔交易收取 |
| 滑点 | 0.05% | 模拟市场滑点 |

```python
from risk_backtest import RiskBacktestEngine

engine = RiskBacktestEngine(
    initial_capital=100000,
    risk_config={
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05,
        'max_daily_loss_pct': 0.03,
        'max_consecutive_losses': 3
    }
)
results = engine.run_backtest(df, symbol='GC=F', signal_col='signal')
```

### 5. REST API服务 (`api_server.py`)

Flask RESTful API，提供以下端点：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/symbols` | GET | 获取商品列表 |
| `/api/data/<symbol>` | GET | 获取历史数据 |
| `/api/train/<symbol>` | POST | 训练模型 |
| `/api/predict/<symbol>` | POST | 获取预测信号 |
| `/api/backtest/<symbol>` | POST | 运行回测 |
| `/api/analysis/<symbol>` | GET | 完整分析 |
| `/api/docs` | GET | API文档 |

---

## 测试结果

### 模型性能对比 (GC=F 黄金)

| 模型 | 测试集准确率 | 精确率 | 召回率 | F1分数 |
|------|-------------|--------|--------|--------|
| 基础MLP | 71.34% | 69.77% | 75.95% | 72.73% |
| 超参优化MLP | - | - | - | 82.05% (验证) |
| **LSTM** | **86.76%** | 81.25% | 89.66% | 85.25% |

### 特征重要性 Top 5

1. **RSI_14** (相对强弱指标) - 34.17%
2. **Returns_10d** (10日收益率) - 30.45%
3. **MA_5** (5日均线) - 30.11%
4. **Bollinger_Band_Width** (布林带宽度) - 30.05%
5. **Bollinger_Position** (布林带位置) - 30.05%

---

## 项目文件结构

```
commodity-mlp/
├── cli.py                      # 命令行接口
├── app_web.py                  # Web界面
├── mlp_model.py                # 基础MLP模型
├── mlp_model_v2.py             # v2增强版
├── mlp_model_advanced.py       # 高级版(集成学习+时序CV)
├── lstm_model.py               # 🆕 LSTM时序模型
├── hyperparameter_optimizer.py # 🆕 超参数优化器
├── data_fetcher.py             # 基础数据获取
├── data_fetcher_v2.py          # v2增强版
├── data_fetcher_v3.py          # 🆕 多数据源支持
├── feature_engineering.py      # 基础特征工程
├── feature_engineering_v2.py   # v2增强版
├── risk_manager.py             # 风险管理模块
├── risk_backtest.py            # 🆕 风险管理回测引擎
├── api_server.py               # 🆕 REST API服务
├── test_*.py                   # 测试脚本
├── reports/                    # 报告目录
│   ├── commodity_mlp_v3_report.html  # 🆕 HTML可视化报告
│   └── comprehensive_test_*.json
└── OPTIMIZATION_V3_SUMMARY.md  # 本文档
```

---

## 快速开始

### 命令行使用

```bash
# 基础分析
python cli.py GC=F

# 使用真实数据
python cli.py GC=F --real

# 高级分析
python cli.py GC=F --advanced
```

### API使用

```bash
# 启动服务
python api_server.py --port 5000 --debug

# 测试端点
curl http://localhost:5000/api/health
curl http://localhost:5000/api/symbols
curl -X POST http://localhost:5000/api/train/GC=F -H "Content-Type: application/json"
```

### Python使用

```python
from data_fetcher_v3 import CommodityDataFetcher
from mlp_model_advanced import AdvancedCommodityMLP
from lstm_model import CommodityLSTMModel
from risk_backtest import RiskBacktestEngine

# 获取数据
fetcher = CommodityDataFetcher()
df = fetcher.fetch_data('GC=F', days=800)

# 训练LSTM
model = CommodityLSTMModel(input_size=15, seq_length=20)
model.train(X, y, epochs=30)

# 风险管理回测
engine = RiskBacktestEngine(initial_capital=100000)
results = engine.run_backtest(df, signal_col='signal')
```

---

## 下一步优化方向

| 优先级 | 优化项 | 预期效果 | 难度 |
|--------|--------|----------|------|
| P0 | 集成更多数据源(Akshare修复) | 解决yfinance速率限制 | 中 |
| P0 | 真实数据回测验证 | 验证实际市场表现 | 中 |
| P1 | 实时预测API | 低延迟在线预测 | 高 |
| P1 | 模型持久化与缓存 | 避免重复训练 | 低 |
| P2 | 前端可视化增强 | 更直观的图表交互 | 中 |
| P2 | 多商品组合策略 | 分散风险提升稳定性 | 高 |

---

## 技术栈

- **后端**: Python 3.13, Flask, Flask-CORS
- **机器学习**: scikit-learn, PyTorch, Optuna
- **数据处理**: pandas, numpy, yfinance
- **可视化**: 原生HTML/CSS/JS
- **测试**: pytest, unittest

---

## 版本历史

- **v3.0** (2026-09-01): LSTM模型、超参优化、多数据源、风险管理回测、REST API
- **v2.0** (2026-09-01): 特征工程增强、模型集成学习、时序交叉验证
- **v1.0** (2026-09-01): 基础MLP模型、CLI工具、Web界面

---

**项目状态**: ✅ 迭代完成，已推送至GitHub  
**最新提交**: `51e9bd5` - docs: 添加v3迭代HTML可视化报告
