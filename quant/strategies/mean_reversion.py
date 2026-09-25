"""
均值回归策略 (Mean Reversion Strategy)

基于均值回归原理的交易策略，包含：
- 布林带突破
- Z-score 回归
- 价格偏离度
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    """
    均值回归策略
    
    当价格偏离均值过大时，预期价格回归。
    
    参数:
        bb_period (int): 布林带周期，默认 20
        bb_std (float): 布林带标准差倍数，默认 2.0
        zscore_period (int): Z-score 周期，默认 20
        zscore_entry (float): Z-score 入场阈值，默认 2.0
        zscore_exit (float): Z-score 出场阈值，默认 0.5
        mode (str): 策略模式 'bollinger' / 'zscore' / 'combined'
    """
    
    @property
    def name(self) -> str:
        return "均值回归策略"
    
    @property
    def description(self) -> str:
        return f"均值回归策略 (模式: {self.params.get('mode', 'bollinger')})"
    
    def init(self):
        """初始化默认参数"""
        defaults = {
            'bb_period': 20,
            'bb_std': 2.0,
            'zscore_period': 20,
            'zscore_entry': 2.0,
            'zscore_exit': 0.5,
            'mode': 'bollinger',
        }
        for key, value in defaults.items():
            if key not in self.params:
                self.params[key] = value
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        close = df['close']
        mode = self.params['mode']
        
        # 计算指标
        upper, middle, lower = self._calculate_bollinger_bands(
            close, self.params['bb_period'], self.params['bb_std']
        )
        
        zscore = self._calculate_zscore(close, self.params['zscore_period'])
        
        self._indicators = {
            'bb_upper': upper,
            'bb_middle': middle,
            'bb_lower': lower,
            'zscore': zscore,
        }
        
        if mode == 'bollinger':
            signals = self._bollinger_signals(close, upper, lower, middle)
        elif mode == 'zscore':
            signals = self._zscore_signals(zscore)
        elif mode == 'combined':
            signals = self._combined_signals(close, upper, lower, middle, zscore)
        else:
            raise ValueError(f"未知策略模式: {mode}")
        
        df['signal'] = signals
        return df
    
    def _calculate_zscore(self, series: pd.Series, period: int) -> pd.Series:
        """计算 Z-score"""
        mean = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        zscore = (series - mean) / std
        return zscore
    
    def _bollinger_signals(self, close: pd.Series, upper: pd.Series, 
                           lower: pd.Series, middle: pd.Series) -> pd.Series:
        """
        布林带信号
        
        - 价格触及下轨 → 买入（预期回归均值）
        - 价格触及上轨 → 卖出（预期回归均值）
        """
        signals = pd.Series(0, index=close.index)
        
        # 触及下轨买入
        buy_signal = close < lower
        signals[buy_signal] = 1
        
        # 触及上轨卖出
        sell_signal = close > upper
        signals[sell_signal] = -1
        
        return signals
    
    def _zscore_signals(self, zscore: pd.Series) -> pd.Series:
        """
        Z-score 信号
        
        - Z-score < -entry → 买入
        - Z-score > entry → 卖出
        - |Z-score| < exit → 平仓
        """
        signals = pd.Series(0, index=zscore.index)
        entry = self.params['zscore_entry']
        
        signals[zscore < -entry] = 1
        signals[zscore > entry] = -1
        
        return signals
    
    def _combined_signals(self, close, upper, lower, middle, zscore) -> pd.Series:
        """组合信号：布林带 + Z-score 双重确认"""
        signals = pd.Series(0, index=close.index)
        
        bb_buy = close < lower
        bb_sell = close > upper
        
        zscore_buy = zscore < -self.params['zscore_entry']
        zscore_sell = zscore > self.params['zscore_entry']
        
        # 两个指标同时确认
        combined_buy = bb_buy & zscore_buy
        combined_sell = bb_sell & zscore_sell
        
        signals[combined_buy] = 1
        signals[combined_sell] = -1
        
        return signals
