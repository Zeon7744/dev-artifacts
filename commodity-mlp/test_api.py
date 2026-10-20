"""
测试API服务的所有端点
"""
import requests
import json
import time
import threading
import sys
import os
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 先终止可能存在的旧服务
try:
    r = requests.get('http://localhost:5000/api/health', timeout=1)
    if r.status_code == 200:
        print("✅ 服务已在运行，先关闭旧服务...")
        os.system("pkill -f 'api_server' 2>/dev/null")
        time.sleep(2)
except:
    pass

# 启动新服务
print("🚀 启动API服务...")
from api_server import app
thread = threading.Thread(target=lambda: app.run(port=5000, debug=False, use_reloader=False))
thread.daemon = True
thread.start()
time.sleep(3)

BASE_URL = "http://localhost:5000"

def encode_symbol(symbol):
    """URL编码商品代码（处理=等特殊字符）"""
    return quote(symbol, safe='')

def test_endpoint(method, path, data=None, label=None):
    """测试单个端点"""
    url = f"{BASE_URL}{path}"
    name = label or path
    try:
        if method == 'GET':
            r = requests.get(url, timeout=120)
        else:
            r = requests.post(url, json=data or {}, timeout=120)
        
        status = '✅' if r.status_code == 200 else '⚠️'
        print(f"{status} {method} {name} -> {r.status_code}")
        if r.status_code == 200:
            try:
                j = r.json()
                keys = list(j.keys())[:5]
                print(f"   返回字段: {keys}")
            except:
                pass
        else:
            print(f"   错误: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ {method} {name} -> 异常: {e}")
        return False

print("\n" + "=" * 60)
print("📡 API端点完整测试")
print("=" * 60)

results = {}
SYM = "GC=F"
SYM_ENC = encode_symbol(SYM)

# 1. 健康检查
print("\n--- 基础接口 ---")
results['health'] = test_endpoint('GET', '/api/health')

# 2. 商品列表
results['symbols'] = test_endpoint('GET', '/api/symbols')

# 3. 数据获取
print("\n--- 数据接口 ---")
results['data'] = test_endpoint('GET', f'/api/data/{SYM_ENC}?days=500',
                                 label=f'/api/data/{SYM}')

# 4. 模型训练
print("\n--- 训练接口 ---")
results['train_mlp'] = test_endpoint('POST', f'/api/train/{SYM_ENC}',
                                      data={'model_type': 'mlp', 'use_real': False},
                                      label=f'/api/train/{SYM}')

# 5. 预测
print("\n--- 预测接口 ---")
results['predict'] = test_endpoint('POST', f'/api/predict/{SYM_ENC}',
                                    data={'model_type': 'mlp'},
                                    label=f'/api/predict/{SYM}')

# 6. 回测
print("\n--- 回测接口 ---")
results['backtest'] = test_endpoint('POST', f'/api/backtest/{SYM_ENC}',
                                     data={'initial_capital': 100000, 'use_real': False},
                                     label=f'/api/backtest/{SYM}')

# 7. 综合分析报告
print("\n--- 分析接口 ---")
results['analysis'] = test_endpoint('GET', f'/api/analysis/{SYM_ENC}?days=500',
                                     label=f'/api/analysis/{SYM}')

# 8. API文档
results['docs'] = test_endpoint('GET', '/api/docs')

# 汇总
print("\n" + "=" * 60)
print("📊 测试结果汇总")
print("=" * 60)
total = len(results)
passed = sum(1 for v in results.values() if v)
for name, ok in results.items():
    print(f"  {'✅' if ok else '❌'} {name}")

print(f"\n总计: {passed}/{total} 通过")
if passed == total:
    print("🎉 所有API端点测试通过！")
else:
    print("⚠️ 部分端点需要修复")
