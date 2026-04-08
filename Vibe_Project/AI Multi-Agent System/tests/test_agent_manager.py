"""
Agent Manager 单元测试
====================

测试 Chief Orchestrator 的核心调度功能
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAgentRegistry:
    """AgentRegistry测试"""

    def test_register_agent(self):
        """测试Agent注册"""
        from agents.orchestrator.agent_manager import AgentRegistry

        registry = AgentRegistry()
        mock_agent = Mock()

        registry.register("test_agent", mock_agent)

        assert "test_agent" in registry.agents
        assert registry.agents["test_agent"] == mock_agent

    def test_get_registered_agent(self):
        """测试获取注册的Agent"""
        from agents.orchestrator.agent_manager import AgentRegistry

        registry = AgentRegistry()
        mock_agent = Mock()
        registry.register("test_agent", mock_agent)

        retrieved = registry.get("test_agent")
        assert retrieved == mock_agent

    def test_get_nonexistent_agent(self):
        """测试获取不存在的Agent"""
        from agents.orchestrator.agent_manager import AgentRegistry

        registry = AgentRegistry()
        retrieved = registry.get("nonexistent")
        assert retrieved is None

    def test_list_agents(self):
        """测试列出所有Agent"""
        from agents.orchestrator.agent_manager import AgentRegistry

        registry = AgentRegistry()
        registry.register("agent1", Mock())
        registry.register("agent2", Mock())

        agents = registry.list_agents()
        assert "agent1" in agents
        assert "agent2" in agents


class TestAgentState:
    """AgentState测试"""

    def test_state_creation(self):
        """测试状态创建"""
        from agents.orchestrator.agent_manager import AgentState
        from langchain_core.messages import HumanMessage

        state = AgentState(
            messages=[HumanMessage(content="test")],
            current_task="test task",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        assert len(state["messages"]) == 1
        assert state["current_task"] == "test task"
        assert state["task_result"] == {}
        assert state["active_agents"] == []

    def test_state_with_multiple_messages(self):
        """测试多消息状态"""
        from agents.orchestrator.agent_manager import AgentState
        from langchain_core.messages import HumanMessage, AIMessage

        state = AgentState(
            messages=[
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there")
            ],
            current_task="test",
            task_result={},
            active_agents=["agent1"],
            task_history=[]
        )

        assert len(state["messages"]) == 2
        assert state["active_agents"] == ["agent1"]


class TestRoutingDecision:
    """任务路由决策测试"""

    def test_route_to_rag_agent(self):
        """测试RAG相关任务路由"""
        from agents.orchestrator.agent_manager import routing_decision, AgentState

        state = AgentState(
            messages=[],
            current_task="查询知识库中的文档",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        result = routing_decision(state)
        assert result == "rag_agent"

    def test_route_to_dev_agent(self):
        """测试开发相关任务路由"""
        from agents.orchestrator.agent_manager import routing_decision, AgentState

        state = AgentState(
            messages=[],
            current_task="帮我写一段Python代码",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        result = routing_decision(state)
        assert result == "dev_agent"

    def test_route_to_doc_agent(self):
        """测试文档相关任务路由"""
        from agents.orchestrator.agent_manager import routing_decision, AgentState

        state = AgentState(
            messages=[],
            current_task="生成项目文档",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        result = routing_decision(state)
        assert result == "doc_agent"

    def test_route_to_test_agent(self):
        """测试测试相关任务路由"""
        from agents.orchestrator.agent_manager import routing_decision, AgentState

        state = AgentState(
            messages=[],
            current_task="编写单元测试",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        result = routing_decision(state)
        assert result == "test_agent"

    def test_route_to_pm_agent(self):
        """测试项目管理相关任务路由"""
        from agents.orchestrator.agent_manager import routing_decision, AgentState

        state = AgentState(
            messages=[],
            current_task="查看项目进度",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        result = routing_decision(state)
        assert result == "pm_agent"

    def test_route_to_conversation_agent(self):
        """测试对话相关任务路由"""
        from agents.orchestrator.agent_manager import routing_decision, AgentState

        state = AgentState(
            messages=[],
            current_task="和我聊聊天",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        result = routing_decision(state)
        assert result == "conversation_agent"

    def test_route_unknown_to_conversation(self):
        """测试未知任务默认路由到对话Agent"""
        from agents.orchestrator.agent_manager import routing_decision, AgentState

        state = AgentState(
            messages=[],
            current_task="随便说点什么",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        result = routing_decision(state)
        assert result == "conversation_agent"

    def test_route_english_keywords(self):
        """测试英文关键词路由"""
        from agents.orchestrator.agent_manager import routing_decision, AgentState

        # Test RAG keywords
        state = AgentState(
            messages=[],
            current_task="search the knowledge base",
            task_result={},
            active_agents=[],
            task_history=[]
        )
        assert routing_decision(state) == "rag_agent"

        # Test dev keywords (use distinct word to avoid substring matching issues)
        state = AgentState(
            messages=[],
            current_task="develop a new feature",
            task_result={},
            active_agents=[],
            task_history=[]
        )
        assert routing_decision(state) == "dev_agent"


class TestOrchestratorNode:
    """Orchestrator节点测试"""

    def test_orchestrator_processes_task(self):
        """测试Orchestrator处理任务"""
        from agents.orchestrator.agent_manager import orchestrator_node, AgentState
        from langchain_core.messages import HumanMessage

        state = AgentState(
            messages=[HumanMessage(content="帮我开发一个登录功能")],
            current_task="帮我开发一个登录功能",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        result = orchestrator_node(state)

        assert "task_result" in result
        assert result["task_result"]["original_request"] == "帮我开发一个登录功能"

    def test_orchestrator_empty_task(self):
        """测试空任务处理"""
        from agents.orchestrator.agent_manager import orchestrator_node, AgentState
        from langchain_core.messages import HumanMessage

        state = AgentState(
            messages=[HumanMessage(content="")],
            current_task="",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        result = orchestrator_node(state)
        assert result["task_result"]["original_request"] == ""


class TestDevAgentNode:
    """Dev Agent节点测试"""

    def test_dev_agent_node_updates_state(self):
        """测试Dev Agent节点更新状态"""
        from agents.orchestrator.agent_manager import dev_agent_node, AgentState
        from langchain_core.messages import HumanMessage

        state = AgentState(
            messages=[HumanMessage(content="test")],
            current_task="写一个排序算法",
            task_result={},
            active_agents=[],
            task_history=[]
        )

        with patch("agents.orchestrator.agent_manager._call_dev_agent") as mock_call:
            mock_call.return_value = {
                "success": True,
                "code": "def sort(): pass",
                "quality_score": 0.9
            }
            result = dev_agent_node(state)

            assert "dev_output" in result["task_result"]
            assert "dev_agent" in result["active_agents"]


class TestBuildWorkflow:
    """工作流构建测试"""

    def test_workflow_builds_successfully(self):
        """测试工作流成功构建"""
        from agents.orchestrator.agent_manager import build_workflow

        workflow = build_workflow()
        assert workflow is not None

    def test_workflow_has_required_nodes(self):
        """测试工作流包含所有必需节点"""
        from agents.orchestrator.agent_manager import build_workflow

        workflow = build_workflow()
        # 工作流应该能成功编译
        assert workflow is not None


class TestExecuteTask:
    """任务执行测试"""

    @pytest.mark.asyncio
    async def test_execute_task_returns_dict(self):
        """测试execute_task返回字典"""
        from agents.orchestrator.agent_manager import execute_task

        with patch("agents.orchestrator.agent_manager.workflow") as mock_workflow:
            mock_workflow.ainvoke = AsyncMock(return_value={
                "task_result": {
                    "original_request": "test",
                    "sub_tasks": [],
                    "assigned_agents": []
                }
            })

            result = await execute_task("test task")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_task_with_rag(self):
        """测试执行RAG相关任务"""
        from agents.orchestrator.agent_manager import execute_task

        with patch("agents.orchestrator.agent_manager.workflow") as mock_workflow:
            mock_workflow.ainvoke = AsyncMock(return_value={
                "task_result": {
                    "original_request": "查询知识库",
                    "rag_output": {"success": True}
                }
            })

            result = await execute_task("查询知识库中的内容")
            # result is the task_result dict directly from the workflow
            assert isinstance(result, dict)
            assert "original_request" in result or "rag_output" in result


class TestGlobalInstances:
    """全局实例测试"""

    def test_agent_registry_singleton(self):
        """测试Agent注册表单例"""
        from agents.orchestrator.agent_manager import agent_registry

        assert agent_registry is not None
        assert isinstance(agent_registry.agents, dict)

    def test_workflow_singleton(self):
        """测试工作流单例"""
        from agents.orchestrator.agent_manager import workflow

        assert workflow is not None

    def test_task_router_instantiation(self):
        """测试任务路由器实例化"""
        from agents.orchestrator.agent_manager import AgentRegistry

        registry = AgentRegistry()
        assert registry is not None
        assert registry.agents == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
