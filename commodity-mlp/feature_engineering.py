"""
大宗商品MLP投资分析工具 - 特征工程模块
计算13个技术指标作为MLP输入特征
"""

import numpy as np
import pandas as pd
from typing import List, Optional
import warnings
warnings.filterwarnings('ignore')

class FeatureEngineer:
    """特征工程类"""
    
    def __init__(self):
        self.feature_names = [
            'Returns_1d', 'Returns_5d', 'Returns_10d',
            'MA_5', 'MA_10', 'MA_20',
            'RSI_14', 'MACD', 'MACD_Signal',
            'Bollinger_Band_Width', 'Bollinger_Position',
            'ATR_14', 'Volume_Ratio'
        ]
    
    def calculate_returns(self, close: pd.Series, periods: List[int]) -> pd.DataFrame:
        """计算不同周期的收益率"""
        df = pd.DataFrame()
        for period in periods:
            df[f'Returns_{period}d'] = close.pct_change(period)
        return df
    
    def calculate_moving_averages(self, close: pd.Series) -> pd.DataFrame:
        """计算移动平均线"""
        df = pd.DataFrame({
            'MA_5': close.rolling(window=5).mean(),
            'MA_10': close.rolling(window=10).mean(),
            'MA_20': close.rolling(window=20).mean(),
        })
        # MA偏离度
        df['MA_5/M20'] = df['MA_5'] / df['MA_20']
        df['MA_10/M20'] = df['MA_10'] / df['MA_20']
        return df
    
    def calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, close: pd.Series) -> pd.DataFrame:
        """计算MACD指标"""
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        return pd.DataFrame({
            'MACD': macd,
            'MACD_Signal': signal
        })
    
    def calculate_bollinger(self, close: pd.Series, window: int = 20, num_std: float = 2) -> pd.DataFrame:
        """计算布林带"""
        ma = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        
        upper = ma + num_std * std
        lower = ma - num_std * std
        
        band_width = (upper - lower) / ma
        position = (close - lower) / (upper - lower)
        
        return pd.DataFrame({
            'Bollinger_Band_Width': band_width,
            'Bollinger_Position': position
        })
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算平均真实波动范围"""
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def calculate_volume_ratio(self, volume: pd.Series, period: int = 20) -> pd.Series:
        """计算成交量比率"""
        vol_ma = volume.rolling(window=period).mean()
        return volume / vol_ma
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """从原始OHLCV数据提取所有特征"""
        close = df['Close']
        volume = df['Volume']
        
        # 计算各类特征
        returns_df = self.calculate_returns(close, [1, 5, 10])
        ma_df = self.calculate_moving_averages(close)
        rsi = self.calculate_rsi(close)
        macd_df = self.calculate_macd(close)
        boll_df = self.calculate_bollinger(close)
        atr = self.calculate_atr(df)
        vol_ratio = self.calculate_volume_ratio(volume)
        
        # 合并所有特征
        features = pd.concat([
            returns_df,
            ma_df,
            rsi.rename('RSI_14'),
            macd_df,
            boll_df,
            atr.rename('ATR_14'),
            vol_ratio.rename('Volume_Ratio')
        ], axis=1)
        
        return features.dropna()
    
    def get_feature_names(self) -> List[str]:
        """获取特征名称列表"""
        return self.feature_names


if __name__ == '__main__':
    # 测试特征工程
    from data_fetcher import CommodityDataFetcher
    
    fetcher = CommodityDataFetcher()
    df = fetcher.generate_simulated_data('GC=F', days=500)
    
    engineer = FeatureEngineer()
    features = engineer.extract_features(df)
    
    print(f"特征矩阵形状: {features.shape}")
    print(f"\n特征名称:")
    for i, name in enumerate(engineer.get_feature_names(), 1):
        print(f"  {i}. {name}")
    
    print(f"\n特征统计:")
    print(features.describe().round(4))
    
    print(f"\n特征相关性矩阵 (前5个):")
    print(features.corr().head(5).round(3))
