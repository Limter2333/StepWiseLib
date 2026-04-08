"""
LLM Provider单元测试
"""

import pytest
from unittest.mock import Mock, patch
import os

from core.llm.llm_provider import (
    LLMProvider,
    LLMResponse,
    LLMWrapper,
    get_llm
)


class TestLLMResponse:
    """LLMResponse数据类测试"""

    def test_creation(self):
        """测试响应创建"""
        response = LLMResponse(
            content="Hello, world!",
            model="claude-3-sonnet",
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            },
            finish_reason="stop"
        )

        assert response.content == "Hello, world!"
        assert response.model == "claude-3-sonnet"
        assert response.usage["total_tokens"] == 15
        assert response.finish_reason == "stop"

    def test_usage_calculation(self):
        """测试token计算"""
        response = LLMResponse(
            content="test",
            model="gpt-4",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            },
            finish_reason="stop"
        )

        assert response.usage["prompt_tokens"] == 100
        assert response.usage["completion_tokens"] == 50


class TestLLMProviderEnum:
    """LLMProvider枚举测试"""

    def test_provider_values(self):
        """测试提供者枚举值"""
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.MINIMAX.value == "minimax"
        assert LLMProvider.LOCAL.value == "local"

    def test_provider_count(self):
        """测试提供者数量"""
        assert len(LLMProvider) == 4


class TestLLMWrapper:
    """LLM包装器测试"""

    def test_default_model_mapping(self):
        """测试默认模型映射"""
        wrapper = LLMWrapper.__new__(LLMWrapper)
        wrapper.provider = LLMProvider.ANTHROPIC
        wrapper.model = wrapper._get_default_model(LLMProvider.ANTHROPIC)
        assert wrapper.model == "claude-3-sonnet-20240229"

        wrapper.provider = LLMProvider.OPENAI
        wrapper.model = wrapper._get_default_model(LLMProvider.OPENAI)
        assert wrapper.model == "gpt-4"

    def test_init_with_anthropic_provider(self):
        """测试Anthropic Provider初始化"""
        with patch('core.llm.llm_provider.AnthropicLLM') as mock:
            mock.return_value = Mock()
            wrapper = LLMWrapper(provider=LLMProvider.ANTHROPIC)
            assert wrapper.provider == LLMProvider.ANTHROPIC
            mock.assert_called_once()

    def test_init_with_openai_provider(self):
        """测试OpenAI Provider初始化"""
        with patch('core.llm.llm_provider.OpenAILLM') as mock:
            mock.return_value = Mock()
            wrapper = LLMWrapper(provider=LLMProvider.OPENAI)
            assert wrapper.provider == LLMProvider.OPENAI
            mock.assert_called_once()

    def test_init_with_minimax_provider(self):
        """测试MiniMax Provider初始化"""
        with patch.dict(os.environ, {'ANTHROPIC_BASE_URL': 'https://api.minimaxi.com/anthropic'}):
            with patch('core.llm.llm_provider.AnthropicLLM') as mock:
                mock.return_value = Mock()
                wrapper = LLMWrapper(provider=LLMProvider.MINIMAX)
                assert wrapper.provider == LLMProvider.MINIMAX

    def test_wrapper_has_generate_method(self):
        """测试包装器有generate方法"""
        wrapper = LLMWrapper.__new__(LLMWrapper)
        wrapper.llm = Mock()
        wrapper.llm.generate = Mock(return_value=LLMResponse(
            content="ok",
            model="test",
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            finish_reason="stop"
        ))
        wrapper.provider = LLMProvider.ANTHROPIC
        wrapper.model = "test-model"

        # 验证generate方法是可调度的（async方法存在）
        assert hasattr(wrapper, 'generate')
        assert callable(wrapper.generate)


class TestGetLLM:
    """全局LLM获取测试"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        import core.llm.llm_provider as llm_module

        # 保存原实例
        original = llm_module._default_llm

        # 创建mock
        mock_instance = Mock(spec=LLMWrapper)
        llm_module._default_llm = mock_instance

        # 验证返回同一实例
        result = get_llm()
        assert result is mock_instance

        # 恢复
        llm_module._default_llm = original

    def test_creates_new_instance_if_none(self):
        """测试无实例时创建新实例"""
        import core.llm.llm_provider as llm_module

        # 保存原实例
        original = llm_module._default_llm
        llm_module._default_llm = None

        with patch('core.llm.llm_provider.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "anthropic"
            mock_settings.LLM_MODEL = "claude-3-sonnet-20240229"

            with patch('core.llm.llm_provider.LLMWrapper') as mock_wrapper:
                mock_instance = Mock()
                mock_wrapper.return_value = mock_instance

                result = get_llm()

                mock_wrapper.assert_called_once()

        # 恢复
        llm_module._default_llm = original


class TestLLMResponseEdgeCases:
    """LLMResponse边界情况测试"""

    def test_empty_content(self):
        """测试空内容"""
        response = LLMResponse(
            content="",
            model="claude-3-sonnet",
            usage={"prompt_tokens": 10, "completion_tokens": 0, "total_tokens": 10},
            finish_reason="stop"
        )
        assert response.content == ""

    def test_large_usage(self):
        """测试大token使用"""
        response = LLMResponse(
            content="long content...",
            model="claude-3-sonnet",
            usage={
                "prompt_tokens": 100000,
                "completion_tokens": 50000,
                "total_tokens": 150000
            },
            finish_reason="stop"
        )
        assert response.usage["total_tokens"] == 150000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
