"""
Conversation Agent Tests
"""

import pytest
from datetime import datetime
from agents.conversation_agent.conversation_agent import (
    ConversationAgent,
    MessageRole,
    Message,
    ConversationContext
)


class TestConversationAgentCreation:
    """测试ConversationAgent创建"""

    def test_agent_creation(self):
        agent = ConversationAgent()
        assert agent.name == "Conversation Agent"
        assert agent.default_session_ttl == 3600


class TestSessionManagement:
    """测试会话管理"""

    @pytest.mark.asyncio
    async def test_create_session(self):
        agent = ConversationAgent()
        session = await agent.create_session(
            session_id="test_session_1",
            user_id="user_1",
            metadata={"source": "test"}
        )

        assert session is not None
        assert session.session_id == "test_session_1"
        assert session.user_id == "user_1"

    @pytest.mark.asyncio
    async def test_get_session(self):
        agent = ConversationAgent()

        # Create first
        await agent.create_session(
            session_id="test_session_2",
            user_id="user_2"
        )

        # Then get
        session = await agent.get_session("test_session_2")
        assert session is not None
        assert session.session_id == "test_session_2"


class TestMessageHandling:
    """测试消息处理"""

    @pytest.mark.asyncio
    async def test_send_message(self):
        agent = ConversationAgent()

        # Create session first
        await agent.create_session(session_id="msg_test_1")

        result = await agent.send_message(
            session_id="msg_test_1",
            message="Hello, how are you?",
            role=MessageRole.USER
        )

        assert result["success"] is True
        assert result["session_id"] == "msg_test_1"
        assert result["message_length"] > 0

    @pytest.mark.asyncio
    async def test_send_message_empty_rejected(self):
        agent = ConversationAgent()
        await agent.create_session(session_id="msg_test_2")

        result = await agent.send_message(
            session_id="msg_test_2",
            message="",
            role=MessageRole.USER
        )

        # Empty messages are rejected by guardrails
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_send_message_assistant_role(self):
        agent = ConversationAgent()
        await agent.create_session(session_id="msg_test_3")

        result = await agent.send_message(
            session_id="msg_test_3",
            message="I'm doing well, thank you!",
            role=MessageRole.ASSISTANT
        )

        assert result["success"] is True


class TestConversationHistory:
    """测试对话历史"""

    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        agent = ConversationAgent()
        session_id = "history_test_1"

        await agent.create_session(session_id=session_id)
        await agent.send_message(session_id, "First message", MessageRole.USER)
        await agent.send_message(session_id, "Second message", MessageRole.USER)

        history = await agent.get_conversation_history(session_id, limit=10)

        assert len(history) >= 2
        assert all(isinstance(msg, Message) for msg in history)

    @pytest.mark.asyncio
    async def test_get_conversation_history_empty(self):
        agent = ConversationAgent()
        session_id = "history_test_2"

        await agent.create_session(session_id=session_id)

        history = await agent.get_conversation_history(session_id)
        # Empty history returns empty list
        assert isinstance(history, list)


class TestConversationSummary:
    """测试对话摘要"""

    @pytest.mark.asyncio
    async def test_summarize_conversation(self):
        agent = ConversationAgent()
        session_id = "summary_test_1"

        await agent.create_session(session_id=session_id)
        await agent.send_message(session_id, "Hello", MessageRole.USER)
        await agent.send_message(session_id, "How can I help you?", MessageRole.ASSISTANT)
        await agent.send_message(session_id, "I need assistance", MessageRole.USER)

        summary = await agent.summarize_conversation(session_id)

        assert isinstance(summary, str)
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_summarize_empty_conversation(self):
        agent = ConversationAgent()
        session_id = "summary_test_2"

        await agent.create_session(session_id=session_id)

        summary = await agent.summarize_conversation(session_id)

        assert summary == ""


class TestEntityExtraction:
    """测试实体提取"""

    @pytest.mark.asyncio
    async def test_extract_entities_question(self):
        agent = ConversationAgent()

        entities = await agent.extract_entities("What is Python?")

        assert entities["has_question"] is True
        assert entities["has_number"] is False
        assert "language" in entities

    @pytest.mark.asyncio
    async def test_extract_entities_number(self):
        agent = ConversationAgent()

        entities = await agent.extract_entities("I need 5 copies")

        assert entities["has_question"] is False
        assert entities["has_number"] is True

    @pytest.mark.asyncio
    async def test_extract_entities_chinese(self):
        agent = ConversationAgent()

        entities = await agent.extract_entities("你好世界，这是一个测试")

        assert entities["has_question"] is False
        assert entities["language"] == "zh"

    @pytest.mark.asyncio
    async def test_extract_entities_english(self):
        agent = ConversationAgent()

        entities = await agent.extract_entities("Hello world, this is a test")

        assert entities["language"] == "en"


class TestIntentDetection:
    """测试意图识别"""

    @pytest.mark.asyncio
    async def test_detect_intent_question(self):
        agent = ConversationAgent()

        intent = await agent.detect_intent("What is Python?")

        assert intent == "question"

    @pytest.mark.asyncio
    async def test_detect_intent_how_to(self):
        agent = ConversationAgent()

        intent = await agent.detect_intent("How do I install Python?")

        assert intent == "how_to"

    @pytest.mark.asyncio
    async def test_detect_intent_why(self):
        agent = ConversationAgent()

        intent = await agent.detect_intent("Why is Python popular?")

        assert intent == "why"

    @pytest.mark.asyncio
    async def test_detect_intent_create(self):
        agent = ConversationAgent()

        intent = await agent.detect_intent("Create a new project")

        assert intent == "create"

    @pytest.mark.asyncio
    async def test_detect_intent_update(self):
        agent = ConversationAgent()

        intent = await agent.detect_intent("Update the settings")

        assert intent == "update"

    @pytest.mark.asyncio
    async def test_detect_intent_delete(self):
        agent = ConversationAgent()

        intent = await agent.detect_intent("Delete the file")

        assert intent == "delete"

    @pytest.mark.asyncio
    async def test_detect_intent_general(self):
        agent = ConversationAgent()

        intent = await agent.detect_intent("Hello there")

        assert intent == "general"


class TestLanguageDetection:
    """测试语言检测"""

    def test_detect_chinese(self):
        agent = ConversationAgent()

        lang = agent._detect_language("你好世界")

        assert lang == "zh"

    def test_detect_english(self):
        agent = ConversationAgent()

        lang = agent._detect_language("Hello world")

        assert lang == "en"

    def test_detect_mixed(self):
        agent = ConversationAgent()

        # Less than 30% Chinese = English
        lang = agent._detect_language("Hello 你好 world")

        assert lang == "en"


class TestMessageRole:
    """测试消息角色"""

    def test_message_role_values(self):
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"

    def test_message_creation(self):
        msg = Message(
            role=MessageRole.USER,
            content="Test message"
        )

        assert msg.role == MessageRole.USER
        assert msg.content == "Test message"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}


class TestConversationContext:
    """测试对话上下文"""

    def test_context_creation(self):
        ctx = ConversationContext(
            session_id="test_session",
            user_id="user_1",
            intent="question",
            sentiment="positive"
        )

        assert ctx.session_id == "test_session"
        assert ctx.user_id == "user_1"
        assert ctx.intent == "question"
        assert ctx.sentiment == "positive"
        assert ctx.entities == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
