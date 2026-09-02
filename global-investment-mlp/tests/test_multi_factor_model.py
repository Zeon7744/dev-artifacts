"""Tests for multi_factor_model.py"""

import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_factor_model import MultiFactorModel, SectorRotationModel


class TestMultiFactorModel(unittest.TestCase):
    """测试 MultiFactorModel 类"""

    def setUp(self):
        np.random.seed(42)
        self.n_samples = 200
        self.n_factors = 10
        self.X = np.random.randn(self.n_samples, self.n_factors)
        self.y = np.random.choice([0, 1], size=self.n_samples)
        self.factors = [f'factor_{i}' for i in range(self.n_factors)]

    def test_init_default(self):
        model = MultiFactorModel()
        self.assertGreater(len(model.factors), 0)
        self.assertEqual(model.optimization_method, 'ic_weighting')
        self.assertEqual(model.rebalance_frequency, 'quarterly')

    def test_init_custom(self):
        model = MultiFactorModel(
            factors=self.factors,
            optimization_method='ml_ranking',
            rebalance_frequency='monthly',
        )
        self.assertEqual(len(model.factors), self.n_factors)
        self.assertEqual(model.optimization_method, 'ml_ranking')
        self.assertEqual(model.rebalance_frequency, 'monthly')

    def test_get_default_factors_count(self):
        model = MultiFactorModel()
        self.assertGreater(len(model._get_default_factors()), 15)

    def test_prepare_data(self):
        model = MultiFactorModel(factors=self.factors)
        df = pd.DataFrame(self.X, columns=self.factors)
        df['return_future_1m'] = self.y
        X_scaled, y, feature_names = model.prepare_data(df)
        self.assertEqual(X_scaled.shape, (self.n_samples, self.n_factors))
        self.assertEqual(len(y), self.n_samples)
        self.assertEqual(len(feature_names), self.n_factors)

    def test_prepare_data_missing_target(self):
        model = MultiFactorModel(factors=self.factors)
        df = pd.DataFrame(self.X, columns=self.factors)
        X_scaled, y, feature_names = model.prepare_data(df)
        self.assertIsNone(y)

    def test_prepare_data_not_enough_factors(self):
        model = MultiFactorModel(factors=self.factors)
        df = pd.DataFrame(np.random.randn(50, 3), columns=['a', 'b', 'c'])
        df['return_future_1m'] = np.random.choice([0, 1], 50)
        with self.assertRaises(ValueError):
            model.prepare_data(df)

    def test_prepare_data_with_nans(self):
        model = MultiFactorModel(factors=self.factors)
        X_with_nan = self.X.copy()
        X_with_nan[0, 0] = np.nan
        X_with_nan[1, 1] = np.inf
        df = pd.DataFrame(X_with_nan, columns=self.factors)
        df['return_future_1m'] = self.y
        X_scaled, y, _ = model.prepare_data(df)
        self.assertFalse(np.isnan(X_scaled).any())
        self.assertFalse(np.isinf(X_scaled).any())

    def test_optimize_weights_ic_weighting(self):
        model = MultiFactorModel(factors=self.factors, optimization_method='ic_weighting')
        weights = model.optimize_weights(self.X, self.y)
        self.assertEqual(len(weights), self.n_factors)
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_optimize_weights_ml_ranking(self):
        model = MultiFactorModel(factors=self.factors, optimization_method='ml_ranking')
        weights = model.optimize_weights(self.X, self.y)
        self.assertEqual(len(weights), self.n_factors)
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_optimize_weights_optimization(self):
        model = MultiFactorModel(factors=self.factors[:5], optimization_method='optimization')
        weights = model.optimize_weights(self.X[:100, :5], self.y[:100])
        self.assertEqual(len(weights), 5)
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_calculate_factor_ic(self):
        model = MultiFactorModel(factors=self.factors)
        ic = model.calculate_factor_ic(self.X, self.y)
        self.assertEqual(len(ic), self.n_factors)
        for k, v in ic.items():
            self.assertIsInstance(v, float)
            self.assertGreaterEqual(v, -1.0)
            self.assertLessEqual(v, 1.0)

    def test_calculate_factor_score(self):
        model = MultiFactorModel(factors=self.factors)
        model.optimize_weights(self.X, self.y)
        scores = model.calculate_factor_score(self.X)
        self.assertEqual(len(scores), self.n_samples)

    def test_calculate_factor_score_no_weights(self):
        """未优化权重时使用空权重"""
        model = MultiFactorModel(factors=self.factors)
        scores = model.calculate_factor_score(self.X)
        self.assertEqual(len(scores), self.n_samples)

    def test_generate_rankings(self):
        model = MultiFactorModel(factors=self.factors)
        model.optimize_weights(self.X, self.y)
        rankings = model.generate_rankings(self.X)
        self.assertEqual(len(rankings), self.n_samples)
        self.assertIn('factor_score', rankings.columns)
        self.assertIn('rank', rankings.columns)
        self.assertIn('quintile', rankings.columns)
        self.assertTrue(rankings['quintile'].isin([1, 2, 3, 4, 5]).all())

    def test_backtest(self):
        model = MultiFactorModel(factors=self.factors, optimization_method='ic_weighting')
        model.optimize_weights(self.X, self.y)
        results = model.backtest(self.X, self.y)
        self.assertIn('long_short_return', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('quintile_returns', results)
        self.assertIn('ic_mean', results)
        self.assertIn('n_factors', results)
        self.assertIn('n_samples', results)

    def test_backtest_top_quintile_false(self):
        model = MultiFactorModel(factors=self.factors, optimization_method='ic_weighting')
        model.optimize_weights(self.X, self.y)
        results = model.backtest(self.X, self.y, top_quintile_ret=False)
        self.assertIn('long_short_return', results)

    def test_get_factor_contribution(self):
        model = MultiFactorModel(factors=self.factors, optimization_method='ic_weighting')
        model.optimize_weights(self.X, self.y)
        contributions = model.get_factor_contribution()
        self.assertEqual(len(contributions), self.n_factors)
        total = sum(contributions.values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_factor_ic_stored(self):
        model = MultiFactorModel(factors=self.factors)
        model.calculate_factor_ic(self.X, self.y)
        self.assertGreater(len(model.factor_ic), 0)

    def test_backtest_stores_results(self):
        model = MultiFactorModel(factors=self.factors, optimization_method='ic_weighting')
        model.optimize_weights(self.X, self.y)
        model.backtest(self.X, self.y)
        self.assertGreater(len(model.backtest_results), 0)


class TestSectorRotationModel(unittest.TestCase):
    """测试 SectorRotationModel 类"""

    def setUp(self):
        np.random.seed(42)
        self.sector_returns = {
            'Technology': pd.Series(np.random.randn(252) * 0.01 + 0.001),
            'Healthcare': pd.Series(np.random.randn(252) * 0.008 + 0.0005),
            'Finance': pd.Series(np.random.randn(252) * 0.012 - 0.0003),
            'Energy': pd.Series(np.random.randn(252) * 0.015 + 0.0008),
            'Consumer': pd.Series(np.random.randn(252) * 0.006 + 0.0002),
        }

    def test_analyze_momentum(self):
        model = SectorRotationModel()
        result = model.analyze_momentum(self.sector_returns)
        self.assertEqual(len(result), 5)
        for sector, data in result.items():
            self.assertIn('momentum_1m', data)
            self.assertIn('momentum_3m', data)
            self.assertIn('momentum_6m', data)
            self.assertIn('composite_score', data)
            self.assertIsInstance(data['composite_score'], float)

    def test_detect_rotation_no_momentum(self):
        model = SectorRotationModel()
        result = model.detect_rotation(market_regime='expansion')
        self.assertEqual(result['signal'], 'neutral')
        self.assertEqual(result['sectors'], {})

    def test_detect_rotation_expansion(self):
        model = SectorRotationModel()
        model.analyze_momentum(self.sector_returns)
        result = model.detect_rotation(market_regime='expansion')
        self.assertEqual(result['regime'], 'expansion')
        self.assertIn('Technology', result['recommended_sectors'])
        self.assertGreater(len(result['top_momentum_sectors']), 0)

    def test_detect_rotation_recession(self):
        model = SectorRotationModel()
        model.analyze_momentum(self.sector_returns)
        result = model.detect_rotation(market_regime='recession')
        self.assertIn('Consumer Staples', result['recommended_sectors'])

    def test_detect_rotation_early_cycle(self):
        model = SectorRotationModel()
        model.analyze_momentum(self.sector_returns)
        result = model.detect_rotation(market_regime='early_cycle')
        self.assertIn('Technology', result['recommended_sectors'])

    def test_detect_rotation_late_cycle(self):
        model = SectorRotationModel()
        model.analyze_momentum(self.sector_returns)
        result = model.detect_rotation(market_regime='late_cycle')
        self.assertIn('Energy', result['recommended_sectors'])

    def test_detect_rotation_unknown_regime(self):
        model = SectorRotationModel()
        model.analyze_momentum(self.sector_returns)
        result = model.detect_rotation(market_regime='unknown_regime')
        self.assertEqual(result['regime'], 'unknown_regime')
        self.assertEqual(result['recommended_sectors'], [])

    def test_rotation_signal_stored(self):
        model = SectorRotationModel()
        model.analyze_momentum(self.sector_returns)
        model.detect_rotation(market_regime='expansion')
        self.assertIsNotNone(model.rotation_signal)

    def test_rotation_strength(self):
        model = SectorRotationModel()
        model.analyze_momentum(self.sector_returns)
        result = model.detect_rotation(market_regime='expansion')
        self.assertGreaterEqual(result['rotation_strength'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
