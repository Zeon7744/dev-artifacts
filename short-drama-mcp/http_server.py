#!/usr/bin/env python3
"""
短剧创作 MCP HTTP Server
MCP 2026-07-28 无状态协议 HTTP 部署入口
"""

import sys
from pathlib import Path

# 导入核心服务器
sys.path.insert(0, str(Path(__file__).parent))
from server import MCPRequestHandler, SERVER_INFO, MCP_PROTOCOL_VERSION

from http.server import HTTPServer
import argparse


def main():
    parser = argparse.ArgumentParser(description='短剧创作 MCP HTTP Server')
    parser.add_argument('--port', type=int, default=8081, help='端口号（默认 8081）')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址')
    args = parser.parse_args()
    
    server = HTTPServer((args.host, args.port), MCPRequestHandler)
    print(f"🎬 短剧创作 MCP HTTP Server 启动中...")
    print(f"协议版本: {MCP_PROTOCOL_VERSION}")
    print(f"监听地址: http://{args.host}:{args.port}")
    print(f"健康检查: http://{args.host}:{args.port}/health")
    print("按 Ctrl+C 停止服务器\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.shutdown()


if __name__ == '__main__':
    main()
