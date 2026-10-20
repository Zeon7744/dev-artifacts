"""
大宗商品MLP投资分析工具 - 简化综合测试
"""

import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from data_fetcher_v2 import CommodityDataFetcher
from feature_engineering import FeatureEngineer
from mlp_model_advanced import AdvancedCommodityMLP
from lstm_model import CommodityLSTMModel
from hyperparameter_optimizer import HyperparameterOptimizer


def test_data_fetch(symbols):
    """测试数据获取"""
    print("\n" + "=" * 60)
    print("测试1: 数据获取")
    print("=" * 60)
    
    fetcher = CommodityDataFetcher()
    data = fetcher.get_data(symbols, use_real=False, days=800)
    
    result = {
        'symbols': symbols,
        'data_shapes': {s: data[s].shape for s in data},
        'success': True
    }
    
    print(f"✓ 数据获取完成")
    for s, shape in result['data_shapes'].items():
        print(f"  {s}: {shape}")
    
    return result, data


def test_feature_engineering(symbol, df):
    """测试特征工程"""
    print("\n" + "=" * 60)
    print(f"测试2: 特征工程 ({symbol})")
    print("=" * 60)
    
    engineer = FeatureEngineer()
    features = engineer.extract_features(df)
    target = df['Target'].iloc[:len(features)]
    
    result = {
        'symbol': symbol,
        'feature_shape': list(features.shape),
        'feature_count': features.shape[1],
        'sample_count': features.shape[0],
        'target_distribution': target.value_counts().to_dict(),
        'success': True
    }
    
    print(f"✓ 特征工程完成")
    print(f"  特征数: {features.shape[1]}")
    print(f"  样本数: {features.shape[0]}")
    
    return result, features, target


def test_mlp(symbol, features, target):
    """测试MLP模型"""
    print("\n" + "=" * 60)
    print(f"测试3: MLP模型 ({symbol})")
    print("=" * 60)
    
    model = AdvancedCommodityMLP(
        use_ensemble=True,
        feature_selection=True,
        threshold=0.55
    )
    
    metrics = model.train(features, target, test_size=0.2, val_size=0.1)
    
    importance = model.get_importance()
    
    result = {
        'symbol': symbol,
        'model_type': 'MLP',
        'metrics': {k: float(v) if isinstance(v, (np.floating, float)) else v for k, v in metrics.items()},
        'top_features': dict(list(importance.items())[:5]),
        'success': True
    }
    
    print(f"✓ MLP训练完成")
    print(f"  测试准确率: {metrics.get('test_accuracy', 0):.4f}")
    
    return result


def test_lstm(symbol, features, target):
    """测试LSTM模型"""
    print("\n" + "=" * 60)
    print(f"测试4: LSTM模型 ({symbol})")
    print("=" * 60)
    
    # 限制特征数量
    input_size = min(features.shape[1], 15)
    features_limited = features.iloc[:, :input_size]
    
    model = CommodityLSTMModel(
        input_size=input_size,
        hidden_size=64,
        num_layers=2,
        epochs=30,
        batch_size=32
    )
    
    metrics = model.train(features_limited, target, test_size=0.2, val_size=0.1)
    
    result = {
        'symbol': symbol,
        'model_type': 'LSTM',
        'metrics': {k: float(v) if isinstance(v, (np.floating, float)) else v for k, v in metrics.items()},
        'success': True
    }
    
    print(f"✓ LSTM训练完成")
    print(f"  测试准确率: {metrics.get('test_accuracy', 0):.4f}")
    
    return result


def test_hyperparameter(symbol, features, target):
    """测试超参数优化"""
    print("\n" + "=" * 60)
    print(f"测试5: 超参数优化 ({symbol})")
    print("=" * 60)
    
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.125, random_state=42, stratify=y_train
    )
    
    optimizer = HyperparameterOptimizer(n_trials=10)
    result = optimizer.optimize(X_train, y_train, X_val, y_val)
    
    opt_result = {
        'symbol': symbol,
        'best_score': float(result['best_score']),
        'n_trials': result['n_trials'],
        'success': True
    }
    
    print(f"✓ 超参数优化完成")
    print(f"  最佳分数: {result['best_score']:.4f}")
    
    return opt_result


def main():
    print("\n" + "=" * 60)
    print("大宗商品MLP投资分析工具 - 综合测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    symbols = ['GC=F', 'CL=F']
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'symbols': symbols,
        'tests': {}
    }
    
    # 测试1: 数据获取
    data_result, data = test_data_fetch(symbols)
    all_results['tests']['data_fetch'] = data_result
    
    # 测试2-5: 每个商品
    for symbol in symbols:
        df = data[symbol]
        
        # 特征工程
        feat_result, features, target = test_feature_engineering(symbol, df)
        
        # MLP
        mlp_result = test_mlp(symbol, features, target)
        
        # LSTM
        lstm_result = test_lstm(symbol, features, target)
        
        # 超参数优化
        hyper_result = test_hyperparameter(symbol, features, target)
        
        all_results['tests'][symbol] = {
            'feature_engineering': feat_result,
            'mlp': mlp_result,
            'lstm': lstm_result,
            'hyperparameter': hyper_result
        }
    
    # 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"reports/comprehensive_test_{timestamp}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print(f"报告路径: {output_path}")
    print("=" * 60)
    
    return all_results


if __name__ == '__main__':
    results = main()
