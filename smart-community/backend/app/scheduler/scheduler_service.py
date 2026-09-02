"""
定时调度服务 - 封装 APScheduler AsyncIOScheduler

- 单例 SchedulerService，管理工作流的 cron 定时任务
- 每个定时任务在独立的数据库会话中执行，避免跨 event loop 复用 session
- 任务执行过程全程 try/except，异常不向上抛出，防止调度循环中断
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from ..core.database import async_session
from ..models.database import (
    Workflow,
    WorkflowExecution,
    TaskStatus,
    SystemMetric,
)
from ..workflows.engine import WorkflowEngine

logger = logging.getLogger(__name__)


class SchedulerService:
    """工作流定时调度服务（单例使用）"""

    def __init__(self) -> None:
        # AsyncIOScheduler 会复用当前运行中的 event loop（FastAPI 启动时的 loop）
        self._scheduler: Optional[AsyncIOScheduler] = None

    # ============ 生命周期 ============

    def start(self) -> None:
        """启动调度器（幂等，重复调用安全）"""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("调度器已启动")

    def shutdown(self) -> None:
        """关闭调度器"""
        if self._scheduler is not None and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("调度器已关闭")

    def _ensure_running(self) -> AsyncIOScheduler:
        """获取调度器实例，若尚未启动则惰性启动（便于 lifespan 未集成时也能工作）"""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        if not self._scheduler.running:
            self._scheduler.start()
        return self._scheduler

    # ============ 任务管理 ============

    def add_workflow_job(self, workflow_id: int, cron_expr: str) -> None:
        """注册/更新工作流定时任务

        :param workflow_id: 工作流 ID
        :param cron_expr: 标准 5 段 cron 表达式（如 "0 9 * * *"）
        """
        scheduler = self._ensure_running()
        trigger = CronTrigger.from_crontab(cron_expr, timezone="Asia/Shanghai")
        scheduler.add_job(
            self._run_workflow_job,
            trigger=trigger,
            args=[workflow_id],
            id=f"workflow_{workflow_id}",
            replace_existing=True,
            coalesce=True,        # 错过多次执行时合并为一次
            max_instances=1,      # 同一任务不并发执行
            misfire_grace_time=60,
        )
        logger.info("已注册定时任务 workflow_%s，cron=%s", workflow_id, cron_expr)

    def remove_workflow_job(self, workflow_id: int) -> None:
        """移除工作流定时任务（任务不存在时忽略）"""
        scheduler = self._ensure_running()
        try:
            scheduler.remove_job(f"workflow_{workflow_id}")
            logger.info("已移除定时任务 workflow_%s", workflow_id)
        except Exception:
            # 任务未注册或调度器状态异常，无需处理
            pass

    def list_jobs(self) -> List[Dict[str, Any]]:
        """列出当前所有调度任务"""
        scheduler = self._ensure_running()
        jobs: List[Dict[str, Any]] = []
        for job in scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "next_run_time": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                    "trigger": str(job.trigger),
                }
            )
        return jobs

    # ============ 启动同步 ============

    async def sync_schedules(self) -> None:
        """从数据库加载所有启用定时调度的工作流并注册到调度器（启动时调用）"""
        self.start()
        async with async_session() as db:
            result = await db.execute(
                select(Workflow).where(
                    Workflow.is_scheduled.is_(True),
                    Workflow.schedule_cron.isnot(None),
                    Workflow.schedule_cron != "",
                )
            )
            workflows = result.scalars().all()

        for workflow in workflows:
            try:
                self.add_workflow_job(workflow.id, workflow.schedule_cron)
            except Exception as e:
                # 单个工作流 cron 异常不影响其他任务同步
                logger.error(
                    "同步工作流 %s 的定时任务失败: %s", workflow.id, e
                )
        logger.info("定时任务同步完成，共 %d 个工作流", len(workflows))

    # ============ 任务执行 ============

    async def _run_workflow_job(self, workflow_id: int) -> None:
        """定时任务实际执行逻辑

        - 使用独立的 async_session（APScheduler 线程/任务内不得复用请求级 session）
        - 全程 try/except，任何异常都不向上抛出
        """
        db = async_session()
        try:
            # 1. 查询工作流（不存在或已取消调度则跳过）
            result = await db.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if workflow is None:
                logger.warning("定时任务 workflow_%s 对应的工作流不存在，跳过", workflow_id)
                return
            if not workflow.is_scheduled:
                logger.info("工作流 %s 已取消调度，跳过本次执行", workflow_id)
                return

            # 2. 创建执行记录
            started_at = datetime.utcnow()
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                status=TaskStatus.RUNNING,
                trigger_type="schedule",
                input_data={},
                started_at=started_at,
            )
            db.add(execution)
            await db.commit()
            await db.refresh(execution)

            # 3. 调用工作流引擎
            engine = WorkflowEngine()
            run_status = "success"
            try:
                engine_result = await engine.run(
                    workflow_id=workflow_id,
                    execution_id=execution.id,
                    definition=workflow.definition,
                    input_data={},
                )
                if engine_result.get("status") == "success":
                    execution.status = TaskStatus.SUCCESS
                else:
                    execution.status = TaskStatus.FAILED
                    run_status = "failed"
                execution.output_data = engine_result.get("final_output", {})
                execution.node_results = engine_result.get("node_results", [])
                errors = engine_result.get("errors", [])
                execution.error_message = "\n".join(errors) if errors else None
            except Exception as e:
                execution.status = TaskStatus.FAILED
                execution.error_message = str(e)
                run_status = "failed"
                logger.exception("工作流 %s 定时执行异常", workflow_id)

            completed_at = datetime.utcnow()
            execution.completed_at = completed_at

            # 4. 更新工作流统计
            workflow.run_count = (workflow.run_count or 0) + 1
            workflow.last_run_at = completed_at
            workflow.last_run_status = execution.status.value

            # 5. 写入系统指标
            metric = SystemMetric(
                metric_name="scheduled_run",
                metric_value=1,
                labels={"workflow_id": str(workflow_id), "status": run_status},
            )
            db.add(metric)

            await db.commit()
            logger.info(
                "工作流 %s 定时执行完成，状态=%s", workflow_id, run_status
            )
        except Exception as e:
            # 兜底：任何未预期异常都不允许抛出到调度器
            logger.exception("定时任务 workflow_%s 执行失败: %s", workflow_id, e)
            try:
                await db.rollback()
            except Exception:
                pass
        finally:
            await db.close()


# 模块级单例，API 层直接导入使用
scheduler_service = SchedulerService()
