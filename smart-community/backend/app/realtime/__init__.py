"""
AI Smart Community - 实时通信模块

提供 WebSocket 连接管理（按房间分组）与实时消息广播能力。

房间(room)命名约定：
    - workflow/{id} : 工作流执行状态推送房间
    - agent/{id}    : Agent 会话房间
    - user/{id}     : 用户私人通知房间
    - global        : 全局广播房间
"""
from .manager import ConnectionManager, manager

__all__ = ["ConnectionManager", "manager"]
