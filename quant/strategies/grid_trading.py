"""
网格交易策略 (Grid Trading Strategy)

在价格区间内设置等距或动态网格，自动低买高卖。
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from .base import BaseStrategy


class GridTradingStrategy(BaseStrategy):
    """
    网格交易策略
    
    在设定的价格区间内划分网格，价格下穿网格线买入，上穿卖出。
    
    参数:
        grid_size (float): 网格间距（比例），默认 0.02 (2%)
        upper_price (float): 网格上界，默认 None（自动计算）
        lower_price (float): 网格下界，默认 None（自动计算）
        num_grids (int): 网格数量，默认 10
        dynamic (bool): 是否使用动态网格，默认 False
        atr_period (int): ATR 周期（动态网格用），默认 14
    """
    
    @property
    def name(self) -> str:
        return "网格交易策略"
    
    @property
    def description(self) -> str:
        return f"网格交易策略 ({'动态' if self.params.get('dynamic') else '固定'}网格)"
    
    def init(self):
        """初始化默认参数"""
        defaults = {
            'grid_size': 0.02,
            'upper_price': None,
            'lower_price': None,
            'num_grids': 10,
            'dynamic': False,
            'atr_period': 14,
        }
        for key, value in defaults.items():
            if key not in self.params:
                self.params[key] = value
        
        self._grid_levels: List[float] = []
        self._last_grid_level: Optional[float] = None
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成网格交易信号"""
        df = data.copy()
        close = df['close']
        
        if self.params['dynamic']:
            signals = self._dynamic_grid_signals(df)
        else:
            signals = self._fixed_grid_signals(close)
        
        df['signal'] = signals
        return df
    
    def _build_fixed_grid(self, close: pd.Series) -> List[float]:
        """构建固定网格"""
        upper = self.params['upper_price']
        lower = self.params['lower_price']
        
        if upper is None:
            upper = close.max() * 1.05
        if lower is None:
            lower = close.min() * 0.95
        
        grid_size = self.params['grid_size']
        num_grids = self.params['num_grids']
        
        # 基于范围生成网格
        grid_levels = np.linspace(lower, upper, num_grids + 1)
        self._grid_levels = grid_levels.tolist()
        return self._grid_levels
    
    def _fixed_grid_signals(self, close: pd.Series) -> pd.Series:
        """
        固定网格信号
        
        价格下穿网格线 → 买入
        价格上穿网格线 → 卖出
        """
        signals = pd.Series(0, index=close.index)
        grid_levels = self._build_fixed_grid(close)
        
        prev_level_idx = None
        
        for i in range(len(close)):
            price = close.iloc[i]
            
            # 找到价格所在网格区间
            current_level_idx = np.searchsorted(grid_levels, price)
            
            if prev_level_idx is not None:
                if current_level_idx < prev_level_idx:
                    # 价格下穿网格线，买入
                    signals.iloc[i] = 1
                elif current_level_idx > prev_level_idx:
                    # 价格上穿网格线，卖出
                    signals.iloc[i] = -1
            
            prev_level_idx = current_level_idx
        
        return signals
    
    def _dynamic_grid_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        动态网格信号
        
        使用 ATR 动态调整网格间距
        """
        signals = pd.Series(0, index=data.index)
        close = data['close']
        
        atr = self._calculate_atr(data, self.params['atr_period'])
        
        # 动态网格间距 = ATR * 系数
        grid_spacing = atr * 1.5
        
        prev_grid = None
        
        for i in range(1, len(close)):
            if pd.isna(grid_spacing.iloc[i]):
                continue
            
            price = close.iloc[i]
            spacing = grid_spacing.iloc[i]
            
            if prev_grid is None:
                prev_grid = price
                continue
            
            # 计算网格边界
            upper_grid = prev_grid + spacing
            lower_grid = prev_grid - spacing
            
            if price < lower_grid:
                signals.iloc[i] = 1  # 买入
                prev_grid = price
            elif price > upper_grid:
                signals.iloc[i] = -1  # 卖出
                prev_grid = price
        
        return signals
