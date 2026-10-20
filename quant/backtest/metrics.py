"""
回测指标计算模块

计算策略绩效的各项关键指标：
- 收益率（总收益、年化收益）
- 夏普比率
- 最大回撤
- 波动率
- Sortino 比率
- Calmar 比率
- 胜率
- 盈亏比
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional


def calculate_returns(equity_curve: pd.Series) -> pd.Series:
    """计算收益率序列"""
    return equity_curve.pct_change().fillna(0)


def calculate_total_return(equity_curve: pd.Series) -> float:
    """计算总收益率"""
    if len(equity_curve) < 2:
        return 0.0
    return (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1.0


def calculate_annual_return(equity_curve: pd.Series, periods_per_year: int = 252) -> float:
    """计算年化收益率"""
    total_return = calculate_total_return(equity_curve)
    n_periods = len(equity_curve) - 1
    if n_periods <= 0:
        return 0.0
    return (1 + total_return) ** (periods_per_year / n_periods) - 1.0


def calculate_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """计算年化波动率"""
    if len(returns) < 2:
        return 0.0
    return returns.std() * np.sqrt(periods_per_year)


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0,
                           periods_per_year: int = 252) -> float:
    """
    计算夏普比率
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率（年化）
        periods_per_year: 每年的周期数
    
    Returns:
        夏普比率
    """
    if len(returns) < 2:
        return 0.0
    
    excess_returns = returns - risk_free_rate / periods_per_year
    volatility = calculate_volatility(returns, periods_per_year)
    
    if volatility == 0:
        return 0.0
    
    annual_return = calculate_annual_return(returns + 1, periods_per_year)
    sharpe = (annual_return - risk_free_rate) / volatility
    return sharpe


def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0,
                            periods_per_year: int = 252) -> float:
    """计算 Sortino 比率（只考虑下行波动）"""
    if len(returns) < 2:
        return 0.0
    
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(periods_per_year)
    
    if downside_std == 0:
        return 0.0
    
    annual_return = calculate_annual_return(returns + 1, periods_per_year)
    return (annual_return - risk_free_rate) / downside_std


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """
    计算最大回撤
    
    Returns:
        最大回撤（负值）
    """
    if len(equity_curve) < 2:
        return 0.0
    
    rolling_max = equity_curve.expanding().max()
    drawdown = (equity_curve - rolling_max) / rolling_max
    return drawdown.min()


def calculate_max_drawdown_duration(equity_curve: pd.Series) -> int:
    """计算最大回撤持续期（周期数）"""
    if len(equity_curve) < 2:
        return 0
    
    rolling_max = equity_curve.expanding().max()
    is_drawdown = equity_curve < rolling_max
    
    max_duration = 0
    current_duration = 0
    
    for dd in is_drawdown:
        if dd:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
        else:
            current_duration = 0
    
    return max_duration


def calculate_calmar_ratio(equity_curve: pd.Series, periods_per_year: int = 252) -> float:
    """计算 Calmar 比率（年化收益/最大回撤）"""
    annual_return = calculate_annual_return(equity_curve, periods_per_year)
    max_dd = abs(calculate_max_drawdown(equity_curve))
    
    if max_dd == 0:
        return 0.0
    
    return annual_return / max_dd


def calculate_win_rate(trades: pd.DataFrame) -> float:
    """
    计算胜率
    
    Args:
        trades: 交易记录 DataFrame，需包含 'pnl' 列
    """
    if len(trades) == 0:
        return 0.0
    
    winning_trades = (trades['pnl'] > 0).sum()
    return winning_trades / len(trades)


def calculate_profit_factor(trades: pd.DataFrame) -> float:
    """
    计算盈亏比（总盈利/总亏损）
    
    Args:
        trades: 交易记录 DataFrame，需包含 'pnl' 列
    """
    if len(trades) == 0:
        return 0.0
    
    gross_profit = trades[trades['pnl'] > 0]['pnl'].sum()
    gross_loss = abs(trades[trades['pnl'] < 0]['pnl'].sum())
    
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    
    return gross_profit / gross_loss


def calculate_trade_statistics(trades: pd.DataFrame) -> Dict:
    """计算交易统计信息"""
    if len(trades) == 0:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'max_win': 0.0,
            'max_loss': 0.0,
            'avg_trade_duration': 0.0,
        }
    
    winning = trades[trades['pnl'] > 0]
    losing = trades[trades['pnl'] < 0]
    
    stats = {
        'total_trades': len(trades),
        'winning_trades': len(winning),
        'losing_trades': len(losing),
        'win_rate': calculate_win_rate(trades),
        'avg_win': winning['pnl'].mean() if len(winning) > 0 else 0.0,
        'avg_loss': losing['pnl'].mean() if len(losing) > 0 else 0.0,
        'profit_factor': calculate_profit_factor(trades),
        'max_win': trades['pnl'].max(),
        'max_loss': trades['pnl'].min(),
        'total_pnl': trades['pnl'].sum(),
    }
    
    # 计算平均持仓时间
    if 'entry_time' in trades.columns and 'exit_time' in trades.columns:
        trades_copy = trades.copy()
        trades_copy['entry_time'] = pd.to_datetime(trades_copy['entry_time'])
        trades_copy['exit_time'] = pd.to_datetime(trades_copy['exit_time'])
        duration = (trades_copy['exit_time'] - trades_copy['entry_time']).dt.total_seconds() / 3600
        stats['avg_trade_duration'] = duration.mean()
    
    return stats


def calculate_metrics(equity_curve: pd.Series, trades: Optional[pd.DataFrame] = None,
                      risk_free_rate: float = 0.0, periods_per_year: int = 252) -> Dict:
    """
    计算所有回测指标
    
    Args:
        equity_curve: 权益曲线
        trades: 交易记录
        risk_free_rate: 无风险利率
        periods_per_year: 年化周期数
    
    Returns:
        包含所有指标的字典
    """
    returns = calculate_returns(equity_curve)
    
    metrics = {
        # 收益指标
        'total_return': calculate_total_return(equity_curve),
        'annual_return': calculate_annual_return(equity_curve, periods_per_year),
        
        # 风险指标
        'volatility': calculate_volatility(returns, periods_per_year),
        'max_drawdown': calculate_max_drawdown(equity_curve),
        'max_drawdown_duration': calculate_max_drawdown_duration(equity_curve),
        
        # 风险调整收益
        'sharpe_ratio': calculate_sharpe_ratio(returns, risk_free_rate, periods_per_year),
        'sortino_ratio': calculate_sortino_ratio(returns, risk_free_rate, periods_per_year),
        'calmar_ratio': calculate_calmar_ratio(equity_curve, periods_per_year),
        
        # 基本统计
        'start_date': str(equity_curve.index[0]),
        'end_date': str(equity_curve.index[-1]),
        'total_periods': len(equity_curve),
        'initial_capital': equity_curve.iloc[0],
        'final_capital': equity_curve.iloc[-1],
    }
    
    # 交易统计
    if trades is not None and len(trades) > 0:
        metrics['trade_stats'] = calculate_trade_statistics(trades)
    
    return metrics
