"""
大宗商品MLP投资分析工具 - 集成学习模块
支持 VotingClassifier 和 StackingClassifier
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import VotingClassifier, StackingClassifier, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class CommodityEnsembleModel:
    """大宗商品集成学习预测模型"""
    
    def __init__(
        self,
        model_type: str = 'voting',
        voting: str = 'soft',
        random_state: int = 42
    ):
        """
        初始化集成学习模型
        
        参数:
            model_type: 集成类型 ('voting' 或 'stacking')
            voting: 投票策略 ('hard' 或 'soft')，仅voting模式有效
            random_state: 随机种子
        """
        self.model_type = model_type
        self.voting = voting
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.history = []
        
    def _build_base_estimators(self) -> List:
        """构建基础预测器列表"""
        return [
            ('mlp', MLPClassifier(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                max_iter=500,
                random_state=self.random_state
            )),
            ('rf', RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=self.random_state,
                n_jobs=-1
            )),
            ('gb', GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=self.random_state
            ))
        ]
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> 'CommodityEnsembleModel':
        """
        训练集成模型
        
        参数:
            X: 特征矩阵 (n_samples, n_features)
            y: 目标变量
            feature_names: 特征名称列表
        """
        self.feature_names = feature_names
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        if self.model_type == 'voting':
            estimators = self._build_base_estimators()
            self.model = VotingClassifier(
                estimators=estimators,
                voting=self.voting,
                n_jobs=-1
            )
        else:  # stacking
            estimators = self._build_base_estimators()
            self.model = StackingClassifier(
                estimators=estimators,
                final_estimator=LogisticRegression(random_state=self.random_state),
                cv=5
            )
        
        self.model.fit(X_scaled, y)
        
        # 记录训练历史
        train_score = self.model.score(X_scaled, y)
        self.history.append({
            'type': self.model_type,
            'voting': self.voting if self.model_type == 'voting' else None,
            'train_accuracy': train_score,
            'timestamp': pd.Timestamp.now().isoformat()
        })
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测分类结果"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        cv: int = 5,
        use_time_series: bool = True
    ) -> Dict[str, float]:
        """
        交叉验证
        
        参数:
            X: 特征矩阵
            y: 目标变量
            cv: 折叠数
            use_time_series: 是否使用时序交叉验证
        """
        X_scaled = self.scaler.transform(X)
        
        if use_time_series:
            cv_splitter = TimeSeriesSplit(n_splits=cv)
        else:
            from sklearn.model_selection import KFold
            cv_splitter = KFold(n_splits=cv, shuffle=True, random_state=self.random_state)
        
        scores = cross_val_score(self.model, X_scaled, y, cv=cv_splitter, scoring='accuracy')
        
        return {
            'mean_accuracy': float(scores.mean()),
            'std_accuracy': float(scores.std()),
            'fold_scores': [float(s) for s in scores],
            'method': 'time_series' if use_time_series else 'kfold'
        }
    
    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        """获取特征重要性（基于MLP权重）"""
        if self.model is None:
            raise ValueError("模型尚未训练")
        
        # 获取MLP的权重
        mlp_model = None
        for name, est in self.model.named_estimators_.items():
            if name == 'mlp' and hasattr(est, 'coefs_'):
                mlp_model = est
                break
        
        if mlp_model is None:
            return pd.DataFrame()
        
        # 计算重要性（第一层权重的绝对值之和）
        importance = np.abs(mlp_model.coefs_[0]).sum(axis=1)
        
        if self.feature_names:
            df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': importance
            })
        else:
            df = pd.DataFrame({
                'feature': [f'feat_{i}' for i in range(len(importance))],
                'importance': importance
            })
        
        return df.sort_values('importance', ascending=False).head(top_n)
    
    def save(self, path: str):
        """保存模型"""
        if self.model is None:
            raise ValueError("没有可保存的模型")
        
        save_dict = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'voting': self.voting,
            'history': self.history
        }
        joblib.dump(save_dict, path)
        
    def load(self, path: str):
        """加载模型"""
        save_dict = joblib.load(path)
        self.model = save_dict['model']
        self.scaler = save_dict['scaler']
        self.feature_names = save_dict.get('feature_names')
        self.model_type = save_dict.get('model_type', 'voting')
        self.voting = save_dict.get('voting', 'soft')
        self.history = save_dict.get('history', [])


if __name__ == '__main__':
    # 测试示例
    print("=== 集成学习模型测试 ===")
    
    # 生成示例数据
    np.random.seed(42)
    X = np.random.randn(500, 20)
    y = np.random.randint(0, 2, 500)
    feature_names = [f'feature_{i}' for i in range(20)]
    
    # 训练Voting模型
    voting_model = CommodityEnsembleModel(model_type='voting', voting='soft')
    voting_model.fit(X, y, feature_names)
    
    # 交叉验证
    cv_results = voting_model.cross_validate(X, y, cv=5, use_time_series=True)
    print(f"\nVoting模型时序交叉验证:")
    print(f"  平均准确率: {cv_results['mean_accuracy']:.4f} ± {cv_results['std_accuracy']:.4f}")
    
    # 训练Stacking模型
    stacking_model = CommodityEnsembleModel(model_type='stacking')
    stacking_model.fit(X, y, feature_names)
    
    cv_results2 = stacking_model.cross_validate(X, y, cv=5, use_time_series=True)
    print(f"\nStacking模型时序交叉验证:")
    print(f"  平均准确率: {cv_results2['mean_accuracy']:.4f} ± {cv_results2['std_accuracy']:.4f}")
    
    # 特征重要性
    importance = voting_model.get_feature_importance(top_n=5)
    print(f"\nTop 5 重要特征:")
    print(importance.to_string(index=False))
