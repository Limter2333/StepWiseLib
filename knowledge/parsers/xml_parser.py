"""
XML解析器 - XML Parser
======================

支持解析 XML 文件 (.xml)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import os
import xml.etree.ElementTree as ET


@dataclass
class XMLDocument:
    """XML文档结构"""
    root_tag: str  # 根元素标签
    content: str  # 解析后的文本内容
    metadata: Dict[str, Any]  # 元数据


class XMLParser:
    """XML解析器

    【功能】
    - 支持 .xml 格式
    - 解析XML结构和内容
    - 提取文本内容
    - 支持大文件分块处理
    """

    def __init__(self):
        self.supported_extensions = [".xml"]

    def parse(self, file_path: str) -> XMLDocument:
        """解析XML文件

        Args:
            file_path: 文件路径

        Returns:
            XMLDocument: 解析结果
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported XML format: {extension}")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            content_parts = []
            content_parts.append(f"=== Root: {root.tag} ===")

            # 递归提取所有文本内容
            self._extract_element_text(root, content_parts, level=0)

            content = "\n".join(content_parts)

            return XMLDocument(
                root_tag=root.tag,
                content=content,
                metadata={
                    "file_name": path.name,
                    "file_size": os.path.getsize(file_path),
                    "total_elements": self._count_elements(root)
                }
            )

        except ET.ParseError as e:
            raise ValueError(f"XML parsing error: {str(e)}")

    def _extract_element_text(self, element: ET.Element, content_parts: List[str], level: int) -> None:
        """递归提取元素文本"""
        indent = "  " * level

        # 提取当前元素的文本（如果有）
        if element.text and element.text.strip():
            content_parts.append(f"{indent}<{element.tag}> {element.text.strip()}")

        # 处理子元素
        for child in element:
            tag_with_attrs = f"{indent}<{child.tag}"
            if child.attrib:
                attr_str = " ".join(f'{k}="{v}"' for k, v in child.attrib.items())
                tag_with_attrs += f" {attr_str}"
            tag_with_attrs += ">"

            if child.text and child.text.strip():
                content_parts.append(f"{tag_with_attrs} {child.text.strip()}")
            else:
                content_parts.append(tag_with_attrs)

            # 递归处理子元素
            self._extract_element_text(child, content_parts, level + 1)

            content_parts.append(f"{indent}</{child.tag}>")

    def _count_elements(self, element: ET.Element) -> int:
        """统计元素数量"""
        count = 1
        for child in element:
            count += self._count_elements(child)
        return count

    def parse_to_dict(self, file_path: str) -> Dict[str, Any]:
        """解析XML为字典

        Args:
            file_path: 文件路径

        Returns:
            Dict: XML结构字典
        """
        tree = ET.parse(file_path)
        root = tree.getroot()
        return self._element_to_dict(root)

    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """将Element转换为字典"""
        result = {"tag": element.tag}

        if element.attrib:
            result["attributes"] = element.attrib

        if element.text and element.text.strip():
            result["text"] = element.text.strip()

        children = []
        for child in element:
            children.append(self._element_to_dict(child))

        if children:
            result["children"] = children

        return result


# 延迟导入xml.etree
try:
    import xml.etree.ElementTree as ET
except ImportError:
    ET = None
