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
from sklearn.ensemble import VotingClassifier
import joblib
import os
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class AdvancedCommodityMLP:
    """高级大宗商品MLP预测模型"""
    
    def __init__(
        self,
        use_ensemble: bool = True,
        feature_selection: bool = True,
        threshold: float = 0.55,
        random_state: int = 42
    ):
        """
        初始化模型
        
        参数:
            use_ensemble: 是否使用集成学习
            feature_selection: 是否进行特征选择
            threshold: 交易信号阈值
            random_state: 随机种子
        """
        self.use_ensemble = use_ensemble
        self.feature_selection = feature_selection
        self.threshold = threshold
        self.random_state = random_state
        
        self.scaler = StandardScaler()
        self.feature_names: Optional[List[str]] = None
        self.selected_features: Optional[List[str]] = None
        self.trained = False
        self.model = None
        self.metrics = {}
    
    def _feature_selection(self, X: pd.DataFrame, y: pd.Series, top_k: int = 20) -> pd.DataFrame:
        """
        基于相关性选择Top-K特征
        
        参数:
            X: 特征DataFrame
            y: 目标变量
            top_k: 选择特征数量
            
        返回:
            选择后的特征DataFrame
        """
        # 计算每个特征与目标变量的相关性
        correlations = X.corrwith(y).abs()
        
        # 选择Top-K特征
        if top_k < len(correlations):
            selected = correlations.nlargest(top_k).index.tolist()
        else:
            # 或者选择显著相关的特征（|corr| > 0.03）
            selected = correlations[correlations > 0.03].index.tolist()
            if len(selected) < 5:
                selected = correlations.nlargest(10).index.tolist()
        
        return X[selected]
    
    def _create_ensemble(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray) -> object:
        """
        创建集成模型（多个MLP的多数投票）
        
        参数:
            X_train: 训练特征
            y_train: 训练标签
            X_val: 验证特征（用于早停）
            
        返回:
            集成模型
        """
        # 创建多个不同配置的MLP
        models = [
            MLPClassifier(
                hidden_layer_sizes=(64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                batch_size=32,
                learning_rate='constant',
                learning_rate_init=0.001,
                max_iter=500,
                early_stopping=True,
                n_iter_no_change=15,
                random_state=self.random_state,
                verbose=False
            ),
            MLPClassifier(
                hidden_layer_sizes=(128, 64),
                activation='relu',
                solver='adam',
                alpha=0.0005,
                batch_size=64,
                max_iter=500,
                early_stopping=True,
                n_iter_no_change=15,
                random_state=self.random_state + 1,
                verbose=False
            ),
            MLPClassifier(
                hidden_layer_sizes=(32, 16),
                activation='relu',
                solver='adam',
                alpha=0.001,
                batch_size=32,
                max_iter=300,
                random_state=self.random_state + 2,
                verbose=False
            )
        ]
        
        # 拟合基础模型
        for i, model in enumerate(models):
            print(f"  训练模型 {i+1}/3...")
            X_scaled = self.scaler.transform(X_train) if hasattr(self, 'scaler_trained') else self.scaler.fit_transform(X_train)
            model.fit(X_scaled, y_train)
            if not hasattr(self, 'scaler_trained'):
                self.scaler_trained = True
        
        # 创建软投票集成
        ensemble = VotingClassifier(
            estimators=[('mlp1', models[0]), ('mlp2', models[1]), ('mlp3', models[2])],
            voting='soft'  # 使用概率加权投票
        )
        
        return ensemble
    
    def train(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        test_size: float = 0.2,
        val_size: float = 0.1
    ) -> Dict[str, float]:
        """
        训练模型并返回评估指标
        
        参数:
            features: 特征DataFrame
            target: 目标变量Series
            test_size: 测试集比例
            val_size: 验证集比例
            
        返回:
            包含各项指标的字典
        """
        self.feature_names = features.columns.tolist()
        
        # 特征选择
        if self.feature_selection:
            print("进行特征选择...")
            features_selected = self._feature_selection(features, target, top_k=15)
            self.selected_features = features_selected.columns.tolist()
            print(f"  选择 {len(self.selected_features)} 个特征: {self.selected_features[:5]}...")
        else:
            features_selected = features
        
        # 分割数据
        X = features_selected.values
        y = target.iloc[:len(features_selected)].values
        
        # 时序分割（训练+验证 / 测试）
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state
        )
        
        # 再分割训练和验证
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
            # 创建集成模型
            models = [
                MLPClassifier(
                    hidden_layer_sizes=(64, 32),
                    activation='relu',
                    solver='adam',
                    alpha=0.0001,
                    batch_size=32,
                    learning_rate='constant',
                    learning_rate_init=0.001,
                    max_iter=500,
                    early_stopping=True,
                    n_iter_no_change=15,
                    random_state=self.random_state,
                    verbose=False
                ),
                MLPClassifier(
                    hidden_layer_sizes=(128, 64),
                    activation='relu',
                    solver='adam',
                    alpha=0.0005,
                    batch_size=64,
                    max_iter=500,
                    early_stopping=True,
                    n_iter_no_change=15,
                    random_state=self.random_state + 1,
                    verbose=False
                ),
                MLPClassifier(
                    hidden_layer_sizes=(32, 16),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    batch_size=32,
                    max_iter=300,
                    random_state=self.random_state + 2,
                    verbose=False
                )
            ]
            
            # 单独训练每个基模型
            for i, model in enumerate(models):
                print(f"  训练模型 {i+1}/3...")
                model.fit(X_train_scaled, y_train)
            
            # 创建软投票集成（使用已训练的模型）
            from sklearn.ensemble import VotingClassifier
            self.model = VotingClassifier(
                estimators=[('mlp1', models[0]), ('mlp2', models[1]), ('mlp3', models[2])],
                voting='soft'
            )
            # 重新fit以包装已训练的模型
            self.model.fit(X_train_scaled, y_train)
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
        
        # 时序交叉验证（模拟真实交易场景）
        print("\n进行时序交叉验证...")
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
            X_fold_train = X_train[train_idx]
            y_fold_train = y_train[train_idx]
            X_fold_val = X_train[val_idx]
            y_fold_val = y_train[val_idx]
            
            # 重新标准化（模拟真实场景）
            fold_scaler = StandardScaler()
            X_fold_train_scaled = fold_scaler.fit_transform(X_fold_train)
            X_fold_val_scaled = fold_scaler.transform(X_fold_val)
            
            # 训练fold模型
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
            
            # 评估
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
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """预测投资方向"""
        if not self.trained:
            raise RuntimeError("模型尚未训练")
        
        # 特征选择
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
        return self.model.predict_proba(X_scaled)[:, 1]
    
    def generate_signals(self, features: pd.DataFrame, threshold: float = None) -> np.ndarray:
        """生成交易信号（考虑阈值）"""
        proba = self.predict_proba(features)
        if threshold is None:
            threshold = self.threshold
        return (proba >= threshold).astype(int)
    
    def get_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if not self.trained:
            raise RuntimeError("模型尚未训练")
        
        importances = {}
        
        # 如果是集成模型，获取每个基模型的权重
        if hasattr(self.model, 'estimators_'):
            for i, estimator in enumerate(self.model.estimators_):
                if hasattr(estimator, 'coefs_') and len(estimator.coefs_) > 0:
                    weights = np.sum(np.abs(estimator.coefs_[0]), axis=1)
                    for j, name in enumerate(self.selected_features if self.selected_features else self.feature_names):
                        if j < len(weights):
                            importances[name] = importances.get(name, 0) + weights[j]
        else:
            # 单个模型
            if hasattr(self.model, 'coefs_') and len(self.model.coefs_) > 0:
                weights = np.sum(np.abs(self.model.coefs_[0]), axis=1)
                for j, name in enumerate(self.feature_names or []):
                    if j < len(weights):
                        importances[name] = float(weights[j])
        
        # 排序
        sorted_importance = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))
        return sorted_importance
    
    def save_model(self, path: str):
        """保存模型"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
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
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.selected_features = data.get('selected_features')
        self.trained = data['trained']
        self.metrics = data.get('metrics', {})
        self.threshold = data.get('threshold', 0.55)
        print(f"模型已从 {path} 加载")


if __name__ == '__main__':
    # 测试高级模型
    from data_fetcher import CommodityDataFetcher
    from feature_engineering_v2 import FeatureEngineer as FE2
    
    print("=" * 70)
    print("高级MLP模型测试")
    print("=" * 70)
    
    fetcher = CommodityDataFetcher()
    df = fetcher.generate_simulated_data('GC=F', days=600)
    
    # 提取特征
    fe = FE2()
    features = fe.extract_features(df)
    target = df['Target'].iloc[:len(features)]
    
    print(f"\n特征矩阵: {features.shape}")
    print(f"目标分布: {target.value_counts().to_dict()}")
    
    # 训练模型
    model = AdvancedCommodityMLP(use_ensemble=True, feature_selection=True)
    metrics = model.train(features, target)
    
    # 特征重要性
    importance = model.get_importance()
    print(f"\nTop 5 重要特征:")
    for i, (name, imp) in enumerate(list(importance.items())[:5], 1):
        print(f"  {i}. {name}: {imp:.4f}")
