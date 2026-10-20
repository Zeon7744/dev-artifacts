"""系统API - 监控/运维/统计"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.database import get_session
from ..core.auth import get_current_user, require_role
from ..models.database import User, Workflow, Agent, Post, SystemMetric, Alert, UserRole
from ..services.llm_service import LLMService

router = APIRouter()

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_session)):
    users = (await db.execute(select(func.count(User.id)))).scalar()
    workflows = (await db.execute(select(func.count(Workflow.id)))).scalar()
    agents = (await db.execute(select(func.count(Agent.id)))).scalar()
    posts = (await db.execute(select(func.count(Post.id)))).scalar()
    return {"users": users, "workflows": workflows, "agents": agents, "posts": posts}

@router.get("/health")
async def system_health():
    llm = LLMService()
    llm_status = await llm.health_check()
    return {"status": "healthy", "llm_providers": llm_status}

@router.get("/metrics")
async def get_metrics(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(SystemMetric).order_by(SystemMetric.recorded_at.desc()).offset(skip).limit(limit))
    metrics = result.scalars().all()
    return [{"name": m.metric_name, "value": m.metric_value, "labels": m.labels,
             "recorded_at": m.recorded_at.isoformat() if m.recorded_at else None} for m in metrics]

@router.get("/alerts")
async def get_alerts(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Alert).where(Alert.is_resolved == False).order_by(Alert.created_at.desc()).limit(limit))
    alerts = result.scalars().all()
    return [{"id": a.id, "type": a.alert_type, "severity": a.severity, "title": a.title,
             "message": a.message, "created_at": a.created_at.isoformat() if a.created_at else None} for a in alerts]
