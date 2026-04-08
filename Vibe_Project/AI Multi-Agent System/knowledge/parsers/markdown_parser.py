"""
Markdown解析器 - Markdown Parser
==============================

支持解析 Markdown 文件 (.md, .markdown)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import re
import os


@dataclass
class MarkdownDocument:
    """Markdown文档结构"""
    title: str  # 标题
    headings: List[str]  # 所有标题
    content: str  # 纯文本内容
    raw_content: str = ""  # 原始markdown内容
    metadata: Dict[str, Any] = None  # 元数据


class MarkdownParser:
    """Markdown解析器

    【功能】
    - 支持 .md 和 .markdown 格式
    - 提取标题层级结构
    - 提取代码块
    - 提取链接和图片
    - 支持表格转换为文本
    """

    def __init__(self):
        self.supported_extensions = [".md", ".markdown", ".mdown"]

    def parse(self, file_path: str) -> MarkdownDocument:
        """解析Markdown文件

        Args:
            file_path: 文件路径

        Returns:
            MarkdownDocument: 解析结果
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported Markdown format: {extension}")

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # 提取标题
        title = self._extract_title(content)
        headings = self._extract_headings(content)

        # 转换为纯文本
        plain_text = self._to_plain_text(content)

        return MarkdownDocument(
            title=title,
            headings=headings,
            content=plain_text,
            raw_content=content,
            metadata={
                "file_name": path.name,
                "file_size": os.path.getsize(file_path),
                "heading_count": len(headings)
            }
        )

    def _extract_title(self, content: str) -> str:
        """提取文档标题（第一个#标题）"""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _extract_headings(self, content: str) -> List[str]:
        """提取所有标题"""
        headings = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append(f"{'#' * level} {text}")
        return headings

    def _to_plain_text(self, content: str) -> str:
        """将Markdown转换为纯文本"""
        # 移除YAML front matter
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

        # 移除代码块
        content = re.sub(r'```[\s\S]*?```', '[代码块]', content)

        # 移除行内代码
        content = re.sub(r'`([^`]+)`', r'\1', content)

        # 移除图片
        content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', content)

        # 处理链接，保留文本
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

        # 处理表格
        content = self._tables_to_text(content)

        # 移除标题标记
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)

        # 移除加粗和斜体
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)

        # 移除引用标记
        content = re.sub(r'^>\s+', '', content, flags=re.MULTILINE)

        # 移除列表标记
        content = re.sub(r'^[-*+]\s+', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\d+\.\s+', '', content, flags=re.MULTILINE)

        # 移除水平线
        content = re.sub(r'^[-*_]{3,}$', '', content, flags=re.MULTILINE)

        return content.strip()

    def _tables_to_text(self, content: str) -> str:
        """将表格转换为文本"""
        table_pattern = r'(\|.+\|\n)+'

        def format_table(match):
            lines = match.group(0).strip().split('\n')

            # 解析表格
            rows = []
            for line in lines:
                if re.match(r'^\|[-:\s]+\|$', line):
                    continue  # 跳过分隔行
                cells = [c.strip() for c in line.strip('|').split('|')]
                rows.append(' | '.join(cells))

            return '\n'.join(rows) + '\n'

        return re.sub(table_pattern, format_table, content)

    def extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """提取代码块

        Returns:
            List[{"language": str, "code": str}]
        """
        blocks = []
        pattern = r'```(\w+)?\n([\s\S]*?)```'

        for match in re.finditer(pattern, content):
            language = match.group(1) or ""
            code = match.group(2).strip()
            blocks.append({
                "language": language,
                "code": code
            })

        return blocks

    def extract_links(self, content: str) -> List[Dict[str, str]]:
        """提取链接

        Returns:
            List[{"text": str, "url": str}]
        """
        links = []
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'

        for match in re.finditer(pattern, content):
            links.append({
                "text": match.group(1),
                "url": match.group(2)
            })

        return links

    def extract_toc(self, document: MarkdownDocument, max_level: int = 3) -> List[str]:
        """提取目录

        Args:
            document: MarkdownDocument文档对象
            max_level: 最大标题级别

        Returns:
            目录列表
        """
        toc = []
        pattern = rf'^(#{{1,{max_level}}})\s+(.+)$'

        for match in re.finditer(pattern, document.raw_content, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2).strip()
            toc.append('  ' * (level - 1) + f"- {text}")

        return toc
