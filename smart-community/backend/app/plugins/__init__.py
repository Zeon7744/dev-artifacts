"""
插件系统包

导入本包即自动注册全部内置插件到全局 registry；
同时导出 Plugin 模型，确保 Base.metadata 包含 plugins 表。
"""
from .base import PluginBase, PluginRegistry, registry
from . import builtins  # noqa: F401  - 导入即注册内置插件
from .models import Plugin

__all__ = ["PluginBase", "PluginRegistry", "registry", "Plugin"]
