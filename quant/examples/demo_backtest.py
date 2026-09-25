"""
回测演示脚本

展示量化策略库的完整使用流程
"""

import sys
import os

# 添加 dev-artifacts 根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from quant.data.mock_data import MockDataConnector
from quant.strategies import (
    MomentumStrategy,
    MeanReversionStrategy,
    GridTradingStrategy,
    StatisticalArbStrategy,
    PairsTradingStrategy,
)
from quant.backtest.engine import BacktestEngine
from quant.risk.manager import RiskManager
from quant.reports.performance import PerformanceReport


def demo_momentum():
    """演示动量策略"""
    print("\n" + "="*60)
    print("  🚀 动量策略回测演示")
    print("="*60)
    
    # 1. 获取数据
    connector = MockDataConnector(trend='up', seed=42)
    data = connector.fetch_data('BTCUSDT', '2023-01-01', '2024-01-01')
    print(f"\n数据: {len(data)} 条, 日期范围: {data.index[0].date()} ~ {data.index[-1].date()}")
    
    # 2. 创建策略
    strategy = MomentumStrategy(
        mode='combined',
        fast_period=10,
        slow_period=30,
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70,
    )
    print(f"策略: {strategy.name} - {strategy.description}")
    
    # 3. 运行回测
    engine = BacktestEngine(initial_capital=100000, commission_rate=0.001)
    result = engine.run(strategy, data)
    
    # 4. 风险评估
    rm = RiskManager(max_drawdown_pct=0.2)
    returns = result['equity_curve'].pct_change().fillna(0)
    risk = rm.risk_rating(returns)
    print(f"\n风险评级: {risk['rating']} (得分: {risk['score']})")
    
    return result


def demo_mean_reversion():
    """演示均值回归策略"""
    print("\n" + "="*60)
    print("  📊 均值回归策略回测演示")
    print("="*60)
    
    connector = MockDataConnector(trend='sideways', volatility=0.03, seed=123)
    data = connector.fetch_data('ETHUSDT', '2023-01-01', '2024-01-01')
    
    strategy = MeanReversionStrategy(mode='bollinger', bb_period=20, bb_std=2.0)
    
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(strategy, data)
    
    return result


def demo_grid_trading():
    """演示网格交易策略"""
    print("\n" + "="*60)
    print("  🔲 网格交易策略回测演示")
    print("="*60)
    
    connector = MockDataConnector(trend='sideways', volatility=0.015, seed=456)
    data = connector.fetch_data('BNBUSDT', '2023-01-01', '2024-01-01')
    
    strategy = GridTradingStrategy(grid_size=0.02, num_grids=15)
    
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(strategy, data)
    
    return result


def demo_comparison():
    """策略对比"""
    print("\n" + "="*60)
    print("  📈 策略对比分析")
    print("="*60)
    
    connector = MockDataConnector(trend='mixed', seed=42)
    data = connector.fetch_data('COMPARISON', '2023-01-01', '2024-01-01')
    
    strategies = {
        '动量策略': MomentumStrategy(mode='combined'),
        '均值回归': MeanReversionStrategy(mode='bollinger'),
        '网格交易': GridTradingStrategy(grid_size=0.02),
        '统计套利': StatisticalArbStrategy(),
    }
    
    results = {}
    for name, strategy in strategies.items():
        engine = BacktestEngine(initial_capital=100000)
        result = engine.run(strategy, data)
        results[name] = result['metrics']
    
    # 对比表格
    print(f"\n{'策略':<12} {'总收益':>10} {'年化收益':>10} {'夏普':>8} {'最大回撤':>10} {'胜率':>8}")
    print("-" * 70)
    
    for name, m in results.items():
        ts = m.get('trade_stats', {})
        print(f"{name:<12} {m['total_return']:>9.2%} {m['annual_return']:>9.2%} "
              f"{m['sharpe_ratio']:>8.4f} {m['max_drawdown']:>9.2%} "
              f"{ts.get('win_rate', 0):>7.1%}")
    
    return results


def main():
    """主函数"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        🗡️ 量化交易策略库 - 回测演示                    ║")
    print("║        Quantitative Trading Strategy Library             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # 运行各策略演示
    r1 = demo_momentum()
    r2 = demo_mean_reversion()
    r3 = demo_grid_trading()
    
    # 策略对比
    comparison = demo_comparison()
    
    # 生成报告
    print("\n" + "="*60)
    print("  📋 生成回测报告")
    print("="*60)
    
    report = PerformanceReport(output_dir='./output')
    report_path = report.generate(r1, "动量策略回测报告")
    
    print(f"\n{'='*60}")
    print(f"  ✅ 演示完成!")
    print(f"  报告路径: {report_path}")
    print(f"{'='*60}")
    
    return r1


if __name__ == '__main__':
    main()
