"""
Orchestrator Tests - Task Router and Related Components
"""

import pytest
from agents.orchestrator.task_router import TaskType, TaskRouter
from agents.orchestrator.shared_context import get_shared_context, ContextScope


class TestTaskType:
    """测试任务类型枚举"""

    def test_task_type_values(self):
        assert TaskType.CODE.value == "code"
        assert TaskType.DOCUMENT.value == "document"
        assert TaskType.TEST.value == "test"
        assert TaskType.KNOWLEDGE.value == "knowledge"
        assert TaskType.PROJECT.value == "project"
        assert TaskType.CONVERSATION.value == "conversation"
        assert TaskType.OPS.value == "ops"
        assert TaskType.FRONTEND.value == "frontend"
        assert TaskType.BACKEND.value == "backend"
        assert TaskType.CODE_REVIEW.value == "code_review"
        assert TaskType.UI_DESIGN.value == "ui_design"
        assert TaskType.PRODUCT.value == "product"
        assert TaskType.REALITY_CHECK.value == "reality_check"
        assert TaskType.API_TEST.value == "api_test"
        assert TaskType.WORKFLOW.value == "workflow"
        assert TaskType.OTHER.value == "other"

    def test_task_type_count(self):
        # Original 6 + 9 new + 1 OTHER = 16 types
        assert len(TaskType) == 16


class TestContextScope:
    """测试上下文作用域枚举"""

    def test_scope_values(self):
        assert ContextScope.GLOBAL.value == "global"
        assert ContextScope.SESSION.value == "session"
        assert ContextScope.TASK.value == "task"
        assert ContextScope.AGENT.value == "agent"

    def test_scope_count(self):
        assert len(ContextScope) == 4


class TestTaskRouter:
    """测试任务路由器"""

    def test_router_creation(self):
        router = TaskRouter()
        assert router is not None

    def test_router_has_agents(self):
        router = TaskRouter()
        assert len(router.agents) > 0
        assert "dev" in router.agents
        assert "test" in router.agents
        assert "doc" in router.agents


class TestSharedContext:
    """测试共享上下文"""

    def test_get_shared_context(self):
        ctx = get_shared_context()
        assert ctx is not None

    def test_context_set_and_get(self):
        ctx = get_shared_context()
        test_key = f"test_key_{id(self)}"
        ctx.set(test_key, "test_value", scope=ContextScope.GLOBAL)
        value = ctx.get(test_key, scope=ContextScope.GLOBAL)
        assert value == "test_value"

    def test_context_stats(self):
        ctx = get_shared_context()
        stats = ctx.get_stats()
        assert stats is not None
        assert "total_entries" in stats or "total_keys" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
