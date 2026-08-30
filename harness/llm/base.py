import abc
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ChatMessage:
    """统一的消息格式，用于 LLM 对话。
    
    设计意图：解耦不同 LLM 提供商的消息格式差异，
    让 AgentRunner 只依赖这个简单结构。
    """
    role: str  # system / user / assistant
    content: str


class BaseLLMClient(abc.ABC):
    """LLM 客户端抽象基类。
    
    设计意图：定义统一的 LLM 调用接口，让 AgentRunner 
    可以无缝切换不同的 LLM 后端（OpenAI、vLLM、本地模型等）。
    """
    
    @abc.abstractmethod
    def chat(
        self, 
        messages: list[ChatMessage], 
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """发起对话请求，返回完整回复。
        
        Args:
            messages: 对话消息列表
            stream_callback: 可选的流式回调函数，用于实时输出
            
        Returns:
            完整的回复文本
            
        Raises:
            Exception: LLM 调用失败（如网络错误、限流等）
        """
        pass
    
    @abc.abstractmethod
    def count_tokens(self, text: str) -> int:
        """估算文本的 token 数量（可选实现）。
        
        用于上下文窗口管理和成本估算。
        如果不实现，默认使用 len(text) // 2 估算中文 token 数。
        """
        return len(text) // 2
