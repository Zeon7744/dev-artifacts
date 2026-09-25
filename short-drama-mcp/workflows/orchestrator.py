#!/usr/bin/env python3
"""工作流编排器

串联所有 Agent，管理上下文，协调执行顺序，汇总结果。
支持多种工作流模式：完整流程 / 单步执行 / 增量续写。
"""

import json
import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.base import BaseAgent, AgentConfig
from agents.plot_agent import PlotAgent
from agents.character_agent import CharacterAgent
from agents.dialogue_agent import DialogueAgent
from agents.script_agent import ScriptAgent
from agents.quality_agent import QualityAgent
from agents.trend_agent import TrendAgent
from agents.seo_agent import SeoAgent


@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str
    agent_name: str
    method: str
    args: Dict = field(default_factory=dict)
    status: str = "pending"  # pending / running / completed / failed / skipped
    result: Optional[Dict] = None
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_id: str
    status: str  # success / partial / failed
    steps: List[WorkflowStep] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    outputs: Dict = field(default_factory=dict)
    total_duration: float = 0.0
    started_at: str = ""
    finished_at: str = ""
    errors: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "total_duration": round(self.total_duration, 2),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": [
                {
                    "name": s.name,
                    "agent": s.agent_name,
                    "status": s.status,
                    "duration": round(s.duration, 2),
                    "error": s.error,
                }
                for s in self.steps
            ],
            "outputs_summary": {k: _summarize(v) for k, v in self.outputs.items()},
            "errors": self.errors,
        }


def _summarize(val: Any, max_len: int = 200) -> str:
    """值的简要摘要"""
    s = json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else val
    return s[:max_len] + "..." if len(s) > max_len else s


