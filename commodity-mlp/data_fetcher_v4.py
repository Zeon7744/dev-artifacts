"""
大宗商品MLP投资分析工具 - v4增强版数据获取
支持多种数据源：yfinance、Akshare、CSV/Excel导入、本地缓存
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
import os
import json
import pickle
warnings.filterwarnings('ignore')

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 商品配置
COMMODITY_CONFIG = {
    'GC=F': {'name': '黄金', 'unit': 'USD/oz', 'base_price': 1950},
    'CL=F': {'name': '原油', 'unit': 'USD/bbl', 'base_price': 80},
    'SI=F': {'name': '白银', 'unit': 'USD/oz', 'base_price': 23},
    'HG=F': {'name': '铜', 'unit': 'USD/lb', 'base_price': 3.8},
    'NG=F': {'name': '天然气', 'unit': 'USD/MMBtu', 'base_price': 2.5},
}

class CommodityDataFetcher:
    """大宗商品数据获取器 - 多源支持v4"""
    
    def __init__(self, primary_source: str = 'yfinance', cache_enabled: bool = True):
        self.primary_source = primary_source
        self.cache_enabled = cache_enabled
        self.cache: Dict[str, pd.DataFrame] = {}
        self._load_cache()
        
    def _get_cache_path(self, symbol: str, source: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(CACHE_DIR, f"{symbol}_{source}_data.pkl")
    
    def _load_cache(self):
        """加载所有缓存"""
        if not self.cache_enabled:
            return
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('_data.pkl'):
                try:
                    with open(os.path.join(CACHE_DIR, filename), 'rb') as f:
                        cache_data = pickle.load(f)
                        symbol = filename.split('_')[0]
                        self.cache[symbol] = cache_data
                except:
                    pass
    
    def _save_cache(self, symbol: str, data: pd.DataFrame):
        """保存缓存"""
        if not self.cache_enabled:
            return
        cache_path = self._get_cache_path(symbol, self.primary_source)
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        self.cache[symbol] = data
    
    def get_data(self, symbol: str, days: int = 800) -> pd.DataFrame:
        """获取数据，自动选择最佳数据源"""
        if symbol in self.cache:
            cached = self.cache[symbol]
            if len(cached) >= days * 0.8:  # 缓存足够新
                return cached
        
        # 尝试主数据源
        data = None
        if self.primary_source == 'yfinance':
            data = self._fetch_yfinance(symbol, days)
        elif self.primary_source == 'akshare':
            data = self._fetch_akshare(symbol, days)
        
        # 如果主数据源失败，尝试备用
        if data is None or len(data) < days * 0.5:
            if self.primary_source == 'yfinance':
                data = self._fetch_akshare(symbol, days)
            else:
                data = self._fetch_yfinance(symbol, days)
        
        # 最后使用模拟数据
        if data is None or len(data) < 100:
            data = self.generate_simulated_data(symbol, days)
        
        if self.cache_enabled:
            self._save_cache(symbol, data)
        
        return data
    
    def _fetch_yfinance(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """从Yahoo Finance获取数据"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d")
            if len(df) > 0:
                df = df.reset_index()
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            print(f"Yahoo Finance获取失败: {e}")
        return None
    
    def _fetch_akshare(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """从Akshare获取数据"""
        try:
            import akshare as ak
            # 尝试获取期货数据
            if symbol == 'GC=F':
                df = ak.futures_main_sina(symbol="黄金")
            elif symbol == 'CL=F':
                df = ak.futures_main_sina(symbol="原油期货")
            elif symbol == 'SI=F':
                df = ak.futures_main_sina(symbol="白银")
            elif symbol == 'HG=F':
                df = ak.futures_main_sina(symbol="铜期货")
            else:
                return None
            
            if len(df) > 0:
                df = df.rename(columns={
                    '日期': 'Date',
                    '开盘': 'Open',
                    '最高': 'High',
                    '最低': 'Low',
                    '收盘': 'Close',
                    '成交量': 'Volume'
                })
                df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                df = df.tail(days)
                return df
        except ImportError:
            print("Akshare未安装，跳过")
        except Exception as e:
            print(f"Akshare获取失败: {e}")
        return None
    
    def generate_simulated_data(self, symbol: str, days: int = 800, seed: Optional[int] = None) -> pd.DataFrame:
        """生成模拟大宗商品数据（含趋势和波动聚集）"""
        if symbol not in COMMODITY_CONFIG:
            raise ValueError(f"不支持的商品代码: {symbol}")
        
        config = COMMODITY_CONFIG[symbol]
        base_price = config['base_price']
        
        if seed is None:
            seed = sum(ord(c) * (i + 1) for i, c in enumerate(symbol)) % (2**32)
        
        np.random.seed(seed)
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
        
        # 生成带趋势和波动聚集的价格
        returns = np.zeros(days)
        volatility = np.zeros(days)
        
        current_vol = 0.02
        for i in range(days):
            # GARCH-like volatility clustering
            volatility[i] = 0.9 * volatility[i-1] + 0.1 * (returns[i-1]**2 if i > 0 else 0.0004)
            returns[i] = np.random.normal(0.0002, volatility[i])
        
        # 添加趋势
        trend = np.linspace(0, np.random.uniform(-0.1, 0.1), days)
        total_returns = returns + trend / days
        
        prices = base_price * np.exp(np.cumsum(total_returns))
        
        df = pd.DataFrame({
            'Date': dates.strftime('%Y-%m-%d'),
            'Open': prices * (1 + np.random.normal(0, 0.001, days)),
            'High': prices * (1 + np.abs(np.random.normal(0, 0.005, days))),
            'Low': prices * (1 - np.abs(np.random.normal(0, 0.005, days))),
            'Close': prices,
            'Volume': np.random.randint(100000, 1000000, days)
        })
        
        return df
    
    def import_from_file(self, filepath: str) -> pd.DataFrame:
        """从CSV/Excel文件导入数据"""
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.csv':
            df = pd.read_csv(filepath)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        # 标准化列名
        column_map = {
            'date': 'Date', '时间': 'Date', '日期': 'Date',
            'open': 'Open', '开盘': 'Open',
            'high': 'High', '最高': 'High',
            'low': 'Low', '最低': 'Low',
            'close': 'Close', '收盘': 'Close',
            'volume': 'Volume', '成交量': 'Volume'
        }
        
        df = df.rename(columns=lambda x: column_map.get(str(x).strip().lower(), x))
        
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"缺少必要列: {missing}")
        
        df = df[required_cols]
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        return df
    
    def batch_import(self, filepaths: List[str]) -> Dict[str, pd.DataFrame]:
        """批量导入多个文件"""
        result = {}
        for fp in filepaths:
            try:
                symbol = os.path.splitext(os.path.basename(fp))[0]
                result[symbol] = self.import_from_file(fp)
            except Exception as e:
                print(f"导入失败 {fp}: {e}")
        return result


if __name__ == "__main__":
    # 测试
    fetcher = CommodityDataFetcher(primary_source='yfinance')
    
    print("测试数据获取...")
    df = fetcher.get_data('GC=F', days=30)
    print(f"获取到 {len(df)} 条数据")
    print(df.tail())
    
    print("\n测试缓存...")
    df2 = fetcher.get_data('GC=F', days=30)
    print(f"从缓存获取: {len(df2)} 条数据")
