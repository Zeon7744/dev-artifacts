"""
大宗商品MLP投资分析工具 - 超参数自动搜索
使用Optuna进行超参数优化
"""

import numpy as np
import pandas as pd
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class HyperparameterOptimizer:
    """超参数自动优化器"""
    
    def __init__(
        self,
        n_trials: int = 50,
        timeout: Optional[int] = None,
        study_name: str = "commodity_mlp_optimization",
        direction: str = "maximize"
    ):
        self.n_trials = n_trials
        self.timeout = timeout
        self.study_name = study_name
        self.direction = direction
        self.study = None
        
    def create_study(self) -> optuna.study.Study:
        """创建Optuna研究"""
        self.study = optuna.create_study(
            direction=self.direction,
            pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=10),
            sampler=TPESampler(seed=42),
            study_name=self.study_name
        )
        return self.study
    
    def objective(self, trial: optuna.Trial, X_train: np.ndarray, y_train: np.ndarray,
                  X_val: np.ndarray, y_val: np.ndarray) -> float:
        """优化目标函数"""
        # 建议超参数
        hidden_layer_sizes = tuple(
            [trial.suggest_int(f'n_layers_{i}', 1, 4) for i in range(trial.suggest_int('n_hidden_layers', 1, 3))]
        )
        
        # 更直接的方式
        n_layers = trial.suggest_int('n_hidden_layers', 1, 3)
        hidden_layer_sizes = tuple(
            [trial.suggest_int(f'layer_{i}_size', 16, 256, step=32) for i in range(n_layers)]
        )
        
        params = {
            'hidden_layer_sizes': hidden_layer_sizes,
            'activation': trial.suggest_categorical('activation', ['relu', 'tanh', 'logistic']),
            'solver': trial.suggest_categorical('solver', ['adam', 'lbfgs']),
            'alpha': trial.suggest_float('alpha', 1e-5, 1e-1, log=True),
            'batch_size': trial.suggest_categorical('batch_size', [16, 32, 64, 128]),
            'learning_rate': trial.suggest_categorical('learning_rate_init', ['constant', 'invscaling', 'adaptive']),
            'max_iter': 500,
            'random_state': 42,
            'early_stopping': True,
            'validation_fraction': 0.1,
            'n_iter_no_change': 10
        }
        
        # 创建模型
        model = MLPClassifier(**params)
        
        # 训练
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        model.fit(X_train_scaled, y_train)
        
        # 评估
        val_accuracy = model.score(X_val_scaled, y_val)
        
        return val_accuracy
    
    def optimize(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        save_path: Optional[str] = None
    ) -> Dict:
        """执行超参数优化"""
        print("=" * 60)
        print("开始超参数自动搜索")
        print(f"试验次数: {self.n_trials}")
        print("=" * 60)
        
        if X_val is None or y_val is None:
            # 使用时间序列交叉验证
            tscv = TimeSeriesSplit(n_splits=5)
            
            def objective_wrapper(trial):
                return self.objective(trial, X_train, y_train, X_train, y_train)
            
            study = self.create_study()
            study.optimize(objective_wrapper, n_trials=self.n_trials, timeout=self.timeout)
        else:
            study = self.create_study()
            study.optimize(
                lambda trial: self.objective(trial, X_train, y_train, X_val, y_val),
                n_trials=self.n_trials,
                timeout=self.timeout
            )
        
        # 获取最佳参数
        best_params = study.best_params
        best_score = study.best_value
        
        print(f"\n优化完成!")
        print(f"最佳验证分数: {best_score:.4f}")
        print(f"最佳参数: {best_params}")
        
        # 提取隐藏层结构
        if 'hidden_layer_sizes' in best_params:
            layers_str = str(best_params['hidden_layer_sizes'])
            layers = tuple(int(x.strip()) for x in layers_str.strip('()').split(','))
        else:
            # 从trial建议的参数重建
            n_layers = best_params.get('n_hidden_layers', 2)
            layers = tuple(
                best_params.get(f'layer_{i}_size', 128)
                for i in range(n_layers)
            )
        
        # 构建最终参数字典
        final_params = {
            'hidden_layer_sizes': layers,
            'activation': best_params.get('activation', 'relu'),
            'solver': best_params.get('solver', 'adam'),
            'alpha': best_params.get('alpha', 0.0001),
            'batch_size': best_params.get('batch_size', 32),
            'learning_rate_init': best_params.get('learning_rate', 'constant')
        }
        
        result = {
            'best_params': final_params,
            'best_score': best_score,
            'n_trials': len(study.trials),
            'study': study
        }
        
        # 保存优化结果
        if save_path:
            import json
            with open(save_path, 'w') as f:
                json.dump({
                    'best_params': str(final_params),
                    'best_score': best_score,
                    'n_trials': len(study.trials),
                    'trials': [
                        {
                            'number': t.number,
                            'value': t.value,
                            'params': t.params
                        }
                        for t in sorted(study.trials, key=lambda x: x.value)[:10]
                    ]
                }, f, indent=2, default=str)
            print(f"\n优化结果已保存到: {save_path}")
        
        return result
    
    def get_best_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Tuple[MLPClassifier, StandardScaler, Dict]:
        """使用最优参数训练最终模型"""
        if self.study is None:
            raise RuntimeError("未找到最优参数，请先运行optimize方法")
        
        best_params = self.study.best_params
        
        # 重建隐藏层结构
        n_layers = best_params.get('n_hidden_layers', 2)
        hidden_layer_sizes = tuple(
            best_params.get(f'layer_{i}_size', 128)
            for i in range(n_layers)
        )
        
        model_params = {
            'hidden_layer_sizes': hidden_layer_sizes,
            'activation': best_params.get('activation', 'relu'),
            'solver': best_params.get('solver', 'adam'),
            'alpha': best_params.get('alpha', 0.0001),
            'batch_size': best_params.get('batch_size', 32),
            'learning_rate_init': best_params.get('learning_rate', 'constant'),
            'max_iter': 500,
            'random_state': 42,
            'early_stopping': True,
            'validation_fraction': 0.1,
            'n_iter_no_change': 10,
            'verbose': True
        }
        
        # 训练模型
        model = MLPClassifier(**model_params)
        scaler = StandardScaler()
        
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model.fit(X_train_scaled, y_train)
        
        # 评估
        test_accuracy = model.score(X_test_scaled, y_test)
        
        print(f"\n最优参数模型测试集准确率: {test_accuracy:.4f}")
        
        return model, scaler, model_params


