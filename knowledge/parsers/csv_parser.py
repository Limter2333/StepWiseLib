"""
CSV解析器 - CSV Parser
=====================

支持解析 CSV 文件 (.csv)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import csv
import os


@dataclass
class CSVDocument:
    """CSV文档结构"""
    headers: List[str]  # 列名
    row_count: int  # 行数
    content: str  # 解析后的文本内容
    metadata: Dict[str, Any]  # 元数据


class CSVParser:
    """CSV解析器

    【功能】
    - 支持 .csv 格式
    - 自动检测分隔符（逗号、制表符、分号等）
    - 处理引号和转义字符
    - 支持大文件分块处理
    """

    def __init__(self):
        self.supported_extensions = [".csv", ".tsv", ".txt"]

    def parse(self, file_path: str, delimiter: str = None) -> CSVDocument:
        """解析CSV文件

        Args:
            file_path: 文件路径
            delimiter: 分隔符（None则自动检测）

        Returns:
            CSVDocument: 解析结果
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.supported_extensions and not delimiter:
            raise ValueError(f"Unsupported format: {extension}")

        try:
            # 自动检测分隔符
            if delimiter is None:
                delimiter = self._detect_delimiter(file_path)

            headers = []
            rows = []

            with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                reader = csv.reader(f, delimiter=delimiter)

                # 读取所有行
                all_rows = list(reader)

                if not all_rows:
                    return CSVDocument(
                        headers=[],
                        row_count=0,
                        content="",
                        metadata={
                            "file_name": path.name,
                            "file_size": os.path.getsize(file_path),
                            "delimiter": delimiter
                        }
                    )

                # 第一行是标题
                headers = [str(h).strip() for h in all_rows[0]]
                rows = all_rows[1:]

            # 转换为文本
            content = self._format_content(headers, rows)

            return CSVDocument(
                headers=headers,
                row_count=len(rows),
                content=content,
                metadata={
                    "file_name": path.name,
                    "file_size": os.path.getsize(file_path),
                    "delimiter": delimiter,
                    "column_count": len(headers)
                }
            )

        except Exception as e:
            raise RuntimeError(f"Failed to parse CSV: {e}")

    def _detect_delimiter(self, file_path: str) -> str:
        """自动检测分隔符"""
        # 常见分隔符
        delimiters = [',', '\t', ';', '|']

        # 读取前几行
        with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            sample = [f.readline() for _ in range(5)]

        # 统计每个分隔符的出现次数
        counts = {}
        for delim in delimiters:
            counts[delim] = sum(line.count(delim) for line in sample)

        # 返回出现次数最多的分隔符
        return max(counts, key=counts.get) if counts else ','

    def _format_content(self, headers: List[str], rows: List[List[str]]) -> str:
        """格式化内容为文本"""
        lines = []

        # 标题行
        lines.append(" | ".join(headers))

        # 数据行
        for row in rows:
            # 处理空值
            values = [str(v).strip() if v else "" for v in row]
            lines.append(" | ".join(values))

        return "\n".join(lines)

    def parse_streaming(self, file_path: str, chunk_size: int = 1000):
        """流式解析大CSV文件

        Args:
            file_path: 文件路径
            chunk_size: 每次返回的行数

        Yields:
            CSVDocument: 分块结果
        """
        path = Path(file_path)

        with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.reader(f, delimiter=',')

            # 读取标题
            headers = [str(h).strip() for h in next(reader)]

            # 分块读取
            chunk_rows = []
            chunk_index = 0

            for row in reader:
                chunk_rows.append(row)

                if len(chunk_rows) >= chunk_size:
                    content = self._format_content(headers, chunk_rows)

                    yield CSVDocument(
                        headers=headers,
                        row_count=len(chunk_rows),
                        content=content,
                        metadata={
                            "file_name": path.name,
                            "chunk_index": chunk_index,
                            "chunk_size": chunk_size
                        }
                    )

                    chunk_rows = []
                    chunk_index += 1

            # 处理剩余行
            if chunk_rows:
                content = self._format_content(headers, chunk_rows)

                yield CSVDocument(
                    headers=headers,
                    row_count=len(chunk_rows),
                    content=content,
                    metadata={
                        "file_name": path.name,
                        "chunk_index": chunk_index,
                        "chunk_size": chunk_size
                    }
                )
