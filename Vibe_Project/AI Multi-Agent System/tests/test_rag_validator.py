"""
测试RAG输入验证器

验证查询验证、文本清洗、注入防护功能
"""

import pytest
from core.rag_validator import (
    QueryValidator,
    DocumentValidator,
    ChunkValidator,
    ValidationLevel,
    ValidationResult,
    get_query_validator,
    get_document_validator
)


class TestQueryValidator:
    """查询验证器测试"""

    @pytest.fixture
    def validator(self):
        return QueryValidator(ValidationLevel.NORMAL)

    def test_valid_query(self, validator):
        """正常查询通过验证"""
        result = validator.validate("What is the capital of France?")
        assert result.is_valid
        assert result.cleaned_query == "What is the capital of France?"
        assert result.error_message is None

    def test_empty_query(self, validator):
        """空查询被拒绝"""
        result = validator.validate("")
        assert not result.is_valid
        assert result.error_message == "Query cannot be empty"

    def test_whitespace_only_query(self, validator):
        """纯空白查询被拒绝"""
        result = validator.validate("   \n\t  ")
        assert not result.is_valid
        assert result.error_message == "Query cannot be empty"

    def test_too_short_query(self, validator):
        """太短的查询被拒绝"""
        result = validator.validate("a")
        assert not result.is_valid

    def test_too_long_query_truncated(self, validator):
        """超长查询被截断（非STRICT模式）"""
        long_query = "a" * 2000
        result = validator.validate(long_query)
        assert result.is_valid
        assert len(result.cleaned_query) == 1000
        assert "truncated" in result.warnings[0].lower()

    def test_too_long_query_rejected_strict(self):
        """STRICT模式下超长查询被拒绝"""
        strict_validator = QueryValidator(ValidationLevel.STRICT)
        long_query = "a" * 2000
        result = strict_validator.validate(long_query)
        assert not result.is_valid
        assert "exceeds maximum length" in result.error_message

    def test_chinese_query(self, validator):
        """中文查询通过验证"""
        result = validator.validate("中国的首都是哪里？")
        assert result.is_valid
        # 验证中文内容保留
        assert "中国" in result.cleaned_query
        assert "首都" in result.cleaned_query

    def test_unicode_normalization(self, validator):
        """Unicode规范化（全角转半角）"""
        # 全角空格
        result = validator.validate("hello　world")  # 全角空格
        assert result.is_valid
        assert "  " not in result.cleaned_query  # 多个空格应合并

    def test_nonsensical_only_stopwords(self, validator):
        """只有停用词的查询被拒绝"""
        result = validator.validate("the a an is are of to")
        assert not result.is_valid

    def test_nonsensical_symbols_only(self, validator):
        """只有符号的查询被拒绝"""
        result = validator.validate("!!! ??? ***")
        assert not result.is_valid

    def test_xss_pattern_warning(self, validator):
        """XSS模式产生警告"""
        result = validator.validate("<script>alert('xss')</script>")
        assert result.is_valid  # 仍通过（NORMAL模式只警告）
        assert any("script" in w.lower() for w in result.warnings)

    def test_strict_sanitizes_html(self):
        """STRICT模式移除HTML标签"""
        strict_validator = QueryValidator(ValidationLevel.STRICT)
        result = strict_validator.validate("<b>hello</b> <script>evil()</script>")
        assert result.is_valid
        assert "<" not in result.cleaned_query
        assert result.sanitized is True

    def test_strict_sanitizes_sql_patterns(self):
        """STRICT模式移除SQL注入模式"""
        strict_validator = QueryValidator(ValidationLevel.STRICT)
        result = strict_validator.validate("'; DROP TABLE users; --")
        assert result.is_valid
        # 危险模式被移除/替换
        assert "DROP" not in result.cleaned_query.upper()
        assert result.sanitized is True

    def test_lenient_allows_nonsensical(self):
        """LENIENT模式允许无意义查询"""
        lenient_validator = QueryValidator(ValidationLevel.LENIENT)
        # 只有2个字符，应该匹配.{0,2}$模式，但LENIENT允许通过
        result = lenient_validator.validate("ab")
        assert result.is_valid
        # LENIENT模式应该不拦截，即使看起来无意义

    def test_type_check_rejects_non_string(self, validator):
        """非字符串类型被拒绝"""
        result = validator.validate(123)
        assert not result.is_valid
        assert "must be a string" in result.error_message

        result = validator.validate(None)
        assert not result.is_valid


class TestDocumentValidator:
    """文档验证器测试"""

    @pytest.fixture
    def validator(self):
        return DocumentValidator()

    def test_valid_content(self, validator):
        """正常内容通过验证"""
        result = validator.validate_content("This is valid document content with enough characters.")
        assert result.is_valid
        assert result.cleaned_query is not None

    def test_too_short_content(self, validator):
        """太短的内容被拒绝"""
        result = validator.validate_content("Short")
        assert not result.is_valid
        assert "too short" in result.error_message

    def test_allowed_extensions(self, validator):
        """允许的文件扩展名"""
        allowed = ['.pdf', '.docx', '.txt', '.md', '.xlsx']
        for ext in allowed:
            assert validator.validate_extension(f'file{ext}') is True

    def test_disallowed_extensions(self, validator):
        """不允许的文件扩展名"""
        disallowed = ['.exe', '.sh', '.bat', '.dll']
        for ext in disallowed:
            assert validator.validate_extension(f'file{ext}') is False


class TestChunkValidator:
    """文本块验证器测试"""

    @pytest.fixture
    def validator(self):
        return ChunkValidator()

    def test_valid_chunk(self, validator):
        """正常的文本块通过验证"""
        result, msg = validator.validate("This is a valid chunk with enough content.")
        assert result is True
        assert msg == ""

    def test_empty_chunk(self, validator):
        """空文本块被拒绝"""
        result, msg = validator.validate("")
        assert result is False
        assert "empty" in msg.lower()

    def test_too_short_chunk(self, validator):
        """太短的文本块被拒绝"""
        result, msg = validator.validate("Short")
        assert result is False
        assert "too short" in msg.lower()


class TestSingletonFunctions:
    """单例函数测试"""

    def test_get_query_validator_returns_same_instance(self):
        """查询验证器单例"""
        v1 = get_query_validator()
        v2 = get_query_validator()
        assert v1 is v2

    def test_get_document_validator_returns_same_instance(self):
        """文档验证器单例"""
        v1 = get_document_validator()
        v2 = get_document_validator()
        assert v1 is v2
