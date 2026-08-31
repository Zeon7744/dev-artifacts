#!/usr/bin/env python3
"""
大宗商品MLP投资分析工具 - 命令行接口
"""

import argparse
import sys
import os
import json
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import CommodityDataFetcher
from feature_engineering import FeatureEngineer
from mlp_model import CommodityMLPModel


def run_analysis(symbols: list, use_real_data: bool, save_model: bool, output_dir: str):
    """运行完整分析流程"""
    print("=" * 70)
    print("大宗商品MLP投资分析工具")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"商品: {', '.join(symbols)}")
    print(f"数据源: {'真实市场数据' if use_real_data else '模拟数据'}")
    print()
    
    # 初始化组件
    fetcher = CommodityDataFetcher(use_real_data=use_real_data)
    engineer = FeatureEngineer()
    
    results = []
    
    for symbol in symbols:
        print(f"\n{'='*50}")
        print(f"处理商品: {symbol}")
        print(f"{'='*50}")
        
        # 获取数据
        print("正在获取数据...")
        df = fetcher.generate_simulated_data(symbol, days=800)
        
        # 提取特征
        print("正在提取特征...")
        features = engineer.extract_features(df)
        target = df['Target'].iloc[:len(features)]
        
        print(f"数据准备完成: {features.shape[0]}样本, {features.shape[1]}特征")
        print(f"目标变量分布: 上涨{target.sum()}次, 下跌{len(target)-target.sum()}次")
        
        # 训练模型
        print("正在训练MLP模型...")
        model = CommodityMLPModel()
        metrics = model.train(features, target)
        
        # 预测最新信号
        latest_features = features.tail(1)
        prediction = model.predict(latest_features)[0]
        proba = model.predict_proba(latest_features)[0]
        
        signal = "看涨" if prediction == 1 else "看跌"
        confidence = max(proba) * 100
        
        print(f"\n最新预测信号: {signal} (置信度: {confidence:.1f}%)")
        
        # 保存结果
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'samples': features.shape[0],
            'features': features.shape[1],
            'metrics': metrics,
            'prediction': int(prediction),
            'signal': signal,
            'confidence': float(confidence),
            'feature_importance': model.get_importance()
        }
        results.append(result)
        
        # 保存模型
        if save_model:
            model_path = os.path.join(output_dir, f'model_{symbol.replace("=", "_")}.pkl')
            model.save_model(model_path)
    
    # 输出汇总报告
    print(f"\n{'='*70}")
    print("分析汇总报告")
    print(f"{'='*70}")
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_commodities': len(results),
        'commodities': results
    }
    
    # 打印汇总表
    print(f"\n{'商品':<10} {'信号':<6} {'置信度':<10} {'测试准确率':<12} {'F1分数':<8}")
    print("-" * 50)
    for r in results:
        print(f"{r['symbol']:<10} {r['signal']:<6} {r['confidence']:<10.1f}% {r['metrics']['test_accuracy']:<12.4f} {r['metrics']['test_f1']:<8.4f}")
    
    # 保存报告
    report_path = os.path.join(output_dir, f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n完整报告已保存: {report_path}")
    
    return report


def run_analysis_optimized(symbols: list, use_real_data: bool, save_model: bool, output_dir: str):
    """运行优化版分析流程"""
    from feature_engineering_v2 import FeatureEngineer as FE2
    from mlp_model_v2 import CommodityMLPModel
    
    print("=" * 70)
    print("大宗商品MLP投资分析工具（优化版）")
    print("=" * 70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"商品: {', '.join(symbols)}")
    print(f"数据源: {'真实市场数据' if use_real_data else '模拟数据'}")
    print()
    
    # 初始化组件
    fetcher = CommodityDataFetcher(use_real_data=use_real_data)
    engineer = FE2()
    
    results = []
    
    for symbol in symbols:
        print(f"\n{'='*50}")
        print(f"处理商品: {symbol}（优化版）")
        print(f"{'='*50}")
        
        # 获取数据
        print("正在获取数据...")
        df = fetcher.generate_simulated_data(symbol, days=800)
        
        # 提取特征
        print("正在提取特征...")
        features = engineer.extract_features(df)
        target = df['Target'].iloc[:len(features)]
        
        # 特征筛选（选择显著特征）
        correlations = features.corrwith(target).abs()
        significant_features = correlations[correlations > 0.05].index.tolist()
        
        if len(significant_features) < len(features.columns):
            print(f"特征筛选: {len(features.columns)} → {len(significant_features)}个显著特征")
            features = features[significant_features]
        
        print(f"数据准备完成: {features.shape[0]}样本, {features.shape[1]}特征")
        print(f"目标变量分布: 上涨{target.sum()}次, 下跌{len(target)-target.sum()}次")
        
        # 训练模型
        print("正在训练MLP模型（优化版）...")
        model = CommodityMLPModel(use_better_params=True)
        metrics = model.train(features, target)
        
        # 预测最新信号
        latest_features = features.tail(1)
        prediction = model.predict(latest_features)[0]
        proba = model.predict_proba(latest_features)[0]
        
        signal = "看涨" if prediction == 1 else "看跌"
        confidence = max(proba) * 100
        
        print(f"\n最新预测信号: {signal} (置信度: {confidence:.1f}%)")
        
        # 保存结果
        result = {
            'symbol': symbol,
            'version': 'optimized',
            'timestamp': datetime.now().isoformat(),
            'samples': features.shape[0],
            'features': features.shape[1],
            'metrics': metrics,
            'prediction': int(prediction),
            'signal': signal,
            'confidence': float(confidence),
            'feature_importance': model.get_importance()
        }
        results.append(result)
        
        # 保存模型
        if save_model:
            model_path = os.path.join(output_dir, f'model_opt_{symbol.replace("=", "_")}.pkl')
            model.save_model(model_path)
    
    # 输出汇总报告
    print(f"\n{'='*70}")
    print("分析汇总报告（优化版）")
    print(f"{'='*70}")
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'version': 'optimized',
        'total_commodities': len(results),
        'commodities': results
    }
    
    # 打印汇总表
    print(f"\n{'商品':<10} {'版本':<10} {'信号':<6} {'置信度':<10} {'测试准确率':<12} {'F1分数':<8}")
    print("-" * 60)
    for r in results:
        print(f"{r['symbol']:<10} {r.get('version','original'):<10} {r['signal']:<6} {r['confidence']:<10.1f}% {r['metrics']['test_accuracy']:<12.4f} {r['metrics']['test_f1']:<8.4f}")
    
    # 保存报告
    report_path = os.path.join(output_dir, f'report_opt_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n完整报告已保存: {report_path}")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description='大宗商品MLP投资分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python cli.py --symbols GC=F CL=F
  python cli.py --all --save-model
  python cli.py --symbols GC=F --real-data
  python cli.py --symbols GC=F --optimize
        '''
    )
    
    parser.add_argument(
        '--symbols', '-s',
        nargs='+',
        help='商品代码列表 (如 GC=F CL=F SI=F)',
        default=['GC=F']
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='分析所有可用商品'
    )
    
    parser.add_argument(
        '--real-data', '-r',
        action='store_true',
        help='使用真实市场数据（需要yfinance）'
    )
    
    parser.add_argument(
        '--save-model', '-m',
        action='store_true',
        help='保存训练好的模型'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='./reports',
        help='输出目录'
    )
    
    parser.add_argument(
        '--optimize',
        action='store_true',
        help='使用优化版模型（增强特征工程+自适应参数）'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 确定要分析的商品
    if args.all:
        symbols = list(CommodityDataFetcher().get_available_symbols().keys())
    else:
        symbols = args.symbols
    
    # 运行分析
    try:
        if args.optimize:
            report = run_analysis_optimized(
                symbols=symbols,
                use_real_data=args.real_data,
                save_model=args.save_model,
                output_dir=args.output_dir
            )
        else:
            report = run_analysis(
                symbols=symbols,
                use_real_data=args.real_data,
                save_model=args.save_model,
                output_dir=args.output_dir
            )
        
        print("\n分析完成!")
        return 0
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
