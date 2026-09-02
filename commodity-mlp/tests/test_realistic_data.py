#!/usr/bin/env python3
"""
大宗商品MLP投资分析工具 - 真实市场特征模拟测试
验证模型在不同数据分布下的泛化能力
"""

import numpy as np
import pandas as pd
from datetime import datetime
import time
import sys
import os
import json

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feature_engineering_v2 import FeatureEngineer as FE2
from mlp_model_advanced import AdvancedCommodityMLP
from backtest import BacktestEngine


def generate_simple_gbm(symbol, days=800, seed=None):
    """简单几何布朗运动数据"""
    np.random.seed(seed if seed else hash(symbol) % 2**32)
    
    base_prices = {'GC=F': 1950, 'CL=F': 80, 'SI=F': 23, 'HG=F': 3.8, 'NG=F': 2.5}
    base_price = base_prices.get(symbol, 100)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
    returns = np.random.normal(0.0001, 0.015, days)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # 生成完整的OHLCV数据
    volumes = np.random.lognormal(10, 0.5, days)
    highs = prices * (1 + np.random.uniform(0, 0.005, days))
    lows = prices * (1 - np.random.uniform(0, 0.005, days))
    opens = prices * (1 + np.random.normal(0, 0.002, days))
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    df['Target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
    
    return df


def generate_complex_simulation(symbol, days=800, seed=None):
    """复杂模拟数据（含趋势和波动聚集）"""
    np.random.seed(seed if seed else hash(symbol) % 2**32)
    
    base_prices = {'GC=F': 1950, 'CL=F': 80, 'SI=F': 23, 'HG=F': 3.8, 'NG=F': 2.5}
    volatility_params = {
        'GC=F': {'base': 0.012, 'trend': 0.0002},
        'CL=F': {'base': 0.020, 'trend': 0.0003},
        'SI=F': {'base': 0.018, 'trend': 0.0002},
        'HG=F': {'base': 0.015, 'trend': 0.0001},
        'NG=F': {'base': 0.025, 'trend': 0.0004}
    }
    
    base_price = base_prices.get(symbol, 100)
    params = volatility_params.get(symbol, {'base': 0.015, 'trend': 0.0002})
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
    prices = [base_price]
    
    for i in range(1, days):
        phase = (i % 600) / 600 * 2 * np.pi
        trend_component = params['trend'] * np.sin(phase)
        
        if i > 10:
            recent_vol = np.std([np.log(prices[j]/prices[j-1]) for j in range(max(0,i-10), i)])
            vol_clustering = 0.9 * recent_vol + 0.1 * params['base']
        else:
            vol_clustering = params['base']
        
        shock = np.random.normal(0, vol_clustering)
        daily_return = trend_component + shock
        new_price = prices[-1] * (1 + daily_return)
        prices.append(new_price)
    
    # 生成完整的OHLCV数据
    volumes = np.random.lognormal(10, 0.5, days)
    highs = np.array(prices) * (1 + np.random.uniform(0, 0.005, days))
    lows = np.array(prices) * (1 - np.random.uniform(0, 0.005, days))
    opens = np.array(prices) * (1 + np.random.normal(0, 0.002, days))
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    df['Target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
    
    return df


def run_comparison_test():
    """运行对比测试"""
    print("=" * 80)
    print("大宗商品MLP投资分析 - 真实市场特征模拟测试")
    print("=" * 80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    symbols = ['GC=F', 'CL=F', 'SI=F', 'HG=F', 'NG=F']
    all_results = []
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"商品: {symbol}")
        print(f"{'='*60}")
        
        symbol_results = {'symbol': symbol}
        
        for method_name, method in [('简单GBM', generate_simple_gbm), ('复杂模拟', generate_complex_simulation)]:
            print(f"\n  使用 {method_name} 数据...")
            
            # 生成数据
            df = method(symbol, days=800)
            
            # 特征工程
            fe = FE2()
            features = fe.extract_features(df)
            target = df['Target'].iloc[:len(features)]
            
            print(f"    样本数: {len(features)}, 特征数: {features.shape[1]}")
            print(f"    目标分布: 上涨{target.sum()}次 ({target.mean()*100:.1f}%), 下跌{len(target)-target.sum()}次")
            
            # 训练模型
            model = AdvancedCommodityMLP(use_ensemble=True, feature_selection=True)
            metrics = model.train(features, target)
            
            # 预测信号
            latest_features = features.tail(1)
            prediction = model.predict(latest_features)[0]
            proba = model.predict_proba(latest_features)[0]
            
            signal = "看涨" if prediction == 1 else "看跌"
            confidence = float(proba) * 100
            
            # 回测
            backtest_engine = BacktestEngine(initial_capital=100000)
            signals = model.generate_signals(features)
            backtest_result = backtest_engine.run_backtest(df.head(len(signals)), signals)
            
            print(f"\n    预测信号: {signal} (置信度: {confidence:.1f}%)")
            print(f"    测试准确率: {metrics['test_accuracy']:.4f}")
            print(f"    时序CV: {metrics['cv_mean']:.4f} ± {metrics['cv_std']:.4f}")
            print(f"    回测收益: {backtest_result['total_return_pct']:.2f}%")
            print(f"    夏普比率: {backtest_result['sharpe_ratio']:.4f}")
            print(f"    最大回撤: {backtest_result['max_drawdown_pct']:.2f}%")
            
            # 保存结果
            symbol_results[f'{method_name}_accuracy'] = metrics['test_accuracy']
            symbol_results[f'{method_name}_cv_mean'] = metrics['cv_mean']
            symbol_results[f'{method_name}_cv_std'] = metrics['cv_std']
            symbol_results[f'{method_name}_return'] = backtest_result['total_return_pct']
            symbol_results[f'{method_name}_sharpe'] = backtest_result['sharpe_ratio']
            symbol_results[f'{method_name}_drawdown'] = backtest_result['max_drawdown_pct']
            symbol_results[f'{method_name}_signal'] = signal
            symbol_results[f'{method_name}_confidence'] = confidence
        
        all_results.append(symbol_results)
        time.sleep(0.5)  # 避免过快请求
    
    # 生成汇总报告
    print(f"\n{'='*80}")
    print("对比测试汇总报告")
    print(f"{'='*80}")
    
    print(f"\n{'商品':<10} {'方法':<12} {'测试准确率':<12} {'时序CV':<15} {'回测收益':<10} {'信号':<6} {'置信度':<8}")
    print("-" * 80)
    
    for r in all_results:
        simple_acc = r.get('简单GBM_accuracy', 0)
        complex_acc = r.get('复杂模拟_accuracy', 0)
        diff = complex_acc - simple_acc
        diff_marker = "↑" if diff > 0 else "↓" if diff < 0 else "="
        
        print(f"{r['symbol']:<10} {'简单GBM':<12} {simple_acc:<12.4f} {r.get('简单GBM_cv_mean', 0):<15.4f} {r.get('简单GBM_return', 0):<10.2f}% {r.get('简单GBM_signal', ''):<6} {r.get('简单GBM_confidence', 0):<8.1f}%")
        print(f"{'':10} {'复杂模拟':<12} {complex_acc:<12.4f} {r.get('复杂模拟_cv_mean', 0):<15.4f} {r.get('复杂模拟_return', 0):<10.2f}% {r.get('复杂模拟_signal', ''):<6} {r.get('复杂模拟_confidence', 0):<8.1f}%")
        print(f"{'':10} {'差异':<12} {diff:+.4f} {diff_marker:<15} {'':10}")
        print()
    
    # 保存报告
    report_path = './reports/realistic_data_comparison.json'
    os.makedirs('./reports', exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"报告已保存: {report_path}")
    
    return all_results


if __name__ == '__main__':
    results = run_comparison_test()
