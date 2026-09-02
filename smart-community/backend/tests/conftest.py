"""
pytest 全局配置与 fixture

注意顺序：本模块顶部必须在 import 任何 app 业务模块之前设置环境变量，
否则 app.core.config / app.core.database 会在导入时用默认 DATABASE_URL
创建 engine，测试隔离失效。
"""
import os
import uuid

# ---- 1. 在导入任何 app 模块之前设置测试环境变量 ----
# 每个测试进程使用独立的临时 sqlite 文件（uuid + pid 双重保证隔离）
_TEST_DB_PATH = f"/tmp/test_sc_{os.getpid()}_{uuid.uuid4().hex[:8]}.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"
# settings 读取的是 SECRET_KEY 环境变量（见 app/core/config.py）
os.environ["SECRET_KEY"] = "test-secret-key-pytest-only-not-for-prod"
# 测试环境强制 LLM 走 ollama（无服务时自动快速降级为 fallback）
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("DEBUG", "false")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402

# ---- 2. 现在才可以导入 app ----
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop_policy():
    """会话级事件循环策略：所有异步 fixture / 测试共享同一个 event loop。

    必要性：app 的 APScheduler 与 SQLAlchemy async engine 均为模块级单例，
    跨 event loop 复用会报错；全局 pytest.ini 默认 function 作用域，这里覆盖为 session。
    """
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client():
    """进程内 ASGI 测试客户端（session 级）。

    - 使用 httpx.ASGITransport 直接挂载 FastAPI app，无需真实端口；
    - 通过 LifespanManager 触发 app 的 lifespan（建表 + 启动调度器）；
    - 所有测试共享一个 event loop（pytest-asyncio session 作用域），
      避免 APScheduler 单例跨 event loop 复用问题。
    """
    try:
        from asgi_lifespan import LifespanManager

        async with LifespanManager(app) as manager:
            transport = ASGITransport(app=manager.app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
                timeout=30.0,
            ) as ac:
                yield ac
    except ImportError:
        # 兜底：没有 asgi-lifespan 时手动初始化数据库
        from app.core.database import init_db

        await init_db()
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            timeout=30.0,
        ) as ac:
            yield ac


async def register_and_login(client: AsyncClient, prefix: str = "") -> dict:
    """注册一个全新随机用户并登录，返回 {"user":..., "token":..., "headers":{...}}。

    每次调用都用 uuid 后缀，保证测试之间用户不冲突。
    """
    suid = uuid.uuid4().hex[:10]
    username = f"test_{prefix}_{suid}"
    email = f"{username}@test.local"
    password = "TestPassw0rd!123"

    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "display_name": f"Test {suid[:6]}",
        },
    )
    assert reg_resp.status_code == 200, f"注册失败: {reg_resp.text}"
    reg_data = reg_resp.json()

    # 登录换 token（顺带验证登录链路）
    login_resp = await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert login_resp.status_code == 200, f"登录失败: {login_resp.text}"
    token = login_resp.json()["access_token"]

    return {
        "user": reg_data.get("user", {}),
        "username": username,
        "email": email,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest_asyncio.fixture
async def auth(client: AsyncClient) -> dict:
    """函数级 fixture：为当前测试创建一个独立新用户（带认证头）。"""
    name = os.environ.get("PYTEST_CURRENT_TEST", "case").split("::")[-1][:20]
    return await register_and_login(client, prefix=name)


@pytest_asyncio.fixture
async def admin_auth(client: AsyncClient) -> dict:
    """函数级 fixture：创建一个管理员角色用户（直接通过 ORM 提权），返回认证头。"""
    auth_info = await register_and_login(client, prefix="admin")
    # 通过独立会话把该用户提升为 admin
    from app.core.database import async_session
    from app.models.database import User, UserRole
    from sqlalchemy import update

    async with async_session() as db:
        await db.execute(
            update(User).where(User.username == auth_info["username"]).values(role=UserRole.ADMIN)
        )
        await db.commit()
    return auth_info
