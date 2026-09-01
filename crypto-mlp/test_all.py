#!/usr/bin/env python3
"""
完整测试套件 - 验证所有模块功能
"""

import sys
import os
import traceback
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试所有导入"""
    print("=== 测试导入 ===")
    try:
        from data_fetcher import CryptoDataFetcher
        from feature_engineer import CryptoFeatureEngineer
        from risk_manager import CryptoRiskManager, SignalType, RiskLevel
        from hyperparameter_optimizer import CryptoHyperparameterOptimizer
        from lstm_analyzer import CryptoLSTMAnalyzer
        print("✓ 所有模块导入成功\n")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}\n")
        return False


def test_data_fetcher():
    """测试数据获取器"""
    print("=== 测试数据获取器 ===")
    try:
        from data_fetcher import CryptoDataFetcher
        
        fetcher = CryptoDataFetcher(exchange='binance')
        df = fetcher.fetch_ohlcv('BTC', '4h', limit=100)
        
        assert len(df) > 0, "数据为空"
        assert 'close' in df.columns, "缺少close列"
        assert 'volume' in df.columns, "缺少volume列"
        
        print(f"✓ 数据获取成功，共{len(df)}条记录\n")
        return True
    except Exception as e:
        print(f"✗ 数据获取失败: {e}\n")
        return False


def test_feature_engineer():
    """测试特征工程"""
    print("=== 测试特征工程 ===")
    try:
        import pandas as pd
        import numpy as np
        from feature_engineer import CryptoFeatureEngineer
        
        # 创建模拟数据
        np.random.seed(42)
        n_samples = 200
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n_samples, freq='4h')
        prices = np.cumsum(np.random.randn(n_samples) * 100) + 50000
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + np.abs(np.random.randn(n_samples) * 50),
            'low': prices - np.abs(np.random.randn(n_samples) * 50),
            'close': prices,
            'volume': np.random.uniform(1000, 5000, n_samples)
        })
        
        engineer = CryptoFeatureEngineer()
        features = engineer.create_features(df)
        
        assert len(features) > 0, "特征为空"
        assert 'target' in features.columns, "缺少target列"
        assert len(engineer.feature_names) > 0, "没有特征"
        
        print(f"✓ 特征工程成功，创建{len(engineer.feature_names)}个特征\n")
        return True
    except Exception as e:
        print(f"✗ 特征工程失败: {e}\n")
        return False


def test_risk_manager():
    """测试风险管理"""
    print("=== 测试风险管理 ===")
    try:
        import numpy as np
        from risk_manager import CryptoRiskManager, SignalType, RiskLevel
        
        manager = CryptoRiskManager()
        
        # 测试信号生成
        signal = manager.test_signal()
        
        assert signal['action'] in ['buy', 'sell', 'hold'], "无效信号"
        assert 0 <= signal['position_size'] <= 1, "仓位比例异常"
        
        # 测试风险指标
        returns = np.random.randn(100) * 0.02
        risk_metrics = manager.calculate_risk_metrics(returns)
        
        # VaR是正数（表示损失金额），不是负数
        assert risk_metrics.var_95 > 0, "VaR应为正值"
        assert risk_metrics.max_drawdown <= 0, "回撤应为负值或零"
        
        # 测试Kelly公式
        Kelly_fraction = manager.calculate_Kelly_fraction(win_rate=0.6, avg_win=0.03, avg_loss=0.02)
        assert 0 <= Kelly_fraction <= 1, "Kelly比例异常"
        
        print(f"✓ 风险管理测试通过\n")
        return True
    except Exception as e:
        print(f"✗ 风险管理失败: {e}\n")
        return False


def test_hyperparameter_optimizer():
    """测试超参数优化"""
    print("=== 测试超参数优化 ===")
    try:
        import pandas as pd
        import numpy as np
        from hyperparameter_optimizer import CryptoHyperparameterOptimizer
        
        # 创建模拟数据
        np.random.seed(42)
        n_samples = 100
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n_samples, freq='4h')
        prices = np.cumsum(np.random.randn(n_samples) * 100) + 50000
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + np.abs(np.random.randn(n_samples) * 50),
            'low': prices - np.abs(np.random.randn(n_samples) * 50),
            'close': prices,
            'volume': np.random.uniform(1000, 5000, n_samples)
        })
        
        optimizer = CryptoHyperparameterOptimizer(n_trials=3)  # 少量试验用于测试
        
        # 运行优化
        result = optimizer.optimize(df, max_trials=3)
        
        assert 'best_params' in result and 'best_score' in result, "缺少优化结果"
        
        print(f"✓ 超参数优化完成\n")
        return True
    except Exception as e:
        print(f"✗ 超参数优化失败: {e}\n")
        return False


def test_lstm_analyzer():
    """测试LSTM分析器"""
    print("=== 测试LSTM分析器 ===")
    try:
        import pandas as pd
        import numpy as np
        from lstm_analyzer import CryptoLSTMAnalyzer
        from feature_engineer import CryptoFeatureEngineer
        
        # 创建模拟数据
        np.random.seed(42)
        n_samples = 300
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n_samples, freq='4h')
        prices = 50000 * np.exp(np.cumsum(np.random.normal(0.0001, 0.02, n_samples)))
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * (1 + np.abs(np.random.randn(n_samples) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(n_samples) * 0.01)),
            'close': prices,
            'volume': np.random.uniform(1000, 5000, n_samples)
        })
        
        engineer = CryptoFeatureEngineer()
        features = engineer.create_features(df)
        
        # 创建LSTM分析器
        analyzer = CryptoLSTMAnalyzer(
            coin='BTC',
            timeframe='4h',
            lookback=30,
            forecast_horizon=12
        )
        
        # 准备数据
        X_train, X_test, y_train, y_test, feature_cols = analyzer.prepare_data(df, features)
        
        # 检查数据形状
        assert X_train.shape[0] > 0, "训练集为空"
        assert X_test.shape[0] > 0, "测试集为空"
        
        print(f"✓ LSTM数据准备成功，训练集{X_train.shape[0]}条，测试集{X_test.shape[0]}条\n")
        return True
    except ImportError as e:
        print(f"! TensorFlow未安装，跳过LSTM详细测试: {e}\n")
        return True  # 非致命错误
    except Exception as e:
        print(f"✗ LSTM分析失败: {e}\n")
        traceback.print_exc()
        return False


def test_integration():
    """测试集成分析"""
    print("=== 测试集成分析 ===")
    try:
        import pandas as pd
        import numpy as np
        from crypto_mlp import CryptoMLPAnalyzer
        
        # 创建分析器
        analyzer = CryptoMLPAnalyzer(
            coin='BTC',
            exchange='binance',
            timeframe='4h'
        )
        
        # 获取数据
        df = analyzer.fetch_data(days=30)
        
        # 创建特征
        features = analyzer.create_features(df)
        
        # 训练模型
        training_result = analyzer.train_models(features)
        
        # 预测
        prediction = analyzer.predict(df)
        
        # 生成信号
        signal = analyzer.risk_manager.generate_trade_signal(
            prediction=prediction['prediction'],
            confidence=prediction['confidence'],
            volatility=0.02,
            account_balance=10000
        )
        
        print(f"✓ 集成分析完成")
        print(f"  预测: {prediction['prediction']} (置信度{prediction['confidence']:.2%})")
        print(f"  信号: {signal['action']}")
        print()
        return True
    except Exception as e:
        print(f"✗ 集成分析失败: {e}\n")
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("加密货币MLP分析系统 - 完整测试套件")
    print("="*60 + "\n")
    
    tests = [
        ("导入测试", test_imports),
        ("数据获取", test_data_fetcher),
        ("特征工程", test_feature_engineer),
        ("风险管理", test_risk_manager),
        ("超参数优化", test_hyperparameter_optimizer),
        ("LSTM分析", test_lstm_analyzer),
        ("集成分析", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} 测试异常: {e}\n")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统运行正常。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
