"""
大宗商品MLP投资分析工具 - 改进版特征工程
添加更多技术指标和市场情绪特征
"""

import numpy as np
import pandas as pd
from typing import List, Optional
import warnings
warnings.filterwarnings('ignore')

class FeatureEngineer:
    """特征工程类 - 增强版"""
    
    def __init__(self):
        self.feature_names = [
            # 收益率特征
            'Returns_1d', 'Returns_5d', 'Returns_10d', 'Returns_20d',
            # 移动平均线
            'MA_5', 'MA_10', 'MA_20', 'MA_50',
            'MA_5/M20', 'MA_5/M50', 'MA_10/M20',
            # RSI
            'RSI_14', 'RSI_7',
            # MACD
            'MACD', 'MACD_Signal', 'MACD_Histogram',
            # 布林带
            'Bollinger_Band_Width', 'Bollinger_Position',
            # ATR
            'ATR_14', 'ATR_7',
            # 成交量
            'Volume_Ratio_20', 'Volume_Ratio_5',
            # 价格位置
            'Price_Position_20', 'Price_Position_50',
            # 波动率
            'Volatility_10d', 'Volatility_20d',
            # 动量
            'ROC_10d', 'ROC_20d'
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
            'MA_50': close.rolling(window=50).mean(),
        })
        # MA偏离度
        df['MA_5/M20'] = df['MA_5'] / df['MA_20']
        df['MA_5/M50'] = df['MA_5'] / df['MA_50']
        df['MA_10/M20'] = df['MA_10'] / df['MA_20']
        return df
    
    def calculate_rsi(self, close: pd.Series, periods: List[int] = None) -> pd.DataFrame:
        """计算RSI指标"""
        if periods is None:
            periods = [7, 14]
        
        df = pd.DataFrame()
        for period in periods:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            df[f'RSI_{period}'] = rsi
        return df
    
    def calculate_macd(self, close: pd.Series) -> pd.DataFrame:
        """计算MACD指标"""
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        return pd.DataFrame({
            'MACD': macd,
            'MACD_Signal': signal,
            'MACD_Histogram': histogram
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
    
    def calculate_atr(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """计算平均真实波动范围"""
        if periods is None:
            periods = [7, 14]
        
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        df_result = pd.DataFrame()
        for period in periods:
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            df_result[f'ATR_{period}'] = atr
        return df_result
    
    def calculate_volume_ratio(self, volume: pd.Series, periods: List[int] = None) -> pd.DataFrame:
        """计算成交量比率"""
        if periods is None:
            periods = [5, 20]
        
        df = pd.DataFrame()
        for period in periods:
            vol_ma = volume.rolling(window=period).mean()
            df[f'Volume_Ratio_{period}'] = volume / vol_ma
        return df
    
    def calculate_price_position(self, close: pd.Series, periods: List[int] = None) -> pd.DataFrame:
        """计算价格在滚动窗口中的位置"""
        if periods is None:
            periods = [20, 50]
        
        df = pd.DataFrame()
        for period in periods:
            high_period = close.rolling(window=period).max()
            low_period = close.rolling(window=period).min()
            df[f'Price_Position_{period}'] = (close - low_period) / (high_period - low_period + 1e-10)
        return df
    
    def calculate_volatility(self, close: pd.Series, periods: List[int] = None) -> pd.DataFrame:
        """计算波动率"""
        if periods is None:
            periods = [10, 20]
        
        df = pd.DataFrame()
        returns = close.pct_change()
        for period in periods:
            df[f'Volatility_{period}d'] = returns.rolling(window=period).std()
        return df
    
    def calculate_roc(self, close: pd.Series, periods: List[int] = None) -> pd.DataFrame:
        """计算变动率（Rate of Change）"""
        if periods is None:
            periods = [10, 20]
        
        df = pd.DataFrame()
        for period in periods:
            df[f'ROC_{period}d'] = close.pct_change(period) * 100
        return df
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """从原始OHLCV数据提取所有特征"""
        close = df['Close']
        volume = df['Volume']
        
        # 计算各类特征
        returns_df = self.calculate_returns(close, [1, 5, 10, 20])
        ma_df = self.calculate_moving_averages(close)
        rsi_df = self.calculate_rsi(close)
        macd_df = self.calculate_macd(close)
        boll_df = self.calculate_bollinger(close)
        atr_df = self.calculate_atr(df)
        vol_ratio_df = self.calculate_volume_ratio(volume)
        price_pos_df = self.calculate_price_position(close)
        vol_df = self.calculate_volatility(close)
        roc_df = self.calculate_roc(close)
        
        # 合并所有特征
        features = pd.concat([
            returns_df,
            ma_df,
            rsi_df,
            macd_df,
            boll_df,
            atr_df,
            vol_ratio_df,
            price_pos_df,
            vol_df,
            roc_df
        ], axis=1)
        
        # 移除NaN值
        features = features.dropna()
        
        return features
    
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
    print(f"\n特征数量: {len(features.columns)}")
    print(f"\n特征名称:")
    for i, name in enumerate(features.columns.tolist(), 1):
        print(f"  {i}. {name}")
    
    print(f"\n特征统计:")
    print(features.describe().round(4))
    
    print(f"\n特征相关性矩阵 (Top 5 by variance):")
    variances = features.var().sort_values(ascending=False)
    top_vars = variances.head(5).index.tolist()
    print(features[top_vars].corr().round(3))
