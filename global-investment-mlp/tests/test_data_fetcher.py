"""Tests for data_fetcher.py"""

import sys
import os
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_fetcher import GlobalFundDataFetcher, generate_synthetic_portfolio


class TestGlobalFundDataFetcher(unittest.TestCase):
    """测试 GlobalFundDataFetcher"""

    def setUp(self):
        self.fetcher = GlobalFundDataFetcher()

    def test_init(self):
        self.assertEqual(self.fetcher.source, 'mixed')
        self.assertIsInstance(self.fetcher.cache, dict)

    def test_init_with_source(self):
        fetcher = GlobalFundDataFetcher(source='yahoo')
        self.assertEqual(fetcher.source, 'yahoo')

    def test_get_market_data_invalid_market(self):
        result = self.fetcher.get_market_data('INVALID_MARKET')
        self.assertIsNone(result)

    def test_get_market_data_by_symbol(self):
        # This may hit real API or return None due to network
        result = self.fetcher.get_market_data_by_symbol('SPY', days=30)
        if result is not None:
            self.assertIsInstance(result, pd.DataFrame)
            self.assertGreater(len(result), 0)
            self.assertIn('Date', result.columns)

    def test_get_market_data_by_symbol_invalid(self):
        result = self.fetcher.get_market_data_by_symbol('ZZZZZZZZZZ')
        self.assertIsNone(result)

    def test_get_sector_data_invalid_market(self):
        result = self.fetcher.get_sector_data(market='INVALID')
        self.assertEqual(result, {})

    def test_get_sector_data_valid(self):
        result = self.fetcher.get_sector_data(market='US', days=30)
        self.assertIsInstance(result, dict)
        for k, v in result.items():
            if v is not None:
                self.assertIsInstance(v, pd.DataFrame)

    def test_generate_fund_data_hedge(self):
        funds = self.fetcher.generate_fund_data('hedge', n_funds=5, days=500)
        self.assertEqual(len(funds), 5)
        for fund in funds:
            self.assertIn('fund_id', fund)
            self.assertIn('returns', fund)
            self.assertIn('risk_metrics', fund)
            self.assertIn('nav_history', fund)
            self.assertIsInstance(fund['nav_history'], pd.DataFrame)
            self.assertGreater(len(fund['nav_history']), 0)

    def test_generate_fund_data_vc(self):
        funds = self.fetcher.generate_fund_data('vc', n_funds=3)
        self.assertEqual(len(funds), 3)
        for fund in funds:
            self.assertGreater(fund['returns']['1y'], -1)
            self.assertGreater(fund['risk_metrics']['volatility'], 0)

    def test_generate_fund_data_pe(self):
        funds = self.fetcher.generate_fund_data('pe', n_funds=3)
        self.assertEqual(len(funds), 3)

    def test_generate_fund_data_mutual(self):
        funds = self.fetcher.generate_fund_data('mutual', n_funds=3)
        self.assertEqual(len(funds), 3)

    def test_generate_fund_data_unknown_type(self):
        funds = self.fetcher.generate_fund_data('unknown_type', n_funds=2)
        self.assertEqual(len(funds), 2)

    def test_generate_fund_data_n_funds_zero(self):
        funds = self.fetcher.generate_fund_data('hedge', n_funds=0)
        self.assertEqual(len(funds), 0)

    def test_generate_fund_data_reproducible(self):
        funds1 = self.fetcher.generate_fund_data('hedge', n_funds=3, days=200)
        funds2 = self.fetcher.generate_fund_data('hedge', n_funds=3, days=200)
        self.assertEqual(funds1[0]['fund_id'], funds2[0]['fund_id'])
        self.assertAlmostEqual(funds1[0]['returns']['1y'], funds2[0]['returns']['1y'])

    def test_generate_fund_data_returns_keys(self):
        funds = self.fetcher.generate_fund_data('hedge', n_funds=1, days=500)
        ret = funds[0]['returns']
        self.assertIn('1m', ret)
        self.assertIn('3m', ret)
        self.assertIn('6m', ret)
        self.assertIn('1y', ret)

    def test_generate_fund_data_risk_metrics_keys(self):
        funds = self.fetcher.generate_fund_data('hedge', n_funds=1, days=500)
        rm = funds[0]['risk_metrics']
        self.assertIn('volatility', rm)
        self.assertIn('sharpe', rm)
        self.assertIn('max_drawdown', rm)
        self.assertIn('skewness', rm)
        self.assertIn('kurtosis', rm)

    def test_get_all_market_data(self):
        result = self.fetcher.get_all_market_data(markets=['US'], days=30)
        self.assertIsInstance(result, dict)

    def test_get_all_market_data_none(self):
        result = self.fetcher.get_all_market_data()
        self.assertIsInstance(result, dict)

    def test_batch_get_etfs(self):
        result = self.fetcher.batch_get_etfs(['SPY', 'QQQ'], days=30)
        self.assertIsInstance(result, dict)

    def test_batch_get_etfs_empty(self):
        result = self.fetcher.batch_get_etfs([], days=30)
        self.assertEqual(result, {})

    def test_market_indices_keys(self):
        self.assertIn('US', self.fetcher.MARKET_INDICES)
        self.assertIn('CN', self.fetcher.MARKET_INDICES)
        self.assertIn('HK', self.fetcher.MARKET_INDICES)

    def test_major_funds_keys(self):
        self.assertIn('Bridgewater', self.fetcher.MAJOR_FUNDS)
        self.assertIn('Sequoia', self.fetcher.MAJOR_FUNDS)
        self.assertIn('Blackstone', self.fetcher.MAJOR_FUNDS)


