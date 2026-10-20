#!/usr/bin/env python3
"""
数据订阅服务
支持定时推送、事件订阅
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("mcp-subscription")


class SubscriptionManager:
    """订阅管理器"""
    
    def __init__(self):
        self.subscriptions: Dict[str, Dict] = {}
        self._running = False
    
    def add_subscription(self, user_id: str, config: Dict) -> str:
        """添加订阅"""
        sub_id = f"sub_{user_id}_{int(time.time())}"
        
        self.subscriptions[sub_id] = {
            "id": sub_id,
            "user_id": user_id,
            "config": config,
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0,
            "is_active": True
        }
        
        logger.info(f"订阅已创建: {sub_id}")
        return sub_id
    
    def _trigger_subscription(self, sub_id: str):
        """触发订阅"""
        sub = self.subscriptions.get(sub_id)
        if not sub or not sub["is_active"]:
            return
        
        sub["last_triggered"] = datetime.now().isoformat()
        sub["trigger_count"] = sub.get("trigger_count", 0) + 1
        
        # 执行订阅逻辑
        config = sub["config"]
        notification = {
            "subscription_id": sub_id,
            "user_id": sub["user_id"],
            "triggered_at": sub["last_triggered"],
            "content": self._generate_content(config)
        }
        
        # 发送到回调URL
        callback_url = config.get("callback_url")
        if callback_url:
            self._send_callback(callback_url, notification)
        
        logger.info(f"订阅触发: {sub_id}, 第{sub['trigger_count']}次")
    
    def _generate_content(self, config: Dict) -> Dict:
        """生成订阅内容"""
        content_type = config.get("content_type", "news_summary")
        
        if content_type == "news_summary":
            return {
                "type": "news_summary",
                "title": "每日财经新闻摘要",
                "generated_at": datetime.now().isoformat(),
                "count": 0,
                "items": []
            }
        
        return {"type": "generic", "content": "订阅通知"}
    
    def _send_callback(self, url: str, notification: Dict):
        """发送回调"""
        try:
            import requests
            requests.post(url, json=notification, timeout=10)
        except Exception as e:
            logger.error(f"回调发送失败: {e}")
    
    def list_subscriptions(self, user_id: str = None) -> List[Dict]:
        """列出订阅"""
        if user_id:
            return [s for s in self.subscriptions.values() if s["user_id"] == user_id]
        return list(self.subscriptions.values())
    
    def cancel_subscription(self, sub_id: str) -> bool:
        """取消订阅"""
        if sub_id in self.subscriptions:
            self.subscriptions[sub_id]["is_active"] = False
            return True
        return False
    
    def start_scheduler(self):
        """启动调度器"""
        self._running = True
        logger.info("订阅调度器已启动")
        
        while self._running:
            time.sleep(1)
    
    def stop_scheduler(self):
        """停止调度器"""
        self._running = False


class DataSubscription:
    """数据订阅服务入口"""
    
    def __init__(self):
        self.manager = SubscriptionManager()
    
    def subscribe(self, user_id: str, config: Dict) -> Dict:
        """订阅数据"""
        sub_id = self.manager.add_subscription(user_id, config)
        return {
            "status": "subscribed",
            "subscription_id": sub_id,
            "config": config
        }
    
    def unsubscribe(self, sub_id: str) -> Dict:
        """取消订阅"""
        success = self.manager.cancel_subscription(sub_id)
        return {
            "status": "unsubscribed" if success else "not_found",
            "subscription_id": sub_id
        }
    
    def list_subscriptions(self, user_id: str = None) -> Dict:
        """列出订阅"""
        return {
            "subscriptions": self.manager.list_subscriptions(user_id),
            "count": len(self.manager.list_subscriptions(user_id))
        }
