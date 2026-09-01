# Investment MCP Server

统一投资分析 MCP 服务器，整合 crypto-mlp、commodity-mlp、global-investment-mlp 三个 MLP 项目的预测、分析、回测能力。

## 特性

- **加密货币预测**: BTC/ETH等主流币种趋势预测
- **大宗商品分析**: 黄金、原油、白银等投资机会
- **基金分析**: 对冲基金、VC、PE等全球投资
- **历史回测**: 策略回测与绩效评估
- **市场状态识别**: 趋势/震荡/高波动期检测

## 协议版本

MCP 2026-07-28 无状态协议

## 工具列表

| 工具名 | 描述 |
|--------|------|
| `predict_crypto` | 加密货币趋势预测，提供方向判断和置信度 |
| `detect_regime` | 市场状态识别（trending/range/volatility） |
| `analyze_commodity` | 大宗商品（黄金/原油等）MLP分析 |
| `analyze_fund` | 全球基金表现与配置建议 |
| `run_backtest` | 历史策略回测（收益率/回撤/夏普） |
| `list_tools` | 列出所有可用工具 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行服务器

```bash
# 直接运行 Python 服务器
python server_core.py

# 或使用 HTTP 部署
python http_server.py --port 8080
```

### 3. 配置 Coze/扣子

在 `.mcp.json` 中添加：

```json
{
  "mcpServers": {
    "investment-mcp": {
      "command": "python",
      "args": ["/path/to/server_core.py"]
    }
  }
}
```

## API 端点

### Discover（能力发现）

```http
POST /mcp
Mcp-Method: server/discover
Mcp-Name: investment-mcp
```

### 列出工具

```http
POST /mcp
Mcp-Method: tools/list
Mcp-Name: investment-mcp
```

### 调用工具

```http
POST /mcp
Mcp-Method: tools/call
Mcp-Name: predict_crypto

{
  "coin": "BTC",
  "timeframe": "4h",
  "account_balance": 10000
}
```

## 项目结构

```
investment-mcp/
├── server_core.py      # 主服务器实现
├── http_server.py      # HTTP 部署入口
├── requirements.txt    # Python 依赖
├── README.md          # 本文档
└── .mcp.json          # Coze 配置示例
```

## 依赖项目

- [crypto-mlp](https://github.com/Zeon7744/crypto-mlp-high-confidence)
- commodity-mlp
- global-investment-mlp

## 注意事项

1. 服务器启动前需确保三个 MLP 项目已正确安装
2. 首次运行会自动下载历史数据
3. 预测结果仅供参考，不构成投资建议

## License

MIT
