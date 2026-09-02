# AI Smart Community - 智能社区平台

> 全智能化社区网站，融合AI驱动的自动化工作流引擎、Agent市场和智能运维系统。

## 核心能力

| 模块 | 功能 | 技术亮点 |
|------|------|----------|
| **工作流引擎** | 可视化DAG编排，6种节点类型 | 拓扑排序执行、条件分支、模板变量解析 |
| **Agent市场** | 创建/发布/对话AI Agent | 多LLM Provider、熔断器降级、Ollama本地优先 |
| **社区中心** | 帖子/评论/分享 | 实时统计、标签系统 |
| **智能运维** | 系统监控、告警、自动化修复 | 指标采集、LLM健康检查 |
| **用户系统** | JWT认证、角色权限 | pbkdf2_sha256加密、API Key管理 |
| **实时通信** | WebSocket消息推送、房间订阅 | 分组广播、JWT鉴权、指数退避重连 |
| **定时调度** | Cron定时执行工作流 | APScheduler AsyncIO、任务历史 |
| **RAG知识库** | 文档上传、向量检索、AI问答 | 分块向量化、Ollama嵌入+哈希降级 |
| **插件系统** | 自定义工作流节点、插件市场 | 插件注册表、内置文本/JSON/数学节点 |

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
- [x] WebSocket实时通信（房间广播 + 事件主动推送）
- [x] 定时调度器（APScheduler，重启自动恢复）
- [x] RAG知识库集成（向量检索 + PDF/Word/Markdown文件上传）
- [x] 插件系统（内置插件 + 自定义插件安全沙箱执行）
- [x] 通知中心（WS实时推送 + 持久化未读）
- [x] 容器化部署（Dockerfile + docker-compose）
- [x] pytest 自动化测试
- [x] 社区互动通知（评论/点赞实时通知作者）
- [x] Agent SSE 流式对话（打字机效果）
- [x] 插件管理员审核流（提交→审核→上架/驳回）
- [x] 系统健康监控（LLM 状态变化告警广播）


## 第四轮功能增强（2026-09-03）

### 社区互动通知
- 评论、回复、点赞事件实时通知帖子作者（落库 + WS 推送），自己互动自己不通知
- 社区页新增帖子详情弹窗：浏览全文、点赞、评论一条龙

### Agent SSE 流式对话
- `POST /api/agents/chat/stream`：text/event-stream，事件协议 `meta` → 多个 `token` → `done`
- LLMService 新增 `generate_stream`：Ollama `/api/chat` stream 与 OpenAI SSE 双通道解析；LLM 不可用时降级文本同样按 token 小块吐出，前端打字机体验一致
- 前端对话面板升级为多轮气泡 + 逐字增量渲染 + 流式光标动画（fetch + ReadableStream 解析 SSE）

### 插件管理员审核流
- 插件模型新增 review_status（pending_review/approved/rejected）、审核人/时间/意见字段，启动时自动轻量迁移（SQLite ADD COLUMN + 历史已发布插件回填 approved）
- 普通作者：提交（自动 AST 安全校验）→ 沙箱试跑 → 提交审核（通知管理员）；管理员：待审列表 → 通过（自动上架+注册引擎+通知作者）/ 驳回（附原因+通知作者）
- 管理员本人发布直接上架；`username=admin` 账号启动自动提权 ADMIN
- API：`GET /api/plugins/custom/mine`、`GET /api/plugins/admin/pending`、`POST /api/plugins/admin/{id}/approve|reject`
- 前端插件页新增「开发者中心」（提交/试跑/我的插件状态）与管理员待审面板（通过/驳回）

### 系统健康监控
- `app/system_health.py`：每 5 分钟检查 LLM provider 可用性，状态翻转（故障/恢复）时通知全体管理员 + global 房间实时广播，内存基线去重避免刷屏

### 验证结果
- **固化 E2E 冒烟 24/24 通过**（`scripts/e2e_smoke.py`，随机用户可重复执行）：覆盖认证、工作流 DAG、插件提交/恶意拒绝/试跑/审核流全链、审核通知、社区评论点赞通知、SSE 事件序列、RAG、cron 调度、WebSocket
- **pytest 31/31 通过**（新增 test_round4.py 7 项：互动通知/审核通过流/驳回流/管理员直发/SSE）
- 健康检查任务手动验证：基线不告警、状态不变不重复通知、周期任务注册成功



