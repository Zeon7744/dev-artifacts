"""
实时通信 API - WebSocket 端点与状态查询

路由说明（注意：WebSocket 端点路径为绝对路径 /api/ws，
主程序集成时请使用 app.include_router(router) 而不要加 prefix）：
    - GET  /api/realtime/status : HTTP 端点，返回实时服务状态
    - WS   /api/ws              : WebSocket 主端点
        query 参数：
            - token : JWT 认证令牌（必填，HS256 验证 sub 字段）
            - room  : 初始房间（可选，默认 global）

客户端消息协议（JSON）：
    {"type": "subscribe", "room": "workflow/1"}     加入额外房间
    {"type": "unsubscribe", "room": "workflow/1"}   离开房间
    {"type": "message", "room": "global", "data": {...}}  向房间广播消息
    {"type": "ping"}                                心跳，服务端回 pong

认证失败时服务端以 WebSocket close code 4001 关闭连接。
"""
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from ..core.config import settings
from ..realtime.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

# 非法/过期 token 的 WebSocket 关闭码
WS_CODE_UNAUTHORIZED = 4001


def _decode_token(token: str) -> Optional[str]:
    """验证 JWT 并返回用户 ID（payload 的 sub 字段）。

    :param token: JWT 令牌字符串
    :return: 验证通过返回用户 ID 字符串；失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        sub = payload.get("sub")
        return str(sub) if sub is not None else None
    except (JWTError, KeyError, ValueError) as exc:
        logger.warning("WebSocket token 验证失败: %s", exc)
        return None


@router.get("/api/realtime/status")
async def realtime_status() -> dict:
    """实时服务状态：可用性、当前房间列表、活跃连接数。"""
    return {
        "ws": "available",
        "rooms": manager.rooms,
        "connections": manager.active_connections,
    }


@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = "", room: str = "global") -> None:
    """WebSocket 主端点：认证、房间订阅、消息转发与心跳。

    :param websocket: WebSocket 连接
    :param token: JWT 认证令牌（query 参数）
    :param room: 初始房间名（query 参数，默认 global）
    """
    # ---- 认证阶段：握手前校验 token，非法则拒绝握手并以 4001 关闭 ----
    user_id = _decode_token(token)
    if user_id is None:
        await websocket.close(code=WS_CODE_UNAUTHORIZED)
        return

    # ---- 接入阶段：接受连接并加入初始房间 ----
    await manager.connect(websocket, room)
    try:
        await manager.send_personal(
            websocket,
            {"type": "system", "message": f"connected to {room}"},
        )

        # ---- 消息循环 ----
        while True:
            try:
                payload = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except Exception:
                # 非 JSON 等无效消息：忽略后继续接收，不断开连接
                logger.debug("收到无法解析的 WebSocket 消息，已忽略")
                continue

            if not isinstance(payload, dict):
                continue

            msg_type = payload.get("type")

            if msg_type == "subscribe":
                target_room = payload.get("room")
                if isinstance(target_room, str) and target_room:
                    await manager.join_room(websocket, target_room)
                    await manager.send_personal(
                        websocket,
                        {"type": "system", "message": f"subscribed to {target_room}"},
                    )

            elif msg_type == "unsubscribe":
                target_room = payload.get("room")
                if isinstance(target_room, str) and target_room:
                    await manager.leave_room(websocket, target_room)
                    await manager.send_personal(
                        websocket,
                        {"type": "system", "message": f"unsubscribed from {target_room}"},
                    )

            elif msg_type == "message":
                # 目标房间优先取消息内 room，缺省回到初始房间
                target_room = payload.get("room") if isinstance(payload.get("room"), str) else room
                await manager.broadcast_to_room(
                    target_room,
                    {
                        "type": "message",
                        "from": user_id,
                        "data": payload.get("data"),
                    },
                )

            elif msg_type == "ping":
                await manager.send_personal(websocket, {"type": "pong"})

            else:
                await manager.send_personal(
                    websocket,
                    {"type": "system", "message": f"unknown message type: {msg_type}"},
                )

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开（user_id=%s）", user_id)
    except Exception:
        # 循环中任何未预期异常都安全落盘，保证清理逻辑必定执行
        logger.exception("WebSocket 会话异常（user_id=%s）", user_id)
    finally:
        # ---- 清理阶段：离开该连接加入的所有房间 ----
        await manager.disconnect(websocket)
