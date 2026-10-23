#!/usr/bin/env bash
# dev-artifacts 一键跑全部子项目测试
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pytest commodity-mlp/ crypto-mlp/ global-investment-mlp/ short-drama-mcp/ -q
