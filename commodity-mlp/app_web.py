"""
大宗商品MLP投资分析工具 - Web界面
基于Flask的交互式Web应用
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime
from typing import Dict, List

from data_fetcher import CommodityDataFetcher
from feature_engineering import FeatureEngineer
from mlp_model import CommodityMLPModel

app = Flask(__name__)

# 全局变量
models: Dict[str, CommodityMLPModel] = {}
reports: Dict[str, dict] = {}

# 模型存储目录
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

REPORT_DIR = os.path.join(os.path.dirname(__file__), 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)


@app.route('/')
def index():
    """首页"""
    commodities = CommodityDataFetcher().get_available_symbols()
    return render_template('index.html', commodities=commodities, models=models)


@app.route('/api/symbols')
def get_symbols():
    """获取可用商品列表"""
    commodities = CommodityDataFetcher().get_available_symbols()
    return jsonify(commodities)


@app.route('/api/train', methods=['POST'])
def train_model():
    """训练模型接口"""
    data = request.json
    symbol = data.get('symbol', 'GC=F')
    use_real = data.get('use_real_data', False)
    
    try:
        print(f"开始训练 {symbol} 的模型...")
        
        # 初始化组件
        fetcher = CommodityDataFetcher()
        engineer = FeatureEngineer()
        
        # 获取数据
        df = fetcher.generate_simulated_data(symbol, days=800)
        
        # 提取特征
        features = engineer.extract_features(df)
        target = df['Target'].iloc[:len(features)]
        
        # 训练模型
        model = CommodityMLPModel()
        metrics = model.train(features, target)
        
        # 预测最新信号
        latest_features = features.tail(1)
        prediction = model.predict(latest_features)[0]
        proba = model.predict_proba(latest_features)[0]
        
        signal = "看涨" if prediction == 1 else "看跌"
        confidence = float(max(proba) * 100)
        
        # 保存模型
        model_path = os.path.join(MODEL_DIR, f'model_{symbol.replace("=", "_")}.pkl')
        model.save_model(model_path)
        
        # 保存结果
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'confidence': confidence,
            'metrics': metrics,
            'feature_importance': model.get_importance()
        }
        reports[symbol] = result
        models[symbol] = model
        
        return jsonify({
            'success': True,
            'message': f'{symbol} 模型训练完成',
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/predict/<symbol>')
def predict(symbol):
    """预测接口"""
    if symbol not in models:
        return jsonify({'error': '模型未训练'}), 404
    
    model = models[symbol]
    fetcher = CommodityDataFetcher()
    engineer = FeatureEngineer()
    
    # 获取最新数据
    df = fetcher.generate_simulated_data(symbol, days=100)
    features = engineer.extract_features(df)
    
    # 预测
    prediction = model.predict(features.tail(1))[0]
    proba = model.predict_proba(features.tail(1))[0]
    
    signal = "看涨" if prediction == 1 else "看跌"
    
    return jsonify({
        'symbol': symbol,
        'prediction': int(prediction),
        'signal': signal,
        'confidence': float(max(proba) * 100),
        'probabilities': {
            '上涨': float(proba[1]),
            '下跌': float(proba[0])
        }
    })


@app.route('/api/report/<symbol>')
def get_report(symbol):
    """获取分析报告"""
    if symbol not in reports:
        return jsonify({'error': '无报告数据'}), 404
    
    return jsonify(reports[symbol])


@app.route('/api/all_reports')
def get_all_reports():
    """获取所有报告"""
    return jsonify(reports)


@app.route('/api/importance/<symbol>')
def get_importance(symbol):
    """获取特征重要性"""
    if symbol not in models:
        return jsonify({'error': '模型未训练'}), 404
    
    model = models[symbol]
    importance = model.get_importance()
    
    return jsonify({
        'symbol': symbol,
        'feature_importance': importance
    })


if __name__ == '__main__':
    print("=" * 60)
    print("大宗商品MLP投资分析工具 - Web服务")
    print("=" * 60)
    print(f"访问地址: http://localhost:5000")
    print(f"按 Ctrl+C 停止服务")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
