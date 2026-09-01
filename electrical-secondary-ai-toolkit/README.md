# 电气二次AI工具包 - 模型训练工作流

> 面向电气二次专业AI应用开发者的完整模型训练工作流与工具集

## 📋 项目概述

本项目基于广东电网有限责任公司《厂站二次设备及其二次回路工作安全技术措施单实施细则（2025版）》，提供一套完整的模型训练工作流，包括：

1. **二次作业知识抽取与结构化系统** - 从标准文档中提取知识，构建领域知识图谱
2. **二次措施单智能生成模型** - 基于输入参数自动生成符合标准的措施单

## 🏗️ 工作流架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    电气二次AI模型训练工作流                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  数据层       │ → │  处理层       │ → │  模型层       │      │
│  │  Data Layer  │    │  Process     │    │  Model       │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│       ↓                       ↓                       ↓         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    成果一：知识图谱系统                    │   │
│  │  • 标准文档解析器                                         │   │
│  │  • 术语与规则抽取器                                       │   │
│  │  • 知识图谱构建器                                         │   │
│  │  • 结构化知识库存储                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    成果二：智能生成模型                    │   │
│  │  • 输入参数建模器                                         │   │
│  │  • 模板匹配引擎                                           │   │
│  │  • 措施内容生成器                                         │   │
│  │  • 合规性校验器                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    输出层                                  │   │
│  │  • Word格式措施单生成                                      │   │
│  │  • JSON结构化数据导出                                     │   │
│  │  • API服务接口                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 项目结构

```
electrical-secondary-ai-toolkit/
├── data/                          # 数据目录
│   ├── parsed_*.json             # 解析结果
│   ├── knowledge_extracted.json  # 抽取知识
│   ├── knowledge_graph*.json     # 知识图谱
│   └── measures_*.json           # 生成结果
├── docs/                          # 输出文档
│   ├── *.docx                    # Word措施单
│   └── *.json                    # JSON数据
├── examples/                      # 示例目录
│   ├── example_220kV_transformer.json
│   └── example_220kV_line.json
├── scripts/                       # 脚本目录
│   ├── 01_data_parsing.py        # 文档解析脚本
│   ├── 02_knowledge_extraction.py # 知识抽取脚本
│   ├── 03_knowledge_graph.py     # 知识图谱构建脚本
│   ├── 03_knowledge_graph_enhanced.py # 增强版图谱构建器
│   ├── 05_measures_generation.py # 措施生成脚本
│   ├── 08_measures_docx_generator.py # Word导出脚本
│   └── run_workflow.py           # 完整工作流集成脚本
├── config/                        # 配置文件目录
│   └── paths.yaml                # 路径配置
├── api_server.py                  # FastAPI服务
├── requirements.txt               # 依赖列表
└── README.md                      # 项目文档
```

## 🎯 两个核心成果

### 成果一：二次作业知识图谱系统

**功能**：
- 自动解析二次作业标准文档（Word/PDF）
- 抽取术语、规则、流程等知识要素
- 构建领域知识图谱（NetworkX）
- 支持知识查询与推理

**技术栈**：
- Python 3.10+
- python-docx（文档解析）
- NetworkX（知识图谱）
- jieba（中文分词）

**已实现**：
- ✅ 文档解析器 - 解析197个章节，0表格
- ✅ 知识抽取器 - 抽取271条规则，1个流程
- ✅ 知识图谱构建器 - 构建227节点、450边的图谱
- ✅ 动作-设备关联映射

### 成果二：二次措施单智能生成模型

**功能**：
- 接收作业参数（变电站等级、设备类型、作业类型等）
- 智能匹配最佳模板
- 生成符合标准格式的措施单
- 自动校验合规性

**技术栈**：
- Python 3.10+
- FastAPI（API服务）
- python-docx（Word生成）
- Pydantic（数据验证）

**已实现**：
- ✅ 措施单生成器 - 基于模板匹配生成
- ✅ Word文档导出器 - 符合附录1格式
- ✅ FastAPI服务 - RESTful API接口
- ✅ 完整工作流集成脚本

## 🚀 快速开始

### 环境准备

```bash
# 进入项目目录
cd electrical-secondary-ai-toolkit

# 安装依赖
pip install -r requirements.txt
```

### 运行工作流

```bash
# 方式1：运行完整流水线
python scripts/run_workflow.py \
  --doc "path/to/实施细则.docx" \
  --output-prefix my_output

# 方式2：仅生成措施单
python scripts/run_workflow.py \
  --mode generate \
  --params examples/example_220kV_transformer.json \
  --output-prefix docs/主变保护定检

# 方式3：使用API服务
python api_server.py
# 访问 http://localhost:8000/docs
```

