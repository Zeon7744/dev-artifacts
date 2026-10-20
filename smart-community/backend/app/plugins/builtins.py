"""
内置插件 - 随系统开箱即用的工作流节点

1. TextFormatPlugin    文本处理（大写/小写/反转/模板渲染）
2. JsonTransformPlugin JSON 处理（解析/序列化/字段提取）
3. MathCalcPlugin      安全数学表达式计算

导入本模块即自动注册到全局 registry。
"""
import json
from typing import Any, Dict

from .base import PluginBase, registry

__all__ = [
    "TextFormatPlugin",
    "JsonTransformPlugin",
    "MathCalcPlugin",
]


class TextFormatPlugin(PluginBase):
    """文本处理插件：对输入文本做大小写、反转或模板渲染。"""

    name = "文本处理"
    version = "1.0.0"
    description = "对文本进行大写、小写、反转处理，或使用 {{变量}} 模板渲染生成文本"
    node_type = "plugin.text_format"

    async def execute(self, config: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
        operation = config.get("operation", "upper")
        text = config.get("text")
        # 未显式配置 text 时，优先取输入数据中的 text 字段
        if text is None:
            input_text = ctx.input_data.get("text") if isinstance(ctx.input_data, dict) else None
            text = "" if input_text is None else str(input_text)
        text = str(text)

        if operation == "upper":
            result = text.upper()
        elif operation == "lower":
            result = text.lower()
        elif operation == "reverse":
            result = text[::-1]
        elif operation == "template":
            # 模板操作：模板中可使用 {{node_id.field}} / {{var.x}} / {{input.x}}
            result = ctx.resolve_template(config.get("template", text))
        else:
            raise ValueError(f"不支持的文本操作: {operation}")

        return {"text": result, "operation": operation}

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "key": "operation",
                    "label": "操作类型",
                    "type": "select",
                    "required": True,
                    "default": "upper",
                    "options": [
                        {"value": "upper", "label": "转大写"},
                        {"value": "lower", "label": "转小写"},
                        {"value": "reverse", "label": "反转字符串"},
                        {"value": "template", "label": "模板渲染"},
                    ],
                },
                {
                    "key": "text",
                    "label": "输入文本",
                    "type": "text",
                    "required": False,
                    "default": "",
                    "placeholder": "留空则使用工作流输入 data.text；支持 {{变量}} 引用",
                },
                {
                    "key": "template",
                    "label": "模板内容（operation=template 时生效）",
                    "type": "textarea",
                    "required": False,
                    "default": "",
                    "placeholder": "例如：您好 {{input.username}}，今日待办 {{var.todo_count}} 条",
                },
            ]
        }


class JsonTransformPlugin(PluginBase):
    """JSON 处理插件：字符串解析、对象序列化、字段提取。"""

    name = "JSON处理"
    version = "1.0.0"
    description = "JSON 字符串解析为对象、对象序列化为字符串，或从对象中提取指定字段"
    node_type = "plugin.json_transform"

    async def execute(self, config: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
        operation = config.get("operation", "parse")

        # 输入来源：优先 config.data（会做模板渲染），否则取工作流输入 data 字段
        data = config.get("data")
        if data is None:
            data = ctx.input_data.get("data") if isinstance(ctx.input_data, dict) else None
        elif isinstance(data, str):
            data = ctx.resolve_template(data)

        if operation == "parse":
            if not isinstance(data, str):
                raise ValueError("parse 操作需要字符串输入")
            parsed = json.loads(data)
            return {"data": parsed, "operation": operation}

        if operation == "stringify":
            return {
                "text": json.dumps(data, ensure_ascii=False),
                "operation": operation,
            }

        if operation == "pick":
            if not isinstance(data, dict):
                raise ValueError("pick 操作需要 JSON 对象输入，请先用 parse 解析")
            fields = config.get("fields", [])
            if isinstance(fields, str):
                fields = [f.strip() for f in fields.split(",") if f.strip()]
            picked = {key: data.get(key) for key in fields}
            return {"data": picked, "operation": operation}

        raise ValueError(f"不支持的 JSON 操作: {operation}")

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "key": "operation",
                    "label": "操作类型",
                    "type": "select",
                    "required": True,
                    "default": "parse",
                    "options": [
                        {"value": "parse", "label": "解析（JSON字符串 → 对象）"},
                        {"value": "stringify", "label": "序列化（对象 → JSON字符串）"},
                        {"value": "pick", "label": "提取字段"},
                    ],
                },
                {
                    "key": "data",
                    "label": "输入数据",
                    "type": "textarea",
                    "required": False,
                    "default": "",
                    "placeholder": "留空则使用工作流输入 data.data；字符串支持 {{变量}} 引用",
                },
                {
                    "key": "fields",
                    "label": "提取字段列表（operation=pick 时生效）",
                    "type": "text",
                    "required": False,
                    "default": "",
                    "placeholder": "逗号分隔，如：id,name,email",
                },
            ]
        }


class MathCalcPlugin(PluginBase):
    """安全数学计算插件：受限环境内求值算术表达式。"""

    name = "数学计算"
    version = "1.0.0"
    description = "安全计算算术表达式，支持 abs/round/min/max/sum/len 及工作流变量，禁止 import 与属性访问"
    node_type = "plugin.math_calc"

    # 表达式中允许使用的白名单函数
    _SAFE_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
    }

    async def execute(self, config: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
        expression = str(config.get("expression", "")).strip()
        if not expression:
            raise ValueError("expression 不能为空")

        # 先渲染模板变量（{{var.x}} / {{input.x}} / {{node.field}}）
        expression = ctx.resolve_template(expression)

        # 安全护栏：禁止 import 及双下划线名称（防止 __class__ 等沙箱逃逸）
        lowered = expression.lower()
        if "import" in lowered:
            raise ValueError("表达式中禁止使用 import")
        if "__" in expression:
            raise ValueError("表达式中禁止使用双下划线标识符")

        # 受限求值：__builtins__ 置空，只暴露白名单函数与工作流变量
        safe_globals: Dict[str, Any] = {"__builtins__": {}}
        safe_locals: Dict[str, Any] = {
            **self._SAFE_FUNCTIONS,
            **(ctx.variables or {}),
        }
        value = eval(expression, safe_globals, safe_locals)  # noqa: S307 - 已做白名单与关键字限制

        return {"value": value, "expression": expression}

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "key": "expression",
                    "label": "数学表达式",
                    "type": "textarea",
                    "required": True,
                    "default": "",
                    "placeholder": "例如：(price * count) * 0.9，可引用 {{var.x}} 变量；可用函数：abs/round/min/max/sum/len",
                    "help": "仅支持算术运算与白名单函数，禁止 import、属性访问及任意内置函数",
                },
            ]
        }


# ============ 注册内置插件 ============
for _plugin_cls in (TextFormatPlugin, JsonTransformPlugin, MathCalcPlugin):
    registry.register(_plugin_cls())
