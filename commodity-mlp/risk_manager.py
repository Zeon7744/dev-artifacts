"""
大宗商品MLP投资分析工具 - 风险管理模块
提供仓位管理和风险控制功能
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class RiskManager:
    """风险管理模块"""
    
    def __init__(
        self,
        max_position_size: float = 0.3,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.15,
        max_daily_loss_pct: float = 0.02,
        max_consecutive_losses: int = 5
    ):
        """
        初始化风险管理器
        
        参数:
            max_position_size: 最大仓位比例
            stop_loss_pct: 止损百分比
            take_profit_pct: 止盈百分比
            max_daily_loss_pct: 每日最大亏损百分比
            max_consecutive_losses: 最大连续亏损次数
        """
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_consecutive_losses = max_consecutive_losses
        
        self.position_size = 0.0
        self.entry_price = 0.0
        self.consecutive_losses = 0
        self.daily_pnl = 0.0
        self.trades_history = []
    
    def calculate_position_size(
        self,
        capital: float,
        signal_confidence: float,
        volatility: float
    ) -> float:
        """
        计算仓位大小
        
        参数:
            capital: 可用资金
            signal_confidence: 信号置信度
            volatility: 标的波动率
            
        返回:
            建议仓位比例
        """
        # 基于置信度的仓位调整
        confidence_factor = min(signal_confidence, 1.0)
        
        # 基于波动率的仓位调整（波动率越高，仓位越小）
        vol_factor = max(0.5, 1.0 - volatility * 2)
        
        # 基础仓位
        base_position = self.max_position_size * confidence_factor * vol_factor
        
        return base_position
    
    def check_stop_loss(
        self,
        entry_price: float,
        current_price: float,
        direction: str = 'long'
    ) -> bool:
        """
        检查是否触发止损
        
        参数:
            entry_price: 入场价格
            current_price: 当前价格
            direction: 方向（long/short）
            
        返回:
            是否触发止损
        """
        if direction == 'long':
            loss_pct = (entry_price - current_price) / entry_price
            return loss_pct >= self.stop_loss_pct
        else:
            loss_pct = (current_price - entry_price) / entry_price
            return loss_pct >= self.stop_loss_pct
    
    def check_take_profit(
        self,
        entry_price: float,
        current_price: float,
        direction: str = 'long'
    ) -> bool:
        """
        检查是否触发止盈
        
        参数:
            entry_price: 入场价格
            current_price: 当前价格
            direction: 方向（long/short）
            
        返回:
            是否触发止盈
        """
        if direction == 'long':
            profit_pct = (current_price - entry_price) / entry_price
            return profit_pct >= self.take_profit_pct
        else:
            profit_pct = (entry_price - current_price) / entry_price
            return profit_pct >= self.take_profit_pct
    
    def check_daily_limit(
        self,
        current_pnl: float,
        initial_capital: float
    ) -> bool:
        """
        检查是否触发每日亏损限制
        
        参数:
            current_pnl: 当前盈亏
            initial_capital: 初始资金
            
        返回:
            是否触发限制
        """
        loss_pct = abs(min(current_pnl, 0)) / initial_capital
        return loss_pct >= self.max_daily_loss_pct
    
    def check_consecutive_losses(self) -> bool:
        """
        检查是否达到最大连续亏损次数
        
        返回:
            是否触发限制
        """
        return self.consecutive_losses >= self.max_consecutive_losses
    
    def update_trades(self, trade_result: Dict):
        """
        更新交易历史
        
        参数:
            trade_result: 交易结果字典
        """
        self.trades_history.append(trade_result)
        
        # 更新连续亏损计数
        if trade_result.get('pnl', 0) < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # 更新当日盈亏
        self.daily_pnl += trade_result.get('pnl', 0)
    
    def get_risk_summary(self) -> Dict:
        """获取风险摘要"""
        return {
            'position_size': self.position_size,
            'entry_price': self.entry_price,
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl': self.daily_pnl,
            'total_trades': len(self.trades_history),
            'winning_trades': len([t for t in self.trades_history if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in self.trades_history if t.get('pnl', 0) < 0]),
            'win_rate': len([t for t in self.trades_history if t.get('pnl', 0) > 0]) / max(len(self.trades_history), 1) * 100
        }
    
    def should_trade(self, capital: float, signal_confidence: float, volatility: float) -> Dict:
        """
        判断是否应该交易
        
        参数:
            capital: 可用资金
            signal_confidence: 信号置信度
            volatility: 波动率
            
        返回:
            交易决策字典
        """
        decision = {
            'should_trade': True,
            'position_size': 0,
            'reason': ''
        }
        
        # 检查连续亏损
        if self.check_consecutive_losses():
            decision['should_trade'] = False
            decision['reason'] = '达到最大连续亏损次数'
            return decision
        
        # 检查每日亏损限制
        if self.daily_pnl < 0 and abs(self.daily_pnl) / capital >= self.max_daily_loss_pct:
            decision['should_trade'] = False
            decision['reason'] = '触发每日亏损限制'
            return decision
        
        # 检查置信度
        if signal_confidence < 0.6:
            decision['should_trade'] = False
            decision['reason'] = '信号置信度过低'
            return decision
        
        # 计算仓位
        position_size = self.calculate_position_size(capital, signal_confidence, volatility)
        decision['position_size'] = position_size
        
        return decision


if __name__ == '__main__':
    # 测试风险管理模块
    print("=" * 60)
    print("风险管理模块测试")
    print("=" * 60)
    
    risk_manager = RiskManager()
    
    # 测试仓位计算
    position = risk_manager.calculate_position_size(
        capital=100000,
        signal_confidence=0.8,
        volatility=0.02
    )
    print(f"\n建议仓位: {position:.2%}")
    
    # 测试止损检查
    stop_triggered = risk_manager.check_stop_loss(
        entry_price=100,
        current_price=94,
        direction='long'
    )
    print(f"止损触发: {stop_triggered}")
    
    # 测试止盈检查
    profit_triggered = risk_manager.check_take_profit(
        entry_price=100,
        current_price=116,
        direction='long'
    )
    print(f"止盈触发: {profit_triggered}")
    
    # 模拟交易历史
    risk_manager.update_trades({'pnl': 1000, 'trade_id': 1})
    risk_manager.update_trades({'pnl': -500, 'trade_id': 2})
    risk_manager.update_trades({'pnl': 2000, 'trade_id': 3})
    
    # 获取风险摘要
    summary = risk_manager.get_risk_summary()
    print(f"\n风险摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
