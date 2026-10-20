#!/usr/bin/env python3
"""
大宗商品MLP投资分析工具 - 高级对比测试
测试原版、优化版、高级版三个版本
"""

import sys
import os
import json
from datetime import datetime
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import CommodityDataFetcher
from feature_engineering import FeatureEngineer
from feature_engineering_v2 import FeatureEngineer as FE2
from mlp_model import CommodityMLPModel
from mlp_model_v2 import CommodityMLPModel as MLP2
from mlp_model_advanced import AdvancedCommodityMLP
from backtest import BacktestEngine
from risk_manager import RiskManager


def run_advanced_comparison(symbols=None, days=600, output_dir='./reports'):
    """运行高级对比测试"""
    if symbols is None:
        symbols = ['GC=F', 'CL=F', 'SI=F', 'HG=F', 'NG=F']
    
    print("=" * 80)
    print("大宗商品MLP模型高级对比测试")
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
        
        # 生成数据
        df = fetcher.generate_simulated_data(symbol, days=days)
        
        # ========== 原版测试 ==========
        print("\n[原版模型]")
        fe1 = FeatureEngineer()
        features1 = fe1.extract_features(df)
        target1 = df['Target'].iloc[:len(features1)]
        
        model1 = CommodityMLPModel()
        metrics1 = model1.train(features1, target1)
        
        predictions1 = model1.predict(features1)
        probas1 = model1.predict_proba(features1)
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
        
        # 特征筛选
        correlations2 = features2.corrwith(target2).abs()
        sig_features2 = correlations2[correlations2 > 0.05].index.tolist()
        
        if len(sig_features2) < len(features2.columns):
            features2_simple = features2[sig_features2]
            print(f"  特征筛选: {len(features2.columns)} → {len(sig_features2)}个")
        else:
            features2_simple = features2
        
        model2 = MLP2(use_better_params=True)
        metrics2 = model2.train(features2_simple, target2)
        
        predictions2 = model2.predict(features2_simple)
        probas2 = model2.predict_proba(features2_simple)
        signals2 = BacktestEngine().generate_signals_from_prediction(
            predictions2, probas2, threshold=0.6
        )
        results2 = backtest1.run_backtest(df.head(len(signals2)), signals2)
        
        print(f"  测试准确率: {metrics2['test_accuracy']:.4f}")
        print(f"  回测收益: {results2['total_return_pct']:.2f}%")
        
        # ========== 高级版测试 ==========
        print("\n[高级版模型（集成+时序CV）]")
        model3 = AdvancedCommodityMLP(use_ensemble=True, feature_selection=True)
        metrics3 = model3.train(features2, target2)
        
        predictions3 = model3.predict(features2)
        probas3 = model3.predict_proba(features2)
        signals3 = model3.generate_signals(features2, threshold=0.55)
        results3 = backtest1.run_backtest(df.head(len(signals3)), signals3)
        
        print(f"  测试准确率: {metrics3['test_accuracy']:.4f}")
        print(f"  时序CV: {metrics3['cv_mean']:.4f} ± {metrics3['cv_std']:.4f}")
        print(f"  回测收益: {results3['total_return_pct']:.2f}%")
        
        # 特征重要性
        importance = model3.get_importance()
        print(f"  Top 3 重要特征:")
        for i, (name, imp) in enumerate(list(importance.items())[:3], 1):
            print(f"    {i}. {name}: {imp:.4f}")
        
        # 风险管理
        risk_manager = RiskManager()
        position = risk_manager.calculate_position_size(
            capital=100000,
            signal_confidence=0.65,
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
                'cv_mean': metrics1.get('cv_mean', 0),
                'backtest_return': results1['total_return_pct'],
                'sharpe_ratio': results1['sharpe_ratio'],
                'max_drawdown': results1['max_drawdown_pct']
            },
            'optimized': {
                'features': features2_simple.shape[1],
                'samples': features2_simple.shape[0],
                'test_accuracy': metrics2['test_accuracy'],
                'cv_mean': metrics2.get('cv_mean', 0),
                'backtest_return': results2['total_return_pct'],
                'sharpe_ratio': results2['sharpe_ratio'],
                'max_drawdown': results2['max_drawdown_pct']
            },
            'advanced': {
                'features': features2.shape[1],
                'samples': features2.shape[0],
                'test_accuracy': metrics3['test_accuracy'],
                'cv_mean': metrics3['cv_mean'],
                'cv_std': metrics3['cv_std'],
                'backtest_return': results3['total_return_pct'],
                'sharpe_ratio': results3['sharpe_ratio'],
                'max_drawdown': results3['max_drawdown_pct'],
                'top_features': list(importance.keys())[:3]
            }
        }
        results['comparison'].append(comparison)
        
        print(f"\n  ✅ {symbol} 测试完成")
    
    # 汇总统计
    print("\n" + "=" * 80)
    print("汇总统计")
    print("=" * 80)
    
    orig_acc = [r['original']['test_accuracy'] for r in results['comparison']]
    opt_acc = [r['optimized']['test_accuracy'] for r in results['comparison']]
    adv_acc = [r['advanced']['test_accuracy'] for r in results['comparison']]
    
    results['summary'] = {
        'original_avg_accuracy': np.mean(orig_acc),
        'optimized_avg_accuracy': np.mean(opt_acc),
        'advanced_avg_accuracy': np.mean(adv_acc),
        'original_avg_return': np.mean([r['original']['backtest_return'] for r in results['comparison']]),
        'optimized_avg_return': np.mean([r['optimized']['backtest_return'] for r in results['comparison']]),
        'advanced_avg_return': np.mean([r['advanced']['backtest_return'] for r in results['comparison']]),
        'best_original': max(orig_acc),
        'best_optimized': max(opt_acc),
        'best_advanced': max(adv_acc)
    }
    
    print(f"\n{'版本':<12} {'平均准确率':<12} {'最佳准确率':<12} {'平均收益':<12}")
    print("-" * 50)
    print(f"{'原版':<12} {orig_acc[0]:<12.4f} {max(orig_acc):<12.4f} {results['summary']['original_avg_return']:<12.2f}%")
    print(f"{'优化版':<12} {opt_acc[0]:<12.4f} {max(opt_acc):<12.4f} {results['summary']['optimized_avg_return']:<12.2f}%")
    print(f"{'高级版':<12} {adv_acc[0]:<12.4f} {max(adv_acc):<12.4f} {results['summary']['advanced_avg_return']:<12.2f}%")
    
    # 保存报告
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, f'advanced_comparison_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n完整报告已保存: {report_path}")
    
    return results


if __name__ == '__main__':
    run_advanced_comparison()
