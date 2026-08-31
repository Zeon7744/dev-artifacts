#!/usr/bin/env python3
"""
大宗商品MLP投资分析工具 - 综合测试脚本
对比原版和优化版模型性能
"""

import sys
import os
import json
from datetime import datetime
import numpy as np
import pandas as pd

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import CommodityDataFetcher
from feature_engineering import FeatureEngineer
from feature_engineering_v2 import FeatureEngineer as FE2
from mlp_model import CommodityMLPModel
from mlp_model_v2 import CommodityMLPModel as MLP2
from backtest import BacktestEngine
from risk_manager import RiskManager


def run_comparison_test(symbols=None, days=500, output_dir='./reports'):
    """运行对比测试"""
    if symbols is None:
        symbols = ['GC=F', 'CL=F', 'SI=F', 'HG=F', 'NG=F']
    
    print("=" * 80)
    print("大宗商品MLP模型对比测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"商品数量: {len(symbols)}")
    print("=" * 80)
    
    fetcher = CommodityDataFetcher()
    results = {
        'timestamp': datetime.now().isoformat(),
        'symbols': symbols,
        'days': days,
        'comparison': [],
        'summary': {}
    }
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"处理商品: {symbol}")
        print(f"{'='*60}")
        
        # 生成模拟数据
        df = fetcher.generate_simulated_data(symbol, days=days)
        
        # ========== 原版测试 ==========
        print("\n[原版模型]")
        fe1 = FeatureEngineer()
        features1 = fe1.extract_features(df)
        target1 = df['Target'].iloc[:len(features1)]
        
        model1 = CommodityMLPModel()
        metrics1 = model1.train(features1, target1)
        
        # 原版预测
        predictions1 = model1.predict(features1)
        probas1 = model1.predict_proba(features1)
        
        # 原版回测
        signals1 = BacktestEngine().generate_signals_from_prediction(
            predictions1, probas1, threshold=0.7
        )
        backtest1 = BacktestEngine(initial_capital=100000)
        results1 = backtest1.run_backtest(df.head(len(signals1)), signals1)
        
        print(f"  测试准确率: {metrics1['test_accuracy']:.4f}")
        print(f"  回测收益: {results1['total_return_pct']:.2f}%")
        
        # ========== 优化版测试 ==========
        print("\n[优化版模型]")
        fe2 = FE2()
        features2 = fe2.extract_features(df)
        target2 = df['Target'].iloc[:len(features2)]
        
        # 选择显著特征（可选）
        correlations = features2.corrwith(target2).abs()
        significant_features = correlations[correlations > 0.05].index.tolist()
        
        if len(significant_features) < len(features2.columns):
            print(f"  特征筛选: {len(features2.columns)} → {len(significant_features)}个显著特征")
            features2_simple = features2[significant_features]
        else:
            features2_simple = features2
        
        model2 = MLP2(use_better_params=True)
        metrics2 = model2.train(features2_simple, target2)
        
        # 优化版预测
        predictions2 = model2.predict(features2_simple)
        probas2 = model2.predict_proba(features2_simple)
        
        # 优化版回测
        signals2 = BacktestEngine().generate_signals_from_prediction(
            predictions2, probas2, threshold=0.7
        )
        results2 = backtest1.run_backtest(df.head(len(signals2)), signals2)
        
        print(f"  测试准确率: {metrics2['test_accuracy']:.4f}")
        print(f"  回测收益: {results2['total_return_pct']:.2f}%")
        
        # ========== 风险管理测试 ==========
        print("\n[风险管理模块]")
        risk_manager = RiskManager()
        position = risk_manager.calculate_position_size(
            capital=100000,
            signal_confidence=0.75,
            volatility=0.02
        )
        print(f"  建议仓位: {position:.2%}")
        
        # 存储结果
        comparison = {
            'symbol': symbol,
            'original': {
                'features': features1.shape[1],
                'samples': features1.shape[0],
                'test_accuracy': metrics1['test_accuracy'],
                'test_f1': metrics1['test_f1'],
                'cv_mean': metrics1['cv_mean'],
                'backtest_return': results1['total_return_pct'],
                'sharpe_ratio': results1['sharpe_ratio'],
                'max_drawdown': results1['max_drawdown_pct']
            },
            'optimized': {
                'features': features2_simple.shape[1],
                'samples': features2_simple.shape[0],
                'test_accuracy': metrics2['test_accuracy'],
                'test_f1': metrics2['test_f1'],
                'cv_mean': metrics2['cv_mean'],
                'backtest_return': results2['total_return_pct'],
                'sharpe_ratio': results2['sharpe_ratio'],
                'max_drawdown': results2['max_drawdown_pct'],
                'feature_selection': len(significant_features) if len(significant_features) < len(features2.columns) else False
            }
        }
        results['comparison'].append(comparison)
        
        print(f"\n  ✅ {symbol} 测试完成")
    
    # 生成汇总统计
    print("\n" + "=" * 80)
    print("汇总统计")
    print("=" * 80)
    
    orig_acc = [r['original']['test_accuracy'] for r in results['comparison']]
    opt_acc = [r['optimized']['test_accuracy'] for r in results['comparison']]
    
    results['summary'] = {
        'original_avg_accuracy': np.mean(orig_acc),
        'optimized_avg_accuracy': np.mean(opt_acc),
        'original_avg_return': np.mean([r['original']['backtest_return'] for r in results['comparison']]),
        'optimized_avg_return': np.mean([r['optimized']['backtest_return'] for r in results['comparison']]),
        'best_original': max(orig_acc),
        'best_optimized': max(opt_acc)
    }
    
    print(f"\n原版平均准确率: {results['summary']['original_avg_accuracy']:.4f}")
    print(f"优化版平均准确率: {results['summary']['optimized_avg_accuracy']:.4f}")
    print(f"原版平均回测收益: {results['summary']['original_avg_return']:.2f}%")
    print(f"优化版平均回测收益: {results['summary']['optimized_avg_return']:.2f}%")
    
    # 保存报告
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, f'comparison_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n完整报告已保存: {report_path}")
    
    return results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='大宗商品MLP模型对比测试')
    parser.add_argument('--symbols', nargs='+', help='商品符号列表')
    parser.add_argument('--days', type=int, default=500, help='数据天数')
    parser.add_argument('--output-dir', default='./reports', help='输出目录')
    
    args = parser.parse_args()
    
    run_comparison_test(
        symbols=args.symbols,
        days=args.days,
        output_dir=args.output_dir
    )
