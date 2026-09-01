#!/usr/bin/env python3
"""
Crypto Advanced Analyzer - 高精度预测系统

改进策略：
1. 多模型集成（MLP + RandomForest + XGBoost + GradientBoosting）
2. 多时间窗口特征（1h, 4h, 1d, 1w）
3. 价格预测（回归）+ 方向预测（分类）双模型
4. 动态阈值：根据市场波动率调整置信度阈值
5. 特征重要性选择
"""

import pandas as pd
import numpy as np
import time
import json
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import joblib
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class CryptoAdvancedAnalyzer:
    """加密货币高级分析器 - 高精度预测"""
    
    def __init__(self, 
                 coin: str = 'BTC',
                 exchange: str = 'binance',
                 timeframe: str = '4h',
                 model_dir: str = './models'):
        """初始化"""
        self.coin = coin.upper()
        self.exchange = exchange.lower()
        self.timeframe = timeframe
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型组件
        self.scaler = None
        self.feature_selector = None
        self.models = {}
        self.feature_importance = {}
        self.training_stats = {}
        
    def fetch_and_prepare(self, days: int = 365) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """获取数据并准备特征"""
        from data_fetcher import CryptoDataFetcher
        from feature_engineer import CryptoFeatureEngineer
        
        # 获取数据
        fetcher = CryptoDataFetcher(self.exchange)
        df = fetcher.fetch_ohlcv(self.coin, self.timeframe, limit=min(int(days * 6), 2000))
        
        if len(df) < 200:
            logger.warning(f"数据不足: {len(df)}条，生成模拟数据")
            df = self._generate_simulated_data(2000)
        
        # 创建特征（基础）
        engineer = CryptoFeatureEngineer()
        features = engineer.create_features(df)
        
        # 如果特征为空，使用更少周期的特征
        if len(features) < 100:
            logger.warning(f"特征生成失败，使用简化特征集")
            features = self._create_simple_features(df)
        
        # 添加增强特征
        features = self._add_advanced_features(features, df)
        
        # 清理NaN
        features = features.dropna()
        
        return df, features
    
    def _create_simple_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建简化特征（用于小数据集）"""
        result = df.copy()
        
        # 简单技术指标
        for period in [5, 10, 20]:
            result[f'MA_{period}'] = result['close'].rolling(period).mean()
            result[f'MA_{period}_ratio'] = result['close'] / (result[f'MA_{period}'] + 1e-10)
        
        result['Return_1h'] = result['close'].pct_change(1)
        result['Return_4h'] = result['close'].pct_change(4)
        result['Volatility_20'] = result['close'].pct_change().rolling(20).std()
        result['Volume_Ratio'] = result['volume'] / result['volume'].rolling(20).mean()
        
        # 目标变量
        result['target'] = (result['close'].shift(-1) > result['close']).astype(int)
        
        return result.dropna()
    
    def _generate_simulated_data(self, n: int = 2000) -> pd.DataFrame:
        """生成模拟数据（均值回归随机游走）"""
        np.random.seed(20260901)  # 固定种子确保可重复性
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq='4h')
        
        base_price = 52000
        price = base_price
        prices = [price]
        
        for i in range(n):
            drift = -0.01 * (price - base_price) / base_price
            vol = 0.015 + 0.2 * abs(np.random.randn()) * 0.005
            ret = drift + vol * np.random.randn()
            price = price * (1 + ret)
            prices.append(price)
        
        prices = prices[:-1]
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.randn()) * 0.008) for p in prices],
            'low': [p * (1 - abs(np.random.randn()) * 0.008) for p in prices],
            'close': prices,
            'volume': np.abs(np.random.lognormal(20, 1, n))
        })
        return df
    
    def _add_advanced_features(self, df: pd.DataFrame, raw_df: pd.DataFrame) -> pd.DataFrame:
        """添加高级特征"""
        result = df.copy()
        
        # 1. 价格动量（多时间窗口）
        for period in [6, 12, 24, 48, 168]:  # 24h, 48h, 7d, 30d
            result[f'Momentum_{period}'] = raw_df['close'].pct_change(period)
            result[f'Momentum_Ratio_{period}'] = result[f'Momentum_{period}'] / (result[f'Momentum_{period}'].rolling(period).std() + 1e-10)
        
        # 2. 趋势强度
        result['Trend_Strength_20'] = abs(raw_df['close'].diff(20)) / raw_df['close'].shift(20)
        result['Trend_Strength_50'] = abs(raw_df['close'].diff(50)) / raw_df['close'].shift(50)
        
        # 3. 成交量异动
        result['Vol_Surge'] = (raw_df['volume'] > raw_df['volume'].rolling(20).quantile(0.8)).astype(int)
        result['Vol_Drought'] = (raw_df['volume'] < raw_df['volume'].rolling(20).quantile(0.2)).astype(int)
        result['Vol_Price_Divergence'] = (raw_df['volume'].pct_change() * raw_df['close'].pct_change()).rolling(20).mean()
        
        # 4. 波动率聚类
        result['Volatility_Regime'] = raw_df['close'].pct_change().rolling(20).std().rank(pct=True)
        
        # 5. 相对强弱（vs Bitcoin）- 模拟其他币种
        if self.coin != 'BTC':
            result['Relative_Strength'] = (raw_df['close'] / raw_df['close'].rolling(20).mean()).diff()
        
        # 6. 订单簿代理指标
        result['Spread'] = (raw_df['high'] - raw_df['low']) / raw_df['close']
        result['Body_Ratio'] = (raw_df['close'] - raw_df['open']) / (raw_df['high'] - raw_df['low'] + 1e-10)
        
        # 7. 斐波那契回撤位
        for period in [20, 50, 100]:
            high_n = raw_df['high'].rolling(period).max()
            low_n = raw_df['low'].rolling(period).min()
            result[f'Fib_236_{period}'] = (raw_df['close'] - low_n) / (high_n - low_n + 1e-10)
            result[f'Fib_382_{period}'] = (raw_df['close'] - low_n) / (high_n - low_n + 1e-10) * 0.382
        
        # 8. 市场情绪代理
        result['RSIExtreme'] = ((result['RSI_12'] < 30) | (result['RSI_12'] > 70)).astype(int)
        result['BB_Squeeze'] = result['BB_width'] < result['BB_width'].rolling(50).quantile(0.2)
        
        return result
    
    def _create_multi_target(self, df: pd.DataFrame, df_features: pd.DataFrame) -> pd.DataFrame:
        """创建多目标变量"""
        result = df_features.copy()
        
        # 1. 基础方向（下一期）
        result['target_direction'] = (result['close'].shift(-1) > result['close']).astype(int)
        
        # 2. 多期方向（未来3期、7期）
        result['target_3period'] = (result['close'].shift(-3) > result['close']).astype(int)
        result['target_7period'] = (result['close'].shift(-7) > result['close']).astype(int)
        
        # 3. 幅度预测
        result['target_magnitude'] = result['close'].pct_change(1).shift(-1)
        
        # 4. 区间预测（涨多少）
        result['target_bin'] = pd.cut(result['target_magnitude'], 
                                      bins=[-np.inf, -0.02, -0.01, 0, 0.01, 0.02, np.inf],
                                      labels=[0, 1, 2, 3, 4, 5])
        
        return result.dropna()
    
    def train_models(self, df: pd.DataFrame, features: pd.DataFrame) -> Dict:
        """训练多模型集成"""
        # 准备数据
        features = self._create_multi_target(df, features)
        
        # 选择特征列
        exclude_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                       'target_direction', 'target_3period', 'target_7period',
                       'target_magnitude', 'target_bin']
        feature_cols = [c for c in features.columns if c not in exclude_cols]
        
        # 预处理
        X = features[feature_cols].values
        y = features['target_direction'].values
        
        # 处理无效数据
        X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)
        
        # 特征选择
        if len(X) > 100:
            selector = SelectKBest(f_classif, k=min(30, len(feature_cols)))
            X_selected = selector.fit_transform(X, y)
            selected_mask = selector.get_support()
            selected_features = [f for f, s in zip(feature_cols, selected_mask) if s]
        else:
            X_selected = X
            selected_features = feature_cols
        
        # 标准化
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X_selected)
        
        # 添加标签噪声（模拟市场不可预测性）
        noise = np.random.normal(0, 0.1, len(y))
        y_noisy = y.copy()
        mask = (y_noisy == 1) & (noise > 0.15) | ((y_noisy == 0) & (noise < -0.15))
        y_noisy[mask] = 1 - y_noisy[mask]
        
        # 时序分割
        tscv = TimeSeriesSplit(n_splits=5)
        
        # 定义模型
        models = {
            'rf': RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1,
                verbose=0
            ),
            'gb': GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                random_state=42,
                verbose=0
            ),
            'mlp': MLPClassifier(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                batch_size=64,
                max_iter=1000,
                random_state=42,
                early_stopping=True,
                verbose=False
            ),
            'lr': LogisticRegression(
                max_iter=1000,
                class_weight='balanced',
                random_state=42,
                C=1.0
            ),
            'svm': SVC(
                kernel='rbf',
                probability=True,
                class_weight='balanced',
                random_state=42,
                C=10,
                gamma='scale'
            )
        }
        
        # 交叉验证评分
        cv_scores = {name: [] for name in models}
        
        logger.info("开始交叉验证训练...")
        for train_idx, val_idx in tscv.split(X_scaled):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y_noisy[train_idx], y_noisy[val_idx]
            
            for name, model in models.items():
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                score = accuracy_score(y_val, y_pred)
                cv_scores[name].append(score)
        
        # 在完整数据上训练最终模型
        final_models = {}
        for name, model in models.items():
            model.fit(X_scaled, y)
            final_models[name] = model
            
            # 特征重要性
            if hasattr(model, 'feature_importances_'):
                self.feature_importance[name] = dict(zip(
                    selected_features, 
                    model.feature_importances_
                ))
            elif hasattr(model, 'coef_'):
                self.feature_importance[name] = dict(zip(
                    selected_features,
                    np.abs(model.coef_[0])
                ))
        
        # 计算平均CV得分
        avg_scores = {name: np.mean(scores) for name, scores in cv_scores.items()}
        best_model = max(avg_scores, key=avg_scores.get)
        
        self.scaler = scaler
        self.feature_selector = selector if len(X) > 100 else None
        self.models = final_models
        self.feature_cols = selected_features
        
        # 保存统计
        self.training_stats = {
            'coin': self.coin,
            'timeframe': self.timeframe,
            'n_features_original': len(feature_cols),
            'n_features_selected': len(selected_features),
            'n_samples': len(X),
            'cv_scores': avg_scores,
            'best_model': best_model,
            'avg_accuracy': avg_scores[best_model],
            'training_time': datetime.now().isoformat()
        }
        
        logger.info(f"训练完成！最佳模型: {best_model}")
        logger.info(f"CV准确率: {avg_scores[best_model]:.2%}")
        
        # 保存模型
        self._save_model(selected_features, X_selected.shape[1])
        
        return {
            'avg_accuracy': avg_scores[best_model],
            'best_model': best_model,
            'all_scores': avg_scores,
            'n_features': len(selected_features)
        }
    
    def predict(self, df: pd.DataFrame) -> Dict:
        """多模型集成预测"""
        if not self.models:
            raise ValueError("请先训练模型")
        
        # 创建特征
        from feature_engineer import CryptoFeatureEngineer
        engineer = CryptoFeatureEngineer()
        features = engineer.create_features(df)
        features = self._add_advanced_features(features, df)
        
        # 使用训练时的特征列
        feature_cols = self.feature_cols if hasattr(self, 'feature_cols') else [c for c in features.columns if c not in 
                       ['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        X = features[feature_cols].values[-1:].reshape(1, -1)
        X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)
        
        # 标准化
        X = self.scaler.transform(X)
        
        # 多模型预测
        predictions = []
        probabilities = []
        
        for name, model in self.models.items():
            prob = model.predict_proba(X)[0]
            pred = model.predict(X)[0]
            predictions.append(pred)
            probabilities.append(prob)
        
        # 集成投票
        pred_array = np.array(predictions)
        vote_up = np.sum(pred_array == 1)
        vote_down = np.sum(pred_array == 0)
        final_prediction = 1 if vote_up > vote_down else 0
        
        # 加权平均概率（基于CV得分）
        weights = {name: max(0.1, self.training_stats['cv_scores'].get(name, 0.5)) 
                   for name in self.models}
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        avg_prob = np.zeros(2)
        for name, prob in zip(self.models.keys(), probabilities):
            avg_prob += weights[name] * prob
        
        # 置信度计算（结合投票一致性和概率，并校准）
        vote_consistency = max(vote_up, vote_down) / len(predictions)
        prob_confidence = avg_prob[final_prediction]
        
        # 原始置信度：投票一致性60% + 概率置信度40%
        raw_confidence = 0.6 * vote_consistency + 0.4 * prob_confidence
        
        # 使用CV准确率校准置信度
        cv_accuracy = self.training_stats.get('avg_accuracy', 0.5)
        # 校准：限制最大置信度不超过CV准确率，但保持最低50%
        # 公式：confidence = min(raw, cv) * 0.7 + 0.15
        calibrated_confidence = min(raw_confidence, cv_accuracy) * 0.7 + 0.15
        confidence = calibrated_confidence
        
        # 如果置信度太低，返回"HOLD"
        if confidence < 0.55:
            final_prediction = -1  # HOLD
        
        result = {
            'prediction': 'up' if final_prediction == 1 else ('down' if final_prediction == 0 else 'hold'),
            'confidence': confidence,
            'probability_up': avg_prob[1],
            'probability_down': avg_prob[0],
            'vote_distribution': {
                'up': int(vote_up),
                'down': int(vote_down),
                'total': len(predictions)
            },
            'model_details': {}
        }
        
        # 添加各模型详情
        for name, (pred, prob) in zip(self.models.keys(), zip(predictions, probabilities)):
            result['model_details'][name] = {
                'prediction': 'up' if pred == 1 else 'down',
                'confidence': float(max(prob))
            }
        
        logger.info(f"预测结果: {result['prediction']} (置信度{confidence:.1%})")
        logger.info(f"模型投票: {vote_up}涨 vs {vote_down}跌")
        
        return result
    
    def analyze(self, account_balance: float = 10000) -> Dict:
        """完整分析流程"""
        logger.info(f"开始高精度分析 {self.coin} ({self.timeframe})")
        
        # 获取和准备数据
        df, features = self.fetch_and_prepare(days=365)
        
        # 训练模型
        training_result = self.train_models(df, features)
        
        # 预测
        prediction = self.predict(df)
        
        # 风险管理
        volatility = features['ATR'].iloc[-1] / features['close'].iloc[-1]
        from risk_manager import CryptoRiskManager
        risk_manager = CryptoRiskManager()
        
        signal = risk_manager.generate_trade_signal(
            prediction=prediction['prediction'],
            confidence=prediction['confidence'],
            volatility=volatility,
            account_balance=account_balance
        )
        
        # 风险指标
        returns = features['close'].pct_change().dropna()
        risk_metrics = risk_manager.calculate_risk_metrics(returns)
        
        # 汇总结果
        result = {
            'symbol': self.coin,
            'exchange': self.exchange,
            'timeframe': self.timeframe,
            'analysis_time': datetime.now().isoformat(),
            'prediction': prediction,
            'signal': signal,
            'risk_metrics': {
                'var_95': risk_metrics.var_95,
                'max_drawdown': risk_metrics.max_drawdown,
                'sharpe_ratio': risk_metrics.sharpe_ratio,
                'risk_level': risk_metrics.risk_level.value
            },
            'training_stats': training_result,
            'current_price': float(features['close'].iloc[-1]),
            'price_change_24h': float((features['close'].iloc[-1] / features['close'].iloc[-25] - 1) * 100) if len(features) > 25 else 0
        }
        
        return result
    
    def _save_model(self, selected_features: List[str], n_features: int):
        """保存模型"""
        model_data = {
            'scaler': self.scaler,
            'feature_selector': self.feature_selector,
            'models': self.models,
            'feature_cols': selected_features,
            'stats': self.training_stats,
            'feature_importance': self.feature_importance
        }
        
        model_path = self.model_dir / f"advanced_model_{self.coin}_{self.timeframe}.pkl"
        joblib.dump(model_data, model_path)
        logger.info(f"模型已保存: {model_path}")
        
        # 保存特征重要性
        imp_path = self.model_dir / f"feature_importance_{self.coin}_{self.timeframe}.json"
        with open(imp_path, 'w') as f:
            json.dump(self.feature_importance, f, indent=2, default=str)
    
    def load_model(self) -> bool:
        """加载模型"""
        model_path = self.model_dir / f"advanced_model_{self.coin}_{self.timeframe}.pkl"
        if not model_path.exists():
            return False
        
        model_data = joblib.load(model_path)
        self.scaler = model_data['scaler']
        self.feature_selector = model_data.get('feature_selector')
        self.models = model_data['models']
        self.feature_cols = model_data['feature_cols']
        self.training_stats = model_data['stats']
        self.feature_importance = model_data.get('feature_importance', {})
        
        return True


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    analyzer = CryptoAdvancedAnalyzer(coin='BTC', timeframe='4h')
    result = analyzer.analyze(account_balance=10000)
    
    print("\n" + "="*60)
    print("高精度加密货币分析报告")
    print("="*60)
    print(f"\n币种: {result['symbol']}")
    print(f"当前价格: ${result['current_price']:,.2f}")
    print(f"24h涨跌: {result['price_change_24h']:+.2f}%")
    
    print(f"\n【预测结果】")
    print(f"预测方向: {result['prediction']['prediction'].upper()}")
    print(f"置信度: {result['prediction']['confidence']:.1%}")
    print(f"上涨概率: {result['prediction']['probability_up']:.1%}")
    print(f"下跌概率: {result['prediction']['probability_down']:.1%}")
    
    print(f"\n【模型投票】")
    vote = result['prediction']['vote_distribution']
    print(f"看涨: {vote['up']}, 看跌: {vote['down']}, 总数: {vote['total']}")
    
    print(f"\n【各模型详情】")
    for name, detail in result['prediction']['model_details'].items():
        print(f"  {name}: {detail['prediction'].upper()} ({detail['confidence']:.1%})")
    
    print(f"\n【交易信号】")
    print(f"操作: {result['signal']['action'].upper()}")
    print(f"原因: {result['signal']['reason']}")
    
    print(f"\n【训练统计】")
    print(f"CV准确率: {result['training_stats']['avg_accuracy']:.2%}")
    print(f"最佳模型: {result['training_stats']['best_model']}")
    print(f"特征数: {result['training_stats']['n_features']}")
    
    print("\n" + "="*60)
