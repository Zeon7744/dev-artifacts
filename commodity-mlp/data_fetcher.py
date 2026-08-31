"""
大宗商品MLP投资分析工具 - 数据获取模块
支持模拟数据和真实市场数据
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
    """大宗商品数据获取器"""
    
    def __init__(self, use_real_data: bool = False):
        self.use_real_data = use_real_data
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
        
        # 使用商品符号作为种子基础，确保每个商品数据不同
        if seed is None:
            seed = sum(ord(c) * (i + 1) for i, c in enumerate(symbol)) % (2**32)
        
        np.random.seed(seed)
        
        # 生成日期序列
        dates = pd.date_range(end=datetime.now(), periods=days, freq='B')  # 工作日
        
        # 模拟价格序列（带趋势和波动聚集的GBM）
        # 1. 长期趋势
        trend_duration = np.random.randint(50, 150)
        trend_direction = np.random.choice([-1, 1])
        trend_strength = np.random.uniform(0.0001, 0.0005)
        
        # 2. 波动聚集（GARCH-like）
        base_volatility = 0.015
        volatility = np.zeros(days)
        volatility[0] = base_volatility
        for i in range(1, days):
            # 波动聚集：高波动后倾向于保持高波动
            volatility[i] = 0.95 * volatility[i-1] + 0.05 * np.random.uniform(0.01, 0.03)
        
        # 3. 收益率生成
        drift = trend_direction * trend_strength
        returns = np.random.normal(drift, volatility, days)
        
        # 4. 生成价格
        prices = base_price * np.exp(np.cumsum(returns))
        
        # 5. 生成OHLC数据
        np.random.seed(seed + 1)
        volumes = np.random.lognormal(mean=10, sigma=0.5, size=days).astype(float)
        
        intraday_vol = volatility * 0.5  # 日内波动约为日波动的50%
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
        
        # 添加目标变量：未来5日涨跌
        df['Target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
        
        return df.dropna().reset_index(drop=True)
    
    def fetch_real_data(self, symbol: str, period: str = '1y') -> pd.DataFrame:
        """从yfinance获取真实数据"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            
            if df.empty:
                return None
            
            df = df.reset_index()
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            
            # 添加目标变量
            df['Target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
            
            return df.dropna()
            
        except Exception as e:
            print(f"获取{symbol}真实数据失败: {e}")
            return None
    
    def get_data(
        self, 
        symbols: List[str], 
        use_real: bool = False,
        days: int = 800
    ) -> Dict[str, pd.DataFrame]:
        """获取多个商品的数据"""
        data = {}
        
        for symbol in symbols:
            if use_real:
                df = self.fetch_real_data(symbol)
                if df is None or df.empty:
                    print(f"警告: {symbol}真实数据获取失败，使用模拟数据")
                    df = self.generate_simulated_data(symbol, days)
            else:
                df = self.generate_simulated_data(symbol, days)
            
            df['Symbol'] = symbol
            data[symbol] = df
        
        return data
    
    def get_available_symbols(self) -> Dict[str, Dict]:
        """获取可用商品列表"""
        return COMMODITY_CONFIG


if __name__ == '__main__':
    # 测试数据获取
    fetcher = CommodityDataFetcher()
    
    print("可用商品列表:")
    for symbol, info in fetcher.get_available_symbols().items():
        print(f"  {symbol}: {info['name']} ({info['unit']})")
    
    print("\n生成模拟数据示例:")
    df = fetcher.generate_simulated_data('GC=F', days=100)
    print(df.tail())
    print(f"\n数据形状: {df.shape}")
    print(f"特征列: {[c for c in df.columns if c not in ['Date', 'Symbol', 'Target']]}")
