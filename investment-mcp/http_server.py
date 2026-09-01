#!/usr/bin/env python3
"""
Investment MCP HTTP Server
MCP 2026-07-28 无状态协议 HTTP 部署入口
"""

import sys
import json
import argparse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 导入核心服务器
sys.path.insert(0, str(Path(__file__).parent))
from server_core import (
    handle_mcp_discover,
    handle_tools_list,
    handle_tools_call,
    MCP_PROTOCOL_VERSION,
    SERVER_INFO
)

class MCPRequestHandler(BaseHTTPRequestHandler):
    """MCP HTTP 请求处理器"""
    
    def log_message(self, format, *args):
        """自定义日志格式"""
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
                "capabilities": ["tools"]
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
        
        # 获取路由头
        method = self.headers.get('Mcp-Method', '')
        mcp_name = self.headers.get('Mcp-Name', '')
        
        # 路由处理
        if method == 'server/discover':
            result = handle_mcp_discover()
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
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Mcp-Method, Mcp-Name, Content-Type')
        self.end_headers()


def main():
    parser = argparse.ArgumentParser(description='Investment MCP HTTP Server')
    parser.add_argument('--port', type=int, default=8080, help='端口号（默认 8080）')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址（默认 0.0.0.0）')
    args = parser.parse_args()
    
    server = HTTPServer((args.host, args.port), MCPRequestHandler)
    print(f"Investment MCP Server 启动中...")
    print(f"协议版本: {MCP_PROTOCOL_VERSION}")
    print(f"监听地址: http://{args.host}:{args.port}")
    print(f"健康检查: http://{args.host}:{args.port}/health")
    print(f"工具列表: POST http://{args.host}:{args.port}/mcp (Mcp-Method: tools/list)")
    print("按 Ctrl+C 停止服务器\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.shutdown()


if __name__ == '__main__':
    main()
