"""
量化交易策略库 (Quantitative Trading Strategy Library)

一个完整的量化交易回测和策略开发框架
"""

__version__ = "1.0.0"
__author__ = "Zeon7744"

from .backtest.engine import BacktestEngine
from .backtest.portfolio import Portfolio
from .strategies.base import BaseStrategy
from .risk.manager import RiskManager
from .reports.performance import PerformanceReport

__all__ = [
    'BacktestEngine',
    'Portfolio',
    'BaseStrategy',
    'RiskManager',
    'PerformanceReport',
]
