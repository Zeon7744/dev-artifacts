"""
通知中心 API

路由（路径内置 /api 前缀，main.py include_router 时不加 prefix）：
- GET  /api/notifications/unread-count   未读数（铃铛角标）
- GET  /api/notifications                通知列表（?unread=true 仅未读）
- POST /api/notifications/read-all       全部标记已读
- POST /api/notifications/{id}/read      单条标记已读
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import get_current_user
from ..core.database import get_session
from ..models.database import User
from ..notifications import list_notifications, mark_read, unread_count

router = APIRouter()


@router.get("/api/notifications/unread-count")
async def get_unread_count(user: User = Depends(get_current_user)):
    """未读通知数量。"""
    return {"unread": await unread_count(user.id)}


@router.get("/api/notifications")
async def get_notifications(
    unread: bool = False,
    limit: int = 30,
    user: User = Depends(get_current_user),
):
    """通知列表（最新在前）。"""
    items = await list_notifications(user.id, unread_only=unread, limit=min(limit, 100))
    return {"items": items, "unread": sum(1 for i in items if not i["is_read"])}


@router.post("/api/notifications/read-all")
async def read_all_notifications(user: User = Depends(get_current_user)):
    """全部标记已读。"""
    count = await mark_read(user.id)
    return {"marked": count}


@router.post("/api/notifications/{notification_id}/read")
async def read_one_notification(
    notification_id: int,
    user: User = Depends(get_current_user),
):
    """单条标记已读。"""
    count = await mark_read(user.id, notification_id)
    if count == 0:
        raise HTTPException(status_code=404, detail="通知不存在或已读")
    return {"marked": count}
