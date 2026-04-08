"""
Word文档解析器
==============

【学习要点】
1. python-docx库
   - 读取Word文档
   - 提取段落、表格
   - 保留基本格式

2. Word文档结构
   - Document: 整个文档
   - Paragraph: 段落
   - Table: 表格
   - Run: 文本片段（含格式）
"""

from typing import List, Dict
from docx import Document


class WordParser:
    """Word文档解析器"""

    def __init__(self):
        self.supported_extensions = [".docx", ".doc"]

    def parse(self, file_path: str) -> Dict:
        """解析Word文档

        Args:
            file_path: Word文件路径

        Returns:
            解析结果字典
        """
        doc = Document(file_path)

        result = {
            "file_path": file_path,
            "num_paragraphs": len(doc.paragraphs),
            "num_tables": len(doc.tables),
            "content": [],
            "metadata": {}
        }

        # 提取段落
        for para_num, para in enumerate(doc.paragraphs):
            if para.text.strip():  # 跳过空段落
                result["content"].append({
                    "type": "paragraph",
                    "index": para_num,
                    "text": para.text,
                    "style": str(para.style.name) if para.style else "Normal"
                })

        # 提取表格
        for table_num, table in enumerate(doc.tables):
            for row_num, row in enumerate(table.rows):
                row_text = [cell.text for cell in row.cells]
                result["content"].append({
                    "type": "table",
                    "table_index": table_num,
                    "row_index": row_num,
                    "text": " | ".join(row_text)
                })

        # 提取核心属性
        core_props = doc.core_properties
        result["metadata"] = {
            "author": core_props.author,
            "title": core_props.title,
            "subject": core_props.subject,
            "keywords": core_props.keywords,
            "created": str(core_props.created) if core_props.created else None,
            "modified": str(core_props.modified) if core_props.modified else None
        }

        return result
