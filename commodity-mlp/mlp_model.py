"""
大宗商品MLP投资分析工具 - MLP模型模块
使用scikit-learn的MLPClassifier进行投资预测
"""

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class CommodityMLPModel:
    """大宗商品MLP投资预测模型"""
    
    def __init__(
        self,
        hidden_layer_sizes: Tuple[int, ...] = (128, 64, 32),
        activation: str = 'relu',
        solver: str = 'adam',
        alpha: float = 0.0001,
        batch_size: int = 32,
        learning_rate: str = 'constant',
        max_iter: int = 500,
        random_state: int = 42
    ):
        """
        初始化MLP模型
        
        参数:
            hidden_layer_sizes: 隐藏层神经元数量
            activation: 激活函数
            solver: 优化器
            alpha: L2正则化参数
            batch_size: 批次大小
            learning_rate: 学习率策略
            max_iter: 最大迭代次数
            random_state: 随机种子
        """
        self.model = MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            activation=activation,
            solver=solver,
            alpha=alpha,
            batch_size=batch_size,
            learning_rate=learning_rate,
            max_iter=max_iter,
            random_state=random_state,
            verbose=True
        )
        self.scaler = StandardScaler()
        self.feature_names: Optional[List[str]] = None
        self.trained = False
        
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
        
        # 分割数据
        X = features.values
        y = target.values
        
        # 先划分训练+验证和测试
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # 再从训练+验证中划分训练和验证
        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=val_ratio, random_state=42, stratify=y_train_val
        )
        
        # 标准化
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练模型
        print("开始训练MLP模型...")
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
        
        # 交叉验证
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='accuracy')
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()
        
        print(f"\n训练完成!")
        print(f"训练集准确率: {metrics['train_accuracy']:.4f}")
        print(f"验证集准确率: {metrics['val_accuracy']:.4f}")
        print(f"测试集准确率: {metrics['test_accuracy']:.4f}")
        print(f"交叉验证: {metrics['cv_mean']:.4f} ± {metrics['cv_std']:.4f}")
        
        return metrics
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """预测投资方向"""
        if not self.trained:
            raise RuntimeError("模型尚未训练，请先调用train方法")
        
        X_scaled = self.scaler.transform(features.values)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if not self.trained:
            raise RuntimeError("模型尚未训练，请先调用train方法")
        
        X_scaled = self.scaler.transform(features.values)
        return self.model.predict_proba(X_scaled)
    
    def get_importance(self) -> Dict[str, float]:
        """获取特征重要性（基于权重绝对值）"""
        if not self.trained:
            raise RuntimeError("模型尚未训练")
        
        # 计算第一层的权重绝对值之和
        importances = {}
        for i, name in enumerate(self.feature_names):
            if i < self.model.coefs_[0].shape[1]:
                importance = np.sum(np.abs(self.model.coefs_[0][i]))
                importances[name] = float(importance)
        
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
            'trained': self.trained
        }, path)
        print(f"模型已保存到: {path}")
    
    def load_model(self, path: str):
        """加载模型"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.trained = data['trained']
        print(f"模型已从 {path} 加载")


if __name__ == '__main__':
    # 测试模型
    from data_fetcher import CommodityDataFetcher
    from feature_engineering import FeatureEngineer
    
    print("=" * 60)
    print("MLP模型训练测试")
    print("=" * 60)
    
    # 获取数据
    fetcher = CommodityDataFetcher()
    engineer = FeatureEngineer()
    
    # 测试单个商品
    symbol = 'GC=F'
    print(f"\n处理商品: {symbol}")
    df = fetcher.generate_simulated_data(symbol, days=800)
    features = engineer.extract_features(df)
    target = df['Target'].iloc[:len(features)]
    
    print(f"特征矩阵形状: {features.shape}")
    print(f"目标变量分布: {target.value_counts().to_dict()}")
    
    # 训练模型
    model = CommodityMLPModel()
    metrics = model.train(features, target)
    
    # 预测
    predictions = model.predict(features.head(10))
    print(f"\n前10个预测结果: {predictions}")
    
    # 特征重要性
    importance = model.get_importance()
    print(f"\n特征重要性Top5:")
    for i, (feat, imp) in enumerate(list(importance.items())[:5], 1):
        print(f"  {i}. {feat}: {imp:.4f}")
    
    # 保存模型
    model.save_model('/tmp/test_mlp_model.pkl')
