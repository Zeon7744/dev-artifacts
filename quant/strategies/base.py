"""
策略基类模块

所有交易策略的抽象基类，定义统一的策略接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd


class BaseStrategy(ABC):
    """
    策略基类
    
    所有交易策略必须继承此基类并实现以下方法：
    - name: 策略名称
    - init(): 初始化策略参数
    - generate_signals(): 生成交易信号
    
    Attributes:
        name: 策略名称
        params: 策略参数字典
        signals: 生成的信号列表
    """
    
    def __init__(self, **params):
        """
        初始化策略
        
        Args:
            **params: 策略参数
        """
        self.params = params
        self.signals: List[Dict] = []
        self._indicators: Dict[str, pd.Series] = {}
        self.init()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    def description(self) -> str:
        """策略描述"""
        return f"{self.name} 策略"
    
    def init(self):
        """
        初始化策略参数
        子类可以重写此方法设置默认参数
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 市场数据 DataFrame（至少包含 'close' 列）
        
        Returns:
            DataFrame，包含 'signal' 列：
            - 1: 买入信号
            - -1: 卖出信号
            - 0: 持仓不变
        """
        pass
    
    def on_bar(self, bar: pd.Series, index: int, data: pd.DataFrame) -> int:
        """
        单 bar 处理（可选实现）
        
        用于逐 bar 回测模式。默认使用 generate_signals 的结果。
        
        Args:
            bar: 当前 bar 数据
            index: 当前 bar 索引
            data: 完整数据（到当前 bar）
        
        Returns:
            信号值 (1=买入, -1=卖出, 0=无操作)
        """
        if index < len(self.signals):
            return self.signals[index].get('signal', 0)
        return 0
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算技术指标
        
        子类可重写此方法计算策略所需的技术指标。
        
        Args:
            data: 市场数据
        
        Returns:
            指标名称到 Series 的映射
        """
        return {}
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取当前策略参数"""
        return self.params.copy()
    
    def set_parameters(self, **params):
        """更新策略参数"""
        self.params.update(params)
        self.init()
    
    def _calculate_sma(self, series: pd.Series, period: int) -> pd.Series:
        """计算简单移动平均线"""
        return series.rolling(window=period).mean()
    
    def _calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均线"""
        return series.ewm(span=period, adjust=False).mean()
    
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """
        计算 RSI 指标
        
        Args:
            series: 价格序列
            period: RSI 周期
        
        Returns:
            RSI 值序列
        """
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, series: pd.Series, 
                        fast: int = 12, slow: int = 26, signal: int = 9):
        """
        计算 MACD 指标
        
        Returns:
            (macd_line, signal_line, histogram)
        """
        ema_fast = self._calculate_ema(series, fast)
        ema_slow = self._calculate_ema(series, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, series: pd.Series, 
                                    period: int = 20, num_std: float = 2.0):
        """
        计算布林带
        
        Returns:
            (upper, middle, lower)
        """
        middle = self._calculate_sma(series, period)
        std = series.rolling(window=period).std()
        upper = middle + num_std * std
        lower = middle - num_std * std
        return upper, middle, lower
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算 ATR（平均真实波幅）
        
        Args:
            data: 包含 high, low, close 列的 DataFrame
        
        Returns:
            ATR 序列
        """
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)
        
        tr = pd.concat([
            high - low,
            (high - close).abs(),
            (low - close).abs()
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        return atr
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(params={self.params})"