### API接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | API信息 |
| `/api/parse` | POST | 解析文档 |
| `/api/extract` | POST | 抽取知识 |
| `/api/graph` | POST | 构建图谱 |
| `/api/generate` | POST | 生成措施单 |
| `/api/download/{file}` | GET | 下载文件 |
| `/api/stats` | GET | 系统统计 |

## 📊 当前状态

### 已完成

- [x] 标准文档解析器（197章节解析）
- [x] 知识抽取器（271条规则抽取）
- [x] 知识图谱构建器（227节点，450边）
- [x] 措施单智能生成器
- [x] Word文档导出器（符合附录1格式）
- [x] FastAPI服务
- [x] 完整工作流集成脚本
- [x] 示例输入文件（主变保护、线路保护）

### 测试结果

```
✓ 文档解析：197章节，0表格
✓ 知识抽取：271条规则，1个流程
✓ 知识图谱：227节点，450边
✓ 措施单生成：成功生成220kV主变保护定检措施单
✓ Word导出：生成标准格式Word文档
```

## 📁 输出文件示例

```
docs/
├── 220kV主变保护定检措施单.docx   # Word格式措施单
├── 220kV主变保护定检措施单.json   # JSON数据
├── 220kV线路保护定检措施单.docx
└── 220kV线路保护定检措施单.json

data/
├── parsed_实施细则.json           # 解析结果
├── knowledge_extracted.json       # 抽取知识
├── knowledge_graph_enhanced.json  # 知识图谱
└── measures_generated.json        # 生成结果
```

## 🔧 模块说明

### 模块1：文档解析器 (`01_data_parsing.py`)

```python
from scripts.01_data_parsing import SecondaryDocParser

parser = SecondaryDocParser()
result = parser.parse_docx("path/to/doc.docx")
# 返回：sections（章节列表）、tables（表格列表）、knowledge_elements（知识元素）
```

### 模块2：知识抽取器 (`02_knowledge_extraction.py`)

```python
from scripts.02_knowledge_extraction import KnowledgeExtractor

extractor = KnowledgeExtractor()
extractor.extract_from_text(text, source_section="第二章")
# 返回：terms（术语）、rules（规则）、procedures（流程）
```

### 模块3：知识图谱构建器 (`03_knowledge_graph_enhanced.py`)

```python
from scripts.03_knowledge_graph_enhanced import EnhancedKnowledgeGraph

builder = EnhancedKnowledgeGraph()
builder.build_from_knowledge(knowledge_data)
builder.export_to_json("output.json")
# 输出：节点227个，边450条
```

### 模块4：措施单生成器 (`05_measures_generation.py`)

```python
from scripts.05_measures_generation import MeasuresGenerator

generator = MeasuresGenerator()
measures = generator.generate(params)
# params: 变电站名称、电压等级、设备类型、工作类型等
```

### 模块5：Word导出器 (`08_measures_docx_generator.py`)

```python
from scripts.08_measures_docx_generator import MeasuresDocGenerator

doc_gen = MeasuresDocGenerator()
doc_gen.generate(measures_data, "output.docx")
# 输出：符合附录1格式的9列表格Word文档
```

## 📖 标准文档来源

- **主文档**：广东电网有限责任公司厂站二次设备及其二次回路工作安全技术措施单实施细则（2025版）
- **附录1**：二次措施单格式（9列表格标准）
- **附录4-6**：220kV主变保护定检作业二次措施单参考文档
- **附录4-7**：220kV线路保护定检作业二次措施单参考文档

## 🛠️ 开发指南

### 添加新模板

1. 在 `examples/` 目录添加新的JSON参数文件
2. 在 `scripts/05_measures_generation.py` 的模板库中添加新模板
3. 测试生成结果

### 扩展知识图谱

1. 修改 `scripts/03_knowledge_graph_enhanced.py` 中的实体提取规则
2. 添加新的关系类型
3. 重新运行图谱构建

### 部署API服务

```bash
# 生产环境部署
pip install gunicorn
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📄 许可证

本项目基于广东电网有限责任公司二次作业标准文档开发，仅供学习和研究使用。

## 🔗 相关链接

- GitHub仓库: https://github.com/Zeon7744/dev-artifacts/tree/main/electrical-secondary-ai-toolkit
- 原始标准文档: `/Coze/Drive/红剑/converted_docs/`
