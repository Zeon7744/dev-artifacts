"""
大宗商品MLP投资分析工具 - REST API服务
提供实时预测和数据查询接口
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
import joblib
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher_v2 import CommodityDataFetcher
from feature_engineering import FeatureEngineer
from mlp_model_advanced import AdvancedCommodityMLP
from lstm_model import CommodityLSTMModel
from risk_manager import RiskManager

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局模型缓存
models = {}
data_cache = {}


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })


@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """获取可用商品列表"""
    fetcher = CommodityDataFetcher()
    symbols = fetcher.get_available_symbols()
    
    return jsonify({
        'symbols': symbols,
        'count': len(symbols)
    })


@app.route('/api/data/<symbol>', methods=['GET'])
def get_data(symbol: str):
    """获取商品数据"""
    days = request.args.get('days', 800, type=int)
    use_real = request.args.get('real', 'false').lower() == 'true'
    
    fetcher = CommodityDataFetcher()
    df = fetcher.get_data(symbol, days=days)
    
    if df is None or df.empty:
        return jsonify({'error': f'无法获取{symbol}数据'}), 404
    
    # 转换为字典
    data = {
        'symbol': symbol,
        'count': len(df),
        'columns': list(df.columns),
        'latest_price': float(df['Close'].iloc[-1]),
        'price_change': float((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100),
        'data': df.tail(100).to_dict('records')  # 只返回最近100条
    }
    
    return jsonify(data)


@app.route('/api/train/<symbol>', methods=['POST'])
def train_model(symbol: str):
    """训练模型"""
    model_type = request.json.get('model_type', 'mlp')
    use_real = request.json.get('use_real', False)
    
    try:
        fetcher = CommodityDataFetcher()
        engineer = FeatureEngineer()
        
        # 获取数据
        df = fetcher.get_data(symbol)
        features = engineer.extract_features(df)
        target = df['Target'].iloc[:len(features)]
        
        # 训练模型
        if model_type == 'lstm':
            model = CommodityLSTMModel(
                input_size=min(features.shape[1], 15),
                epochs=30
            )
        else:
            model = AdvancedCommodityMLP(use_ensemble=True)
        
        metrics = model.train(features, target, test_size=0.2)
        
        # 保存模型
        model_path = f"models/{symbol}_{model_type}.pkl"
        os.makedirs('models', exist_ok=True)
        
        if model_type == 'lstm':
            model.save_model(model_path)
        else:
            joblib.dump({
                'model': model,
                'feature_names': model.feature_names,
                'selected_features': model.selected_features
            }, model_path)
        
        models[symbol] = {
            'type': model_type,
            'path': model_path,
            'metrics': metrics,
            'trained_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'model_type': model_type,
            'metrics': {k: float(v) if isinstance(v, (np.floating, float)) else v 
                       for k, v in metrics.items()},
            'model_path': model_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict/<symbol>', methods=['POST'])
def predict(symbol: str):
    """实时预测"""
    model_type = request.json.get('model_type', 'mlp')
    
    try:
        # 加载模型
        if symbol in models and models[symbol]['type'] == model_type:
            model_info = models[symbol]
            model_path = model_info['path']
        else:
            model_path = f"models/{symbol}_{model_type}.pkl"
            if not os.path.exists(model_path):
                return jsonify({'error': f'模型不存在: {model_path}，请先训练'}), 404
        
        # 加载模型
        fetcher = CommodityDataFetcher()
        engineer = FeatureEngineer()
        
        # 获取最新数据
        df = fetcher.get_data(symbol, days=100)
        features = engineer.extract_features(df)
        
        # 预测
        if model_type == 'lstm':
            model = CommodityLSTMModel()
            model.load_model(model_path)
            predictions = model.predict(features)
            probabilities = model.predict_proba(features)
        else:
            data = joblib.load(model_path)
            model = data['model']
            predictions = model.predict(features)
            probabilities = model.predict_proba(features)
        
        # 返回最新预测
        latest_pred = int(predictions[-1])
        latest_prob = float(probabilities[-1][latest_pred]) if len(probabilities[-1]) > 1 else 0.5
        
        return jsonify({
            'symbol': symbol,
            'prediction': 'BUY' if latest_pred == 1 else 'SELL',
            'confidence': latest_prob,
            'timestamp': datetime.now().isoformat(),
            'latest_price': float(df['Close'].iloc[-1])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/<symbol>', methods=['POST'])
def backtest(symbol: str):
    """运行回测"""
    model_type = request.json.get('model_type', 'mlp')
    initial_capital = request.json.get('initial_capital', 100000)
    
    try:
        from risk_backtest import RiskBacktestEngine
        
        fetcher = CommodityDataFetcher()
        engineer = FeatureEngineer()
        
        # 获取数据
        df = fetcher.get_data(symbol)
        features = engineer.extract_features(df)
        target = df['Target'].iloc[:len(features)]
        
        # 加载或训练模型
        model_path = f"models/{symbol}_{model_type}.pkl"
        if os.path.exists(model_path):
            if model_type == 'lstm':
                model = CommodityLSTMModel()
                model.load_model(model_path)
            else:
                data = joblib.load(model_path)
                model = data['model']
        else:
            # 临时训练
            if model_type == 'lstm':
                model = CommodityLSTMModel(input_size=min(features.shape[1], 15), epochs=20)
            else:
                model = AdvancedCommodityMLP()
            model.train(features, target, test_size=0.3)
        
        # 生成预测和信号
        predictions = model.predict(features)
        probabilities = model.predict_proba(features)
        signals = pd.Series(np.where(probabilities[:, 1] > 0.6, 1,
                              np.where(probabilities[:, 0] > 0.6, -1, 0)))
        
        # 运行回测
        backtest = RiskBacktestEngine(initial_capital=initial_capital)
        results = backtest.run_backtest(df, signals, probabilities)
        
        return jsonify({
            'symbol': symbol,
            'model_type': model_type,
            'results': {k: float(v) if isinstance(v, (np.floating, float)) else v 
                       for k, v in results.items() if k != 'trades'}
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analysis/<symbol>', methods=['GET'])
def analysis(symbol: str):
    """综合分析（训练+回测+预测）"""
    model_type = request.args.get('model_type', 'mlp')
    
    try:
        fetcher = CommodityDataFetcher()
        engineer = FeatureEngineer()
        
        # 获取数据
        df = fetcher.get_data(symbol)
        features = engineer.extract_features(df)
        target = df['Target'].iloc[:len(features)]
        
        # 训练模型
        if model_type == 'lstm':
            model = CommodityLSTMModel(input_size=min(features.shape[1], 15), epochs=30)
        else:
            model = AdvancedCommodityMLP(use_ensemble=True)
        
        metrics = model.train(features, target, test_size=0.2)
        
        # 预测
        predictions = model.predict(features)
        probabilities = model.predict_proba(features)
        
        # 回测
        signals = pd.Series(np.where(probabilities[:, 1] > 0.6, 1,
                              np.where(probabilities[:, 0] > 0.6, -1, 0)))
        
        backtest = RiskBacktestEngine(initial_capital=100000)
        bt_results = backtest.run_backtest(df, signals, probabilities)
        
        # 最新预测
        latest_pred = int(predictions[-1])
        latest_prob = float(probabilities[-1][latest_pred])
        
        return jsonify({
            'symbol': symbol,
            'model_type': model_type,
            'metrics': {k: float(v) if isinstance(v, (np.floating, float)) else v 
                       for k, v in metrics.items()},
            'prediction': {
                'signal': 'BUY' if latest_pred == 1 else 'SELL',
                'confidence': latest_prob,
                'price': float(df['Close'].iloc[-1])
            },
            'backtest': {
                'total_return': bt_results['total_return_pct'],
                'max_drawdown': bt_results['max_drawdown_pct'],
                'sharpe_ratio': bt_results['sharpe_ratio'],
                'win_rate': bt_results['win_rate']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/docs', methods=['GET'])
def get_docs():
    """获取API文档"""
    return jsonify({
        'name': '大宗商品MLP投资分析工具 API',
        'version': '2.0.0',
        'endpoints': {
            'GET /api/health': '健康检查',
            'GET /api/symbols': '获取可用商品列表',
            'GET /api/data/<symbol>': '获取商品数据',
            'POST /api/train/<symbol>': '训练模型',
            'POST /api/predict/<symbol>': '实时预测',
            'POST /api/backtest/<symbol>': '运行回测',
            'GET /api/analysis/<symbol>': '综合分析',
            'GET /api/docs': '本接口'
        },
        'examples': {
            'train': {'method': 'POST', 'url': '/api/train/GC=F', 'body': {'model_type': 'mlp', 'use_real': false}},
            'predict': {'method': 'POST', 'url': '/api/predict/GC=F', 'body': {'model_type': 'mlp'}},
            'backtest': {'method': 'POST', 'url': '/api/backtest/GC=F', 'body': {'model_type': 'mlp', 'initial_capital': 100000}},
            'analysis': {'method': 'GET', 'url': '/api/analysis/GC=F?model_type=mlp'}
        }
    })


def run_api(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """启动API服务"""
    print(f"\n{'='*60}")
    print(f"大宗商品MLP投资分析工具 - API服务")
    print(f"{'='*60}")
    print(f"服务地址: http://{host}:{port}")
    print(f"API文档:  http://{host}:{port}/api/docs")
    print(f"健康检查: http://{host}:{port}/api/health")
    print(f"{'='*60}\n")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='启动大宗商品分析API服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=5000, help='监听端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    run_api(args.host, args.port, args.debug)
