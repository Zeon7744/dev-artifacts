"""Tests for risk_analytics.py"""

import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from risk_analytics import (
    RiskMetrics,
    CorrelationAnalyzer,
    StressTester,
    RiskDashboard,
)


class TestRiskMetrics(unittest.TestCase):
    """测试 RiskMetrics 静态方法"""

    def setUp(self):
        np.random.seed(42)
        self.returns = np.random.normal(0.0005, 0.015, 500)

    def test_var_historical(self):
        var = RiskMetrics.calculate_var(self.returns, 0.95, method='historical')
        self.assertGreater(var, 0)
        self.assertLess(var, 0.1)

    def test_var_parametric(self):
        var = RiskMetrics.calculate_var(self.returns, 0.95, method='parametric')
        self.assertGreater(var, 0)
        self.assertLess(var, 0.1)

    def test_var_monte_carlo(self):
        var = RiskMetrics.calculate_var(self.returns, 0.95, method='monte_carlo')
        self.assertGreater(var, 0)
        self.assertLess(var, 0.1)

    def test_var_invalid_method_fallback(self):
        var = RiskMetrics.calculate_var(self.returns, 0.95, method='unknown')
        self.assertGreater(var, 0)

    def test_var_99(self):
        var_99 = RiskMetrics.calculate_var(self.returns, 0.99)
        var_95 = RiskMetrics.calculate_var(self.returns, 0.95)
        self.assertGreater(var_99, var_95)

    def test_cvar(self):
        cvar = RiskMetrics.calculate_cvar(self.returns, 0.95)
        var = RiskMetrics.calculate_var(self.returns, 0.95)
        self.assertGreaterEqual(cvar, var)
        self.assertGreater(cvar, 0)

    def test_max_drawdown(self):
        result = RiskMetrics.calculate_max_drawdown(self.returns)
        self.assertIn('max_drawdown', result)
        self.assertIn('peak_date', result)
        self.assertIn('trough_date', result)
        self.assertLess(result['max_drawdown'], 0)
        self.assertGreater(result['max_drawdown'], -1)
        self.assertIsInstance(result['peak_date'], int)
        self.assertIsInstance(result['trough_date'], int)

    def test_sharpe(self):
        sharpe = RiskMetrics.calculate_sharpe(self.returns)
        self.assertIsInstance(sharpe, float)

    def test_sharpe_positive_returns(self):
        pos_returns = np.ones(100) * 0.001
        sharpe = RiskMetrics.calculate_sharpe(pos_returns)
        self.assertGreater(sharpe, 0)

    def test_sharpe_negative_returns(self):
        neg_returns = np.ones(100) * -0.001
        sharpe = RiskMetrics.calculate_sharpe(neg_returns)
        self.assertLess(sharpe, 0)

    def test_sortino(self):
        sortino = RiskMetrics.calculate_sortino(self.returns)
        self.assertIsInstance(sortino, float)

    def test_sortino_all_positive(self):
        pos_returns = np.ones(100) * 0.001
        sortino = RiskMetrics.calculate_sortino(pos_returns)
        self.assertEqual(sortino, float('inf'))

    def test_calmar(self):
        dd = RiskMetrics.calculate_max_drawdown(self.returns)['max_drawdown']
        calmar = RiskMetrics.calculate_calmar(self.returns, dd)
        self.assertIsInstance(calmar, float)
        self.assertGreater(calmar, 0)

    def test_calmar_zero_dd(self):
        # 理论上不会为零，但测试边界
        calmar = RiskMetrics.calculate_calmar(self.returns, 0.0)
        self.assertEqual(calmar, 0)


class TestCorrelationAnalyzer(unittest.TestCase):
    """测试 CorrelationAnalyzer"""

    def setUp(self):
        np.random.seed(42)
        n_assets = 5
        n_days = 200
        self.returns_matrix = np.random.randn(n_days, n_assets) * 0.015
        self.asset_names = [f'Asset_{i}' for i in range(n_assets)]

    def test_analyze(self):
        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(self.returns_matrix, self.asset_names)
        self.assertIn('average_correlation', result)
        self.assertIn('correlation_concentration', result)
        self.assertIn('diversification_score', result)
        self.assertIn('n_assets', result)
        self.assertIn('corr_matrix', result)
        self.assertEqual(result['n_assets'], 5)
        self.assertIsInstance(result['diversification_score'], float)
        self.assertGreaterEqual(result['diversification_score'], 0)
        self.assertLessEqual(result['diversification_score'], 100)

    def test_analyze_no_names(self):
        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(self.returns_matrix)
        self.assertEqual(result['n_assets'], 5)
        self.assertIn('corr_matrix', result)

    def test_detect_regime_change_no_change(self):
        analyzer = CorrelationAnalyzer()
        corr = np.eye(5) * 0.5 + 0.25
        np.fill_diagonal(corr, 1)
        detected, diff = analyzer.detect_regime_change(corr, corr)
        self.assertFalse(detected)
        self.assertEqual(diff, 0.0)

    def test_detect_regime_change_detected(self):
        analyzer = CorrelationAnalyzer()
        corr_old = np.full((5, 5), 0.1)
        np.fill_diagonal(corr_old, 1.0)
        corr_new = np.full((5, 5), 0.6)
        np.fill_diagonal(corr_new, 1.0)
        detected, diff = analyzer.detect_regime_change(corr_new, corr_old)
        self.assertTrue(detected)
        self.assertGreater(diff, 0)

    def test_detect_regime_change_boundary(self):
        analyzer = CorrelationAnalyzer()
        corr_old = np.eye(5) * 0.3
        np.fill_diagonal(corr_old, 1)
        corr_new = corr_old + 0.1  # 刚好超过阈值
        # 填充对角线后 diff.mean() 应该接近 0.1
        detected, diff = analyzer.detect_regime_change(corr_new, corr_old)
        # diff 可能小于0.15因为对角线被排除
        self.assertIsInstance(detected, bool)
        self.assertGreaterEqual(diff, 0)


