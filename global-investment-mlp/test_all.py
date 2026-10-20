#!/usr/bin/env python3
"""
测试套件 - Global Investment MLP
"""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core_analyzer import GlobalInvestmentAnalyzer, FundType, FundProfile
from multi_factor_model import MultiFactorModel, SectorRotationModel
from risk_analytics import RiskMetrics, StressTester, RiskDashboard, CorrelationAnalyzer
from data_fetcher import GlobalFundDataFetcher, generate_synthetic_portfolio
from report_generator import InvestmentReportGenerator


class TestFundAnalysis(unittest.TestCase):
    """基金分析测试"""
    
    def setUp(self):
        self.analyzer = GlobalInvestmentAnalyzer()
    
    def test_add_fund(self):
        """测试添加基金"""
        fund = FundProfile(
            fund_id='TEST001',
            name='Test Fund',
            fund_type=FundType.HEDGE_FUND,
            inception_date='2020-01-01',
            AUM=100.0,
            strategy='long_short',
            benchmark='SPX',
            managers=['Manager A'],
            geography_focus=['US'],
            sector_focus=['Tech'],
            vintages=[2020]
        )
        self.analyzer.add_fund(fund)
        self.assertEqual(len(self.analyzer.fund_database), 1)
        self.assertEqual(self.analyzer.fund_database['TEST001'].name, 'Test Fund')
    
    def test_detect_hotspots(self):
        """测试热点检测"""
        hotspots = self.analyzer.detect_hotspots()
        self.assertGreater(len(hotspots), 0)
        self.assertLessEqual(len(hotspots), 10)
        for h in hotspots:
            self.assertGreaterEqual(h.score, 0)
            self.assertLessEqual(h.score, 100)


class TestMultiFactorModel(unittest.TestCase):
    """多因子模型测试"""
    
    def setUp(self):
        np.random.seed(42)
        self.n_samples = 200
        self.n_factors = 10
        self.X = np.random.randn(self.n_samples, self.n_factors)
        self.y = np.random.choice([0, 1], size=self.n_samples)
        self.model = MultiFactorModel(
            factors=[f'factor_{i}' for i in range(self.n_factors)],
            optimization_method='ic_weighting'
        )
    
    def test_optimize_weights(self):
        """测试权重优化"""
        weights = self.model.optimize_weights(self.X, self.y)
        self.assertEqual(len(weights), self.n_factors)
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=5)
    
    def test_backtest(self):
        """测试回测"""
        self.model.optimize_weights(self.X, self.y)
        results = self.model.backtest(self.X, self.y)
        self.assertIn('long_short_return', results)
        self.assertIn('sharpe_ratio', results)


class TestRiskAnalytics(unittest.TestCase):
    """风险分析测试"""
    
    def setUp(self):
        np.random.seed(42)
        self.returns = np.random.normal(0.0005, 0.015, 500)
    
    def test_var_calculation(self):
        """测试VaR计算"""
        var = RiskMetrics.calculate_var(self.returns, 0.95)
        self.assertGreater(var, 0)
        self.assertLess(var, 0.1)
    
    def test_cvar_calculation(self):
        """测试CVaR计算"""
        cvar = RiskMetrics.calculate_cvar(self.returns, 0.95)
        var = RiskMetrics.calculate_var(self.returns, 0.95)
        self.assertGreaterEqual(cvar, var)
    
    def test_max_drawdown(self):
        """测试最大回撤"""
        result = RiskMetrics.calculate_max_drawdown(self.returns)
        self.assertLess(result['max_drawdown'], 0)
        self.assertGreater(result['max_drawdown'], -1)
    
    def test_stress_test(self):
        """测试压力测试"""
        tester = StressTester()
        n_assets = 5
        weights = np.ones(n_assets) / n_assets
        vols = np.array([0.2, 0.25, 0.18, 0.22, 0.30])
        corr = np.eye(n_assets) * 0.5 + 0.25
        
        result = tester.stress_test(1000000, weights, vols, corr, '2008_crisis')
        self.assertIn('var_95', result)
        self.assertGreater(result['var_95'], 0)


class TestDataFetcher(unittest.TestCase):
    """数据获取测试"""
    
    def test_generate_fund_data(self):
        """测试基金数据生成"""
        fetcher = GlobalFundDataFetcher()
        funds = fetcher.generate_fund_data('hedge', n_funds=5)
        self.assertEqual(len(funds), 5)
        for fund in funds:
            self.assertIn('fund_id', fund)
            self.assertIn('returns', fund)
            self.assertIn('risk_metrics', fund)
    
    def test_generate_portfolio(self):
        """测试组合数据生成"""
        portfolio = generate_synthetic_portfolio(n_assets=10, n_days=300)
        self.assertEqual(portfolio.shape[0], 300)
        self.assertEqual(portfolio.shape[1], 10)


class TestReportGenerator(unittest.TestCase):
    """报告生成测试"""
    
    def test_generate_report(self):
        """测试报告生成"""
        gen = InvestmentReportGenerator()
        result = {
            'hotspots': [
                {'sector': 'AI', 'score': 85, 'expected_return': 0.25, 
                 'risk_level': 'high', 'key_themes': ['LLM'], 'timeframe': 'long_term'}
            ],
            'recommendations': [
                {'target_weight': 0.15, 'current_weight': 0.05, 'action': 'overweight',
                 'confidence': 0.85, 'rationale': 'test', 'risk_adjusted_return': 0.30}
            ],
            'market_summary': {
                'total_funds_analyzed': 10,
                'avg_return_1y': 0.12,
                'avg_sharpe': 1.2,
                'market_sentiment': 'bullish'
            },
            'fund_analysis': []
        }
        
        path = gen.generate_comprehensive_report(result)
        self.assertTrue(path.endswith('.html'))
        self.assertTrue(os.path.exists(path))
        
        # 清理
        os.remove(path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
