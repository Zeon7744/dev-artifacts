"""
定时调度API - 工作流定时任务管理与调度历史

路由使用完整路径（/api/scheduler/...），main.py 中直接 include_router(router) 即可，
无需额外 prefix。
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.triggers.cron import CronTrigger

from ..core.auth import get_current_user
from ..core.database import get_session
from ..models.database import User, Workflow, WorkflowExecution
from ..scheduler.scheduler_service import scheduler_service

router = APIRouter()


class ScheduleRequest(BaseModel):
    """设置定时调度的请求体"""
    cron: str


@router.get("/api/scheduler/jobs")
async def list_scheduler_jobs(
    user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """列出当前所有调度任务"""
    return scheduler_service.list_jobs()


@router.post("/api/scheduler/workflows/{workflow_id}/schedule")
async def schedule_workflow(
    workflow_id: int,
    req: ScheduleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """为工作流设置 cron 定时调度"""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow or workflow.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # 校验 cron 表达式合法性
    try:
        CronTrigger.from_crontab(req.cron)
    except Exception:
        raise HTTPException(status_code=400, detail=f"非法的 cron 表达式: {req.cron}")

    workflow.schedule_cron = req.cron
    workflow.is_scheduled = True
    await db.commit()

    # 注册到调度器
    scheduler_service.add_workflow_job(workflow_id, req.cron)

    return {
        "workflow_id": workflow_id,
        "cron": req.cron,
        "is_scheduled": True,
        "status": "scheduled",
    }


@router.delete("/api/scheduler/workflows/{workflow_id}/schedule")
async def unschedule_workflow(
    workflow_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """取消工作流的定时调度"""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow or workflow.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.is_scheduled = False
    await db.commit()

    scheduler_service.remove_workflow_job(workflow_id)

    return {"workflow_id": workflow_id, "is_scheduled": False, "status": "unscheduled"}


@router.get("/api/scheduler/history")
async def list_schedule_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> List[Dict[str, Any]]:
    """查询最近 20 条定时触发的工作流执行记录（仅当前用户的工作流）"""
    result = await db.execute(
        select(WorkflowExecution)
        .join(Workflow, WorkflowExecution.workflow_id == Workflow.id)
        .where(
            WorkflowExecution.trigger_type == "schedule",
            Workflow.user_id == user.id,
        )
        .order_by(WorkflowExecution.created_at.desc())
        .limit(20)
    )
    executions = result.scalars().all()
    return [
        {
            "id": e.id,
            "workflow_id": e.workflow_id,
            "status": e.status.value,
            "trigger_type": e.trigger_type,
            "error_message": e.error_message,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in executions
    ]
