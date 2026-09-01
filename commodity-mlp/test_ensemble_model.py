#!/usr/bin/env python3
"""test_ensemble_model.py - CommodityEnsembleModel 单元测试

覆盖：fit/predict、交叉验证、特征重要性、save/load
"""

import sys
import os
import tempfile
import warnings
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'commodity-mlp'))
from ensemble_model import CommodityEnsembleModel

warnings.filterwarnings('ignore')

# ── 固定随机种子，保证可复现 ──
SEED = 20240902


# ═══════════════════════════════════════════════════════════════
# fixture：共享数据与模型实例
# ═══════════════════════════════════════════════════════════════
@pytest.fixture(scope="module")
def sample_data():
    """生成用于训练的样本数据（小数据集加速测试）"""
    np.random.seed(SEED)
    X = np.random.randn(120, 6)
    y = np.random.randint(0, 2, 120)
    feature_names = [f"feat_{i}" for i in range(6)]
    return X, y, feature_names


@pytest.fixture(scope="module")
def voting_model(sample_data):
    """voting 集成模型实例"""
    X, y, _ = sample_data
    m = CommodityEnsembleModel(model_type="voting", voting="soft", random_state=SEED)
    m.fit(X, y)
    return m


@pytest.fixture(scope="module")
def stacking_model(sample_data):
    """stacking 集成模型实例"""
    X, y, _ = sample_data
    m = CommodityEnsembleModel(model_type="stacking", random_state=SEED)
    m.fit(X, y)
    return m


# ═══════════════════════════════════════════════════════════════
# 初始化测试
# ═══════════════════════════════════════════════════════════════
class TestInit:
    def test_default_init(self):
        m = CommodityEnsembleModel()
        assert m.model_type == "voting"
        assert m.voting == "soft"
        assert m.random_state == 42
        assert m.model is None
        assert m.feature_names is None
        assert m.history == []

    @pytest.mark.parametrize("model_type,voting", [
        ("voting", "soft"),
        ("voting", "hard"),
        ("stacking", "soft"),
    ])
    def test_param_init(self, model_type, voting):
        m = CommodityEnsembleModel(model_type=model_type, voting=voting, random_state=7)
        assert m.model_type == model_type
        assert m.voting == voting
        assert m.random_state == 7


# ═══════════════════════════════════════════════════════════════
# fit / predict 测试
# ═══════════════════════════════════════════════════════════════
class TestFitPredict:
    def test_fit_sets_model(self, voting_model):
        assert voting_model.model is not None

    def test_fit_returns_self(self, sample_data):
        X, y, fn = sample_data
        m = CommodityEnsembleModel(model_type="voting")
        result = m.fit(X, y, fn)
        assert result is m

    def test_predict_shape(self, voting_model, sample_data):
        X, y, _ = sample_data
        pred = voting_model.predict(X)
        assert isinstance(pred, np.ndarray)
        assert pred.shape == y.shape

    def test_predict_binary_labels(self, voting_model, sample_data):
        X, y, _ = sample_data
        pred = voting_model.predict(X)
        assert set(pred).issubset({0, 1})

    def test_predict_proba_shape(self, voting_model, sample_data):
        X, y, _ = sample_data
        proba = voting_model.predict_proba(X)
        assert proba.shape[0] == X.shape[0]
        assert proba.shape[1] == 2  # 二分类
        assert np.allclose(proba.sum(axis=1), 1.0)

    def test_history_recorded_after_fit(self, voting_model):
        assert len(voting_model.history) >= 1
        entry = voting_model.history[-1]
        assert entry["type"] == "voting"
        assert isinstance(entry["train_accuracy"], float)
        assert "timestamp" in entry

    def test_stack_predict(self, stacking_model, sample_data):
        X, y, _ = sample_data
        pred = stacking_model.predict(X)
        assert pred.shape == y.shape

    def test_stack_predict_proba(self, stacking_model, sample_data):
        X, _, _ = sample_data
        proba = stacking_model.predict_proba(X)
        assert proba.shape[1] == 2


