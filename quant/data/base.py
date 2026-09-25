"""
数据连接器基类

定义统一的数据获取接口
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Dict, List


class DataConnector(ABC):
    """
    数据连接器抽象基类
    
    所有数据源连接器必须实现 fetch_data 方法。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        pass
    
    @abstractmethod
    def fetch_data(self, symbol: str, start_date: str, end_date: str,
                   interval: str = 'daily') -> pd.DataFrame:
        """
        获取历史数据
        
        Args:
            symbol: 交易标的
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            interval: 数据频率 'daily'/'weekly'/'monthly'/'1h'/'4h'
        
        Returns:
            DataFrame 包含列: date, open, high, low, close, volume
        """
        pass
    
    @abstractmethod
    def fetch_realtime(self, symbol: str) -> Dict:
        """
        获取实时数据
        
        Args:
            symbol: 交易标的
        
        Returns:
            包含最新价格和成交量的字典
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """验证数据格式"""
        required_columns = ['open', 'high', 'low', 'close']
        return all(col in df.columns for col in required_columns)
    
    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        df = df.copy()
        
        # 确保有 datetime 索引
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            elif 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
        
        # 统一列名为小写
        df.columns = [col.lower() for col in df.columns]
        
        # 确保必需列存在
        required = ['open', 'high', 'low', 'close']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"缺少必需列: {col}")
        
        if 'volume' not in df.columns:
            df['volume'] = 0
        
        # 排序
        df = df.sort_index()
        
        return df
