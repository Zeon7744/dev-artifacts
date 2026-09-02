"""实时通信状态测试"""
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_realtime_status(client):
    """GET /api/realtime/status 返回 ws available"""
    resp = await client.get("/api/realtime/status")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ws"] == "available"
    # 房间与连接数字段存在
    assert "rooms" in data
    assert "connections" in data
    assert isinstance(data["connections"], int)
