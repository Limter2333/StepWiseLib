import abc
from typing import Optional
from harness.llm.base import ChatMessage


class MemoryProvider(abc.ABC):
    """记忆提供者抽象基类。
    
    设计意图：定义统一的记忆管理接口，支持短期记忆（滑动窗口、摘要压缩）
    和长期记忆（向量存储、事实检索）的不同实现。
    """
    
    @abc.abstractmethod
    def history(self) -> list[ChatMessage]:
        """获取历史对话消息列表。
        
        可能经过压缩/摘要处理，只返回当前需要的消息。
        """
        pass
    
    @abc.abstractmethod
    def add(self, message: ChatMessage) -> None:
        """添加一条新消息到记忆中。"""
        pass
    
    @abc.abstractmethod
    def clear(self) -> None:
        """清空记忆。"""
        pass
    
    @abc.abstractmethod
    def summarize_if_needed(self) -> Optional[str]:
        """如果需要，对记忆进行摘要压缩。
        
        Returns:
            摘要文本，如果不需要摘要则返回 None
        """
        pass
