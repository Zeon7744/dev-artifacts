"""插件市场 API - 插件列表、安装、自定义插件提交、配置 schema 查询"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_session
from ..core.auth import get_current_user, require_role
from ..models.database import User, UserRole
# 导入 plugins 包：触发内置插件注册，并确保 plugins 表已注册到 Base.metadata
from ..plugins import registry
from ..plugins.models import Plugin

router = APIRouter()


def _register_to_registry(plugin: Plugin) -> None:
    """将已发布插件注册到全局 registry（立即生效，无需重启）。异常由调用方决定处理。"""
    from ..plugins.base import registry as reg
    from ..plugins.sandbox import CustomSandboxPlugin

    reg.register(CustomSandboxPlugin(plugin))


def _plugin_dict(plugin: Plugin) -> dict:
    """自定义插件序列化（作者/审核面板共用）。"""
    return {
        "id": plugin.id,
        "name": plugin.name,
        "version": plugin.version,
        "description": plugin.description,
        "node_type": plugin.node_type,
        "config_schema": plugin.config_schema or {},
        "tags": plugin.tags or [],
        "is_published": bool(plugin.is_published),
        "review_status": plugin.review_status or "pending_review",
        "review_comment": plugin.review_comment,
        "install_count": plugin.install_count or 0,
        "author_id": plugin.author_id,
        "created_at": plugin.created_at.isoformat() if plugin.created_at else None,
        "reviewed_at": plugin.reviewed_at.isoformat() if plugin.reviewed_at else None,
    }


class CustomPluginCreate(BaseModel):
    """开发者提交自定义插件的请求体"""
    name: str = Field(..., max_length=100, description="插件名称")
    description: str = ""
    node_type: str = Field(..., max_length=100, description="自定义节点类型名，如 plugin.my_sms")
    code: Optional[str] = None
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


@router.get("/")
async def list_plugins(db: AsyncSession = Depends(get_session)):
    """列出所有可用插件：内置 registry 插件 + 数据库中已发布插件"""
    # 内置插件（注册器中的）
    result = []
    for meta in registry.list_all():
        result.append({
            "name": meta["name"],
            "version": meta["version"],
            "description": meta["description"],
            "node_type": meta["node_type"],
            "config_schema": meta["config_schema"],
            "is_builtin": True,
            "install_count": 0,
        })

    # 数据库中已发布的自定义插件
    db_result = await db.execute(select(Plugin).where(Plugin.is_published == True))  # noqa: E712
    for plugin in db_result.scalars().all():
        result.append({
            "name": plugin.name,
            "version": plugin.version,
            "description": plugin.description,
            "node_type": plugin.node_type,
            "config_schema": plugin.config_schema or {},
            "is_builtin": bool(plugin.is_builtin),
            "install_count": plugin.install_count or 0,
        })
    return result


@router.get("/types")
async def list_plugin_types(db: AsyncSession = Depends(get_session)):
    """返回所有可用 node_type 列表（工作流编辑器节点面板使用）"""
    types = set(registry.node_types())
    db_result = await db.execute(
        select(Plugin.node_type).where(Plugin.is_published == True)  # noqa: E712
    )
    types.update(row[0] for row in db_result.all())
    return {"types": sorted(types)}


@router.post("/install/{node_type}")
async def install_plugin(node_type: str, db: AsyncSession = Depends(get_session)):
    """安装插件：数据库中的插件 install_count + 1；内置插件无需安装直接可用"""
    result = await db.execute(select(Plugin).where(Plugin.node_type == node_type))
    plugin = result.scalar_one_or_none()
    if plugin is not None:
        plugin.install_count = (plugin.install_count or 0) + 1
        await db.commit()
        return {"node_type": node_type, "installed": True, "install_count": plugin.install_count}

    # 内置插件不存数据库，注册器中存在即视为可直接使用
    if registry.get(node_type) is not None:
        return {"node_type": node_type, "installed": True, "is_builtin": True, "install_count": 0}

    raise HTTPException(status_code=404, detail="插件不存在")


@router.post("/custom")
async def create_custom_plugin(
    req: CustomPluginCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """开发者提交自定义插件（需登录认证）。

    安全模型：
    - node_type 不得与内置插件冲突，也不得与已有插件重复（冲突返回 409）；
    - code 提交时经沙箱静态校验（AST 白名单），违规直接拒绝（400）；
    - 提交后 review_status=pending_review，可通过 /custom/{id}/test 沙箱试跑；
    - 普通作者调用 /custom/{id}/publish 为「提交审核」，管理员审核通过后上架；
      管理员调用 publish 直接发布；
    - 自定义插件 execute 为同步函数，运行在受限沙箱（无 import/文件/网络，
      循环步数限制，5 秒超时）。
    """
    # 内置 node_type 冲突检查
    if registry.get(req.node_type) is not None:
        raise HTTPException(status_code=409, detail="node_type 与内置插件冲突，请更换")

    # 数据库重复检查
    existing = await db.execute(select(Plugin).where(Plugin.node_type == req.node_type))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="node_type 已被占用，请更换")

    # 代码沙箱静态校验：违规代码直接拒绝
    if req.code:
        from ..plugins.sandbox import SandboxError, validate_code

        try:
            validate_code(req.code)
        except SandboxError as exc:
            raise HTTPException(status_code=400, detail=f"插件代码未通过安全校验: {exc}")

    plugin = Plugin(
        name=req.name,
        version="1.0.0",
        description=req.description,
        author_id=user.id,
        node_type=req.node_type,
        code=req.code,
        config_schema=req.config_schema,
        is_builtin=False,
        is_published=False,  # 审核通过后才上架
        review_status="pending_review",
        install_count=0,
        tags=req.tags,
    )
    db.add(plugin)
    await db.commit()
    await db.refresh(plugin)

    # 通知管理员有新插件待审（旁路，失败不影响提交）
    try:
        from ..notifications import notify_admins

        await notify_admins(
            category="plugin",
            level="info",
            title=f"新插件待审核：{plugin.name}",
            content=f"开发者 {user.username} 提交了插件 {plugin.node_type}，请前往插件审核处理。",
            data={"plugin_id": plugin.id, "node_type": plugin.node_type, "action": "review"},
        )
    except Exception:
        pass

    return {
        "id": plugin.id,
        "node_type": plugin.node_type,
        "status": "pending_review",
        "message": "插件已提交并通过安全校验，沙箱试跑后将由管理员审核上架",
    }


class PluginTestRequest(BaseModel):
    """插件沙箱试跑请求"""

    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置")
    ctx: Dict[str, Any] = Field(default_factory=dict, description="模拟上下文（input_data 等）")


@router.post("/custom/{plugin_id}/test")
async def test_custom_plugin(
    plugin_id: int,
    req: PluginTestRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """在安全沙箱中试跑自定义插件（不发布、不影响线上）。仅插件作者可试跑。"""
    from ..plugins.sandbox import SandboxError, run_plugin_code

    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if plugin is None or plugin.author_id != user.id:
        raise HTTPException(status_code=404, detail="插件不存在")

    if not plugin.code:
        raise HTTPException(status_code=400, detail="该插件没有可执行代码")

    try:
        output, elapsed_ms = await run_plugin_code(plugin.code, req.config, req.ctx)
    except SandboxError as exc:
        return {"success": False, "error": str(exc)}
    return {"success": True, "output": output, "elapsed_ms": elapsed_ms}


@router.get("/custom/mine")
async def list_my_plugins(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """查看我提交的所有插件及其审核状态（作者面板）。"""
    result = await db.execute(
        select(Plugin)
        .where(Plugin.author_id == user.id)
        .order_by(Plugin.created_at.desc())
    )
    return [_plugin_dict(p) for p in result.scalars().all()]


@router.post("/custom/{plugin_id}/publish")
async def publish_custom_plugin(
    plugin_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """发布/提交审核自定义插件。

    - 管理员调用：沙箱编译校验通过后直接上架并注册到引擎；
    - 普通作者调用：将插件置为待审核（pending_review），通知管理员审核；
      审核通过后才会上架。
    """
    from ..plugins.sandbox import SandboxError, _compile_plugin

    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if plugin is None or plugin.author_id != user.id:
        raise HTTPException(status_code=404, detail="插件不存在")
    if not plugin.code:
        raise HTTPException(status_code=400, detail="插件缺少可执行代码，无法发布")

    # 发布前再次沙箱编译校验
    try:
        _compile_plugin(plugin.code)
    except SandboxError as exc:
        raise HTTPException(status_code=400, detail=f"安全校验未通过: {exc}")

    is_admin = user.role == UserRole.ADMIN

    if is_admin:
        # 管理员直接发布
        plugin.is_published = True
        plugin.review_status = "approved"
        plugin.reviewed_by = user.id
        from datetime import datetime

        plugin.reviewed_at = datetime.utcnow()
        await db.commit()
        try:
            _register_to_registry(plugin)
        except Exception:
            pass
        return {
            "id": plugin.id,
            "node_type": plugin.node_type,
            "status": "published",
            "message": "插件已发布上架，工作流引擎立即可用",
        }

    # 普通作者：提交审核
    plugin.review_status = "pending_review"
    plugin.is_published = False
    await db.commit()

    try:
        from ..notifications import notify_admins

        await notify_admins(
            category="plugin",
            level="info",
            title=f"插件提交审核：{plugin.name}",
            content=f"开发者 {user.username} 请求发布插件 {plugin.node_type}。",
            data={"plugin_id": plugin.id, "node_type": plugin.node_type, "action": "review"},
        )
    except Exception:
        pass

    return {
        "id": plugin.id,
        "node_type": plugin.node_type,
        "status": "pending_review",
        "message": "已提交审核，管理员通过后插件将自动上架",
    }


class PluginReviewRequest(BaseModel):
    """管理员审核请求"""

    comment: str = ""


@router.get("/admin/pending")
async def admin_list_pending(
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_session),
):
    """管理员：待审核插件列表。"""
    result = await db.execute(
        select(Plugin)
        .where(Plugin.review_status == "pending_review", Plugin.is_builtin == False)  # noqa: E712
        .order_by(Plugin.created_at.asc())
    )
    return [_plugin_dict(p) for p in result.scalars().all()]


@router.post("/admin/{plugin_id}/approve")
async def admin_approve_plugin(
    plugin_id: int,
    req: PluginReviewRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_session),
):
    """管理员：审核通过 → 上架并立即注册到引擎，通知作者。"""
    from datetime import datetime

    from ..plugins.sandbox import SandboxError, _compile_plugin

    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if plugin is None:
        raise HTTPException(status_code=404, detail="插件不存在")

    if not plugin.code:
        raise HTTPException(status_code=400, detail="插件缺少可执行代码，无法上架")
    try:
        _compile_plugin(plugin.code)
    except SandboxError as exc:
        raise HTTPException(status_code=400, detail=f"安全校验未通过: {exc}")

    plugin.is_published = True
    plugin.review_status = "approved"
    plugin.reviewed_by = admin.id
    plugin.reviewed_at = datetime.utcnow()
    plugin.review_comment = req.comment or None
    await db.commit()

    try:
        _register_to_registry(plugin)
    except Exception:
        pass

    try:
        from ..notifications import notify_user

        await notify_user(
            plugin.author_id,
            category="plugin",
            level="success",
            title=f"插件「{plugin.name}」审核通过",
            content=req.comment or "您的插件已通过审核并上架，工作流引擎立即可用。",
            data={"plugin_id": plugin.id, "node_type": plugin.node_type, "status": "approved"},
        )
    except Exception:
        pass

    return {"id": plugin.id, "node_type": plugin.node_type, "status": "approved"}


@router.post("/admin/{plugin_id}/reject")
async def admin_reject_plugin(
    plugin_id: int,
    req: PluginReviewRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_session),
):
    """管理员：审核驳回 → 通知作者并说明原因。"""
    from datetime import datetime

    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if plugin is None:
        raise HTTPException(status_code=404, detail="插件不存在")

    plugin.is_published = False
    plugin.review_status = "rejected"
    plugin.reviewed_by = admin.id
    plugin.reviewed_at = datetime.utcnow()
    plugin.review_comment = req.comment or "未通过审核"
    await db.commit()

    try:
        from ..notifications import notify_user

        await notify_user(
            plugin.author_id,
            category="plugin",
            level="warning",
            title=f"插件「{plugin.name}」审核未通过",
            content=req.comment or "您的插件未通过审核，可修改后重新提交。",
            data={"plugin_id": plugin.id, "node_type": plugin.node_type, "status": "rejected"},
        )
    except Exception:
        pass

    return {"id": plugin.id, "node_type": plugin.node_type, "status": "rejected"}


@router.get("/{node_type}/schema")
async def get_plugin_schema(node_type: str, db: AsyncSession = Depends(get_session)):
    """返回单个插件的配置 schema（前端渲染节点配置表单）"""
    builtin = registry.get(node_type)
    if builtin is not None:
        return {
            "node_type": node_type,
            "name": builtin.name,
            "config_schema": builtin.get_config_schema(),
        }

    result = await db.execute(
        select(Plugin).where(Plugin.node_type == node_type)
    )
    plugin = result.scalar_one_or_none()
    if plugin is not None:
        return {
            "node_type": node_type,
            "name": plugin.name,
            "config_schema": plugin.config_schema or {},
        }

    raise HTTPException(status_code=404, detail="插件不存在")
