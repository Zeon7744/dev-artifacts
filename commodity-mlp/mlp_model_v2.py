"""
大宗商品MLP投资分析工具 - 改进版MLP模型
添加超参数搜索、早停机制、正则化优化
"""

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class CommodityMLPModel:
    """大宗商品MLP投资预测模型 - 优化版"""
    
    def __init__(
        self,
        hidden_layer_sizes: Tuple[int, ...] = (64, 32),
        activation: str = 'relu',
        solver: str = 'adam',
        alpha: float = 0.0001,  # 减小L2正则化
        batch_size: int = 32,
        learning_rate: str = 'constant',
        learning_rate_init: float = 0.001,
        max_iter: int = 500,
        early_stopping: bool = True,
        n_iter_no_change: int = 20,
        random_state: int = 42,
        do_search: bool = False,  # 是否进行超参数搜索
        use_better_params: bool = True  # 是否使用自适应参数
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
            learning_rate_init: 初始学习率
            max_iter: 最大迭代次数
            early_stopping: 是否启用早停
            n_iter_no_change: 早停容忍轮数
            random_state: 随机种子
            do_search: 是否进行超参数网格搜索
            use_better_params: 是否使用自适应参数（根据特征数量自动调整）
        """
        self.do_search = do_search
        self.use_better_params = use_better_params
        self.best_params_ = None
        self.scaler = StandardScaler()
        self.feature_names: Optional[List[str]] = None
        self.trained = False
        
    def _get_adaptive_params(self, n_features: int) -> dict:
        """根据特征数量自适应调整参数"""
        if n_features > 15:
            # 特征较多时使用更简单的架构防止过拟合
            return dict(
                hidden_layer_sizes=(64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                batch_size=32,
                learning_rate='constant',
                learning_rate_init=0.001,
                max_iter=500,
                early_stopping=True,
                n_iter_no_change=20,
                random_state=42,
                verbose=True
            )
        else:
            # 使用原版推荐参数
            return dict(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                batch_size=32,
                learning_rate='constant',
                max_iter=500,
                random_state=42,
                verbose=True
            )
    
    def _get_param_grid(self) -> dict:
        """定义超参数搜索网格（简化版）"""
        return {
            'hidden_layer_sizes': [(64, 32), (128, 64)],
            'alpha': [0.0001, 0.001],
            'batch_size': [32]
        }
    
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
        
        print("开始训练MLP模型...")
        
        # 超参数搜索
        if self.do_search:
            print("执行超参数搜索...")
            param_grid = self._get_param_grid()
            grid_search = GridSearchCV(
                MLPClassifier(
                    early_stopping=True,
                    max_iter=500,
                    random_state=42,
                    verbose=True
                ),
                param_grid,
                cv=3,
                scoring='accuracy',
                n_jobs=-1,
                verbose=0
            )
            grid_search.fit(X_train_scaled, y_train)
            self.best_params_ = grid_search.best_params_
            self.model = grid_search.best_estimator_
            print(f"最佳参数: {self.best_params_}")
        else:
            # 根据特征数量选择参数
            if self.use_better_params:
                base_params = self._get_adaptive_params(features.shape[1])
            else:
                base_params = dict(
                    hidden_layer_sizes=(128, 64, 32),
                    activation='relu',
                    solver='adam',
                    alpha=0.0001,
                    batch_size=32,
                    learning_rate='constant',
                    max_iter=500,
                    random_state=42,
                    verbose=True
                )
            
            self.model = MLPClassifier(**base_params)
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
            'trained': self.trained,
            'best_params': self.best_params_
        }, path)
        print(f"模型已保存到: {path}")
    
    def load_model(self, path: str):
        """加载模型"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.trained = data['trained']
        self.best_params_ = data.get('best_params')
        print(f"模型已从 {path} 加载")


if __name__ == '__main__':
    # 测试模型
    from data_fetcher import CommodityDataFetcher
    from feature_engineering import FeatureEngineer
    from feature_engineering_v2 import FeatureEngineer as FE2
    
    print("=" * 70)
    print("MLP模型训练测试（优化版 - 修复后）")
    print("=" * 70)
    
    # 获取数据
    fetcher = CommodityDataFetcher()
    df = fetcher.generate_simulated_data('GC=F', days=500)
    
    # 测试原版特征
    print("\n--- 测试原版特征（15个）---")
    fe1 = FeatureEngineer()
    features1 = fe1.extract_features(df)
    target1 = df['Target'].iloc[:len(features1)]
    
    model1 = CommodityMLPModel(use_better_params=True)
    metrics1 = model1.train(features1, target1)
    print(f"原版测试准确率: {metrics1['test_accuracy']:.4f}")
    
    # 测试优化版特征
    print("\n--- 测试优化版特征（28个）---")
    fe2 = FE2()
    features2 = fe2.extract_features(df)
    target2 = df['Target'].iloc[:len(features2)]
    
    model2 = CommodityMLPModel(use_better_params=True)
    metrics2 = model2.train(features2, target2)
    print(f"优化版测试准确率: {metrics2['test_accuracy']:.4f}")
    
    # 对比总结
    print("\n" + "=" * 70)
    print("性能对比")
    print("=" * 70)
    print(f"原版特征 ({features1.shape[1]}个): 测试准确率 {metrics1['test_accuracy']:.4f}")
    print(f"优化版特征 ({features2.shape[1]}个): 测试准确率 {metrics2['test_accuracy']:.4f}")
