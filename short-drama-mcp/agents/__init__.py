#!/usr/bin/env python3
"""短剧创作 Agent 系统

基于 LLM 的智能 Agent 集合，覆盖剧情生成、角色设计、对话生成、
剧本格式化、质量检查、趋势分析和 SEO 优化全流程。
"""

from .base import BaseAgent, AgentConfig
from .plot_agent import PlotAgent
from .character_agent import CharacterAgent
from .dialogue_agent import DialogueAgent
from .script_agent import ScriptAgent
from .quality_agent import QualityAgent
from .trend_agent import TrendAgent
from .seo_agent import SeoAgent

__version__ = "2.0.0"
__all__ = [
    "BaseAgent",
    "AgentConfig",
    "PlotAgent",
    "CharacterAgent",
    "DialogueAgent",
    "ScriptAgent",
    "QualityAgent",
    "TrendAgent",
    "SeoAgent",
]
