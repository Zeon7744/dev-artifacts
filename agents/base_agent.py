"""
Agent 基类 - 所有 Agent 的抽象父类
"""
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Agent 运行上下文"""
    agent_id: str
    workflow_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "running"
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "workflow_id": self.workflow_id,
            "context": self.context,
            "metadata": self.metadata,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "error": self.error
        }


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        description: str = "",
        retry_count: int = 3,
        timeout: int = 300
    ):
        self.agent_id = agent_id or str(uuid.uuid4())[:8]
        self.name = name or self.__class__.__name__
        self.description = description
        self.retry_count = retry_count
        self.timeout = timeout
        self._state = "idle"
        self._history: List[Dict] = []
        
        logger.info(f"Agent 初始化: {self.name} ({self.agent_id})")
    
    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent 主执行方法
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果
        """
        pass
    
    async def run_with_context(
        self, 
        input_data: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> tuple[Dict[str, Any], AgentContext]:
        """
        带上下文的执行方法
        
        Returns:
            (结果, 上下文)
        """
        if context is None:
            context = AgentContext(
                agent_id=self.agent_id,
                workflow_id=uuid.uuid4().hex[:12]
            )
        
        context.status = "running"
        context.context = input_data
        
        try:
            logger.info(f"{self.name} 开始执行")
            
            # 执行前钩子
            await self._on_before_run(input_data, context)
            
            # 重试机制
            result = None
            for attempt in range(1, self.retry_count + 1):
                try:
                    result = await asyncio.wait_for(
                        self.run(input_data),
                        timeout=self.timeout
                    )
                    break
                except asyncio.TimeoutError:
                    logger.warning(f"{self.name} 执行超时 (attempt {attempt})")
                    if attempt == self.retry_count:
                        context.error = f"执行超时: {self.timeout}s"
                        context.status = "failed"
                        raise
                except Exception as e:
                    logger.error(f"{self.name} 执行失败 (attempt {attempt}): {e}")
                    if attempt == self.retry_count:
                        context.error = str(e)
                        context.status = "failed"
                        raise
            
            # 成功后处理
            if result:
                context.status = "completed"
                await self._on_after_run(result, context)
            
            return result, context
            
        except Exception as e:
            context.status = "failed"
            context.error = str(e)
            context.end_time = datetime.now()
            raise
    
    async def _on_before_run(self, input_data: Dict, context: AgentContext):
        """执行前钩子"""
        pass
    
    async def _on_after_run(self, result: Dict, context: AgentContext):
        """执行后钩子"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "state": self._state,
            "retry_count": self.retry_count,
            "timeout": self.timeout,
            "history_length": len(self._history)
        }
    
    def _log_event(self, event_type: str, data: Dict = None):
        """记录事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "agent_id": self.agent_id,
            "data": data or {}
        }
        self._history.append(event)
        logger.debug(f"{self.name} 事件: {event_type}")
    
    def clear_history(self):
        """清空历史记录"""
        self._history.clear()
        logger.info(f"{self.name} 历史记录已清空")
