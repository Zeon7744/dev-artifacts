"""
大宗商品MLP投资分析工具 - LSTM时序模型
使用PyTorch实现LSTM进行价格预测
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class CommodityDataset(Dataset):
    """商品时间序列数据集"""
    
    def __init__(self, features: np.ndarray, targets: np.ndarray, sequence_length: int = 20):
        self.features = features
        self.targets = targets
        self.sequence_length = sequence_length
        
    def __len__(self):
        return len(self.features) - self.sequence_length
    
    def __getitem__(self, idx):
        x = self.features[idx:idx + self.sequence_length]
        y = self.targets[idx + self.sequence_length - 1]
        return torch.FloatTensor(x), torch.FloatTensor([y])


class LSTMModel(nn.Module):
    """LSTM时序预测模型"""
    
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, 
                 dropout: float = 0.3, output_dropout: float = 0.5):
        super(LSTMModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        self.dropout = nn.Dropout(output_dropout)
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        # x: (batch, seq_len, features)
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # 取最后一个时间步的输出
        last_output = lstm_out[:, -1, :]
        
        out = self.dropout(last_output)
        out = self.relu(self.fc1(out))
        out = self.sigmoid(self.fc2(out))
        
        return out.squeeze(-1)


class CommodityLSTMModel:
    """商品LSTM预测模型封装"""
    
    def __init__(
        self,
        input_size: int = 15,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.3,
        sequence_length: int = 20,
        learning_rate: float = 0.001,
        epochs: int = 100,
        batch_size: int = 32,
        device: str = 'cpu'
    ):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.sequence_length = sequence_length
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.device = device
        
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names: Optional[List[str]] = None
        self.trained = False
        self.training_history = []
        
    def train(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        test_size: float = 0.2,
        val_size: float = 0.1
    ) -> Dict[str, float]:
        """训练LSTM模型"""
        self.feature_names = features.columns.tolist()
        
        X = features.values
        y = target.values
        
        # 分割数据
        n_samples = len(X)
        test_size_actual = int(n_samples * test_size)
        val_size_actual = int((n_samples - test_size_actual) * val_size / (1 - val_size))
        
        X_train = X[:n_samples - test_size_actual - val_size_actual]
        y_train = y[:n_samples - test_size_actual - val_size_actual]
        X_val = X[n_samples - test_size_actual - val_size_actual:n_samples - test_size_actual]
        y_val = y[n_samples - test_size_actual - val_size_actual:n_samples - test_size_actual]
        X_test = X[n_samples - test_size_actual:]
        y_test = y[n_samples - test_size_actual:]
        
        # 标准化
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 创建数据集
        train_dataset = CommodityDataset(X_train_scaled, y_train, self.sequence_length)
        val_dataset = CommodityDataset(X_val_scaled, y_val, self.sequence_length)
        test_dataset = CommodityDataset(X_test_scaled, y_test, self.sequence_length)
        
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)
        test_loader = DataLoader(test_dataset, batch_size=self.batch_size, shuffle=False)
        
        # 初始化模型
        self.model = LSTMModel(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout
        ).to(self.device)
        
        # 损失函数和优化器
        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
        
        print("=" * 60)
        print("开始训练LSTM模型...")
        print(f"训练样本: {len(train_dataset)}, 验证样本: {len(val_dataset)}, 测试样本: {len(test_dataset)}")
        print(f"序列长度: {self.sequence_length}")
        print("=" * 60)
        
        best_val_loss = float('inf')
        patience = 15
        patience_counter = 0
        
        for epoch in range(self.epochs):
            # 训练阶段
            self.model.train()
            train_loss = 0
            for X_batch, y_batch in train_loader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                
                optimizer.zero_grad()
                output = self.model(X_batch)
                loss = criterion(output, y_batch.squeeze(-1))
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            
            # 验证阶段
            self.model.eval()
            val_loss = 0
            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                    output = self.model(X_batch)
                    loss = criterion(output, y_batch.squeeze(-1))
                    val_loss += loss.item()
            
            val_loss /= len(val_loader)
            scheduler.step(val_loss)
            
            self.training_history.append({
                'epoch': epoch + 1,
                'train_loss': train_loss,
                'val_loss': val_loss
            })
            
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"Epoch [{epoch+1}/{self.epochs}] Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            
            # 早停
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_model_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"早停触发，最佳验证损失: {best_val_loss:.4f}")
                    break
        
        # 加载最佳模型
        if 'best_model_state' in locals():
            self.model.load_state_dict(best_model_state)
        
        # 测试评估
        self.model.eval()
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for X_batch, y_batch in test_loader:
                X_batch = X_batch.to(self.device)
                output = self.model(X_batch)
                all_preds.extend(output.cpu().numpy())
                all_targets.extend(y_batch.numpy())
        
        all_preds = np.array(all_preds)
        all_targets = np.array(all_targets)
        
        # 计算指标
        binary_preds = (all_preds > 0.5).astype(int)
        
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        accuracy = accuracy_score(all_targets, binary_preds)
        precision = precision_score(all_targets, binary_preds, zero_division=0)
        recall = recall_score(all_targets, binary_preds, zero_division=0)
        f1 = f1_score(all_targets, binary_preds, zero_division=0)
        
        metrics = {
            'test_accuracy': accuracy,
            'test_precision': precision,
            'test_recall': recall,
            'test_f1': f1,
            'best_val_loss': best_val_loss
        }
        
        print(f"\n训练完成!")
        print(f"测试集准确率: {accuracy:.4f}")
        print(f"测试集精确率: {precision:.4f}")
        print(f"测试集召回率: {recall:.4f}")
        print(f"测试集F1分数: {f1:.4f}")
        print(f"最佳验证损失: {best_val_loss:.4f}")
        
        self.trained = True
        return metrics
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """预测投资方向"""
        if not self.trained or self.model is None:
            raise RuntimeError("模型尚未训练，请先调用train方法")
        
        X = self.scaler.transform(features.values)
        X = X.reshape(-1, self.sequence_length, self.input_size)
        
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            output = self.model(X_tensor)
            return (output.cpu().numpy() > 0.5).astype(int)
    
    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if not self.trained or self.model is None:
            raise RuntimeError("模型尚未训练")
        
        X = self.scaler.transform(features.values)
        X = X.reshape(-1, self.sequence_length, self.input_size)
        
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            output = self.model(X_tensor)
            return output.cpu().numpy()
    
    def get_importance(self) -> Dict[str, float]:
        """获取特征重要性（基于LSTM权重）"""
        if not self.trained or self.model is None:
            raise RuntimeError("模型尚未训练")
        
        # 计算输入层权重的绝对值之和
        importance = {}
        for i, name in enumerate(self.feature_names):
            if i < self.input_size:
                weight = self.model.lstm.weight_ih_l0[:, i].abs().sum().item()
                importance[name] = weight
        
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    def save_model(self, path: str):
        """保存模型"""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'model_state': self.model.state_dict(),
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'trained': self.trained,
            'training_history': self.training_history
        }, path)
        print(f"模型已保存到: {path}")
    
    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model = LSTMModel(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout
        ).to(self.device)
        self.model.load_state_dict(checkpoint['model_state'])
        self.scaler = checkpoint['scaler']
        self.feature_names = checkpoint['feature_names']
        self.trained = checkpoint['trained']
        self.training_history = checkpoint.get('training_history', [])
        print(f"模型已从 {path} 加载")


if __name__ == '__main__':
    from data_fetcher_v2 import CommodityDataFetcher
    from feature_engineering_v2 import FeatureEngineerV2
    
    print("=" * 60)
    print("LSTM模型测试")
    print("=" * 60)
    
    fetcher = CommodityDataFetcher()
    engineer = FeatureEngineerV2()
    
    symbol = 'GC=F'
    print(f"\n处理商品: {symbol}")
    
    df = fetcher.generate_simulated_data(symbol, days=800)
    features = engineer.extract_features(df)
    target = df['Target'].iloc[:len(features)]
    
    print(f"特征矩阵形状: {features.shape}")
    
    # 训练LSTM
    lstm_model = CommodityLSTMModel(
        input_size=features.shape[1],
        hidden_size=64,
        num_layers=2,
        epochs=50,
        batch_size=32
    )
    
    metrics = lstm_model.train(features, target)
    
    # 预测
    predictions = lstm_model.predict(features.head(20))
    probabilities = lstm_model.predict_proba(features.head(20))
    
    print(f"\n预测结果: {predictions}")
    print(f"预测概率: {probabilities.round(3)}")
    
    # 特征重要性
    importance = lstm_model.get_importance()
    print(f"\n特征重要性Top5:")
    for i, (feat, imp) in enumerate(list(importance.items())[:5], 1):
        print(f"  {i}. {feat}: {imp:.4f}")