## 第三轮功能增强（2026-09-03）

### 通知中心（双通道）
- **实时通道**：WebSocket 连接后自动加入 `user/{id}` 专属房间；工作流执行完成、定时任务触发等事件主动推送
- **持久通道**：通知落库（notifications 表），离线/断线重连后拉取未读历史
- API：`GET /api/notifications`、`/unread-count`、`POST /read-all`、`/{id}/read`
- 前端：顶栏铃铛实时角标、类别/级别标识、一键全部已读

### 自定义插件安全沙箱
自定义插件以源码提交，经过四重安全限制后可直接在工作流引擎中执行：
1. **AST 静态校验**：禁止 import/global/nonlocal/with，禁止下划线属性与名称，禁止 eval/exec/open/getattr 等危险内建
2. **受限内建环境**：仅暴露安全内建 + json/math/re/datetime 白名单模块，无文件系统/网络入口
3. **循环步数插桩**：while/for 注入步数守卫，死循环 ~10 万次迭代内被 RuntimeError 终止
4. **线程级超时**：独立线程执行 + 5 秒墙钟超时，daemon 线程不阻塞服务

API：`POST /api/plugins/custom`（提交即校验，恶意代码 400 拒绝）、`/custom/{id}/test`（沙箱试跑）、`/custom/{id}/publish`（发布即注册，无需重启）；服务启动时自动加载已发布插件。

### RAG 文件上传
- `POST /api/rag/kb/{id}/upload`：multipart 上传 .txt/.md/.pdf/.docx（10MB 上限）
- 解析库（pypdf/python-docx）延迟导入，缺失时返回 501 与安装提示，不影响其他格式
- 前端知识库页内置文件上传入口，上传后自动刷新文档列表

### 前端工作流构建器增强
- 节点面板新增「插件节点」分组（emerald 色系），从 `/api/plugins` 实时拉取
- 插件节点选中后按 config_schema 动态渲染配置表单（text/textarea/number/select/checkbox）
- 保存工作流时插件节点类型（plugin.*）与完整配置一并写入 DAG 定义

### 验证结果
- **通知 + 沙箱 E2E 23/23 通过**：通知列表/未读/已读/401、合规插件提交、恶意代码拒绝、沙箱试跑、死循环终止、发布上架、插件节点全链工作流执行（total=60）、WS 实时通知帧、通知持久化
- **回归**：基础 14 项、四大模块 15 项全部保持通过
- **文件上传**：txt/docx/pdf 上传切分入库成功，空白页 PDF 与不支持格式正确报错，缺依赖返回 501


## License

MIT

---

<div align="center">

**由 [Zeon7744](https://github.com/Zeon7744) 开发维护**

*AI驱动 · 自动化 · 智能运维*

</div>


## 端到端验证结果（2026-09-03）

**基础功能 14/14 通过**：健康检查、注册/登录、JWT鉴权、工作流创建与DAG执行、Agent创建与对话降级、社区发帖/评论/浏览计数、系统统计。

**新功能 15/15 通过 + WebSocket 4/4 + 插件节点工作流**：
- 插件：列表/类型/schema/安装，3个内置节点
- RAG：知识库创建、文档分块向量化、向量检索、LLM降级问答（检索结果正常返回）
- 调度：cron创建/非法cron拒绝(400)/任务列表/历史/取消
- WebSocket：合法连接欢迎消息、ping/pong、房间订阅、非法token拒绝(4001)
- 插件节点接入工作流引擎：text_format 大写转换、math_calc 计算 `3*(4+5)=27` 全链成功

### 启动方式

```bash
# 后端
cd backend && pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && npm install --registry=https://registry.npmmirror.com
npm run dev   # http://localhost:3000 （/api 已代理到 8000）
```

### 降级设计
- **LLM**：优先本地 Ollama，未启动时 OpenAI 兜底，均不可用时 Agent/RAG 优雅返回提示
- **RAG 嵌入**：优先 Ollama nomic-embed-text，失败降级为确定性哈希向量（零外部依赖可运行）
- **数据库**：默认 SQLite（/tmp 可覆盖 DATABASE_URL），零配置启动
