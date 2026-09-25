# 🗡️ 量化交易策略库 (Quantitative Trading Strategy Library)

> dev-artifacts 量化交易模块 - 完整的策略回测框架

## 项目结构

```
quant/
├── backtest/           # 回测引擎
│   ├── engine.py       # 核心回测引擎
│   ├── portfolio.py    # 投资组合管理
│   └── metrics.py      # 绩效指标计算
├── strategies/         # 策略模板
│   ├── base.py                 # 策略基类
│   ├── momentum_strategy.py    # 动量策略
│   ├── mean_reversion.py       # 均值回归策略
│   ├── grid_trading.py         # 网格交易策略
│   ├── statistical_arb.py      # 统计套利策略
│   └── pairs_trading.py        # 配对交易策略
├── data/               # 数据连接器
│   ├── base.py                 # 连接器基类
│   ├── mock_data.py            # 模拟数据
│   ├── yfinance_connector.py   # Yahoo Finance (美股)
│   ├── binance_connector.py    # Binance (加密货币)
│   ├── akshare_connector.py    # AKShare (A股)
│   └── tushare_connector.py    # Tushare (专业数据)
├── risk/               # 风险管理
│   ├── manager.py          # 风险管理器
│   ├── position_sizing.py   # 仓位管理
│   └── stop_loss.py        # 止损模块
├── reports/            # 绩效报告
│   └── performance.py      # 报告生成器
├── tests/              # 测试
│   └── test_strategies.py
└── examples/           # 示例
    └── demo_backtest.py
```

## 快速开始

### 1. 基本回测

```python
from quant.data.mock_data import MockDataConnector
from quant.strategies import MomentumStrategy
from quant.backtest.engine import BacktestEngine

# 获取数据
connector = MockDataConnector(trend='up', seed=42)
data = connector.fetch_data('BTCUSDT', '2023-01-01', '2024-01-01')

# 创建策略
strategy = MomentumStrategy(mode='combined', fast_period=10, slow_period=30)

# 运行回测
engine = BacktestEngine(initial_capital=100000)
result = engine.run(strategy, data)

# 查看结果
print(f"总收益率: {result['metrics']['total_return']:.2%}")
print(f"夏普比率: {result['metrics']['sharpe_ratio']:.4f}")
```

### 2. 使用真实数据

```python
# 美股数据 (需要 yfinance)
from quant.data import YFinanceConnector
connector = YFinanceConnector()
data = connector.fetch_data('AAPL', '2023-01-01', '2024-01-01')

# 加密货币数据 (需要 requests)
from quant.data import BinanceConnector
connector = BinanceConnector()
data = connector.fetch_data('BTCUSDT', '2023-01-01', '2024-01-01')

# A 股数据 (需要 akshare)
from quant.data import AKShareConnector
connector = AKShareConnector()
data = connector.fetch_data('000001', '2023-01-01', '2024-01-01')
```

### 3. 风险管理

```python
from quant.risk import RiskManager

rm = RiskManager(
    max_position_pct=0.3,    # 最大仓位 30%
    max_drawdown_pct=0.15,   # 最大回撤 15%
    stop_loss_pct=0.05,      # 止损 5%
)

# 检查仓位
result = rm.check_position_size(capital=100000, price=50000, quantity=1.0)

# 风险评级
rating = rm.risk_rating(returns)
print(f"风险等级: {rating['rating']}")
```

### 4. 生成报告

```python
from quant.reports import PerformanceReport

report = PerformanceReport(output_dir='./output')
report.generate(result, title="我的策略回测报告")
```

## 策略说明

### 动量策略 (MomentumStrategy)

基于趋势跟踪的交易策略。

| 模式 | 说明 |
|------|------|
| `ma_cross` | 均线交叉 (EMA10/EMA30) |
| `rsi` | RSI 超买超卖 (30/70) |
| `macd` | MACD 金叉死叉 |
| `combined` | 多指标组合确认 |

```python
strategy = MomentumStrategy(mode='combined', fast_period=10, slow_period=30)
```

### 均值回归策略 (MeanReversionStrategy)

价格偏离均值后预期回归。

| 模式 | 说明 |
|------|------|
| `bollinger` | 布林带突破 |
| `zscore` | Z-score 回归 |
| `combined` | 布林带 + Z-score |

```python
strategy = MeanReversionStrategy(mode='bollinger', bb_period=20, bb_std=2.0)
```

### 网格交易策略 (GridTradingStrategy)

在价格区间内设置网格，自动低买高卖。

```python
strategy = GridTradingStrategy(
    grid_size=0.02,     # 网格间距 2%
    num_grids=10,       # 10 条网格线
    dynamic=False,      # 固定网格
)
```

### 统计套利策略 (StatisticalArbStrategy)

基于价差统计特性的套利策略。

```python
strategy = StatisticalArbStrategy(
    lookback_period=60,
    entry_zscore=2.0,
    exit_zscore=0.5,
)
```

### 配对交易策略 (PairsTradingStrategy)

利用两个高相关性资产的价差交易。

```python
strategy = PairsTradingStrategy(
    lookback_period=60,
    entry_threshold=2.0,
    min_correlation=0.8,
)
```

## 绩效指标

| 指标 | 说明 | 优秀标准 |
|------|------|----------|
| 总收益率 | 策略总回报 | > 20% |
| 年化收益率 | 年化后的回报 | > 15% |
| 夏普比率 | 风险调整收益 | > 1.0 |
| 最大回撤 | 最大亏损幅度 | < 15% |
| Sortino 比率 | 下行风险调整收益 | > 1.5 |
| Calmar 比率 | 收益/最大回撤 | > 2.0 |
| 胜率 | 盈利交易占比 | > 50% |
| 盈亏比 | 平均盈利/平均亏损 | > 1.5 |

## 运行测试

```bash
cd dev-artifacts
python -m pytest quant/tests/test_strategies.py -v
```

## 运行演示

```bash
cd dev-artifacts
python quant/examples/demo_backtest.py
```

## 自定义策略

```python
from quant.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "我的策略"
    
    def init(self):
        self.params.setdefault('period', 20)
    
    def generate_signals(self, data):
        df = data.copy()
        close = df['close']
        
        # 你的信号逻辑
        sma = self._calculate_sma(close, self.params['period'])
        df['signal'] = 0
        df.loc[close > sma, 'signal'] = 1
        df.loc[close < sma, 'signal'] = -1
        
        return df
```

## 依赖

核心依赖（无外部依赖即可运行）:
- pandas
- numpy

可选依赖:
- yfinance (Yahoo Finance 数据)
- akshare (A 股数据)
- tushare (专业数据)
- matplotlib (图表可视化)
- requests (API 调用)

## 许可

MIT License

---

**⚠️ 免责声明**: 本库仅供学习和研究使用，不构成投资建议。量化交易存在风险，请谨慎使用。