class TestGenerateSyntheticPortfolio(unittest.TestCase):
    """测试 generate_synthetic_portfolio 函数"""

    def test_default_params(self):
        portfolio = generate_synthetic_portfolio()
        self.assertEqual(portfolio.shape[1], 20)
        self.assertEqual(portfolio.shape[0], 500)
        self.assertEqual(portfolio.index.name, 'Date')

    def test_custom_n_assets(self):
        portfolio = generate_synthetic_portfolio(n_assets=10, n_days=300)
        self.assertEqual(portfolio.shape, (300, 10))

    def test_custom_seed(self):
        p1 = generate_synthetic_portfolio(n_assets=5, n_days=100, seed=123)
        p2 = generate_synthetic_portfolio(n_assets=5, n_days=100, seed=123)
        np.testing.assert_array_equal(p1.values, p2.values)

    def test_different_seed_different_data(self):
        p1 = generate_synthetic_portfolio(n_assets=5, n_days=100, seed=1)
        p2 = generate_synthetic_portfolio(n_assets=5, n_days=100, seed=2)
        self.assertFalse((p1.values == p2.values).all())

    def test_column_names(self):
        portfolio = generate_synthetic_portfolio(n_assets=5, n_days=50)
        cols = list(portfolio.columns)
        for i, col in enumerate(cols):
            self.assertEqual(col, f'Asset_{i+1}')

    def test_all_positive_values(self):
        """收益值应合理（不为NaN）"""
        portfolio = generate_synthetic_portfolio(n_assets=5, n_days=100)
        self.assertFalse(portfolio.isnull().values.any())

    def test_n_assets_clamped_to_20(self):
        """n_assets 上限为20"""
        portfolio = generate_synthetic_portfolio(n_assets=100, n_days=50)
        self.assertEqual(portfolio.shape[1], 20)

    def test_correlation_structure(self):
        """验证相关性结构合理"""
        portfolio = generate_synthetic_portfolio(n_assets=5, n_days=200)
        corr = portfolio.corr()
        self.assertAlmostEqual(corr.loc['Asset_1', 'Asset_1'], 1.0)
        # 非对角线元素应在合理范围
        off_diag = corr.values[~np.eye(5, dtype=bool)]
        self.assertGreaterEqual(off_diag.min(), -0.5)
        self.assertLessEqual(off_diag.max(), 1.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
