"""
动量策略 (Momentum Strategy)

基于技术指标的动量交易策略，包含：
- 移动平均线交叉 (MA Crossover)
- RSI 超买超卖
- MACD 信号
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base import BaseStrategy


class MomentumStrategy(BaseStrategy):
    """
    动量策略
    
    使用移动平均线交叉、RSI 和 MACD 组合产生交易信号。
    
    参数:
        fast_period (int): 快速均线周期，默认 10
        slow_period (int): 慢速均线周期，默认 30
        rsi_period (int): RSI 周期，默认 14
        rsi_overbought (float): RSI 超买阈值，默认 70
        rsi_oversold (float): RSI 超卖阈值，默认 30
        macd_fast (int): MACD 快速线周期，默认 12
        macd_slow (int): MACD 慢速线周期，默认 26
        macd_signal (int): MACD 信号线周期，默认 9
        mode (str): 策略模式 'ma_cross' / 'rsi' / 'macd' / 'combined'
    """
    
    @property
    def name(self) -> str:
        return "动量策略"
    
    @property
    def description(self) -> str:
        return f"动量策略 (模式: {self.params.get('mode', 'combined')})"
    
    def init(self):
        """初始化默认参数"""
        defaults = {
            'fast_period': 10,
            'slow_period': 30,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'mode': 'combined',
        }
        for key, value in defaults.items():
            if key not in self.params:
                self.params[key] = value
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 市场数据（需包含 close 列）
        
        Returns:
            包含 signal 列的 DataFrame
        """
        df = data.copy()
        close = df['close']
        mode = self.params['mode']
        
        # 计算指标
        fast_ma = self._calculate_ema(close, self.params['fast_period'])
        slow_ma = self._calculate_ema(close, self.params['slow_period'])
        rsi = self._calculate_rsi(close, self.params['rsi_period'])
        macd_line, signal_line, histogram = self._calculate_macd(
            close,
            self.params['macd_fast'],
            self.params['macd_slow'],
            self.params['macd_signal']
        )
        
        # 存储指标
        self._indicators = {
            'fast_ma': fast_ma,
            'slow_ma': slow_ma,
            'rsi': rsi,
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram,
        }
        
        # 生成信号
        if mode == 'ma_cross':
            signals = self._ma_cross_signals(fast_ma, slow_ma)
        elif mode == 'rsi':
            signals = self._rsi_signals(rsi)
        elif mode == 'macd':
            signals = self._macd_signals(macd_line, signal_line, histogram)
        elif mode == 'combined':
            signals = self._combined_signals(fast_ma, slow_ma, rsi, macd_line, signal_line, histogram)
        else:
            raise ValueError(f"未知策略模式: {mode}")
        
        df['signal'] = signals
        return df
    
    def _ma_cross_signals(self, fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
        """移动平均线交叉信号"""
        signals = pd.Series(0, index=fast_ma.index)
        
        # 金叉买入
        cross_up = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        signals[cross_up] = 1
        
        # 死叉卖出
        cross_down = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        signals[cross_down] = -1
        
        return signals
    
    def _rsi_signals(self, rsi: pd.Series) -> pd.Series:
        """RSI 超买超卖信号"""
        signals = pd.Series(0, index=rsi.index)
        
        overbought = self.params['rsi_overbought']
        oversold = self.params['rsi_oversold']
        
        # 超卖区域买入
        buy_signal = (rsi < oversold) & (rsi.shift(1) >= oversold)
        signals[buy_signal] = 1
        
        # 超买区域卖出
        sell_signal = (rsi > overbought) & (rsi.shift(1) <= overbought)
        signals[sell_signal] = -1
        
        return signals
    
    def _macd_signals(self, macd_line: pd.Series, signal_line: pd.Series,
                       histogram: pd.Series) -> pd.Series:
        """MACD 信号"""
        signals = pd.Series(0, index=macd_line.index)
        
        # MACD 金叉
        cross_up = (histogram > 0) & (histogram.shift(1) <= 0)
        signals[cross_up] = 1
        
        # MACD 死叉
        cross_down = (histogram < 0) & (histogram.shift(1) >= 0)
        signals[cross_down] = -1
        
        return signals
    
    def _combined_signals(self, fast_ma, slow_ma, rsi, macd_line, signal_line, histogram):
        """
        组合信号
        
        需要至少 2 个指标确认才产生信号
        """
        n = len(fast_ma)
        signals = pd.Series(0, index=fast_ma.index)
        
        ma_buy = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        ma_sell = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        
        rsi_buy = rsi < self.params['rsi_oversold']
        rsi_sell = rsi > self.params['rsi_overbought']
        
        macd_buy = (histogram > 0) & (histogram.shift(1) <= 0)
        macd_sell = (histogram < 0) & (histogram.shift(1) >= 0)
        
        for i in range(1, n):
            buy_score = int(ma_buy.iloc[i]) + int(rsi_buy.iloc[i]) + int(macd_buy.iloc[i])
            sell_score = int(ma_sell.iloc[i]) + int(rsi_sell.iloc[i]) + int(macd_sell.iloc[i])
            
            if buy_score >= 2:
                signals.iloc[i] = 1
            elif sell_score >= 2:
                signals.iloc[i] = -1
        
        return signals
