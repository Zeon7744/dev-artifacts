"""
大宗商品MLP投资分析工具 - v2超参数优化器
使用Optuna进行自动化超参数搜索
"""

import numpy as np
import pandas as pd
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
import warnings
warnings.filterwarnings('ignore')


class HyperparameterOptimizer:
    """超参数优化器"""
    
    def __init__(self, model_class, n_trials: int = 100, timeout: int = 3600):
        self.model_class = model_class
        self.n_trials = n_trials
        self.timeout = timeout
        self.study = None
        
    def _create_model(self, trial):
        """根据trial创建模型"""
        raise NotImplementedError
    
    def optimize(self, X_train, y_train, X_val, y_val) -> dict:
        """执行超参数优化"""
        self.study = optuna.create_study(
            direction="maximize",
            pruner=MedianPruner(),
            sampler=TPESampler(seed=42)
        )
        
        def objective(trial):
            # 创建模型
            model = self._create_model(trial)
            
            # 训练
            model.fit(X_train, y_train)
            
            # 验证
            y_pred = model.predict(X_val)
            y_prob = model.predict_proba(X_val) if hasattr(model, 'predict_proba') else y_pred
            
            # 评估指标
            acc = accuracy_score(y_val, y_pred)
            f1 = f1_score(y_val, y_pred, average='weighted')
            try:
                auc = roc_auc_score(y_val, y_prob)
            except:
                auc = 0.5
            
            # 综合得分
            score = 0.4 * acc + 0.3 * f1 + 0.3 * auc
            
            return score
        
        try:
            self.study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout)
        except Exception as e:
            print(f"优化过程异常: {e}")
        
        return self.study.best_params
    
    def get_best_model(self, X_train, y_train) -> object:
        """获取最佳模型"""
        if self.study is None:
            raise ValueError("请先运行optimize()方法")
        
        best_params = self.study.best_params
        model = self.model_class(**best_params)
        model.fit(X_train, y_train)
        
        return model
    
    def visualize_optimization(self):
        """可视化优化过程"""
        if self.study is None:
            raise ValueError("请先运行optimize()方法")
        
        fig1 = optuna.visualization.plot_optimization_history(self.study)
        fig2 = optuna.visualization.plot_param_importances(self.study)
        fig3 = optuna.visualization.plot_contour(self.study)
        
        return fig1, fig2, fig3


class MLPHyperparameterOptimizer(HyperparameterOptimizer):
    """MLP模型超参数优化器"""
    
    def __init__(self, n_trials: int = 50, timeout: int = 1800):
        from mlp_model_advanced import MLPModel
        super().__init__(model_class=MLPModel, n_trials=n_trials, timeout=timeout)
    
    def _create_model(self, trial):
        """创建MLP模型"""
        return MLPModel(
            input_size=trial.suggest_int('input_size', 10, 30),
            hidden_layers=trial.suggest_list('hidden_layers', [
                (64,),
                (128,),
                (64, 64),
                (128, 64),
                (256, 128, 64)
            ]),
            dropout=trial.suggest_float('dropout', 0.1, 0.5),
            learning_rate=trial.suggest_loguniform('learning_rate', 1e-4, 1e-2),
            epochs=trial.suggest_int('epochs', 50, 200),
            batch_size=trial.suggest_categorical('batch_size', [16, 32, 64, 128]),
            optimizer=trial.suggest_categorical('optimizer', ['adam', 'sgd', 'rmsprop']),
        )


class LSTMHyperparameterOptimizer(HyperparameterOptimizer):
    """LSTM模型超参数优化器"""
    
    def __init__(self, n_trials: int = 30, timeout: int = 1800):
        from lstm_model import CommodityLSTMModel
        super().__init__(model_class=CommodityLSTMModel, n_trials=n_trials, timeout=timeout)
    
    def _create_model(self, trial):
        """创建LSTM模型"""
        return CommodityLSTMModel(
            input_size=trial.suggest_int('input_size', 10, 30),
            hidden_size=trial.suggest_categorical('hidden_size', [32, 64, 128]),
            num_layers=trial.suggest_int('num_layers', 1, 3),
            dropout=trial.suggest_float('dropout', 0.1, 0.5),
            learning_rate=trial.suggest_loguniform('learning_rate', 1e-4, 1e-2),
            epochs=trial.suggest_int('epochs', 50, 200),
            batch_size=trial.suggest_categorical('batch_size', [16, 32, 64]),
        )


if __name__ == "__main__":
    # 测试
    print("超参数优化器初始化测试...")
    
    # 创建测试数据
    np.random.seed(42)
    X = np.random.randn(100, 15)
    y = np.random.randint(0, 2, 100)
    
    # 测试MLP优化器
    mlp_optimizer = MLPHyperparameterOptimizer(n_trials=5)
    best_params = mlp_optimizer.optimize(X[:80], y[:80], X[80:], y[80:])
    print(f"MLP最佳参数: {best_params}")
    
    # 测试LSTM优化器
    lstm_optimizer = LSTMHyperparameterOptimizer(n_trials=5)
    best_params = lstm_optimizer.optimize(X[:80], y[:80], X[80:], y[80:])
    print(f"LSTM最佳参数: {best_params}")
    
    print("\n✅ 超参数优化器测试完成")
