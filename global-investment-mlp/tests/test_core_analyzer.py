"""Tests for core_analyzer.py"""

import sys
import os
import unittest
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core_analyzer import (
    GlobalInvestmentAnalyzer,
    FundType,
    InvestmentStage,
    RiskLevel,
    FundProfile,
    SectorHotspot,
    AllocationRecommendation,
)


class TestEnums(unittest.TestCase):
    """测试枚举类"""

    def test_fund_type_values(self):
        self.assertEqual(FundType.HEDGE_FUND.value, "hedge_fund")
        self.assertEqual(FundType.MUTUAL_FUND.value, "mutual_fund")
        self.assertEqual(FundType.VC_FUND.value, "vc_fund")
        self.assertEqual(FundType.PE_FUND.value, "pe_fund")
        self.assertEqual(FundType.ANGEL_FUND.value, "angel_fund")
        self.assertEqual(FundType.SOVEREIGN.value, "sovereign_wealth")
        self.assertEqual(FundType.ENDOWMENT.value, "endowment")
        self.assertEqual(FundType.PENSION.value, "pension_fund")

    def test_investment_stage_values(self):
        self.assertEqual(InvestmentStage.SEED.value, "seed")
        self.assertEqual(InvestmentStage.EARLY_STAGE.value, "early_stage")
        self.assertEqual(InvestmentStage.GROWTH.value, "growth")
        self.assertEqual(InvestmentStage.LATE_STAGE.value, "late_stage")
        self.assertEqual(InvestmentStage.PRE_IPO.value, "pre_ipo")
        self.assertEqual(InvestmentStage.IPO.value, "ipo")
        self.assertEqual(InvestmentStage.POST_IPO.value, "post_ipo")

    def test_risk_level_values(self):
        self.assertEqual(RiskLevel.VERY_LOW.value, "very_low")
        self.assertEqual(RiskLevel.LOW.value, "low")
        self.assertEqual(RiskLevel.MEDIUM.value, "medium")
        self.assertEqual(RiskLevel.HIGH.value, "high")
        self.assertEqual(RiskLevel.VERY_HIGH.value, "very_high")


class TestFundProfile(unittest.TestCase):
    """测试 FundProfile 数据类"""

    def test_create_minimal(self):
        fund = FundProfile(
            fund_id='F001',
            name='Test Fund',
            fund_type=FundType.HEDGE_FUND,
            inception_date='2020-01-01',
            AUM=50.0,
            strategy='long_short',
            benchmark='SPX',
            managers=['Manager A'],
            geography_focus=['US'],
            sector_focus=['Tech'],
            vintages=[2020],
        )
        self.assertEqual(fund.fund_id, 'F001')
        self.assertEqual(fund.name, 'Test Fund')
        self.assertEqual(fund.returns_1y, 0.0)
        self.assertEqual(len(fund.top_holdings), 0)
        self.assertEqual(len(fund.sector_allocation), 0)

    def test_to_dict(self):
        fund = FundProfile(
            fund_id='F002',
            name='Alpha Fund',
            fund_type=FundType.VC_FUND,
            inception_date='2019-06-15',
            AUM=200.0,
            strategy='growth',
            benchmark='NASDAQ',
            managers=['M1', 'M2'],
            geography_focus=['US', 'Asia'],
            sector_focus=['AI', 'Biotech'],
            vintages=[2019, 2020],
            returns_1y=0.25,
            sharpe_ratio=1.5,
            max_drawdown=-0.12,
            sector_allocation={'AI': 0.4, 'Biotech': 0.3},
        )
        d = fund.to_dict()
        self.assertEqual(d['fund_id'], 'F002')
        self.assertEqual(d['fund_type'], 'vc_fund')
        self.assertAlmostEqual(d['aum_usd_billion'], 200.0)
        self.assertAlmostEqual(d['returns_1y'], 0.25)
        self.assertEqual(d['top_sectors'], ['AI', 'Biotech'])

    def test_to_dict_with_defaults(self):
        fund = FundProfile(
            fund_id='F003', name='Basic', fund_type=FundType.MUTUAL_FUND,
            inception_date='2021-01-01', AUM=10.0, strategy='index',
            benchmark='SPX', managers=[], geography_focus=[], sector_focus=[],
            vintages=[],
        )
        d = fund.to_dict()
        self.assertEqual(d['returns_1y'], 0.0)
        self.assertEqual(d['top_sectors'], [])


class TestSectorHotspot(unittest.TestCase):
    """测试 SectorHotspot 数据类"""

    def test_to_dict(self):
        h = SectorHotspot(
            sector='AI/ML', score=85.0, momentum=0.25,
            risk_level='high', expected_return=0.30,
            timeframe='long_term',
            key_themes=['LLM', 'Agent', 'AIGC', '垂直应用'],
            top_funds=['Fund A', 'Fund B', 'Fund C', 'Fund D'],
        )
        d = h.to_dict()
        self.assertEqual(d['sector'], 'AI/ML')
        self.assertEqual(len(d['key_themes']), 3)
        self.assertEqual(len(d['top_funds']), 3)
        self.assertAlmostEqual(d['score'], 85.0)

    def test_to_dict_few_themes(self):
        h = SectorHotspot(
            sector='Clean Energy', score=70.0, momentum=0.15,
            risk_level='medium', expected_return=0.20,
            timeframe='medium_term',
            key_themes=['储能'],
            top_funds=['Green Fund'],
        )
        d = h.to_dict()
        self.assertEqual(d['key_themes'], ['储能'])
        self.assertEqual(d['top_funds'], ['Green Fund'])


