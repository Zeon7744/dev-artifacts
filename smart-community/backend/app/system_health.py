"""
系统健康监控 - 周期性检查 LLM Provider 可用性，状态变化时告警

设计：
- check_and_alert() 由调度器周期触发（默认 5 分钟）；
- 内存中维护上一次健康状态，仅在 可用→不可用 / 恢复 时发通知，避免刷屏；
- 告警同时：① 落库+WS 通知所有管理员 ② global 房间实时广播（在线用户即时可见）；
- 旁路设计：任何异常都不抛出，绝不影响调度器与主业务。
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# provider -> 上次是否可用（None 表示尚未首次检查，首次不告警）
_last_status: Dict[str, Optional[bool]] = {}


async def check_and_alert() -> Dict[str, bool]:
    """执行一次健康检查，状态变化时发送告警。返回当前各 provider 状态。"""
    try:
        from .services.llm_service import LLMService

        llm = LLMService()
        status = await llm.health_check()
    except Exception:
        logger.exception("健康检查执行失败")
        return {"ollama": False, "openai": False}

    global _last_status
    for provider, available in status.items():
        previous = _last_status.get(provider)
        _last_status[provider] = available
        if previous is None:
            # 首次检查只记录基线，不告警
            continue
        if previous == available:
            continue

        try:
            if not available:
                title = f"⚠️ LLM 服务异常：{provider} 不可用"
                content = (
                    f"健康检查检测到 {provider} 连接失败，依赖 AI 的功能（Agent 对话、"
                    "工作流 AI 节点、RAG 回答）将进入降级模式。"
                )
                level = "error"
            else:
                title = f"✅ LLM 服务恢复：{provider} 已可用"
                content = f"{provider} 健康检查通过，AI 功能恢复正常。"
                level = "success"

            # 1. 管理员落库通知（离线可追溯）
            from .notifications import notify_admins, notify_system

            await notify_admins(
                category="system",
                level=level,
                title=title,
                content=content,
                data={"provider": provider, "available": available, "kind": "llm_health"},
            )
            # 2. 全局实时广播（在线用户即时看到）
            await notify_system(
                category="system",
                level=level,
                title=title,
                content=content,
                data={"provider": provider, "available": available, "kind": "llm_health"},
            )
        except Exception:
            logger.exception("健康告警发送失败 provider=%s", provider)

    return status


def register_health_job(scheduler_service, minutes: int = 5) -> None:
    """把健康检查注册为周期任务（幂等）。"""
    try:
        scheduler = scheduler_service._ensure_running()
        scheduler.add_job(
            check_and_alert,
            "interval",
            minutes=minutes,
            id="system_health_check",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        logger.info("系统健康检查任务已注册，间隔 %s 分钟", minutes)
    except Exception:
        logger.exception("注册健康检查任务失败（不影响主服务）")
