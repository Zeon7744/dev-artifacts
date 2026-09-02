"""
工作流引擎 - DAG 执行器
支持：触发器 → 条件分支 → AI处理 → 动作输出
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    TRIGGER = "trigger"       # 触发器：手动/定时/webhook/API
    ACTION = "action"         # 动作：HTTP请求/数据库操作/文件操作
    CONDITION = "condition"   # 条件：if/else分支
    AI = "ai"                 # AI节点：LLM调用/Agent调用
    TRANSFORM = "transform"   # 数据转换：映射/过滤/聚合
    DELAY = "delay"           # 延迟等待
    WEBHOOK = "webhook"       # Webhook发送
    NOTIFY = "notify"         # 通知：邮件/消息


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    node_id: str
    status: NodeStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class ExecutionContext:
    """执行上下文 - 在节点间传递数据"""
    workflow_id: int
    execution_id: int
    input_data: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def set_node_output(self, node_id: str, output: Dict[str, Any]):
        self.node_outputs[node_id] = output

    def get_node_output(self, node_id: str) -> Dict[str, Any]:
        return self.node_outputs.get(node_id, {})

    def set_variable(self, key: str, value: Any):
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def resolve_template(self, template: str) -> str:
        """解析模板变量 {{node_id.field}} 或 {{var.name}}"""
        import re
        def replacer(match):
            path = match.group(1)
            parts = path.split(".")
            if parts[0] == "var":
                val = self.variables
                for p in parts[1:]:
                    val = val.get(p, "") if isinstance(val, dict) else ""
                return str(val)
            elif parts[0] == "input":
                val = self.input_data
                for p in parts[1:]:
                    val = val.get(p, "") if isinstance(val, dict) else ""
                return str(val)
            else:
                val = self.node_outputs.get(parts[0], {})
                for p in parts[1:]:
                    val = val.get(p, "") if isinstance(val, dict) else ""
                return str(val)
        return re.sub(r"\{\{(.+?)\}\}", replacer, template)


class NodeExecutor:
    """节点执行器 - 处理各类节点"""

    def __init__(self):
        self._handlers = {
            NodeType.TRIGGER: self._exec_trigger,
            NodeType.ACTION: self._exec_action,
            NodeType.CONDITION: self._exec_condition,
            NodeType.AI: self._exec_ai,
            NodeType.TRANSFORM: self._exec_transform,
            NodeType.DELAY: self._exec_delay,
            NodeType.WEBHOOK: self._exec_webhook,
            NodeType.NOTIFY: self._exec_notify,
        }

    async def execute(self, node: Dict, ctx: ExecutionContext) -> NodeResult:
        node_type_str = node.get("type", "action")
        start = datetime.utcnow()

        # 插件节点：类型以 "plugin." 开头时路由到插件注册表
        if isinstance(node_type_str, str) and node_type_str.startswith("plugin."):
            try:
                output = await self._exec_plugin(node, ctx)
                elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
                return NodeResult(node_id=node["id"], status=NodeStatus.SUCCESS,
                                  output=output, duration_ms=elapsed)
            except Exception as e:
                elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
                logger.error(f"Plugin node {node['id']} failed: {e}")
                return NodeResult(node_id=node["id"], status=NodeStatus.FAILED,
                                  error=str(e), duration_ms=elapsed)

        node_type = NodeType(node_type_str)
        handler = self._handlers.get(node_type, self._exec_action)
        try:
            output = await handler(node, ctx)
            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
            return NodeResult(
                node_id=node["id"],
                status=NodeStatus.SUCCESS,
                output=output,
                duration_ms=elapsed,
            )
        except Exception as e:
            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
            logger.error(f"Node {node['id']} failed: {e}")
            return NodeResult(
                node_id=node["id"],
                status=NodeStatus.FAILED,
                error=str(e),
                duration_ms=elapsed,
            )

    async def _exec_plugin(self, node: Dict, ctx: ExecutionContext) -> Dict:
        """插件节点 - 从插件注册表查找并执行自定义插件"""
        from ..plugins.base import registry
        node_type = node.get("type", "")
        plugin = registry.get(node_type)
        if plugin is None:
            raise ValueError(f"未安装的插件节点类型: {node_type}")
        config = node.get("config", {})
        result = await plugin.execute(config, ctx)
        return result if isinstance(result, dict) else {"result": result}

    async def _exec_trigger(self, node: Dict, ctx: ExecutionContext) -> Dict:
        """触发器节点 - 传递输入数据"""
        config = node.get("config", {})
        trigger_type = config.get("trigger_type", "manual")
        return {
            "trigger_type": trigger_type,
            "data": ctx.input_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _exec_action(self, node: Dict, ctx: ExecutionContext) -> Dict:
        """动作节点 - HTTP请求/数据库/文件等"""
        config = node.get("config", {})
        action_type = config.get("action_type", "http")

        if action_type == "http":
            return await self._http_request(config, ctx)
        elif action_type == "database":
            return await self._db_action(config, ctx)
        elif action_type == "file":
            return await self._file_action(config, ctx)
        else:
            return {"status": "ok", "action_type": action_type}

    async def _http_request(self, config: Dict, ctx: ExecutionContext) -> Dict:
        """HTTP 请求"""
        import aiohttp
        method = config.get("method", "GET").upper()
        url = ctx.resolve_template(config.get("url", ""))
        headers = config.get("headers", {})
        body = config.get("body")
        if body and isinstance(body, str):
            body = ctx.resolve_template(body)

        timeout = aiohttp.ClientTimeout(total=config.get("timeout", 30))
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method, url, headers=headers, json=body if method != "GET" else None) as resp:
                text = await resp.text()
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    data = {"raw": text}
                return {"status_code": resp.status, "data": data}

    async def _db_action(self, config: Dict, ctx: ExecutionContext) -> Dict:
        """数据库操作（模拟）"""
        query = ctx.resolve_template(config.get("query", ""))
        return {"status": "ok", "query": query, "rows_affected": 0}

    async def _file_action(self, config: Dict, ctx: ExecutionContext) -> Dict:
        """文件操作"""
        action = config.get("file_action", "read")
        path = ctx.resolve_template(config.get("path", ""))
        return {"status": "ok", "action": action, "path": path}

    async def _exec_condition(self, node: Dict, ctx: ExecutionContext) -> Dict:
        """条件节点 - 评估表达式"""
        config = node.get("config", {})
        expression = ctx.resolve_template(config.get("expression", "true"))

        # 安全评估
        try:
            result = eval(expression, {"__builtins__": {}}, {
                "len": len, "int": int, "float": float, "str": str,
                "true": True, "false": False, "null": None,
                **ctx.variables,
            })
        except Exception:
            result = False

        return {"result": bool(result), "branch": "true" if result else "false"}

    async def _exec_ai(self, node: Dict, ctx: ExecutionContext) -> Dict:
        """AI 节点 - LLM 调用"""
        config = node.get("config", {})
        prompt = ctx.resolve_template(config.get("prompt", ""))
        provider = config.get("provider", "ollama")
        model = config.get("model", "llama3.2")
        max_tokens = config.get("max_tokens", 1000)

        # 调用 LLM
        try:
            from ..services.llm_service import LLMService
            llm = LLMService()
            response = await llm.generate(
                prompt=prompt,
                provider=provider,
                model=model,
                max_tokens=max_tokens,
            )
            return {"response": response, "provider": provider, "model": model}
        except ImportError:
            # LLM service not available, return mock
            return {
                "response": f"[AI Response to: {prompt[:100]}...]",
                "provider": provider,
                "model": model,
                "mock": True,
            }

    async def _exec_transform(self, node: Dict, ctx: ExecutionContext) -> Dict:
        """数据转换节点"""
        config = node.get("config", {})
        transform_type = config.get("transform_type", "map")
        source = ctx.resolve_template(config.get("source", "{{input}}"))

        try:
            data = json.loads(source) if isinstance(source, str) else source
        except (json.JSONDecodeError, TypeError):
            data = {"raw": source}

        if transform_type == "map":
            mapping = config.get("mapping", {})
            result = {}
            for key, expr in mapping.items():
                result[key] = ctx.resolve_template(str(expr))
            return result
        elif transform_type == "filter":
            field_name = config.get("field", "")
            value = config.get("value")
            if isinstance(data, list):
                return {"filtered": [d for d in data if d.get(field_name) == value]}
            return {"filtered": data}
        return {"data": data}

    async def _exec_delay(self, node: Dict, ctx: ExecutionContext) -> Dict:
        """延迟节点"""
        config = node.get("config", {})
        seconds = config.get("seconds", 1)
        await asyncio.sleep(min(seconds, 60))  # 最多等60秒
        return {"delayed": seconds}

    async def _exec_webhook(self, node: Dict, ctx: ExecutionContext) -> Dict:
        """Webhook 发送"""
        config = node.get("config", {})
        url = ctx.resolve_template(config.get("url", ""))
        payload = config.get("payload", {})
        if isinstance(payload, str):
            payload = json.loads(ctx.resolve_template(payload))
        # 复用HTTP请求
        return await self._http_request({
            "method": "POST",
            "url": url,
            "body": payload,
        }, ctx)

    async def _exec_notify(self, node: Dict, ctx: ExecutionContext) -> Dict:
        """通知节点"""
        config = node.get("config", {})
        channel = config.get("channel", "log")
        message = ctx.resolve_template(config.get("message", ""))
        logger.info(f"[NOTIFY:{channel}] {message}")
        return {"notified": True, "channel": channel, "message": message}


class WorkflowEngine:
    """工作流引擎 - DAG 编排执行"""

    def __init__(self):
        self.node_executor = NodeExecutor()

    async def run(
        self,
        workflow_id: int,
        execution_id: int,
        definition: Dict,
        input_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        执行工作流
        definition: {
            "nodes": [{"id": "n1", "type": "trigger", "config": {...}}, ...],
            "edges": [{"from": "n1", "to": "n2", "condition": "true"}, ...]
        }
        """
        nodes = {n["id"]: n for n in definition.get("nodes", [])}
        edges = definition.get("edges", [])
        ctx = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            input_data=input_data or {},
        )

        results: List[NodeResult] = []

        # 拓扑排序
        exec_order = self._topological_sort(nodes, edges)

        # 逐个执行
        for node_id in exec_order:
            node = nodes[node_id]

            # 检查前置条件
            if not self._check_edge_conditions(node_id, edges, results, ctx):
                results.append(NodeResult(
                    node_id=node_id,
                    status=NodeStatus.SKIPPED,
                    output={"reason": "condition not met"},
                ))
                continue

            # 执行节点
            result = await self.node_executor.execute(node, ctx)
            results.append(result)
            ctx.set_node_output(node_id, result.output)

            # 失败处理
            if result.status == NodeStatus.FAILED:
                ctx.errors.append(f"Node {node_id}: {result.error}")
                on_error = node.get("config", {}).get("on_error", "stop")
                if on_error == "stop":
                    break
                elif on_error == "skip":
                    continue

        # 汇总
        success = all(r.status in (NodeStatus.SUCCESS, NodeStatus.SKIPPED) for r in results)
        return {
            "status": "success" if success else "failed",
            "node_results": [
                {
                    "node_id": r.node_id,
                    "status": r.status.value,
                    "output": r.output,
                    "error": r.error,
                    "duration_ms": r.duration_ms,
                }
                for r in results
            ],
            "errors": ctx.errors,
            "final_output": ctx.node_outputs,
        }

    def _topological_sort(self, nodes: Dict, edges: List[Dict]) -> List[str]:
        """Kahn's algorithm for topological sort"""
        in_degree = {nid: 0 for nid in nodes}
        adj = {nid: [] for nid in nodes}

        for edge in edges:
            src, dst = edge.get("from"), edge.get("to")
            if src in adj and dst in in_degree:
                adj[src].append(dst)
                in_degree[dst] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 如果有环，追加剩余节点
        remaining = [nid for nid in nodes if nid not in order]
        order.extend(remaining)
        return order

    def _check_edge_conditions(
        self,
        target_node_id: str,
        edges: List[Dict],
        results: List[NodeResult],
        ctx: ExecutionContext,
    ) -> bool:
        """检查到达目标节点的所有边条件"""
        incoming = [e for e in edges if e.get("to") == target_node_id]
        if not incoming:
            return True  # 没有入边 = 起始节点

        for edge in incoming:
            src_id = edge.get("from")
            condition = edge.get("condition")

            # 找源节点结果
            src_result = next((r for r in results if r.node_id == src_id), None)
            if not src_result:
                continue

            if src_result.status == NodeStatus.FAILED:
                return False

            if condition:
                resolved = ctx.resolve_template(condition)
                try:
                    if not eval(resolved, {"__builtins__": {}}, {"true": True, "false": False}):
                        return False
                except Exception:
                    return False

        return True
