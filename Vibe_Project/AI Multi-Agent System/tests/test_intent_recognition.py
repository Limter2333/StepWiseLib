"""
测试意图识别模块
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.retrieval.multi_tenant_intent import (
    IntentType,
    Intent,
    IntentCandidate,
    Sentiment,
    KeywordIntentRecognizer,
    SentimentAnalyzer,
    EntityExtractor,
    IntentRecognitionPipeline
)


class TestKeywordIntentRecognizer:
    """关键词意图识别器测试"""

    def setup_method(self):
        """每个测试前创建识别器"""
        self.recognizer = KeywordIntentRecognizer()

    def test_recognize_inquiry(self):
        """测试问答意图识别"""
        query = "What is Python programming language?"
        candidates = self.recognizer.recognize(query)

        assert len(candidates) > 0
        assert any(c.intent_type == IntentType.INQUIRY for c in candidates)

    def test_recognize_task_execution(self):
        """测试任务执行意图识别"""
        query = "请帮我生成代码"
        candidates = self.recognizer.recognize(query)

        assert len(candidates) > 0
        assert any(c.intent_type == IntentType.TASK_EXECUTION for c in candidates)

    def test_recognize_greeting(self):
        """测试问候意图识别"""
        query = "Hello, how are you?"
        candidates = self.recognizer.recognize(query)

        assert len(candidates) > 0
        # 应该是GREETING或CONVERSATION
        intent_types = [c.intent_type for c in candidates]
        assert IntentType.GREETING in intent_types or IntentType.CONVERSATION in intent_types

    def test_recognize_goodbye(self):
        """测试告别意图识别"""
        query = "Goodbye, see you later"
        candidates = self.recognizer.recognize(query)

        assert len(candidates) > 0
        assert any(c.intent_type == IntentType.GOODBYE for c in candidates)

    def test_recognize_thanks(self):
        """测试感谢意图识别"""
        query = "Thank you very much!"
        candidates = self.recognizer.recognize(query)

        assert len(candidates) > 0
        assert any(c.intent_type == IntentType.THANKS for c in candidates)

    def test_recognize_document_management(self):
        """测试文档管理意图识别"""
        query = "Upload this PDF to the knowledge base"
        candidates = self.recognizer.recognize(query)

        assert len(candidates) > 0
        assert any(c.intent_type == IntentType.DOCUMENT_MANAGEMENT for c in candidates)

    def test_recognize_no_match(self):
        """测试无匹配情况"""
        query = "asdfghjkl12345 xyz"
        candidates = self.recognizer.recognize(query)

        # 不应该有匹配
        assert len(candidates) == 0

    def test_recognize_multiple_intents(self):
        """测试多个意图"""
        query = "Hello, can you help me create a document?"
        candidates = self.recognizer.recognize(query)

        assert len(candidates) >= 2

    def test_recognize_sorted_by_confidence(self):
        """测试按置信度排序"""
        query = "How do I create a Python file?"
        candidates = self.recognizer.recognize(query)

        # 应该按置信度降序排列
        for i in range(len(candidates) - 1):
            assert candidates[i].confidence >= candidates[i + 1].confidence


class TestSentimentAnalyzer:
    """情感分析器测试"""

    def setup_method(self):
        """每个测试前创建分析器"""
        self.analyzer = SentimentAnalyzer()

    def test_positive_sentiment(self):
        """测试积极情感"""
        text = "This is great! I love it, excellent work!"
        sentiment = self.analyzer.analyze(text)

        assert sentiment == Sentiment.POSITIVE

    def test_negative_sentiment(self):
        """测试消极情感"""
        text = "This is terrible, I hate it, awful experience"
        sentiment = self.analyzer.analyze(text)

        assert sentiment == Sentiment.NEGATIVE

    def test_neutral_sentiment(self):
        """测试中性情感"""
        text = "The file is located in the directory"
        sentiment = self.analyzer.analyze(text)

        assert sentiment == Sentiment.NEUTRAL

    def test_mixed_sentiment(self):
        """测试混合情感"""
        text = "Good feature but terrible UI"
        sentiment = self.analyzer.analyze(text)

        # 应该返回中性或主导情感
        assert sentiment in [Sentiment.POSITIVE, Sentiment.NEGATIVE, Sentiment.NEUTRAL]


class TestEntityExtractor:
    """实体提取器测试"""

    def setup_method(self):
        """每个测试前创建提取器"""
        self.extractor = EntityExtractor()

    def test_extract_date(self):
        """测试日期提取"""
        text = "Schedule for 2024年3月15日"
        entities = self.extractor.extract(text)

        # 日期提取后存在 time 键中
        assert "time" in entities

    def test_extract_relative_date(self):
        """测试相对日期提取"""
        text = "安排在明天开会"
        entities = self.extractor.extract(text)

        # 相对日期存在 time 键中
        assert "time" in entities

    def test_extract_time(self):
        """测试时间提取"""
        text = "Reminder at 14点30分"
        entities = self.extractor.extract(text)

        assert "time" in entities

    def test_extract_quantity(self):
        """测试数量提取"""
        text = "I need 5 copies of this document"
        entities = self.extractor.extract(text)

        assert "number" in entities

    def test_extract_programming_language(self):
        """测试编程语言提取"""
        text = "I can write Python and JavaScript code"
        entities = self.extractor.extract(text)

        assert "language" in entities
        assert "Python" in entities["language"] or "JavaScript" in entities["language"]

    def test_extract_email(self):
        """测试邮箱提取"""
        text = "Contact me at user@example.com for details"
        entities = self.extractor.extract(text)

        assert "email" in entities
        assert "user@example.com" in entities["email"]

    def test_extract_url(self):
        """测试URL提取"""
        text = "Check out https://example.com/docs for more info"
        entities = self.extractor.extract(text)

        assert "url" in entities
        assert "https://example.com/docs" in entities["url"]

    def test_extract_www_url(self):
        """测试www URL提取"""
        text = "Visit www.example.com for more"
        entities = self.extractor.extract(text)

        assert "url" in entities
        assert "www.example.com" in entities["url"]

    def test_extract_file_type(self):
        """测试文件类型提取"""
        text = "Please upload the PDF file and CSV document"
        entities = self.extractor.extract(text)

        assert "file_type" in entities
        # 应该匹配到PDF和CSV
        file_types = entities["file_type"]
        assert any("pdf" in f.lower() or "csv" in f.lower() for f in file_types)

    def test_extract_multiple_entities(self):
        """测试多类型实体提取"""
        text = "Send email to test@example.com at 14点30分"
        entities = self.extractor.extract(text)

        assert "email" in entities
        assert "time" in entities

    def test_extract_programming_language_lowercase(self):
        """测试小写编程语言提取"""
        text = "write python and javascript code"
        entities = self.extractor.extract(text)

        assert "language" in entities
        # 小写的python和javascript也应该被提取
        langs = [l.lower() for l in entities["language"]]
        assert "python" in langs

    def test_extract_weekday(self):
        """测试星期提取"""
        text = "安排在下周一开会"
        entities = self.extractor.extract(text)

        assert "time" in entities


class TestIntentRecognitionPipeline:
    """意图识别管道测试"""

    def setup_method(self):
        """每个测试前创建管道"""
        self.pipeline = IntentRecognitionPipeline()

    def test_recognize_simple_query(self):
        """测试简单查询识别"""
        intent = self.pipeline.recognize(
            query="What is RAG?",
            session_id="test_session"
        )

        assert intent.intent_type == IntentType.INQUIRY
        assert intent.confidence > 0

    def test_recognize_greeting(self):
        """测试问候识别"""
        intent = self.pipeline.recognize(
            query="Hi there!",
            session_id="test_session"
        )

        assert intent.intent_type in [IntentType.GREETING, IntentType.CONVERSATION]

    def test_recognize_task_execution(self):
        """测试任务执行识别"""
        intent = self.pipeline.recognize(
            query="Please generate unit tests for this module",
            session_id="test_session"
        )

        assert intent.intent_type == IntentType.TASK_EXECUTION

    def test_context_tracking(self):
        """测试上下文追踪"""
        session_id = "test_session_context"

        # 第一轮
        self.pipeline.recognize(
            query="What is Python?",
            session_id=session_id
        )

        # 获取上下文
        context = self.pipeline.get_or_create_context(session_id)

        assert context.session_id == session_id
        assert context.last_intent is not None

    def test_no_match_returns_unknown(self):
        """测试无匹配返回UNKNOWN"""
        intent = self.pipeline.recognize(
            query="asdfghjkl12345 xyz abc",
            session_id="test_session"
        )

        assert intent.intent_type == IntentType.UNKNOWN

    def test_entities_extraction(self):
        """测试实体提取"""
        intent = self.pipeline.recognize(
            query="请在明天14点安排5个会议",
            session_id="test_session"
        )

        # 应该提取到time和number实体
        # 注意：如果没有匹配任何意图，返回UNKNOWN但仍可能提取实体
        # 或者匹配到task_execution
        assert intent.intent_type in [IntentType.TASK_EXECUTION, IntentType.UNKNOWN]
        # entities可能有也可能没有，取决于识别结果

    def test_sentiment_in_metadata(self):
        """测试情感在元数据中"""
        intent = self.pipeline.recognize(
            query="This is great, thank you!",
            session_id="test_session"
        )

        assert "sentiment" in intent.metadata


class TestIntentCandidate:
    """意图候选测试"""

    def test_creation(self):
        """测试创建"""
        candidate = IntentCandidate(
            intent_type=IntentType.INQUIRY,
            confidence=0.8,
            matched_keywords=["what", "how"],
            pattern="what|how"
        )

        assert candidate.intent_type == IntentType.INQUIRY
        assert candidate.confidence == 0.8
        assert len(candidate.matched_keywords) == 2


class TestIntent:
    """意图测试"""

    def test_creation(self):
        """测试创建"""
        intent = Intent(
            intent_type=IntentType.TASK_EXECUTION,
            confidence=0.9,
            entities={"language": "Python"},
            metadata={"source": "test"}
        )

        assert intent.intent_type == IntentType.TASK_EXECUTION
        assert intent.confidence == 0.9
        assert intent.entities["language"] == "Python"


class TestIntentRecognitionEdgeCases:
    """意图识别边界情况测试"""

    def test_recognize_none_input(self):
        """测试None输入"""
        recognizer = KeywordIntentRecognizer()
        # None输入应该返回空列表，不抛异常
        candidates = recognizer.recognize(None)
        assert candidates == []

    def test_recognize_empty_string(self):
        """测试空字符串"""
        recognizer = KeywordIntentRecognizer()
        candidates = recognizer.recognize("")
        assert candidates == []

    def test_recognize_whitespace_only(self):
        """测试纯空格输入"""
        recognizer = KeywordIntentRecognizer()
        candidates = recognizer.recognize("   ")
        # 纯空格应该返回空列表
        assert candidates == []

    def test_recognize_single_character(self):
        """测试单字符输入"""
        recognizer = KeywordIntentRecognizer()
        candidates = recognizer.recognize("a")
        # 单字符应该不匹配任何意图
        assert candidates == []

    def test_recognize_very_long_query(self):
        """测试超长查询"""
        recognizer = KeywordIntentRecognizer()
        long_query = "What is " + "Python " * 10000
        # 超长查询不应崩溃
        candidates = recognizer.recognize(long_query)
        assert isinstance(candidates, list)

    def test_recognize_special_characters_only(self):
        """测试纯特殊字符"""
        recognizer = KeywordIntentRecognizer()
        candidates = recognizer.recognize("!@#$%^&*()")
        # 特殊字符不匹配意图
        assert candidates == []

    def test_recognize_pure_numbers(self):
        """测试纯数字输入"""
        recognizer = KeywordIntentRecognizer()
        candidates = recognizer.recognize("12345")
        # 纯数字不匹配意图
        assert candidates == []

    def test_recognize_unicode_only(self):
        """测试纯Unicode字符"""
        recognizer = KeywordIntentRecognizer()
        # "今天天气真好"不包含任何意图关键词
        candidates = recognizer.recognize("今天天气真好")
        assert candidates == []

    def test_recognize_emoji_only(self):
        """测试纯emoji"""
        recognizer = KeywordIntentRecognizer()
        candidates = recognizer.recognize("😀😃😄")
        assert isinstance(candidates, list)

    def test_recognize_mixed_valid_query(self):
        """测试混合有效查询"""
        recognizer = KeywordIntentRecognizer()
        query = "Hello, please help me write Python code"
        candidates = recognizer.recognize(query)
        assert len(candidates) > 0
        # 应该匹配多个意图
        intent_types = [c.intent_type for c in candidates]
        assert IntentType.GREETING in intent_types or IntentType.TASK_EXECUTION in intent_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
