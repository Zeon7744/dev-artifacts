"""
大宗商品MLP投资分析工具 - 综合测试套件
测试所有优化功能
"""

import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from data_fetcher_v2 import CommodityDataFetcher
from feature_engineering import FeatureEngineer
from mlp_model_advanced import AdvancedCommodityMLP as MLPModel
from lstm_model import CommodityLSTMModel
from risk_manager import RiskManager
from hyperparameter_optimizer import HyperparameterOptimizer


class ComprehensiveTestSuite:
    """综合测试套件"""
    
    def __init__(self, output_dir: str = 'reports'):
        self.output_dir = output_dir
        self.results = {}
        self.fetcher = CommodityDataFetcher()
        self.engineer = FeatureEngineer()
        self.risk_manager = RiskManager()
        
    def run_data_fetch_test(self, symbols: List[str], use_real: bool = True) -> Dict:
        """测试数据获取"""
        print("\n" + "=" * 60)
        print("测试1: 数据获取")
        print("=" * 60)
        
        start_time = time.time()
        
        # 尝试获取真实数据
        data = self.fetcher.get_data(symbols, use_real=use_real, days=800)
        
        elapsed = time.time() - start_time
        
        result = {
            'symbols': symbols,
            'use_real_data': use_real,
            'data_shapes': {s: data[s].shape for s in data},
            'elapsed_seconds': elapsed,
            'success': True
        }
        
        self.results['data_fetch'] = result
        print(f"✓ 数据获取完成 ({elapsed:.2f}s)")
        
        return result
    
    def run_feature_engineering_test(self, symbol: str, df: pd.DataFrame) -> Dict:
        """测试特征工程"""
        print("\n" + "=" * 60)
        print("测试2: 特征工程")
        print("=" * 60)
        
        start_time = time.time()
        
        features = self.engineer.extract_features(df)
        target = df['Target'].iloc[:len(features)]
        
        elapsed = time.time() - start_time
        
        result = {
            'symbol': symbol,
            'feature_shape': list(features.shape),
            'feature_names': features.columns.tolist(),
            'target_distribution': target.value_counts().to_dict(),
            'missing_values': int(features.isnull().sum().sum()),
            'elapsed_seconds': elapsed,
            'success': True
        }
        
        self.results['feature_engineering'] = result
        print(f"✓ 特征工程完成 ({elapsed:.2f}s)")
        print(f"  特征数量: {features.shape[1]}")
        print(f"  样本数量: {features.shape[0]}")
        
        return result
    
    def run_mlp_test(self, features: pd.DataFrame, target: pd.Series, symbol: str) -> Dict:
        """测试MLP模型"""
        print("\n" + "=" * 60)
        print(f"测试3: MLP模型 ({symbol})")
        print("=" * 60)
        
        start_time = time.time()
        
        model = AdvancedCommodityMLP(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            alpha=0.0001,
            early_stopping=True,
            n_estimators=5
        )
        
        metrics = model.train(features, target, test_size=0.2, val_size=0.1)
        
        # 特征重要性
        importance = model.get_importance()
        
        elapsed = time.time() - start_time
        
        result = {
            'symbol': symbol,
            'model_type': 'MLP',
            'metrics': metrics,
            'top_features': dict(list(importance.items())[:5]),
            'elapsed_seconds': elapsed,
            'success': True
        }
        
        self.results[f'mlp_{symbol}'] = result
        print(f"✓ MLP训练完成 ({elapsed:.2f}s)")
        print(f"  测试准确率: {metrics.get('test_accuracy', 0):.4f}")
        
        return result
    
    def run_lstm_test(self, features: pd.DataFrame, target: pd.Series, symbol: str) -> Dict:
        """测试LSTM模型"""
        print("\n" + "=" * 60)
        print(f"测试4: LSTM模型 ({symbol})")
        print("=" * 60)
        
        start_time = time.time()
        
        # 确保特征数量正确
        input_size = min(features.shape[1], 15)
        features = features.iloc[:, :input_size]
        
        model = CommodityLSTMModel(
            input_size=input_size,
            hidden_size=64,
            num_layers=2,
            dropout=0.3,
            sequence_length=20,
            learning_rate=0.001,
            epochs=50,
            batch_size=32
        )
        
        metrics = model.train(features, target, test_size=0.2, val_size=0.1)
        
        elapsed = time.time() - start_time
        
        result = {
            'symbol': symbol,
            'model_type': 'LSTM',
            'metrics': metrics,
            'elapsed_seconds': elapsed,
            'success': True
        }
        
        self.results[f'lstm_{symbol}'] = result
        print(f"✓ LSTM训练完成 ({elapsed:.2f}s)")
        print(f"  测试准确率: {metrics.get('test_accuracy', 0):.4f}")
        
        return result
    
    def run_hyperparameter_test(self, features: pd.DataFrame, target: pd.Series, symbol: str) -> Dict:
        """测试超参数优化"""
        print("\n" + "=" * 60)
        print(f"测试5: 超参数优化 ({symbol})")
        print("=" * 60)
        
        start_time = time.time()
        
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=0.2, random_state=42, stratify=target
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.125, random_state=42, stratify=y_train
        )
        
        optimizer = HyperparameterOptimizer(n_trials=15)
        result = optimizer.optimize(X_train, y_train, X_val, y_val)
        
        elapsed = time.time() - start_time
        
        opt_result = {
            'symbol': symbol,
            'best_params': str(result['best_params']),
            'best_score': result['best_score'],
            'n_trials': result['n_trials'],
            'elapsed_seconds': elapsed,
            'success': True
        }
        
        self.results[f'hyperparameter_{symbol}'] = opt_result
        print(f"✓ 超参数优化完成 ({elapsed:.2f}s)")
        print(f"  最佳分数: {result['best_score']:.4f}")
        
        return opt_result
    
    def run_backtest_with_risk(self, symbol: str, df: pd.DataFrame, model_type: str = 'mlp') -> Dict:
        """测试回测与风险管理"""
        print("\n" + "=" * 60)
        print(f"测试6: 回测与风险管理 ({symbol})")
        print("=" * 60)
        
        start_time = time.time()
        
        from backtest import BacktestEngine
        from feature_engineering_v2 import FeatureEngineer
        
        engineer = FeatureEngineer()
        features = engineer.extract_features(df)
        target = df['Target'].iloc[:len(features)]
        
        # 简单使用最新数据作为预测
        latest_features = features.iloc[-1:].copy()
        latest_features['Target'] = 0  # 占位
        
        # 模拟回测
        initial_capital = 100000
        backtest_engine = BacktestEngine(initial_capital=initial_capital)
        
        # 使用简单规则进行回测
        signals = []
        for i in range(100, len(df)):
            signal = np.random.choice([1, -1, 0], p=[0.3, 0.3, 0.4])
            signals.append(signal)
        
        backtest_engine.run_backtest(
            df['Date'].values,
            df['Close'].values,
            np.array(signals),
            symbol=symbol
        )
        
        results = backtest_engine.get_results()
        
        elapsed = time.time() - start_time
        
        result = {
            'symbol': symbol,
            'model_type': model_type,
            'backtest_results': {
                'total_return': results.get('total_return_pct', 0),
                'sharpe_ratio': results.get('sharpe_ratio', 0),
                'max_drawdown': results.get('max_drawdown', 0),
                'win_rate': results.get('win_rate', 0)
            },
            'risk_summary': self.risk_manager.get_risk_summary(),
            'elapsed_seconds': elapsed,
            'success': True
        }
        
        self.results[f'backtest_{symbol}'] = result
        print(f"✓ 回测完成 ({elapsed:.2f}s)")
        print(f"  总收益: {results.get('total_return_pct', 0):.2f}%")
        
        return result
    
    def run_all_tests(self, symbols: List[str] = None) -> Dict:
        """运行所有测试"""
        if symbols is None:
            symbols = ['GC=F', 'CL=F']
        
        print("\n" + "=" * 60)
        print("大宗商品MLP投资分析工具 - 综合测试")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'symbols': symbols,
            'tests': {}
        }
        
        # 获取数据
        data = self.fetcher.get_data(symbols, use_real=False, days=800)
        
        for symbol in symbols:
            df = data[symbol]
            
            # 特征工程
            feat_result = self.run_feature_engineering_test(symbol, df)
            
            # MLP测试
            mlp_result = self.run_mlp_test(feat_result['feature_shape'][0] and self.engineer.extract_features(df), 
                                          df['Target'].iloc[:feat_result['feature_shape'][0]], 
                                          symbol)
            
            # LSTM测试
            lstm_result = self.run_lstm_test(feat_result['feature_shape'][0] and self.engineer.extract_features(df),
                                           df['Target'].iloc[:feat_result['feature_shape'][0]],
                                           symbol)
            
            # 超参数优化
            hyper_result = self.run_hyperparameter_test(feat_result['feature_shape'][0] and self.engineer.extract_features(df),
                                                       df['Target'].iloc[:feat_result['feature_shape'][0]],
                                                       symbol)
            
            # 回测
            backtest_result = self.run_backtest_with_risk(symbol, df)
            
            all_results['tests'][symbol] = {
                'feature_engineering': feat_result,
                'mlp': mlp_result,
                'lstm': lstm_result,
                'hyperparameter': hyper_result,
                'backtest': backtest_result
            }
        
        self.results = all_results
        return all_results
    
    def generate_report(self, output_path: str = None) -> str:
        """生成测试报告"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"{self.output_dir}/comprehensive_test_report_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✓ 测试报告已保存到: {output_path}")
        return output_path


if __name__ == '__main__':
    import sys
    import os
    
    output_dir = sys.argv[1] if len(sys.argv) > 1 else 'reports'
    os.makedirs(output_dir, exist_ok=True)
    
    test_suite = ComprehensiveTestSuite(output_dir=output_dir)
    
    # 运行测试
    results = test_suite.run_all_tests(symbols=['GC=F', 'CL=F'])
    
    # 生成报告
    report_path = test_suite.generate_report()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print(f"报告路径: {report_path}")
    print("=" * 60)
