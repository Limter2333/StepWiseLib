"""
Task Router 测试
================

测试任务路由器功能
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator.task_router import TaskRouter, task_router, TaskType


class TestTaskRouter:
    """Task Router测试"""

    def test_router_initialization(self):
        """测试路由器初始化"""
        router = TaskRouter()
        assert len(router.agents) >= 6
        assert "dev" in router.agents
        assert "test" in router.agents
        assert "doc" in router.agents
        assert "rag" in router.agents
        assert "pm" in router.agents
        assert "ops" in router.agents

    def test_route_code_keywords(self):
        """测试代码相关任务路由"""
        router = TaskRouter()

        # 代码关键词匹配
        assert router.route("写代码") == TaskType.CODE
        assert router.route("开发新功能") == TaskType.CODE  # "开发" 匹配

        # 英文关键词
        assert router.route("write code") == TaskType.CODE
        assert router.route("implement function") == TaskType.CODE
        assert router.route("generate code") == TaskType.CODE

    def test_route_doc_keywords(self):
        """测试文档相关任务路由"""
        router = TaskRouter()

        assert router.route("写文档") == TaskType.DOCUMENT
        assert router.route("生成README") == TaskType.DOCUMENT
        assert router.route("撰写技术方案") == TaskType.DOCUMENT
        assert router.route("write doc") == TaskType.DOCUMENT

    def test_route_test_keywords(self):
        """测试测试相关任务路由"""
        router = TaskRouter()

        assert router.route("单元测试") == TaskType.TEST  # "测试" 匹配
        assert router.route("写测试") == TaskType.TEST  # "测试" 匹配
        assert router.route("运行测试") == TaskType.TEST  # "测试" 匹配
        assert router.route("generate tests") == TaskType.TEST

    def test_route_knowledge_keywords(self):
        """测试知识库相关任务路由"""
        router = TaskRouter()

        assert router.route("搜索知识库") == TaskType.KNOWLEDGE  # "知识库" 匹配
        assert router.route("索引知识") == TaskType.KNOWLEDGE  # "索引" 匹配
        assert router.route("检索知识") == TaskType.KNOWLEDGE  # "检索" 匹配
        assert router.route("search knowledge") == TaskType.KNOWLEDGE

    def test_route_project_keywords(self):
        """测试项目管理相关任务路由"""
        router = TaskRouter()

        assert router.route("项目进度") == TaskType.PROJECT  # "项目" 匹配
        assert router.route("创建任务") == TaskType.PROJECT  # "任务" 匹配
        assert router.route("milestone计划") == TaskType.PROJECT  # "milestone" 匹配
        assert router.route("track task") == TaskType.PROJECT

    def test_route_conversation_keywords(self):
        """测试对话相关任务路由"""
        router = TaskRouter()

        assert router.route("开始对话") == TaskType.CONVERSATION  # "对话" 匹配
        assert router.route("发送消息") == TaskType.CONVERSATION  # "消息" 匹配
        assert router.route("chat with me") == TaskType.CONVERSATION
        assert router.route("session对话") == TaskType.CONVERSATION  # "session" 匹配

    def test_route_ops_keywords(self):
        """测试运维相关任务路由"""
        router = TaskRouter()

        assert router.route("部署应用到生产") == TaskType.OPS
        assert router.route("监控系统状态") == TaskType.OPS
        assert router.route("运维管理") == TaskType.OPS
        assert router.route("基础设施配置") == TaskType.OPS
        assert router.route("deploy to production") == TaskType.OPS
        assert router.route("monitoring") == TaskType.OPS

    def test_route_default(self):
        """测试默认路由"""
        router = TaskRouter()
        assert router.route("随便问点什么") == TaskType.OTHER
        assert router.route("hello world") == TaskType.OTHER

    def test_get_agent_for_task(self):
        """测试获取任务的Agent"""
        router = TaskRouter()

        assert router.get_agent_for_task(TaskType.CODE) is not None
        assert router.get_agent_for_task(TaskType.DOCUMENT) is not None
        assert router.get_agent_for_task(TaskType.TEST) is not None
        assert router.get_agent_for_task(TaskType.KNOWLEDGE) is not None
        assert router.get_agent_for_task(TaskType.PROJECT) is not None
        assert router.get_agent_for_task(TaskType.CONVERSATION) is not None
        assert router.get_agent_for_task(TaskType.OPS) is not None
        assert router.get_agent_for_task(TaskType.OTHER) is None

    def test_list_agents(self):
        """测试列出所有Agent"""
        agents = task_router.list_agents()

        assert "dev" in agents
        assert "doc" in agents
        assert "test" in agents
        assert "rag" in agents
        assert "pm" in agents
        assert "ops" in agents

        # 验证每个agent都有name
        for name, caps in agents.items():
            assert "name" in caps

    @pytest.mark.asyncio
    async def test_execute_code_task(self):
        """测试执行代码任务"""
        result = await task_router.execute_task("Write a hello world function")

        # 由于没有真实的LLM，可能返回错误或模拟结果
        assert "success" in result or "error" in result
        assert "task_type" in result
        assert result["task_type"] == TaskType.CODE.value

    @pytest.mark.asyncio
    async def test_execute_ops_task(self):
        """测试执行运维任务"""
        result = await task_router.execute_task("Deploy to production")

        # Ops任务应该被路由
        assert result["task_type"] == TaskType.OPS.value

    def test_task_type_enum_values(self):
        """测试任务类型枚举值"""
        assert TaskType.CODE.value == "code"
        assert TaskType.DOCUMENT.value == "document"
        assert TaskType.TEST.value == "test"
        assert TaskType.KNOWLEDGE.value == "knowledge"
        assert TaskType.PROJECT.value == "project"
        assert TaskType.CONVERSATION.value == "conversation"
        assert TaskType.OPS.value == "ops"
        assert TaskType.OTHER.value == "other"


class TestTaskTypeDistribution:
    """测试任务类型分布"""

    def test_all_task_types_have_routing(self):
        """测试所有任务类型都有路由映射"""
        router = TaskRouter()

        for task_type in TaskType:
            agent = router.get_agent_for_task(task_type)
            if task_type == TaskType.OTHER:
                assert agent is None
            else:
                assert agent is not None

    def test_all_agents_have_capabilities(self):
        """测试所有Agent都有能力定义"""
        agents = task_router.list_agents()

        # 所有agent至少有name字段
        for name, caps in agents.items():
            assert "name" in caps, f"Agent {name} missing name"


class TestTaskRouterEdgeCases:
    """Task Router边界情况测试"""

    def test_empty_string_routing(self):
        """测试空字符串路由"""
        router = TaskRouter()
        result = router.route("")
        assert result == TaskType.OTHER

    def test_whitespace_only_routing(self):
        """测试纯空白字符路由"""
        router = TaskRouter()
        result = router.route("   ")
        assert result == TaskType.OTHER

    def test_mixed_language_routing(self):
        """测试中英混合路由"""
        router = TaskRouter()
        # 代码相关的中英混合
        result = router.route("write 代码")
        assert result == TaskType.CODE

    def test_very_long_task_routing(self):
        """测试超长任务描述路由"""
        router = TaskRouter()
        long_desc = "帮我" + "写代码" * 100
        result = router.route(long_desc)
        assert result == TaskType.CODE

    def test_case_sensitivity(self):
        """测试大小写敏感性"""
        router = TaskRouter()
        # 英文应该不区分大小写
        assert router.route("WRITE CODE") == TaskType.CODE
        assert router.route("write code") == TaskType.CODE
        assert router.route("Write Code") == TaskType.CODE

    def test_special_characters_routing(self):
        """测试特殊字符路由"""
        router = TaskRouter()
        result = router.route("!!!写代码###")
        assert result == TaskType.CODE

    def test_numbers_in_description(self):
        """测试描述中带数字"""
        router = TaskRouter()
        result = router.route("为功能123写测试")
        assert result == TaskType.TEST

    def test_punctuation_routing(self):
        """测试标点符号路由"""
        router = TaskRouter()
        result = router.route("写代码？")
        assert result == TaskType.CODE

    def test_ambiguous_routing(self):
        """测试模糊任务路由"""
        router = TaskRouter()
        # "帮我" 不明确，应该路由到 OTHER 或第一个匹配的
        result = router.route("帮我")
        assert isinstance(result, TaskType)

    def test_route_returns_task_type(self):
        """测试路由返回正确类型"""
        router = TaskRouter()
        result = router.route("写代码")
        assert isinstance(result, TaskType)
        assert result.value == "code"

    def test_get_agent_with_nonexistent_task_type(self):
        """测试获取不存在任务类型的Agent"""
        router = TaskRouter()
        # TaskType.OTHER不应该有Agent
        agent = router.get_agent_for_task(TaskType.OTHER)
        assert agent is None


class TestTaskRouterEdgeCases:
    """TaskRouter边界情况测试"""

    def test_route_none_input(self):
        """测试None输入路由"""
        router = TaskRouter()
        result = router.route(None)
        assert result == TaskType.OTHER

    def test_route_empty_string(self):
        """测试空字符串路由"""
        router = TaskRouter()
        result = router.route("")
        assert result == TaskType.OTHER

    def test_route_whitespace_only(self):
        """测试仅空格输入"""
        router = TaskRouter()
        result = router.route("   ")
        assert result == TaskType.OTHER

    def test_route_very_long_description(self):
        """测试超长任务描述"""
        router = TaskRouter()
        long_desc = "帮我写代码" + "啊" * 10000
        result = router.route(long_desc)
        assert result == TaskType.CODE

    def test_route_pure_special_characters(self):
        """测试纯特殊字符"""
        router = TaskRouter()
        result = router.route("!@#$%^&*()")
        assert result == TaskType.OTHER

    def test_route_mixed_chinese_english(self):
        """测试中英混合"""
        router = TaskRouter()
        result = router.route("帮我code这个function")
        assert result == TaskType.CODE

    def test_route_no_matching_keywords(self):
        """测试无匹配关键词"""
        router = TaskRouter()
        result = router.route("asdfghjkl qwertyuio")
        assert result == TaskType.OTHER

    def test_route_simultaneous_keywords(self):
        """测试同时匹配多个类别"""
        router = TaskRouter()
        # 同时包含 code 和 test 关键词
        result = router.route("帮我写代码并写测试")
        assert result in [TaskType.CODE, TaskType.TEST]
        assert result is not TaskType.OTHER

    def test_route_chinese_only(self):
        """测试纯中文无关键词"""
        router = TaskRouter()
        result = router.route("今天天气真好")
        assert result == TaskType.OTHER

    def test_route_single_character(self):
        """测试单字符输入"""
        router = TaskRouter()
        result = router.route("a")
        assert result == TaskType.OTHER

    def test_route_numeric_string(self):
        """测试纯数字字符串"""
        router = TaskRouter()
        result = router.route("12345")
        assert result == TaskType.OTHER

    def test_get_agent_for_all_task_types(self):
        """测试所有TaskType获取Agent"""
        router = TaskRouter()
        for task_type in TaskType:
            agent = router.get_agent_for_task(task_type)
            if task_type == TaskType.OTHER:
                assert agent is None
            else:
                assert agent is not None

    def test_route_unicode_injection(self):
        """测试Unicode注入"""
        router = TaskRouter()
        result = router.route("\u0000\u2027\u0000")
        assert result == TaskType.OTHER

    def test_route_case_variations(self):
        """测试大小写变体"""
        router = TaskRouter()
        assert router.route("CODE") == TaskType.CODE
        assert router.route("Code") == TaskType.CODE
        assert router.route("cOdE") == TaskType.CODE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
