"""认证与受保护接口鉴权测试"""
import pytest

from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_register_login_and_protected_access(client):
    """注册 -> 登录 -> 带 token 访问受保护接口成功"""
    account = await register_and_login(client, prefix="auth_ok")
    headers = account["headers"]

    # 带 token 访问 /api/users/me（受保护接口）
    resp = await client.get("/api/users/me", headers=headers)
    assert resp.status_code == 200, resp.text
    me = resp.json()
    assert me["username"] == account["username"]
    assert me["id"] == account["user"]["id"]


async def test_protected_without_token_unauthorized(client):
    """无 token 访问受保护接口被拒绝（401/403）"""
    resp = await client.get("/api/users/me")
    # HTTPBearer(auto_error=True) 无凭据时 FastAPI 返回 403
    assert resp.status_code in (401, 403), resp.text


async def test_protected_with_bad_token_unauthorized(client):
    """伪造/无效 token 访问受保护接口返回 401"""
    resp = await client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert resp.status_code == 401, resp.text


async def test_duplicate_register_fails(client):
    """重复用户名/邮箱注册返回 400"""
    account = await register_and_login(client, prefix="auth_dup")
    resp = await client.post(
        "/api/auth/register",
        json={
            "username": account["username"],
            "email": account["email"],
            "password": account["password"],
        },
    )
    assert resp.status_code == 400, resp.text


async def test_login_wrong_password(client):
    """错误密码登录返回 401"""
    account = await register_and_login(client, prefix="auth_pwd")
    resp = await client.post(
        "/api/auth/login",
        json={"username": account["username"], "password": "wrong-password-xxx"},
    )
    assert resp.status_code == 401, resp.text
