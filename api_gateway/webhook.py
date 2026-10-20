#!/usr/bin/env python3
"""
Webhook服务
支持事件推送、回调通知
"""

import json
import hashlib
import hmac
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("mcp-webhook")


class WebhookService:
    """Webhook推送服务"""
    
    def __init__(self, max_retries: int = 3, timeout: int = 10):
        self.max_retries = max_retries
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._delivery_log: List[Dict] = []
    
    def register_webhook(self, api_key: str, webhook_url: str, events: List[str], secret: str = "") -> Dict:
        """注册Webhook"""
        webhook_id = hashlib.sha256(f"{api_key}_{webhook_url}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        return {
            "webhook_id": webhook_id,
            "api_key": api_key,
            "url": webhook_url,
            "events": events,
            "secret": secret,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
    
    def trigger_event(self, event_type: str, data: Dict, webhook_list: List[Dict] = None):
        """触发事件并推送给所有注册的Webhook"""
        if not webhook_list:
            return
        
        for webhook in webhook_list:
            if event_type not in webhook.get("events", []):
                continue
            
            self._deliver(webhook, event_type, data)
    
    def _deliver(self, webhook: Dict, event_type: str, data: Dict):
        """投递单个Webhook"""
        url = webhook["url"]
        secret = webhook.get("secret", "")
        
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "id": hashlib.sha256(f"{event_type}_{data}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event_type,
            "X-Webhook-ID": payload["id"]
        }
        
        if secret:
            signature = hmac.new(
                secret.encode(),
                json.dumps(payload, ensure_ascii=False).encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Hub-Signature-256"] = f"sha256={signature}"
        
        # 异步投递
        self.executor.submit(self._send_request, url, payload, headers)
    
    def _send_request(self, url: str, payload: Dict, headers: Dict):
        """发送Webhook请求"""
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                delivery_record = {
                    "url": url,
                    "event": payload["event"],
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat(),
                    "attempt": attempt + 1,
                    "success": 200 <= response.status_code < 300
                }
                
                self._delivery_log.append(delivery_record)
                
                if delivery_record["success"]:
                    logger.info(f"Webhook推送成功: {url} - {payload['event']}")
                    return
                
                logger.warning(f"Webhook推送失败 (attempt {attempt+1}): {url} - {response.status_code}")
                
            except Exception as e:
                logger.error(f"Webhook推送异常: {url} - {e}")
                
                self._delivery_log.append({
                    "url": url,
                    "event": payload["event"],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "attempt": attempt + 1,
                    "success": False
                })
        
        logger.error(f"Webhook推送最终失败: {url}")
    
    def get_delivery_history(self, limit: int = 100) -> List[Dict]:
        """获取推送历史"""
        return self._delivery_log[-limit:]
    
    def cleanup_old_records(self, days: int = 7):
        """清理旧记录"""
        cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
        self._delivery_log = [
            r for r in self._delivery_log
            if datetime.fromisoformat(r["timestamp"]) > cutoff
        ]
