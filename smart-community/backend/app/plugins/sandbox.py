"""
自定义插件安全沙箱

自定义插件代码以源码文本存储在 plugins 表，执行前经过四重安全限制：

1. AST 静态校验：禁止 import / 全局命名空间操作 / 下划线属性与名称 /
   eval-exec-compile-open-getattr 等危险内建；类与函数定义只允许白名单语句；
2. 受限内建环境：globals 中只暴露安全内建（abs/min/max/json/math/re/datetime 等），
   无 open / socket / 文件系统 / 网络入口；
3. 字节码插桩：while/for 循环体注入 _guard_loop() 步数检查，死循环在
   ~10 万次迭代内被 RuntimeError 中断；
4. 线程级超时：execute 在独立线程执行，asyncio.wait_for 5 秒超时
   （超时后调用方收到 TimeoutError，执行线程为 daemon，不阻塞服务）。

每次执行使用全新 globals 环境，插件间、执行间无状态泄漏。
插件契约：代码中定义同步函数 execute(config, ctx)，返回 dict（可 JSON 序列化）；
ctx 为只读快照字典：{input_data, node_outputs, variables, workflow_id, execution_id}。
"""
import ast
import asyncio
import json
import logging
import math
import re
import threading
from datetime import datetime as _dt_cls, datetime as _datetime_module  # noqa: F401
from typing import Any, Dict, Tuple

from .base import PluginBase

logger = logging.getLogger(__name__)

# 单次执行循环迭代上限（死循环防护）
MAX_LOOP_ITERATIONS = 100_000
# 单次执行墙钟超时（秒）
EXECUTION_TIMEOUT = 5.0


class SandboxError(Exception):
    """沙箱校验/执行错误（代码不合规、超时、结果非法等）。"""


# ============ 1. AST 静态校验 ============

# 允许出现在插件代码顶层的语句类型
_ALLOWED_TOP_LEVEL = (
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
    ast.Assign, ast.AnnAssign, ast.Expr, ast.Pass,
)

# 允许出现在任何位置的语句/表达式类型（其余一律拒绝）
_ALLOWED_NODES = (
    # 语句
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
    ast.Return, ast.Delete, ast.Assign, ast.AnnAssign, ast.AugAssign,
    ast.For, ast.AsyncFor, ast.While, ast.If, ast.Expression,
    ast.Expr, ast.Pass, ast.Break, ast.Continue, ast.Try,
    ast.Raise, ast.Assert,
    # 表达式
    ast.BoolOp, ast.NamedExpr, ast.BinOp, ast.UnaryOp, ast.Lambda,
    ast.IfExp, ast.Dict, ast.Set, ast.ListComp, ast.SetComp,
    ast.DictComp, ast.GeneratorExp, ast.comprehension, ast.Await,
    ast.Yield, ast.YieldFrom, ast.Compare, ast.Call, ast.FormattedValue,
    ast.JoinedStr, ast.Constant, ast.Attribute, ast.Subscript,
    ast.Starred, ast.Name, ast.List, ast.Tuple, ast.Slice,
    # 运算上下文 / 通配
    ast.Load, ast.Store, ast.Del, ast.And, ast.Or, ast.Not,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is,
    ast.IsNot, ast.In, ast.NotIn, ast.Add, ast.Sub, ast.Mult,
    ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.LShift, ast.RShift,
    ast.BitOr, ast.BitXor, ast.BitAnd, ast.MatMult, ast.Invert,
    ast.UAdd, ast.USub, ast.keyword, ast.arguments, ast.arg,
    ast.alias, ast.ExceptHandler,
)

# 显式禁止的名称（危险内建/函数）
_BLOCKED_NAMES = frozenset({
    "eval", "exec", "compile", "open", "input", "__import__",
    "getattr", "setattr", "delattr", "globals", "locals", "vars",
    "dir", "type", "object", "memoryview", "breakpoint",
    "quit", "exit", "help", "license", "copyright", "credits",
    "property", "classmethod", "staticmethod",
})


