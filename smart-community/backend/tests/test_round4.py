"""第四轮功能测试：社区互动通知 + 插件审核流 + Agent SSE 流式对话"""
import uuid

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

SAFE_PLUGIN_CODE = """
def execute(config, ctx):
    values = config.get("values", [1, 2, 3])
    total = sum(v for v in values)
    return {"sum": total, "count": len(values)}
"""


# ============ 社区互动通知 ============

async def test_comment_notifies_post_author(client, auth):
    """B 评论 A 的帖子 → A 收到 community 通知；A 自己评论自己不通知"""
    headers_a = auth["headers"]
    # A 发帖
    post_resp = await client.post(
        "/api/community/posts",
        headers=headers_a,
        json={"title": f"通知测试帖_{uuid.uuid4().hex[:6]}", "content": "求评论"},
    )
    post_id = post_resp.json()["id"]

    # B 注册并评论
    suid = uuid.uuid4().hex[:10]
    await client.post(
        "/api/auth/register",
        json={"username": f"cmt_{suid}", "email": f"cmt_{suid}@t.local", "password": "TestPassw0rd!123"},
    )
    login_b = await client.post(
        "/api/auth/login", json={"username": f"cmt_{suid}", "password": "TestPassw0rd!123"}
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    cresp = await client.post(
        f"/api/community/posts/{post_id}/comments",
        headers=headers_b,
        json={"content": "好帖，支持一下！"},
    )
    assert cresp.status_code == 200, cresp.text

    # A 的通知列表应有 community 类通知
    notif_resp = await client.get("/api/notifications", headers=headers_a)
    assert notif_resp.status_code == 200
    community_notifs = [n for n in notif_resp.json()["items"] if n["category"] == "community"]
    assert len(community_notifs) >= 1, "帖子作者未收到评论通知"
    assert "评论" in community_notifs[0]["title"]

    # A 自己评论自己的帖子 → 不新增通知
    before = len(community_notifs)
    await client.post(
        f"/api/community/posts/{post_id}/comments",
        headers=headers_a,
        json={"content": "自评一条"},
    )
    notif_resp2 = await client.get("/api/notifications", headers=headers_a)
    self_notifs = [n for n in notif_resp2.json()["items"] if n["category"] == "community"]
    assert len(self_notifs) == before, "自己评论自己不应产生通知"


async def test_like_notifies_post_author(client, auth):
    """B 点赞 A 的帖子 → A 收到点赞通知"""
    headers_a = auth["headers"]
    post_id = (
        await client.post(
            "/api/community/posts",
            headers=headers_a,
            json={"title": f"点赞测试_{uuid.uuid4().hex[:6]}", "content": "赞我"},
        )
    ).json()["id"]

    suid = uuid.uuid4().hex[:10]
    await client.post(
        "/api/auth/register",
        json={"username": f"lik_{suid}", "email": f"lik_{suid}@t.local", "password": "TestPassw0rd!123"},
    )
    login_b = await client.post(
        "/api/auth/login", json={"username": f"lik_{suid}", "password": "TestPassw0rd!123"}
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    lresp = await client.post(f"/api/community/posts/{post_id}/like", headers=headers_b)
    assert lresp.status_code == 200

    notifs = (await client.get("/api/notifications", headers=headers_a)).json()["items"]
    like_notifs = [n for n in notifs if (n.get("data") or {}).get("action") == "like"]
    assert len(like_notifs) >= 1, "帖子作者未收到点赞通知"


# ============ 插件审核流 ============

async def test_plugin_review_flow(client, auth, admin_auth):
    """普通作者提交插件 → 自发布仅进入待审 → 管理员审核通过后上架并可用"""
    headers = auth["headers"]
    admin_headers = admin_auth["headers"]
    node_type = f"plugin.review_{uuid.uuid4().hex[:8]}"

    # 1. 作者提交带代码插件
    resp = await client.post(
        "/api/plugins/custom",
        headers=headers,
        json={
            "name": "待审插件",
            "node_type": node_type,
            "code": SAFE_PLUGIN_CODE,
            "config_schema": {"fields": []},
        },
    )
    assert resp.status_code == 200, resp.text
    plugin_id = resp.json()["id"]
    assert resp.json()["status"] == "pending_review"

    # 2. 沙箱试跑可用
    test_resp = await client.post(
        f"/api/plugins/custom/{plugin_id}/test",
        headers=headers,
        json={"config": {"values": [10, 20, 30]}, "ctx": {}},
    )
    assert test_resp.status_code == 200, test_resp.text
    assert test_resp.json()["success"] is True
    assert test_resp.json()["output"]["sum"] == 60

    # 3. 作者调 publish → 仍为待审核，不上架
    pub_resp = await client.post(f"/api/plugins/custom/{plugin_id}/publish", headers=headers)
    assert pub_resp.status_code == 200, pub_resp.text
    assert pub_resp.json()["status"] == "pending_review"

    # 市场列表与 types 中不应出现
    listed = await client.get("/api/plugins/")
    assert node_type not in {p["node_type"] for p in listed.json()}

    # 4. 管理员看到待审列表
    pending = await client.get("/api/plugins/admin/pending", headers=admin_headers)
    assert pending.status_code == 200
    assert node_type in {p["node_type"] for p in pending.json()}

    # 普通用户无权访问待审列表
    forbidden = await client.get("/api/plugins/admin/pending", headers=headers)
    assert forbidden.status_code == 403

    # 5. 管理员审核通过
    approve = await client.post(
        f"/api/plugins/admin/{plugin_id}/approve",
        headers=admin_headers,
        json={"comment": "代码安全，同意上架"},
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["status"] == "approved"

    # 6. 上架后市场可见、types 包含
    listed2 = await client.get("/api/plugins/")
    assert node_type in {p["node_type"] for p in listed2.json()}
    types2 = await client.get("/api/plugins/types")
    assert node_type in types2.json()["types"]

    # 7. 作者收到审核通过通知
    author_notifs = (await client.get("/api/notifications", headers=headers)).json()["items"]
    approved_notifs = [
        n for n in author_notifs if n["category"] == "plugin" and "通过" in n["title"]
    ]
    assert len(approved_notifs) >= 1, "作者未收到审核通过通知"


async def test_plugin_reject_flow(client, auth, admin_auth):
    """管理员驳回 → 插件不上架，作者收到驳回通知"""
    headers = auth["headers"]
    admin_headers = admin_auth["headers"]
    node_type = f"plugin.reject_{uuid.uuid4().hex[:8]}"

    plugin_id = (
        await client.post(
            "/api/plugins/custom",
            headers=headers,
            json={"name": "被驳回插件", "node_type": node_type, "code": SAFE_PLUGIN_CODE},
        )
    ).json()["id"]

    reject = await client.post(
        f"/api/plugins/admin/{plugin_id}/reject",
        headers=admin_headers,
        json={"comment": "功能与内置插件重复"},
    )
    assert reject.status_code == 200, reject.text
    assert reject.json()["status"] == "rejected"

    listed = await client.get("/api/plugins/")
    assert node_type not in {p["node_type"] for p in listed.json()}

    author_notifs = (await client.get("/api/notifications", headers=headers)).json()["items"]
    rejected_notifs = [n for n in author_notifs if "未通过" in n["title"]]
    assert len(rejected_notifs) >= 1, "作者未收到驳回通知"

    # 我的插件列表能看到 rejected 状态
    mine = await client.get("/api/plugins/custom/mine", headers=headers)
    assert mine.status_code == 200
    mine_entry = [p for p in mine.json() if p["node_type"] == node_type][0]
    assert mine_entry["review_status"] == "rejected"


async def test_admin_publish_directly(client, admin_auth):
    """管理员提交并自行发布 → 直接上架（无需二审）"""
    admin_headers = admin_auth["headers"]
    node_type = f"plugin.admpub_{uuid.uuid4().hex[:8]}"

    plugin_id = (
        await client.post(
            "/api/plugins/custom",
            headers=admin_headers,
            json={"name": "管理员插件", "node_type": node_type, "code": SAFE_PLUGIN_CODE},
        )
    ).json()["id"]

    pub = await client.post(f"/api/plugins/custom/{plugin_id}/publish", headers=admin_headers)
    assert pub.status_code == 200, pub.text
    assert pub.json()["status"] == "published"

    listed = await client.get("/api/plugins/")
    assert node_type in {p["node_type"] for p in listed.json()}


# ============ Agent SSE 流式对话 ============

async def test_agent_chat_stream_sse(client, auth):
    """/api/agents/chat/stream 返回 SSE 事件流（LLM 不可用时降级文本也走 token 事件）"""
    headers = auth["headers"]
    agent_id = (
        await client.post(
            "/api/agents/",
            headers=headers,
            json={"name": "流式助手", "system_prompt": "你是助手"},
        )
    ).json()["id"]

    async with client.stream(
        "POST",
        "/api/agents/chat/stream",
        headers=headers,
        json={"agent_id": agent_id, "message": "你好，流式回复测试"},
    ) as resp:
        assert resp.status_code == 200, resp.text
        assert "text/event-stream" in resp.headers["content-type"]
        events = []
        async for line in resp.aiter_lines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())

    assert "meta" in events
    assert "token" in events
    assert events[-1] == "done"


async def test_agent_stream_requires_auth(client):
    """流式对话需要登录"""
    resp = await client.post(
        "/api/agents/chat/stream", json={"agent_id": 1, "message": "hi"}
    )
    assert resp.status_code in (401, 403), resp.text