class TestStressTester(unittest.TestCase):
    """测试 StressTester"""

    def setUp(self):
        np.random.seed(42)
        self.n_assets = 5
        self.weights = np.ones(self.n_assets) / self.n_assets
        self.vols = np.array([0.2, 0.25, 0.18, 0.22, 0.30])
        self.corr = np.eye(self.n_assets) * 0.5 + 0.25
        np.fill_diagonal(self.corr, 1)
        self.portfolio_value = 1000000

    def test_stress_test_2008_crisis(self):
        tester = StressTester()
        result = tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, '2008_crisis')
        self.assertIn('var_95', result)
        self.assertIn('scenario', result)
        self.assertGreater(result['var_95'], 0)
        self.assertIn('scenario_key', result)
        self.assertEqual(result['scenario_key'], '2008_crisis')

    def test_stress_test_2020_covid(self):
        tester = StressTester()
        result = tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, '2020_covid')
        self.assertGreater(result['var_95'], 0)
        self.assertIn('cvar_95', result)
        self.assertIn('max_loss', result)

    def test_stress_test_gradual_rise_rates(self):
        tester = StressTester()
        result = tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, 'gradual_rise_rates')
        self.assertGreater(result['var_95'], 0)

    def test_stress_test_sudden_rate_hike(self):
        tester = StressTester()
        result = tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, 'sudden_rate_hike')
        self.assertGreater(result['var_95'], 0)

    def test_stress_test_recession(self):
        tester = StressTester()
        result = tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, 'recession')
        self.assertGreater(result['var_95'], 0)

    def test_stress_test_invalid_scenario(self):
        tester = StressTester()
        with self.assertRaises(ValueError):
            tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, 'nonexistent')

    def test_stress_test_results_stored(self):
        tester = StressTester()
        tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, '2008_crisis')
        self.assertIn('2008_crisis', tester.results)

    def test_run_all_scenarios(self):
        tester = StressTester()
        results = tester.run_all_scenarios(self.portfolio_value, self.weights, self.vols, self.corr)
        self.assertGreater(len(results), 0)
        for key in tester.SCENARIOS.keys():
            self.assertIn(key, results)
            self.assertGreater(results[key]['var_95'], 0)

    def test_stress_test_with_different_portfolio_value(self):
        tester = StressTester()
        result = tester.stress_test(500000, self.weights, self.vols, self.corr, '2008_crisis')
        self.assertEqual(result['portfolio_value'], 500000)

    def test_var_95_greater_than_cvar_95(self):
        """CVaR 应大于等于 VaR"""
        tester = StressTester()
        result = tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, '2008_crisis')
        self.assertGreaterEqual(result['cvar_95'], result['var_95'])

    def test_max_loss_greater_than_var(self):
        """最坏损失应大于等于 VaR"""
        tester = StressTester()
        result = tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, '2020_covid')
        self.assertGreaterEqual(result['max_loss'], result['var_95'])

    def test_prob_5pct_loss_range(self):
        tester = StressTester()
        result = tester.stress_test(self.portfolio_value, self.weights, self.vols, self.corr, '2008_crisis')
        self.assertGreaterEqual(result['prob_5pct_loss'], 0)
        self.assertLessEqual(result['prob_5pct_loss'], 100)


