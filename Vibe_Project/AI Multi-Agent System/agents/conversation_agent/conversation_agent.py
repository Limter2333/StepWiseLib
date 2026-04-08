"""
Conversation Agent - 对话智能体
===============================

职责:
- 用户对话管理
- 上下文维护
- 多轮对话
- Prompt优化
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 导入记忆模块
from memory.short_term import short_term_memory, MemoryType, ConversationSession
from core.guardrails import guardrails
from core.prompt_engine import prompt_manager


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """消息"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: Optional[str] = None
    intent: Optional[str] = None
    entities: Dict = field(default_factory=dict)
    sentiment: str = "neutral"  # positive, neutral, negative
    topic: Optional[str] = None


class ConversationAgent:
    """对话智能体

    【能力】
    - 多轮对话管理
    - 上下文理解
    - 对话摘要
    - 意图识别
    """

    def __init__(self):
        self.name = "Conversation Agent"
        self.default_session_ttl = 3600  # 1小时

    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ConversationSession:
        """创建对话会话"""
        return short_term_memory.create_session(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {}
        )

    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """获取会话"""
        return short_term_memory.get_session(session_id)

    async def send_message(
        self,
        session_id: str,
        message: str,
        role: MessageRole = MessageRole.USER
    ) -> Dict:
        """发送消息

        Args:
            session_id: 会话ID
            message: 消息内容
            role: 角色

        Returns:
            处理结果
        """
        # 输入检查
        guard_result = guardrails.check_input(message)
        if not guard_result.passed:
            return {
                "success": False,
                "error": guard_result.message,
                "guardrail_result": guard_result.model_dump()
            }

        # 获取或创建会话
        session = short_term_memory.get_or_create_session(session_id)

        # 保存用户消息
        memory_type = (
            MemoryType.USER_MESSAGE if role == MessageRole.USER
            else MemoryType.AI_RESPONSE if role == MessageRole.ASSISTANT
            else MemoryType.INTERMEDIATE_RESULT
        )

        short_term_memory.add_to_session(
            session_id=session_id,
            content=message,
            memory_type=memory_type,
            metadata={"role": role.value}
        )

        return {
            "success": True,
            "session_id": session_id,
            "message_length": len(message)
        }

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Message]:
        """获取对话历史"""
        history = short_term_memory.get_conversation_history(session_id, limit)

        messages = []
        for item in history:
            msg_type = MessageRole.USER
            if item["type"] == "ai_response":
                msg_type = MessageRole.ASSISTANT

            messages.append(Message(
                role=msg_type,
                content=item["content"],
                timestamp=datetime.fromisoformat(item["timestamp"])
            ))

        return messages

    async def summarize_conversation(
        self,
        session_id: str,
        max_length: int = 500
    ) -> str:
        """总结对话

        【学习要点】对话摘要的作用
        - 压缩历史记录节省Token
        - 提取关键信息
        - 保留重要上下文
        """
        history = await self.get_conversation_history(session_id, limit=50)

        if not history:
            return ""

        # 简单实现：提取关键消息
        summary_parts = []
        total_length = 0

        for msg in history[-10:]:  # 最近10条
            if total_length + len(msg.content) > max_length:
                break
            prefix = "User" if msg.role == MessageRole.USER else "Assistant"
            summary_parts.append(f"{prefix}: {msg.content[:100]}...")
            total_length += len(msg.content)

        return "\n".join(summary_parts)

    async def extract_entities(self, message: str) -> Dict:
        """提取实体

        【学习要点】NER (Named Entity Recognition)
        - 识别人名、地名、机构
        - 提取关键信息
        - 理解用户意图
        """
        # 简化实现
        entities = {
            "has_question": "?" in message,
            "has_number": any(c.isdigit() for c in message),
            "length": len(message),
            "language": self._detect_language(message)
        }

        return entities

    def _detect_language(self, text: str) -> str:
        """简单语言检测"""
        # 统计中文字符
        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_count / len(text) > 0.3:
            return "zh"
        return "en"

    async def detect_intent(self, message: str) -> str:
        """识别意图

        【简化实现】
        实际应该用分类模型
        """
        message_lower = message.lower()

        if any(kw in message_lower for kw in ["what", "什么是", "是什么"]):
            return "question"
        if any(kw in message_lower for kw in ["how", "如何", "怎么办"]):
            return "how_to"
        if any(kw in message_lower for kw in ["why", "为什么"]):
            return "why"
        if any(kw in message_lower for kw in ["create", "生成", "创建"]):
            return "create"
        if any(kw in message_lower for kw in ["update", "修改", "更新"]):
            return "update"
        if any(kw in message_lower for kw in ["delete", "删除"]):
            return "delete"

        return "general"

    async def detect_intent_with_llm(
        self,
        message: str,
        context: str = ""
    ) -> str:
        """使用LLM识别意图

        Args:
            message: 用户消息
            context: 上下文信息

        Returns:
            意图类别
        """
        try:
            system_prompt, user_prompt = prompt_manager.render(
                "intent_classification",
                message=message,
                context=context or "No additional context"
            )

            from core.llm import get_llm
            llm = get_llm()
            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=50,
                temperature=0.1
            )

            # 解析意图
            intent = response.content.strip().lower()
            valid_intents = ["question", "request", "update", "delete",
                           "greeting", "thanks", "farewell", "feedback",
                           "complaint", "general"]

            if intent in valid_intents:
                return intent
            return "general"

        except Exception as e:
            # 回退到关键词检测
            return self.detect_intent(message)

    async def build_context_prompt(
        self,
        session_id: str,
        current_message: str,
        max_history: int = 10
    ) -> str:
        """构建上下文Prompt

        【用途】
        - 将历史对话压缩
        - 附加到系统Prompt
        - 保持长期上下文
        """
        history = await self.get_conversation_history(session_id, limit=max_history)

        if not history:
            return current_message

        # 构建历史摘要
        history_text = "\n\n".join([
            f"{'User' if msg.role == MessageRole.USER else 'Assistant'}: {msg.content}"
            for msg in history
        ])

        return f"""## Previous Conversation

{history_text}

## Current Message

{current_message}"""

    async def clear_session(self, session_id: str) -> bool:
        """清除会话"""
        return short_term_memory.delete_session(session_id)

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "features": [
                "multi_turn_conversation",
                "context_management",
                "intent_detection",
                "entity_extraction",
                "conversation_summarization"
            ],
            "supported_roles": [r.value for r in MessageRole]
        }


# 全局实例
conversation_agent = ConversationAgent()
