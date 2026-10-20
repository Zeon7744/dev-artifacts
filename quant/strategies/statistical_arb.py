"""
统计套利策略 (Statistical Arbitrage Strategy)

基于统计关系的套利策略，利用价格偏离统计平衡态时的回归特性。
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from .base import BaseStrategy


class StatisticalArbStrategy(BaseStrategy):
    """
    统计套利策略
    
    使用协整关系和价差统计进行套利交易。
    
    参数:
        lookback_period (int): 统计回看周期，默认 60
        entry_zscore (float): 入场 Z-score 阈值，默认 2.0
        exit_zscore (float): 出场 Z-score 阈值，默认 0.5
        stop_loss_zscore (float): 止损 Z-score 阈值，默认 4.0
        cointegration_window (int): 协整检验窗口，默认 120
    """
    
    @property
    def name(self) -> str:
        return "统计套利策略"
    
    @property
    def description(self) -> str:
        return "统计套利策略 - 基于价差均值回归"
    
    def init(self):
        """初始化默认参数"""
        defaults = {
            'lookback_period': 60,
            'entry_zscore': 2.0,
            'exit_zscore': 0.5,
            'stop_loss_zscore': 4.0,
            'cointegration_window': 120,
        }
        for key, value in defaults.items():
            if key not in self.params:
                self.params[key] = value
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成信号
        
        Args:
            data: 需包含 'close' 列（单资产价差模式）
                  或 'close' 和 'benchmark' 列（相对模式）
        """
        df = data.copy()
        
        if 'benchmark' in df.columns:
            # 相对模式：计算与基准的价差
            spread = df['close'] - df['benchmark']
        else:
            # 单资产模式：计算价格偏离
            spread = df['close'] - df['close'].rolling(
                window=self.params['lookback_period']
            ).mean()
        
        # 计算价差 Z-score
        zscore = self._calculate_spread_zscore(spread)
        
        # 存储指标
        self._indicators = {
            'spread': spread,
            'zscore': zscore,
        }
        
        # 生成信号
        signals = self._generate_zscore_signals(zscore)
        df['signal'] = signals
        df['spread'] = spread
        df['zscore'] = zscore
        
        return df
    
    def _calculate_spread_zscore(self, spread: pd.Series) -> pd.Series:
        """计算价差 Z-score"""
        period = self.params['lookback_period']
        mean = spread.rolling(window=period).mean()
        std = spread.rolling(window=period).std()
        zscore = (spread - mean) / std
        return zscore
    
    def _generate_zscore_signals(self, zscore: pd.Series) -> pd.Series:
        """
        基于 Z-score 生成信号
        
        - Z-score > entry → 做空价差（卖出）
        - Z-score < -entry → 做多价差（买入）
        - |Z-score| < exit → 平仓
        - |Z-score| > stop_loss → 止损
        """
        signals = pd.Series(0, index=zscore.index)
        entry = self.params['entry_zscore']
        exit_val = self.params['exit_zscore']
        stop_loss = self.params['stop_loss_zscore']
        
        position = 0  # 0=空仓, 1=多头, -1=空头
        
        for i in range(len(zscore)):
            if pd.isna(zscore.iloc[i]):
                continue
            
            z = zscore.iloc[i]
            
            if position == 0:
                if z < -entry:
                    signals.iloc[i] = 1  # 买入
                    position = 1
                elif z > entry:
                    signals.iloc[i] = -1  # 卖出
                    position = -1
            
            elif position == 1:
                if z > -exit_val or z < -stop_loss:
                    signals.iloc[i] = -1  # 平仓
                    position = 0
            
            elif position == -1:
                if z < exit_val or z > stop_loss:
                    signals.iloc[i] = 1  # 平仓
                    position = 0
        
        return signals
    
    def test_cointegration(self, series_a: pd.Series, series_b: pd.Series) -> Dict:
        """
        协整检验（简化版）
        
        使用 Engle-Granger 两步法的简化实现
        
        Returns:
            包含 is_cointegrated, p_value, hedge_ratio 的字典
        """
        # 计算对冲比率
        from numpy.polynomial import polynomial as P
        
        # 简单线性回归
        x = series_b.values
        y = series_a.values
        
        # OLS 回归
        slope = np.cov(x, y)[0, 1] / np.var(x)
        intercept = np.mean(y) - slope * np.mean(x)
        
        # 残差
        residuals = y - (slope * x + intercept)
        
        # ADF 检验（简化版）
        adf_stat = self._simple_adf_test(residuals)
        
        # 判断是否协整（简化阈值）
        is_cointegrated = adf_stat < -3.0
        
        return {
            'is_cointegrated': is_cointegrated,
            'adf_statistic': adf_stat,
            'hedge_ratio': slope,
            'intercept': intercept,
        }
    
    def _simple_adf_test(self, series: np.ndarray) -> float:
        """简化版 ADF 检验"""
        n = len(series)
        if n < 10:
            return 0.0
        
        # 计算差分
        diff = np.diff(series)
        
        # 回归 Δy_t = α + β*y_{t-1} + ε
        y_lag = series[:-1]  # length n-1
        
        try:
            # 使用 y_lag 和 diff，两者长度都是 n-1
            x = np.column_stack([np.ones(len(diff)), y_lag[:len(diff)]])
            beta = np.linalg.lstsq(x, diff, rcond=None)[0]
            residuals = diff - x @ beta
            
            # 计算 t 统计量
            se = np.std(residuals) / np.sqrt(len(diff) - 2) if len(diff) > 2 else 1.0
            t_stat = beta[1] / se if se > 0 else 0.0
            
            return t_stat
        except Exception:
            return 0.0
