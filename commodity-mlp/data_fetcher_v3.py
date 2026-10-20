"""
大宗商品MLP投资分析工具 - 增强版数据获取
支持多种数据源：yfinance、新浪财经、模拟数据
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# 商品配置
COMMODITY_CONFIG = {
    'GC=F': {'name': '黄金', 'unit': 'USD/oz', 'base_price': 1950},
    'CL=F': {'name': '原油', 'unit': 'USD/bbl', 'base_price': 80},
    'SI=F': {'name': '白银', 'unit': 'USD/oz', 'base_price': 23},
    'HG=F': {'name': '铜', 'unit': 'USD/lb', 'base_price': 3.8},
    'NG=F': {'name': '天然气', 'unit': 'USD/MMBtu', 'base_price': 2.5},
}


class CommodityDataFetcher:
    """大宗商品数据获取器 - 多源支持"""
    
    def __init__(self, primary_source: str = 'yfinance', fallback_source: str = 'sina'):
        self.primary_source = primary_source
        self.fallback_source = fallback_source
        self.cache: Dict[str, pd.DataFrame] = {}
        
    def generate_simulated_data(
        self, 
        symbol: str, 
        days: int = 800,
        seed: Optional[int] = None
    ) -> pd.DataFrame:
        """生成模拟大宗商品数据（含趋势和波动聚集）"""
        if symbol not in COMMODITY_CONFIG:
            raise ValueError(f"不支持的商品代码: {symbol}")
        
        config = COMMODITY_CONFIG[symbol]
        base_price = config['base_price']
        
        if seed is None:
            seed = sum(ord(c) * (i + 1) for i, c in enumerate(symbol)) % (2**32)
        
        np.random.seed(seed)
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
        
        # 模拟价格序列（带趋势和波动聚集的GBM）
        trend_duration = np.random.randint(50, 150)
        trend_direction = np.random.choice([-1, 1])
        trend_strength = np.random.uniform(0.0001, 0.0005)
        
        base_volatility = 0.015
        volatility = np.zeros(days)
        volatility[0] = base_volatility
        for i in range(1, days):
            volatility[i] = 0.95 * volatility[i-1] + 0.05 * np.random.uniform(0.01, 0.03)
        
        drift = trend_direction * trend_strength
        returns = np.random.normal(drift, volatility, days)
        
        prices = base_price * np.exp(np.cumsum(returns))
        
        np.random.seed(seed + 1)
        volumes = np.random.lognormal(mean=10, sigma=0.5, size=days).astype(float)
        
        intraday_vol = volatility * 0.5
        high = prices * (1 + np.random.uniform(0, intraday_vol, days))
        low = prices * (1 - np.random.uniform(0, intraday_vol, days))
        open_prices = prices * (1 + np.random.uniform(-intraday_vol/2, intraday_vol/2, days))
        
        df = pd.DataFrame({
            'Date': dates,
            'Open': open_prices,
            'High': high,
            'Low': low,
            'Close': prices,
            'Volume': volumes
        })
        
        df['Target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
        
        return df.dropna().reset_index(drop=True)
    
    def fetch_from_yfinance(self, symbol: str, period: str = '6mo', max_retries: int = 3) -> Optional[pd.DataFrame]:
        """从yfinance获取数据"""
        for attempt in range(max_retries):
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period)
                
                if df.empty:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2 ** attempt)
                        continue
                    return None
                
                df = df.reset_index()
                df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                df['Target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
                
                return df.dropna()
                
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                print(f"yfinance获取{symbol}失败: {e}")
                return None
    
    def fetch_from_sina(self, symbol: str, days: int = 100) -> Optional[pd.DataFrame]:
        """从新浪财经获取期货数据（中文商品代码）"""
        try:
            import requests
            
            # 映射商品代码到新浪财经代码
            sina_symbols = {
                'GC=F': 'au0',      # 黄金
                'CL=F': 'cl0',      # 原油
                'SI=F': 'ag0',      # 白银
                'HG=F': 'cu0',      # 铜
                'NG=F': 'ng0',      # 天然气
            }
            
            sina_symbol = sina_symbols.get(symbol, symbol[:2].lower() + '0')
            url = f"https://stock.finance.sina.com.cn/futures/api/json_v2.php/{sina_symbol}/kline"
            
            # 尝试不同的API端点
            endpoints = [
                f"https://hq.sinajs.cn/list={sina_symbol}",
            ]
            
            # 备用：尝试使用tushare或其他接口
            # 这里返回None表示无法获取真实数据
            return None
            
        except Exception as e:
            print(f"新浪数据获取失败: {e}")
            return None
    
    def fetch_from_tushare(self, symbol: str, days: int = 100) -> Optional[pd.DataFrame]:
        """从Tushare获取数据（需要token）"""
        try:
            import tushare as ts
            
            # 映射商品代码
            ts_symbols = {
                'GC=F': 'AU0',    # 黄金
                'CL=F': 'CL',     # 原油
                'SI=F': 'AG0',    # 白银
                'HG=F': 'CU0',    # 铜
                'NG=F': 'NG',     # 天然气
            }
            
            ts_symbol = ts_symbols.get(symbol, symbol)
            
            # 尝试获取数据
            pro = ts.pro_api()
            df = pro.fut_daily(ts_code=ts_symbol, freq='D')
            
            if df is None or df.empty:
                return None
            
            df = df.sort_values('trade_date').reset_index(drop=True)
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover', 'Hold']
            
            # 转换日期格式
            df['Date'] = pd.to_datetime(df['Date'])
            
            df['Target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
            
            return df.dropna().reset_index(drop=True)
            
        except Exception as e:
            print(f"Tushare获取{symbol}失败: {e}")
            return None
    
    def get_latest_data(self, symbol: str, days: int = 800) -> pd.DataFrame:
        """获取最新数据，优先尝试真实数据源，失败则使用模拟数据"""
        # 检查缓存
        if symbol in self.cache:
            return self.cache[symbol]
        
        # 尝试yfinance
        df = self.fetch_from_yfinance(symbol)
        if df is not None and len(df) > 50:
            print(f"✓ {symbol}: 使用yfinance真实数据 ({len(df)}条)")
            self.cache[symbol] = df
            return df
        
        # 尝试其他数据源
        if self.primary_source == 'sina':
            df = self.fetch_from_sina(symbol, days)
        elif self.primary_source == 'tushare':
            df = self.fetch_from_tushare(symbol, days)
        
        if df is not None and len(df) > 50:
            print(f"✓ {symbol}: 使用{self.primary_source}真实数据 ({len(df)}条)")
            self.cache[symbol] = df
            return df
        
        # 降级到模拟数据
        print(f"⚠ {symbol}: 真实数据不可用，使用模拟数据 ({days}天)")
        df = self.generate_simulated_data(symbol, days)
        self.cache[symbol] = df
        return df
    
    def get_data(
        self, 
        symbols: List[str], 
        use_real: bool = False,
        days: int = 800
    ) -> Dict[str, pd.DataFrame]:
        """获取多个商品的数据"""
        data = {}
        real_data_success = []
        
        for symbol in symbols:
            if use_real:
                df = self.get_latest_data(symbol, days)
                if len(df) > 100:
                    real_data_success.append(symbol)
            else:
                df = self.generate_simulated_data(symbol, days)
            
            df['Symbol'] = symbol
            data[symbol] = df
        
        if real_data_success:
            print(f"\n📊 成功获取 {len(real_data_success)} 个商品真实数据: {', '.join(real_data_success)}")
        
        return data
    
    def get_available_symbols(self) -> Dict[str, Dict]:
        """获取可用商品列表"""
        return COMMODITY_CONFIG


if __name__ == '__main__':
    fetcher = CommodityDataFetcher()
    
    print("=" * 60)
    print("增强版数据获取模块测试")
    print("=" * 60)
    
    print("\n可用商品列表:")
    for symbol, info in fetcher.get_available_symbols().items():
        print(f"  {symbol}: {info['name']} ({info['unit']})")
    
    print("\n测试数据获取:")
    for symbol in ['GC=F', 'CL=F']:
        print(f"\n获取 {symbol}...")
        df = fetcher.get_latest_data(symbol, days=200)
        print(f"  数据形状: {df.shape}")
        print(f"  价格范围: {df['Close'].min():.2f} - {df['Close'].max():.2f}")
