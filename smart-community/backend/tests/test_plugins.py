"""插件市场测试：3 个内置插件 + 自定义插件提交与冲突"""
import uuid

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

BUILTIN_NODE_TYPES = {"plugin.text_format", "plugin.json_transform", "plugin.math_calc"}


async def test_list_builtin_plugins(client):
    """GET /api/plugins 包含 3 个内置插件（无需登录）"""
    resp = await client.get("/api/plugins/")
    assert resp.status_code == 200, resp.text
    plugins = resp.json()
    node_types = {p["node_type"] for p in plugins}
    assert BUILTIN_NODE_TYPES <= node_types, f"内置插件缺失: {node_types}"

    builtin_plugins = [p for p in plugins if p["is_builtin"]]
    assert len(builtin_plugins) >= 3

    # types 面板同样包含内置类型
    types_resp = await client.get("/api/plugins/types")
    assert types_resp.status_code == 200
    types = set(types_resp.json()["types"])
    assert BUILTIN_NODE_TYPES <= types


async def test_create_custom_plugin_and_conflict(client, auth):
    """提交自定义插件成功；重复 node_type 返回 409"""
    headers = auth["headers"]
    node_type = f"plugin.custom_{uuid.uuid4().hex[:8]}"

    # 首次提交 -> pending_review
    resp1 = await client.post(
        "/api/plugins/custom",
        headers=headers,
        json={
            "name": "我的自定义插件",
            "description": "pytest custom plugin",
            "node_type": node_type,
            "config_schema": {"fields": []},
            "tags": ["custom"],
        },
    )
    assert resp1.status_code == 200, resp1.text
    assert resp1.json()["status"] == "pending_review"

    # 同 node_type 再次提交 -> 409
    resp2 = await client.post(
        "/api/plugins/custom",
        headers=headers,
        json={"name": "重复插件", "node_type": node_type},
    )
    assert resp2.status_code == 409, resp2.text

    # 与内置 node_type 冲突也 -> 409
    resp3 = await client.post(
        "/api/plugins/custom",
        headers=headers,
        json={"name": "抢内置类型", "node_type": "plugin.math_calc"},
    )
    assert resp3.status_code == 409, resp3.text


async def test_custom_plugin_requires_auth(client):
    """提交自定义插件需要登录"""
    resp = await client.post(
        "/api/plugins/custom",
        json={"name": "x", "node_type": "plugin.anonymous_x"},
    )
    assert resp.status_code in (401, 403), resp.text
