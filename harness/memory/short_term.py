from typing import Optional
from harness.llm.base import ChatMessage, BaseLLMClient
from .base import MemoryProvider


class SlidingWindowMemory(MemoryProvider):
    """滑动窗口记忆管理。
    
    设计意图：限制消息历史长度，防止上下文无限增长。
    当消息超过阈值时，使用 LLM 对早期消息进行摘要压缩。
    """
    
    def __init__(
        self, 
        max_messages: int = 20,
        summarize_after: int = 10,
        llm: Optional[BaseLLMClient] = None
    ):
        """初始化滑动窗口记忆。
        
        Args:
            max_messages: 最大消息数量
            summarize_after: 超过此数量时触发摘要
            llm: LLM 客户端，用于生成摘要（可选）
        """
        self._messages: list[ChatMessage] = []
        self._max_messages = max_messages
        self._summarize_after = summarize_after
        self._llm = llm
        self._summary: Optional[str] = None
    
    def history(self) -> list[ChatMessage]:
        """获取历史消息列表。
        
        如果有摘要，会在开头添加一条摘要消息。
        """
        messages = []
        
        # 添加摘要消息（如果有）
        if self._summary:
            messages.append(ChatMessage(
                role="system",
                content=f"先前对话摘要：{self._summary}"
            ))
        
        # 添加历史消息
        messages.extend(self._messages)
        
        return messages
    
    def add(self, message: ChatMessage) -> None:
        """添加新消息，超长时触发压缩。"""
        self._messages.append(message)
        
        # 检查是否需要摘要压缩
        if len(self._messages) > self._summarize_after:
            self._compress_if_needed()
    
    def clear(self) -> None:
        """清空记忆。"""
        self._messages.clear()
        self._summary = None
    
    def summarize_if_needed(self) -> Optional[str]:
        """手动触发摘要压缩。"""
        if len(self._messages) <= self._summarize_after:
            return None
        return self._compress_if_needed()
    
    def _compress_if_needed(self) -> Optional[str]:
        """压缩早期消息，保留最近的消息。"""
        if not self._llm or len(self._messages) <= self._max_messages:
            return None
        
        # 保留最近 N/2 条消息
        keep_recent = len(self._messages) // 2
        to_summarize = self._messages[:-keep_recent]
        
        # 生成摘要
        summary = self._summarize_messages(to_summarize)
        
        # 更新状态
        self._summary = summary
        self._messages = self._messages[-keep_recent:]
        
        return summary
    
    def _summarize_messages(self, messages: list[ChatMessage]) -> str:
        """使用 LLM 对消息进行摘要。"""
        # 构建摘要提示
        conversation = "\n".join(f"{m.role}: {m.content}" for m in messages)
        summary_prompt = [
            ChatMessage(role="system", content="请用简洁的语言总结以下对话的要点："),
            ChatMessage(role="user", content=conversation)
        ]
        
        try:
            summary = self._llm.chat(summary_prompt)
            return summary
        except Exception:
            # 摘要失败时，使用简单的截断
            return f"（已压缩 {len(messages)} 条消息）"
