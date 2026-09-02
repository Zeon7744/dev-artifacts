"""Tests for main.py"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_analysis, main


class TestRunAnalysis(unittest.TestCase):
    """测试 run_analysis 函数"""

    @patch('main.argparse.ArgumentParser')
    def test_main_parsing(self, mock_parser):
        """测试命令行参数解析"""
        # main() 调用 argparse，我们不需要真正运行它
        # 这里只是验证导入成功
        from main import run_analysis
        self.assertTrue(callable(run_analysis))

    @patch('main.GlobalInvestmentAnalyzer')
    @patch('main.MultiFactorModel')
    @patch('main.RiskDashboard')
    @patch('main.StressTester')
    @patch('main.InvestmentReportGenerator')
    @patch('main.GlobalFundDataFetcher')
    @patch('main.generate_synthetic_portfolio')
    def test_run_analysis_basic(self, mock_gen_portfolio, mock_fetcher_cls,
                                 mock_report_cls, mock_stress_cls,
                                 mock_risk_cls, mock_factor_cls, mock_analyzer_cls):
        """测试基础分析流程"""
        # 模拟 analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.detect_hotspots.return_value = []
        mock_analyzer.run_comprehensive_analysis.return_value = {
            'hotspots': [], 'recommendations': [],
            'market_summary': {}, 'fund_analysis': []
        }
        mock_analyzer.generate_allocation_recommendations.return_value = []
        mock_analyzer_cls.return_value = mock_analyzer

        # 模拟 factor model
        mock_factor = MagicMock()
        mock_factor.prepare_data.return_value = (np.zeros((10, 3)), np.zeros(10), ['a', 'b', 'c'])
        mock_factor.optimize_weights.return_value = {'a': 0.3, 'b': 0.3, 'c': 0.4}
        mock_factor.backtest.return_value = {'ic_mean': 0.05, 'long_short_return': 0.01, 'sharpe_ratio': 1.0}
        mock_factor_cls.return_value = mock_factor

        # 模拟 risk dashboard
        mock_risk = MagicMock()
        mock_risk.calculate_all.return_value = {
            'var_95': 0.02, 'max_drawdown': -0.05, 'sharpe_ratio': 1.5,
            'alerts': []
        }
        mock_risk_cls.return_value = mock_risk

        # 模拟 stress tester
        mock_stress = MagicMock()
        mock_stress.run_all_scenarios.return_value = {}
        mock_stress_cls.return_value = mock_stress

        # 模拟 report generator
        mock_report = MagicMock()
        mock_report.generate_comprehensive_report.return_value = '/tmp/report.html'
        mock_report.generate_summary_json.return_value = '/tmp/summary.json'
        mock_report_cls.return_value = mock_report

        # 模拟 data fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.get_all_market_data.return_value = {}
        mock_fetcher.generate_fund_data.side_effect = lambda ft, n_funds=5, days=500: [
            {
                'fund_id': f'{ft[:3].upper()}001',
                'name': f'{ft} Fund 1',
                'type': ft,
                'inception_date': '2020-01-01',
                'aum_billions': 50.0,
                'returns': {'1y': 0.15},
                'risk_metrics': {'sharpe': 1.2, 'max_drawdown': -0.1}
            }
        ]
        mock_fetcher_cls.return_value = mock_fetcher

        # 模拟 portfolio
        mock_gen_portfolio.return_value = pd.DataFrame(
            np.random.randn(100, 5),
            columns=[f'Asset_{i}' for i in range(5)]
        )

        # 创建 args 对象
        class Args:
            markets = 'US'
            days = 100
            n_funds = 1
            n_assets = 5
            portfolio_value = 1000000
            factor_method = 'ic_weighting'
            regime = 'expansion'

        result = run_analysis(Args())
        self.assertIn('report_path', result)
        self.assertIn('summary_path', result)
        self.assertIn('hotspots', result)
        self.assertIn('risk_metrics', result)



    @patch('main.argparse.ArgumentParser')
    def test_main_runs_with_args(self, mock_parser_cls):
        """测试 main() 函数入口（CLI 路径）"""
        from unittest.mock import MagicMock, patch
        mock_args = MagicMock()
        mock_args.markets = 'US'
        mock_args.days = 100
        mock_args.n_funds = 1
        mock_args.n_assets = 3
        mock_args.portfolio_value = 1000000
        mock_args.factor_method = 'ic_weighting'
        mock_args.regime = 'expansion'

        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_parser_cls.return_value = mock_parser

        with patch('main.run_analysis') as mock_run:
            mock_run.return_value = {'report_path': '/tmp/r.html'}
            from main import main
            main()
            mock_run.assert_called_once_with(mock_args)

    @patch('main.GlobalInvestmentAnalyzer')
    @patch('main.MultiFactorModel')
    @patch('main.RiskDashboard')
    @patch('main.StressTester')
    @patch('main.InvestmentReportGenerator')
    @patch('main.GlobalFundDataFetcher')
    @patch('main.generate_synthetic_portfolio')
    def test_run_analysis_with_hotspots_and_sectors(self, mock_gen_portfolio,
                                                     mock_fetcher_cls,
                                                     mock_report_cls,
                                                     mock_stress_cls,
                                                     mock_risk_cls,
                                                     mock_factor_cls,
                                                     mock_analyzer_cls):
        """测试含热点和 sector 数据的完整流程"""
        from core_analyzer import SectorHotspot, AllocationRecommendation

        hotspots = [
            SectorHotspot(sector='Tech', score=85.0, momentum=0.15,
                          risk_level='medium', expected_return=0.12,
                          timeframe='1y', key_themes=['AI', 'Cloud'], top_funds=[]),
            SectorHotspot(sector='Health', score=72.0, momentum=0.08,
                          risk_level='low', expected_return=0.08,
                          timeframe='1y', key_themes=['Biotech'], top_funds=[]),
        ]
        recommendations = [
            AllocationRecommendation(target_weight=0.3, current_weight=0.15,
                                      action='overweight', confidence=0.85,
                                      rationale='strong momentum',
                                      risk_adjusted_return=0.12),
        ]
        mock_analyzer = MagicMock()
        mock_analyzer.detect_hotspots.return_value = hotspots
        mock_analyzer.run_comprehensive_analysis.return_value = {
            'hotspots': [], 'recommendations': [],
            'market_summary': {}, 'fund_analysis': []
        }
        mock_analyzer.generate_allocation_recommendations.return_value = recommendations
        mock_analyzer_cls.return_value = mock_analyzer

        mock_factor = MagicMock()
        mock_factor.prepare_data.return_value = (np.zeros((3, 2)), np.zeros(3), ['a', 'b'])
        mock_factor.optimize_weights.return_value = {'a': 0.5, 'b': 0.5}
        mock_factor.backtest.return_value = {'ic_mean': 0.05, 'long_short_return': 0.01, 'sharpe_ratio': 1.2}
        mock_factor_cls.return_value = mock_factor

        mock_risk = MagicMock()
        mock_risk.calculate_all.return_value = {
            'var_95': 0.015, 'max_drawdown': -0.04, 'sharpe_ratio': 1.8,
            'alerts': []
        }
        mock_risk.alerts = []
        mock_risk_cls.return_value = mock_risk

        mock_stress = MagicMock()
        mock_stress.run_all_scenarios.return_value = {
            '2008_crisis': {'scenario': '2008_crisis', 'var_95': 500000}
        }
        mock_stress_cls.return_value = mock_stress

        mock_report = MagicMock()
        mock_report.generate_comprehensive_report.return_value = '/tmp/r.html'
        mock_report.generate_summary_json.return_value = '/tmp/s.json'
        mock_report_cls.return_value = mock_report

        mock_fetcher = MagicMock()
        mock_fetcher.get_all_market_data.return_value = {
            'US': pd.DataFrame({'Close': range(100)}, index=pd.date_range('2024-01-01', periods=100))
        }
        mock_fetcher.generate_fund_data.side_effect = lambda ft, n_funds=1, days=500: [
            {
                'fund_id': 'US001', 'name': 'US Fund', 'type': ft,
                'inception_date': '2020-01-01', 'aum_billions': 50.0,
                'returns': {'1y': 0.10}, 'risk_metrics': {'sharpe': 1.0, 'max_drawdown': -0.08}
            }
        ]
        mock_fetcher_cls.return_value = mock_fetcher

        mock_gen_portfolio.return_value = pd.DataFrame(
            np.random.randn(100, 3), columns=[f'Asset_{i}' for i in range(3)]
        )

        class Args:
            markets = 'US'
            days = 100
            n_funds = 1
            n_assets = 3
            portfolio_value = 1000000
            factor_method = 'ic_weighting'
            regime = 'expansion'

        result = run_analysis(Args())
        self.assertIn('report_path', result)
        mock_analyzer.detect_hotspots.assert_called_once()


class TestImports(unittest.TestCase):
    """测试模块导入"""

    def test_import_main(self):
        from main import run_analysis, main
        self.assertTrue(callable(run_analysis))
        self.assertTrue(callable(main))

    def test_import_from_modules(self):
        from core_analyzer import GlobalInvestmentAnalyzer, FundType
        from multi_factor_model import MultiFactorModel, SectorRotationModel
        from risk_analytics import RiskDashboard, StressTester, CorrelationAnalyzer
        from data_fetcher import GlobalFundDataFetcher, generate_synthetic_portfolio
        from report_generator import InvestmentReportGenerator
        self.assertTrue(GlobalInvestmentAnalyzer is not None)

