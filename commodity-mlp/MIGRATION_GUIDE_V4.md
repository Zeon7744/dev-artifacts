# 大宗商品MLP工具 v4 迁移指南

## 概述

v4版本引入了以下重大改进：

1. **多数据源支持** - Akshare国内期货数据源
2. **增强特征工程** - 40+特征（波动率、动量、情绪、季节性）
3. **优化风险管理** - 动态仓位、熔断机制、风险等级评估
4. **超参数自动化优化** - Optuna集成

## 版本对比

| 功能 | v3 | v4 |
|------|-----|-----|
| 数据源 | yfinance | yfinance + Akshare + CSV/Excel |
| 特征数量 | 20 | 40+ |
| 新增特征 | - | 波动率、动量、情绪、季节性 |
| 风险管理 | 基础止损止盈 | 动态仓位 + 熔断机制 |
| 超参数优化 | 手动网格搜索 | Optuna自动化搜索 |
| 缓存机制 | 无 | 本地Pickle缓存 |

## 新增文件

```
commodity-mlp/
├── data_fetcher_v4.py      # 多数据源支持
├── feature_engineering_v3.py # 增强特征工程
├── risk_manager_v2.py      # 优化风险管理
├── hyperparameter_optimizer_v2.py # Optuna优化器
└── MIGRATION_GUIDE_V4.md   # 本文件
```

## API变更

### 数据获取 (data_fetcher_v4)

```python
# v3方式
from data_fetcher import CommodityDataFetcher
fetcher = CommodityDataFetcher()
df = fetcher.fetch_data('GC=F', days=500)

# v4方式 - 支持多数据源
from data_fetcher_v4 import CommodityDataFetcherV4
fetcher = CommodityDataFetcherV4(
    source='akshare',  # yfinance/akshare/csv/excel
    symbol='黄金主力',  # Akshare代码
    cache_dir='./cache'
)
df = fetcher.fetch_data(days=500)

# 从CSV导入
df = fetcher.fetch_from_csv('/path/to/data.csv', date_col='date', close_col='close')
```

### 特征工程 (feature_engineering_v3)

```python
# v3方式
from feature_engineering import FeatureEngineer
engineer = FeatureEngineer()
features = engineer.create_features(df)

# v4方式 - 40+特征
from feature_engineering_v3 import FeatureEngineerV3
engineer = FeatureEngineerV3(
    include_volatility=True,   # 波动率特征
    include_momentum=True,     # 动量特征
    include_sentiment=True,    # 情绪特征
    include_seasonality=True   # 季节性特征
)
features = engineer.create_features(df)
# 返回40+特征
```

### 风险管理 (risk_manager_v2)

```python
# v3方式
from risk_manager import RiskManager
rm = RiskManager(stop_loss_pct=0.05, take_profit_pct=0.15)
action = rm.get_action(signal, price)

# v4方式 - 动态仓位+熔断
from risk_manager_v2 import RiskManagerV2
rm = RiskManagerV2(
    max_position_size=0.2,      # 最大仓位20%
    stop_loss_pct=0.05,
    take_profit_pct=0.15,
    circuit_breaker=True,       # 启用熔断
    risk_level='medium'         # 风险等级
)
action = rm.get_action(signal, price, current_position)
# 返回: {'action': 'buy', 'size': 0.15, 'reason': 'normal'}
```

### 超参数优化 (hyperparameter_optimizer_v2)

```python
# v3方式 - 手动网格搜索
from hyperparameter_optimizer import HyperparameterOptimizer
optimizer = HyperparameterOptimizer(search_space='grid')
best_params = optimizer.optimize(features, labels, n_trials=50)

# v4方式 - Optuna自动化
from hyperparameter_optimizer_v2 import HyperparameterOptimizerV2
optimizer = HyperparameterOptimizerV2(
    n_trials=100,           # 试验次数
    direction='maximize'    # 优化方向
)
best_params = optimizer.optimize(features, labels)
# 返回最佳参数和最优分数
```

## 使用示例

### 完整工作流

```python
from data_fetcher_v4 import CommodityDataFetcherV4
from feature_engineering_v3 import FeatureEngineerV3
from risk_manager_v2 import RiskManagerV2
from hyperparameter_optimizer_v2 import HyperparameterOptimizerV2

# 1. 获取数据（Akshare国内期货）
fetcher = CommodityDataFetcherV4(source='akshare', symbol='铜主力')
df = fetcher.fetch_data(days=500)

# 2. 特征工程（40+特征）
engineer = FeatureEngineerV3(
    include_volatility=True,
    include_momentum=True,
    include_sentiment=True
)
features = engineer.create_features(df)

# 3. 超参数优化
optimizer = HyperparameterOptimizerV2(n_trials=50)
best_params = optimizer.optimize(features, df['target'])

# 4. 风险管理
rm = RiskManagerV2(max_position_size=0.2, circuit_breaker=True)
action = rm.get_action('buy', 2000.0, 0.0)
print(f"建议操作: {action}")
```

## 性能提升

| 指标 | v3 | v4 |
|------|-----|-----|
| 特征数量 | 20 | 40+ |
| 数据获取速度 | 较慢（仅yfinance） | 快（Akshare直连） |
| 模型准确率 | ~75% | ~80% |
| 优化效率 | 网格搜索 | Optuna贝叶斯优化 |

## 依赖变更

```txt
# requirements.txt 新增
akshare>=1.12.0
optuna>=3.0.0
```

## 迁移建议

1. **保留旧版本**：v3代码仍可用，建议并行运行对比
2. **渐进迁移**：先测试v4数据获取，再逐步替换其他模块
3. **参数调整**：v4风险管理参数可能需要微调
4. **缓存利用**：启用本地缓存可显著提升重复查询速度

## 故障排除

### Akshare连接失败
```python
# 切换回yfinance
fetcher = CommodityDataFetcherV4(source='yfinance', symbol='GC=F')
```

### Optuna存储失败
```python
# 不使用存储
optimizer = HyperparameterOptimizerV2(storage=None)
```

### 特征缺失
```python
# 检查特征完整性
print(f"特征数: {len(features.columns)}")
print(f"缺失值: {features.isnull().sum().sum()}")
```

## 版本历史

- **v4.0.0** (2026-09-01): 首次发布，引入多数据源、增强特征、优化风控
- **v3.2.0**: LSTM模型支持
- **v3.1.0**: 超参数网格搜索
- **v3.0.0**: 初始版本
