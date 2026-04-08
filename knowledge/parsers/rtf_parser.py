"""
RTF Parser - Rich Text Format文档解析器
========================================

解析RTF文件，提取纯文本内容
"""

from typing import Dict, Optional
from dataclasses import dataclass
import re
from pathlib import Path


@dataclass
class RTFDocument:
    """RTF文档"""
    path: str
    content: str  # 纯文本内容
    char_count: int  # 字符数
    word_count: int  # 单词数（估算）


class RTFParser:
    """RTF解析器

    【功能】
    - 解析RTF文件
    - 提取纯文本内容
    - 移除格式控制码
    """

    def __init__(self):
        self.supported_extensions = [".rtf"]

    def parse(self, file_path: str) -> RTFDocument:
        """解析RTF文件

        Args:
            file_path: 文件路径

        Returns:
            RTFDocument对象
        """
        extension = Path(file_path).suffix.lower()
        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported RTF format: {extension}")

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            rtf_content = f.read()

        # 提取纯文本
        plain_text = self._extract_text(rtf_content)
        char_count = len(plain_text)
        word_count = len(plain_text.split())

        return RTFDocument(
            path=file_path,
            content=plain_text,
            char_count=char_count,
            word_count=word_count
        )

    def _extract_text(self, rtf_content: str) -> str:
        """从RTF内容中提取纯文本

        Args:
            rtf_content: RTF格式内容

        Returns:
            纯文本内容
        """
        # 如果内容本身是纯文本，直接返回
        if not rtf_content.startswith('{\\rtf'):
            return rtf_content.strip()

        # 替换常见的RTF控制码为空格
        text = rtf_content

        # 移除RTF头部
        text = re.sub(r'\{\\rtf[^{]*', '', text)

        # 处理控制词（保留普通文本）
        text = re.sub(r'\\[a-z]+\d*\s?', ' ', text)

        # 处理Unicode转义
        text = re.sub(r'\\u(\d+)\s?', lambda m: chr(int(m.group(1))) if int(m.group(1)) < 65536 else '', text)

        # 移除花括号（仅保留文本）
        text = re.sub(r'[{}\\]', '', text)

        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)

        return text.strip()


def get_rtf_parser() -> RTFParser:
    """获取RTF解析器单例"""
    return RTFParser()
