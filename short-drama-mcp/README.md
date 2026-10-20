# 🎬 短剧创作 MCP 服务器 v2.0

> 从小说到剧本的一站式 AI 短剧创作系统

## ✨ 功能概览

### 基础工具（规则层）
| 工具 | 功能 |
|------|------|
| `check_script_format` | 剧本格式校验（禁止字符、括号、标题、对话长度） |
| `count_shuang_points` | 爽点/甜点密度统计 |
| `generate_episode_outline` | 小说→集纲大纲 |
| `check_platform_compliance` | 红果平台投稿规范检查 |
| `classify_content` | 内容自动分类 |
| `create_character_profile` | 角色设定卡片生成 |
| `optimize_dialogue` | 对话质量优化 |

### 🤖 AI Agent 系统（LLM 层）
| Agent | 功能 | 接口 |
|-------|------|------|
| **PlotAgent** | 剧情生成 | `generate_plot(novel_input, genre, episode_count)` |
| **CharacterAgent** | 角色设计 | `create_characters(story_summary, genre, character_count)` |
| **DialogueAgent** | 对话生成 | `generate_dialogue(scene, characters, mood)` |
| **ScriptAgent** | 剧本格式化 | `format_script(content, format_type, episode_count)` |
| **QualityAgent** | 质量审查 | `check_quality(script_content)` |
| **TrendAgent** | 趋势分析 | `analyze_trends(platform, genre)` |
| **SeoAgent** | SEO 优化 | `optimize_seo(title, description, tags, genre)` |

### 🔄 工作流编排
一键串联所有 Agent，完成 **趋势分析 → 剧情生成 → 角色设计 → 对话生成 → 剧本格式化 → 质量审查 → SEO 优化** 全流程。

```python
from workflows.orchestrator import WorkflowOrchestrator
from agents.base import AgentConfig

config = AgentConfig(api_key="sk-...")
orch = WorkflowOrchestrator(config)
result = orch.run_full_workflow(
    novel_input="你的小说/大纲...",
    genre="都市逆袭",
    episode_count=8,
)
```

## 🚀 快速开始

### 安装

```bash
cd /Coze/Drive/红剑/dev-artifacts/short-drama-mcp
pip install -e ".[dev]"
pip install openai  # Agent 系统依赖
```

### 配置 API Key

```bash
export OPENAI_API_KEY="sk-..."
```

### 运行 MCP 服务器

```bash
python main.py
```

### 运行演示

```bash
# 完整工作流演示
python examples/demo_workflow.py --step full

# 单 Agent 演示
python examples/demo_workflow.py --step single

# 质量检查演示
python examples/demo_workflow.py --step quality

# SEO 优化演示
python examples/demo_workflow.py --step seo
```

### 运行测试

```bash
pytest tests/test_agents.py -v
```

## 📁 项目结构

```
short-drama-mcp/
├── main.py                          # MCP 服务器入口（v2.0）
├── pyproject.toml                   # 项目配置
├── README.md                        # 本文档
│
├── agents/                          # 🤖 AI Agent 系统
│   ├── __init__.py
│   ├── base.py                      # 基类（LLM 调用、重试、JSON 解析）
│   ├── plot_agent.py                # 剧情生成 Agent
│   ├── character_agent.py           # 角色设计 Agent
│   ├── dialogue_agent.py            # 对话生成 Agent
│   ├── script_agent.py              # 剧本格式化 Agent
│   ├── quality_agent.py             # 质量检查 Agent
│   ├── trend_agent.py               # 趋势分析 Agent
│   └── seo_agent.py                 # SEO 优化 Agent
│
├── tools/                           # 🔧 基础工具（规则层）
│   ├── __init__.py
│   ├── format_checker.py            # 格式校验
│   ├── shuang_analyzer.py           # 爽点统计
│   ├── character_creator.py         # 角色设定
│   ├── dialogue_optimizer.py        # 对话优化
│   ├── outline_generator.py         # 集纲生成
│   ├── platform_checker.py          # 平台合规
│   ├── classifier.py                # 内容分类
│   ├── stats_analyzer.py            # 统计分析
│   └── storyboard_generator.py      # 分镜生成
│
├── workflows/                       # 🔄 工作流编排
│   ├── __init__.py
│   └── orchestrator.py              # 编排器（串联所有 Agent）
│
├── examples/                        # 📖 使用示例
│   └── demo_workflow.py             # 完整工作流演示
│
└── tests/                           # 🧪 测试
    └── test_agents.py               # Agent 系统测试（32 用例）
```

## 🎯 Agent 使用示例

### 剧情生成

```python
from agents.plot_agent import PlotAgent
from agents.base import AgentConfig

agent = PlotAgent(AgentConfig(api_key="sk-..."))
plot = agent.generate_plot(
    novel_input="他曾是商界传奇，失去一切后以助理身份归来...",
    genre="都市逆袭",
    episode_count=8,
)
print(plot["title"])        # 剧名
print(plot["episodes"])     # 分集剧情
```

### 角色设计

```python
from agents.character_agent import CharacterAgent

agent = CharacterAgent(AgentConfig(api_key="sk-..."))
characters = agent.create_characters(
    story_summary="商界传奇复仇归来，与前妻重逢",
    genre="都市逆袭",
    character_count=5,
)
for c in characters["characters"]:
    print(f"{c['name']}: {c['identity']}")
```

### 对话生成

```python
from agents.dialogue_agent import DialogueAgent

agent = DialogueAgent(AgentConfig(api_key="sk-..."))
dialogue = agent.generate_dialogue(
    scene={"location": "公司大堂", "description": "主角第一天上班"},
    characters=[
        {"name": "顾寒声", "personality": "冷静", "speech_style": "冷淡简洁"},
        {"name": "前台", "personality": "势利", "speech_style": "阴阳怪气"},
    ],
    mood="紧张",
)
for line in dialogue["dialogue_lines"]:
    print(f'{line["character"]}："{line["dialogue"]}"')
```

### 质量检查

```python
from agents.quality_agent import QualityAgent

agent = QualityAgent(AgentConfig(api_key="sk-..."))

# 快速检查（仅规则，不调 LLM）
result = agent.quick_check(script_content)
print(f"分数: {result['score']}, 通过: {result['passed']}")

# 完整检查（规则 + LLM）
report = agent.check_quality(script_content)
print(f"等级: {report['grade']}")
```

### SEO 优化

```python
from agents.seo_agent import SeoAgent

agent = SeoAgent(AgentConfig(api_key="sk-..."))
titles = agent.generate_titles(
    story_summary="商界传奇复仇归来",
    genre="都市逆袭",
    core_conflict="身份暴露 vs 隐藏复仇",
)
print(f"推荐标题: {titles['best_pick']}")
```

## 📐 设计规范

### 短剧创作规范（内置）
- 每集 ≥3 爽点 + ≥1 甜点
- 对话每句 ≤15 字
- 禁止字符：耀、曜
- 每集 800-1200 字
- 标准格式：`## 第X集：集名` / `【场景标记】` / `第X集完`

### Agent 架构设计
- **BaseAgent** 基类统一 LLM 调用、重试、JSON 解析
- 每个 Agent 有独立 prompt 模板和输出格式
- Agent 间通过 `WorkflowOrchestrator` 传递上下文
- 工具层（tools/）+ Agent 层（agents/）双层架构

## 🔗 关联项目

- [awesome-ai-short-drama](https://github.com/Zeon7744/awesome-ai-short-drama) - AI 短剧全链路资源精选清单
- [dev-artifacts](https://github.com/Zeon7744/dev-artifacts) - 开发成品库

## 📝 License

MIT
