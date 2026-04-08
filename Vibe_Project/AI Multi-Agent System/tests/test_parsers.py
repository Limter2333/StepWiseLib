"""
文档解析器测试
==============
"""

import sys
import os
import tempfile
import importlib.util
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_parser_module(module_name, file_path):
    """直接加载解析器模块，避免触发knowledge/__init__的循环依赖"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_unified_parser_mapping():
    """测试统一解析器文件类型映射"""
    # 直接加载，避免循环依赖
    unified = load_parser_module('unified_parser', 'knowledge/parsers/unified_parser.py')
    PARSER_MAPPING = unified.PARSER_MAPPING

    # 验证常见类型
    assert PARSER_MAPPING.get(".pdf") == "pdf"
    assert PARSER_MAPPING.get(".docx") == "word"
    assert PARSER_MAPPING.get(".xlsx") == "excel"
    assert PARSER_MAPPING.get(".pptx") == "powerpoint"
    assert PARSER_MAPPING.get(".xml") == "xml"
    assert PARSER_MAPPING.get(".epub") == "epub"
    assert PARSER_MAPPING.get(".csv") == "csv"
    assert PARSER_MAPPING.get(".md") == "markdown"
    assert PARSER_MAPPING.get(".txt") == "text"
    assert PARSER_MAPPING.get(".html") == "web"

    # 验证不支持的类型
    assert PARSER_MAPPING.get(".unknown") is None

    print("    - File type mapping OK")


def test_unified_parser_creation():
    """测试统一解析器创建"""
    unified = load_parser_module('unified_parser', 'knowledge/parsers/unified_parser.py')
    UnifiedParser = unified.UnifiedParser

    parser = UnifiedParser()
    assert parser is not None

    # 检查支持的类型
    supported = parser.get_supported_types()
    assert "PDF" in supported
    assert "Word" in supported
    assert "Excel" in supported
    assert "PowerPoint" in supported
    assert "XML" in supported
    assert "EPUB" in supported
    assert "CSV/TSV" in supported
    assert "Markdown" in supported
    assert "Text" in supported

    print("    - UnifiedParser creation OK")


def test_csv_parser():
    """测试CSV解析器"""
    csv_parser = load_parser_module('csv_parser', 'knowledge/parsers/csv_parser.py')
    CSVParser = csv_parser.CSVParser

    # 创建临时CSV文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("Name,Age,City\n")
        f.write("Alice,30,Beijing\n")
        f.write("Bob,25,Shanghai\n")
        temp_path = f.name

    try:
        parser = CSVParser()
        result = parser.parse(temp_path)

        assert result.headers == ["Name", "Age", "City"]
        assert result.row_count == 2
        assert "Alice" in result.content
        assert "Beijing" in result.content

        print("    - CSV parser OK")
    finally:
        os.unlink(temp_path)


def test_markdown_parser():
    """测试Markdown解析器"""
    md_parser = load_parser_module('markdown_parser', 'knowledge/parsers/markdown_parser.py')
    MarkdownParser = md_parser.MarkdownParser

    # 创建临时MD文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write("# Hello World\n\n")
        f.write("This is a test document.\n\n")
        f.write("## Features\n\n")
        f.write("- Feature 1\n")
        f.write("- Feature 2\n")
        temp_path = f.name

    try:
        parser = MarkdownParser()
        result = parser.parse(temp_path)

        assert result.title == "Hello World"
        assert len(result.headings) >= 2
        assert "This is a test document" in result.content

        # 测试TOC提取
        toc = parser.extract_toc(result)
        assert len(toc) >= 1

        print("    - Markdown parser OK")
    finally:
        os.unlink(temp_path)


def test_text_parser():
    """测试文本解析器"""
    text_parser = load_parser_module('text_parser', 'knowledge/parsers/text_parser.py')
    TextParser = text_parser.TextParser

    # 创建临时TXT文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("Line 1\nLine 2\nLine 3")
        temp_path = f.name

    try:
        parser = TextParser()
        result = parser.parse(temp_path)

        assert result.line_count >= 3
        assert "Line 1" in result.content
        assert result.metadata["word_count"] >= 3

        # 测试统计
        stats = parser.get_statistics(temp_path)
        assert stats["line_count"] >= 3

        print("    - Text parser OK")
    finally:
        os.unlink(temp_path)


def test_text_parser_chunked():
    """测试文本解析器分块"""
    text_parser = load_parser_module('text_parser', 'knowledge/parsers/text_parser.py')
    TextParser = text_parser.TextParser

    # 创建临时TXT文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        for i in range(100):
            f.write(f"Line {i}\n")
        temp_path = f.name

    try:
        parser = TextParser()
        chunks = parser.parse_chunked(temp_path, chunk_size=30)

        assert len(chunks) == 4  # 100行，30行/块 = 4块

        # 验证每块的内容
        assert chunks[0].line_count == 30
        assert chunks[3].line_count == 10

        print("    - Text parser chunked OK")
    finally:
        os.unlink(temp_path)


def test_unified_parser_with_csv():
    """测试统一解析器处理CSV"""
    from knowledge.parsers.unified_parser import get_unified_parser

    # 创建临时CSV文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("A,B,C\n")
        f.write("1,2,3\n")
        temp_path = f.name

    try:
        parser = get_unified_parser()
        result = parser.parse(temp_path)

        assert result.success == True
        assert result.parser_used == "csv"
        assert "A" in result.content
        assert result.error is None

        print("    - Unified parser with CSV OK")
    finally:
        os.unlink(temp_path)


def test_unified_parser_with_markdown():
    """测试统一解析器处理Markdown"""
    from knowledge.parsers.unified_parser import get_unified_parser

    # 创建临时MD文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write("# Test\n\nContent here.\n")
        temp_path = f.name

    try:
        parser = get_unified_parser()
        result = parser.parse(temp_path)

        assert result.success == True
        assert result.parser_used == "markdown"
        assert "Test" in result.content

        print("    - Unified parser with Markdown OK")
    finally:
        os.unlink(temp_path)


def test_unified_parser_unsupported():
    """测试统一解析器处理不支持的文件"""
    from knowledge.parsers.unified_parser import get_unified_parser

    parser = get_unified_parser()
    result = parser.parse("/fake/path/file.xyz")

    assert result.success == False
    assert result.error is not None
    assert "Unsupported" in result.error

    print("    - Unified parser unsupported type OK")


def test_unified_parser_with_powerpoint():
    """测试统一解析器处理PowerPoint"""
    from knowledge.parsers.unified_parser import get_unified_parser

    parser = get_unified_parser()
    result = parser.parse("data/test_docs/test.pptx")

    assert result.success == True
    assert result.parser_used == "powerpoint"
    assert "Test Presentation" in result.content
    assert result.error is None

    print("    - Unified parser with PowerPoint OK")


def test_unified_parser_with_xml():
    """测试统一解析器处理XML"""
    from knowledge.parsers.unified_parser import get_unified_parser

    parser = get_unified_parser()
    result = parser.parse("data/test_docs/test.xml")

    assert result.success == True
    assert result.parser_used == "xml"
    assert "Test Document" in result.content
    assert result.error is None

    print("    - Unified parser with XML OK")


def test_parser_status():
    """测试解析器状态"""
    unified = load_parser_module('unified_parser4', 'knowledge/parsers/unified_parser.py')
    get_unified_parser = unified.get_unified_parser

    parser = get_unified_parser()
    status = parser.get_parser_status()

    # 至少text和csv应该可用（不依赖外部库）
    assert "text" in status
    assert "csv" in status

    # 检查哪些解析器可用
    available = [k for k, v in status.items() if v]
    print(f"    - Available parsers: {', '.join(available)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Document Parsers Test")
    print("=" * 60)
    print()

    tests = [
        ("UnifiedParser Mapping", test_unified_parser_mapping),
        ("UnifiedParser Creation", test_unified_parser_creation),
        ("CSV Parser", test_csv_parser),
        ("Markdown Parser", test_markdown_parser),
        ("Text Parser", test_text_parser),
        ("Text Parser Chunked", test_text_parser_chunked),
        ("UnifiedParser with CSV", test_unified_parser_with_csv),
        ("UnifiedParser with Markdown", test_unified_parser_with_markdown),
        ("UnifiedParser Unsupported", test_unified_parser_unsupported),
        ("Parser Status", test_parser_status),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"[{name}]")
        try:
            test_func()
            passed += 1
            print("    PASS")
        except AssertionError as e:
            print(f"    FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"    ERROR: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Result: {passed}/{passed+failed} passed")
    if failed > 0:
        print(f"Failed: {failed}")
    print("=" * 60)
