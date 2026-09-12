from enum import Enum
from typing import Optional
from harness.tools.base import ToolSpec


class PermissionDecision(Enum):
    """权限决策枚举。"""
    ALLOW = "allow"      # 自动允许
    CONFIRM = "confirm"  # 需要用户确认
    DENY = "deny"        # 拒绝执行


class PermissionPolicy:
    """权限策略管理。
    
    设计意图：统一管理工具的权限控制，支持：
    - 基于工具名的规则配置
    - 基于工具权限级别的默认策略
    - 自定义权限检查逻辑
    """
    
    def __init__(self, rules: Optional[dict[str, str]] = None):
        """初始化权限策略。
        
        Args:
            rules: 工具名 -> 权限级别的映射
                   支持的值：allow, confirm, deny
        """
        self._rules = rules or {}
    
    def check(self, spec: ToolSpec) -> PermissionDecision:
        """检查工具调用权限。
        
        优先级：
        1. 显式配置的规则（_rules）
        2. 工具自身的权限级别（spec.permission_level）
        3. 需要确认的工具列表（spec.requires_confirm）
        
        Returns:
            PermissionDecision 枚举值
        """
        # 优先检查显式规则
        if spec.name in self._rules:
            level = self._rules[spec.name].lower()
            if level == "allow":
                return PermissionDecision.ALLOW
            elif level == "confirm":
                return PermissionDecision.CONFIRM
            elif level == "deny":
                return PermissionDecision.DENY
        
        # 检查工具是否需要确认
        if spec.requires_confirm:
            return PermissionDecision.CONFIRM
        
        # 根据权限级别返回默认决策
        level = spec.permission_level.lower()
        if level == "safe":
            return PermissionDecision.ALLOW
        elif level == "confirm":
            return PermissionDecision.CONFIRM
        elif level == "admin":
            return PermissionDecision.CONFIRM
        
        # 默认需要确认
        return PermissionDecision.CONFIRM
    
    def add_rule(self, tool_name: str, level: str) -> None:
        """添加或更新工具权限规则。"""
        self._rules[tool_name] = level.lower()
    
    def remove_rule(self, tool_name: str) -> None:
        """移除工具权限规则。"""
        self._rules.pop(tool_name, None)
    
    def list_rules(self) -> dict[str, str]:
        """返回当前所有权限规则。"""
        return self._rules.copy()
