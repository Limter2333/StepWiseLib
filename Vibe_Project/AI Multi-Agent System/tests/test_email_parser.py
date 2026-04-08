"""
测试邮件解析器

验证.eml和.msg文件解析功能
"""

import pytest
import os
from pathlib import Path


class TestEmailParser:
    """邮件解析器测试"""

    @pytest.fixture
    def parser(self):
        from knowledge.parsers.email_parser import EmailParser
        return EmailParser()

    @pytest.fixture
    def eml_path(self):
        return "G:/claude_code_project/tests/fixtures/test_email.eml"

    def test_parser_initialization(self, parser):
        """解析器初始化"""
        assert parser is not None
        assert '.eml' in parser.supported_extensions
        assert '.msg' in parser.supported_extensions

    def test_can_parse_eml(self, parser, eml_path):
        """识别.eml文件"""
        assert parser.can_parse(eml_path) is True

    def test_cannot_parse_other_formats(self, parser):
        """不识别其他格式"""
        assert parser.can_parse("test.pdf") is False
        assert parser.can_parse("test.docx") is False
        assert parser.can_parse("test.txt") is False

    def test_parse_eml_basic_fields(self, parser, eml_path):
        """解析基本字段"""
        result = parser.parse(eml_path)

        assert 'subject' in result
        assert 'sender' in result
        assert 'recipients' in result
        assert 'date' in result
        assert 'body_text' in result
        assert 'body_plain' in result
        assert 'body_html' in result

    def test_parse_eml_sender(self, parser, eml_path):
        """解析发件人"""
        result = parser.parse(eml_path)
        assert 'tester@example.com' in result['sender']
        assert 'Tester' in result['sender']

    def test_parse_eml_recipients(self, parser, eml_path):
        """解析收件人"""
        result = parser.parse(eml_path)
        assert len(result['recipients']) == 2
        assert 'user1@example.com' in result['recipients']
        assert 'user2@example.com' in result['recipients']

    def test_parse_eml_date(self, parser, eml_path):
        """解析日期"""
        result = parser.parse(eml_path)
        assert '2026' in result['date']
        assert 'Apr' in result['date']

    def test_parse_eml_body_text(self, parser, eml_path):
        """解析纯文本正文"""
        result = parser.parse(eml_path)
        assert 'test email' in result['body_text'].lower()
        assert 'hello' in result['body_text'].lower()

    def test_parse_eml_body_plain(self, parser, eml_path):
        """解析简化纯文本"""
        result = parser.parse(eml_path)
        # 简化文本应该包含主要内容和签名
        assert 'test email' in result['body_plain'].lower()
        assert 'tester' in result['body_plain'].lower()

    def test_parse_eml_body_html(self, parser, eml_path):
        """解析HTML正文"""
        result = parser.parse(eml_path)
        assert result['body_html'] is not None
        assert len(result['body_html']) > 0
        assert '<html>' in result['body_html'].lower() or '<p>' in result['body_html'].lower()

    def test_parse_eml_headers(self, parser, eml_path):
        """解析邮件头"""
        result = parser.parse(eml_path)
        assert 'headers' in result
        assert isinstance(result['headers'], dict)
        assert 'From' in result['headers']
        assert 'To' in result['headers']

    def test_parse_eml_metadata(self, parser, eml_path):
        """解析元数据"""
        result = parser.parse(eml_path)
        assert 'metadata' in result
        assert 'file_name' in result['metadata']
        assert 'file_size' in result['metadata']

    def test_parse_eml_no_attachments(self, parser, eml_path):
        """无附件邮件"""
        result = parser.parse(eml_path)
        assert result['num_attachments'] == 0
        assert result['attachments'] == []

    def test_parse_eml_message_id(self, parser, eml_path):
        """解析Message-ID"""
        result = parser.parse(eml_path)
        assert 'message_id' in result or 'Message-ID' in result.get('headers', {})


class TestEmailParserUnsupported:
    """不支持格式测试"""

    def test_unsupported_format_raises_error(self):
        """不支持的格式抛出错误"""
        from knowledge.parsers.email_parser import EmailParser
        parser = EmailParser()

        with pytest.raises(ValueError, match="Unsupported email format"):
            parser.parse("test.pdf")


class TestEmailParserEdgeCases:
    """边界情况测试"""

    def test_empty_sender(self):
        """空发件人"""
        from knowledge.parsers.email_parser import EmailParser
        parser = EmailParser()

        # 创建一个最小化的.eml
        minimal_eml = b"""From: \nTo: test@example.com\nSubject: Test\nDate: Wed, 8 Apr 2026 10:00:00\n\nTest body"""

        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.eml', delete=False) as f:
            f.write(minimal_eml)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            assert result['sender'] == '' or result['sender'] == '<>'
        finally:
            os.unlink(temp_path)
