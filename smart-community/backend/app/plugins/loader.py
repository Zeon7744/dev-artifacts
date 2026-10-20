"""
自定义插件加载器

启动时从数据库加载所有 is_published=True 且含 code 的自定义插件，
通过沙箱包装后注册到全局 registry，使工作流引擎可以执行 plugin.* 节点。

加载策略：逐条沙箱编译校验，任何一条失败只记日志并跳过，不影响其他插件。
"""
import logging

from sqlalchemy import select

from ..core.database import async_session
from .base import registry
from .models import Plugin
from .sandbox import CustomSandboxPlugin, SandboxError, _compile_plugin

logger = logging.getLogger(__name__)


async def load_published_plugins() -> int:
    """加载并注册所有已发布的自定义插件，返回成功注册数量。"""
    async with async_session() as db:
        result = await db.execute(
            select(Plugin).where(
                Plugin.is_published.is_(True),
                Plugin.code.isnot(None),
            )
        )
        records = result.scalars().all()

    loaded = 0
    for record in records:
        try:
            # 编译期校验：不合规代码直接跳过，不注册
            _compile_plugin(record.code)
            registry.register(CustomSandboxPlugin(record))
            loaded += 1
            logger.info("自定义插件已加载: %s (%s)", record.node_type, record.name)
        except SandboxError as exc:
            logger.warning(
                "自定义插件 %s 沙箱校验失败，跳过: %s", record.node_type, exc
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("自定义插件 %s 加载异常，跳过: %s", record.node_type, exc)
    return loaded
