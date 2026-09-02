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

    # 安装统计
    install_count = Column(Integer, default=0)

    # 标签列表
    tags = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