class TestAllocationRecommendation(unittest.TestCase):
    """测试 AllocationRecommendation 数据类"""

    def test_to_dict(self):
        r = AllocationRecommendation(
            target_weight=0.15, current_weight=0.05,
            action='overweight', confidence=0.85,
            rationale='高景气赛道', risk_adjusted_return=0.30,
        )
        d = r.to_dict()
        self.assertEqual(d['action'], 'overweight')
        self.assertAlmostEqual(d['target_weight'], 0.15)
        self.assertAlmostEqual(d['risk_adjusted_return'], 0.30)


class TestGlobalInvestmentAnalyzer(unittest.TestCase):
    """测试 GlobalInvestmentAnalyzer 核心类"""

    def setUp(self):
        self.analyzer = GlobalInvestmentAnalyzer()

    def test_init_creates_data_dir(self):
        analyzer = GlobalInvestmentAnalyzer(data_dir='./test_data_dir_tmp')
        self.assertTrue(os.path.isdir('./test_data_dir_tmp'))
        # 清理
        import shutil
        shutil.rmtree('./test_data_dir_tmp', ignore_errors=True)

    def test_add_fund(self):
        fund = FundProfile(
            fund_id='TEST001', name='Test Fund',
            fund_type=FundType.HEDGE_FUND, inception_date='2020-01-01',
            AUM=100.0, strategy='long_short', benchmark='SPX',
            managers=['Manager A'], geography_focus=['US'],
            sector_focus=['Tech'], vintages=[2020],
        )
        self.analyzer.add_fund(fund)
        self.assertEqual(len(self.analyzer.fund_database), 1)
        self.assertIn('TEST001', self.analyzer.fund_database)

    def test_add_fund_overwrites(self):
        fund1 = FundProfile(
            fund_id='DUPE', name='First', fund_type=FundType.MUTUAL_FUND,
            inception_date='2020-01-01', AUM=10.0, strategy='index',
            benchmark='SPX', managers=[], geography_focus=[], sector_focus=[],
            vintages=[],
        )
        fund2 = FundProfile(
            fund_id='DUPE', name='Second', fund_type=FundType.HEDGE_FUND,
            inception_date='2021-01-01', AUM=20.0, strategy='long_short',
            benchmark='SPX', managers=[], geography_focus=[], sector_focus=[],
            vintages=[],
        )
        self.analyzer.add_fund(fund1)
        self.analyzer.add_fund(fund2)
        self.assertEqual(self.analyzer.fund_database['DUPE'].name, 'Second')

    def test_analyze_sector_performance_returns_valid(self):
        result = self.analyzer.analyze_sector_performance('AI/ML', '1y')
        self.assertIn('sector', result)
        self.assertIn('returns', result)
        self.assertIn('volatility', result)
        self.assertIn('sharpe', result)
        self.assertIn('correlation_with_market', result)
        self.assertIn('momentum_score', result)
        self.assertGreaterEqual(result['returns'], -0.1)
        self.assertLessEqual(result['returns'], 0.3)
        self.assertGreaterEqual(result['volatility'], 0.15)
        self.assertLessEqual(result['volatility'], 0.4)

    def test_detect_hotspots_returns_list(self):
        hotspots = self.analyzer.detect_hotspots()
        self.assertIsInstance(hotspots, list)
        self.assertLessEqual(len(hotspots), 10)
        for h in hotspots:
            self.assertIsInstance(h, SectorHotspot)
            self.assertGreaterEqual(h.score, 0)
            self.assertLessEqual(h.score, 100)

    def test_detect_hotspots_stores_analyzer_hotspots(self):
        self.analyzer.detect_hotspots()
        self.assertGreater(len(self.analyzer.hotspots), 0)

    def test_assess_risk_low(self):
        self.assertEqual(self.analyzer._assess_risk(0.15), 'low')

    def test_assess_risk_medium(self):
        self.assertEqual(self.analyzer._assess_risk(0.25), 'medium')

    def test_assess_risk_high(self):
        self.assertEqual(self.analyzer._assess_risk(0.35), 'high')

    def test_assess_risk_very_high(self):
        self.assertEqual(self.analyzer._assess_risk(0.45), 'very_high')

    def test_assess_risk_boundary_low(self):
        self.assertEqual(self.analyzer._assess_risk(0.20), 'medium')

    def test_assess_risk_boundary_medium(self):
        self.assertEqual(self.analyzer._assess_risk(0.30), 'high')

    def test_assess_risk_boundary_high(self):
        self.assertEqual(self.analyzer._assess_risk(0.40), 'very_high')

    def test_get_timeframe_short_term(self):
        self.assertEqual(self.analyzer._get_timeframe(80), 'short_term')

    def test_get_timeframe_medium_term(self):
        self.assertEqual(self.analyzer._get_timeframe(60), 'medium_term')

    def test_get_timeframe_long_term(self):
        self.assertEqual(self.analyzer._get_timeframe(30), 'long_term')

    def test_get_timeframe_boundary_medium(self):
        self.assertEqual(self.analyzer._get_timeframe(50), 'long_term')

    def test_get_timeframe_boundary_long(self):
        self.assertEqual(self.analyzer._get_timeframe(49), 'long_term')

    def test_get_timeframe_boundary_short(self):
        self.assertEqual(self.analyzer._get_timeframe(76), 'short_term')

    def test_get_themes_known_sector(self):
        themes = self.analyzer._get_themes('AI/ML')
        self.assertGreater(len(themes), 0)
        self.assertIn('大模型', themes)

    def test_get_themes_unknown_sector(self):
        themes = self.analyzer._get_themes('Unknown Sector')
        self.assertEqual(themes, ['新兴技术', '高增长', '政策支持'])

    def test_get_top_funds(self):
        funds = self.analyzer._get_top_funds('AI/ML')
        self.assertEqual(len(funds), 3)
        self.assertTrue(all('AI/ML' in f for f in funds))

    def test_generate_allocation_recommendations(self):
        hotspots = self.analyzer.detect_hotspots()
        recs = self.analyzer.generate_allocation_recommendations(
            investor_profile={'type': 'institutional'},
            target_return=0.15,
            risk_tolerance=0.6,
        )
        self.assertGreater(len(recs), 0)
        for r in recs:
            self.assertIsInstance(r, AllocationRecommendation)
            self.assertGreaterEqual(r.target_weight, 0)
            self.assertLessEqual(r.target_weight, 0.25)
            self.assertGreaterEqual(r.confidence, 0)
            self.assertLessEqual(r.confidence, 0.9)

    def test_generate_allocation_recommendations_stores(self):
        self.analyzer.detect_hotspots()
        self.analyzer.generate_allocation_recommendations(
            investor_profile={}, target_return=0.1, risk_tolerance=0.5,
        )
        self.assertGreater(len(self.analyzer.recommendations), 0)

    def test_run_comprehensive_analysis_empty_db(self):
        result = self.analyzer.run_comprehensive_analysis()
        self.assertIn('hotspots', result)
        self.assertIn('recommendations', result)
        self.assertIn('market_summary', result)
        self.assertIn('fund_analysis', result)
        self.assertEqual(len(result['fund_analysis']), 0)

    def test_run_comprehensive_analysis_with_funds(self):
        for i in range(5):
            fund = FundProfile(
                fund_id=f'R{i:03d}', name=f'Research Fund {i}',
                fund_type=FundType.HEDGE_FUND, inception_date='2020-01-01',
                AUM=np.random.uniform(10, 500), strategy='multi',
                benchmark='SPX', managers=['M1'],
                geography_focus=['US'], sector_focus=['Tech'],
                vintages=[2020],
                returns_1y=np.random.uniform(-0.1, 0.4),
                sharpe_ratio=np.random.uniform(0.5, 2.5),
                max_drawdown=np.random.uniform(-0.2, -0.05),
            )
            self.analyzer.add_fund(fund)

        result = self.analyzer.run_comprehensive_analysis()
        self.assertGreater(len(result['fund_analysis']), 0)
        self.assertGreater(len(result['hotspots']), 0)
        self.assertGreater(len(result['recommendations']), 0)
        summary = result['market_summary']
        self.assertGreater(summary['total_funds_analyzed'], 0)

    def test_run_comprehensive_analysis_with_specific_funds(self):
        fund = FundProfile(
            fund_id='SPEC01', name='Spec Fund',
            fund_type=FundType.VC_FUND, inception_date='2020-01-01',
            AUM=100.0, strategy='growth', benchmark='NASDAQ',
            managers=['M1'], geography_focus=['US'],
            sector_focus=['AI'], vintages=[2020],
            returns_1y=0.25, sharpe_ratio=1.8, max_drawdown=-0.10,
        )
        self.analyzer.add_fund(fund)

        result = self.analyzer.run_comprehensive_analysis(fund_ids=['SPEC01'])
        self.assertEqual(len(result['fund_analysis']), 1)
        self.assertEqual(result['fund_analysis'][0]['fund_id'], 'SPEC01')

    def test_run_comprehensive_analysis_with_nonexistent_funds(self):
        result = self.analyzer.run_comprehensive_analysis(fund_ids=['NONEXIST'])
        self.assertEqual(len(result['fund_analysis']), 0)

    def test_run_comprehensive_analysis_focus_sectors(self):
        result = self.analyzer.run_comprehensive_analysis(focus_sectors=['AI/ML', 'Biotech'])
        self.assertIn('hotspots', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
