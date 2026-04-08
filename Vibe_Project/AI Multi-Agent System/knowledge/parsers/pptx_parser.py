"""
PowerPoint解析器 - PowerPoint Parser
====================================

支持解析 PowerPoint 文件 (.pptx)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import os


@dataclass
class PowerPointDocument:
    """PowerPoint文档结构"""
    slides: List[str]  # 幻灯片标题列表
    content: str  # 解析后的文本内容
    metadata: Dict[str, Any]  # 元数据


class PowerPointParser:
    """PowerPoint解析器

    【功能】
    - 支持 .pptx 格式
    - 解析所有幻灯片
    - 提取标题和文本内容
    - 提取表格和列表内容
    """

    def __init__(self):
        self.supported_extensions = [".pptx"]

    def parse(self, file_path: str) -> PowerPointDocument:
        """解析PowerPoint文件

        Args:
            file_path: 文件路径

        Returns:
            PowerPointDocument: 解析结果
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported PowerPoint format: {extension}")

        try:
            from pptx import Presentation
        except ImportError:
            raise ImportError(
                "python-pptx is required for PowerPoint parsing. "
                "Install with: pip install python-pptx"
            )

        prs = Presentation(file_path)

        slide_titles = []
        content_parts = []

        for idx, slide in enumerate(prs.slides):
            # 提取标题
            title = self._extract_slide_title(slide)
            if title:
                slide_titles.append(title)

            # 提取文本内容
            slide_content = self._extract_slide_content(slide)
            if slide_content:
                content_parts.append(f"=== Slide {idx + 1}: {title or 'Untitled'} ===")
                content_parts.append(slide_content)
                content_parts.append("")

        content = "\n".join(content_parts)

        return PowerPointDocument(
            slides=slide_titles,
            content=content,
            metadata={
                "file_name": path.name,
                "file_size": os.path.getsize(file_path),
                "slide_count": len(prs.slides),
                "title_count": len([t for t in slide_titles if t])
            }
        )

    def _extract_slide_title(self, slide) -> str:
        """提取幻灯片标题"""
        if slide.shapes.title:
            return slide.shapes.title.text.strip()
        return ""

    def _extract_slide_content(self, slide) -> str:
        """提取幻灯片文本内容"""
        content_lines = []

        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue

            # 跳过标题（已单独处理）
            if shape == slide.shapes.title:
                continue

            for paragraph in shape.text_frame.paragraphs:
                text = paragraph.text.strip()
                if text:
                    # 根据缩进级别添加标记
                    level = paragraph.level if hasattr(paragraph, 'level') else 0
                    if level == 0:
                        content_lines.append(text)
                    else:
                        content_lines.append("  " * level + "- " + text)

        return "\n".join(content_lines)

    def parse_slides(self, file_path: str) -> List[Dict[str, Any]]:
        """逐幻灯片解析

        Args:
            file_path: 文件路径

        Returns:
            List[Dict]: 每张幻灯片的详细信息
        """
        try:
            from pptx import Presentation
        except ImportError:
            raise ImportError("python-pptx is required for PowerPoint parsing")

        prs = Presentation(file_path)
        slides_data = []

        for idx, slide in enumerate(prs.slides):
            slide_info = {
                "slide_number": idx + 1,
                "title": self._extract_slide_title(slide),
                "content": self._extract_slide_content(slide),
                "tables": [],
                "images": []
            }

            # 提取表格
            for shape in slide.shapes:
                if shape.has_table:
                    table_data = self._extract_table(shape.table)
                    slide_info["tables"].append(table_data)

            slides_data.append(slide_info)

        return slides_data

    def _extract_table(self, table) -> List[List[str]]:
        """提取表格数据"""
        table_data = []
        for row in table.rows:
            row_data = []
            for cell in row.cells:
                row_data.append(cell.text.strip())
            table_data.append(row_data)
        return table_data


# 延迟导入pptx
try:
    from pptx import Presentation
except ImportError:
    Presentation = None
