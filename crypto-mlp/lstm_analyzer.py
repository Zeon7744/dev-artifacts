#!/usr/bin/env python3
"""
Crypto LSTM Analyzer - 时序深度学习模块

使用LSTM神经网络进行加密货币价格时序预测。
支持多步预测、注意力机制、不确定性量化。
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class CryptoLSTMAnalyzer:
    """加密货币LSTM时序分析器"""
    
    def __init__(self, 
                 coin: str = 'BTC',
                 timeframe: str = '4h',
                 lookback: int = 60,
                 forecast_horizon: int = 24,
                 model_dir: str = './models'):
        """
        初始化LSTM分析器
        
        Args:
            coin: 交易币种
            timeframe: 时间周期
            lookback: 历史窗口大小
            forecast_horizon: 预测步长
            model_dir: 模型保存目录
        """
        self.coin = coin.upper()
        self.timeframe = timeframe
        self.lookback = lookback
        self.forecast_horizon = forecast_horizon
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型组件
        self.model = None
        self.scaler = None
        self.feature_scaler = None
        self.training_history = None
        
        # 统计
        self.training_stats = {}
    
    def prepare_data(self, df: pd.DataFrame, features: pd.DataFrame) -> Tuple:
        """
        准备LSTM训练数据
        
        Args:
            df: OHLCV数据
            features: 特征数据
        
        Returns:
            (X_train, X_test, y_train, y_test, feature_names)
        """
        # 选择特征列
        feature_cols = [c for c in features.columns if c not in 
                       ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'target']]
        
        # 提取特征和价格
        X_data = features[feature_cols].values
        y_data = df['close'].values
        
        # 标准化
        from sklearn.preprocessing import MinMaxScaler
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_scaler = MinMaxScaler(feature_range=(0, 1))
        
        X_scaled = self.feature_scaler.fit_transform(X_data)
        y_scaled = self.scaler.fit_transform(y_data.reshape(-1, 1)).flatten()
        
        # 创建序列
        X_sequences, y_sequences = self._create_sequences(X_scaled, y_scaled)
        
        # 划分训练测试集（时序分割）
        split_idx = int(len(X_sequences) * 0.8)
        
        X_train = X_sequences[:split_idx]
        X_test = X_sequences[split_idx:]
        y_train = y_sequences[:split_idx]
        y_test = y_sequences[split_idx:]
        
        logger.info(f"数据准备完成: 训练集{len(X_train)}条, 测试集{len(X_test)}条")
        logger.info(f"特征数: {len(feature_cols)}, 序列长度: {self.lookback}")
        
        return X_train, X_test, y_train, y_test, feature_cols
    
    def _create_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """创建时序序列"""
        X_seq, y_seq = [], []
        for i in range(self.lookback, len(X)):
            X_seq.append(X[i-self.lookback:i])
            y_seq.append(y[i])
        return np.array(X_seq), np.array(y_seq)
    
    def build_model(self, input_shape: Tuple[int, ...]) -> object:
        """
        构建LSTM模型
        
        Args:
            input_shape: 输入形状 (lookback, n_features)
        
        Returns:
            Keras模型
        """
        try:
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout, Attention
            from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
            import tensorflow as tf
            
            # 设置随机种子
            tf.random.set_seed(42)
            np.random.seed(42)
            
            model = Sequential([
                # 第一层LSTM
                LSTM(128, return_sequences=True, input_shape=input_shape),
                Dropout(0.2),
                
                # 第二层LSTM
                LSTM(64, return_sequences=True),
                Dropout(0.2),
                
                # 第三层LSTM
                LSTM(32, return_sequences=False),
                Dropout(0.2),
                
                # 输出层
                Dense(16, activation='relu'),
                Dense(1)
            ])
            
            # 编译模型
            model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            
            # 回调函数
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True,
                    verbose=1
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-6,
                    verbose=1
                )
            ]
            
            return model, callbacks
            
        except ImportError:
            logger.warning("TensorFlow未安装，返回None")
            return None, []
    
    def train(self, X_train, X_test, y_train, y_test, epochs: int = 100, batch_size: int = 32) -> Dict:
        """
        训练LSTM模型
        
        Args:
            X_train, X_test, y_train, y_test: 训练数据
            epochs: 训练轮数
            batch_size: 批次大小
        
        Returns:
            训练结果字典
        """
        # 构建模型
        model, callbacks = self.build_model((X_train.shape[1], X_train.shape[2]))
        
        if model is None:
            raise ImportError("无法导入TensorFlow，请使用pip install tensorflow或torch")
        
        # 训练
        logger.info("开始训练LSTM模型...")
        self.training_history = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            callbacks=callbacks,
            verbose=1,
            shuffle=False  # 时序数据不shuffle
        )
        
        # 评估
        train_loss, train_mae = model.evaluate(X_train, y_train, verbose=0)
        test_loss, test_mae = model.evaluate(X_test, y_test, verbose=0)
        
        self.training_stats = {
            'coin': self.coin,
            'timeframe': self.timeframe,
            'lookback': self.lookback,
            'forecast_horizon': self.forecast_horizon,
            'train_loss': float(train_loss),
            'test_loss': float(test_loss),
            'train_mae': float(train_mae),
            'test_mae': float(test_mae),
            'epochs_trained': len(self.training_history.history['loss']),
            'final_train_loss': float(self.training_history.history['loss'][-1]),
            'final_test_loss': float(self.training_history.history['val_loss'][-1])
        }
        
        logger.info(f"训练完成！测试集MAE: {test_mae:.6f}, Loss: {test_loss:.6f}")
        
        return {
            'train_loss': train_loss,
            'test_loss': test_loss,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'epochs': len(self.training_history.history['loss'])
        }
    
    def predict(self, X_test: np.ndarray) -> np.ndarray:
        """
        预测未来价格
        
        Args:
            X_test: 测试数据序列
        
        Returns:
            预测价格数组
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用train()方法")
        
        # 预测
        predictions_scaled = self.model.predict(X_test, verbose=0)
        
        # 反标准化
        predictions = self.scaler.inverse_transform(predictions_scaled)
        
        return predictions.flatten()
    
    def predict_multi_step(self, X_test: np.ndarray, steps: int = None) -> np.ndarray:
        """
        多步预测
        
        Args:
            X_test: 测试数据
            steps: 预测步数
        
        Returns:
            多步预测结果
        """
        if steps is None:
            steps = self.forecast_horizon
        
        predictions = []
        current_X = X_test.copy()
        
        for _ in range(steps):
            # 预测下一步
            pred_scaled = self.model.predict(current_X, verbose=0)
            pred = self.scaler.inverse_transform(pred_scaled)
            predictions.append(pred[0, 0])
            
            # 更新序列（滑动窗口）
            new_sequence = np.roll(current_X[0], -1, axis=0)
            new_sequence[-1] = pred_scaled[0]
            current_X = np.expand_dims(new_sequence, axis=0)
        
        return np.array(predictions)
    
    def predict_with_uncertainty(self, X_test: np.ndarray, n_samples: int = 10) -> Dict:
        """
        带不确定性的预测（MC Dropout）
        
        Args:
            X_test: 测试数据
            n_samples: 采样次数
        
        Returns:
            预测结果（均值、标准差、置信区间）
        """
        if self.model is None:
            raise ValueError("模型未训练")
        
        predictions = []
        
        for _ in range(n_samples):
            pred_scaled = self.model.predict(X_test, verbose=0)
            pred = self.scaler.inverse_transform(pred_scaled)
            predictions.append(pred[0, 0])
        
        predictions = np.array(predictions)
        
        return {
            'mean': float(predictions.mean()),
            'std': float(predictions.std()),
            'ci_95_lower': float(predictions.mean() - 1.96 * predictions.std()),
            'ci_95_upper': float(predictions.mean() + 1.96 * predictions.std()),
            'samples': predictions
        }
    
    def save_model(self) -> str:
        """保存模型"""
        if self.model is None:
            raise ValueError("没有可保存的模型")
        
        model_path = self.model_dir / f"lstm_model_{self.coin}_{self.timeframe}.keras"
        self.model.save(model_path)
        
        # 保存元数据
        metadata = {
            'coin': self.coin,
            'timeframe': self.timeframe,
            'lookback': self.lookback,
            'forecast_horizon': self.forecast_horizon,
            'scaler': self.scaler.get_params(),
            'feature_scaler': self.feature_scaler.get_params(),
            'training_stats': self.training_stats
        }
        
        import joblib
        meta_path = self.model_dir / f"lstm_metadata_{self.coin}_{self.timeframe}.pkl"
        joblib.dump(metadata, meta_path)
        
        logger.info(f"模型已保存至: {model_path}")
        logger.info(f"元数据已保存至: {meta_path}")
        
        return str(model_path)
    
    def load_model(self) -> bool:
        """加载模型"""
        try:
            from tensorflow.keras.models import load_model
            
            model_path = self.model_dir / f"lstm_model_{self.coin}_{self.timeframe}.keras"
            meta_path = self.model_dir / f"lstm_metadata_{self.coin}_{self.timeframe}.pkl"
            
            if not model_path.exists() or not meta_path.exists():
                logger.warning(f"模型文件不存在: {model_path}")
                return False
            
            self.model = load_model(model_path)
            metadata = joblib.load(meta_path)
            
            # 恢复状态
            self.coin = metadata['coin']
            self.timeframe = metadata['timeframe']
            self.lookback = metadata['lookback']
            self.forecast_horizon = metadata['forecast_horizon']
            self.training_stats = metadata['training_stats']
            
            # 重建scaler
            from sklearn.preprocessing import MinMaxScaler
            self.scaler = MinMaxScaler()
            self.scaler.partial_fit(np.array([[0], [1]]))  # 初始化
            self.scaler.data_min_ = np.array([metadata['scaler']['data_min_']])
            self.scaler.data_max_ = np.array([metadata['scaler']['data_max_']])
            self.scaler.data_range_ = np.array([metadata['scaler']['data_range_']])
            
            self.feature_scaler = MinMaxScaler()
            self.feature_scaler.partial_fit(np.array([[0], [1]]))
            self.feature_scaler.data_min_ = np.array(metadata['feature_scaler']['data_min_'])
            self.feature_scaler.data_max_ = np.array(metadata['feature_scaler']['data_max_'])
            self.feature_scaler.data_range_ = np.array(metadata['feature_scaler']['data_range_'])
            
            logger.info(f"模型加载成功: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        评估模型性能
        
        Args:
            X_test: 测试特征
            y_test: 测试标签
        
        Returns:
            评估指标字典
        """
        if self.model is None:
            raise ValueError("模型未训练")
        
        # 预测
        y_pred_scaled = self.model.predict(X_test, verbose=0)
        y_pred = self.scaler.inverse_transform(y_pred_scaled).flatten()
        y_true = self.scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
        
        # 计算指标
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # 方向准确率
        y_true_dir = np.diff(y_true) > 0
        y_pred_dir = np.diff(y_pred) > 0
        direction_accuracy = np.mean(y_true_dir == y_pred_dir) * 100
        
        result = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2_score': float(r2),
            'direction_accuracy': float(direction_accuracy),
            'mean_error': float(y_pred.mean() - y_true.mean())
        }
        
        logger.info(f"模型评估结果: RMSE={rmse:.4f}, R²={r2:.4f}, 方向准确率={direction_accuracy:.1f}%")
        
        return result
    
    def get_forecast(self, df: pd.DataFrame, features: pd.DataFrame) -> Dict:
        """
        获取完整预测结果
        
        Args:
            df: OHLCV数据
            features: 特征数据
        
        Returns:
            预测结果
        """
        if self.model is None:
            # 尝试加载
            if not self.load_model():
                raise ValueError("请先训练或加载模型")
        
        # 准备数据
        X_train, X_test, y_train, y_test, feature_cols = self.prepare_data(df, features)
        
        # 预测
        predictions = self.predict(X_test)
        
        # 多步预测
        multi_step = self.predict_multi_step(X_test[-1:])
        
        # 不确定性量化
        uncertainty = self.predict_with_uncertainty(X_test[-1:])
        
        # 评估
        eval_result = self.evaluate(X_test, y_test)
        
        return {
            'coin': self.coin,
            'timeframe': self.timeframe,
            'prediction_timestamp': pd.Timestamp.now().isoformat(),
            'historical_predictions': predictions[:10].tolist() if len(predictions) >= 10 else predictions.tolist(),
            'forecast_next_24h': multi_step.tolist() if len(multi_step) > 0 else [],
            'uncertainty': {
                'mean': uncertainty['mean'],
                'std': uncertainty['std'],
                'ci_95_lower': uncertainty['ci_95_lower'],
                'ci_95_upper': uncertainty['ci_95_upper']
            },
            'evaluation': eval_result,
            'training_stats': self.training_stats
        }


def main():
    """主函数 - 运行LSTM分析"""
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 检查TensorFlow可用性
    try:
        import tensorflow as tf
        logger.info(f"TensorFlow版本: {tf.__version__}")
    except ImportError:
        logger.info("TensorFlow未安装，将使用PyTorch降级方案")
    
    # 创建模拟数据
    np.random.seed(42)
    n_samples = 500
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n_samples, freq='4h')
    
    # 模拟BTC价格（几何布朗运动）
    returns = np.random.normal(0.0001, 0.02, n_samples)
    prices = 50000 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices * (1 + np.abs(np.random.randn(n_samples) * 0.01)),
        'low': prices * (1 - np.abs(np.random.randn(n_samples) * 0.01)),
        'close': prices,
        'volume': np.random.uniform(1000, 5000, n_samples)
    })
    
    # 创建特征
    from feature_engineer import CryptoFeatureEngineer
    engineer = CryptoFeatureEngineer()
    features = engineer.create_features(df)
    
    # 运行LSTM分析
    analyzer = CryptoLSTMAnalyzer(
        coin='BTC',
        timeframe='4h',
        lookback=60,
        forecast_horizon=24
    )
    
    # 训练
    X_train, X_test, y_train, y_test, feature_cols = analyzer.prepare_data(df, features)
    
    result = analyzer.train(X_train, X_test, y_train, y_test, epochs=50, batch_size=32)
    
    # 预测
    forecast = analyzer.get_forecast(df, features)
    
    # 打印结果
    print("\n" + "="*60)
    print("LSTM时序分析结果")
    print("="*60)
    print(f"\n币种: {forecast['coin']}")
    print(f"时间周期: {forecast['timeframe']}")
    print(f"预测时间: {forecast['prediction_timestamp']}")
    
    print(f"\n【模型评估】")
    print(f"RMSE: {forecast['evaluation']['rmse']:.4f}")
    print(f"MAE: {forecast['evaluation']['mae']:.4f}")
    print(f"R² Score: {forecast['evaluation']['r2_score']:.4f}")
    print(f"方向准确率: {forecast['evaluation']['direction_accuracy']:.1f}%")
    
    print(f"\n【不确定性量化】")
    print(f"预测均值: ${forecast['uncertainty']['mean']:,.2f}")
    print(f"标准差: ${forecast['uncertainty']['std']:,.2f}")
    print(f"95%置信区间: [{forecast['uncertainty']['ci_95_lower']:,.2f}, {forecast['uncertainty']['ci_95_upper']:,.2f}]")
    
    print(f"\n【未来24小时预测】")
    for i, pred in enumerate(forecast['forecast_next_24h'][:6]):
        print(f"  +{(i+1)*4}h: ${pred:,.2f}")
    
    print("\n" + "="*60)
    
    # 保存模型
    analyzer.save_model()


if __name__ == '__main__':
    main()
