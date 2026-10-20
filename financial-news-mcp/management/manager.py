#!/usr/bin/env python3
"""
管理平台主模块
整合用户管理、权限控制、计费策略
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .pricing import PricingStrategy, PricingTier
from .permissions import PermissionController, RoleManager

logger = logging.getLogger("mcp-management")


class ManagementSystem:
    """管理系统主入口"""
    
    def __init__(self):
        self.pricing = PricingStrategy()
        self.permissions = PermissionController()
        self.roles = RoleManager()
    
    def register_user(self, user_id: str, name: str, email: str, role: str = "viewer") -> Dict:
        """注册用户"""
        # 检查角色是否存在
        role_def = self.roles.get_role(role)
        if not role_def:
            return {"error": f"角色 {role} 不存在"}
        
        # 注册用户
        result = self.pricing.register_user(user_id, name, email, tier="free")
        
        if "error" in result:
            return result
        
        # 设置角色权限
        self.permissions.grant_permission(user_id, "__role__", role)
        
        logger.info(f"用户注册成功: {user_id}, 角色: {role}")
        
        return {
            **result,
            "role": role,
            "permissions": role_def["permissions"]
        }
    
    def upgrade_user(self, user_id: str, new_tier: str) -> Dict:
        """升级用户层级"""
        result = self.pricing.upgrade_tier(user_id, new_tier)
        
        if "error" in result:
            return result
        
        logger.info(f"用户升级: {user_id}, {result['old_tier']} -> {result['new_tier']}")
        
        return result
    
    def check_access(self, user_id: str, resource: str, action: str) -> Dict:
        """检查访问权限"""
        # 管理员直接放行
        if user_id.startswith("admin_"):
            return {"allowed": True, "reason": "管理员", "role": "admin"}

        # 检查用户是否存在
        if user_id not in self.pricing.users:
            return {"allowed": False, "reason": "用户不存在", "tier": "none"}

        # 检查角色
        role_result = self._get_user_role(user_id)

        if role_result.get("role") == "admin":
            return {"allowed": True, "reason": "管理员", "role": "admin"}

        # 检查层级功能（将resource映射到对应的feature名）
        tier = self.pricing.users[user_id].get("tier", "free")
        feature_map = {"news": "news_sources", "sentiment": "sentiment_depth",
                       "predict": "prediction_horizon", "validate": "news_sources",
                       "webhook": "webhook"}
        feature_name = feature_map.get(resource, resource)
        tier_check = PricingTier.check_feature(tier, feature_name)

        # 检查角色权限
        role = role_result.get("role", "viewer")
        role_perm = self.roles.check_role_permission(role, resource, action)

        # 综合判断：层级允许且角色允许则通过
        allowed = tier_check and role_perm.get("allowed", False)

        return {
            "allowed": allowed,
            "tier": tier,
            "role": role,
            "resource": resource,
            "action": action
        }
    
    def _get_user_role(self, user_id: str) -> Dict:
        """获取用户角色"""
        perms = self.permissions.get_user_permissions(user_id)
        role_perms = perms.get("__role__", {})
        # __role__ 存储格式为 {role_name: True}，从中提取角色名
        role = "viewer"
        for k, v in role_perms.items():
            if v is True:
                role = k
                break
        return {"user_id": user_id, "role": role}
    
    def record_usage(self, user_id: str, count: int = 1) -> Dict:
        """记录使用情况"""
        return self.pricing.record_usage(user_id, count)
    
    def get_user_info(self, user_id: str) -> Dict:
        """获取用户信息"""
        base = self.pricing.get_user_stats(user_id)
        if "error" in base:
            return base
        role_result = self._get_user_role(user_id)
        base["role"] = role_result.get("role", "viewer")
        return base
    
    def list_users(self, limit: int = 100) -> Dict:
        """列出用户"""
        return self.pricing.list_users(limit)
    
    def get_system_stats(self) -> Dict:
        """获取系统统计"""
        return {
            "total_users": len(self.pricing.users),
            "active_users": sum(1 for u in self.pricing.users.values() if u.get("is_active")),
            "tier_distribution": self._get_tier_distribution(),
            "total_revenue": self._calculate_revenue(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_tier_distribution(self) -> Dict:
        """获取层级分布"""
        distribution = {}
        for user in self.pricing.users.values():
            tier = user.get("tier", "free")
            distribution[tier] = distribution.get(tier, 0) + 1
        return distribution
    
    def _calculate_revenue(self) -> float:
        """计算收入"""
        total = 0
        for user in self.pricing.users.values():
            if user.get("is_active"):
                tier = user.get("tier", "free")
                tier_config = PricingTier.TIERS.get(tier, {})
                total += tier_config.get("price", 0)
        return round(total, 2)
    
    def export_data(self) -> Dict:
        """导出数据"""
        return {
            "users": self.pricing.users,
            "permissions": self.permissions.permissions,
            "billing_history": self.pricing.billing_history,
            "exported_at": datetime.now().isoformat()
        }
