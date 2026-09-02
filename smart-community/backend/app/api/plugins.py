"""插件市场 API - 插件列表、安装、自定义插件提交、配置 schema 查询"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_session
from ..core.auth import get_current_user
from ..models.database import User
# 导入 plugins 包：触发内置插件注册，并确保 plugins 表已注册到 Base.metadata
from ..plugins import registry
from ..plugins.models import Plugin

router = APIRouter()


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

    安全说明（MVP）：
    - node_type 不得与内置插件冲突，也不得与已有插件重复（冲突返回 409）；
    - code 字段仅做持久化存储，服务端不会执行；
      后续版本需经审核 + 沙箱运行环境后才允许注册执行；
    - 提交后 is_published=False，管理员审核发布后才会出现在插件市场。
    """
    # 内置 node_type 冲突检查
    if registry.get(req.node_type) is not None:
        raise HTTPException(status_code=409, detail="node_type 与内置插件冲突，请更换")

    # 数据库重复检查
    existing = await db.execute(select(Plugin).where(Plugin.node_type == req.node_type))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="node_type 已被占用，请更换")

    plugin = Plugin(
        name=req.name,
        version="1.0.0",
        description=req.description,
        author_id=user.id,
        node_type=req.node_type,
        code=req.code,
        config_schema=req.config_schema,
        is_builtin=False,
        is_published=False,  # MVP：提交后待审核，不直接上架
        install_count=0,
        tags=req.tags,
    )
    db.add(plugin)
    await db.commit()
    await db.refresh(plugin)
    return {
        "id": plugin.id,
        "node_type": plugin.node_type,
        "status": "pending_review",
        "message": "插件元数据已提交，code 仅存储不会执行；待管理员审核发布后上架市场",
    }


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
