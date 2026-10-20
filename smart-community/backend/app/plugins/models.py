"""
插件 ORM 模型 - 插件市场数据表

内置插件只存在于 PluginRegistry 中不落库；开发者提交的自定义插件
元数据（含代码文本）存入 plugins 表，MVP 阶段代码仅存储不执行。
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON

from ..models.database import Base


class Plugin(Base):
    """插件市场中的插件记录"""

    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    version = Column(String(20), default="1.0.0")
    description = Column(Text, default="")

    # 提交者（系统内置插件可为空）
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 自定义节点类型名，如 "plugin.my_sms"，全市场唯一
    node_type = Column(String(100), unique=True, nullable=False, index=True)

    # 插件源码（MVP 仅存储，不在服务端执行；执行需沙箱环境）
    code = Column(Text, nullable=True)

    # 配置表单 JSON Schema，结构与 PluginBase.get_config_schema 一致
    config_schema = Column(JSON, default=dict)

    # 是否内置插件 / 是否已发布上架
    is_builtin = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)

    # ===== 审核流字段（第四轮）=====
    # 审核状态：pending_review（待审核）/ approved（已通过）/ rejected（已驳回）
    # 内置插件与历史数据默认 approved
    review_status = Column(String(20), default="pending_review", nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)

    # 安装统计
    install_count = Column(Integer, default=0)

    # 标签列表
    tags = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 轻量迁移：为旧库 plugins 表补齐审核流列（SQLite ALTER TABLE ADD COLUMN）
# 新库由 create_all 直接建出，无需迁移；逐列添加，已存在则跳过。
_REVIEW_COLUMNS = {
    "review_status": "ALTER TABLE plugins ADD COLUMN review_status VARCHAR(20) NOT NULL DEFAULT 'pending_review'",
    "reviewed_by": "ALTER TABLE plugins ADD COLUMN reviewed_by INTEGER",
    "reviewed_at": "ALTER TABLE plugins ADD COLUMN reviewed_at DATETIME",
    "review_comment": "ALTER TABLE plugins ADD COLUMN review_comment TEXT",
    "updated_at": "ALTER TABLE plugins ADD COLUMN updated_at DATETIME",
}


async def migrate_plugin_review_columns(engine) -> None:
    """启动时调用：确保 plugins 表包含审核流字段。任何异常都不阻断启动。"""
    from sqlalchemy import text

    try:
        async with engine.begin() as conn:
            existing = {
                row[1]
                for row in (await conn.execute(text("PRAGMA table_info(plugins)"))).all()
            }
            if not existing:
                # 表还没建（首次启动），create_all 会处理
                return
            for col, ddl in _REVIEW_COLUMNS.items():
                if col not in existing:
                    await conn.execute(text(ddl))
            # 历史已发布插件回填为 approved（旧库没有审核流概念）
            await conn.execute(
                text("UPDATE plugins SET review_status='approved' WHERE is_published=1")
            )
    except Exception:
        import logging

        logging.getLogger(__name__).exception("plugins 审核字段迁移失败（不影响启动）")
