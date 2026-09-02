"""
commodity-mlp 测试夹具
"""
import sys
import os
import pytest
import numpy as np
import pandas as pd

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def symbol():
    """默认商品代码"""
    return "GC=F"


@pytest.fixture
def symbols():
    """商品代码列表"""
    return ["GC=F", "CL=F"]


@pytest.fixture
def features():
    """示例特征数据 (DataFrame)，样本量足够大以支持 LSTM 序列切分"""
    np.random.seed(42)
    n_samples, n_features = 500, 13
    col_names = [f'feature_{i}' for i in range(n_features)]
    return pd.DataFrame(np.random.rand(n_samples, n_features), columns=col_names)


@pytest.fixture
def target():
    """示例目标数据 (Series, 二分类标签，兼容 LSTM BCELoss)"""
    np.random.seed(42)
    labels = np.random.choice([0, 1], size=500, p=[0.5, 0.5])
    return pd.Series(labels, name='Target')


@pytest.fixture
def df():
    """示例商品数据 DataFrame (包含 OHLCV + Target)"""
    np.random.seed(42)
    n = 200
    dates = pd.date_range('2024-01-01', periods=n, freq='D')
    data = {
        'Open': np.random.uniform(1800, 2100, n),
        'High': np.random.uniform(1900, 2200, n),
        'Low': np.random.uniform(1700, 2000, n),
        'Close': np.random.uniform(1800, 2100, n),
        'Volume': np.random.uniform(100000, 500000, n),
        'Target': np.random.choice([0, 1, 2], n, p=[0.4, 0.4, 0.2]),
    }
    return pd.DataFrame(data, index=dates)
