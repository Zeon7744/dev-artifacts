#!/usr/bin/env python3
"""
计费策略模块
支持免费/收费层级管理
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("mcp-pricing")


class PricingTier:
    """计费层级定义"""
    
    TIERS = {
        "free": {
            "name": "免费层",
            "price": 0,
            "currency": "USD",
            "features": {
                "daily_requests": 100,
                "news_sources": ["basic"],
                "sentiment_depth": "basic",
                "prediction_horizon": "1d",
                "webhook": False,
                "subscription": False,
                "bulk_query": False,
                "custom_sources": False
            },
            "rate_limit": {
                "per_minute": 10,
                "per_hour": 100,
                "per_day": 1000
            }
        },
        "premium": {
            "name": "高级层",
            "price": 29.99,
            "currency": "USD",
            "interval": "month",
            "features": {
                "daily_requests": 10000,
                "news_sources": ["all"],
                "sentiment_depth": "advanced",
                "prediction_horizon": "1w",
                "webhook": True,
                "subscription": True,
                "bulk_query": False,
                "custom_sources": False
            },
            "rate_limit": {
                "per_minute": 100,
                "per_hour": 1000,
                "per_day": 10000
            }
        },
        "enterprise": {
            "name": "企业层",
            "price": 199.99,
            "currency": "USD",
            "interval": "month",
            "features": {
                "daily_requests": -1,  # 无限制
                "news_sources": ["all", "premium"],
                "sentiment_depth": "advanced",
                "prediction_horizon": "1m",
                "webhook": True,
                "subscription": True,
                "bulk_query": True,
                "custom_sources": True,
                "api_access": True,
                "priority_support": True
            },
            "rate_limit": {
                "per_minute": 1000,
                "per_hour": 10000,
                "per_day": -1
            }
        }
    }
    
    @classmethod
    def get_tier(cls, tier_name: str) -> Optional[Dict]:
        """获取层级配置"""
        return cls.TIERS.get(tier_name)
    
    @classmethod
    def list_tiers(cls) -> List[Dict]:
        """列出所有层级"""
        return [
            {
                "name": name,
                "price": config["price"],
                "currency": config["currency"],
                "interval": config.get("interval", "one-time"),
                "features": list(config["features"].keys())
            }
            for name, config in cls.TIERS.items()
        ]
    
    @classmethod
    def check_feature(cls, tier_name: str, feature: str) -> bool:
        """检查是否包含某功能"""
        tier = cls.TIERS.get(tier_name)
        if not tier:
            return False
        return tier["features"].get(feature, False)
    
    @classmethod
    def calculate_usage_percentage(cls, tier_name: str, used: int) -> float:
        """计算使用率"""
        tier = cls.TIERS.get(tier_name)
        if not tier:
            return 0.0
        
        daily_limit = tier["features"]["daily_requests"]
        if daily_limit == -1:
            return 0.0
        
        return min(used / daily_limit * 100, 100.0)


class PricingStrategy:
    """定价策略管理器"""
    
    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.billing_history: List[Dict] = []
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        try:
            import os
            data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
        except Exception as e:
            logger.warning(f"加载用户数据失败: {e}")
    
    def save_data(self):
        """保存数据"""
        try:
            import os
            data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
            os.makedirs(os.path.dirname(data_file), exist_ok=True)
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}")
    
    def register_user(self, user_id: str, name: str, email: str, tier: str = "free") -> Dict:
        """注册用户"""
        if user_id in self.users:
            return {"error": "用户已存在", "user_id": user_id}
        
        self.users[user_id] = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "tier": tier,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "usage": {
                "daily": 0,
                "monthly": 0,
                "total": 0
            },
            "billing": {
                "current_period_start": datetime.now().isoformat(),
                "current_period_end": (datetime.now() + timedelta(days=30)).isoformat(),
                "next_billing_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "status": "active"
            },
            "is_active": True
        }
        
        self.save_data()
        
        return {
            "status": "registered",
            "user_id": user_id,
            "tier": tier,
            "features": list(PricingTier.TIERS.get(tier, {}).get("features", {}).keys())
        }
    
    def upgrade_tier(self, user_id: str, new_tier: str) -> Dict:
        """升级层级"""
        if user_id not in self.users:
            return {"error": "用户不存在"}
        
        old_tier = self.users[user_id]["tier"]
        self.users[user_id]["tier"] = new_tier
        self.users[user_id]["billing"]["current_period_start"] = datetime.now().isoformat()
        self.users[user_id]["billing"]["current_period_end"] = (datetime.now() + timedelta(days=30)).isoformat()
        
        # 记录计费历史
        self.billing_history.append({
            "user_id": user_id,
            "action": "upgrade",
            "from_tier": old_tier,
            "to_tier": new_tier,
            "timestamp": datetime.now().isoformat()
        })
        
        self.save_data()
        
        return {
            "status": "upgraded",
            "user_id": user_id,
            "old_tier": old_tier,
            "new_tier": new_tier
        }
    
    def check_access(self, user_id: str, feature: str) -> Dict:
        """检查访问权限"""
        if user_id not in self.users:
            return {"allowed": False, "reason": "用户不存在"}
        
        user = self.users[user_id]
        tier = user["tier"]
        
        if not user["is_active"]:
            return {"allowed": False, "reason": "账户已停用"}
        
        allowed = PricingTier.check_feature(tier, feature)
        
        return {
            "allowed": allowed,
            "tier": tier,
            "feature": feature
        }
    
    def record_usage(self, user_id: str, count: int = 1) -> Dict:
        """记录使用情况"""
        if user_id not in self.users:
            return {"error": "用户不存在"}
        
        user = self.users[user_id]
        user["usage"]["daily"] += count
        user["usage"]["monthly"] += count
        user["usage"]["total"] += count
        
        # 检查是否超出限制
        tier_config = PricingTier.TIERS.get(user["tier"], {})
        daily_limit = tier_config.get("features", {}).get("daily_requests", 100)
        
        if daily_limit != -1 and user["usage"]["daily"] >= daily_limit:
            return {
                "status": "limit_exceeded",
                "daily_used": user["usage"]["daily"],
                "daily_limit": daily_limit,
                "percentage": PricingTier.calculate_usage_percentage(user["tier"], user["usage"]["daily"])
            }
        
        return {
            "status": "recorded",
            "daily_used": user["usage"]["daily"],
            "daily_limit": daily_limit,
            "percentage": PricingTier.calculate_usage_percentage(user["tier"], user["usage"]["daily"])
        }
    
    def get_user_stats(self, user_id: str) -> Dict:
        """获取用户统计"""
        if user_id not in self.users:
            return {"error": "用户不存在"}
        
        user = self.users[user_id]
        tier_config = PricingTier.TIERS.get(user["tier"], {})
        
        return {
            "user_id": user_id,
            "tier": user["tier"],
            "tier_name": tier_config.get("name", "Unknown"),
            "usage": user["usage"],
            "billing": user["billing"],
            "features": list(tier_config.get("features", {}).keys()),
            "limits": tier_config.get("rate_limit", {})
        }
    
    def list_users(self, limit: int = 100) -> Dict:
        """列出用户"""
        users = []
        for uid, data in self.users.items():
            users.append({
                "user_id": uid,
                "name": data["name"],
                "email": data["email"],
                "tier": data["tier"],
                "created_at": data["created_at"],
                "is_active": data["is_active"]
            })
        
        return {
            "users": users[:limit],
            "total": len(users)
        }
