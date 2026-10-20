"""
止损模块

实现多种止损策略
"""

import pandas as pd
from typing import Dict, Optional


class StopLoss:
    """
    止损管理器
    
    支持多种止损方式：
    - 固定百分比止损
    - 跟踪止损
    - ATR 止损
    - 时间止损
    
    参数:
        stop_loss_pct (float): 固定止损比例
        trailing_pct (float): 跟踪止损回撤比例
    """
    
    def __init__(self, stop_loss_pct: float = 0.05,
                 trailing_pct: float = 0.03,
                 method: str = 'fixed'):
        self.stop_loss_pct = stop_loss_pct
        self.trailing_pct = trailing_pct
        self.method = method
        
        self._highest_price = 0
        self._entry_time = None
    
    def check(self, entry_price: float, current_price: float,
              direction: int = 1, **kwargs) -> Dict:
        """
        检查是否触发止损
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            direction: 方向 (1=多头, -1=空头)
        
        Returns:
            {
                'should_stop': bool,
                'loss_pct': float,
                'distance_to_stop': float,
                'stop_price': float,
            }
        """
        if self.method == 'fixed':
            return self._check_fixed(entry_price, current_price, direction)
        elif self.method == 'trailing':
            return self._check_trailing(entry_price, current_price, direction)
        elif self.method == 'atr':
            return self._check_atr(entry_price, current_price, direction, **kwargs)
        else:
            return self._check_fixed(entry_price, current_price, direction)
    
    def _check_fixed(self, entry_price: float, current_price: float,
                     direction: int) -> Dict:
        """固定百分比止损"""
        if direction == 1:
            loss_pct = (current_price - entry_price) / entry_price
            stop_price = entry_price * (1 - self.stop_loss_pct)
            should_stop = current_price <= stop_price
        else:
            loss_pct = (entry_price - current_price) / entry_price
            stop_price = entry_price * (1 + self.stop_loss_pct)
            should_stop = current_price >= stop_price
        
        distance = abs(current_price - stop_price) / current_price
        
        return {
            'should_stop': should_stop,
            'loss_pct': loss_pct,
            'distance_to_stop': distance,
            'stop_price': stop_price,
        }
    
    def _check_trailing(self, entry_price: float, current_price: float,
                        direction: int) -> Dict:
        """
        跟踪止损
        
        跟踪最高价，当从最高点回撤超过阈值时止损
        """
        if direction == 1:
            self._highest_price = max(self._highest_price, current_price)
            stop_price = self._highest_price * (1 - self.trailing_pct)
            loss_pct = (current_price - entry_price) / entry_price
            should_stop = current_price <= stop_price
        else:
            if self._highest_price == 0 or current_price < self._highest_price:
                self._highest_price = current_price
            stop_price = self._highest_price * (1 + self.trailing_pct)
            loss_pct = (entry_price - current_price) / entry_price
            should_stop = current_price >= stop_price
        
        distance = abs(current_price - stop_price) / current_price
        
        return {
            'should_stop': should_stop,
            'loss_pct': loss_pct,
            'distance_to_stop': distance,
            'stop_price': stop_price,
            'highest_price': self._highest_price,
        }
    
    def _check_atr(self, entry_price: float, current_price: float,
                   direction: int, atr: float = 0, atr_multiplier: float = 2.0,
                   **kwargs) -> Dict:
        """ATR 止损"""
        if atr <= 0:
            return self._check_fixed(entry_price, current_price, direction)
        
        if direction == 1:
            stop_price = entry_price - atr * atr_multiplier
            loss_pct = (current_price - entry_price) / entry_price
            should_stop = current_price <= stop_price
        else:
            stop_price = entry_price + atr * atr_multiplier
            loss_pct = (entry_price - current_price) / entry_price
            should_stop = current_price >= stop_price
        
        distance = abs(current_price - stop_price) / current_price
        
        return {
            'should_stop': should_stop,
            'loss_pct': loss_pct,
            'distance_to_stop': distance,
            'stop_price': stop_price,
        }
    
    def reset(self):
        """重置跟踪止损状态"""
        self._highest_price = 0
        self._entry_time = None
