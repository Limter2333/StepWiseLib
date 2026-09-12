import os
import time
from typing import Callable, Optional

from openai import OpenAI

from harness.config import LLMConfig
from .base import BaseLLMClient, ChatMessage


class OpenAIClient(BaseLLMClient):
    """OpenAI 兼容的 LLM 客户端实现。
    
    支持所有兼容 OpenAI 协议的服务，如 OpenAI、OpenRouter、Zen Gateway 等。
    内置 429 限流重试机制（指数退避）。
    """
    
    def __init__(self, config: LLMConfig):
        """初始化客户端。
        
        Args:
            config: LLM 配置，包含 base_url、model、api_key_env 等
        """
        self._config = config
        self._client = OpenAI(
            base_url=config.base_url,
            api_key=os.getenv(config.api_key_env),
        )
    
    def chat(
        self, 
        messages: list[ChatMessage], 
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """发起对话请求，支持流式输出和自动重试。
        
        Args:
            messages: 对话消息列表
            stream_callback: 流式回调，用于实时输出每个 token
            
        Returns:
            完整的回复文本
        """
        # 转换消息格式为 OpenAI 格式
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        for attempt in range(self._config.max_retries):
            try:
                stream = self._client.chat.completions.create(
                    model=self._config.model,
                    messages=openai_messages,
                    stream=True,
                )
                
                content_parts = []
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        content_parts.append(token)
                        if stream_callback:
                            stream_callback(token)
                
                return "".join(content_parts)
            
            except Exception as e:
                # 仅对限流(429)与临时错误重试
                if getattr(e, "status_code", None) != 429 or attempt == self._config.max_retries - 1:
                    raise
                wait = 2 ** attempt  # 指数退避：1s, 2s, 4s, 8s, ...
                print(f"\n⚠️ 触发限流(429)，{wait} 秒后重试（第 {attempt + 1}/{self._config.max_retries} 次）...")
                time.sleep(wait)
    
    def count_tokens(self, text: str) -> int:
        """估算 token 数量。
        
        简单估算：英文约 4 字符/token，中文约 2 字符/token。
        生产环境可接入 tiktoken 或模型提供商的 tokenizer API。
        """
        # 简单启发式：中文字符数/2 + 英文单词数
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = len(text) - chinese_chars
        return chinese_chars // 2 + english_chars // 4
