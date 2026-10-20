#!/usr/bin/env python3
"""
Crypto Risk Manager - 高级风险管理模块

功能:
- 动态仓位管理（Kelly公式）
- 多层止损止盈
- 熔断机制
- 风险评级
- 组合风险控制
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Position:
    """仓位信息"""
    symbol: str
    size: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_pct: float
    open_time: float
    stop_loss: float
    take_profit: float


@dataclass
class RiskMetrics:
    """风险指标"""
    var_95: float  # 95% VaR
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    risk_level: RiskLevel


class CryptoRiskManager:
    """加密货币风险管理器"""
    
    def __init__(self, 
                 max_position_size: float = 0.20,
                 max_total_exposure: float = 0.80,
                 stop_loss_pct: float = 0.05,
                 take_profit_pct: float = 0.15,
                 trailing_stop: bool = True,
                 circuit_breaker: bool = True,
                 kelly_fraction: float = 0.25):
        """
        初始化风险管理器
        
        Args:
            max_position_size: 单币种最大仓位比例
            max_total_exposure: 总仓位上限
            stop_loss_pct: 止损比例
            take_profit_pct: 止盈比例
            trailing_stop: 是否启用追踪止损
            circuit_breaker: 是否启用熔断
            kelly_fraction: Kelly公式分数（实际使用为1/kelly_fraction）
        """
        self.max_position_size = max_position_size
        self.max_total_exposure = max_total_exposure
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop = trailing_stop
        self.circuit_breaker = circuit_breaker
        self.kelly_fraction = kelly_fraction
        
        self.positions: Dict[str, Position] = {}
        self.equity_curve: List[float] = []
        self.trade_history: List[Dict] = []
        
        # 熔断状态
        self.circuit_breaker_active = False
        self.last_circuit_breaker_time = None
        self.circuit_breaker_threshold = 0.10  # 10%回撤触发
    
    def calculate_Kelly_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        计算Kelly公式比例
        
        Args:
            win_rate: 胜率
            avg_win: 平均盈利
            avg_loss: 平均亏损
        
        Returns:
            Kelly比例
        """
        if win_rate <= 0.5 or avg_loss == 0:
            return 0.0
        
        b = avg_win / abs(avg_loss)  # 盈亏比
        p = win_rate
        q = 1 - p
        
        kelly = p - q / b
        return max(0, min(kelly, 0.25))  # 限制最大25%
    
    def calculate_position_size(self,
                                symbol: str,
                                account_balance: float,
                                win_rate: float,
                                profit_factor: float,
                                volatility: float = 0.02) -> float:
        """
        计算最佳仓位大小（Kelly公式）
        
        Args:
            symbol: 交易币种
            account_balance: 账户余额
            win_rate: 胜率
            profit_factor: 盈亏比
            volatility: 波动率
        
        Returns:
            建议仓位比例
        """
        # Kelly公式
        if win_rate <= 0.5 or profit_factor <= 0:
            kelly = 0
        else:
            b = profit_factor
            p = win_rate
            q = 1 - p
            kelly = p - q / b
        
        # 实际应用为1/kelly_fraction
        adjusted_kelly = kelly * self.kelly_fraction
        
        # 波动率调整（高波动降低仓位）
        vol_adjustment = max(0.5, 1 - volatility * 5)
        
        # 综合仓位计算
        position_size = min(adjusted_kelly, self.max_position_size) * vol_adjustment
        position_size = max(0, min(position_size, self.max_position_size))
        
        position_value = position_size * account_balance
        
        logger.debug(f"{symbol} 仓位计算: Kelly={kelly:.2%}, 调整后={position_size:.2%}, 金额={position_value:.2f}")
        
        return position_size
    
    def calculate_dynamic_stop_loss(self,
                                     entry_price: float,
                                     volatility: float,
                                     signal_type: SignalType) -> Tuple[float, float]:
        """
        计算动态止损止盈
        
        Args:
            entry_price: 入场价格
            volatility: 波动率（ATR）
            signal_type: 信号类型
        
        Returns:
            (止损价格, 止盈价格)
        """
        atr_multiplier = 2.0
        
        if signal_type == SignalType.BUY:
            stop_loss = entry_price - volatility * atr_multiplier
            take_profit = entry_price + volatility * atr_multiplier * 3  # 风险收益比1:3
        else:
            stop_loss = entry_price + volatility * atr_multiplier
            take_profit = entry_price - volatility * atr_multiplier * 3
        
        return stop_loss, take_profit
    
    def update_trailing_stop(self, position: Position, current_price: float,
                             highest_price: float = None) -> Optional[float]:
        """
        更新追踪止损
        
        Returns:
            新的止损价格，如果不变返回None
        """
        if not self.trailing_stop or highest_price is None:
            return None
        
        # 追踪止损距离
        trail_distance = position.stop_loss * 0.1  # 10%距离
        
        if position is None:
            new_stop = highest_price - trail_distance
        else:
            new_stop = highest_price - trail_distance
        
        # 只有提高止损才更新
        if position is None or new_stop > position.stop_loss:
            return new_stop
        
        return None
    
    def check_circuit_breaker(self, current_drawdown: float) -> bool:
        """
        检查是否触发熔断
        
        Args:
            current_drawdown: 当前回撤
        
        Returns:
            是否触发熔断
        """
        if not self.circuit_breaker:
            return False
        
        if abs(current_drawdown) >= self.circuit_breaker_threshold:
            if self.last_circuit_breaker_time is None or \
               (pd.Timestamp.now() - self.last_circuit_breaker_time).total_seconds() > 3600:
                self.circuit_breaker_active = True
                self.last_circuit_breaker_time = pd.Timestamp.now()
                logger.warning(f"熔断触发！当前回撤: {current_drawdown:.2%}")
                return True
        
        return False
    
    def assess_risk_level(self,
                          portfolio_value: float,
                          unrealized_pnl: float,
                          max_drawdown: float,
                          volatility: float) -> RiskLevel:
        """
        评估整体风险等级
        
        Returns:
            风险等级
        """
        drawdown_pct = unrealized_pnl / portfolio_value if portfolio_value > 0 else 0
        
        # 综合评分
        score = 0
        score += abs(drawdown_pct) * 100  # 回撤权重
        score += volatility * 50  # 波动率权重
        score += max(abs(max_drawdown) * 100, 0)  # 最大回撤权重
        
        if score < 20:
            return RiskLevel.LOW
        elif score < 40:
            return RiskLevel.MEDIUM
        elif score < 60:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        计算VaR（风险价值）
        
        Args:
            returns: 收益率序列
            confidence: 置信水平
        
        Returns:
            VaR值
        """
        var = np.percentile(returns, (1 - confidence) * 100)
        return abs(var)
    
    def calculate_risk_metrics(self, returns: pd.Series, 
                                risk_free_rate: float = 0.02) -> RiskMetrics:
        """
        计算综合风险指标
        
        Returns:
            RiskMetrics对象
        """
        # 确保是pandas Series
        if isinstance(returns, np.ndarray):
            returns = pd.Series(returns)
        
        if len(returns) < 2:
            return RiskMetrics(0, 0, 0, 0, 0, RiskLevel.LOW)
        
        # VaR
        var_95 = self.calculate_var(returns)
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 夏普比率
        excess_returns = returns - risk_free_rate / 252  # 日度
        sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0
        
        # Sortino比率
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino = np.sqrt(252) * returns.mean() / downside_std if downside_std > 0 else 0
        
        # Calmar比率
        calmar = returns.mean() * 252 / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 风险评级
        risk_score = abs(max_drawdown) * 100 + var_95 * 50 + (1 - sharpe / 2) * 20
        if risk_score < 20:
            risk_level = RiskLevel.LOW
        elif risk_score < 40:
            risk_level = RiskLevel.MEDIUM
        elif risk_score < 60:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        return RiskMetrics(var_95, max_drawdown, sharpe, sortino, calmar, risk_level)
    
    def generate_trade_signal(self,
                              prediction: str,
                              confidence: float,
                              volatility: float,
                              current_position: Optional[Position] = None,
                              account_balance: float = 10000,
                              win_rate: float = 0.6,
                              profit_factor: float = 1.5) -> Dict:
        """
        生成交易信号
        
        Returns:
            包含action, size, stop_loss, take_profit等信息的字典
        """
        signal = {
            'action': SignalType.HOLD.value,
            'confidence': confidence,
            'position_size': 0,
            'stop_loss': None,
            'take_profit': None,
            'reason': '',
            'risk_level': RiskLevel.LOW.value
        }
        
        # 检查熔断
        if self.circuit_breaker_active:
            signal['reason'] = '熔断保护中，暂停交易'
            return signal
        
        # 根据预测生成信号
        if prediction == 'up' and confidence > 0.6:
            signal['action'] = SignalType.BUY.value
            position_size = self.calculate_position_size(
                'BTC', account_balance, win_rate, profit_factor, volatility
            )
            signal['position_size'] = position_size
            
            # 计算止损止盈
            # 假设当前价格为1（标准化），实际使用时需传入真实价格
            entry_price = 1.0
            stop, take = self.calculate_dynamic_stop_loss(
                entry_price, volatility, SignalType.BUY
            )
            signal['stop_loss'] = stop
            signal['take_profit'] = take
            
            signal['reason'] = f'上涨信号，置信度{confidence:.1%}'
            
        elif prediction == 'down' and confidence > 0.6:
            signal['action'] = SignalType.SELL.value
            position_size = self.calculate_position_size(
                'BTC', account_balance, win_rate, profit_factor, volatility
            )
            signal['position_size'] = position_size
            
            entry_price = 1.0
            stop, take = self.calculate_dynamic_stop_loss(
                entry_price, volatility, SignalType.SELL
            )
            signal['stop_loss'] = stop
            signal['take_profit'] = take
            
            signal['reason'] = f'下跌信号，置信度{confidence:.1%}'
        
        else:
            signal['action'] = SignalType.HOLD.value
            signal['reason'] = '无明确信号或置信度不足'
        
        # 风险评估
        risk = self.assess_risk_level(account_balance, 0, 0, volatility)
        signal['risk_level'] = risk.value
        
        return signal

    def test_signal(self) -> Dict:
        """测试生成交易信号"""
        return self.generate_trade_signal(
            prediction='up',
            confidence=0.75,
            volatility=0.02,
            account_balance=10000
        )


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    manager = CryptoRiskManager()
    
    # 测试仓位计算
    size = manager.calculate_position_size(
        'BTC', 10000, win_rate=0.65, profit_factor=1.8, volatility=0.03
    )
    print(f"建议仓位: {size:.2%}")
    
    # 测试交易信号生成
    signal = manager.generate_trade_signal(
        prediction='up',
        confidence=0.75,
        volatility=0.025,
        account_balance=10000
    )
    print(f"交易信号: {signal}")
    
    # 测试风险指标计算
    returns = pd.Series(np.random.randn(100) * 0.02)
    metrics = manager.calculate_risk_metrics(returns)
    print(f"风险指标: VaR={metrics.var_95:.2%}, 最大回撤={metrics.max_drawdown:.2%}, 夏普={metrics.sharpe_ratio:.2f}")