class WorkflowOrchestrator:
    """工作流编排器
    
    使用方式：
        config = AgentConfig(api_key="...", model="gpt-4o-mini")
        orch = WorkflowOrchestrator(config)
        result = orch.run_full_workflow(
            novel_input="小说内容...",
            genre="都市甜宠",
            episode_count=8,
        )
    """

    # 标准工作流步骤定义
    DEFAULT_STEPS = [
        ("trend_analysis", "TrendAgent", "analyze_trends"),
        ("plot_generation", "PlotAgent", "generate_plot"),
        ("character_design", "CharacterAgent", "create_characters"),
        ("dialogue_generation", "DialogueAgent", "generate_dialogue"),
        ("script_formatting", "ScriptAgent", "format_script"),
        ("quality_check", "QualityAgent", "check_quality"),
        ("seo_optimization", "SeoAgent", "optimize_seo"),
    ]

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self._agents: Dict[str, BaseAgent] = {}
        self._init_agents()
        self._logs: List[str] = []

    def _init_agents(self):
        """初始化所有 Agent"""
        self._agents["PlotAgent"] = PlotAgent(self.config)
        self._agents["CharacterAgent"] = CharacterAgent(self.config)
        self._agents["DialogueAgent"] = DialogueAgent(self.config)
        self._agents["ScriptAgent"] = ScriptAgent(self.config)
        self._agents["QualityAgent"] = QualityAgent(self.config)
        self._agents["TrendAgent"] = TrendAgent(self.config)
        self._agents["SeoAgent"] = SeoAgent(self.config)

    def get_agent(self, name: str) -> BaseAgent:
        """获取指定 Agent"""
        if name not in self._agents:
            raise ValueError(f"未知 Agent: {name}。可用: {list(self._agents.keys())}")
        return self._agents[name]

    def run_full_workflow(
        self,
        novel_input: str,
        genre: str = "都市甜宠",
        episode_count: int = 8,
        skip_steps: Optional[List[str]] = None,
    ) -> WorkflowResult:
        """执行完整工作流
        
        流程: 趋势分析 → 剧情生成 → 角色设计 → 对话生成 → 剧本格式化 → 质量检查 → SEO 优化
        
        Args:
            novel_input: 小说原文 / 大纲 / 故事梗概
            genre: 题材类型
            episode_count: 目标集数
            skip_steps: 要跳过的步骤名列表
        
        Returns:
            WorkflowResult
        """
        wf_id = f"wf_{int(time.time())}"
        result = WorkflowResult(
            workflow_id=wf_id,
            status="running",
            started_at=datetime.now().isoformat(),
        )

        skip = set(skip_steps or [])
        self._log(f"[Orchestrator] 启动工作流 {wf_id}: {genre} x {episode_count}集")

        # ── 上下文容器 ──
        ctx: Dict[str, Any] = {
            "novel_input": novel_input,
            "genre": genre,
            "episode_count": episode_count,
        }

        # ── 步骤执行 ──
        step_configs = self._build_step_configs(ctx, skip)

        for step_cfg in step_configs:
            step = WorkflowStep(**step_cfg)
            result.steps.append(step)

            if step.name in skip:
                step.status = "skipped"
                self._log(f"[Orchestrator] 跳过: {step.name}")
                continue

            self._log(f"[Orchestrator] 执行: {step.name}")
            step.status = "running"
            t0 = time.time()

            try:
                step.result = self._execute_step(step, ctx)
                step.status = "completed"
                step.duration = time.time() - t0
                self._log(f"[Orchestrator] 完成: {step.name} ({step.duration:.1f}s)")
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                step.duration = time.time() - t0
                result.errors.append(f"{step.name}: {e}")
                self._log(f"[Orchestrator] 失败: {step.name}: {e}")
                # 关键步骤失败则中止
                if step.name in ("plot_generation", "character_design"):
                    self._log("[Orchestrator] 关键步骤失败，中止工作流")
                    break

        # ── 汇总 ──
        result.context = ctx
        result.outputs = {
            "trend_analysis": ctx.get("trend_analysis"),
            "plot": ctx.get("plot"),
            "characters": ctx.get("characters"),
            "dialogues": ctx.get("dialogues"),
            "script": ctx.get("script"),
            "quality_report": ctx.get("quality_report"),
            "seo": ctx.get("seo"),
        }
        # 清除 None
        result.outputs = {k: v for k, v in result.outputs.items() if v is not None}

        # 判断整体状态
        failed = [s for s in result.steps if s.status == "failed"]
        completed = [s for s in result.steps if s.status == "completed"]
        if not failed:
            result.status = "success"
        elif completed:
            result.status = "partial"
        else:
            result.status = "failed"

        result.finished_at = datetime.now().isoformat()
        result.total_duration = time.time() - time.mktime(
            datetime.fromisoformat(result.started_at).timetuple()
        )
        result.logs = list(self._logs)

        self._log(f"[Orchestrator] 工作流结束: {result.status}")
        return result

    def run_step(
        self,
        step_name: str,
        context: Dict,
    ) -> Dict:
        """执行单个步骤
        
        Args:
            step_name: 步骤名
            context: 上下文 dict
        
        Returns:
            步骤执行结果
        """
        step_map = {
            "trend_analysis": self._step_trend,
            "plot_generation": self._step_plot,
            "character_design": self._step_character,
            "dialogue_generation": self._step_dialogue,
            "script_formatting": self._step_script,
            "quality_check": self._step_quality,
            "seo_optimization": self._step_seo,
        }
        if step_name not in step_map:
            raise ValueError(f"未知步骤: {step_name}。可用: {list(step_map.keys())}")
        return step_map[step_name](context)

    def _build_step_configs(self, ctx: Dict, skip: set) -> List[Dict]:
        """构建步骤配置列表"""
        all_steps = [
            {"name": "trend_analysis", "agent_name": "TrendAgent", "method": "analyze_trends"},
            {"name": "plot_generation", "agent_name": "PlotAgent", "method": "generate_plot"},
            {"name": "character_design", "agent_name": "CharacterAgent", "method": "create_characters"},
            {"name": "dialogue_generation", "agent_name": "DialogueAgent", "method": "generate_dialogue"},
            {"name": "script_formatting", "agent_name": "ScriptAgent", "method": "format_script"},
            {"name": "quality_check", "agent_name": "QualityAgent", "method": "check_quality"},
            {"name": "seo_optimization", "agent_name": "SeoAgent", "method": "optimize_seo"},
        ]
        return all_steps

    def _execute_step(self, step: WorkflowStep, ctx: Dict) -> Dict:
        """执行单个步骤并更新上下文"""
        method_map = {
            "trend_analysis": self._step_trend,
            "plot_generation": self._step_plot,
            "character_design": self._step_character,
            "dialogue_generation": self._step_dialogue,
            "script_formatting": self._step_script,
            "quality_check": self._step_quality,
            "seo_optimization": self._step_seo,
        }
        return method_map[step.name](ctx)

    # ── 各步骤实现 ──────────────────────────────────────────

    def _step_trend(self, ctx: Dict) -> Dict:
        agent: TrendAgent = self._agents["TrendAgent"]
        result = agent.analyze_trends(
            platform=ctx.get("platform", "红果短剧"),
            genre=ctx["genre"],
        )
        ctx["trend_analysis"] = result
        return result

    def _step_plot(self, ctx: Dict) -> Dict:
        agent: PlotAgent = self._agents["PlotAgent"]
        result = agent.generate_plot(
            novel_input=ctx["novel_input"],
            genre=ctx["genre"],
            episode_count=ctx["episode_count"],
        )
        ctx["plot"] = result
        return result

    def _step_character(self, ctx: Dict) -> Dict:
        agent: CharacterAgent = self._agents["CharacterAgent"]
        story_summary = ctx.get("plot", {}).get("logline", ctx["novel_input"][:500])
        result = agent.create_characters(
            story_summary=story_summary,
            genre=ctx["genre"],
        )
        ctx["characters"] = result
        return result

    def _step_dialogue(self, ctx: Dict) -> Dict:
        agent: DialogueAgent = self._agents["DialogueAgent"]
        plot = ctx.get("plot", {})
        characters = ctx.get("characters", {}).get("characters", [])

        # 取第一集的关键场景生成对话
        episodes = plot.get("episodes", [])
        if not episodes:
            self._log("[Orchestrator] 无剧情数据，跳过对话生成")
            return {"status": "skipped", "reason": "无剧情数据"}

        ep1 = episodes[0]
        scenes = []
        for i, scene_desc in enumerate(ep1.get("key_scenes", ["开场"])):
            scenes.append({
                "location": scene_desc if isinstance(scene_desc, str) else str(scene_desc),
                "time": "日" if i % 2 == 0 else "夜",
                "description": scene_desc,
                "events": ep1.get("conflicts", []),
            })

        if not scenes:
            scenes = [{"location": "主场景", "description": ep1.get("summary", "")}]

        results = []
        for scene in scenes:
            r = agent.generate_dialogue(
                scene=scene,
                characters=characters,
                mood="紧张" if ep1.get("conflicts") else "平静",
                scene_goal=ep1.get("summary", "推动剧情"),
            )
            results.append(r)

        ctx["dialogues"] = results
        return {"scenes_count": len(results), "dialogues": results}

    def _step_script(self, ctx: Dict) -> Dict:
        agent: ScriptAgent = self._agents["ScriptAgent"]

        # 将剧情 + 对话组合成原始内容
        plot = ctx.get("plot", {})
        dialogues = ctx.get("dialogues", [])

        content_parts = [f"# {plot.get('title', '未命名')}\n"]
        for ep in plot.get("episodes", []):
            content_parts.append(f"## 第{ep.get('episode', 1)}集：{ep.get('title', '')}\n")
            content_parts.append(f"{ep.get('summary', '')}\n")

        # 追加对话内容
        for d in dialogues:
            for line in d.get("dialogue_lines", []):
                char = line.get("character", "")
                emotion = line.get("emotion", "")
                dialogue = line.get("dialogue", "")
                action = line.get("action", "")
                if action:
                    content_parts.append(f"（{action}）\n")
                content_parts.append(f'{char}【{emotion}】："{dialogue}"\n')

        raw_content = "\n".join(content_parts)

        result = agent.format_script(
            content=raw_content,
            format_type="standard",
            episode_count=ctx["episode_count"],
        )
        ctx["script"] = result
        return result

    def _step_quality(self, ctx: Dict) -> Dict:
        agent: QualityAgent = self._agents["QualityAgent"]
        script = ctx.get("script", {})
        content = script.get("formatted_text", "")

        if not content:
            self._log("[Orchestrator] 无剧本内容，使用快速检查")
            return {"status": "skipped", "reason": "无剧本内容"}

        result = agent.check_quality(content)
        ctx["quality_report"] = result
        return result

    def _step_seo(self, ctx: Dict) -> Dict:
        agent: SeoAgent = self._agents["SeoAgent"]
        plot = ctx.get("plot", {})
        title = plot.get("title", "")
        logline = plot.get("logline", "")

        result = agent.optimize_seo(
            title=title,
            description=logline,
            genre=ctx["genre"],
        )
        ctx["seo"] = result
        return result

    def _log(self, msg: str):
        self._logs.append(msg)
        print(msg)


# ── 快捷函数 ──────────────────────────────────────────────────

def quick_workflow(
    novel_input: str,
    genre: str = "都市甜宠",
    episode_count: int = 8,
    api_key: str = "",
    model: str = "gpt-4o-mini",
) -> Dict:
    """一键执行完整工作流
    
    Args:
        novel_input: 小说 / 大纲内容
        genre: 题材
        episode_count: 集数
        api_key: API Key
        model: 模型名
    
    Returns:
        工作流结果 dict
    """
    config = AgentConfig(api_key=api_key or "", model=model)
    orch = WorkflowOrchestrator(config)
    result = orch.run_full_workflow(novel_input, genre, episode_count)
    return result.to_dict()


if __name__ == "__main__":
    print("WorkflowOrchestrator 模块加载成功")
    print("可用步骤:", [s[0] for s in WorkflowOrchestrator.DEFAULT_STEPS])
