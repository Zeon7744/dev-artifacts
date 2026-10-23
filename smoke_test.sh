#!/usr/bin/env bash
# dev-artifacts 冒烟：import + billing.check_access + pytest 收集
set -uo pipefail
cd "$(dirname "$0")"
PASS=0; FAIL=0
python3 -c "import billing; r=billing.check_access('free','tool_call'); assert r['allowed'] is True; print('billing.check_access OK', r)" \
  && PASS=$((PASS+1)) || { echo "FAIL: billing"; FAIL=$((FAIL+1)); }
N=$(python3 -m pytest --collect-only -q commodity-mlp/ 2>/dev/null | grep -c "::" || echo 0)
echo "commodity-mlp 收集 $N 个测试"
[ "$N" -gt 0 ] && PASS=$((PASS+1)) || { echo "FAIL: pytest 收集"; FAIL=$((FAIL+1)); }
echo "smoke_test: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && echo "=== SMOKE PASS ===" && exit 0 || { echo "=== SMOKE FAIL ==="; exit 1; }
