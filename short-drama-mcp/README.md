# Short Drama MCP Server

短剧创作 MCP 服务器 — 集成剧本校验、爽点统计、集纲生成等创作工具。

基于 [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) 规范构建（无状态协议）。

## 🎬 工具列表

| 工具 | 功能 | 复用模块 |
|------|------|---------|
| `check_script_format` | 校验剧本格式（禁止字符、括号、标题、对话） | baibai/tools/format_checker.py |
| `count_shuang_points` | 统计爽点密度和分布 | tools/shuang_analyzer.py |
| `generate_episode_outline` | 根据小说生成集纲大纲 | tools/outline_generator.py |
| `check_platform_compliance` | 红果平台投稿规范检查 | tools/platform_checker.py |
| `classify_content` | 内容分类（短剧/小说/教程等） | baibai/tools/classifier.py |

## 📦 安装

```bash
pip install -e ".[dev]"
```

## 🚀 使用方法

### 作为 MCP 服务器启动

```bash
python main.py
```

### 配置 MCP 客户端

```json
{
  "mcpServers": {
    "short-drama-creator": {
      "command": "python",
      "args": ["/Coze/Drive/红剑/dev-artifacts/short-drama-mcp/main.py"]
    }
  }
}
```

### CLI 模式（直接调用工具）

```bash
# 校验剧本格式
python -c "from tools.format_checker import check_markdown_file; print(check_markdown_file('script.md'))"

# 统计爽点
python tools/shuang_analyzer.py <剧本路径>

# 检查平台合规
python tools/platform_checker.py <剧本路径>

# 内容分类
python tools/classifier.py <目录路径>
```

## 📋 工具详情

### check_script_format

校验剧本是否符合短剧创作规范：
- ✅ 禁止字符检测：耀、曜
- ✅ 禁止括号检测：【】
- ✅ 标题格式验证：第X集：集名
- ✅ 结尾格式验证：第X集完
- ✅ 严格模式：检查对话长度（≤15字）

**参数：**
- `filepath` (str): 剧本文件路径
- `strict_mode` (bool): 是否启用严格模式

### count_shuang_points

统计剧本中的爽点密度：
- 📊 总爽点数、总甜点数
- 📈 每集爽点分布
- 🎯 爽点类型分析（打脸反转、实力展现、危机解除等）
- ✅ 平台标准达标检查（≥3爽点/集，≥500字/集）

### generate_episode_outline

根据小说内容生成集纲大纲：
- 📝 自动提取小说结构
- 🎬 按题材生成集标题
- ⏱️ 估算每集字数
- 💡 提供创作建议

**参数：**
- `novel_content` (str): 小说内容或文件路径
- `total_episodes` (int): 目标集数（默认10）
- `genre` (str): 题材类型（默认"玄幻重生"）

### check_platform_compliance

检查是否符合红果短剧平台投稿规范：
- ✅ 标题格式规范
- ✅ 结尾格式规范
- ✅ 对话长度限制（≤15字）
- ✅ 爽点密度要求（≥3爽点/集）
- ✅ 字数要求（≥500字/集）
- ✅ 禁止元素检测

### classify_content

自动识别文件类型：
- 🎭 短剧剧本
- 📖 短篇小说
- 📚 教程文档
- 🔧 工具脚本
- ⚙️ 配置文件

## 📁 项目结构

```
short-drama-mcp/
├── main.py              # MCP 服务器入口
├── pyproject.toml       # 项目配置
├── .mcp.json            # MCP 客户端配置模板
├── README.md            # 本文档
└── tools/
    ├── __init__.py      # 工具模块导出
    ├── format_checker.py # 格式校验（来自 baibai）
    ├── shuang_analyzer.py # 爽点分析（新增）
    ├── classifier.py     # 内容分类（来自 baibai）
    ├── platform_checker.py # 平台合规检查（新增）
    └── outline_generator.py # 集纲生成（新增）
```

## 🔗 相关资源

- [awesome-ai-short-drama](https://github.com/Zeon7744/awesome-ai-short-drama) - 短剧创作全栈方案
- [baibai](https://github.com/Zeon7744/baibai) - 通用 Vibe Coding 工具库
- [MCP 规范](https://modelcontextprotocol.io) - Model Context Protocol

## 📄 License

MIT License
