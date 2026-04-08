"""
LLM集成测试 - 实际API调用
========================

【目的】
验证LLM实际调用功能，不是mock测试
当API Key配置正确时运行，否则跳过

【运行方式】
- 有API Key: pytest tests/test_llm_integration.py -v
- 无API Key: 自动跳过所有测试
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def is_api_key_configured():
    """检查是否配置了有效的API Key"""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    return bool(api_key and api_key != "your_minimax_api_key_here")


# 只有配置了API Key才运行这些测试
pytestmark = pytest.mark.skipif(
    not is_api_key_configured(),
    reason="ANTHROPIC_API_KEY not configured"
)


class TestLLMIntegration:
    """LLM实际调用集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前初始化"""
        from core.llm.llm_provider import get_llm, LLMWrapper, LLMProvider
        self.llm_provider = get_llm()
        yield
        # 清理全局实例以便下一个测试独立
        import core.llm.llm_provider as llm_module
        llm_module._default_llm = None

    @pytest.mark.asyncio
    async def test_simple_generate(self):
        """测试简单生成调用"""
        response = await self.llm_provider.generate(
            prompt="请回复: 1+1等于几?",
            system_prompt="你是一个简洁的数学助手，只回答数字。"
        )

        assert response.content is not None
        assert len(response.content) > 0
        assert response.model is not None
        assert response.usage is not None
        assert "total_tokens" in response.usage

    @pytest.mark.asyncio
    async def test_chat_messages(self):
        """测试对话消息格式"""
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
            {"role": "user", "content": "今天天气怎么样？"}
        ]

        response = await self.llm_provider.chat(messages=messages)

        assert response.content is not None
        assert len(response.content) > 0
        assert response.usage["total_tokens"] > 0

    @pytest.mark.asyncio
    async def test_token_tracking(self):
        """测试Token追踪"""
        from core.token_manager import token_manager

        # 记录初始状态
        initial_stats = token_manager.get_stats()
        initial_total = initial_stats.get("total_tokens", 0)

        # 执行一次调用
        response = await self.llm_provider.generate(
            prompt="测试token追踪",
            system_prompt="简洁回复"
        )

        # 验证token被追踪
        current_stats = token_manager.get_stats()
        current_total = current_stats.get("total_tokens", 0)

        # 验证token增加
        assert current_total >= initial_total + response.usage["total_tokens"]

    @pytest.mark.asyncio
    async def test_chinese_content(self):
        """测试中文内容处理"""
        response = await self.llm_provider.generate(
            prompt="用一句话介绍Python编程语言",
            system_prompt="你是一个专业的技术文档助手。"
        )

        assert response.content is not None
        assert len(response.content) > 0
        # 验证能处理中文
        assert any('\u4e00' <= c <= '\u9fff' for c in response.content) or len(response.content) > 5

    @pytest.mark.asyncio
    async def test_empty_system_prompt(self):
        """测试空system prompt"""
        response = await self.llm_provider.generate(
            prompt="3+3等于几?",
            system_prompt=None
        )

        assert response.content is not None
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_temperature_parameter(self):
        """测试temperature参数"""
        # 相同问题，不同temperature
        prompt = "给我一个随机数种子:"

        response1 = await self.llm_provider.generate(
            prompt=prompt,
            temperature=0.1
        )

        response2 = await self.llm_provider.generate(
            prompt=prompt,
            temperature=1.0
        )

        # 两个响应都应该有效
        assert response1.content is not None
        assert response2.content is not None

    @pytest.mark.asyncio
    async def test_max_tokens_parameter(self):
        """测试max_tokens参数"""
        response = await self.llm_provider.generate(
            prompt="写一个200字的自我介绍",
            max_tokens=50  # 限制很短
        )

        # 响应应该被截断或接近限制
        assert response.content is not None
        # completion tokens应该不超过max_tokens + 一些buffer
        assert response.usage["completion_tokens"] <= 60


class TestMiniMaxProvider:
    """MiniMax特定提供商的测试"""

    @pytest.fixture(autouse=True)
    def setup_minimax(self):
        """设置MiniMax provider"""
        # 检查是否配置了MiniMax
        base_url = os.getenv("ANTHROPIC_BASE_URL", "")
        if "minimaxi" not in base_url:
            pytest.skip("MiniMax provider not configured")

        from core.llm.llm_provider import LLMWrapper, LLMProvider
        import core.llm.llm_provider as llm_module
        llm_module._default_llm = None

        self.llm = LLMWrapper(provider=LLMProvider.MINIMAX)
        yield
        llm_module._default_llm = None

    @pytest.mark.asyncio
    async def test_minimax_call(self):
        """测试MiniMax API调用"""
        response = await self.llm.generate(
            prompt="简短回复: 今天是你的生日吗?",
            system_prompt="你是MiniMax助手，简洁回答。"
        )

        assert response.content is not None
        assert len(response.content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
