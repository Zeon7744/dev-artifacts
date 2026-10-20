# baibai：一个轻量级 MCP 工具库，让 AI 编程助手更懂金融与内容

> 开源地址：[Zeon7744/baibai](https://github.com/Zeon7744/baibai)
> 三平台同步：GitHub / Gitee / GitCode

---

## 写在前面

最近我在研究如何让 AI 编程助手（Claude Code、Cursor、Codex）更好地处理金融数据和内容创作任务。MCP（Model Context Protocol）协议的出现给了我很好的思路——**把工具标准化，让 AI 能像操作本地命令一样调用复杂服务**。

今天分享我写的开源项目 **baibai**，一个轻量级 MCP 工具库，内置 12 个标准工具，覆盖代码检查、数据分析、报告生成、TTS 语音合成等场景。

---

## 为什么做 baibai？

### 痛点

在使用 Claude Code 做金融分析或短剧内容创作时，我遇到了几个反复出现的问题：

1. **格式校验繁琐** — 每次写完 Markdown 报告都要手动检查格式是否正确
2. **数据分析重复** — 同样的统计逻辑在多个项目中重复编写
3. **README 千篇一律** — 每个项目都要手写 README，浪费大量时间
4. **多平台同步麻烦** — GitHub 更新后需要同步到 Gitee 和 GitCode

### 解决方案

用 MCP 把这些高频操作封装成标准化工具，AI 助手可以按需调用，无需每次重新写脚本。

---

## 架构设计

```
┌─────────────────────────────────────────────┐
│           AI 编程助手 (Claude/Cursor/Codex) │
│              通过 MCP 协议连接               │
└────────────────────┬────────────────────────┘
                     │ JSON-RPC 2.0
                     ▼
┌─────────────────────────────────────────────┐
│            baibai MCP Server                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 工具层   │ │ 服务层   │ │ 通信层   │   │
│  │ 12 tools │ │ baibai   │ │  HTTP    │   │
│  │          │ │ core     │ │ MCP      │   │
│  └────┬─────┘ └──────────┘ └──────────┘   │
└───────┼─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│           外部服务                           │
│  TTS 语音合成  ·  数据分析  ·  报告生成      │
└─────────────────────────────────────────────┘
```

**核心原则：零依赖（核心）、多平台、可扩展。**

---

## 12 个标准工具一览

| 工具 | 功能 | 典型场景 |
|------|------|---------|
| `check_format` | 代码/文档格式校验 | Markdown、JSON、YAML 一致性检查 |
| `analyze` | 数据统计分析 | CSV/JSON 数据快速统计 |
| `gen_readme` | README 自动生成 | 新项目快速生成项目说明 |
| `md2html` | Markdown 转 HTML | 生成可预览的技术文档 |
| `classify` | 内容自动分类 | 短剧剧本类型识别 |
| `get_time` | 获取当前时间 | 日志记录、时间戳生成 |
| `read_file` | 读取文件内容 | 快速查看文件内容 |
| `write_file` | 写入文件内容 | 生成报告、保存结果 |
| `search` | 全局搜索 | 在项目中查找关键代码 |
| `tts` | 文字转语音 | 生成音频播报 |
| `speech` | 语音转文字 | 会议纪要转文字稿 |
| `http_get` | HTTP 请求 | 调用外部 API 获取数据 |

### 工具设计原则

每个工具都遵循以下规范：

- **单一职责** — 一个工具只做一件事
- **输入可验证** — 参数校验 + 错误信息提示
- **输出结构化** — 统一 JSON 格式返回
- **轻量无依赖** — 核心功能不引入第三方包

---

## 快速开始

### 安装

```bash
# 方式一：从 GitHub Releases 安装（预编译 wheel）
pip install https://github.com/Zeon7744/baibai/releases/download/v1.2.0/baibai-1.2.0-py3-none-any.whl

# 方式二：源码安装
git clone https://github.com/Zeon7744/baibai.git
cd baibai
pip install -e .
```

### MCP 集成配置

在 Claude Code 或 Cursor 中配置：

```json
{
  "mcpServers": {
    "baibai": {
      "command": "python",
      "args": ["-m", "tools.cli", "mcp", "serve"]
    }
  }
}
```

### 使用示例

```python
# 在 AI 对话中直接使用
"请帮我检查当前目录的 README 格式是否正确，用 check_format 工具"
"分析 data/report.json 的数据统计，用 analyze 工具生成摘要"
"把 docs/analysis.md 转换成 HTML，用 md2html 工具"
```

---

## 三平台同步方案

为了让国内开发者更方便地访问，我配置了 GitHub Actions 自动同步到 Gitee 和 GitCode。

### GitHub Actions 配置

```yaml
name: sync-gitee-gitcode
on:
  push:
    branches: [main]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Sync to Gitee
        uses: wearerequired/git-mirror-action@master
        env:
          SSH_PRIVATE_KEY: ${{ secrets.GITEE_SSH_KEY }}
        with:
          source-repo: git@github.com:Zeon7744/baibai.git
          destination-repo: git@gitee.com:Zeon7744/baibai.git
      - name: Sync to GitCode
        uses: wearerequired/git-mirror-action@master
        env:
          SSH_PRIVATE_KEY: ${{ secrets.GITCODE_SSH_KEY }}
        with:
          source-repo: git@github.com:Zeon7744/baibai.git
          destination-repo: git@gitcode.com:Zeon7744/baibai.git
```

### 效果

每次推送到 GitHub，自动同步到：
- [Gitee](https://gitee.com/Zeon7744/baibai) — 国内访问更快
- [GitCode](https://gitcode.com/Zeon7744/baibai) — 华为云托管

---

## 项目现状

| 指标 | 数值 |
|------|------|
| GitHub Stars | 1 |
| 最新版本 | v1.2.0 |
| Python 支持 | 3.9+ |
| 工具数量 | 12 |
| 许可证 | MIT |
| 依赖数 | 核心零依赖 |

---

## 后续规划

- [ ] 增加金融数据分析专用工具（行情获取、指标计算）
- [ ] 集成更多 TTS 引擎（Azure、讯飞）
- [ ] 支持 Docker 一键部署
- [ ] 添加更多短剧创作工具（剧本格式校验、情节分析）

---

## 结语

baibai 的目标是让 AI 编程助手在处理日常开发任务时更高效——**少写脚本，多解决问题**。

如果你有使用需求或者改进建议，欢迎 Star、Fork 或者提 Issue。也欢迎加入我们的开发讨论群。

**项目地址：** [github.com/Zeon7744/baibai](https://github.com/Zeon7744/baibai)

---

*作者：Zeon7744 · 发布于 2026-09*
