"""
文本解析器 - Text Parser
=======================

支持解析纯文本文件 (.txt)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import os
import re


@dataclass
class TextDocument:
    """文本文档结构"""
    content: str  # 文档内容
    line_count: int  # 行数
    metadata: Dict[str, Any]  # 元数据


class TextParser:
    """文本解析器

    【功能】
    - 支持 .txt 格式
    - 自动检测编码（UTF-8, GBK, GB2312等）
    - 统计行数、字数、段落数
    - 支持大文件分块读取
    """

    # 支持的编码列表（按优先级）
    ENCODINGS = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'latin-1']

    def __init__(self):
        self.supported_extensions = [".txt", ".text", ".log"]

    def parse(self, file_path: str) -> TextDocument:
        """解析文本文件

        Args:
            file_path: 文件路径

        Returns:
            TextDocument: 解析结果
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported text format: {extension}")

        # 自动检测编码
        encoding = self._detect_encoding(file_path)

        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()

        # 统计
        lines = content.split('\n')
        line_count = len(lines)
        char_count = len(content)
        word_count = len(re.findall(r'\S+', content))
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])

        return TextDocument(
            content=content,
            line_count=line_count,
            metadata={
                "file_name": path.name,
                "file_size": os.path.getsize(file_path),
                "encoding": encoding,
                "char_count": char_count,
                "word_count": word_count,
                "paragraph_count": paragraph_count
            }
        )

    def _detect_encoding(self, file_path: str) -> str:
        """自动检测文件编码"""
        for encoding in self.ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue

        # 默认返回UTF-8
        return 'utf-8'

    def parse_chunked(self, file_path: str, chunk_size: int = 1000) -> List[TextDocument]:
        """分块解析大文本文件

        Args:
            file_path: 文件路径
            chunk_size: 每块的行数

        Returns:
            List[TextDocument]: 分块结果
        """
        path = Path(file_path)
        encoding = self._detect_encoding(file_path)

        results = []
        chunk_index = 0

        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            chunk_lines = []

            for line in f:
                chunk_lines.append(line.rstrip('\n'))

                if len(chunk_lines) >= chunk_size:
                    content = '\n'.join(chunk_lines)

                    results.append(TextDocument(
                        content=content,
                        line_count=len(chunk_lines),
                        metadata={
                            "file_name": path.name,
                            "chunk_index": chunk_index,
                            "chunk_size": chunk_size
                        }
                    ))

                    chunk_lines = []
                    chunk_index += 1

            # 处理剩余内容
            if chunk_lines:
                content = '\n'.join(chunk_lines)

                results.append(TextDocument(
                    content=content,
                    line_count=len(chunk_lines),
                    metadata={
                        "file_name": path.name,
                        "chunk_index": chunk_index,
                        "chunk_size": chunk_size
                    }
                ))

        return results

    def extract_lines_with_pattern(self, file_path: str, pattern: str) -> List[str]:
        """提取匹配模式的行

        Args:
            file_path: 文件路径
            pattern: 正则表达式模式

        Returns:
            匹配的行列表
        """
        encoding = self._detect_encoding(file_path)
        matches = []

        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            for line in f:
                if re.search(pattern, line):
                    matches.append(line.rstrip())

        return matches

    def get_statistics(self, file_path: str) -> Dict[str, Any]:
        """获取文件统计信息

        Returns:
            统计信息字典
        """
        doc = self.parse(file_path)

        return {
            "file_name": doc.metadata["file_name"],
            "file_size": doc.metadata["file_size"],
            "line_count": doc.line_count,
            "char_count": doc.metadata["char_count"],
            "word_count": doc.metadata["word_count"],
            "paragraph_count": doc.metadata["paragraph_count"],
            "encoding": doc.metadata["encoding"]
        }
