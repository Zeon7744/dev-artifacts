#!/usr/bin/env python3
"""
Data Fetcher - 全球投资数据获取器

支持数据源：
- Yahoo Finance (yf)
- Akshare (A股/港股)
- 模拟数据生成器
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# 缓存目录
import os
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)


class GlobalFundDataFetcher:
    """全球基金数据获取器"""
    
    # 主要市场指数
    MARKET_INDICES = {
        'US': '^GSPC',      # S&P 500
        'EU': '^STOXX600',  # 欧洲STOXX 600
        'CN': '000001.SS',  # 上证指数
        'HK': '^HSI',       # 恒生指数
        'JP': '^N225',      # 日经225
        'KR': '^KS11',      # 韩国KOSPI
    }
    
    # 主要行业ETF
    SECTOR_ETFS = {
        'US': {
            'Technology': 'XLK',
            'Healthcare': 'XLV',
            'Financials': 'XLF',
            'Energy': 'XLE',
            'Consumer': 'XLP',
            'Industrials': 'XLI',
            'Materials': 'XLB',
            'Utilities': 'XLU',
            'Real Estate': 'XLRE',
            'Communication': 'XLC'
        },
        'China': {
            'Tech': '512720.SH',
            'Healthcare': '512290.SH',
            'Finance': '510240.SH',
            'Consumer': '159928.SZ'
        }
    }
    
    # 全球主要基金代码
    MAJOR_FUNDS = {
        # 对冲基金 (模拟)
        'Bridgewater': 'RWR',
        'Renaissance': 'REN',
        'Citadel': 'CIT',
        'Millennium': 'MLM',
        'Point72': 'PSH',
        
        # VC基金
        'Sequoia': 'SEQ',
        'Andreessen': 'a16z',
        'Benchmark': 'BMRK',
        'Accel': 'ACCEL',
        'Greylock': 'GREY',
        
        # PE基金
        'Blackstone': 'BX',
        'KKR': 'KKR',
        'Carlyle': 'CG',
        'Apollo': 'APO',
        'BlackRock': 'BLK',
        
        # 主权基金
        'Norway_Gov': 'NBIM',
        'Saudi_PIB': 'PIB',
        'Singapore_GIC': 'GIC',
        'Abu_Dhabi': 'ADIA',
    }
    
    def __init__(self, source: str = 'mixed'):
        self.source = source
        self.cache = {}
    
    def get_market_data(self, market: str, days: int = 365) -> Optional[pd.DataFrame]:
        """获取市场指数数据"""
        if market not in self.MARKET_INDICES:
            return None
        
        symbol = self.MARKET_INDICES[market]
        
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d")
            
            if len(df) > 0:
                df = df.reset_index()
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            print(f"获取{market}数据失败: {e}")
        
        return None
    
    def get_sector_data(self, market: str = 'US', days: int = 365) -> Dict[str, pd.DataFrame]:
        """获取行业数据"""
        if market not in self.SECTOR_ETFS:
            return {}
        
        etfs = self.SECTOR_ETFS[market]
        sector_data = {}
        
        for sector, symbol in etfs.items():
            df = self.get_market_data_by_symbol(symbol, days)
            if df is not None and len(df) > 0:
                sector_data[sector] = df
        
        return sector_data
    
    def get_market_data_by_symbol(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        """通过代码获取市场数据"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d")
            
            if len(df) > 0:
                df = df.reset_index()
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            print(f"获取{symbol}数据失败: {e}")
        
        return None
    
    def generate_fund_data(self, fund_type: str, n_funds: int = 20, 
                           days: int = 500) -> List[Dict]:
        """生成模拟基金数据"""
        funds = []
        
        np.random.seed(42)
        
        for i in range(n_funds):
            # 根据基金类型设定参数
            if fund_type == 'hedge':
                base_return = np.random.uniform(0.08, 0.20)
                volatility = np.random.uniform(0.10, 0.25)
            elif fund_type == 'vc':
                base_return = np.random.uniform(0.15, 0.35)
                volatility = np.random.uniform(0.20, 0.45)
            elif fund_type == 'pe':
                base_return = np.random.uniform(0.12, 0.25)
                volatility = np.random.uniform(0.12, 0.28)
            elif fund_type == 'mutual':
                base_return = np.random.uniform(0.05, 0.15)
                volatility = np.random.uniform(0.08, 0.18)
            else:
                base_return = np.random.uniform(0.05, 0.20)
                volatility = np.random.uniform(0.10, 0.30)
            
            # 生成NAV序列
            dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
            returns = np.random.normal(base_return/252, volatility/np.sqrt(252), days)
            nav = 100 * np.exp(np.cumsum(returns))
            
            fund = {
                'fund_id': f'{fund_type[:3].upper()}{i+1:03d}',
                'name': f'{fund_type.title()} Fund {i+1}',
                'type': fund_type,
                'inception_date': (datetime.now() - timedelta(days=np.random.randint(500, 2000))).strftime('%Y-%m-%d'),
                'aum_billions': round(np.random.uniform(0.5, 500), 2),
                'nav_history': pd.DataFrame({
                    'date': dates.strftime('%Y-%m-%d'),
                    'nav': nav
                }),
                'returns': {
                    '1m': float(returns[-21:].mean() * 21),
                    '3m': float(returns[-63:].mean() * 63),
                    '6m': float(returns[-126:].mean() * 126),
                    '1y': float(returns[-252:].mean() * 252),
                    '3y_annualized': float((nav[-1]/nav[-756]) ** (252/756) - 1) if days > 756 else 0,
                    '5y_annualized': float((nav[-1]/nav[-1260]) ** (252/1260) - 1) if days > 1260 else 0
                },
                'risk_metrics': {
                    'volatility': float(volatility),
                    'sharpe': float((base_return - 0.02) / volatility),
                    'max_drawdown': float((nav.min() / nav.max() - 1)),
                    'skewness': float(pd.Series(returns).skew()),
                    'kurtosis': float(pd.Series(returns).kurtosis())
                }
            }
            
            funds.append(fund)
        
        return funds
    
    def get_all_market_data(self, markets: List[str] = None, days: int = 365) -> Dict:
        """获取所有市场数据"""
        if markets is None:
            markets = list(self.MARKET_INDICES.keys())
        
        result = {}
        for market in markets:
            df = self.get_market_data(market, days)
            if df is not None:
                result[market] = df
        
        return result
    
    def batch_get_etfs(self, symbols: List[str], days: int = 365) -> Dict[str, pd.DataFrame]:
        """批量获取ETF数据"""
        result = {}
        for symbol in symbols:
            df = self.get_market_data_by_symbol(symbol, days)
            if df is not None:
                result[symbol] = df
        return result


