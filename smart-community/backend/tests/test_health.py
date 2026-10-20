"""系统健康检查测试"""
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_health_ok(client):
    """GET /api/health 返回 200 且状态 healthy"""
    resp = await client.get("/api/health")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    # llm_providers 字典存在（ollama 未启动时对应值为 False，不影响健康）
    assert "llm_providers" in data
    assert "ollama" in data["llm_providers"]


async def test_root_info(client):
    """根路径返回服务元信息"""
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert "modules" in data
