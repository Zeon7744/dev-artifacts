# dev-artifacts 快速上手（5 分钟跑通）

## 1. 克隆
```bash
git clone https://github.com/Zeon7744/dev-artifacts.git
cd dev-artifacts
```

## 2. 运行子项目测试
```bash
python -m pytest commodity-mlp/ crypto-mlp/ global-investment-mlp/ short-drama-mcp/ -q
```

## 3. 收款与门控
- 各子项目独立定价（见各子目录 billing.py）
- 爱发电：https://afdian.com/@Zeon7744
- 冒烟：`bash smoke_test.sh`
