"""
风险管理器

统一管理策略的风险控制
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from .position_sizing import PositionSizer
from .stop_loss import StopLoss


class RiskManager:
    """
    风险管理器
    
    统一管理仓位控制、止损逻辑和风险评级。
    
    参数:
        max_position_pct (float): 最大仓位占比，默认 0.3
        max_drawdown_pct (float): 最大回撤限制，默认 0.15
        stop_loss_pct (float): 单笔止损比例，默认 0.05
        risk_free_rate (float): 无风险利率，默认 0.03
        var_confidence (float): VaR 置信水平，默认 0.95
    """
    
    def __init__(self, max_position_pct: float = 0.3,
                 max_drawdown_pct: float = 0.15,
                 stop_loss_pct: float = 0.05,
                 risk_free_rate: float = 0.03,
                 var_confidence: float = 0.95):
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.stop_loss_pct = stop_loss_pct
        self.risk_free_rate = risk_free_rate
        self.var_confidence = var_confidence
        
        self.position_sizer = PositionSizer(
            max_position_pct=max_position_pct
        )
        self.stop_loss = StopLoss(
            stop_loss_pct=stop_loss_pct
        )
        
        self._risk_events: List[Dict] = []
        self._is_risk_alert = False
    
    def check_position_size(self, capital: float, price: float,
                            quantity: float) -> Dict:
        """
        检查仓位大小
        
        Returns:
            {
                'allowed': bool,
                'max_quantity': float,
                'position_pct': float,
                'suggested_quantity': float,
            }
        """
        return self.position_sizer.calculate(capital, price, quantity)
    
    def check_stop_loss(self, entry_price: float, current_price: float,
                        direction: int = 1) -> Dict:
        """
        检查止损条件
        
        Returns:
            {
                'should_stop': bool,
                'loss_pct': float,
                'distance_to_stop': float,
            }
        """
        return self.stop_loss.check(entry_price, current_price, direction)
    
    def check_drawdown(self, equity_curve: pd.Series) -> Dict:
        """
        检查回撤是否超限
        
        Returns:
            {
                'is_breached': bool,
                'current_drawdown': float,
                'max_allowed': float,
            }
        """
        rolling_max = equity_curve.expanding().max()
        drawdown = (equity_curve - rolling_max) / rolling_max
        current_dd = drawdown.iloc[-1]
        
        is_breached = abs(current_dd) > self.max_drawdown_pct
        
        if is_breached:
            self._log_risk_event('DRAWDOWN_BREACH', {
                'current_drawdown': current_dd,
                'threshold': self.max_drawdown_pct,
            })
            self._is_risk_alert = True
        
        return {
            'is_breached': is_breached,
            'current_drawdown': current_dd,
            'max_allowed': self.max_drawdown_pct,
        }
    
    def calculate_var(self, returns: pd.Series) -> float:
        """
        计算 Value at Risk (VaR)
        
        Returns:
            VaR 值（正值表示损失）
        """
        if len(returns) < 2:
            return 0.0
        
        sorted_returns = np.sort(returns)
        index = int((1 - self.var_confidence) * len(sorted_returns))
        var = abs(sorted_returns[index])
        return var
    
    def calculate_cvar(self, returns: pd.Series) -> float:
        """计算 Conditional VaR (CVaR / Expected Shortfall)"""
        var = self.calculate_var(returns)
        tail_returns = returns[returns <= -var]
        
        if len(tail_returns) == 0:
            return var
        
        return abs(tail_returns.mean())
    
    def risk_rating(self, returns: pd.Series) -> Dict:
        """
        风险评级
        
        Returns:
            {
                'rating': str,  # '低' / '中' / '高' / '极高'
                'score': float,  # 0-100
                'details': dict,
            }
        """
        if len(returns) < 10:
            return {'rating': '未知', 'score': 0, 'details': {}}
        
        volatility = returns.std() * np.sqrt(252)
        
        # 计算最大回撤（简化版）
        cum_returns = (1 + returns).cumprod()
        rolling_max = cum_returns.cummax()
        drawdown = (cum_returns - rolling_max) / rolling_max
        max_dd = abs(drawdown.min())
        
        var = self.calculate_var(returns)
        
        # 评分
        score = 0
        if volatility < 0.1:
            score += 25
        elif volatility < 0.2:
            score += 50
        elif volatility < 0.35:
            score += 75
        else:
            score += 100
        
        if max_dd < 0.05:
            score += 25
        elif max_dd < 0.10:
            score += 50
        elif max_dd < 0.20:
            score += 75
        else:
            score += 100
        
        if var < 0.01:
            score += 25
        elif var < 0.02:
            score += 50
        elif var < 0.04:
            score += 75
        else:
            score += 100
        
        score = score / 3
        
        if score < 30:
            rating = '低风险'
        elif score < 50:
            rating = '中风险'
        elif score < 75:
            rating = '高风险'
        else:
            rating = '极高风险'
        
        return {
            'rating': rating,
            'score': round(score, 1),
            'details': {
                'volatility': round(volatility, 4),
                'max_drawdown': round(max_dd, 4),
                'var_95': round(var, 4),
            }
        }
    
    def _log_risk_event(self, event_type: str, details: Dict):
        """记录风险事件"""
        self._risk_events.append({
            'timestamp': pd.Timestamp.now(),
            'type': event_type,
            'details': details,
        })
    
    def get_risk_events(self) -> List[Dict]:
        """获取风险事件列表"""
        return self._risk_events
    
    @property
    def is_alert(self) -> bool:
        """是否有风险警报"""
        return self._is_risk_alert
    
    def reset_alert(self):
        """重置警报状态"""
        self._is_risk_alert = False