# ═══════════════════════════════════════════════════════════════
# 交叉验证测试
# ═══════════════════════════════════════════════════════════════
class TestCrossValidate:
    def test_cv_returns_dict(self, voting_model, sample_data):
        X, y, _ = sample_data
        result = voting_model.cross_validate(X, y, cv=3, use_time_series=True)
        assert isinstance(result, dict)
        assert "mean_accuracy" in result
        assert "std_accuracy" in result
        assert "fold_scores" in result
        assert "method" in result

    def test_cv_mean_in_range(self, voting_model, sample_data):
        X, y, _ = sample_data
        result = voting_model.cross_validate(X, y, cv=3)
        assert 0.0 <= result["mean_accuracy"] <= 1.0

    def test_cv_fold_scores_length(self, voting_model, sample_data):
        X, y, _ = sample_data
        result = voting_model.cross_validate(X, y, cv=4)
        assert len(result["fold_scores"]) == 4

    def test_cv_kfold_method(self, voting_model, sample_data):
        X, y, _ = sample_data
        result = voting_model.cross_validate(X, y, cv=3, use_time_series=False)
        assert result["method"] == "kfold"

    def test_cv_timeseries_method(self, voting_model, sample_data):
        X, y, _ = sample_data
        result = voting_model.cross_validate(X, y, cv=3, use_time_series=True)
        assert result["method"] == "time_series"


# ═══════════════════════════════════════════════════════════════
# 特征重要性测试
# ═══════════════════════════════════════════════════════════════
class TestFeatureImportance:
    def test_importance_returns_df(self, voting_model, sample_data):
        _, _, feature_names = sample_data
        df = voting_model.get_feature_importance(top_n=5)
        assert df is not None
        assert "feature" in df.columns
        assert "importance" in df.columns

    def test_importance_sorted_descending(self, voting_model):
        df = voting_model.get_feature_importance(top_n=10)
        if len(df) >= 2:
            assert (df["importance"].diff().dropna() <= 1e-9).all()

    def test_importance_uses_feature_names(self, voting_model, sample_data):
        _, _, feature_names = sample_data
        df = voting_model.get_feature_importance(top_n=6)
        # 所有特征名应能被识别
        assert df["feature"].str.startswith("feat_").all()

    def test_importance_unfitted_raises(self):
        m = CommodityEnsembleModel()
        with pytest.raises(ValueError, match="尚未训练"):
            m.get_feature_importance()


# ═══════════════════════════════════════════════════════════════
# save / load 测试
# ═══════════════════════════════════════════════════════════════
class TestSaveLoad:
    def test_save_and_load_roundtrip(self, voting_model, sample_data, tmp_path):
        X, y, _ = sample_data
        path = str(tmp_path / "model.pkl")
        voting_model.save(path)

        # 新建实例加载
        loaded = CommodityEnsembleModel()
        loaded.load(path)

        pred_orig = voting_model.predict(X)
        pred_load = loaded.predict(X)
        np.testing.assert_array_equal(pred_orig, pred_load)

    def test_save_unfitted_raises(self):
        m = CommodityEnsembleModel()
        with pytest.raises(ValueError, match="可保存的模型"):
            m.save("/tmp/nope.pkl")

    def test_load_preserves_history(self, voting_model, tmp_path):
        path = str(tmp_path / "model2.pkl")
        voting_model.save(path)
        loaded = CommodityEnsembleModel()
        loaded.load(path)
        assert len(loaded.history) == len(voting_model.history)


# ═══════════════════════════════════════════════════════════════
# 异常边界测试
# ═══════════════════════════════════════════════════════════════
class TestEdgeCases:
    def test_predict_before_fit_raises(self):
        m = CommodityEnsembleModel()
        with pytest.raises(AttributeError):
            m.predict(np.array([[1, 2]]))

    def test_fit_with_different_feature_names(self, sample_data):
        X, y, _ = sample_data
        m = CommodityEnsembleModel()
        m.fit(X, y, feature_names=["a", "b", "c", "d", "e", "f"])
        assert m.feature_names == ["a", "b", "c", "d", "e", "f"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