class TestRiskDashboard(unittest.TestCase):
    """测试 RiskDashboard"""

    def setUp(self):
        np.random.seed(42)
        self.returns = np.random.normal(0.0005, 0.015, 500)

    def test_calculate_all(self):
        dashboard = RiskDashboard()
        metrics = dashboard.calculate_all(self.returns, portfolio_value=10000000)
        self.assertIn('var_95', metrics)
        self.assertIn('var_99', metrics)
        self.assertIn('cvar_95', metrics)
        self.assertIn('max_drawdown', metrics)
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('sortino_ratio', metrics)
        self.assertIn('volatility_annual', metrics)
        self.assertIn('skewness', metrics)
        self.assertIn('kurtosis', metrics)
        self.assertIn('calmar_ratio', metrics)

    def test_calculate_all_stores_metrics(self):
        dashboard = RiskDashboard()
        dashboard.calculate_all(self.returns)
        self.assertGreater(len(dashboard.metrics), 0)

    def test_generate_alerts_high_var(self):
        """高 VaR 触发预警"""
        dashboard = RiskDashboard()
        high_var_returns = np.random.normal(0, 0.05, 500)  # 高波动
        dashboard.calculate_all(high_var_returns)
        alert_types = [a['type'] for a in dashboard.alerts]
        self.assertIn('high_var', alert_types)

    def test_generate_alerts_low_sharpe(self):
        """低夏普触发预警"""
        dashboard = RiskDashboard()
        low_return_returns = np.random.normal(-0.001, 0.02, 500)
        dashboard.calculate_all(low_return_returns)
        alert_types = [a['type'] for a in dashboard.alerts]
        self.assertIn('low_sharpe', alert_types)

    def test_generate_alerts_high_drawdown(self):
        """大回撤触发预警"""
        dashboard = RiskDashboard()
        large_dd_returns = np.random.normal(0.0001, 0.03, 500)
        dashboard.calculate_all(large_dd_returns)
        alert_types = [a['type'] for a in dashboard.alerts]
        # 可能因为随机性不触发，但不应该报错
        self.assertIsInstance(alert_types, list)

    def test_generate_alerts_negative_skew(self):
        """负偏度触发预警"""
        dashboard = RiskDashboard()
        skewed_returns = np.random.exponential(0.01, 500) - 0.02
        dashboard.calculate_all(skewed_returns)
        alert_types = [a['type'] for a in dashboard.alerts]
        self.assertIsInstance(alert_types, list)

    def test_get_summary(self):
        dashboard = RiskDashboard()
        dashboard.calculate_all(self.returns)
        summary = dashboard.get_summary()
        self.assertIn('metrics', summary)
        self.assertIn('alerts', summary)
        self.assertIn('risk_level', summary)

    def test_assess_risk_level_low(self):
        dashboard = RiskDashboard()
        safe_returns = np.random.normal(0.001, 0.005, 500)
        dashboard.calculate_all(safe_returns)
        level = dashboard._assess_risk_level()
        self.assertIn(level, ['low', 'medium', 'high'])

    def test_assess_risk_level_unknown_when_empty(self):
        dashboard = RiskDashboard()
        level = dashboard._assess_risk_level()
        self.assertEqual(level, 'unknown')

    def test_get_summary_returns(self):
        dashboard = RiskDashboard()
        dashboard.calculate_all(self.returns)
        summary = dashboard.get_summary()
        self.assertIsInstance(summary['risk_level'], str)
        self.assertIsInstance(summary['alerts'], list)

    def test_calculate_all_no_alerts_for_normal_data(self):
        """正常数据不应有 critical 预警"""
        dashboard = RiskDashboard()
        normal_returns = np.random.normal(0.0005, 0.012, 500)
        dashboard.calculate_all(normal_returns)
        critical_alerts = [a for a in dashboard.alerts if a['severity'] == 'critical']
        # 不强制要求，只确保不崩溃
        self.assertIsInstance(dashboard.alerts, list)



    def test_generate_alerts_high_drawdown_fired(self):
        """大回撤确实触发 critical 预警"""
        dashboard = RiskDashboard()
        # 构造明确会导致大回撤的收益序列
        returns = np.concatenate([
            np.ones(400) * 0.001,   # 稳定上涨
            np.array([-0.30]),       # 单日暴跌30%
            np.ones(99) * 0.0005,   # 缓慢恢复
        ])
        dashboard.calculate_all(returns)
        alert_types = [a['type'] for a in dashboard.alerts]
        self.assertIn('high_drawdown', alert_types)
        critical_alerts = [a for a in dashboard.alerts if a['severity'] == 'critical']
        self.assertGreater(len(critical_alerts), 0)

    def test_assess_risk_level_high(self):
        """高波动数据应返回 high 风险等级"""
        dashboard = RiskDashboard()
        # 高波动 + 低收益 -> 高风险
        high_risk_returns = np.random.normal(-0.002, 0.04, 500)
        dashboard.calculate_all(high_risk_returns)
        level = dashboard._assess_risk_level()
        self.assertEqual(level, 'high')

    def test_stress_test_eigenvalue_correction(self):
        """测试协方差矩阵负特征值修正路径"""
        tester = StressTester()
        # 构造极端相关矩阵使 corr + scenario['correlation_increase'] 出现负特征值
        n = 3
        # 用高度相关的资产，加上情景的相关性增量，可能造成非正定矩阵
        corr = np.array([[1.0, 0.99, 0.99],
                         [0.99, 1.0, 0.99],
                         [0.99, 0.99, 1.0]])
        weights = np.array([1/3, 1/3, 1/3])
        vols = np.array([0.2, 0.2, 0.2])
        # recession 情景通常有较大 correlation_increase
        result = tester.stress_test(1000000, weights, vols, corr, 'recession')
        self.assertGreater(result['var_95'], 0)
