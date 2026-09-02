"""Tests for report_generator.py"""

import sys
import os
import unittest
import json
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from report_generator import InvestmentReportGenerator


class TestInvestmentReportGenerator(unittest.TestCase):
    """测试 InvestmentReportGenerator"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.gen = InvestmentReportGenerator(output_dir=self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_creates_output_dir(self):
        custom_dir = os.path.join(self.tmpdir, 'custom_reports')
        gen = InvestmentReportGenerator(output_dir=custom_dir)
        self.assertTrue(os.path.isdir(custom_dir))

    def test_generate_comprehensive_report(self):
        result = {
            'hotspots': [
                {'sector': 'AI/ML', 'score': 85, 'expected_return': 0.25,
                 'risk_level': 'high', 'key_themes': ['LLM', 'Agent', 'AIGC'],
                 'timeframe': 'long_term'},
                {'sector': 'Clean Energy', 'score': 78, 'expected_return': 0.18,
                 'risk_level': 'medium', 'key_themes': ['储能', '氢能'],
                 'timeframe': 'medium_term'},
            ],
            'recommendations': [
                {'target_weight': 0.15, 'current_weight': 0.05, 'action': 'overweight',
                 'confidence': 0.85, 'rationale': '高景气赛道',
                 'risk_adjusted_return': 0.30},
                {'target_weight': 0.10, 'current_weight': 0.12, 'action': 'neutral',
                 'confidence': 0.70, 'rationale': '平衡配置',
                 'risk_adjusted_return': 0.18},
            ],
            'market_summary': {
                'total_funds_analyzed': 50,
                'avg_return_1y': 0.12,
                'avg_sharpe': 1.2,
                'market_sentiment': 'bullish'
            },
            'fund_analysis': [
                {'name': 'Sequoia Capital', 'fund_type': 'VC', 'aum_usd_billion': 85.5,
                 'returns_1y': 0.28, 'sharpe_ratio': 1.8, 'max_drawdown': -0.15},
            ]
        }

        path = self.gen.generate_comprehensive_report(result)
        self.assertTrue(path.endswith('.html'))
        self.assertTrue(os.path.exists(path))

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('全球资本投资分析报告', content)
        self.assertIn('AI/ML', content)
        self.assertIn('overweight', content)
        self.assertIn('BULLISH', content)

    def test_generate_comprehensive_report_empty_data(self):
        result = {
            'hotspots': [],
            'recommendations': [],
            'market_summary': {},
            'fund_analysis': []
        }
        path = self.gen.generate_comprehensive_report(result)
        self.assertTrue(path.endswith('.html'))
        self.assertTrue(os.path.exists(path))

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('暂无数据', content)

    def test_generate_comprehensive_report_with_risk_metrics(self):
        result = {
            'hotspots': [],
            'recommendations': [],
            'market_summary': {},
            'fund_analysis': []
        }
        risk = {'var_95': 0.03, 'sharpe_ratio': 1.5, 'max_drawdown': -0.08}
        path = self.gen.generate_comprehensive_report(result, risk_metrics=risk)
        self.assertTrue(os.path.exists(path))

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('0.0300', content)

    def test_generate_comprehensive_report_with_factor_analysis(self):
        result = {'hotspots': [], 'recommendations': [], 'market_summary': {}, 'fund_analysis': []}
        factors = {'PB': 0.15, 'PE': 0.12, 'ROE': 0.10}
        path = self.gen.generate_comprehensive_report(result, factor_analysis=factors)
        self.assertTrue(os.path.exists(path))

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('PB', content)

    def test_generate_comprehensive_report_with_stress_tests(self):
        result = {'hotspots': [], 'recommendations': [], 'market_summary': {}, 'fund_analysis': []}
        stress = {
            '2008_crisis': {
                'scenario': '2008年金融危机',
                'var_95': 50000,
                'cvar_95': 65000,
                'max_loss': 80000,
                'prob_5pct_loss': 12.5
            }
        }
        path = self.gen.generate_comprehensive_report(result, pressure_tests=stress)
        self.assertTrue(os.path.exists(path))

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('2008年金融危机', content)
        self.assertIn('50,000', content)

    def test_generate_summary_json(self):
        result = {
            'market_summary': {'total_funds_analyzed': 50, 'avg_return_1y': 0.12},
            'hotspots': [
                {'sector': 'AI/ML', 'score': 85, 'expected_return': 0.25},
                {'sector': 'Biotech', 'score': 72, 'expected_return': 0.22},
            ]
        }
        path = self.gen.generate_summary_json(result)
        self.assertTrue(path.endswith('.json'))
        self.assertTrue(os.path.exists(path))

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIn('generated_at', data)
        self.assertIn('market_summary', data)
        self.assertIn('top_hotspots', data)
        self.assertEqual(len(data['top_hotspots']), 2)
        self.assertEqual(data['top_hotspots'][0], 'AI/ML')

    def test_generate_summary_json_empty_hotspots(self):
        result = {'market_summary': {}, 'hotspots': []}
        path = self.gen.generate_summary_json(result)
        self.assertTrue(os.path.exists(path))

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data['top_hotspots'], [])
        self.assertEqual(data['risk_level'], 'medium')

    def test_report_filename_format(self):
        result = {'hotspots': [], 'recommendations': [], 'market_summary': {}, 'fund_analysis': []}
        path = self.gen.generate_comprehensive_report(result)
        # 文件名格式: investment_report_YYYYMMDD_HHMMSS.html
        self.assertTrue(path.startswith(self.tmpdir))
        self.assertIn('investment_report_', path)
        self.assertTrue(path.endswith('.html'))

    def test_summary_filename_format(self):
        result = {'market_summary': {}, 'hotspots': []}
        path = self.gen.generate_summary_json(result)
        self.assertIn('summary_', path)
        self.assertTrue(path.endswith('.json'))

    def test_html_contains_expected_sections(self):
        result = {
            'hotspots': [{'sector': 'Test', 'score': 50, 'expected_return': 0.1,
                          'risk_level': 'medium', 'key_themes': ['A'], 'timeframe': 'long_term'}],
            'recommendations': [{'target_weight': 0.1, 'current_weight': 0.05, 'action': 'overweight',
                                 'confidence': 0.7, 'rationale': 'test', 'risk_adjusted_return': 0.15}],
            'market_summary': {'total_funds_analyzed': 10, 'avg_return_1y': 0.1,
                               'avg_sharpe': 1.0, 'market_sentiment': 'neutral'},
            'fund_analysis': []
        }
        path = self.gen.generate_comprehensive_report(result)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('投资热点', content)
        self.assertIn('资产配置建议', content)
        self.assertIn('基金表现分析', content)
        self.assertIn('风险指标', content)
        self.assertIn('压力测试结果', content)
        self.assertIn('因子分析', content)


if __name__ == '__main__':
    unittest.main(verbosity=2)
