"""
编排器 - 多 Agent 协作工作流
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Agent 工作流编排器
    
    支持：
    - 串行执行
    - 并行执行
    - 条件分支
    - 错误处理
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.agents: Dict[str, BaseAgent] = {}
        self.workflow_history: List[Dict] = []
    
    def add_agent(self, agent: BaseAgent):
        """添加 Agent"""
        self.agents[agent.agent_id] = agent
        logger.info(f"添加 Agent: {agent.name} ({agent.agent_id})")
    
    def remove_agent(self, agent_id: str):
        """移除 Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"移除 Agent: {agent_id}")
    
    async def run_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        sequential: bool = True
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_name: 工作流名称
            input_data: 输入数据
            sequential: 是否串行执行（False则并行）
        
        Returns:
            工作流执行结果
        """
        workflow_id = uuid.uuid4().hex[:12]
        start_time = datetime.now()
        
        logger.info(f"开始工作流: {workflow_name} ({workflow_id})")
        
        # 构建执行计划
        plan = self._build_plan(workflow_name, input_data)
        
        # 执行
        if sequential:
            results = await self._execute_sequential(plan, input_data)
        else:
            results = await self._execute_parallel(plan, input_data)
        
        # 汇总
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "status": "completed",
            "duration_seconds": duration,
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "agents_executed": len(results),
            "results": results
        }
        
        self.workflow_history.append(summary)
        
        logger.info(f"工作流完成: {workflow_name} ({duration:.2f}s)")
        
        return summary
    
    def _build_plan(
        self, 
        workflow_name: str, 
        input_data: Dict
    ) -> List[Dict]:
        """构建执行计划"""
        plans = {
            "daily_report": [
                {"agent": "analyst", "action": "collect_and_analyze", "timeout": 60},
                {"agent": "reporter", "action": "generate_markdown", "depends": ["analyst"]},
            ],
            "weekly_summary": [
                {"agent": "analyst", "action": "weekly_analysis", "timeout": 120},
                {"agent": "reporter", "action": "generate_html", "depends": ["analyst"]},
            ],
            "alert_check": [
                {"agent": "watcher", "action": "check_all", "timeout": 30},
            ],
            "full_pipeline": [
                {"agent": "analyst", "action": "full_analysis", "timeout": 90},
                {"agent": "watcher", "action": "check_alerts", "timeout": 30},
                {"agent": "reporter", "action": "generate_report", "depends": ["analyst", "watcher"]},
            ]
        }
        
        return plans.get(workflow_name, plans.get("daily_report", []))
    
    async def _execute_sequential(
        self, 
        plan: List[Dict], 
        input_data: Dict
    ) -> Dict[str, Any]:
        """串行执行"""
        results = {}
        shared_context = {"input": input_data}
        
        for step in plan:
            agent_name = step["agent"]
            action = step["action"]
            
            agent = self.agents.get(agent_name)
            if not agent:
                logger.warning(f"Agent {agent_name} 未找到，跳过")
                continue
            
            try:
                logger.info(f"执行步骤: {agent_name}.{action}")
                
                step_input = {
                    **shared_context["input"],
                    "action": action,
                    "previous_results": results
                }
                
                result, context = await agent.run_with_context(step_input)
                results[agent_name] = result
                
                # 更新共享上下文
                shared_context[agent_name] = result
                
            except Exception as e:
                logger.error(f"步骤执行失败 {agent_name}: {e}")
                results[agent_name] = {"error": str(e)}
        
        return results
    
    async def _execute_parallel(
        self, 
        plan: List[Dict], 
        input_data: Dict
    ) -> Dict[str, Any]:
        """并行执行"""
        tasks = []
        
        for step in plan:
            agent_name = step["agent"]
            action = step["action"]
            
            agent = self.agents.get(agent_name)
            if not agent:
                logger.warning(f"Agent {agent_name} 未找到")
                continue
            
            task = asyncio.create_task(
                self._run_single_agent(agent, action, input_data)
            )
            tasks.append((agent_name, task))
        
        # 等待所有任务完成
        results = {}
        for agent_name, task in tasks:
            try:
                result, _ = await task
                results[agent_name] = result
            except Exception as e:
                logger.error(f"并行任务失败 {agent_name}: {e}")
                results[agent_name] = {"error": str(e)}
        
        return results
    
    async def _run_single_agent(
        self, 
        agent: BaseAgent, 
        action: str, 
        input_data: Dict
    ) -> tuple:
        """运行单个 Agent"""
        step_input = {
            **input_data,
            "action": action
        }
        return await agent.run_with_context(step_input)
    
    def get_workflow_stats(self) -> Dict:
        """获取工作流统计"""
        return {
            "total_workflows": len(self.workflow_history),
            "recent_workflows": self.workflow_history[-10:],
            "agents_registered": list(self.agents.keys())
        }
