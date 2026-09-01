#!/usr/bin/env python3
"""API功能测试脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher_v3 import CommodityDataFetcher
from mlp_model_advanced import AdvancedCommodityMLP
from lstm_model import CommodityLSTMModel
from hyperparameter_optimizer import HyperparameterOptimizer
from risk_manager import RiskManager
from risk_backtest import RiskBacktestEngine
import pandas as pd
import numpy as np
from datetime import datetime

def test_data_fetcher():
    print("=" * 60)
    print("测试1: 数据获取模块")
    print("=" * 60)
    fetcher = CommodityDataFetcher(primary_source='yfinance', fallback_source='simulated')
    data = fetcher.fetch_data('GC=F', days=60)
    if data is not None and len(data) > 0:
        print(f"成功获取黄金(GC=F)数据: {len(data)}条")
        print(f"日期范围: {data.index[0]} ~ {data.index[-1]}")
        return True
    print("使用模拟数据测试...")
    data = fetcher.fetch_simulated_data('GC=F', days=60)
    print(f"成功获取模拟数据: {len(data)}条")
    return True

def test_mlp_model():
    print("\n" + "=" * 60)
    print("测试2: MLP模型")
    print("=" * 60)
    np.random.seed(42)
    data = pd.DataFrame({
        'close': np.cumsum(np.random.randn(100)) + 100,
        'volume': np.random.randint(1000, 5000, 100)
    }, index=pd.date_range(start='2024-01-01', periods=100, freq='D'))
    model = AdvancedCommodityMLP(use_ensemble=True, feature_selection=True)
    model.train(data, target_col='close', epochs=10, verbose=0)
    pred = model.predict(data)
    print(f"MLP模型训练完成")
    print(f"预测结果样本: {pred.head().to_dict()}")
    return True

def test_lstm_model():
    print("\n" + "=" * 60)
    print("测试3: LSTM模型")
    print("=" * 60)
    np.random.seed(42)
    sequence = np.random.randn(200, 1) * 10 + 100
    X, y = [], []
    seq_len = 10
    for i in range(len(sequence) - seq_len):
        X.append(sequence[i:i+seq_len])
        y.append(sequence[i+seq_len])
    X, y = np.array(X), np.array(y)
    model = CommodityLSTMModel(input_size=1, seq_length=seq_len)
    model.train(X, y, epochs=10, verbose=0)
    pred = model.predict(X[:5])
    print(f"LSTM模型训练完成")
    print(f"输入形状: {X.shape}")
    print(f"预测结果: {pred.flatten()[:5]}")
    return True

def test_hyperparameter_optimizer():
    print("\n" + "=" * 60)
    print("测试4: 超参数优化器")
    print("=" * 60)
    np.random.seed(42)
    data = pd.DataFrame({
        'close': np.cumsum(np.random.randn(100)) + 100
    }, index=pd.date_range(start='2024-01-01', periods=100, freq='D'))
    optimizer = HyperparameterOptimizer(n_trials=3)
    best_params = optimizer.optimize(data, target_col='close')
    print(f"超参数优化完成")
    print(f"最佳分数: {best_params.get('best_score', 'N/A')}")
    return True

def test_risk_manager():
    print("\n" + "=" * 60)
    print("测试5: 风险管理")
    print("=" * 60)
    risk_config = {
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05,
        'max_daily_loss_pct': 0.03,
        'max_consecutive_losses': 3
    }
    risk_manager = RiskManager(**risk_config)
    positions = []
    for i in range(10):
        signal = 1 if i % 3 == 0 else -1
        pnl = np.random.randn() * 0.01
        action = risk_manager.evaluate_signal(signal, pnl, day_counter=i)
        if action != 'hold':
            positions.append({'day': i, 'action': action})
    print(f"风险管理测试完成")
    print(f"触发交易: {len(positions)}次")
    return True

def test_risk_backtest():
    print("\n" + "=" * 60)
    print("测试6: 风险管理回测引擎")
    print("=" * 60)
    risk_config = {
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05,
        'max_daily_loss_pct': 0.03,
        'max_consecutive_losses': 3
    }
    engine = RiskBacktestEngine(initial_capital=100000, risk_config=risk_config)
    np.random.seed(42)
    prices = np.cumsum(np.random.randn(100)) + 100
    df = pd.DataFrame({'close': prices}, index=pd.date_range(start='2024-01-01', periods=100, freq='D'))
    df['signal'] = np.where(df['close'].diff() > 0, 1, -1)
    df.loc[df.index[0], 'signal'] = 0
    results = engine.run_backtest(df, symbol='TEST', signal_col='signal')
    print(f"风险管理回测完成")
    print(f"初始资金: ${results['initial_capital']:,.2f}")
    print(f"最终资金: ${results['final_value']:,.2f}")
    print(f"总收益: {results['total_return']:.2f}%")
    print(f"夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"最大回撤: {results['max_drawdown']:.2f}%")
    print(f"交易次数: {results['total_trades']}")
    return True

def main():
    print("\n" + "=" * 60)
    print("大宗商品MLP投资分析工具 - API功能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    tests = [test_data_fetcher, test_mlp_model, test_lstm_model, 
             test_hyperparameter_optimizer, test_risk_manager, test_risk_backtest]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"失败: {test.__name__} - {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "通过" if result else "失败"
        print(f"{status}: {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n所有测试通过！")
        return 0
    else:
        print(f"\n{total - passed} 个测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
