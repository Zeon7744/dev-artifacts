"""Agent 创建与对话测试（LLM 降级时仍返回 200）"""
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_agent_and_chat(client, auth):
    """创建 agent -> 对话接口在 LLM 不可用时优雅降级，仍 200"""
    headers = auth["headers"]

    create_resp = await client.post(
        "/api/agents/",
        headers=headers,
        json={
            "name": "测试助手",
            "description": "pytest agent",
            "agent_type": "custom",
            "system_prompt": "你是一个测试助手",
            "tools": [],
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    agent_id = create_resp.json()["id"]

    chat_resp = await client.post(
        "/api/agents/chat",
        headers=headers,
        json={"agent_id": agent_id, "message": "你好，做个自我介绍"},
    )
    assert chat_resp.status_code == 200, chat_resp.text
    data = chat_resp.json()
    assert "response" in data
    # LLM 不可用时 provider 为 fallback；可用时为 llm。两种都接受
    assert data["provider"] in ("llm", "fallback")
    assert data["agent"] == "测试助手"
    assert isinstance(data["response"], str) and data["response"].strip()


async def test_chat_nonexistent_agent_404(client, auth):
    """与不存在的 agent 对话返回 404"""
    resp = await client.post(
        "/api/agents/chat",
        headers=auth["headers"],
        json={"agent_id": 99999999, "message": "hi"},
    )
    assert resp.status_code == 404, resp.text


async def test_chat_requires_auth(client):
    """对话接口需要登录"""
    resp = await client.post(
        "/api/agents/chat",
        json={"agent_id": 1, "message": "hi"},
    )
    assert resp.status_code in (401, 403), resp.text
