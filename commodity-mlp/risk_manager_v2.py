"""
大宗商品MLP投资分析工具 - 增强版风险管理
支持止损止盈、熔断机制、动态仓位控制
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class PositionType(Enum):
    LONG = "long"
    SHORT = "short"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TradeSignal:
    signal: str  # buy, sell, hold
    confidence: float  # 0-1
    position_size: float  # 仓位比例
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@dataclass
class RiskMetrics:
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    risk_level: RiskLevel
    daily_pnl: float
    position_count: int

class RiskManager:
    """增强版风险管理引擎"""
    
    def __init__(
        self,
        initial_capital: float = 100000,
        max_position_size: float = 0.2,  # 最大单仓位20%
        stop_loss_pct: float = 0.05,  # 止损5%
        take_profit_pct: float = 0.15,  # 止盈15%
        max_daily_loss: float = 0.03,  # 日最大亏损3%
        max_open_positions: int = 5,
        volatility_target: float = 0.15,  # 目标波动率
    ):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_daily_loss = max_daily_loss
        self.max_open_positions = max_open_positions
        self.volatility_target = volatility_target
        
        self.positions: Dict[str, dict] = {}
        self.trade_history: List[dict] = []
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        
    def check_daily_limit(self) -> bool:
        """检查日亏损限额"""
        if self.daily_pnl <= -self.max_daily_loss * self.initial_capital:
            return False  # 触发熔断
        return True
    
    def calculate_position_size(self, signal: TradeSignal, price: float) -> float:
        """计算动态仓位大小"""
        # 基础仓位
        base_size = self.capital * self.max_position_size
        
        # 根据信号置信度调整
        confidence_adjustment = signal.confidence
        
        # 根据波动率调整（高波动降低仓位）
        volatility_adjustment = self.volatility_target / max(signal.confidence, 0.1)
        
        position_size = base_size * confidence_adjustment * volatility_adjustment
        
        # 限制最大仓位
        position_size = min(position_size, self.capital * self.max_position_size)
        
        return position_size
    
    def generate_signal(
        self,
        model_prediction: float,
        price: float,
        volatility: float
    ) -> TradeSignal:
        """生成交易信号"""
        # 根据预测值判断方向
        if model_prediction > 0.6:
            signal_type = "buy"
            confidence = model_prediction
        elif model_prediction < 0.4:
            signal_type = "sell"
            confidence = 1 - model_prediction
        else:
            return TradeSignal(
                signal="hold",
                confidence=model_prediction,
                position_size=0
            )
        
        # 计算止损止盈
        if signal_type == "buy":
            stop_loss = price * (1 - self.stop_loss_pct)
            take_profit = price * (1 + self.take_profit_pct)
        else:
            stop_loss = price * (1 + self.stop_loss_pct)
            take_profit = price * (1 - self.take_profit_pct)
        
        # 计算仓位
        position_size = self.calculate_position_size(
            TradeSignal(signal=signal_type, confidence=confidence, position_size=0),
            price
        )
        
        return TradeSignal(
            signal=signal_type,
            confidence=confidence,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    def execute_trade(
        self,
        symbol: str,
        signal: TradeSignal,
        price: float,
        quantity: int
    ) -> Optional[dict]:
        """执行交易"""
        # 检查每日限额
        if not self.check_daily_limit():
            return None
        
        # 检查持仓数量
        if signal.signal != "sell" and len(self.positions) >= self.max_open_positions:
            return None
        
        trade = {
            'symbol': symbol,
            'signal': signal.signal,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'timestamp': pd.Timestamp.now()
        }
        
        if signal.signal == "buy":
            self.positions[symbol] = {
                'entry_price': price,
                'quantity': quantity,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'entry_time': pd.Timestamp.now()
            }
            self.capital -= trade['value']
        elif signal.signal == "sell":
            if symbol in self.positions:
                position = self.positions.pop(symbol)
                pnl = (price - position['entry_price']) * quantity
                self.capital += trade['value']
                trade['pnl'] = pnl
                trade['closed'] = True
                
                if pnl < 0:
                    self.consecutive_losses += 1
                else:
                    self.consecutive_losses = 0
        
        self.trade_history.append(trade)
        return trade
    
    def check_stop_loss_take_profit(
        self,
        symbol: str,
        current_price: float
    ) -> Optional[TradeSignal]:
        """检查止损止盈"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        # 检查止损
        if position['stop_loss'] and current_price <= position['stop_loss']:
            return TradeSignal(
                signal="sell",
                confidence=0.9,
                position_size=position['quantity'] * position['entry_price'],
                stop_loss=None,
                take_profit=None
            )
        
        # 检查止盈
        if position['take_profit'] and current_price >= position['take_profit']:
            return TradeSignal(
                signal="sell",
                confidence=0.85,
                position_size=position['quantity'] * position['entry_price'],
                stop_loss=None,
                take_profit=None
            )
        
        return None
    
    def get_risk_metrics(self) -> RiskMetrics:
        """计算风险指标"""
        if not self.trade_history:
            return RiskMetrics(
                max_drawdown=0,
                sharpe_ratio=0,
                win_rate=0,
                profit_factor=0,
                risk_level=RiskLevel.LOW,
                daily_pnl=0,
                position_count=len(self.positions)
            )
        
        # 计算收益序列
        pnls = [t.get('pnl', 0) for t in self.trade_history if t.get('closed')]
        if not pnls:
            return RiskMetrics(
                max_drawdown=0,
                sharpe_ratio=0,
                win_rate=0,
                profit_factor=0,
                risk_level=RiskLevel.LOW,
                daily_pnl=self.daily_pnl,
                position_count=len(self.positions)
            )
        
        pnl_array = np.array(pnls)
        winning_trades = pnl_array[pnl_array > 0]
        losing_trades = pnl_array[pnl_array < 0]
        
        win_rate = len(winning_trades) / len(pnl_array) if len(pnl_array) > 0 else 0
        gross_profit = np.sum(winning_trades) if len(winning_trades) > 0 else 0
        gross_loss = abs(np.sum(losing_trades)) if len(losing_trades) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # 计算夏普比率
        if len(pnl_array) > 1 and np.std(pnl_array) > 0:
            sharpe = np.mean(pnl_array) / np.std(pnl_array) * np.sqrt(252)
        else:
            sharpe = 0
        
        # 估算最大回撤
        cumulative = np.cumsum(pnl_array)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
        
        # 判断风险等级
        if max_drawdown > self.initial_capital * 0.1 or self.consecutive_losses >= 3:
            risk_level = RiskLevel.CRITICAL
        elif max_drawdown > self.initial_capital * 0.05 or self.consecutive_losses >= 2:
            risk_level = RiskLevel.HIGH
        elif max_drawdown > self.initial_capital * 0.02:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return RiskMetrics(
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            win_rate=win_rate,
            profit_factor=profit_factor,
            risk_level=risk_level,
            daily_pnl=self.daily_pnl,
            position_count=len(self.positions)
        )
    
    def reset_daily(self):
        """重置每日状态"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0


if __name__ == "__main__":
    # 测试
    rm = RiskManager(initial_capital=100000)
    
    # 模拟交易
    for i in range(10):
        signal = TradeSignal(
            signal="buy" if i % 2 == 0 else "sell",
            confidence=0.7 if i % 2 == 0 else 0.6,
            position_size=20000,
            stop_loss=1800,
            take_profit=2100
        )
        trade = rm.execute_trade("GC=F", signal, 1950, 10)
        if trade:
            print(f"交易执行: {trade['signal']} {trade['quantity']} @ {trade['price']}")
    
    # 输出风险指标
    metrics = rm.get_risk_metrics()
    print(f"\n风险指标:")
    print(f"最大回撤: {metrics.max_drawdown:.2f}")
    print(f"夏普比率: {metrics.sharpe_ratio:.2f}")
    print(f"胜率: {metrics.win_rate:.2%}")
    print(f"风险等级: {metrics.risk_level.value}")
