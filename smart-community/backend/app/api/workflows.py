"""
工作流API - CRUD + 执行
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_session
from ..core.auth import get_current_user
from ..models.database import User, Workflow, WorkflowExecution, WorkflowStatus, TaskStatus
from ..workflows.engine import WorkflowEngine

router = APIRouter()


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    definition: Dict[str, Any]
    schedule_cron: Optional[str] = None
    is_public: bool = False
    tags: List[str] = []


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    schedule_cron: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class WorkflowRun(BaseModel):
    input_data: Dict[str, Any] = {}


@router.get("/")
async def list_workflows(
    skip: int = 0, limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(Workflow).where(Workflow.user_id == user.id).offset(skip).limit(limit)
    )
    workflows = result.scalars().all()
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "status": w.status.value,
            "is_scheduled": w.is_scheduled,
            "run_count": w.run_count,
            "tags": w.tags,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in workflows
    ]


@router.post("/")
async def create_workflow(
    req: WorkflowCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    workflow = Workflow(
        user_id=user.id,
        name=req.name,
        description=req.description,
        definition=req.definition,
        schedule_cron=req.schedule_cron,
        is_scheduled=bool(req.schedule_cron),
        is_public=req.is_public,
        tags=req.tags,
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return {"id": workflow.id, "name": workflow.name, "status": "created"}


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status.value,
        "definition": workflow.definition,
        "schedule_cron": workflow.schedule_cron,
        "is_public": workflow.is_public,
        "tags": workflow.tags,
        "run_count": workflow.run_count,
        "last_run_at": workflow.last_run_at.isoformat() if workflow.last_run_at else None,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
    }


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: int,
    req: WorkflowUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow or workflow.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(workflow, field, value)
    await db.commit()
    return {"id": workflow.id, "status": "updated"}


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow or workflow.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(workflow)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: int,
    req: WorkflowRun,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow or workflow.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # 创建执行记录
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        status=TaskStatus.RUNNING,
        trigger_type="manual",
        input_data=req.input_data,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # 执行工作流
    engine = WorkflowEngine()
    try:
        result = await engine.run(
            workflow_id=workflow.id,
            execution_id=execution.id,
            definition=workflow.definition,
            input_data=req.input_data,
        )

        execution.status = TaskStatus.SUCCESS if result["status"] == "success" else TaskStatus.FAILED
        execution.output_data = result.get("final_output", {})
        execution.node_results = result.get("node_results", [])
        execution.error_message = "\n".join(result.get("errors", []))
    except Exception as e:
        execution.status = TaskStatus.FAILED
        execution.error_message = str(e)

    from datetime import datetime
    execution.completed_at = datetime.utcnow()

    # 更新工作流统计
    workflow.run_count += 1
    workflow.last_run_at = execution.completed_at
    workflow.last_run_status = execution.status.value

    await db.commit()

    # 实时通知：工作流执行结果推送到用户铃铛（旁路，失败不影响响应）
    try:
        from ..notifications import notify_user

        ok = execution.status == TaskStatus.SUCCESS
        await notify_user(
            user_id=user.id,
            category="workflow",
            level="success" if ok else "error",
            title=f"工作流「{workflow.name}」执行{'成功' if ok else '失败'}",
            content=(
                f"手动触发的工作流已执行完成，状态：{execution.status.value}。"
                if ok else f"工作流执行失败：{execution.error_message or '未知错误'}"
            ),
            data={
                "workflow_id": workflow.id,
                "execution_id": execution.id,
                "status": execution.status.value,
            },
        )
    except Exception:
        pass

    return {
        "execution_id": execution.id,
        "status": execution.status.value,
        "node_results": execution.node_results,
        "errors": execution.error_message,
    }


@router.get("/{workflow_id}/executions")
async def list_executions(
    workflow_id: int,
    skip: int = 0, limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == workflow_id)
        .order_by(WorkflowExecution.created_at.desc())
        .offset(skip).limit(limit)
    )
    executions = result.scalars().all()
    return [
        {
            "id": e.id,
            "status": e.status.value,
            "trigger_type": e.trigger_type,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        }
        for e in executions
    ]
