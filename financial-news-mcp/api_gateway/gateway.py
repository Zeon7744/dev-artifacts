#!/usr/bin/env python3
"""
RESTful API网关
支持外部应用接入、数据订阅、认证鉴权
"""

import hashlib
import hmac
import json
import time
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

logger = logging.getLogger("mcp-api-gateway")


class APIKeyManager:
    """API密钥管理"""
    
    def __init__(self):
        self.keys: Dict[str, Dict] = {}
        self._load_keys()
    
    def _load_keys(self):
        """加载密钥配置"""
        try:
            import os
            keys_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'api_keys.json')
            if os.path.exists(keys_file):
                with open(keys_file, 'r', encoding='utf-8') as f:
                    self.keys = json.load(f)
        except Exception as e:
            logger.warning(f"加载API密钥失败: {e}")
    
    def save_keys(self):
        """保存密钥配置"""
        try:
            import os
            keys_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'api_keys.json')
            os.makedirs(os.path.dirname(keys_file), exist_ok=True)
            with open(keys_file, 'w', encoding='utf-8') as f:
                json.dump(self.keys, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存API密钥失败: {e}")
    
    def create_key(self, name: str, tier: str = "free", rate_limit: int = 100) -> Dict[str, Any]:
        """创建新的API密钥"""
        key_id = hashlib.sha256(f"{name}_{time.time()}_{uuid.uuid4()}".encode()).hexdigest()[:16]
        api_key = f"fnmcp_{key_id}"
        
        self.keys[api_key] = {
            "name": name,
            "tier": tier,
            "rate_limit": rate_limit,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "request_count": 0,
            "is_active": True,
            "permissions": self._get_tier_permissions(tier)
        }
        
        self.save_keys()
        
        return {
            "api_key": api_key,
            "name": name,
            "tier": tier,
            "rate_limit": rate_limit,
            "created_at": self.keys[api_key]["created_at"]
        }
    
    def _get_tier_permissions(self, tier: str) -> List[str]:
        """获取不同等级的权限"""
        permissions = {
            "free": ["news_basic", "sentiment_basic", "predict_basic"],
            "premium": ["news_all", "sentiment_advanced", "predict_advanced", "investment_advice"],
            "enterprise": ["all", "webhook", "subscription", "bulk_query", "custom_sources"]
        }
        return permissions.get(tier, permissions["free"])
    
    def validate_key(self, api_key: str) -> Optional[Dict]:
        """验证API密钥"""
        if not api_key or not api_key.startswith("fnmcp_"):
            return None
        
        key_data = self.keys.get(api_key)
        if not key_data:
            return None
        
        if not key_data.get("is_active"):
            return None
        
        # 更新使用时间
        key_data["last_used"] = datetime.now().isoformat()
        key_data["request_count"] = key_data.get("request_count", 0) + 1
        self.save_keys()
        
        return key_data
    
    def check_rate_limit(self, api_key: str) -> bool:
        """检查速率限制"""
        key_data = self.keys.get(api_key)
        if not key_data:
            return False
        
        limit = key_data.get("rate_limit", 100)
        count = key_data.get("request_count", 0)
        
        # 简单的速率限制（实际应用中应使用时窗计数）
        return count < limit * 10  # 允许10倍突发
    
    def get_tier(self, api_key: str) -> str:
        """获取账户等级"""
        key_data = self.keys.get(api_key)
        return key_data.get("tier", "free") if key_data else "unauthorized"
    
    def revoke_key(self, api_key: str) -> bool:
        """撤销密钥"""
        if api_key in self.keys:
            self.keys[api_key]["is_active"] = False
            self.save_keys()
            return True
        return False


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    gateway = None
    
    def do_GET(self):
        """处理GET请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # CORS
        self.send_cors_headers()
        
        if path == "/health":
            self._send_json({"status": "ok", "timestamp": datetime.now().isoformat()})
        
        elif path == "/api/v1/status":
            self._send_json({
                "service": "financial-news-mcp",
                "version": "2.0.0",
                "endpoints": self._list_endpoints(),
                "documentation": "/api-docs"
            })
        
        elif path == "/api/v1/sources":
            api_key = self._get_api_key(params)
            if not self.gateway.api_manager.validate_key(api_key):
                self._send_error(401, "Unauthorized")
                return
            self._send_json(self.gateway._get_sources_list())
        
        elif path == "/api/v1/tools":
            api_key = self._get_api_key(params)
            if not self.gateway.api_manager.validate_key(api_key):
                self._send_error(401, "Unauthorized")
                return
            self._send_json(self.gateway._list_tools())
        
        elif path.startswith("/api/v1/news"):
            self._handle_news_request(params)
        
        elif path.startswith("/api/v1/predict"):
            self._handle_predict_request(params)
        
        elif path == "/api-docs":
            self._send_documentation()
        
        else:
            self._send_error(404, "Not found")
    
    def do_POST(self):
        """处理POST请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        self.send_cors_headers()
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return
        
        api_key = data.get("api_key") or self.headers.get("X-API-Key")
        
        if not api_key:
            self._send_error(401, "API key required")
            return
        
        key_data = self.gateway.api_manager.validate_key(api_key)
        if not key_data:
            self._send_error(401, "Invalid API key")
            return
        
        if not self.gateway.api_manager.check_rate_limit(api_key):
            self._send_error(429, "Rate limit exceeded")
            return
        
        # 权限检查
        if not self._check_permission(key_data, path):
            self._send_error(403, "Permission denied")
            return
        
        if path == "/api/v1/news/collect":
            self._handle_collect_news(data)
        
        elif path == "/api/v1/sentiment/analyze":
            self._handle_analyze_sentiment(data)
        
        elif path == "/api/v1/predict":
            self._handle_predict(data)
        
        elif path == "/api/v1/advice":
            self._handle_get_advice(data)
        
        elif path == "/api/v1/validate":
            self._handle_validate(data)
        
        elif path == "/webhook/register":
            self._handle_register_webhook(data, api_key)
        
        else:
            self._send_error(404, "Endpoint not found")
    
    def send_cors_headers(self):
        """发送CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.send_header('Content-Type', 'application/json')
    
    def _send_json(self, data: Any):
        """发送JSON响应"""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": {"code": code, "message": message}
        }, ensure_ascii=False).encode('utf-8'))
    
    def _get_api_key(self, params: Dict) -> str:
        """从参数获取API密钥"""
        return params.get("api_key", [None])[0]
    
    def _check_permission(self, key_data: Dict, path: str) -> bool:
        """检查权限"""
        permissions = key_data.get("permissions", [])
        tier = key_data.get("tier", "free")
        
        # 权限映射
        path_permissions = {
            "/api/v1/news/collect": "news_all" if tier != "free" else "news_basic",
            "/api/v1/sentiment/analyze": "sentiment_advanced" if tier in ["premium", "enterprise"] else "sentiment_basic",
            "/api/v1/predict": "predict_advanced" if tier in ["premium", "enterprise"] else "predict_basic",
            "/api/v1/advice": "investment_advice",
            "/api/v1/validate": "news_basic",
            "/webhook/register": "webhook" if tier == "enterprise" else None,
        }
        
        required = path_permissions.get(path)
        if not required:
            return True
        
        return required in permissions
    
    def _handle_news_request(self, params: Dict):
        """处理新闻请求"""
        api_key = self._get_api_key(params)
        category = params.get("category", ["all"])[0]
        limit = int(params.get("limit", [20])[0])
        time_range = params.get("time_range", ["24h"])[0]
        
        result = self.gateway._execute_tool("collect_news", {
            "category": category,
            "limit": limit,
            "time_range": time_range
        })
        
        self._send_json(result)
    
    def _handle_collect_news(self, data: Dict):
        """处理新闻采集"""
        result = self.gateway._execute_tool("collect_news", data)
        self._send_json(result)
    
    def _handle_analyze_sentiment(self, data: Dict):
        """处理情感分析"""
        result = self.gateway._execute_tool("analyze_sentiment", data)
        self._send_json(result)
    
    def _handle_predict(self, data: Dict):
        """处理趋势预测"""
        result = self.gateway._execute_tool("predict_trend", data)
        self._send_json(result)
    
    def _handle_get_advice(self, data: Dict):
        """处理投资建议"""
        result = self.gateway._execute_tool("get_investment_advice", data)
        self._send_json(result)
    
    def _handle_validate(self, data: Dict):
        """处理数据验证"""
        result = self.gateway._execute_tool("validate_data_source", data)
        self._send_json(result)
    
    def _handle_register_webhook(self, data: Dict, api_key: str):
        """注册Webhook"""
        result = self.gateway._register_webhook(api_key, data)
        self._send_json(result)
    
    def _list_endpoints(self) -> List[Dict]:
        """列出可用端点"""
        return [
            {"method": "GET", "path": "/health", "desc": "健康检查"},
            {"method": "GET", "path": "/api/v1/status", "desc": "服务状态"},
            {"method": "GET", "path": "/api/v1/sources", "desc": "数据源列表"},
            {"method": "GET", "path": "/api/v1/tools", "desc": "工具列表"},
            {"method": "GET", "path": "/api/v1/news", "desc": "新闻查询"},
            {"method": "POST", "path": "/api/v1/news/collect", "desc": "新闻采集"},
            {"method": "POST", "path": "/api/v1/sentiment/analyze", "desc": "情感分析"},
            {"method": "POST", "path": "/api/v1/predict", "desc": "趋势预测"},
            {"method": "POST", "path": "/api/v1/advice", "desc": "投资建议"},
            {"method": "POST", "path": "/api/v1/validate", "desc": "数据验证"},
            {"method": "POST", "path": "/webhook/register", "desc": "注册Webhook"},
        ]
    
    def _send_documentation(self):
        """发送API文档"""
        docs = {
            "title": "Financial News MCP API",
            "version": "2.0.0",
            "base_url": "http://localhost:8766",
            "authentication": "API Key (header: X-API-Key)",
            "tiers": {
                "free": {"rate_limit": 100, "description": "基础功能"},
                "premium": {"rate_limit": 1000, "description": "高级功能"},
                "enterprise": {"rate_limit": "unlimited", "description": "全部功能+Webhook"}
            },
            "endpoints": self._list_endpoints()
        }
        self._send_json(docs)


class APIGateway:
    """API网关主类"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8766):
        self.host = host
        self.port = port
        self.api_manager = APIKeyManager()
        self.webhooks: Dict[str, List[Dict]] = {}
        self.server = None
        self.thread = None
        
        WebhookHandler.gateway = self
    
    def start(self, blocking: bool = False):
        """启动API网关"""
        self.server = HTTPServer((self.host, self.port), WebhookHandler)
        
        if blocking:
            logger.info(f"API网关启动于 http://{self.host}:{self.port}")
            self.server.serve_forever()
        else:
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            logger.info(f"API网关已启动于 http://{self.host}:{self.port}")
    
    def stop(self):
        """停止API网关"""
        if self.server:
            self.server.shutdown()
            logger.info("API网关已停止")
    
    def _execute_tool(self, tool_name: str, args: Dict) -> Dict:
        """执行MCP工具（通过进程间通信）"""
        return {
            "tool": tool_name,
            "args": args,
            "status": "executed",
            "timestamp": datetime.now().isoformat(),
            "note": "实际执行需通过IPC调用主服务器"
        }
    
    def _get_sources_list(self) -> List[Dict]:
        """获取数据源列表"""
        try:
            from tools.news_collector import FinancialNewsCollector
            collector = FinancialNewsCollector()
            return collector.get_available_sources()
        except Exception as e:
            logger.error(f"获取数据源列表失败: {e}")
            return []
    
    def _list_tools(self) -> List[Dict]:
        """列出可用工具"""
        return [
            {
                "name": "collect_news",
                "description": "采集全球财经新闻",
                "tier_required": "free"
            },
            {
                "name": "analyze_sentiment",
                "description": "新闻情感分析",
                "tier_required": "free"
            },
            {
                "name": "predict_trend",
                "description": "市场趋势预测",
                "tier_required": "premium"
            },
            {
                "name": "get_investment_advice",
                "description": "投资建议生成",
                "tier_required": "premium"
            },
            {
                "name": "validate_data_source",
                "description": "数据源验证",
                "tier_required": "free"
            }
        ]
    
    def _register_webhook(self, api_key: str, data: Dict) -> Dict:
        """注册Webhook"""
        if api_key not in self.webhooks:
            self.webhooks[api_key] = []
        
        webhook = {
            "url": data.get("url"),
            "events": data.get("events", ["news.collected", "sentiment.changed"]),
            "secret": data.get("secret", hashlib.sha256(str(time.time()).encode()).hexdigest()[:32]),
            "created_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        self.webhooks[api_key].append(webhook)
        
        return {
            "status": "registered",
            "webhook_id": len(self.webhooks[api_key]) - 1,
            "url": webhook["url"]
        }
    
    def create_api_key(self, name: str, tier: str = "free") -> Dict:
        """创建API密钥"""
        return self.api_manager.create_key(name, tier)
    
    def revoke_api_key(self, api_key: str) -> bool:
        """撤销API密钥"""
        return self.api_manager.revoke_key(api_key)
    
    def get_tier_info(self, api_key: str) -> Dict:
        """获取账户信息"""
        key_data = self.api_manager.validate_key(api_key)
        if not key_data:
            return {"error": "Invalid key"}
        
        return {
            "name": key_data["name"],
            "tier": key_data["tier"],
            "rate_limit": key_data["rate_limit"],
            "permissions": key_data["permissions"],
            "request_count": key_data["request_count"],
            "last_used": key_data["last_used"]
        }
