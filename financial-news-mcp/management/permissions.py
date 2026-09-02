#!/usr/bin/env python3
"""
权限控制模块
支持细粒度权限管理
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("mcp-permissions")


class PermissionController:
    """权限控制器"""
    
    def __init__(self):
        self.permissions: Dict[str, Dict] = {}
        self._load_permissions()
    
    def _load_permissions(self):
        """加载权限配置"""
        try:
            import os
            perm_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'permissions.json')
            if os.path.exists(perm_file):
                with open(perm_file, 'r', encoding='utf-8') as f:
                    self.permissions = json.load(f)
        except Exception as e:
            logger.warning(f"加载权限配置失败: {e}")
    
    def save_permissions(self):
        """保存权限配置"""
        try:
            import os
            perm_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'permissions.json')
            os.makedirs(os.path.dirname(perm_file), exist_ok=True)
            with open(perm_file, 'w', encoding='utf-8') as f:
                json.dump(self.permissions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存权限配置失败: {e}")
    
    def check_permission(self, user_id: str, resource: str, action: str) -> Dict:
        """检查权限"""
        # 默认允许管理员
        if user_id.startswith("admin_"):
            return {"allowed": True, "reason": "管理员权限"}
        
        # 检查用户特定权限
        user_perms = self.permissions.get(user_id, {})
        
        # 检查资源权限
        resource_perms = user_perms.get(resource, {})
        
        # 检查动作权限
        if action in resource_perms:
            return {
                "allowed": resource_perms[action],
                "resource": resource,
                "action": action,
                "permission_level": "explicit"
            }
        
        # 检查通配符权限
        if "*" in resource_perms:
            return {
                "allowed": resource_perms["*"],
                "resource": resource,
                "action": action,
                "permission_level": "wildcard"
            }
        
        # 默认拒绝
        return {
            "allowed": False,
            "resource": resource,
            "action": action,
            "permission_level": "denied"
        }
    
    def grant_permission(self, user_id: str, resource: str, action: str, granted: bool = True):
        """授予权限"""
        if user_id not in self.permissions:
            self.permissions[user_id] = {}
        
        if resource not in self.permissions[user_id]:
            self.permissions[user_id][resource] = {}
        
        self.permissions[user_id][resource][action] = granted
        self.save_permissions()
        
        return {
            "status": "granted",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "granted": granted
        }
    
    def revoke_permission(self, user_id: str, resource: str, action: str):
        """撤销权限"""
        if user_id in self.permissions:
            if resource in self.permissions[user_id]:
                if action in self.permissions[user_id][resource]:
                    del self.permissions[user_id][resource][action]
                    self.save_permissions()
                    
                    return {
                        "status": "revoked",
                        "user_id": user_id,
                        "resource": resource,
                        "action": action
                    }
        
        return {"status": "not_found"}
    
    def get_user_permissions(self, user_id: str) -> Dict:
        """获取用户所有权限"""
        return self.permissions.get(user_id, {})
    
    def batch_check(self, user_id: str, checks: List[Dict]) -> List[Dict]:
        """批量检查权限"""
        results = []
        for check in checks:
            result = self.check_permission(
                user_id,
                check.get("resource"),
                check.get("action")
            )
            results.append({
                **check,
                **result
            })
        return results


class RoleManager:
    """角色管理器"""
    
    ROLES = {
        "viewer": {
            "name": "观察者",
            "permissions": {
                "news": ["read"],
                "sentiment": ["read"],
                "predict": ["read_basic"],
                "validate": ["read"]
            }
        },
        "analyst": {
            "name": "分析师",
            "permissions": {
                "news": ["read", "collect"],
                "sentiment": ["read", "analyze"],
                "predict": ["read", "predict"],
                "validate": ["read", "validate"],
                "advice": ["read"]
            }
        },
        "trader": {
            "name": "交易员",
            "permissions": {
                "news": ["read", "collect"],
                "sentiment": ["read", "analyze"],
                "predict": ["read", "predict"],
                "validate": ["read", "validate"],
                "advice": ["read", "generate"],
                "portfolio": ["read", "manage"]
            }
        },
        "admin": {
            "name": "管理员",
            "permissions": {
                "all": ["*"]
            }
        }
    }
    
    @classmethod
    def get_role(cls, role_name: str) -> Optional[Dict]:
        """获取角色定义"""
        return cls.ROLES.get(role_name)
    
    @classmethod
    def list_roles(cls) -> List[Dict]:
        """列出所有角色"""
        return [
            {
                "name": name,
                "display_name": config["name"],
                "permissions": list(config["permissions"].keys())
            }
            for name, config in cls.ROLES.items()
        ]
    
    @classmethod
    def check_role_permission(cls, role_name: str, resource: str, action: str) -> Dict:
        """检查角色权限"""
        role = cls.ROLES.get(role_name)
        if not role:
            return {"allowed": False, "reason": "角色不存在"}
        
        permissions = role["permissions"]
        
        # 检查通配符
        if "all" in permissions and "*" in permissions["all"]:
            return {"allowed": True, "role": role_name, "level": "admin"}
        
        # 检查具体权限 - 权限值是列表格式: {"news": ["read", "collect"]}
        resource_perms = permissions.get(resource, [])
        
        if isinstance(resource_perms, list):
            allowed = action in resource_perms
            return {
                "allowed": allowed,
                "role": role_name,
                "resource": resource,
                "action": action,
                "permission_level": "multiple"
            }
        elif isinstance(resource_perms, dict):
            allowed = action in resource_perms
            perm_value = resource_perms[action]
            return {
                "allowed": allowed,
                "role": role_name,
                "resource": resource,
                "action": action,
                "permission_level": perm_value if not isinstance(perm_value, list) else "multiple"
            }
        
        return {
            "allowed": False,
            "role": role_name,
            "resource": resource,
            "action": action,
            "reason": "未授权"
        }