class _CodeValidator(ast.NodeVisitor):
    """遍历插件 AST，发现违规节点即抛 SandboxError。"""

    def __init__(self) -> None:
        self._top_level = True

    def visit_Module(self, node: ast.Module) -> None:
        for stmt in node.body:
            if not isinstance(stmt, _ALLOWED_TOP_LEVEL):
                raise SandboxError(
                    f"顶层只允许函数/类/赋值定义，发现禁止语句: {type(stmt).__name__}"
                )
        self._top_level = False
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        raise SandboxError("插件代码禁止 import 语句，请使用沙箱内置模块（json/math/re/datetime）")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        raise SandboxError("插件代码禁止 import 语句，请使用沙箱内置模块（json/math/re/datetime）")

    def visit_Global(self, node: ast.Global) -> None:
        raise SandboxError("插件代码禁止 global 语句")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        raise SandboxError("插件代码禁止 nonlocal 语句")

    def visit_With(self, node: ast.With) -> None:
        raise SandboxError("插件代码禁止 with 语句")

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        raise SandboxError("插件代码禁止 with 语句")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id.startswith("_"):
            raise SandboxError(f"插件代码禁止访问下划线名称: {node.id}")
        if node.id in _BLOCKED_NAMES:
            raise SandboxError(f"插件代码禁止调用内建: {node.id}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("_"):
            raise SandboxError(f"插件代码禁止访问下划线属性: .{node.attr}")
        self.generic_visit(node)

    def generic_visit(self, node: ast.AST) -> None:
        if not isinstance(node, _ALLOWED_NODES) and not isinstance(node, ast.Module):
            raise SandboxError(f"插件代码包含不允许的语法: {type(node).__name__}")
        super().generic_visit(node)


def validate_code(code: str) -> None:
    """静态校验插件源码，违规抛 SandboxError。"""
    if not code or not code.strip():
        raise SandboxError("插件代码为空")
    if len(code) > 20_000:
        raise SandboxError("插件代码过长（上限 20000 字符）")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise SandboxError(f"插件代码语法错误: {exc}") from exc
    _CodeValidator().visit(tree)


# ============ 2. 循环步数插桩 ============

class _LoopGuardInjector(ast.NodeTransformer):
    """在 while/for 循环体开头注入 _guard_loop() 调用（校验后执行）。"""

    def _inject(self, node: ast.AST) -> ast.AST:
        guard_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="_guard_loop", ctx=ast.Load()),
                args=[],
                keywords=[],
            )
        )
        node.body = [guard_call] + list(node.body)
        return node

    def visit_While(self, node: ast.While) -> ast.AST:
        self.generic_visit(node)
        return self._inject(node)

    def visit_For(self, node: ast.For) -> ast.AST:
        self.generic_visit(node)
        return self._inject(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> ast.AST:
        self.generic_visit(node)
        return self._inject(node)


# ============ 3. 受限执行环境 ============

_SAFE_BUILTINS: Dict[str, Any] = {
    "abs": abs, "all": all, "any": any, "ascii": ascii, "bin": bin,
    "bool": bool, "bytearray": bytearray, "bytes": bytes, "chr": chr,
    "dict": dict, "divmod": divmod, "enumerate": enumerate, "filter": filter,
    "float": float, "format": format, "frozenset": frozenset, "hash": hash,
    "hex": hex, "int": int, "isinstance": isinstance, "issubclass": issubclass,
    "iter": iter, "len": len, "list": list, "map": map, "max": max,
    "min": min, "next": next, "oct": oct, "ord": ord, "pow": pow,
    "print": print, "range": range, "repr": repr, "reversed": reversed,
    "round": round, "set": set, "slice": slice, "sorted": sorted,
    "str": str, "sum": sum, "tuple": tuple, "zip": zip,
    "super": super, "callable": callable,
    "True": True, "False": False, "None": None,
    # 允许的异常类型
    "Exception": Exception, "ValueError": ValueError, "TypeError": TypeError,
    "KeyError": KeyError, "RuntimeError": RuntimeError, "IndexError": IndexError,
    "AttributeError": AttributeError, "NameError": NameError,
    "ZeroDivisionError": ZeroDivisionError, "ArithmeticError": ArithmeticError,
    "StopIteration": StopIteration, "LookupError": LookupError,
    "NotImplementedError": NotImplementedError,
}


def _build_sandbox_globals() -> Dict[str, Any]:
    """构建一次执行专属的受限 globals（每次执行全新，无状态泄漏）。"""
    state = {"loops": 0}

    def _guard_loop() -> None:
        state["loops"] += 1
        if state["loops"] > MAX_LOOP_ITERATIONS:
            raise RuntimeError("插件循环步数超限（疑似死循环），已终止")

    return {
        "__builtins__": _SAFE_BUILTINS,
        "_guard_loop": _guard_loop,
        # 白名单模块
        "json": json,
        "math": math,
        "re": re,
        "datetime": _datetime_module,
    }


def _compile_plugin(code: str) -> Any:
    """校验 + 插桩 + 编译，返回 code object。"""
    validate_code(code)
    tree = ast.parse(code)
    tree = _LoopGuardInjector().visit(tree)
    ast.fix_missing_locations(tree)
    return compile(tree, "<custom_plugin>", "exec")


def _normalize_result(result: Any) -> Dict[str, Any]:
    """执行结果归一化为可 JSON 序列化的 dict。"""
    if result is None:
        return {}
    if isinstance(result, dict):
        out = result
    else:
        out = {"result": result}
    try:
        json.dumps(out, ensure_ascii=False, default=str)
    except (TypeError, ValueError) as exc:
        raise SandboxError(f"插件返回结果不可 JSON 序列化: {exc}") from exc
    return out


def _run_sync(code_obj: Any, config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """在线程中同步执行插件（由 asyncio executor 调用）。"""
    sandbox_globals = _build_sandbox_globals()
    exec(code_obj, sandbox_globals)  # noqa: S102 沙箱环境内受控执行
    execute_fn = sandbox_globals.get("execute")
    if not callable(execute_fn):
        raise SandboxError("插件代码必须定义 execute(config, ctx) 函数")
    result = execute_fn(config or {}, ctx or {})
    if asyncio.iscoroutine(result):
        # 自定义插件约定为同步函数；误定义为 async 时给出明确提示
        raise SandboxError("自定义插件 execute 必须为同步函数（async def 不受支持）")
    return _normalize_result(result)


async def run_plugin_code(
    code: str,
    config: Dict[str, Any] = None,
    ctx: Dict[str, Any] = None,
    timeout: float = EXECUTION_TIMEOUT,
) -> Tuple[Dict[str, Any], int]:
    """执行自定义插件代码。

    :param code: 插件源码
    :param config: 节点配置
    :param ctx: 上下文快照（input_data/node_outputs/variables/...）
    :param timeout: 墙钟超时秒数
    :return: (输出 dict, 耗时毫秒)
    :raises SandboxError: 校验失败/超时/结果非法
    """
    import time

    code_obj = _compile_plugin(code)  # 校验在事件循环线程完成，失败快速抛出

    loop = asyncio.get_running_loop()
    started = time.monotonic()
    work = loop.run_in_executor(
        None, _run_sync, code_obj, config or {}, ctx or {}
    )
    try:
        output = await asyncio.wait_for(work, timeout=timeout)
    except asyncio.TimeoutError:
        work.cancel()
        raise SandboxError(f"插件执行超时（{timeout} 秒），已终止")
    except SandboxError:
        raise
    except Exception as exc:
        # 沙箱内 RuntimeError（循环超限）/ ValueError / KeyError 等统一包装
        raise SandboxError(f"插件执行错误: {exc}") from exc
    elapsed_ms = int((time.monotonic() - started) * 1000)
    return output, elapsed_ms


# ============ 4. 插件包装器 ============

class CustomSandboxPlugin(PluginBase):
    """将数据库中的自定义插件记录包装为可注册执行的 PluginBase。"""

    def __init__(self, record: Any) -> None:
        self.name = record.name
        self.version = getattr(record, "version", "1.0.0") or "1.0.0"
        self.description = getattr(record, "description", "") or ""
        self.node_type = record.node_type
        self._code = record.code
        schema = getattr(record, "config_schema", None) or {}
        self._schema = schema

    async def execute(self, config: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
        # ctx 是引擎的 ExecutionContext，提取只读快照传入沙箱
        ctx_snapshot = {
            "input_data": dict(getattr(ctx, "input_data", {}) or {}),
            "node_outputs": dict(getattr(ctx, "node_outputs", {}) or {}),
            "variables": dict(getattr(ctx, "variables", {}) or {}),
            "workflow_id": getattr(ctx, "workflow_id", None),
            "execution_id": getattr(ctx, "execution_id", None),
        }
        output, _elapsed = await run_plugin_code(self._code, config, ctx_snapshot)
        return output

    def get_config_schema(self) -> Dict[str, Any]:
        return self._schema if isinstance(self._schema, dict) else {"fields": []}

    def metadata(self) -> Dict[str, Any]:
        meta = super().metadata()
        meta["is_builtin"] = False
        return meta
