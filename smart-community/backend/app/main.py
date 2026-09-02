"""
AI Smart Community - FastAPI 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .core.config import settings
from .core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


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

# 注册路由
from .api import auth, users, workflows, agents, community, system

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["工作流"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agent"])
app.include_router(community.router, prefix="/api/community", tags=["社区"])
app.include_router(system.router, prefix="/api/system", tags=["系统"])


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
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
