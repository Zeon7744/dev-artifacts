"""
Binance 数据连接器

获取加密货币市场数据
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .base import DataConnector


class BinanceConnector(DataConnector):
    """
    Binance 数据连接器
    
    获取加密货币市场数据。
    支持直接 API 调用或使用模拟数据。
    """
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self._session = None
    
    @property
    def name(self) -> str:
        return "Binance"
    
    def _get_session(self):
        if self._session is None:
            try:
                import requests
                self._session = requests.Session()
                if self.api_key:
                    self._session.headers.update({'X-MBX-APIKEY': self.api_key})
            except ImportError:
                pass
        return self._session
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str,
                   interval: str = 'daily') -> pd.DataFrame:
        """获取加密货币历史数据"""
        interval_map = {
            'daily': '1d',
            'weekly': '1w',
            'monthly': '1M',
            '1h': '1h',
            '4h': '4h',
        }
        binance_interval = interval_map.get(interval, '1d')
        
        # 尝试 API 调用
        session = self._get_session()
        if session:
            try:
                start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
                end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)
                
                url = f"{self.BASE_URL}/klines"
                params = {
                    'symbol': symbol.replace('/', '').upper(),
                    'interval': binance_interval,
                    'startTime': start_ts,
                    'endTime': end_ts,
                    'limit': 1000,
                }
                
                response = session.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_klines(data)
            except Exception as e:
                print(f"[Binance] API 调用失败: {e}，使用模拟数据")
        
        # 使用模拟数据
        from .mock_data import MockDataConnector
        mock = MockDataConnector(seed=42)
        return mock.fetch_data(symbol, start_date, end_date, interval)
    
    def _parse_klines(self, data: list) -> pd.DataFrame:
        """解析 Binance K 线数据"""
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['date'] = pd.to_datetime(df['open_time'], unit='ms')
        df = df.set_index('date')
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df = df[['open', 'high', 'low', 'close', 'volume']]
        return df
    
    def fetch_realtime(self, symbol: str) -> Dict:
        """获取最新价格"""
        session = self._get_session()
        if session:
            try:
                url = f"{self.BASE_URL}/ticker/price"
                params = {'symbol': symbol.replace('/', '').upper()}
                response = session.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'symbol': symbol,
                        'price': float(data['price']),
                        'timestamp': pd.Timestamp.now().isoformat(),
                    }
            except Exception:
                pass
        
        # 模拟数据
        from .mock_data import MockDataConnector
        mock = MockDataConnector()
        return mock.fetch_realtime(symbol)