def generate_synthetic_portfolio(n_assets: int = 20, 
                                  n_days: int = 500,
                                  seed: int = 42) -> pd.DataFrame:
    """
    生成合成投资组合数据
    
    Returns:
        DataFrame with columns: date, and asset returns
    """
    np.random.seed(seed)
    
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='B')
    
    # 生成资产收益矩阵
    n_assets = min(n_assets, 20)
    
    # 设置相关性结构
    base_corr = 0.4
    corr_matrix = np.ones((n_assets, n_assets)) * base_corr
    np.fill_diagonal(corr_matrix, 1)
    
    # 添加一些差异化
    for i in range(n_assets):
        for j in range(i+1, n_assets):
            diff = np.random.uniform(-0.2, 0.2)
            corr_matrix[i, j] = max(0, min(1, corr_matrix[i, j] + diff))
            corr_matrix[j, i] = corr_matrix[i, j]
    
    # 生成收益
    means = np.random.uniform(-0.0002, 0.001, n_assets)
    vols = np.random.uniform(0.01, 0.03, n_assets)
    
    cov_matrix = np.outer(vols, vols) * corr_matrix
    
    returns = np.random.multivariate_normal(means, cov_matrix, n_days)
    
    # 创建DataFrame
    columns = [f'Asset_{i+1}' for i in range(n_assets)]
    df = pd.DataFrame(returns, index=dates, columns=columns)
    df.index.name = 'Date'
    
    return df


if __name__ == '__main__':
    print("="*70)
    print("数据获取器测试")
    print("="*70)
    
    fetcher = GlobalFundDataFetcher()
    
    # 测试市场数据
    print("\n【市场指数】")
    markets = fetcher.get_all_market_data(['US', 'CN', 'HK'], days=90)
    for market, df in markets.items():
        print(f"  {market}: {len(df)}条数据")
    
    # 测试模拟基金数据
    print("\n【模拟基金数据】")
    hedge_funds = fetcher.generate_fund_data('hedge', n_funds=5)
    for f in hedge_funds:
        print(f"  {f['name']}: 1年收益={f['returns']['1y']:.1%}, 夏普={f['risk_metrics']['sharpe']:.2f}")
    
    # 测试合成组合
    print("\n【合成投资组合】")
    portfolio = generate_synthetic_portfolio(n_assets=10, n_days=300)
    print(f"  资产数: {len(portfolio.columns)}")
    print(f"  时间跨度: {len(portfolio)}天")
    print(f"  平均收益: {portfolio.mean().mean():.3%}")
    
    print("\n" + "="*70)
