"""
配对交易策略 (Pairs Trading Strategy)

利用两个高相关性资产之间的价格关系进行交易。
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from .base import BaseStrategy


class PairsTradingStrategy(BaseStrategy):
    """
    配对交易策略
    
    选择两个高相关性资产，当价差偏离均值时进行套利。
    
    参数:
        lookback_period (int): 回看周期，默认 60
        entry_threshold (float): 入场阈值（标准差倍数），默认 2.0
        exit_threshold (float): 出场阈值，默认 0.5
        stop_loss (float): 止损阈值，默认 4.0
        min_correlation (float): 最低相关性要求，默认 0.8
    """
    
    @property
    def name(self) -> str:
        return "配对交易策略"
    
    @property
    def description(self) -> str:
        return "配对交易策略 - 利用资产间价格关系"
    
    def init(self):
        """初始化默认参数"""
        defaults = {
            'lookback_period': 60,
            'entry_threshold': 2.0,
            'exit_threshold': 0.5,
            'stop_loss': 4.0,
            'min_correlation': 0.8,
        }
        for key, value in defaults.items():
            if key not in self.params:
                self.params[key] = value
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成配对交易信号
        
        Args:
            data: 需包含 'close' 和 'pair_close' 列
        """
        df = data.copy()
        
        if 'pair_close' not in df.columns:
            raise ValueError("配对交易策略需要 'pair_close' 列")
        
        # 计算对冲比率
        hedge_ratio = self._calculate_hedge_ratio(df['close'], df['pair_close'])
        
        # 计算价差
        spread = df['close'] - hedge_ratio * df['pair_close']
        
        # 计算价差 Z-score
        zscore = self._calculate_spread_zscore(spread)
        
        # 存储指标
        self._indicators = {
            'spread': spread,
            'zscore': zscore,
            'hedge_ratio': pd.Series(hedge_ratio, index=df.index),
        }
        
        # 生成信号
        signals = self._generate_pair_signals(zscore)
        
        df['signal'] = signals
        df['spread'] = spread
        df['zscore'] = zscore
        df['hedge_ratio'] = hedge_ratio
        
        return df
    
    def _calculate_hedge_ratio(self, series_a: pd.Series, series_b: pd.Series) -> float:
        """
        计算对冲比率（OLS 回归斜率）
        """
        x = series_b.values
        y = series_a.values
        
        # 去除 NaN
        mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[mask]
        y_clean = y[mask]
        
        if len(x_clean) < 10:
            return 1.0
        
        # OLS 回归
        cov_matrix = np.cov(x_clean, y_clean)
        if cov_matrix[0, 0] == 0:
            return 1.0
        
        hedge_ratio = cov_matrix[0, 1] / cov_matrix[0, 0]
        return hedge_ratio
    
    def _calculate_spread_zscore(self, spread: pd.Series) -> pd.Series:
        """计算价差 Z-score"""
        period = self.params['lookback_period']
        mean = spread.rolling(window=period).mean()
        std = spread.rolling(window=period).std()
        zscore = (spread - mean) / std
        return zscore
    
    def _generate_pair_signals(self, zscore: pd.Series) -> pd.Series:
        """
        生成配对交易信号
        
        - Z-score < -entry → 做多价差（买 A 卖 B）
        - Z-score > entry → 做空价差（卖 A 买 B）
        - |Z-score| < exit → 平仓
        """
        signals = pd.Series(0, index=zscore.index)
        entry = self.params['entry_threshold']
        exit_val = self.params['exit_threshold']
        stop = self.params['stop_loss']
        
        position = 0
        
        for i in range(len(zscore)):
            if pd.isna(zscore.iloc[i]):
                continue
            
            z = zscore.iloc[i]
            
            if position == 0:
                if z < -entry:
                    signals.iloc[i] = 1  # 做多价差
                    position = 1
                elif z > entry:
                    signals.iloc[i] = -1  # 做空价差
                    position = -1
            
            elif position == 1:
                if z > -exit_val or z < -stop:
                    signals.iloc[i] = -1  # 平仓
                    position = 0
            
            elif position == -1:
                if z < exit_val or z > stop:
                    signals.iloc[i] = 1  # 平仓
                    position = 0
        
        return signals
    
    def find_correlated_pairs(self, price_data: Dict[str, pd.Series],
                               min_correlation: Optional[float] = None) -> List[Tuple]:
        """
        寻找高相关性配对
        
        Args:
            price_data: {资产名: 价格序列} 字典
            min_correlation: 最低相关性阈值
        
        Returns:
            [(资产A, 资产B, 相关系数)] 列表，按相关系数降序排列
        """
        if min_correlation is None:
            min_correlation = self.params['min_correlation']
        
        assets = list(price_data.keys())
        n = len(assets)
        pairs = []
        
        # 构建价格矩阵
        prices = pd.DataFrame(price_data)
        
        # 计算相关系数矩阵
        corr_matrix = prices.corr()
        
        for i in range(n):
            for j in range(i + 1, n):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) >= min_correlation:
                    pairs.append((assets[i], assets[j], corr))
        
        # 按相关系数绝对值降序排列
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        return pairs
