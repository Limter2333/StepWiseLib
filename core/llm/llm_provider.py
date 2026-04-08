"""
LLM调用模块
============

支持多种LLM provider的集成
"""

from typing import Optional, Dict, Any, List, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import os

# 导入配置
from config.settings import settings
# 导入Token管理器
from core.token_manager import token_manager


class LLMProvider(Enum):
    """LLM提供者枚举"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    MINIMAX = "minimax"
    LOCAL = "local"


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: str


class BaseLLM(ABC):
    """LLM基类

    【设计模式】策略模式
    - 不同provider实现统一接口
    - 便于切换和扩展
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """生成响应"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """对话"""
        pass


class AnthropicLLM(BaseLLM):
    """Anthropic Claude集成

    【学习要点】Anthropic API
    - 使用Claude模型
    - 支持system prompt
    - 需要API key
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-sonnet-20240229",
        base_url: Optional[str] = None
    ):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("请安装anthropic: pip install anthropic")

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")

        if self.base_url:
            self.client = Anthropic(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = Anthropic(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """生成响应（异步调用，避免阻塞事件循环）"""
        import asyncio

        def _sync_call():
            return self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )

        # 在线程池中执行同步SDK调用，避免阻塞事件循环
        response = await asyncio.to_thread(_sync_call)

        # 处理思考模型（如 MiniMax M2.7）的响应格式
        content_text = ""
        for block in response.content:
            if hasattr(block, 'text') and block.text:
                content_text = block.text
                break

        return LLMResponse(
            content=content_text,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            finish_reason=response.stop_reason
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """对话（异步调用，避免阻塞事件循环）"""
        import asyncio

        # 转换消息格式
        anthropic_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                system_prompt = msg.get("content")
            else:
                anthropic_messages.append({
                    "role": "assistant" if role == "assistant" else "user",
                    "content": msg.get("content", "")
                })

        def _sync_call():
            return self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
                system=system_prompt,
                messages=anthropic_messages,
                **kwargs
            )

        # 在线程池中执行同步SDK调用，避免阻塞事件循环
        response = await asyncio.to_thread(_sync_call)

        # 处理思考模型（如 MiniMax M2.7）的响应格式
        content_text = ""
        for block in response.content:
            if hasattr(block, 'text') and block.text:
                content_text = block.text
                break

        return LLMResponse(
            content=content_text,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            finish_reason=response.stop_reason
        )


class OpenAILLM(BaseLLM):
    """OpenAI GPT集成

    【学习要点】OpenAI API
    - ChatGPT模型
    - 函数调用支持
    - 流式响应
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装openai: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """生成响应（异步调用，避免阻塞事件循环）"""
        import asyncio

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        def _sync_call():
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
                **kwargs
            )

        # 在线程池中执行同步SDK调用，避免阻塞事件循环
        response = await asyncio.to_thread(_sync_call)

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            finish_reason=choice.finish_reason
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """对话（异步调用，避免阻塞事件循环）"""
        import asyncio

        def _sync_call():
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                **kwargs
            )

        # 在线程池中执行同步SDK调用，避免阻塞事件循环
        response = await asyncio.to_thread(_sync_call)

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            finish_reason=choice.finish_reason
        )


class LLMWrapper:
    """LLM包装器

    【功能】
    - 统一接口
    - 自动重试
    - 降级处理
    - Token追踪
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.provider = provider
        self.model = model or self._get_default_model(provider)
        self.api_key = api_key

        # 初始化LLM
        if provider == LLMProvider.ANTHROPIC:
            base_url = os.getenv("ANTHROPIC_BASE_URL")
            self.llm = AnthropicLLM(api_key=api_key, model=self.model, base_url=base_url)
        elif provider == LLMProvider.MINIMAX:
            # MiniMax 兼容 Anthropic API
            base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")
            # MiniMax使用与Anthropic相同的环境变量名
            minimax_key = os.getenv("ANTHROPIC_API_KEY") or api_key
            self.llm = AnthropicLLM(api_key=minimax_key, model=self.model, base_url=base_url)
        elif provider == LLMProvider.OPENAI:
            self.llm = OpenAILLM(api_key=api_key, model=self.model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _get_default_model(self, provider: LLMProvider) -> str:
        """获取默认模型"""
        defaults = {
            LLMProvider.ANTHROPIC: "claude-3-sonnet-20240229",
            LLMProvider.MINIMAX: os.getenv("ANTHROPIC_MODEL", "MiniMax-M2.7"),
            LLMProvider.OPENAI: "gpt-4"
        }
        return defaults.get(provider, "claude-3-sonnet-20240229")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """生成响应（带重试和Token记录）"""
        max_retries = kwargs.pop("max_retries", 3)
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = await self.llm.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    **kwargs
                )
                # 记录Token使用量
                if response.usage:
                    await token_manager.consume(
                        prompt_tokens=response.usage.get("prompt_tokens", 0),
                        completion_tokens=response.usage.get("completion_tokens", 0)
                    )
                return response

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise e

        raise RuntimeError("Max retries exceeded")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """对话（带重试）"""
        max_retries = kwargs.pop("max_retries", 3)
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = await self.llm.chat(messages=messages, **kwargs)
                # 记录Token使用量
                if response.usage:
                    await token_manager.consume(
                        prompt_tokens=response.usage.get("prompt_tokens", 0),
                        completion_tokens=response.usage.get("completion_tokens", 0)
                    )
                return response

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise e

        raise RuntimeError("Max retries exceeded")


# 全局默认实例
_default_llm: Optional[LLMWrapper] = None


def get_llm() -> LLMWrapper:
    """获取全局LLM实例"""
    global _default_llm

    if _default_llm is None:
        # 检测 MiniMax (通过环境变量)
        base_url = os.getenv("ANTHROPIC_BASE_URL", "")
        if "minimaxi" in base_url:
            provider = LLMProvider.MINIMAX
            model = os.getenv("ANTHROPIC_MODEL", "MiniMax-M2.7")
        elif settings.LLM_PROVIDER.lower() == "openai":
            provider = LLMProvider.OPENAI
            model = settings.LLM_MODEL
        else:
            provider = LLMProvider.ANTHROPIC
            model = settings.LLM_MODEL

        _default_llm = LLMWrapper(
            provider=provider,
            model=model
        )

    return _default_llm


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 初始化
llm = LLMWrapper(provider=LLMProvider.ANTHROPIC, model="claude-3-sonnet-20240229")

# 2. 简单生成
response = await llm.generate(
    prompt="What is Python?",
    system_prompt="You are a helpful assistant."
)
print(response.content)

# 3. 对话
messages = [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What is Python?"}
]
response = await llm.chat(messages)
print(response.content)

# 4. 使用便捷函数
llm = get_llm()  # 使用配置的默认LLM
response = await llm.generate("Hello")
"""
