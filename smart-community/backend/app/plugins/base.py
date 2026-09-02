"""
插件系统 - 基类与注册器

插件以自定义工作流节点的形式存在：每个插件声明一个唯一的 node_type
（如 "plugin.text_format"），工作流引擎执行到该类型节点时，可通过
PluginRegistry 找到对应插件并调用 execute。
"""
from typing import Any, Dict, List, Optional


class PluginBase:
    """插件基类，所有内置/第三方插件均继承此类。

    子类需设置类属性 name/version/description/node_type，
    并实现 execute()；配置项通过 get_config_schema() 声明，
    供前端动态渲染配置表单。
    """

    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    node_type: str = ""

    async def execute(self, config: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
        """执行插件逻辑。

        :param config: 节点配置（与 get_config_schema 描述的字段对应）
        :param ctx: 工作流执行上下文 ExecutionContext，
                    提供 resolve_template / set_variable / node_outputs / input_data
        :return: 节点输出字典，会写入 ctx.node_outputs 供下游节点引用
        """
        raise NotImplementedError("插件必须实现 execute 方法")

    def get_config_schema(self) -> Dict[str, Any]:
        """返回配置项的 JSON Schema，用于前端动态表单。

        子类应覆盖此方法，返回形如
        {"fields": [{"key": "operation", "label": "操作", "type": "select",
                      "options": [...], "default": "...", "required": True}]}
        的结构。
        """
        return {"fields": []}

    def metadata(self) -> Dict[str, Any]:
        """返回插件元数据（注册/列表接口使用）。"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "node_type": self.node_type,
            "config_schema": self.get_config_schema(),
            "is_builtin": True,
        }


class PluginRegistry:
    """插件注册器（单例），管理 node_type -> 插件实例的映射。"""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginBase] = {}

    def register(self, plugin: PluginBase) -> None:
        """注册插件。node_type 重复时后者覆盖前者并记录警告。"""
        if not plugin.node_type:
            raise ValueError(f"插件 {plugin.__class__.__name__} 缺少 node_type")
        if plugin.node_type in self._plugins:
            import logging
            logging.getLogger(__name__).warning(
                "插件 node_type %s 已注册（%s），被 %s 覆盖",
                plugin.node_type,
                self._plugins[plugin.node_type].__class__.__name__,
                plugin.__class__.__name__,
            )
        self._plugins[plugin.node_type] = plugin

    def get(self, node_type: str) -> Optional[PluginBase]:
        """按 node_type 获取插件实例，未注册返回 None。"""
        return self._plugins.get(node_type)

    def list_all(self) -> List[Dict[str, Any]]:
        """返回所有已注册插件的元数据列表。"""
        return [p.metadata() for p in self._plugins.values()]

    def node_types(self) -> List[str]:
        """返回所有已注册的 node_type（工作流编辑器节点面板用）。"""
        return list(self._plugins.keys())


# 模块级全局注册器单例
registry = PluginRegistry()
