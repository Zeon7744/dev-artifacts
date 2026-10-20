"""
通知中心 - ORM 模型

通知双通道：
1. 实时通道：创建时通过 WebSocket 推送到该用户房间（user/{id}）
2. 持久通道：写入 notifications 表，用户离线/断线重连后可拉取未读

所有业务模块（工作流执行、定时任务、告警、插件审核等）统一走
app.notifications.service.notify_user / notify_system，不直接操作本表。
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from ..models.database import Base


class Notification(Base):
    """用户通知记录"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 接收用户；系统级广播通知 user_id 为 NULL（暂不使用，预留）
    user_id = Column(Integer, index=True, nullable=True)

    # 通知类别：workflow(工作流) / schedule(定时任务) / agent / system / plugin / community
    category = Column(String(30), default="system", index=True)

    # 级别：info / success / warning / error
    level = Column(String(10), default="info")

    title = Column(String(200), default="")
    content = Column(Text, default="")

    # 附加结构化数据（工作流 id、执行 id 等，前端可用于跳转）
    data = Column(JSON, default=dict)

    is_read = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
