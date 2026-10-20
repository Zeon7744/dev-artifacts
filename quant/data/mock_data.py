"""
模拟数据连接器

生成模拟市场数据，用于测试和演示
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base import DataConnector


class MockDataConnector(DataConnector):
    """
    模拟数据连接器
    
    生成各种模式的模拟数据用于策略测试。
    
    参数:
        trend (str): 趋势类型 'up'/'down'/'sideways'/'mixed'
        volatility (float): 波动率，默认 0.02
        noise_level (float): 噪声级别，默认 0.1
    """
    
    def __init__(self, trend: str = 'mixed', volatility: float = 0.02,
                 noise_level: float = 0.1, seed: Optional[int] = None):
        self.trend = trend
        self.volatility = volatility
        self.noise_level = noise_level
        self.seed = seed
    
    @property
    def name(self) -> str:
        return "模拟数据"
    
    def fetch_data(self, symbol: str = 'MOCK',
                   start_date: str = '2023-01-01',
                   end_date: str = '2024-01-01',
                   interval: str = 'daily') -> pd.DataFrame:
        """生成模拟市场数据"""
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        n = len(dates)
        
        if self.seed is not None:
            np.random.seed(self.seed)
        
        # 基础价格
        initial_price = 100.0
        prices = self._generate_prices(n, initial_price)
        
        # 生成 OHLCV
        data = self._generate_ohlcv(prices, n)
        
        df = pd.DataFrame(data, index=dates)
        df.index.name = 'date'
        return df
    
    def _generate_prices(self, n: int, initial_price: float) -> np.ndarray:
        """生成价格序列"""
        returns = np.zeros(n)
        
        if self.trend == 'up':
            drift = 0.0005
        elif self.trend == 'down':
            drift = -0.0005
        elif self.trend == 'mixed':
            # 前半段上涨，后半段下跌
            half = n // 2
            returns[:half] = np.random.normal(0.0005, self.volatility, half)
            returns[half:] = np.random.normal(-0.0003, self.volatility, n - half)
            returns = np.cumsum(returns)
            prices = initial_price * np.exp(returns)
            return prices
        else:  # sideways
            drift = 0.0
        
        for i in range(1, n):
            returns[i] = drift + np.random.normal(0, self.volatility) + \
                         self.noise_level * np.sin(2 * np.pi * i / 60)
        
        prices = initial_price * np.exp(np.cumsum(returns))
        return prices
    
    def _generate_ohlcv(self, prices: np.ndarray, n: int) -> Dict:
        """从收盘价生成 OHLCV 数据"""
        noise = self.volatility * 0.3
        
        data = {
            'open': np.zeros(n),
            'high': np.zeros(n),
            'low': np.zeros(n),
            'close': prices,
            'volume': np.random.randint(100000, 1000000, n).astype(float),
        }
        
        for i in range(n):
            data['open'][i] = prices[i] * (1 + np.random.normal(0, noise * 0.5))
            data['high'][i] = max(data['open'][i], prices[i]) * (1 + abs(np.random.normal(0, noise)))
            data['low'][i] = min(data['open'][i], prices[i]) * (1 - abs(np.random.normal(0, noise)))
        
        return data
    
    def fetch_realtime(self, symbol: str = 'MOCK') -> Dict:
        """模拟实时数据"""
        price = 100 + np.random.normal(0, 2)
        return {
            'symbol': symbol,
            'price': price,
            'volume': np.random.randint(10000, 100000),
            'timestamp': pd.Timestamp.now().isoformat(),
        }
    
    def generate_pair_data(self, start_date: str = '2023-01-01',
                           end_date: str = '2024-01-01',
                           correlation: float = 0.9,
                           seed: Optional[int] = None) -> pd.DataFrame:
        """
        生成配对交易用的两组相关数据
        
        Returns:
            DataFrame 包含 'close' 和 'pair_close' 列
        """
        if seed is not None:
            np.random.seed(seed)
        
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        n = len(dates)
        
        # 生成基准价格
        base_returns = np.random.normal(0, 0.02, n)
        base_prices = 100 * np.exp(np.cumsum(base_returns))
        
        # 生成相关价格
        noise = np.random.normal(0, 0.005 * (1 - correlation), n)
        pair_returns = correlation * base_returns + noise
        pair_prices = 100 * np.exp(np.cumsum(pair_returns))
        
        df = pd.DataFrame({
            'open': base_prices * (1 + np.random.normal(0, 0.001, n)),
            'high': base_prices * (1 + abs(np.random.normal(0, 0.005, n))),
            'low': base_prices * (1 - abs(np.random.normal(0, 0.005, n))),
            'close': base_prices,
            'pair_close': pair_prices,
            'volume': np.random.randint(100000, 1000000, n),
        }, index=dates)
        
        return df
