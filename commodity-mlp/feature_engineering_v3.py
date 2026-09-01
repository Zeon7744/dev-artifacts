"""
大宗商品MLP投资分析工具 - v3特征工程
新增：动态波动率特征、动量指标、市场情绪特征
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class AdvancedFeatureEngineer:
    """高级特征工程器"""
    
    def __init__(self, lookback_windows: List[int] = [5, 10, 20, 30]):
        self.lookback_windows = lookback_windows
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成所有特征"""
        features = []
        
        # 基础价格特征
        features.extend(self._price_features(df))
        
        # 技术指标特征
        features.extend(self._technical_indicators(df))
        
        # 波动率特征
        features.extend(self._volatility_features(df))
        
        # 动量特征
        features.extend(self._momentum_features(df))
        
        # 市场情绪特征
        features.extend(self._sentiment_features(df))
        
        # 季节性特征
        features.extend(self._seasonal_features(df))
        
        return pd.concat(features, axis=1)
    
    def _price_features(self, df: pd.DataFrame) -> List[pd.Series]:
        """基础价格特征"""
        features = []
        
        # 价格对数收益率
        df['log_return'] = np.log(df['Close'] / df['Close'].shift(1))
        features.append(df['log_return'])
        
        # 多周期收益率
        for window in self.lookback_windows:
            df[f'return_{window}d'] = df['Close'].pct_change(window)
            features.append(df[f'return_{window}d'])
        
        # 价格位置（当前价格在历史区间的位置）
        for window in [20, 50]:
            high_window = df['High'].rolling(window).max()
            low_window = df['Low'].rolling(window).min()
            price_range = high_window - low_window
            df[f'price_position_{window}'] = (df['Close'] - low_window) / price_range.replace(0, 1)
            features.append(df[f'price_position_{window}'])
        
        return [f for f in features if f in df.columns]
    
    def _technical_indicators(self, df: pd.DataFrame) -> List[pd.Series]:
        """技术指标特征"""
        features = []
        
        # 移动平均线
        for window in [5, 10, 20, 50]:
            df[f'SMA_{window}'] = df['Close'].rolling(window).mean()
            df[f'EMA_{window}'] = df['Close'].ewm(span=window, adjust=False).mean()
            features.append(df[f'SMA_{window}'])
            features.append(df[f'EMA_{window}'])
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        features.extend([df['MACD'], df['MACD_signal'], df['MACD_histogram']])
        
        # RSI
        for period in [6, 14, 28]:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss.replace(0, 1e-10)
            df[f'RSI_{period}'] = 100 - (100 / (1 + rs))
            features.append(df[f'RSI_{period}'])
        
        # 布林带
        df['BB_middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_upper'] = df['BB_middle'] + 2 * bb_std
        df['BB_lower'] = df['BB_middle'] - 2 * bb_std
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
        df['BB_position'] = (df['Close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower']).replace(0, 1)
        features.extend([df['BB_middle'], df['BB_width'], df['BB_position']])
        
        # 成交量特征
        df['volume_sma'] = df['Volume'].rolling(20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_smi'].replace(0, 1)
        features.extend([df['volume_sma'], df['volume_ratio']])
        
        return [f for f in features if f in df.columns]
    
    def _volatility_features(self, df: pd.DataFrame) -> List[pd.Series]:
        """波动率特征"""
        features = []
        
        # 历史波动率
        for window in [5, 10, 20, 30]:
            df[f'hist_vol_{window}'] = df['log_return'].rolling(window).std() * np.sqrt(252)
            features.append(df[f'hist_vol_{window}'])
        
        # 波动率变化率
        df['vol_change'] = df['hist_vol_20'].diff(5) / df['hist_vol_20'].shift(5).replace(0, 1e-10)
        features.append(df['vol_change'])
        
        # 波动率区间位置
        df['vol_range_20'] = df['hist_vol_20']
        vol_high = df['hist_vol_20'].rolling(60).max()
        vol_low = df['hist_vol_20'].rolling(60).min()
        df['vol_position'] = (df['hist_vol_20'] - vol_low) / (vol_high - vol_low).replace(0, 1)
        features.extend([df['vol_range_20'], df['vol_position']])
        
        # 真实波幅 (ATR)
        df['tr1'] = df['High'] - df['Low']
        df['tr2'] = abs(df['High'] - df['Close'].shift(1))
        df['tr3'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['ATR_14'] = df['TR'].rolling(14).mean()
        df['ATR_ratio'] = df['ATR_14'] / df['Close']
        features.extend([df['ATR_14'], df['ATR_ratio']])
        
        return [f for f in features if f in df.columns]
    
    def _momentum_features(self, df: pd.DataFrame) -> List[pd.Series]:
        """动量特征"""
        features = []
        
        # 价格动量
        for window in [5, 10, 20]:
            df[f'momentum_{window}'] = df['Close'] / df['Close'].shift(window) - 1
            features.append(df[f'momentum_{window}'])
        
        # 成交量动量
        df['volume_momentum'] = df['Volume'] / df['Volume'].shift(5) - 1
        features.append(df['volume_momentum'])
        
        # ROC (变化率)
        for period in [5, 10, 20]:
            df[f'ROC_{period}'] = df['Close'].pct_change(period) * 100
            features.append(df[f'ROC_{period}'])
        
        return [f for f in features if f in df.columns]
    
    def _sentiment_features(self, df: pd.DataFrame) -> List[pd.Series]:
        """市场情绪特征"""
        features = []
        
        # 涨跌天数统计
        df['daily_direction'] = (df['Close'] > df['Close'].shift(1)).astype(int)
        df['up_days_5'] = df['daily_direction'].rolling(5).sum()
        df['up_ratio_5'] = df['up_days_5'] / 5
        features.extend([df['up_days_5'], df['up_ratio_5']])
        
        # 连续涨跌天数
        df['consecutive_up'] = 0
        df['consecutive_down'] = 0
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                df.loc[df.index[i], 'consecutive_up'] = df['consecutive_up'].iloc[i-1] + 1
                df.loc[df.index[i], 'consecutive_down'] = 0
            else:
                df.loc[df.index[i], 'consecutive_down'] = df['consecutive_down'].iloc[i-1] + 1
                df.loc[df.index[i], 'consecutive_up'] = 0
        features.extend([df['consecutive_up'], df['consecutive_down']])
        
        # 大单流向（假设成交量突增为大单）
        df['volume_zscore'] = (df['Volume'] - df['Volume'].rolling(20).mean()) / df['Volume'].rolling(20).std().replace(0, 1e-10)
        df['large_buy'] = ((df['volume_zscore'] > 1.5) & (df['Close'] > df['Open'])).astype(int)
        df['large_sell'] = ((df['volume_zscore'] > 1.5) & (df['Close'] < df['Open'])).astype(int)
        df['net_flow_5'] = df['large_buy'].rolling(5).sum() - df['large_sell'].rolling(5).sum()
        features.extend([df['volume_zscore'], df['net_flow_5']])
        
        return [f for f in features if f in df.columns]
    
    def _seasonal_features(self, df: pd.DataFrame) -> List[pd.Series]:
        """季节性特征"""
        features = []
        
        # 日期特征
        df['day_of_week'] = pd.to_datetime(df['Date']).dt.dayofweek
        df['month'] = pd.to_datetime(df['Date']).dt.month
        df['quarter'] = pd.to_datetime(df['Date']).dt.quarter
        
        # 月份效应
        df['month_effect'] = df.groupby('month')['log_return'].transform('mean')
        features.extend([df['day_of_week'], df['month'], df['quarter'], df['month_effect']])
        
        # 周末效应
        df['weekend_effect'] = df['day_of_week'].isin([4, 5]).astype(int)
        features.append(df['weekend_effect'])
        
        return [f for f in features if f in df.columns]
    
    def prepare_targets(self, df: pd.DataFrame, forward_days: int = 5) -> pd.Series:
        """准备目标变量（未来涨跌）"""
        # 未来收益率
        df['future_return'] = df['Close'].shift(-forward_days) / df['Close'] - 1
        
        # 分类标签（上涨为1，下跌为0）
        df['target'] = (df['future_return'] > 0).astype(int)
        
        return df['target'].dropna()
    
    def get_feature_names(self) -> List[str]:
        """获取所有特征名称"""
        return [
            'log_return', 'return_5d', 'return_10d', 'return_20d', 'return_30d',
            'price_position_20', 'price_position_50',
            'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
            'EMA_5', 'EMA_10', 'EMA_20', 'EMA_50',
            'MACD', 'MACD_signal', 'MACD_histogram',
            'RSI_6', 'RSI_14', 'RSI_28',
            'BB_middle', 'BB_width', 'BB_position',
            'volume_sma', 'volume_ratio',
            'hist_vol_5', 'hist_vol_10', 'hist_vol_20', 'hist_vol_30',
            'vol_change', 'vol_position',
            'ATR_14', 'ATR_ratio',
            'momentum_5', 'momentum_10', 'momentum_20',
            'volume_momentum',
            'ROC_5', 'ROC_10', 'ROC_20',
            'up_days_5', 'up_ratio_5',
            'consecutive_up', 'consecutive_down',
            'volume_zscore', 'net_flow_5',
            'day_of_week', 'month', 'quarter', 'month_effect', 'weekend_effect'
        ]


if __name__ == "__main__":
    # 测试
    df = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=100, freq='B'),
        'Open': np.random.randn(100).cumsum() + 100,
        'High': np.random.randn(100).cumsum() + 101,
        'Low': np.random.randn(100).cumsum() + 99,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(100000, 1000000, 100)
    })
    
    engineer = AdvancedFeatureEngineer()
    features = engineer.engineer_features(df)
    targets = engineer.prepare_targets(df)
    
    print(f"特征数量: {len(features.columns)}")
    print(f"特征列: {features.columns.tolist()}")
    print(f"有效样本数: {len(targets)}")
