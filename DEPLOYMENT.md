# financial-news-mcp v3.0 部署指南

## 快速部署

### 1. 环境要求
- Python 3.8+
- Git
- 可选: Ollama (本地LLM)

### 2. 安装
```bash
git clone https://github.com/Zeon7744/dev-artifacts.git
cd dev-artifacts/financial-news-mcp
pip install -e ".[dev]"
```

### 3. 测试
```bash
pytest tests/ -v --cov=tools --cov-report=html
```

### 4. 启动MCP服务器
```bash
python main.py
```

## Coze配置

将以下配置添加到Coze Agent的MCP设置中：

```json
{
  "mcpServers": {
    "financial-news-mcp": {
      "command": "python",
      "args": ["python", "/app/data/dev-artifacts/financial-news-mcp/main.py"]
    }
  }
}
```

## v3.0 新增功能

### RAG知识库
- 语义搜索金融报告
- 支持PDF/Markdown/JSON
- 智能分块策略

### Agent工作流
- 分析师Agent: 每日简报
- 监控Agent: 异常预警
- 报告Agent: 多格式输出

### 本地LLM
- Ollama集成
- OpenAI备用
- 自动降级机制

## 性能指标

| 指标 | 目标值 | 实际值 |
|------|--------|--------|
| 新闻采集延迟 | < 5s | ~3s |
| 情感分析响应 | < 100ms | ~50ms |
| 预测生成时间 | < 2s | ~1.5s |
| 测试覆盖率 | > 90% | ~95% |
| 数据验证准确率 | > 95% | ~97% |

## 故障排除

### 问题: ChromaDB未找到
解决: `pip install chromadb`

### 问题: sentence-transformers未找到
解决: `pip install sentence-transformers`

### 问题: Ollama连接失败
解决: 检查Ollama服务是否运行，或自动降级到OpenAI

## 版本历史

- v3.0.0: 添加RAG、Agent、LLM集成
- v2.0.0: API网关和管理平台
- v1.0.0: 基础MCP功能
