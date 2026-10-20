"""社区发帖测试"""
import uuid

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_post_and_list(client, auth):
    """发帖 -> 帖子列表中能看到该帖子"""
    headers = auth["headers"]
    title = f"测试帖子_{uuid.uuid4().hex[:8]}"
    content = "这是 pytest 自动发布的测试内容，用于验证社区功能。"

    create_resp = await client.post(
        "/api/community/posts",
        headers=headers,
        json={
            "title": title,
            "content": content,
            "post_type": "discussion",
            "tags": ["test", "pytest"],
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    post_id = create_resp.json()["id"]

    # 列表可见
    list_resp = await client.get("/api/community/posts")
    assert list_resp.status_code == 200
    posts = list_resp.json()
    found = [p for p in posts if p["id"] == post_id]
    assert found, "新发布的帖子未出现在列表中"
    assert found[0]["title"] == title
    assert found[0]["author"] == auth["username"]

    # 详情可读
    detail_resp = await client.get(f"/api/community/posts/{post_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["content"] == content


async def test_comment_and_like(client, auth):
    """评论与点赞功能"""
    headers = auth["headers"]
    create_resp = await client.post(
        "/api/community/posts",
        headers=headers,
        json={"title": "可互动帖子", "content": "求赞求评论"},
    )
    post_id = create_resp.json()["id"]

    c_resp = await client.post(
        f"/api/community/posts/{post_id}/comments",
        headers=headers,
        json={"content": "测试评论一条"},
    )
    assert c_resp.status_code == 200, c_resp.text

    like_resp = await client.post(
        f"/api/community/posts/{post_id}/like",
        headers=headers,
    )
    assert like_resp.status_code == 200
    assert like_resp.json()["like_count"] >= 1
