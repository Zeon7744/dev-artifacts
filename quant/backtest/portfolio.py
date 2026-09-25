"""
投资组合管理模块

跟踪资金、持仓、交易记录和权益曲线
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class Portfolio:
    """
    投资组合管理器
    
    管理账户资金、持仓、交易记录和权益曲线。
    支持做多/做空、手续费和滑点模拟。
    
    Attributes:
        initial_capital: 初始资金
        cash: 当前现金
        positions: 当前持仓
        trades: 交易记录
        equity_curve: 权益曲线
    """
    
    def __init__(self, initial_capital: float = 100000.0,
                 commission_rate: float = 0.001,
                 slippage: float = 0.0005):
        """
        初始化投资组合
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点比例
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self.positions: Dict[str, Dict] = {}
        self.trades: List[Dict] = []
        self.equity_history: List[Tuple] = []
        
    @property
    def total_equity(self) -> float:
        """当前总权益"""
        return self.cash + self._position_value()
    
    def _position_value(self, prices: Optional[Dict[str, float]] = None) -> float:
        """计算持仓总价值"""
        total = 0.0
        for symbol, pos in self.positions.items():
            if prices and symbol in prices:
                price = prices[symbol]
            else:
                price = pos.get('avg_price', 0)
            
            total += pos['quantity'] * price * pos.get('direction', 1)
        return total
    
    def buy(self, symbol: str, quantity: float, price: float, 
            timestamp: Optional[datetime] = None) -> bool:
        """
        买入操作
        
        Args:
            symbol: 交易标的
            quantity: 买入数量
            price: 买入价格
            timestamp: 交易时间
        
        Returns:
            是否成功
        """
        # 加入滑点
        actual_price = price * (1 + self.slippage)
        cost = actual_price * quantity
        
        # 手续费
        commission = cost * self.commission_rate
        total_cost = cost + commission
        
        # 检查资金
        if total_cost > self.cash:
            return False
        
        # 更新持仓
        if symbol in self.positions:
            pos = self.positions[symbol]
            old_cost = pos['avg_price'] * pos['quantity']
            new_cost = actual_price * quantity
            pos['quantity'] += quantity
            pos['avg_price'] = (old_cost + new_cost) / pos['quantity'] if pos['quantity'] > 0 else 0
        else:
            self.positions[symbol] = {
                'quantity': quantity,
                'avg_price': actual_price,
                'direction': 1,
                'entry_time': timestamp or datetime.now(),
            }
        
        # 扣减现金
        self.cash -= total_cost
        
        # 记录交易
        self.trades.append({
            'timestamp': timestamp or datetime.now(),
            'symbol': symbol,
            'action': 'BUY',
            'quantity': quantity,
            'price': actual_price,
            'commission': commission,
            'pnl': 0.0,
        })
        
        return True
    
    def sell(self, symbol: str, quantity: float, price: float,
             timestamp: Optional[datetime] = None) -> bool:
        """
        卖出操作
        
        Args:
            symbol: 交易标的
            quantity: 卖出数量
            price: 卖出价格
            timestamp: 交易时间
        
        Returns:
            是否成功
        """
        if symbol not in self.positions:
            return False
        
        pos = self.positions[symbol]
        if quantity > pos['quantity']:
            return False
        
        # 加入滑点
        actual_price = price * (1 - self.slippage)
        revenue = actual_price * quantity
        
        # 手续费
        commission = revenue * self.commission_rate
        net_revenue = revenue - commission
        
        # 计算盈亏
        pnl = (actual_price - pos['avg_price']) * quantity - commission
        
        # 更新持仓
        pos['quantity'] -= quantity
        if pos['quantity'] <= 0:
            del self.positions[symbol]
        
        # 增加现金
        self.cash += net_revenue
        
        # 记录交易
        self.trades.append({
            'timestamp': timestamp or datetime.now(),
            'symbol': symbol,
            'action': 'SELL',
            'quantity': quantity,
            'price': actual_price,
            'commission': commission,
            'pnl': pnl,
        })
        
        return True
    
    def short(self, symbol: str, quantity: float, price: float,
              timestamp: Optional[datetime] = None) -> bool:
        """做空操作"""
        actual_price = price * (1 - self.slippage)
        revenue = actual_price * quantity
        commission = revenue * self.commission_rate
        
        if symbol in self.positions:
            pos = self.positions[symbol]
            if pos['direction'] == 1:
                return False  # 已有多头
        
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': quantity,
                'avg_price': actual_price,
                'direction': -1,
                'entry_time': timestamp or datetime.now(),
            }
        else:
            pos = self.positions[symbol]
            old_cost = pos['avg_price'] * pos['quantity']
            new_cost = actual_price * quantity
            pos['quantity'] += quantity
            pos['avg_price'] = (old_cost + new_cost) / pos['quantity'] if pos['quantity'] > 0 else 0
        
        self.cash += revenue - commission
        
        self.trades.append({
            'timestamp': timestamp or datetime.now(),
            'symbol': symbol,
            'action': 'SHORT',
            'quantity': quantity,
            'price': actual_price,
            'commission': commission,
            'pnl': 0.0,
        })
        
        return True
    
    def cover(self, symbol: str, quantity: float, price: float,
              timestamp: Optional[datetime] = None) -> bool:
        """平空操作"""
        if symbol not in self.positions:
            return False
        
        pos = self.positions[symbol]
        if pos['direction'] != -1:
            return False
        
        if quantity > pos['quantity']:
            return False
        
        actual_price = price * (1 + self.slippage)
        cost = actual_price * quantity
        commission = cost * self.commission_rate
        pnl = (pos['avg_price'] - actual_price) * quantity - commission
        
        pos['quantity'] -= quantity
        if pos['quantity'] <= 0:
            del self.positions[symbol]
        
        self.cash -= cost + commission
        
        self.trades.append({
            'timestamp': timestamp or datetime.now(),
            'symbol': symbol,
            'action': 'COVER',
            'quantity': quantity,
            'price': actual_price,
            'commission': commission,
            'pnl': pnl,
        })
        
        return True
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """获取指定标的的持仓信息"""
        return self.positions.get(symbol)
    
    def update_equity(self, timestamp, prices: Dict[str, float]):
        """更新权益曲线记录"""
        equity = self.cash + self._position_value(prices)
        self.equity_history.append((timestamp, equity))
    
    def get_equity_curve(self) -> pd.Series:
        """获取权益曲线"""
        if not self.equity_history:
            return pd.Series([self.initial_capital], index=[pd.Timestamp('2020-01-01')])
        
        timestamps, values = zip(*self.equity_history)
        return pd.Series(values, index=pd.DatetimeIndex(timestamps), name='equity')
    
    def get_trades_df(self) -> pd.DataFrame:
        """获取交易记录 DataFrame"""
        if not self.trades:
            return pd.DataFrame(columns=['timestamp', 'symbol', 'action', 'quantity', 'price', 'commission', 'pnl'])
        return pd.DataFrame(self.trades)
    
    def reset(self):
        """重置投资组合"""
        self.cash = self.initial_capital
        self.positions.clear()
        self.trades.clear()
        self.equity_history.clear()
