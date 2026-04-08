"""
统一解析器 - Unified Parser
=========================

自动检测文件类型并选择合适的解析器
"""

from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass


# 扩展名到解析器的映射
PARSER_MAPPING = {
    # PDF
    ".pdf": "pdf",
    # Office
    ".docx": "word",
    ".doc": "word",
    ".xlsx": "excel",
    ".xls": "excel",
    ".pptx": "powerpoint",
    # XML
    ".xml": "xml",
    # EPUB
    ".epub": "epub",
    # Web
    ".html": "web",
    ".htm": "web",
    # Text
    ".txt": "text",
    ".log": "text",
    # Data
    ".csv": "csv",
    ".tsv": "csv",
    # Markdown
    ".md": "markdown",
    ".markdown": "markdown",
    ".mdown": "markdown",
    # Configuration & Data
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    # Rich Text
    ".rtf": "rtf",
}


@dataclass
class ParseResult:
    """解析结果"""
    success: bool
    parser_used: str
    content: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


class UnifiedParser:
    """统一解析器

    【功能】
    - 自动检测文件类型
    - 选择合适的解析器
    - 统一返回格式
    - 错误处理
    """

    def __init__(self):
        self.parsers = {}
        self._init_parsers()

    def _init_parsers(self):
        """初始化所有解析器"""
        try:
            from .pdf_parser import PDFParser
            self.parsers["pdf"] = PDFParser()
        except ImportError as e:
            self.parsers["pdf_error"] = str(e)

        try:
            from .word_parser import WordParser
            self.parsers["word"] = WordParser()
        except ImportError as e:
            self.parsers["word_error"] = str(e)

        try:
            from .web_parser import WebParser
            self.parsers["web"] = WebParser()
        except ImportError as e:
            self.parsers["web_error"] = str(e)

        try:
            from .excel_parser import ExcelParser
            self.parsers["excel"] = ExcelParser()
        except ImportError as e:
            self.parsers["excel_error"] = str(e)

        try:
            from .csv_parser import CSVParser
            self.parsers["csv"] = CSVParser()
        except ImportError as e:
            self.parsers["csv_error"] = str(e)

        try:
            from .markdown_parser import MarkdownParser
            self.parsers["markdown"] = MarkdownParser()
        except ImportError as e:
            self.parsers["markdown_error"] = str(e)

        try:
            from .text_parser import TextParser
            self.parsers["text"] = TextParser()
        except ImportError as e:
            self.parsers["text_error"] = str(e)

        try:
            from .pptx_parser import PowerPointParser
            self.parsers["powerpoint"] = PowerPointParser()
        except ImportError as e:
            self.parsers["powerpoint_error"] = str(e)

        try:
            from .xml_parser import XMLParser
            self.parsers["xml"] = XMLParser()
        except ImportError as e:
            self.parsers["xml_error"] = str(e)

        try:
            from .epub_parser import EPUBParser
            self.parsers["epub"] = EPUBParser()
        except ImportError as e:
            self.parsers["epub_error"] = str(e)

        try:
            from .json_parser import JSONParser
            self.parsers["json"] = JSONParser()
        except ImportError as e:
            self.parsers["json_error"] = str(e)

        try:
            from .yaml_parser import YAMLParser
            self.parsers["yaml"] = YAMLParser()
        except ImportError as e:
            self.parsers["yaml_error"] = str(e)

        try:
            from .rtf_parser import RTFParser
            self.parsers["rtf"] = RTFParser()
        except ImportError as e:
            self.parsers["rtf_error"] = str(e)

    def parse(self, file_path: str) -> ParseResult:
        """解析文件

        Args:
            file_path: 文件路径

        Returns:
            ParseResult: 统一格式的解析结果
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        # 获取解析器类型
        parser_type = PARSER_MAPPING.get(extension)

        if not parser_type:
            return ParseResult(
                success=False,
                parser_used="",
                content="",
                metadata={},
                error=f"Unsupported file type: {extension}"
            )

        # 检查解析器是否可用
        if parser_type not in self.parsers:
            error_key = f"{parser_type}_error"
            error_msg = self.parsers.get(error_key, "Parser not available")

            return ParseResult(
                success=False,
                parser_used=parser_type,
                content="",
                metadata={},
                error=f"{parser_type} parser not available: {error_msg}"
            )

        # 执行解析
        parser = self.parsers[parser_type]

        try:
            result = parser.parse(file_path)

            # 统一转换为ParseResult
            if hasattr(result, 'content'):
                # 有content属性的dataclass
                return ParseResult(
                    success=True,
                    parser_used=parser_type,
                    content=result.content,
                    metadata=result.metadata if hasattr(result, 'metadata') else {}
                )
            else:
                return ParseResult(
                    success=True,
                    parser_used=parser_type,
                    content=str(result),
                    metadata={}
                )

        except Exception as e:
            return ParseResult(
                success=False,
                parser_used=parser_type,
                content="",
                metadata={},
                error=str(e)
            )

    def get_supported_types(self) -> Dict[str, list]:
        """获取支持的文档类型"""
        return {
            "PDF": [".pdf"],
            "Word": [".docx", ".doc"],
            "Excel": [".xlsx", ".xls"],
            "PowerPoint": [".pptx"],
            "XML": [".xml"],
            "EPUB": [".epub"],
            "CSV/TSV": [".csv", ".tsv"],
            "Markdown": [".md", ".markdown", ".mdown"],
            "Text": [".txt", ".log"],
            "Web": [".html", ".htm"],
            "JSON": [".json"],
            "YAML": [".yaml", ".yml"],
            "RTF": [".rtf"]
        }

    def get_parser_status(self) -> Dict[str, bool]:
        """获取各解析器状态"""
        status = {}
        for key in ["pdf", "word", "web", "excel", "csv", "markdown", "text", "powerpoint", "xml", "epub", "json", "yaml", "rtf"]:
            status[key] = key in self.parsers
        return status


# 全局实例
_unified_parser: Optional[UnifiedParser] = None


def get_unified_parser() -> UnifiedParser:
    """获取统一解析器实例"""
    global _unified_parser
    if _unified_parser is None:
        _unified_parser = UnifiedParser()
    return _unified_parser
