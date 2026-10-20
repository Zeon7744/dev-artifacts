"""
策略测试模块

完整测试所有策略和回测引擎
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant.strategies.base import BaseStrategy
from quant.strategies.momentum_strategy import MomentumStrategy
from quant.strategies.mean_reversion import MeanReversionStrategy
from quant.strategies.grid_trading import GridTradingStrategy
from quant.strategies.statistical_arb import StatisticalArbStrategy
from quant.strategies.pairs_trading import PairsTradingStrategy
from quant.backtest.engine import BacktestEngine
from quant.backtest.portfolio import Portfolio
from quant.backtest.metrics import calculate_metrics
from quant.risk.manager import RiskManager
from quant.risk.position_sizing import PositionSizer
from quant.risk.stop_loss import StopLoss
from quant.data.mock_data import MockDataConnector
from quant.reports.performance import PerformanceReport


# ============ 测试数据生成 ============

@pytest.fixture
def sample_data():
    """生成测试用市场数据"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='B')
    n = len(dates)
    
    prices = 100 * np.exp(np.cumsum(np.random.normal(0, 0.02, n)))
    
    return pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.001, n)),
        'high': prices * (1 + abs(np.random.normal(0, 0.005, n))),
        'low': prices * (1 - abs(np.random.normal(0, 0.005, n))),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n),
    }, index=dates)


