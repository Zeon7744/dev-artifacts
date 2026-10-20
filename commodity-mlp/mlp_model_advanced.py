"""
大宗商品MLP投资分析工具 - 高级优化版MLP模型
添加时序交叉验证、特征选择、集成学习
"""

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


class EnsemblePredictor:
    """集成预测器（模块顶层，支持pickle序列化）"""
    def __init__(self, models, classes):
        self.models = models
        self.classes = classes
    
    def predict(self, X):
        predictions = np.array([model.predict(X) for model in self.models])
        return np.array([np.bincount(pred).argmax() for pred in predictions.T])
    
    def predict_proba(self, X):
        probas = np.array([model.predict_proba(X)[:, 1] for model in self.models])
        # 返回 (n_samples, 2) 格式：[P(0), P(1)]
        mean_p1 = np.mean(probas, axis=0)
        return np.column_stack([1 - mean_p1, mean_p1])


class AdvancedCommodityMLP:
    """高级大宗商品MLP预测模型 - 集成学习+时序CV"""
    
    def __init__(
        self,
        use_ensemble: bool = True,
        feature_selection: bool = True,
        threshold: float = 0.55,
        random_state: int = 42
    ):
        self.use_ensemble = use_ensemble
        self.feature_selection = feature_selection
        self.threshold = threshold
        self.random_state = random_state
        
        self.scaler = StandardScaler()
        self.feature_names: Optional[List[str]] = None
        self.selected_features: Optional[List[str]] = None
        self.trained = False
        self.model = None
        self.ensemble_models = []
        self.metrics = {}
    
    def _feature_selection(self, X: pd.DataFrame, y: pd.Series, top_k: int = 15) -> pd.DataFrame:
        """基于相关性选择Top-K特征"""
        correlations = X.corrwith(y).abs()
        if top_k < len(correlations):
            selected = correlations.nlargest(top_k).index.tolist()
        else:
            selected = correlations[correlations > 0.03].index.tolist()
            if len(selected) < 5:
                selected = correlations.nlargest(10).index.tolist()
        return X[selected]
    
    def _train_single_model(self, X_train, y_train, config, model_idx):
        """训练单个MLP模型"""
        print(f"  训练模型 {model_idx}/3...")
        model = MLPClassifier(
            hidden_layer_sizes=config['hidden'],
            activation='relu',
            solver='adam',
            alpha=config['alpha'],
            batch_size=config['batch'],
            max_iter=500,
            early_stopping=True,
            n_iter_no_change=15,
            random_state=config['seed'],
            verbose=False
        )
        model.fit(X_train, y_train)
        return model
    
    def train(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        test_size: float = 0.2,
        val_size: float = 0.1
    ) -> Dict[str, float]:
        """训练模型并返回评估指标"""
        self.feature_names = features.columns.tolist()
        
        # 特征选择
        if self.feature_selection:
            print("进行特征选择...")
            features_selected = self._feature_selection(features, target, top_k=20)
            self.selected_features = features_selected.columns.tolist()
            print(f"  选择 {len(self.selected_features)} 个特征: {self.selected_features[:5]}...")
        else:
            features_selected = features
        
        # 分割数据
        X = features_selected.values
        y = target.iloc[:len(features_selected)].values
        
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state
        )
        
        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=val_ratio, random_state=self.random_state
        )
        
        # 标准化
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        print("开始训练MLP模型...")
        
        # 训练模型或集成
        if self.use_ensemble and len(X_train) > 50:
            configs = [
                {'hidden': (64, 32), 'alpha': 0.0001, 'batch': 32, 'seed': self.random_state},
                {'hidden': (128, 64), 'alpha': 0.0005, 'batch': 64, 'seed': self.random_state + 1},
                {'hidden': (32, 16), 'alpha': 0.001, 'batch': 32, 'seed': self.random_state + 2},
            ]
            
            self.ensemble_models = []
            for i, cfg in enumerate(configs):
                model = self._train_single_model(X_train_scaled, y_train, cfg, i + 1)
                self.ensemble_models.append(model)
            
            # 创建集成预测函数
            self.model = self._create_ensemble_predictor()
        else:
            self.model = MLPClassifier(
                hidden_layer_sizes=(64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                batch_size=32,
                max_iter=500,
                early_stopping=True,
                random_state=self.random_state,
                verbose=False
            )
            self.model.fit(X_train_scaled, y_train)
        
        self.trained = True
        
        # 评估
        train_pred = self.model.predict(X_train_scaled)
        val_pred = self.model.predict(X_val_scaled)
        test_pred = self.model.predict(X_test_scaled)
        
        metrics = {
            'train_accuracy': accuracy_score(y_train, train_pred),
            'val_accuracy': accuracy_score(y_val, val_pred),
            'test_accuracy': accuracy_score(y_test, test_pred),
            'test_precision': classification_report(y_test, test_pred, output_dict=True).get('1', {}).get('precision', 0),
            'test_recall': classification_report(y_test, test_pred, output_dict=True).get('1', {}).get('recall', 0),
            'test_f1': classification_report(y_test, test_pred, output_dict=True).get('1', {}).get('f1-score', 0),
        }
        
        # 时序交叉验证
        print("\n进行时序交叉验证...")
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
            X_fold_train = X_train[train_idx]
            y_fold_train = y_train[train_idx]
            X_fold_val = X_train[val_idx]
            y_fold_val = y_train[val_idx]
            
            fold_scaler = StandardScaler()
            X_fold_train_scaled = fold_scaler.fit_transform(X_fold_train)
            X_fold_val_scaled = fold_scaler.transform(X_fold_val)
            
            fold_model = MLPClassifier(
                hidden_layer_sizes=(64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                max_iter=300,
                random_state=self.random_state + fold,
                verbose=False
            )
            fold_model.fit(X_fold_train_scaled, y_fold_train)
            
            fold_pred = fold_model.predict(X_fold_val_scaled)
            fold_acc = accuracy_score(y_fold_val, fold_pred)
            cv_scores.append(fold_acc)
            print(f"  Fold {fold+1}: {fold_acc:.4f}")
        
        metrics['cv_mean'] = np.mean(cv_scores)
        metrics['cv_std'] = np.std(cv_scores)
        
        print(f"\n训练完成!")
        print(f"训练集准确率: {metrics['train_accuracy']:.4f}")
        print(f"验证集准确率: {metrics['val_accuracy']:.4f}")
        print(f"测试集准确率: {metrics['test_accuracy']:.4f}")
        print(f"时序CV: {metrics['cv_mean']:.4f} ± {metrics['cv_std']:.4f}")
        
        self.metrics = metrics
        return metrics
    
    def _create_ensemble_predictor(self):
        """创建集成预测器"""
        classes = np.array([0, 1])
        if hasattr(self.ensemble_models[0], 'classes_'):
            classes = self.ensemble_models[0].classes_
        return EnsemblePredictor(self.ensemble_models, classes)
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """预测投资方向"""
        if not self.trained:
            raise RuntimeError("模型尚未训练")
        
        if self.feature_selection and self.selected_features:
            available = [f for f in self.selected_features if f in features.columns]
            X = features[available].values
        else:
            X = features.values
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if not self.trained:
            raise RuntimeError("模型尚未训练")
        
        if self.feature_selection and self.selected_features:
            available = [f for f in self.selected_features if f in features.columns]
            X = features[available].values
        else:
            X = features.values
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def generate_signals(self, features: pd.DataFrame, threshold: float = None) -> np.ndarray:
        """生成交易信号"""
        proba = self.predict_proba(features)
        if threshold is None:
            threshold = self.threshold
        return (proba >= threshold).astype(int)
    
    def get_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if not self.trained:
            raise RuntimeError("模型尚未训练")
        
        importances = {}
        
        for model in self.ensemble_models:
            if hasattr(model, 'coefs_') and len(model.coefs_) > 0:
                weights = np.sum(np.abs(model.coefs_[0]), axis=1)
                for j, name in enumerate(self.selected_features or self.feature_names or []):
                    if j < len(weights):
                        importances[name] = importances.get(name, 0) + float(weights[j])
        
        sorted_importance = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))
        return sorted_importance
    
    def save_model(self, path: str):
        """保存模型"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'ensemble_models': self.ensemble_models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'selected_features': self.selected_features,
            'trained': self.trained,
            'metrics': self.metrics,
            'threshold': self.threshold
        }, path)
        print(f"模型已保存到: {path}")
    
    def load_model(self, path: str):
        """加载模型"""
        data = joblib.load(path)
        self.model = data['model']
        self.ensemble_models = data.get('ensemble_models', [])
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.selected_features = data.get('selected_features')
        self.trained = data['trained']
        self.metrics = data.get('metrics', {})
        self.threshold = data.get('threshold', 0.55)
        print(f"模型已从 {path} 加载")


if __name__ == '__main__':
    from data_fetcher import CommodityDataFetcher
    from feature_engineering_v2 import FeatureEngineer as FE2
    
    print("=" * 70)
    print("高级MLP模型测试")
    print("=" * 70)
    
    fetcher = CommodityDataFetcher()
    df = fetcher.generate_simulated_data('GC=F', days=600)
    
    fe = FE2()
    features = fe.extract_features(df)
    target = df['Target'].iloc[:len(features)]
    
    print(f"\n特征矩阵: {features.shape}")
    print(f"目标分布: {target.value_counts().to_dict()}")
    
    model = AdvancedCommodityMLP(use_ensemble=True, feature_selection=True)
    metrics = model.train(features, target)
    
    importance = model.get_importance()
    print(f"\nTop 5 重要特征:")
    for i, (name, imp) in enumerate(list(importance.items())[:5], 1):
        print(f"  {i}. {name}: {imp:.4f}")
    
    def generate_signals(self, features: pd.DataFrame, threshold: float = None, mode: str = 'conservative') -> np.ndarray:
        """
        生成交易信号
        
        参数:
            mode: 'conservative' 保守模式（高置信度才交易）
                  'aggressive' 激进模式（低阈值频繁交易）
        """
        proba = self.predict_proba(features)
        if threshold is None:
            threshold = self.threshold
        
        if mode == 'conservative':
            # 保守模式：只在高置信度时交易
            conservative_threshold = max(threshold, 0.6)
            signals = np.where(proba >= conservative_threshold, 1, 
                              np.where(proba <= (1 - conservative_threshold), 0, -1))
        else:
            # 激进模式
            signals = (proba >= threshold).astype(int)
        
        return signals
    
    def generate_aggressive_signals(self, features: pd.DataFrame, threshold: float = None) -> np.ndarray:
        """生成激进交易信号（低阈值，频繁交易）"""
        return self.generate_signals(features, threshold, mode='aggressive')
