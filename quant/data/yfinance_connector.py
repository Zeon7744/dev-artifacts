"""
YFinance 数据连接器

通过 yfinance 库获取美股和国际市场数据
"""

import pandas as pd
from typing import Dict, Optional
from .base import DataConnector


class YFinanceConnector(DataConnector):
    """
    Yahoo Finance 数据连接器
    
    使用 yfinance 获取全球股票市场数据。
    需要安装: pip install yfinance
    
    注意: 如果 yfinance 不可用，将使用模拟数据。
    """
    
    def __init__(self):
        self._yf = None
        try:
            import yfinance as yf
            self._yf = yf
        except ImportError:
            print("[YFinance] yfinance 未安装，将使用模拟数据替代")
    
    @property
    def name(self) -> str:
        return "Yahoo Finance"
    
    @property
    def is_available(self) -> bool:
        return self._yf is not None
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str,
                   interval: str = 'daily') -> pd.DataFrame:
        """获取历史数据"""
        if self._yf is None:
            from .mock_data import MockDataConnector
            mock = MockDataConnector(seed=42)
            return mock.fetch_data(symbol, start_date, end_date, interval)
        
        interval_map = {
            'daily': '1d',
            'weekly': '1wk',
            'monthly': '1mo',
            '1h': '1h',
            '4h': '1h',  # yfinance 不支持 4h，用 1h 后聚合
        }
        yf_interval = interval_map.get(interval, '1d')
        
        try:
            ticker = self._yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=yf_interval)
            
            if df.empty:
                raise ValueError(f"未获取到 {symbol} 的数据")
            
            df = self.normalize_data(df)
            return df
        except Exception as e:
            print(f"[YFinance] 获取数据失败: {e}，使用模拟数据")
            from .mock_data import MockDataConnector
            mock = MockDataConnector(seed=42)
            return mock.fetch_data(symbol, start_date, end_date, interval)
    
    def fetch_realtime(self, symbol: str) -> Dict:
        """获取最新价格"""
        if self._yf is None:
            from .mock_data import MockDataConnector
            mock = MockDataConnector()
            return mock.fetch_realtime(symbol)
        
        try:
            ticker = self._yf.Ticker(symbol)
            info = ticker.fast_info
            return {
                'symbol': symbol,
                'price': getattr(info, 'last_price', None),
                'volume': getattr(info, 'last_volume', None),
                'market_cap': getattr(info, 'market_cap', None),
                'timestamp': pd.Timestamp.now().isoformat(),
            }
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def fetch_multiple(self, symbols: list, start_date: str, end_date: str,
                       interval: str = 'daily') -> Dict[str, pd.DataFrame]:
        """批量获取多个标的的数据"""
        results = {}
        for symbol in symbols:
            try:
                df = self.fetch_data(symbol, start_date, end_date, interval)
                results[symbol] = df
            except Exception as e:
                print(f"[YFinance] {symbol} 获取失败: {e}")
        return results
