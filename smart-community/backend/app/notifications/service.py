"""
通知服务 - 通知持久化 + WebSocket 实时推送

业务模块统一调用：
    await notify_user(db, user_id, category, title, content, level, data)
    await notify_system(...)         # 向 global 房间广播（不落库）

设计要点：
- 每个通知用独立的数据库会话写入（async_session），不依赖调用方的请求会话，
  因此可以安全地在请求结束后、调度任务、后台协程中调用；
- 实时推送与持久化相互隔离：推送失败只记日志，不影响落库；
- 任何异常都不向上抛出——通知是旁路能力，绝不能阻断主业务。
"""
import logging
from typing import Any, Dict, List, Optional

from ..core.database import async_session
from ..realtime.manager import manager
from .models import Notification

logger = logging.getLogger(__name__)


async def notify_user(
    user_id: Optional[int],
    category: str,
    title: str,
    content: str = "",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
    *,
    db=None,
    persist: bool = True,
) -> None:
    """向单个用户发送通知：落库 + WS 推送到 user/{id} 房间。

    :param user_id: 接收用户 ID；为 None 时只做全局广播
    :param category: 通知类别 workflow/schedule/agent/system/plugin/community
    :param title: 通知标题
    :param content: 正文
    :param level: info/success/warning/error
    :param data: 附加结构化数据
    :param db: 可选，复用调用方会话；不传则内部开独立会话
    :param persist: 是否落库（实时-only 场景可传 False）
    """
    message = {
        "type": "notification",
        "category": category,
        "level": level,
        "title": title,
        "message": content or title,  # message 字段兼容前端既有渲染
        "data": data or {},
    }

    # 1. 实时推送（在线用户立即收到）
    try:
        if user_id is not None:
            await manager.broadcast_to_room(f"user/{user_id}", message)
    except Exception:
        logger.warning("通知 WS 推送失败 user=%s title=%s", user_id, title)

    # 2. 持久化（离线用户稍后拉取）
    if not persist or user_id is None:
        return
    try:
        own_session = db is None
        if own_session:
            db = async_session()
        try:
            notif = Notification(
                user_id=user_id,
                category=category,
                level=level,
                title=title,
                content=content,
                data=data or {},
                is_read=False,
            )
            db.add(notif)
            await db.commit()
        finally:
            if own_session:
                await db.close()
    except Exception:
        logger.exception("通知落库失败 user=%s title=%s", user_id, title)


async def notify_system(
    category: str,
    title: str,
    content: str = "",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """系统级广播：推送到 global 房间（所有在线用户），不落库。"""
    message = {
        "type": "notification",
        "category": category,
        "level": level,
        "title": title,
        "message": content or title,
        "data": data or {},
    }
    try:
        await manager.broadcast_global(message)
    except Exception:
        logger.warning("系统广播通知推送失败 title=%s", title)


async def list_notifications(
    user_id: int, unread_only: bool = False, limit: int = 30
) -> List[Dict[str, Any]]:
    """拉取用户通知列表（最新在前）。"""
    from sqlalchemy import select

    async with async_session() as db:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        rows = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": n.id,
                "category": n.category,
                "level": n.level,
                "title": n.title,
                "content": n.content,
                "data": n.data or {},
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in rows
        ]


async def unread_count(user_id: int) -> int:
    """用户未读通知数（铃铛角标）。"""
    from sqlalchemy import func, select

    async with async_session() as db:
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        return int((await db.execute(stmt)).scalar() or 0)


async def mark_read(user_id: int, notification_id: Optional[int] = None) -> int:
    """标记通知已读。notification_id 为 None 时全部已读，返回受影响行数。"""
    from sqlalchemy import select, update

    async with async_session() as db:
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        if notification_id is not None:
            stmt = stmt.where(Notification.id == notification_id)
        rows = (await db.execute(stmt)).scalars().all()
        for row in rows:
            row.is_read = True
        await db.commit()
        return len(rows)


async def notify_admins(
    category: str,
    title: str,
    content: str = "",
    level: str = "warning",
    data: Optional[Dict[str, Any]] = None,
) -> int:
    """向所有管理员（role=admin）发送通知：落库 + WS 推送到各自 user 房间。

    用于插件审核请求、系统健康告警等运维场景。旁路设计，任何异常都不抛出。
    返回实际发送的管理员数量。
    """
    try:
        from sqlalchemy import select

        from ..models.database import User, UserRole

        async with async_session() as db:
            admins = (
                await db.execute(select(User).where(User.role == UserRole.ADMIN))
            ).scalars().all()
            admin_ids = [a.id for a in admins]

        for admin_id in admin_ids:
            try:
                await notify_user(
                    admin_id,
                    category=category,
                    title=title,
                    content=content,
                    level=level,
                    data=data,
                )
            except Exception:
                logger.warning("管理员通知发送失败 admin=%s title=%s", admin_id, title)
        return len(admin_ids)
    except Exception:
        logger.exception("notify_admins 执行失败 title=%s", title)
        return 0
