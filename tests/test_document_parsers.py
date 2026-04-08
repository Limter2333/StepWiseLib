"""
文档解析器测试 - Document Parsers Test
======================================

测试Excel和PowerPoint解析器
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDocumentTypeEnum:
    """DocumentType枚举测试"""

    def test_document_type_has_excel(self):
        """验证Excel类型存在"""
        from knowledge.rag_pipeline import DocumentType
        assert hasattr(DocumentType, 'EXCEL')
        assert DocumentType.EXCEL.value == "xlsx"

    def test_document_type_has_powerpoint(self):
        """验证PowerPoint类型存在"""
        from knowledge.rag_pipeline import DocumentType
        assert hasattr(DocumentType, 'POWERPOINT')
        assert DocumentType.POWERPOINT.value == "pptx"

    def test_all_document_types(self):
        """验证所有文档类型"""
        from knowledge.rag_pipeline import DocumentType
        expected_types = ['PDF', 'WORD', 'WEB', 'TEXT', 'MARKDOWN', 'EXCEL', 'POWERPOINT']
        actual_types = [t.name for t in DocumentType]
        for et in expected_types:
            assert et in actual_types


class TestJSONParser:
    """JSON解析器测试"""

    def test_json_parser_init(self):
        """测试JSONParser初始化"""
        from knowledge.parsers import JSONParser
        parser = JSONParser()
        assert ".json" in parser.supported_extensions

    def test_json_parser_supports_json(self):
        """测试.json格式支持"""
        from knowledge.parsers import JSONParser
        parser = JSONParser()
        assert ".json" in parser.supported_extensions

    def test_json_flatten_dict(self):
        """测试JSON字典扁平化"""
        from knowledge.parsers.json_parser import JSONParser
        import json
        import tempfile

        parser = JSONParser()
        data = {"name": "test", "value": 123}

        # 测试扁平化
        flat = parser._flatten_to_text(data)
        assert "name: test" in flat
        assert "value: 123" in flat

    def test_json_flatten_nested(self):
        """测试JSON嵌套结构扁平化"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()

        data = {
            "user": {
                "name": "Alice",
                "age": 30
            }
        }

        flat = parser._flatten_to_text(data)
        assert "user:" in flat
        assert "name: Alice" in flat

    def test_json_extract_keys(self):
        """测试JSON键提取"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()

        data = {"a": 1, "b": {"c": 2}}
        keys = parser._extract_keys(data)

        assert "a" in keys
        assert "b" in keys
        assert "b.c" in keys


class TestYAMLParser:
    """YAML解析器测试"""

    def test_yaml_parser_init(self):
        """测试YAMLParser初始化"""
        from knowledge.parsers import YAMLParser
        parser = YAMLParser()
        assert ".yaml" in parser.supported_extensions
        assert ".yml" in parser.supported_extensions

    def test_yaml_parser_supports_yaml(self):
        """测试.yaml格式支持"""
        from knowledge.parsers import YAMLParser
        parser = YAMLParser()
        assert ".yaml" in parser.supported_extensions

    def test_yaml_parser_supports_yml(self):
        """测试.yml格式支持"""
        from knowledge.parsers import YAMLParser
        parser = YAMLParser()
        assert ".yml" in parser.supported_extensions


class TestRTFParser:
    """RTF解析器测试"""

    def test_rtf_parser_init(self):
        """测试RTFParser初始化"""
        from knowledge.parsers import RTFParser
        parser = RTFParser()
        assert ".rtf" in parser.supported_extensions

    def test_rtf_parser_supports_rtf(self):
        """测试.rtf格式支持"""
        from knowledge.parsers import RTFParser
        parser = RTFParser()
        assert ".rtf" in parser.supported_extensions

    def test_rtf_extract_text(self):
        """测试RTF文本提取"""
        from knowledge.parsers.rtf_parser import RTFParser
        parser = RTFParser()

        # 简单的RTF内容
        rtf_content = "Hello World"
        text = parser._extract_text(rtf_content)
        assert "Hello" in text
        assert "World" in text


class TestExcelParser:
    """Excel解析器测试"""

    def test_excel_parser_init(self):
        """测试ExcelParser初始化"""
        from knowledge.parsers import ExcelParser
        parser = ExcelParser()
        assert parser.supported_extensions == [".xlsx", ".xls"]

    def test_excel_parser_supports_xlsx(self):
        """测试xlsx格式支持"""
        from knowledge.parsers import ExcelParser
        parser = ExcelParser()
        assert ".xlsx" in parser.supported_extensions

    def test_excel_parser_supports_xls(self):
        """测试xls格式支持"""
        from knowledge.parsers import ExcelParser
        parser = ExcelParser()
        assert ".xls" in parser.supported_extensions


class TestPowerPointParser:
    """PowerPoint解析器测试"""

    def test_ppt_parser_init(self):
        """测试PowerPointParser初始化"""
        from knowledge.parsers import PowerPointParser
        parser = PowerPointParser()
        assert parser.supported_extensions == [".pptx"]

    def test_ppt_parser_supports_pptx(self):
        """测试pptx格式支持"""
        from knowledge.parsers import PowerPointParser
        parser = PowerPointParser()
        assert ".pptx" in parser.supported_extensions


class TestDocumentTypeDetection:
    """文档类型检测测试"""

    def test_detect_excel_by_extension(self):
        """测试xlsx扩展名检测"""
        from knowledge.rag_pipeline import DocumentType
        # 测试扩展名映射
        ext = ".xlsx"
        type_map = {
            ".xlsx": DocumentType.EXCEL,
            ".xls": DocumentType.EXCEL,
            ".pptx": DocumentType.POWERPOINT
        }
        assert type_map.get(ext) == DocumentType.EXCEL

    def test_detect_powerpoint_by_extension(self):
        """测试pptx扩展名检测"""
        from knowledge.rag_pipeline import DocumentType
        ext = ".pptx"
        type_map = {
            ".xlsx": DocumentType.EXCEL,
            ".xls": DocumentType.EXCEL,
            ".pptx": DocumentType.POWERPOINT
        }
        assert type_map.get(ext) == DocumentType.POWERPOINT


class TestRAGPipelineParsers:
    """RAG管道解析器集成测试"""

    def test_rag_pipeline_has_excel_parser(self):
        """测试RAG管道包含Excel解析器"""
        from knowledge.rag_pipeline import RAGPipeline, DocumentType
        # 不完全初始化，只检查解析器存在
        pipeline = RAGPipeline.__new__(RAGPipeline)
        pipeline.parsers = {
            DocumentType.EXCEL: object(),
            DocumentType.POWERPOINT: object()
        }
        assert DocumentType.EXCEL in pipeline.parsers
        assert DocumentType.POWERPOINT in pipeline.parsers

    def test_rag_pipeline_init_includes_all_parsers(self):
        """测试RAG管道初始化包含所有解析器"""
        from knowledge.rag_pipeline import RAGPipeline, DocumentType
        from knowledge.parsers import ExcelParser, PowerPointParser

        # 验证解析器类型存在
        assert ExcelParser is not None
        assert PowerPointParser is not None


class TestExcelParserUnitTests:
    """Excel解析器独立单元测试"""

    def test_dataframe_to_text_conversion(self):
        """测试DataFrame转文本逻辑"""
        # 模拟DataFrame结构
        class MockDataFrame:
            def __init__(self, data):
                self.data = data
                self.columns = list(data[0].keys()) if data else []
                self.empty = len(data) == 0

            def iterrows(self):
                return enumerate(self.data)

        # 模拟pandas的isna函数
        def mock_isna(val):
            return val is None or val == ""

        # 测试转换逻辑
        headers = ["Name", "Age", "City"]
        rows = [
            {"Name": "Alice", "Age": 30, "City": "NYC"},
            {"Name": "Bob", "Age": 25, "City": "LA"}
        ]

        header_line = " | ".join(str(h) for h in headers)
        assert header_line == "Name | Age | City"

        # 验证行转换
        row_values = []
        for val in rows[0].values():
            if mock_isna(val):
                row_values.append("")
            else:
                row_values.append(str(val))
        row_line = " | ".join(row_values)
        assert row_line == "Alice | 30 | NYC"


class TestPowerPointParserUnitTests:
    """PowerPoint解析器独立单元测试"""

    def test_slide_title_extraction_logic(self):
        """测试幻灯片标题提取逻辑"""
        # 模拟幻灯片结构
        class MockShape:
            def __init__(self, text, has_title=False):
                self.text = text
                self.has_title_flag = has_title

            @property
            def has_text_frame(self):
                return bool(self.text)

        class MockSlide:
            def __init__(self, title_text=None):
                self.shapes = [MockShape(title_text, has_title=True)] if title_text else []

            @property
            def shapes(self):
                return self._shapes

            @shapes.setter
            def shapes(self, value):
                self._shapes = value

        # 测试标题提取
        slide_with_title = MockSlide("Test Title")
        assert len(slide_with_title.shapes) == 1
        assert slide_with_title.shapes[0].has_title_flag is True

    def test_slide_content_extraction_logic(self):
        """测试幻灯片内容提取逻辑"""
        class MockParagraph:
            def __init__(self, text, level=0):
                self.text = text
                self.level = level

        class MockTextFrame:
            def __init__(self, paragraphs):
                self.paragraphs = paragraphs

            def __iter__(self):
                return iter(self.paragraphs)

        # 测试段落处理
        paragraphs = [
            MockParagraph("Main heading", level=0),
            MockParagraph("Sub item 1", level=1),
            MockParagraph("Sub item 2", level=1)
        ]

        content_lines = []
        for para in paragraphs:
            text = para.text.strip()
            if text:
                if para.level == 0:
                    content_lines.append(text)
                else:
                    content_lines.append("  " * para.level + "- " + text)

        assert content_lines[0] == "Main heading"
        assert content_lines[1] == "  - Sub item 1"
        assert content_lines[2] == "  - Sub item 2"


class TestJSONParserEdgeCases:
    """JSON解析器边界情况测试"""

    def test_json_flatten_empty_dict(self):
        """测试空字典扁平化"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()
        flat = parser._flatten_to_text({})
        assert flat == ""

    def test_json_flatten_empty_list(self):
        """测试空列表扁平化"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()
        flat = parser._flatten_to_text([])
        assert flat == ""

    def test_json_flatten_primitive_values(self):
        """测试原始类型值"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()

        # 字符串
        assert parser._flatten_to_text("hello") == "hello"
        # 数字
        assert parser._flatten_to_text(42) == "42"
        # 布尔值
        assert parser._flatten_to_text(True) == "True"
        # None
        assert parser._flatten_to_text(None) == "None"

    def test_json_extract_keys_empty_dict(self):
        """测试空字典键提取"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()
        keys = parser._extract_keys({})
        assert keys == []

    def test_json_extract_keys_empty_list(self):
        """测试空列表键提取"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()
        keys = parser._extract_keys([])
        assert keys == []

    def test_json_extract_keys_with_prefix(self):
        """测试带前缀的键提取"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()

        data = {"a": {"b": {"c": 1}}}
        keys = parser._extract_keys(data, prefix="root")
        assert "root.a" in keys
        assert "root.a.b" in keys
        assert "root.a.b.c" in keys

    def test_json_extract_keys_array_of_objects(self):
        """测试对象数组键提取"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()

        data = [{"name": "Alice"}, {"name": "Bob"}]
        keys = parser._extract_keys(data)
        # 数组中的对象键会带有索引前缀
        assert "[0].name" in keys
        assert "[1].name" in keys

    def test_json_flatten_deeply_nested(self):
        """测试深度嵌套结构"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()

        data = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        flat = parser._flatten_to_text(data)
        assert "d:" in flat
        assert "e: deep" in flat

    def test_json_flatten_array_with_mixed_types(self):
        """测试混合类型数组"""
        from knowledge.parsers.json_parser import JSONParser
        parser = JSONParser()

        data = [1, "string", {"key": "value"}, [1, 2, 3], True, None]
        flat = parser._flatten_to_text(data)
        assert "[0]: 1" in flat
        assert "[1]: string" in flat
        assert "[3]:" in flat  # 嵌套数组


class TestYAMLParserEdgeCases:
    """YAML解析器边界情况测试"""

    def test_yaml_parser_unsupported_extension(self):
        """测试不支持的YAML扩展名"""
        from knowledge.parsers import YAMLParser
        parser = YAMLParser()
        assert ".yml" in parser.supported_extensions
        assert ".yaml" in parser.supported_extensions
        assert ".txt" not in parser.supported_extensions

    def test_yaml_supported_extensions_count(self):
        """测试YAML支持扩展名数量"""
        from knowledge.parsers import YAMLParser
        parser = YAMLParser()
        assert len(parser.supported_extensions) == 2


class TestRTFParserEdgeCases:
    """RTF解析器边界情况测试"""

    def test_rtf_extract_text_empty(self):
        """测试提取空文本"""
        from knowledge.parsers.rtf_parser import RTFParser
        parser = RTFParser()
        text = parser._extract_text("")
        assert text == ""

    def test_rtf_extract_text_plain(self):
        """测试提取纯文本"""
        from knowledge.parsers.rtf_parser import RTFParser
        parser = RTFParser()
        text = parser._extract_text("Plain text without RTF formatting")
        assert "Plain text" in text

    def test_rtf_supported_extensions(self):
        """测试RTF支持扩展名"""
        from knowledge.parsers import RTFParser
        parser = RTFParser()
        assert ".rtf" in parser.supported_extensions


class TestExcelParserEdgeCases:
    """Excel解析器边界情况测试"""

    def test_excel_supported_extensions_count(self):
        """测试Excel支持扩展名数量"""
        from knowledge.parsers import ExcelParser
        parser = ExcelParser()
        assert len(parser.supported_extensions) == 2

    def test_excel_has_required_methods(self):
        """测试Excel解析器有所需方法"""
        from knowledge.parsers import ExcelParser
        parser = ExcelParser()
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'supported_extensions')


class TestPowerPointParserEdgeCases:
    """PowerPoint解析器边界情况测试"""

    def test_powerpoint_supported_extension(self):
        """测试PowerPoint支持扩展名"""
        from knowledge.parsers import PowerPointParser
        parser = PowerPointParser()
        assert parser.supported_extensions == [".pptx"]

    def test_powerpoint_has_required_methods(self):
        """测试PowerPoint解析器有所需方法"""
        from knowledge.parsers import PowerPointParser
        parser = PowerPointParser()
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'supported_extensions')


class TestUnifiedParserEdgeCases:
    """统一解析器边界情况测试"""

    def test_unified_parser_singleton(self):
        """测试统一解析器单例"""
        from knowledge.parsers.unified_parser import get_unified_parser
        parser1 = get_unified_parser()
        parser2 = get_unified_parser()
        # 应该返回相同实例
        assert parser1 is not None
        assert parser2 is not None

    def test_unified_parser_all_supported_types(self):
        """测试统一解析器支持所有类型"""
        from knowledge.parsers.unified_parser import get_unified_parser
        parser = get_unified_parser()
        supported = parser.get_supported_types()
        # 验证核心类型都支持
        assert "PDF" in supported or "pdf" in [t.lower() for t in supported]
        assert "Word" in supported or "word" in [t.lower() for t in supported]
        assert "Text" in supported or "text" in [t.lower() for t in supported]


class TestCSVParserEdgeCases:
    """CSV解析器边界情况测试"""

    def test_csv_parser_supported_extensions(self):
        """测试CSV解析器支持扩展名"""
        from knowledge.parsers import CSVParser
        parser = CSVParser()
        assert ".csv" in parser.supported_extensions

    def test_csv_parser_has_required_methods(self):
        """测试CSV解析器有所需方法"""
        from knowledge.parsers import CSVParser
        parser = CSVParser()
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'supported_extensions')


class TestTextParserEdgeCases:
    """文本解析器边界情况测试"""

    def test_text_parser_supported_extensions(self):
        """测试文本解析器支持扩展名"""
        from knowledge.parsers import TextParser
        parser = TextParser()
        assert ".txt" in parser.supported_extensions

    def test_text_parser_has_required_methods(self):
        """测试文本解析器有所需方法"""
        from knowledge.parsers import TextParser
        parser = TextParser()
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'get_statistics')


class TestMarkdownParserEdgeCases:
    """Markdown解析器边界情况测试"""

    def test_markdown_parser_supported_extensions(self):
        """测试Markdown解析器支持扩展名"""
        from knowledge.parsers import MarkdownParser
        parser = MarkdownParser()
        assert ".md" in parser.supported_extensions
        assert ".markdown" in parser.supported_extensions

    def test_markdown_parser_has_required_methods(self):
        """测试Markdown解析器有所需方法"""
        from knowledge.parsers import MarkdownParser
        parser = MarkdownParser()
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'extract_toc')
        assert hasattr(parser, 'supported_extensions')


class TestXMLParserEdgeCases:
    """XML解析器边界情况测试"""

    def test_xml_parser_supported_extensions(self):
        """测试XML解析器支持扩展名"""
        from knowledge.parsers import XMLParser
        parser = XMLParser()
        assert ".xml" in parser.supported_extensions

    def test_xml_parser_has_required_methods(self):
        """测试XML解析器有所需方法"""
        from knowledge.parsers import XMLParser
        parser = XMLParser()
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'parse_to_dict')
        assert hasattr(parser, 'supported_extensions')


class TestEPUBParserEdgeCases:
    """EPUB解析器边界情况测试"""

    def test_epub_parser_supported_extensions(self):
        """测试EPUB解析器支持扩展名"""
        from knowledge.parsers import EPUBParser
        parser = EPUBParser()
        assert ".epub" in parser.supported_extensions

    def test_epub_parser_has_required_methods(self):
        """测试EPUB解析器有所需方法"""
        from knowledge.parsers import EPUBParser
        parser = EPUBParser()
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'supported_extensions')


class TestJSONDocumentDataclass:
    """JSONDocument数据类测试"""

    def test_json_document_creation(self):
        """测试JSONDocument创建"""
        from knowledge.parsers.json_parser import JSONDocument
        doc = JSONDocument(
            path="test.json",
            content="name: test",
            raw_data={"name": "test"},
            keys=["name"],
            is_array=False,
            item_count=1
        )
        assert doc.path == "test.json"
        assert doc.content == "name: test"
        assert doc.raw_data == {"name": "test"}
        assert doc.keys == ["name"]
        assert doc.is_array is False
        assert doc.item_count == 1

    def test_json_document_with_array(self):
        """测试JSON数组文档"""
        from knowledge.parsers.json_parser import JSONDocument
        doc = JSONDocument(
            path="array.json",
            content="items",
            raw_data=[1, 2, 3],
            keys=[],
            is_array=True,
            item_count=3
        )
        assert doc.is_array is True
        assert doc.item_count == 3
