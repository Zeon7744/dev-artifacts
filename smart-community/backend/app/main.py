"""
AI Smart Community - FastAPI 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup：初始化数据库 + 启动定时调度器 + 加载已发布自定义插件
    await init_db()
    scheduler = None
    try:
        from .scheduler.scheduler_service import scheduler_service
        scheduler_service.start()
        await scheduler_service.sync_schedules()
        scheduler = scheduler_service
    except Exception as e:
        print(f"[lifespan] 调度器启动失败（不影响主服务）: {e}")
    try:
        from .plugins.loader import load_published_plugins
        count = await load_published_plugins()
        print(f"[lifespan] 已加载 {count} 个已发布自定义插件")
    except Exception as e:
        print(f"[lifespan] 自定义插件加载失败（不影响主服务）: {e}")
    yield
    # Shutdown
    if scheduler is not None:
        try:
            scheduler.shutdown()
        except Exception:
            pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（注意：realtime/scheduler/rag/plugins 的路由路径自带 /api 前缀，不加 prefix）
from .api import auth, users, workflows, agents, community, system
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["工作流"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agent"])
app.include_router(community.router, prefix="/api/community", tags=["社区"])
app.include_router(system.router, prefix="/api/system", tags=["系统"])

# 新功能模块（realtime/scheduler/notifications 路由内部已含 /api 前缀；rag/plugins 用 prefix 挂载）
from .api import realtime as realtime_api
from .api import scheduler as scheduler_api
from .api import notifications as notifications_api
from .api import rag as rag_api
from .api import plugins as plugins_api
app.include_router(realtime_api.router, tags=["实时通信"])
app.include_router(scheduler_api.router, tags=["定时调度"])
app.include_router(notifications_api.router, tags=["通知中心"])
app.include_router(rag_api.router, prefix="/api/rag", tags=["知识库RAG"])
app.include_router(plugins_api.router, prefix="/api/plugins", tags=["插件系统"])

# 导入 RAG / 插件 / 通知 ORM 模型以触发表注册（init_db 建表时使用）
try:
    from .rag import models as _rag_models  # noqa: F401
    from .plugins import models as _plugin_models  # noqa: F401
    from .notifications import models as _notif_models  # noqa: F401
except Exception:
    pass


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "modules": ["workflows", "agents", "community", "realtime(ws)", "scheduler", "rag", "plugins"],
    }


@app.get("/api/health")
async def health():
    from .services.llm_service import LLMService
    llm = LLMService()
    llm_health = await llm.health_check()
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "llm_providers": llm_health,
    }
