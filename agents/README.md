# Agent 工作流模块

## 架构
- `base_agent.py` - Agent基类
- `analyst_agent.py` - 分析师Agent（每日简报）
- `watcher_agent.py` - 监控Agent（异常预警）
- `reporter_agent.py` - 报告Agent（格式化输出）
- `orchestrator.py` - 编排器（多Agent协作）
- `workflow.py` - 工作流定义

## 设计模式
- 消息队列（Redis/AMQP或本地队列）
- 事件驱动架构
- 状态机管理
- 错误重试机制

## 使用示例
```python
from agents import Orchestrator

orch = Orchestrator()
orch.add_agents([AnalystAgent(), WatcherAgent()])
result = orch.run_workflow("daily_report")
```
