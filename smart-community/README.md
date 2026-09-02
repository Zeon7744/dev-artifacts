# AI Smart Community - 智能社区平台

> 全智能化社区网站，融合AI驱动的自动化工作流引擎、Agent市场和智能运维系统。

## 核心能力

| 模块 | 功能 | 技术亮点 |
|------|------|----------|
| **工作流引擎** | 可视化DAG编排，6种节点类型 | 拓扑排序执行、条件分支、模板变量解析 |
| **Agent市场** | 创建/发布/对话AI Agent | 多LLM Provider、熔断器降级、Ollama本地优先 |
| **社区中心** | 帖子/评论/分享 | 实时统计、标签系统 |
| **智能运维** | 系统监控、告警、自动化修复 | 指标采集、LLM健康检查 |
| **用户系统** | JWT认证、角色权限 | bcrypt加密、API Key管理 |

## 技术架构

```
smart-community/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── api/               # REST API 路由
│   │   │   ├── auth.py        # 注册/登录/JWT
│   │   │   ├── users.py       # 用户管理
│   │   │   ├── workflows.py   # 工作流CRUD+执行
│   │   │   ├── agents.py      # Agent市场+对话
│   │   │   ├── community.py   # 社区帖子
│   │   │   └── system.py      # 运维监控
│   │   ├── core/
│   │   │   ├── config.py      # 配置中心
│   │   │   ├── auth.py        # JWT+权限
│   │   │   └── database.py    # 异步DB会话
│   │   ├── models/
│   │   │   └── database.py    # SQLAlchemy ORM模型
│   │   ├── services/
│   │   │   └── llm_service.py # 统一LLM调用(Ollama/OpenAI)
│   │   ├── workflows/
│   │   │   └── engine.py      # DAG工作流引擎
│   │   └── main.py            # FastAPI入口
│   └── pyproject.toml
├── frontend/                   # React + Tailwind 前端
│   ├── src/
│   │   ├── components/        # Layout + 通用组件
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx  # 登录/注册
│   │   │   ├── DashboardPage.jsx    # 控制台
│   │   │   ├── WorkflowsPage.jsx    # 工作流列表
│   │   │   ├── WorkflowBuilderPage.jsx  # 可视化编辑器
│   │   │   ├── AgentsPage.jsx       # Agent市场
│   │   │   ├── CommunityPage.jsx    # 社区
│   │   │   └── SystemPage.jsx       # 智能运维
│   │   ├── hooks/useAuth.js   # Zustand状态管理
│   │   └── styles/            # Tailwind CSS
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 工作流引擎

支持6种节点类型，通过DAG拓扑排序自动执行：

| 节点类型 | 功能 | 示例 |
|----------|------|------|
| ⚡ 触发器 | 手动/定时/Webhook触发 | 每日9点执行 |
| ⚙️ 动作 | HTTP请求/数据库/文件操作 | 调用API获取数据 |
| 🔀 条件 | 表达式判断分支 | if sentiment > 0.7 |
| 🤖 AI处理 | LLM调用（Ollama/OpenAI） | 分析新闻情感 |
| 🔄 数据转换 | 映射/过滤/聚合 | 提取关键字段 |
| 🔔 通知 | 日志/邮件/消息推送 | 发送告警 |

**模板变量系统**：`{{node_id.field}}` 引用上游输出，`{{var.name}}` 引用全局变量

## 快速开始

### 后端
```bash
cd smart-community/backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### 前端
```bash
cd smart-community/frontend
npm install
npm run dev
```

访问 http://localhost:3000

## AI集成

- **Ollama本地模型**：优先使用，零成本、隐私安全
- **OpenAI API**：备用，自动降级
- **熔断器机制**：Provider故障自动切换，3次失败后降级

## 开发状态

- [x] 后端架构 + 数据库模型
- [x] 工作流引擎（DAG执行器）
- [x] JWT认证系统
- [x] LLM多Provider服务
- [x] 前端React SPA
- [x] 可视化工作流编辑器（ReactFlow）
- [ ] WebSocket实时通信
- [ ] 定时调度器（APScheduler）
- [ ] RAG知识库集成
- [ ] 插件系统

## License

MIT

---

<div align="center">

**由 [Zeon7744](https://github.com/Zeon7744) 开发维护**

*AI驱动 · 自动化 · 智能运维*

</div>
