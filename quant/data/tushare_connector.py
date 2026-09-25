"""
Tushare 数据连接器

获取专业金融市场数据
"""

import pandas as pd
from typing import Dict, Optional
from .base import DataConnector


class TushareConnector(DataConnector):
    """
    Tushare 数据连接器
    
    获取专业级金融数据（需要 API Token）。
    需要安装: pip install tushare
    
    参数:
        token: Tushare API Token
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self._pro = None
        try:
            import tushare as ts
            if token:
                ts.set_token(token)
                self._pro = ts.pro_api()
        except ImportError:
            print("[Tushare] tushare 未安装，将使用模拟数据替代")
    
    @property
    def name(self) -> str:
        return "Tushare (专业数据)"
    
    @property
    def is_available(self) -> bool:
        return self._pro is not None
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str,
                   interval: str = 'daily') -> pd.DataFrame:
        """获取历史数据"""
        if self._pro is None:
            from .mock_data import MockDataConnector
            mock = MockDataConnector(seed=42)
            return mock.fetch_data(symbol, start_date, end_date, interval)
        
        try:
            ts_code = self._convert_symbol(symbol)
            
            df = self._pro.daily(
                ts_code=ts_code,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
            )
            
            if df is None or df.empty:
                raise ValueError(f"未获取到 {symbol} 的数据")
            
            column_map = {
                'trade_date': 'date',
                'vol': 'volume',
            }
            df = df.rename(columns=column_map)
            df = self.normalize_data(df)
            return df
            
        except Exception as e:
            print(f"[Tushare] 获取数据失败: {e}，使用模拟数据")
            from .mock_data import MockDataConnector
            mock = MockDataConnector(seed=42)
            return mock.fetch_data(symbol, start_date, end_date, interval)
    
    def fetch_realtime(self, symbol: str) -> Dict:
        """获取实时行情（Tushare 免费版不支持实时）"""
        from .mock_data import MockDataConnector
        mock = MockDataConnector()
        return mock.fetch_realtime(symbol)
    
    def _convert_symbol(self, symbol: str) -> str:
        """转换股票代码为 Tushare 格式"""
        if '.' in symbol:
            return symbol
        
        # 自动判断交易所
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        else:
            return f"{symbol}.SZ"
