"""权限模块单元测试。"""
import pytest
from harness.permissions import PermissionDecision, PermissionPolicy
from harness.tools.base import tool, ToolSpec


class TestPermissionPolicy:
    """PermissionPolicy 测试。"""
    
    def test_safe_tool_allowed(self):
        """测试安全工具自动允许。"""
        policy = PermissionPolicy()
        
        @tool(permission="safe")
        def safe_tool() -> str:
            return "ok"
        
        decision = policy.check(safe_tool)
        assert decision == PermissionDecision.ALLOW
    
    def test_admin_tool_confirm(self):
        """测试管理员工具需要确认。"""
        policy = PermissionPolicy()
        
        @tool(permission="admin")
        def admin_tool() -> str:
            return "ok"
        
        decision = policy.check(admin_tool)
        assert decision == PermissionDecision.CONFIRM
    
    def test_explicit_rule(self):
        """测试显式规则覆盖。"""
        policy = PermissionPolicy(rules={"my_tool": "deny"})
        
        @tool(permission="safe")
        def my_tool() -> str:
            return "ok"
        
        decision = policy.check(my_tool)
        assert decision == PermissionDecision.DENY
    
    def test_requires_confirm(self):
        """测试 requires_confirm 标志。"""
        policy = PermissionPolicy()
        
        @tool(requires_confirm=True)
        def confirm_tool() -> str:
            return "ok"
        
        decision = policy.check(confirm_tool)
        assert decision == PermissionDecision.CONFIRM
    
    def test_add_rule(self):
        """测试添加规则。"""
        policy = PermissionPolicy()
        policy.add_rule("tool1", "allow")
        
        assert policy.list_rules().get("tool1") == "allow"
    
    def test_remove_rule(self):
        """测试移除规则。"""
        policy = PermissionPolicy()
        policy.add_rule("tool1", "allow")
        policy.remove_rule("tool1")
        
        assert "tool1" not in policy.list_rules()
