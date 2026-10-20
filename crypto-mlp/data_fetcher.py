#!/usr/bin/env python3
"""
Crypto Data Fetcher - 加密货币数据获取模块

使用yfinance获取加密货币数据（无需API密钥）
支持BTC, ETH等主要币种
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import time
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class CryptoDataFetcher:
    """加密货币数据获取器"""
    
    # 主流加密货币映射
    COIN_MAP = {
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD',
        'BNB': 'BNB-USDT',
        'SOL': 'SOL-USD',
        'XRP': 'XRP-USD',
        'ADA': 'ADA-USD',
        'DOGE': 'DOGE-USD',
        'MATIC': 'MATIC-USD',
        'AVAX': 'AVAX-USD',
        'DOT': 'DOT-USD',
        'LINK': 'LINK-USD',
        'UNI': 'UNI-USD',
        'LTC': 'LTC-USD',
        'ATOM': 'ATOM-USD',
        'FIL': 'FIL-USD',
    }
    
    def __init__(self, exchange: str = 'binance'):
        """
        初始化数据获取器
        
        Args:
            exchange: 交易所名称（用于兼容接口）
        """
        self.exchange = exchange.lower()
        self.cache_dir = Path('./cache')
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"数据获取器初始化完成，交易所: {self.exchange}")
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '4h', limit: int = 500) -> pd.DataFrame:
        """
        获取OHLCV数据
        
        Args:
            symbol: 币种代码，如 BTC
            timeframe: 时间周期 (1m, 5m, 15m, 1h, 4h, 1d)
            limit: 数据条数
        
        Returns:
            DataFrame with OHLCV data
        """
        # 转换符号格式
        yahoo_symbol = self.COIN_MAP.get(symbol.upper(), f"{symbol.upper()}-USD")
        
        # 时间周期映射
        period_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1wk'
        }
        period = period_map.get(timeframe, '4h')
        
        # 检查缓存
        cache_file = self.cache_dir / f"{yahoo_symbol}_{period}.pkl"
        if cache_file.exists():
            try:
                cached = pd.read_pickle(cache_file)
                if len(cached) >= limit * 0.8:
                    logger.debug(f"使用缓存数据: {cache_file}")
                    return cached.head(limit)
            except Exception as e:
                logger.debug(f"缓存读取失败: {e}")
        
        try:
            logger.info(f"获取数据: {yahoo_symbol}, 周期: {period}, 数量: {limit}")
            
            # 使用yfinance获取数据
            ticker = yf.Ticker(yahoo_symbol)
            
            # 获取历史数据
            if period in ['1m', '5m', '15m', '30m']:
                df = ticker.history(period='5d', interval=period)
            else:
                df = ticker.history(period='1y', interval=period)
            
            if df.empty:
                logger.warning(f"无法获取数据，使用模拟数据: {yahoo_symbol}")
                return self._generate_synthetic_data(symbol, timeframe, limit)
            
            # 重命名列
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 重置索引
            df = df.reset_index()
            df.columns = ['timestamp'] + list(df.columns[1:])
            
            # 限制条数
            df = df.tail(limit)
            
            # 保存缓存
            df.to_pickle(cache_file)
            
            logger.info(f"成功获取{len(df)}条数据: {yahoo_symbol}")
            return df
            
        except Exception as e:
            logger.error(f"获取数据失败 {yahoo_symbol}: {e}")
            return self._generate_synthetic_data(symbol, timeframe, limit)
    
    def _generate_synthetic_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """生成模拟数据（当API失败时）- 使用均值回归防止漂移"""
        logger.warning(f"使用模拟数据: {symbol}")
        
        np.random.seed(42)
        dates = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq=timeframe)
        
        # 模拟价格（均值回归随机游走）
        base_price = {'BTC': 52000, 'ETH': 3500, 'BNB': 600}[symbol] if symbol in ['BTC', 'ETH', 'BNB'] else 100
        prices = []
        price = base_price
        for _ in range(limit):
            # 均值回归力（拉向base_price）
            drift = -0.005 * (price - base_price) / base_price
            # 随机波动
            ret = drift + np.random.normal(0, 0.015)
            price = price * (1 + ret)
            prices.append(price)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.008))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.008))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, limit)
        })
        
        return df
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的币种列表"""
        return list(self.COIN_MAP.keys())
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格"""
        yahoo_symbol = self.COIN_MAP.get(symbol.upper(), f"{symbol.upper()}-USD")
        try:
            ticker = yf.Ticker(yahoo_symbol)
            # 获取最近的数据
            data = ticker.history(period='1d')
            if not data.empty and 'Close' in data.columns:
                return float(data['Close'].iloc[-1])
        except Exception as e:
            logger.debug(f"获取当前价格失败 {symbol}: {e}")
        return None


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    fetcher = CryptoDataFetcher()
    
    # 测试获取BTC数据
    df = fetcher.fetch_ohlcv('BTC', '4h', 100)
    print(df.head(10))
    print(f"\n数据形状: {df.shape}")
    print(f"时间范围: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
    
    # 测试获取ETH数据
    df_eth = fetcher.fetch_ohlcv('ETH', '1d', 50)
    print(f"\nETH数据形状: {df_eth.shape}")
    
    # 测试获取当前价格
    price = fetcher.get_current_price('BTC')
    print(f"\n当前BTC价格: ${price:,.2f}" if price else "\n无法获取当前价格")
