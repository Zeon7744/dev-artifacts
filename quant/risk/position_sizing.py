"""
仓位管理模块

根据风险参数计算合适的仓位大小
"""

import numpy as np
from typing import Dict, Optional


class PositionSizer:
    """
    仓位管理器
    
    支持多种仓位计算方法：
    - 固定比例法
    - Kelly 公式法
    - ATR 波动率法
    - 固定金额法
    
    参数:
        max_position_pct (float): 最大仓位占比
        method (str): 仓位计算方法
    """
    
    def __init__(self, max_position_pct: float = 0.3,
                 method: str = 'fixed_pct',
                 risk_per_trade: float = 0.02):
        self.max_position_pct = max_position_pct
        self.method = method
        self.risk_per_trade = risk_per_trade
    
    def calculate(self, capital: float, price: float,
                  quantity: Optional[float] = None,
                  **kwargs) -> Dict:
        """
        计算仓位大小
        
        Args:
            capital: 总资金
            price: 当前价格
            quantity: 期望数量（可选）
            **kwargs: 额外参数（win_rate, avg_win, avg_loss, atr 等）
        
        Returns:
            {
                'allowed': bool,
                'max_quantity': float,
                'position_pct': float,
                'suggested_quantity': float,
            }
        """
        if self.method == 'fixed_pct':
            return self._fixed_pct(capital, price)
        elif self.method == 'kelly':
            return self._kelly_criterion(capital, price, **kwargs)
        elif self.method == 'atr':
            return self._atr_method(capital, price, **kwargs)
        else:
            return self._fixed_pct(capital, price)
    
    def _fixed_pct(self, capital: float, price: float) -> Dict:
        """固定比例法"""
        max_value = capital * self.max_position_pct
        max_qty = max_value / price if price > 0 else 0
        
        return {
            'allowed': True,
            'max_quantity': max_qty,
            'position_pct': self.max_position_pct,
            'suggested_quantity': max_qty,
        }
    
    def _kelly_criterion(self, capital: float, price: float,
                          win_rate: float = 0.5,
                          avg_win: float = 0.02,
                          avg_loss: float = 0.01,
                          **kwargs) -> Dict:
        """
        Kelly 公式法
        
        f* = (p*b - q) / b
        p = 胜率, q = 1-p, b = 盈亏比
        """
        if avg_loss == 0:
            b = 1
        else:
            b = avg_win / avg_loss
        
        q = 1 - win_rate
        kelly_fraction = (win_rate * b - q) / b
        
        # 限制 Kelly 比例在 0-1 之间
        kelly_fraction = max(0, min(kelly_fraction, 1))
        
        # 使用半 Kelly（更保守）
        position_pct = kelly_fraction * 0.5
        position_pct = min(position_pct, self.max_position_pct)
        
        position_value = capital * position_pct
        max_qty = position_value / price if price > 0 else 0
        
        return {
            'allowed': position_pct > 0,
            'max_quantity': max_qty,
            'position_pct': position_pct,
            'suggested_quantity': max_qty,
            'kelly_fraction': kelly_fraction,
        }
    
    def _atr_method(self, capital: float, price: float,
                    atr: float = 0, risk_per_trade: float = None,
                    **kwargs) -> Dict:
        """
        ATR 波动率法
        
        仓位 = (总资金 * 单笔风险比例) / ATR
        """
        if risk_per_trade is None:
            risk_per_trade = self.risk_per_trade
        
        if atr <= 0:
            return self._fixed_pct(capital, price)
        
        risk_amount = capital * risk_per_trade
        quantity = risk_amount / atr
        
        position_value = quantity * price
        position_pct = position_value / capital if capital > 0 else 0
        
        # 不超过最大仓位
        if position_pct > self.max_position_pct:
            quantity = (capital * self.max_position_pct) / price
            position_pct = self.max_position_pct
        
        return {
            'allowed': quantity > 0,
            'max_quantity': quantity,
            'position_pct': min(position_pct, self.max_position_pct),
            'suggested_quantity': quantity,
        }
