"""
测试API服务的所有端点 (pytest 版本)
"""
import pytest
import requests
import json
import time
import threading
import sys
import os
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def encode_symbol(symbol):
    """URL编码商品代码（处理=等特殊字符）"""
    return quote(symbol, safe='')


@pytest.fixture(scope="module")
def api_server():
    """启动 API 服务（模块级别复用）"""
    # 先终止可能存在的旧服务
    try:
        r = requests.get('http://localhost:5000/api/health', timeout=1)
        if r.status_code == 200:
            os.system("pkill -f 'api_server' 2>/dev/null")
            time.sleep(2)
    except Exception:
        pass

    from api_server import app
    thread = threading.Thread(target=lambda: app.run(port=5001, debug=False, use_reloader=False))
    thread.daemon = True
    thread.start()
    time.sleep(3)
    yield "http://localhost:5001"
    # teardown: 终止服务
    os.system("pkill -f 'api_server.*5001' 2>/dev/null")


@pytest.fixture
def base_url(api_server):
    return api_server


@pytest.fixture
def sym():
    return "GC=F"


@pytest.fixture
def sym_enc(sym):
    return encode_symbol(sym)


def _call(method, base_url, path, data=None, timeout=120):
    url = f"{base_url}{path}"
    if method == 'GET':
        r = requests.get(url, timeout=timeout)
    else:
        r = requests.post(url, json=data or {}, timeout=timeout)
    return r


def test_health(base_url):
    r = _call('GET', base_url, '/api/health')
    assert r.status_code == 200


def test_symbols(base_url):
    r = _call('GET', base_url, '/api/symbols')
    assert r.status_code == 200


def test_data(base_url, sym_enc):
    r = _call('GET', base_url, f'/api/data/{sym_enc}?days=500')
    assert r.status_code == 200


def test_train_mlp(base_url, sym_enc):
    r = _call('POST', base_url, f'/api/train/{sym_enc}',
              data={'model_type': 'mlp', 'use_real': False})
    assert r.status_code == 200


def test_predict(base_url, sym_enc):
    r = _call('POST', base_url, f'/api/predict/{sym_enc}',
              data={'model_type': 'mlp'})
    assert r.status_code == 200


def test_backtest(base_url, sym_enc):
    r = _call('POST', base_url, f'/api/backtest/{sym_enc}',
              data={'initial_capital': 100000, 'use_real': False})
    assert r.status_code == 200


def test_analysis(base_url, sym_enc):
    r = _call('GET', base_url, f'/api/analysis/{sym_enc}?days=500')
    assert r.status_code == 200


def test_docs(base_url):
    r = _call('GET', base_url, '/api/docs')
    assert r.status_code == 200