@pytest.fixture
def pair_data():
    """生成配对交易测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='B')
    n = len(dates)
    
    base = 100 * np.exp(np.cumsum(np.random.normal(0, 0.02, n)))
    pair = 100 * np.exp(np.cumsum(0.9 * np.random.normal(0, 0.02, n) + 0.1 * np.random.normal(0, 0.005, n)))
    
    return pd.DataFrame({
        'open': base * (1 + np.random.normal(0, 0.001, n)),
        'high': base * (1 + abs(np.random.normal(0, 0.005, n))),
        'low': base * (1 - abs(np.random.normal(0, 0.005, n))),
        'close': base,
        'pair_close': pair,
        'volume': np.random.randint(100000, 1000000, n),
    }, index=dates)


# ============ 策略测试 ============

class TestMomentumStrategy:
    """动量策略测试"""
    
    def test_init(self):
        """测试初始化"""
        strategy = MomentumStrategy()
        assert strategy.name == "动量策略"
        assert 'fast_period' in strategy.params
    
    def test_ma_cross_mode(self, sample_data):
        """测试均线交叉模式"""
        strategy = MomentumStrategy(mode='ma_cross', fast_period=10, slow_period=30)
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns
        assert set(result['signal'].unique()).issubset({-1, 0, 1})
    
    def test_rsi_mode(self, sample_data):
        """测试 RSI 模式"""
        strategy = MomentumStrategy(mode='rsi')
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns
    
    def test_macd_mode(self, sample_data):
        """测试 MACD 模式"""
        strategy = MomentumStrategy(mode='macd')
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns
    
    def test_combined_mode(self, sample_data):
        """测试组合模式"""
        strategy = MomentumStrategy(mode='combined')
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns


class TestMeanReversionStrategy:
    """均值回归策略测试"""
    
    def test_init(self):
        strategy = MeanReversionStrategy()
        assert strategy.name == "均值回归策略"
    
    def test_bollinger_mode(self, sample_data):
        strategy = MeanReversionStrategy(mode='bollinger')
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns
    
    def test_zscore_mode(self, sample_data):
        strategy = MeanReversionStrategy(mode='zscore')
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns
    
    def test_combined_mode(self, sample_data):
        strategy = MeanReversionStrategy(mode='combined')
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns


class TestGridTradingStrategy:
    """网格交易策略测试"""
    
    def test_init(self):
        strategy = GridTradingStrategy()
        assert strategy.name == "网格交易策略"
    
    def test_fixed_grid(self, sample_data):
        strategy = GridTradingStrategy(grid_size=0.02, num_grids=10)
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns
    
    def test_dynamic_grid(self, sample_data):
        strategy = GridTradingStrategy(dynamic=True)
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns


class TestStatisticalArbStrategy:
    """统计套利策略测试"""
    
    def test_init(self):
        strategy = StatisticalArbStrategy()
        assert strategy.name == "统计套利策略"
    
    def test_generate_signals(self, sample_data):
        strategy = StatisticalArbStrategy()
        result = strategy.generate_signals(sample_data)
        assert 'signal' in result.columns
        assert 'spread' in result.columns
        assert 'zscore' in result.columns
    
    def test_cointegration(self):
        """测试协整检验"""
        strategy = StatisticalArbStrategy()
        np.random.seed(42)
        x = pd.Series(np.cumsum(np.random.normal(0, 1, 200)))
        y = pd.Series(x.values * 0.5 + np.random.normal(0, 0.5, 200))
        result = strategy.test_cointegration(y, x)
        assert 'is_cointegrated' in result
        assert 'hedge_ratio' in result


class TestPairsTradingStrategy:
    """配对交易策略测试"""
    
    def test_init(self):
        strategy = PairsTradingStrategy()
        assert strategy.name == "配对交易策略"
    
    def test_generate_signals(self, pair_data):
        strategy = PairsTradingStrategy()
        result = strategy.generate_signals(pair_data)
        assert 'signal' in result.columns
        assert 'spread' in result.columns
    
    def test_missing_pair_column(self, sample_data):
        """测试缺少 pair_close 列"""
        strategy = PairsTradingStrategy()
        with pytest.raises(ValueError, match="pair_close"):
            strategy.generate_signals(sample_data)
    
    def test_find_pairs(self):
        """测试寻找配对"""
        strategy = PairsTradingStrategy()
        np.random.seed(42)
        data = {
            'A': pd.Series(np.cumsum(np.random.normal(0, 1, 100))),
            'B': pd.Series(np.cumsum(np.random.normal(0, 1, 100)) * 0.9),
            'C': pd.Series(np.random.normal(0, 1, 100)),
        }
        pairs = strategy.find_correlated_pairs(data, min_correlation=0.7)
        assert isinstance(pairs, list)


# ============ 回测引擎测试 ============

class TestBacktestEngine:
    """回测引擎测试"""
    
    def test_init(self):
        engine = BacktestEngine()
        assert engine.initial_capital == 100000.0
    
    def test_run(self, sample_data):
        """测试运行回测"""
        engine = BacktestEngine(initial_capital=100000)
        strategy = MomentumStrategy(mode='ma_cross')
        result = engine.run(strategy, sample_data)
        
        assert 'equity_curve' in result
        assert 'trades' in result
        assert 'metrics' in result
        assert 'signals' in result
    
    def test_metrics_structure(self, sample_data):
        """测试指标结构"""
        engine = BacktestEngine()
        strategy = MomentumStrategy(mode='rsi')
        result = engine.run(strategy, sample_data)
        
        metrics = result['metrics']
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'volatility' in metrics
    
    def test_custom_params(self, sample_data):
        """测试参数覆盖"""
        engine = BacktestEngine(initial_capital=200000)
        strategy = MomentumStrategy()
        result = engine.run(strategy, sample_data, params={'fast_period': 5, 'slow_period': 20})
        assert result is not None
    
    def test_invalid_data(self):
        """测试无效数据"""
        engine = BacktestEngine()
        strategy = MomentumStrategy()
        with pytest.raises(ValueError):
            engine.run(strategy, pd.DataFrame({'wrong': [1, 2, 3]}))


# ============ Portfolio 测试 ============

class TestPortfolio:
    """投资组合测试"""
    
    def test_init(self):
        portfolio = Portfolio(initial_capital=100000)
        assert portfolio.cash == 100000
        assert portfolio.total_equity == 100000
    
    def test_buy(self):
        portfolio = Portfolio(initial_capital=100000)
        success = portfolio.buy('BTC', 1.0, 50000)
        assert success
        assert 'BTC' in portfolio.positions
        assert portfolio.cash < 100000
    
    def test_sell(self):
        portfolio = Portfolio(initial_capital=100000)
        portfolio.buy('BTC', 1.0, 50000)
        success = portfolio.sell('BTC', 1.0, 55000)
        assert success
        assert 'BTC' not in portfolio.positions
        assert portfolio.cash > 50000
    
    def test_insufficient_funds(self):
        portfolio = Portfolio(initial_capital=100000)
        success = portfolio.buy('BTC', 100.0, 50000)
        assert not success
    
    def test_equity_curve(self):
        portfolio = Portfolio(initial_capital=100000)
        portfolio.update_equity(pd.Timestamp('2024-01-01'), {'BTC': 50000})
        portfolio.update_equity(pd.Timestamp('2024-01-02'), {'BTC': 52000})
        curve = portfolio.get_equity_curve()
        assert len(curve) == 2


# ============ Risk Manager 测试 ============

class TestRiskManager:
    """风险管理器测试"""
    
    def test_position_size(self):
        rm = RiskManager(max_position_pct=0.3)
        result = rm.check_position_size(100000, 50000, 1.0)
        assert result['allowed']
        assert result['max_quantity'] > 0
    
    def test_stop_loss(self):
        rm = RiskManager(stop_loss_pct=0.05)
        result = rm.check_stop_loss(100, 94, direction=1)
        assert result['should_stop']
    
    def test_no_stop_loss(self):
        rm = RiskManager(stop_loss_pct=0.05)
        result = rm.check_stop_loss(100, 97, direction=1)
        assert not result['should_stop']
    
    def test_drawdown_check(self):
        rm = RiskManager(max_drawdown_pct=0.15)
        equity = pd.Series([100, 95, 90, 84, 83], 
                          index=pd.date_range('2024-01-01', periods=5))
        result = rm.check_drawdown(equity)
        assert 'is_breached' in result
    
    def test_var(self):
        rm = RiskManager()
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 252))
        var = rm.calculate_var(returns)
        assert var > 0
    
    def test_risk_rating(self):
        rm = RiskManager()
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 252))
        rating = rm.risk_rating(returns)
        assert 'rating' in rating
        assert 'score' in rating


# ============ Position Sizer 测试 ============

class TestPositionSizer:
    """仓位管理测试"""
    
    def test_fixed_pct(self):
        sizer = PositionSizer(method='fixed_pct', max_position_pct=0.3)
        result = sizer.calculate(100000, 100)
        assert result['position_pct'] == 0.3
    
    def test_kelly(self):
        sizer = PositionSizer(method='kelly')
        result = sizer.calculate(100000, 100, win_rate=0.6, avg_win=0.03, avg_loss=0.01)
        assert result['allowed']
        assert result['position_pct'] > 0


# ============ Stop Loss 测试 ============

class TestStopLoss:
    """止损测试"""
    
    def test_fixed_stop_loss(self):
        sl = StopLoss(stop_loss_pct=0.05)
        result = sl.check(100, 94, direction=1)
        assert result['should_stop']
    
    def test_trailing_stop(self):
        sl = StopLoss(method='trailing', trailing_pct=0.03)
        # 价格上涨到 110
        sl.check(100, 110, direction=1)
        # 跟踪止损线 = 110 * 0.97 = 106.7
        # 价格回落到 105，低于 106.7，应触发止损
        result = sl.check(100, 105, direction=1)
        assert result['should_stop']  # 105 < 106.7


# ============ Metrics 测试 ============

class TestMetrics:
    """指标计算测试"""
    
    def test_total_return(self):
        equity = pd.Series([100, 110, 120], index=pd.date_range('2024-01-01', periods=3))
        metrics = calculate_metrics(equity)
        assert metrics['total_return'] == pytest.approx(0.2, rel=0.01)
    
    def test_max_drawdown(self):
        equity = pd.Series([100, 110, 90, 95], index=pd.date_range('2024-01-01', periods=4))
        metrics = calculate_metrics(equity)
        assert metrics['max_drawdown'] < 0
    
    def test_sharpe_ratio(self):
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        equity = (1 + returns).cumprod()
        metrics = calculate_metrics(equity)
        assert 'sharpe_ratio' in metrics


# ============ Data Connector 测试 ============

class TestMockDataConnector:
    """模拟数据连接器测试"""
    
    def test_fetch_data(self):
        connector = MockDataConnector(seed=42)
        data = connector.fetch_data('TEST', '2023-01-01', '2024-01-01')
        assert len(data) > 0
        assert 'open' in data.columns
        assert 'close' in data.columns
    
    def test_fetch_realtime(self):
        connector = MockDataConnector()
        result = connector.fetch_realtime('TEST')
        assert 'price' in result
    
    def test_pair_data(self):
        connector = MockDataConnector()
        data = connector.generate_pair_data('2023-01-01', '2024-01-01', correlation=0.9)
        assert 'close' in data.columns
        assert 'pair_close' in data.columns


# ============ Performance Report 测试 ============

class TestPerformanceReport:
    """绩效报告测试"""
    
    def test_generate(self, sample_data, tmp_path):
        """测试报告生成"""
        engine = BacktestEngine()
        strategy = MomentumStrategy(mode='ma_cross')
        result = engine.run(strategy, sample_data)
        
        report = PerformanceReport(output_dir=str(tmp_path))
        html_path = report.generate(result)
        assert os.path.exists(html_path)


# ============ 集成测试 ============

class TestIntegration:
    """端到端集成测试"""
    
    def test_full_backtest_momentum(self):
        """完整动量策略回测"""
        connector = MockDataConnector(trend='up', seed=42)
        data = connector.fetch_data('TEST', '2023-01-01', '2024-01-01')
        
        engine = BacktestEngine(initial_capital=100000)
        strategy = MomentumStrategy(mode='combined')
        result = engine.run(strategy, data)
        
        assert result['metrics']['total_periods'] > 0
        assert len(result['equity_curve']) > 0
    
    def test_full_backtest_mean_reversion(self):
        """完整均值回归策略回测"""
        connector = MockDataConnector(trend='sideways', seed=42)
        data = connector.fetch_data('TEST', '2023-01-01', '2024-01-01')
        
        engine = BacktestEngine(initial_capital=100000)
        strategy = MeanReversionStrategy(mode='bollinger')
        result = engine.run(strategy, data)
        
        assert 'metrics' in result
    
    def test_full_backtest_grid(self):
        """完整网格策略回测"""
        connector = MockDataConnector(trend='sideways', seed=42)
        data = connector.fetch_data('TEST', '2023-01-01', '2024-01-01')
        
        engine = BacktestEngine(initial_capital=100000)
        strategy = GridTradingStrategy(grid_size=0.02)
        result = engine.run(strategy, data)
        
        assert 'metrics' in result
    
    def test_all_strategies_runnable(self):
        """测试所有策略可运行"""
        connector = MockDataConnector(trend='mixed', seed=42)
        data = connector.fetch_data('TEST', '2023-01-01', '2024-01-01')
        
        strategies = [
            MomentumStrategy(),
            MeanReversionStrategy(),
            GridTradingStrategy(),
            StatisticalArbStrategy(),
        ]
        
        for strategy in strategies:
            engine = BacktestEngine(initial_capital=100000)
            result = engine.run(strategy, data)
            assert 'metrics' in result, f"{strategy.name} 回测失败"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
