"""
AKShare 数据连接器

获取 A 股和中国金融市场数据
"""

import pandas as pd
from typing import Dict, Optional
from .base import DataConnector


class AKShareConnector(DataConnector):
    """
    AKShare 数据连接器
    
    获取 A 股、期货、基金等中国市场数据。
    需要安装: pip install akshare
    """
    
    def __init__(self):
        self._ak = None
        try:
            import akshare as ak
            self._ak = ak
        except ImportError:
            print("[AKShare] akshare 未安装，将使用模拟数据替代")
    
    @property
    def name(self) -> str:
        return "AKShare (A股)"
    
    @property
    def is_available(self) -> bool:
        return self._ak is not None
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str,
                   interval: str = 'daily') -> pd.DataFrame:
        """获取 A 股历史数据"""
        if self._ak is None:
            from .mock_data import MockDataConnector
            mock = MockDataConnector(seed=42)
            return mock.fetch_data(symbol, start_date, end_date, interval)
        
        try:
            # AKShare 获取 A 股日线数据
            df = self._ak.stock_zh_a_hist(
                symbol=symbol,
                period='daily',
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust='qfq'  # 前复权
            )
            
            if df.empty:
                raise ValueError(f"未获取到 {symbol} 的数据")
            
            # 标准化列名
            column_map = {
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
            }
            df = df.rename(columns=column_map)
            df = self.normalize_data(df)
            return df
            
        except Exception as e:
            print(f"[AKShare] 获取数据失败: {e}，使用模拟数据")
            from .mock_data import MockDataConnector
            mock = MockDataConnector(seed=42)
            return mock.fetch_data(symbol, start_date, end_date, interval)
    
    def fetch_realtime(self, symbol: str) -> Dict:
        """获取 A 股实时行情"""
        if self._ak is None:
            from .mock_data import MockDataConnector
            mock = MockDataConnector()
            return mock.fetch_realtime(symbol)
        
        try:
            df = self._ak.stock_zh_a_spot_em()
            row = df[df['代码'] == symbol]
            if not row.empty:
                row = row.iloc[0]
                return {
                    'symbol': symbol,
                    'price': float(row.get('最新价', 0)),
                    'volume': float(row.get('成交量', 0)),
                    'name': row.get('名称', ''),
                    'timestamp': pd.Timestamp.now().isoformat(),
                }
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
        
        return {'symbol': symbol, 'error': '未找到'}
