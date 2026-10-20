"""
实时通信 - WebSocket 连接管理器

ConnectionManager 负责：
    1. 维护 WebSocket 连接的生命周期（连接/断开/异常清理）
    2. 按房间(room)对连接分组管理
    3. 向指定房间或全局广播 JSON 消息

所有方法均为 async，内部使用 asyncio.Lock 保证并发安全；
发送失败的死连接会被自动清理，不会导致广播整体崩溃。
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器（房间分组、广播、安全清理）。"""

    def __init__(self) -> None:
        """初始化房间与连接索引。"""
        # 房间名 -> 房间内的 WebSocket 连接集合
        self._rooms: Dict[str, Set[WebSocket]] = {}
        # WebSocket 连接 -> 该连接已加入的房间集合（断开时用于全量清理）
        self._connections: Dict[WebSocket, Set[str]] = {}
        # 保护上述两个字典的异步锁
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room: str) -> None:
        """接受 WebSocket 连接并加入指定房间。

        :param websocket: 待接入的 WebSocket 连接
        :param room: 初始房间名（如 global、workflow/1、agent/2、user/3）
        """
        # 先完成握手；若握手失败（客户端中途断开）则不会污染连接索引
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(room, set()).add(websocket)
            self._connections.setdefault(websocket, set()).add(room)
        logger.info(
            "WebSocket 已连接，加入房间 %s（房间连接数=%d，总连接数=%d）",
            room,
            len(self._rooms.get(room, ())),
            len(self._connections),
        )

    async def join_room(self, websocket: WebSocket, room: str) -> None:
        """将已接受的连接加入额外房间（幂等，重复加入无副作用）。

        :param websocket: 已连接的 WebSocket
        :param room: 目标房间名
        """
        async with self._lock:
            self._rooms.setdefault(room, set()).add(websocket)
            self._connections.setdefault(websocket, set()).add(room)
        logger.info("WebSocket 加入房间 %s", room)

    async def leave_room(self, websocket: WebSocket, room: str) -> None:
        """将连接移出指定房间；房间为空时自动回收。

        :param websocket: 已连接的 WebSocket
        :param room: 目标房间名
        """
        async with self._lock:
            self._remove_unlocked(websocket, room)
        logger.info("WebSocket 离开房间 %s", room)

    async def disconnect(self, websocket: WebSocket, room: Optional[str] = None) -> None:
        """断开清理：从指定房间移除，或从其加入的所有房间移除。

        异常安全：连接/房间不存在时静默跳过，绝不抛出异常。

        :param websocket: 待清理的 WebSocket
        :param room: 指定房间则只清理该房间；为 None 则清理该连接的全部房间
        """
        async with self._lock:
            if room is not None:
                self._remove_unlocked(websocket, room)
            else:
                # 拷贝一份，避免迭代过程中修改集合
                for r in list(self._connections.get(websocket, set())):
                    self._remove_unlocked(websocket, r)
            # 兜底：确保连接索引中不再残留
            self._connections.pop(websocket, None)
        logger.info("WebSocket 已断开清理，当前总连接数=%d", len(self._connections))

    async def broadcast_to_room(self, room: str, message: dict) -> None:
        """向指定房间内的所有连接广播 JSON 消息。

        单个连接发送失败不影响其他连接，失败连接会被自动清理。

        :param room: 目标房间名
        :param message: 可序列化为 JSON 的字典消息
        """
        # 锁内只做快照，锁外执行网络发送，避免慢连接阻塞其他操作
        async with self._lock:
            members: List[WebSocket] = list(self._rooms.get(room, set()))

        dead: List[WebSocket] = []
        for ws in members:
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning("向房间 %s 广播时发送失败，连接将被清理", room)
                dead.append(ws)

        for ws in dead:
            await self.disconnect(ws)

    async def broadcast_global(self, message: dict) -> None:
        """向 global 全局房间广播 JSON 消息。

        :param message: 可序列化为 JSON 的字典消息
        """
        await self.broadcast_to_room("global", message)

    async def send_personal(self, websocket: WebSocket, message: dict) -> bool:
        """向单个连接发送 JSON 消息（系统通知/回执/错误等）。

        :param websocket: 目标连接
        :param message: 可序列化为 JSON 的字典消息
        :return: 发送成功返回 True；失败（连接已断）返回 False 并清理
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            logger.warning("向单个连接发送消息失败，连接将被清理")
            await self.disconnect(websocket)
            return False

    def _remove_unlocked(self, websocket: WebSocket, room: str) -> None:
        """从房间与连接双向索引中移除（调用方需持有 self._lock）。"""
        members = self._rooms.get(room)
        if members is not None:
            members.discard(websocket)
            if not members:
                self._rooms.pop(room, None)

        joined = self._connections.get(websocket)
        if joined is not None:
            joined.discard(room)
            if not joined:
                self._connections.pop(websocket, None)

    @property
    def active_connections(self) -> int:
        """当前活跃连接总数。"""
        return len(self._connections)

    @property
    def rooms(self) -> List[str]:
        """当前非空房间名列表。"""
        return list(self._rooms.keys())


# 全局单例：API 路由与业务服务（工作流引擎/Agent 等）共用同一个管理器
manager = ConnectionManager()
