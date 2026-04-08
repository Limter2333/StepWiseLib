"""
PDF文档解析器
=============

【学习要点】
1. PDF解析库对比
   - PyPDF2: 简单，支持基本提取
   - PyMuPDF(fitz): 更强大，保留格式
   - pdfplumber: 表格处理强

2. PDF结构
   - Page: 每一页
   - Text: 文本内容
   - Image: 图片
   - Table: 表格
"""

from typing import List, Dict, Optional
from pathlib import Path
import PyPDF2


class PDFParser:
    """PDF解析器

    【使用流程】
    1. 打开PDF文件
    2. 遍历每一页
    3. 提取文本
    4. 提取元数据
    """

    def __init__(self):
        self.supported_extensions = [".pdf"]

    def parse(
        self,
        file_path: str,
        extract_images: bool = False
    ) -> Dict:
        """解析PDF文件

        Args:
            file_path: PDF文件路径
            extract_images: 是否提取图片

        Returns:
            解析结果字典
        """
        result = {
            "file_path": file_path,
            "num_pages": 0,
            "content": [],
            "metadata": {}
        }

        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)

            # 提取元数据
            if reader.metadata:
                result["metadata"] = {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                }

            result["num_pages"] = len(reader.pages)

            # 逐页提取文本
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                result["content"].append({
                    "page_num": page_num + 1,
                    "text": text,
                    "char_count": len(text) if text else 0
                })

        return result

    def extract_page(
        self,
        file_path: str,
        page_num: int
    ) -> str:
        """提取指定页面

        Args:
            file_path: PDF文件路径
            page_num: 页码（从1开始）

        Returns:
            页面文本
        """
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if 0 < page_num <= len(reader.pages):
                return reader.pages[page_num - 1].extract_text()
        return ""

    def get_info(self, file_path: str) -> Dict:
        """获取PDF信息（不解析全部内容）"""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return {
                "num_pages": len(reader.pages),
                "metadata": reader.metadata if reader.metadata else {},
                "is_encrypted": reader.is_encrypted
            }
