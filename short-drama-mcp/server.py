#!/usr/bin/env python3
"""
短剧创作 MCP 服务器 - MCP 2026-07-28 无状态协议实现

集成剧本校验、爽点统计、大纲生成等创作工具
"""

import json
import sys
import uuid
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "tools"))

from tools.format_checker import check_markdown_file, scan_files, CheckResult
from tools.stats_analyzer import analyze_content, classify_content as classify_by_stats
from tools.classifier import classify_content as classify_file
from tools.shuang_analyzer import count_shuang_points
from tools.platform_checker import check_platform_compliance, PLATFORM_RULES
from tools.outline_generator import generate_episode_outline

# MCP 协议版本
MCP_PROTOCOL_VERSION = "2026-07-28"
SERVER_INFO = {
    "name": "short-drama-mcp",
    "version": "1.0.0"
}

# 工具定义
TOOLS_REGISTRY = {
    "check_script_format": {
        "name": "check_script_format",
        "description": "校验剧本格式：检查禁止字符（耀/曜）、括号规范（【】）、标题格式、对话字数限制",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "要校验的剧本文件路径"},
                "strict_mode": {"type": "boolean", "description": "是否启用严格模式", "default": False}
            },
            "required": ["filepath"]
        }
    },
    "count_shuang_points": {
        "name": "count_shuang_points",
        "description": "统计爽点密度：分析剧本中的爽点数量和分布，计算每集爽点密度",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "剧本文件路径"}
            },
            "required": ["filepath"]
        }
    },
    "generate_episode_outline": {
        "name": "generate_episode_outline",
        "description": "根据小说生成集纲：分析小说内容，生成符合短剧规范的集数大纲",
        "inputSchema": {
            "type": "object",
            "properties": {
                "novel_content": {"type": "string", "description": "小说内容文本"},
                "total_episodes": {"type": "integer", "description": "总集数", "default": 10},
                "genre": {"type": "string", "description": "题材类型", "default": "都市异能"}
            },
            "required": ["novel_content"]
        }
    },
    "check_platform_compliance": {
        "name": "check_platform_compliance",
        "description": "检查红果平台投稿规范：验证对话长度、爽点数量、禁止元素等",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "剧本文件路径"}
            },
            "required": ["filepath"]
        }
    },
    "classify_content": {
        "name": "classify_content",
        "description": "内容分类：自动识别短剧剧本、短篇小说、教程文档等类型",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "文件路径"}
            },
            "required": ["filepath"]
        }
    },
    "list_tools": {
        "name": "list_tools",
        "description": "列出所有可用工具",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
}


def handle_discover() -> dict:
    """处理 server/discover 请求"""
    return {
        "jsonrpc": "2.0",
        "result": {
            "resultType": "complete",
            "serverInfo": SERVER_INFO,
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {},
                "prompts": {}
            },
            "instructions": "此MCP服务器提供短剧创作工具：check_script_format, count_shuang_points, generate_episode_outline, check_platform_compliance, classify_content"
        }
    }


def handle_tools_list() -> dict:
    """处理 tools/list 请求"""
    return {
        "jsonrpc": "2.0",
        "result": {
            "resultType": "complete",
            "tools": list(TOOLS_REGISTRY.values()),
            "ttlMs": 300000,
            "cacheScope": "public"
        }
    }


def handle_tools_call(name: str, arguments: dict) -> dict:
    """处理 tools/call 请求"""
    try:
        if name == "check_script_format":
            result = _handle_check_format(arguments.get("filepath"), arguments.get("strict_mode", False))
        elif name == "count_shuang_points":
            result = _handle_count_shuang(arguments.get("filepath"))
        elif name == "generate_episode_outline":
            result = _handle_generate_outline(
                arguments.get("novel_content", ""),
                arguments.get("total_episodes", 10),
                arguments.get("genre", "都市异能")
            )
        elif name == "check_platform_compliance":
            result = _handle_check_compliance(arguments.get("filepath"))
        elif name == "classify_content":
            result = _handle_classify(arguments.get("filepath"))
        elif name == "list_tools":
            result = {"tools": list(TOOLS_REGISTRY.values()), "count": len(TOOLS_REGISTRY)}
        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"未知工具: {name}"}]
            }
        
        return {
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
        }
    except Exception as e:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"错误: {str(e)}"}]
        }


def _handle_check_format(filepath: str, strict_mode: bool = False) -> dict:
    """处理格式校验"""
    result = check_markdown_file(filepath)
    return {
        "file": filepath,
        "name": result.name,
        "items": result.items,
        "total_chars": result.total_chars,
        "score": result.score,
        "issues": result.issues,
        "passed": len(result.issues) == 0
    }


def _handle_count_shuang(filepath: str) -> dict:
    """处理爽点统计"""
    return count_shuang_points(filepath)


def _handle_generate_outline(novel_content: str, total_episodes: int, genre: str) -> dict:
    """处理集纲生成"""
    return generate_episode_outline(novel_content, total_episodes, genre)


def _handle_check_compliance(filepath: str) -> dict:
    """处理平台合规检查"""
    return check_platform_compliance(filepath)


def _handle_classify(filepath: str) -> dict:
    """处理内容分类"""
    return classify_file(filepath)


class MCPRequestHandler(BaseHTTPRequestHandler):
    """MCP HTTP 请求处理器"""
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}", flush=True)
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        
        if parsed.path == "/health":
            self._send_json({
                "status": "ok",
                "server": SERVER_INFO["name"],
                "version": SERVER_INFO["version"],
                "protocol": MCP_PROTOCOL_VERSION
            })
        elif parsed.path == "/info":
            self._send_json({
                "server": SERVER_INFO,
                "protocol": MCP_PROTOCOL_VERSION,
                "tools": list(TOOLS_REGISTRY.keys())
            })
        else:
            self._send_error(404, "Not Found")
    
    def do_POST(self):
        """处理 POST 请求"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            request = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return
        
        method = self.headers.get('Mcp-Method', '')
        
        if method == 'server/discover':
            result = handle_discover()
        elif method == 'tools/list':
            result = handle_tools_list()
        elif method == 'tools/call':
            tool_name = request.get('name', '')
            tool_args = request.get('arguments', {})
            result = handle_tools_call(tool_name, tool_args)
        else:
            result = {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        self._send_json(result)
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Mcp-Method, Mcp-Name, Content-Type')
        self.end_headers()
    
    def _send_json(self, data: dict):
        """发送 JSON 响应"""
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        error = {"error": {"code": code, "message": message}}
        self.wfile.write(json.dumps(error, ensure_ascii=False).encode('utf-8'))


def main():
    import argparse
    parser = argparse.ArgumentParser(description='短剧创作 MCP Server')
    parser.add_argument('--port', type=int, default=8081, help='端口号（默认 8081）')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址')
    args = parser.parse_args()
    
    server = HTTPServer((args.host, args.port), MCPRequestHandler)
    print(f"🎬 短剧创作 MCP Server 启动中...")
    print(f"协议版本: {MCP_PROTOCOL_VERSION}")
    print(f"监听地址: http://{args.host}:{args.port}")
    print(f"健康检查: http://{args.host}:{args.port}/health")
    print(f"工具数量: {len(TOOLS_REGISTRY)}")
    print("按 Ctrl+C 停止服务器\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.shutdown()


if __name__ == '__main__':
    main()