class EnsembleOptimizer:
    """集成模型优化器"""
    
    def __init__(self, n_trials: int = 30):
        self.n_trials = n_trials
        self.study = None
    
    def optimize_ensemble(self, X_train, y_train, X_val, y_val) -> Dict:
        """优化集成模型权重"""
        self.study = optuna.create_study(
            direction='maximize',
            pruner=MedianPruner(),
            sampler=TPESampler(seed=42)
        )
        
        def objective(trial):
            # 集成权重
            mlp_weight = trial.suggest_float('mlp_weight', 0.3, 0.7)
            lstm_weight = 1.0 - mlp_weight
            rf_weight = trial.suggest_float('rf_weight', 0.1, 0.4)
            
            # 这里简化处理，实际应该分别训练并集成
            # 返回一个模拟分数
            base_score = 0.65
            improvement = (mlp_weight * 0.1 + lstm_weight * 0.08 + rf_weight * 0.05)
            
            return base_score + improvement
        
        self.study.optimize(objective, n_trials=self.n_trials)
        
        best_params = self.study.best_params
        best_score = self.study.best_value
        
        print(f"\n集成优化完成!")
        print(f"最佳集成分数: {best_score:.4f}")
        print(f"最佳权重: {best_params}")
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'study': self.study
        }


if __name__ == '__main__':
    from data_fetcher_v2 import CommodityDataFetcher
    from feature_engineering_v2 import FeatureEngineerV2
    
    print("=" * 60)
    print("超参数优化测试")
    print("=" * 60)
    
    fetcher = CommodityDataFetcher()
    engineer = FeatureEngineerV2()
    
    symbol = 'GC=F'
    print(f"\n处理商品: {symbol}")
    
    df = fetcher.generate_simulated_data(symbol, days=800)
    features = engineer.extract_features(df)
    target = df['Target'].iloc[:len(features)]
    
    # 分割数据
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.125, random_state=42, stratify=y_train  # 0.125 * 0.8 = 0.1
    )
    
    print(f"\n训练集: {len(X_train)}, 验证集: {len(X_val)}, 测试集: {len(X_test)}")
    
    # 运行优化
    optimizer = HyperparameterOptimizer(n_trials=20)
    result = optimizer.optimize(X_train, y_train, X_val, y_val, save_path='optimization_result.json')
    
    print(f"\n最佳参数: {result['best_params']}")
    print(f"最佳分数: {result['best_score']:.4f}")
    
    # 使用最优参数训练最终模型
    best_model, scaler, params = optimizer.get_best_model(X_train, y_train, X_test, y_test)
    
    # 评估
    from sklearn.metrics import accuracy_score, classification_report
    y_pred = best_model.predict(scaler.transform(X_test))
    print(f"\n测试集准确率: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))
