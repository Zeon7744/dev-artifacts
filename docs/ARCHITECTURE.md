# dev-artifacts 模块结构

## 目录（多子项目聚合仓）
```
dev-artifacts/
├── commodity-mlp/        # 商品多因子（32 测试）
├── crypto-mlp/           # 加密多因子（18 测试）
├── global-investment-mlp/# 全球投资 MLP（13 测试）
├── short-drama-mcp/      # 短剧 MCP（118 测试）
├── billing.py            # 顶层收款层
├── cli.py / tools.py     # 顶层 CLI 工具
└── docs/
```

## 数据流
各子项目独立：数据获取 → 多因子 → 风控 → 报告；测试走 pytest。
