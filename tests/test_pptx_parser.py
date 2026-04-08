"""
测试PowerPoint解析器
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.parsers.pptx_parser import PowerPointParser, PowerPointDocument


class TestPowerPointParser:
    """PowerPoint解析器测试"""

    def setup_method(self):
        """每个测试前创建解析器"""
        self.parser = PowerPointParser()
        self.test_file = "data/test_docs/test.pptx"

    def test_parser_initialization(self):
        """测试解析器初始化"""
        assert self.parser.supported_extensions == [".pptx"]

    def test_parse_success(self):
        """测试成功解析"""
        result = self.parser.parse(self.test_file)

        assert isinstance(result, PowerPointDocument)
        assert len(result.slides) > 0
        assert result.content
        assert result.metadata["slide_count"] == 2

    def test_slide_titles_extracted(self):
        """测试幻灯片标题提取"""
        result = self.parser.parse(self.test_file)

        assert "Test Presentation" in result.slides

    def test_content_extraction(self):
        """测试内容提取"""
        result = self.parser.parse(self.test_file)

        assert "First bullet point" in result.content
        assert "Second bullet point" in result.content

    def test_metadata(self):
        """测试元数据"""
        result = self.parser.parse(self.test_file)

        assert result.metadata["file_name"] == "test.pptx"
        assert result.metadata["slide_count"] == 2
        assert "file_size" in result.metadata

    def test_parse_unsupported_format(self):
        """测试不支持的格式"""
        with pytest.raises(ValueError) as excinfo:
            self.parser.parse("test.docx")

        assert "Unsupported PowerPoint format" in str(excinfo.value)

    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        with pytest.raises(Exception):
            self.parser.parse("nonexistent.pptx")


class TestPowerPointParserSlides:
    """逐幻灯片解析测试"""

    def setup_method(self):
        """每个测试前创建解析器"""
        self.parser = PowerPointParser()
        self.test_file = "data/test_docs/test.pptx"

    def test_parse_slides(self):
        """测试逐幻灯片解析"""
        slides = self.parser.parse_slides(self.test_file)

        assert len(slides) == 2
        assert slides[0]["title"] == "Test Presentation"
        assert "First bullet point" in slides[1]["content"]

    def test_slide_numbers(self):
        """测试幻灯片编号"""
        slides = self.parser.parse_slides(self.test_file)

        assert slides[0]["slide_number"] == 1
        assert slides[1]["slide_number"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
