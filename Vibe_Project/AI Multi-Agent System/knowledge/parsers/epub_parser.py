"""
EPUB解析器 - EPUB Parser
========================

支持解析 EPUB 电子书文件 (.epub)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import os
import zipfile
import xml.etree.ElementTree as ET


@dataclass
class EPUBDocument:
    """EPUB文档结构"""
    title: str  # 书名
    content: str  # 解析后的文本内容
    metadata: Dict[str, Any]  # 元数据


class EPUBParser:
    """EPUB解析器

    【功能】
    - 支持 .epub 格式（本质上是一个ZIP文件）
    - 解析书籍元数据
    - 提取章节内容
    - 支持大文件分块处理
    """

    def __init__(self):
        self.supported_extensions = [".epub"]

    def parse(self, file_path: str) -> EPUBDocument:
        """解析EPUB文件

        Args:
            file_path: 文件路径

        Returns:
            EPUBDocument: 解析结果
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported EPUB format: {extension}")

        try:
            with zipfile.ZipFile(file_path, 'r') as epub:
                # 解析container.xml找到OPF文件
                container_xml = epub.read("META-INF/container.xml")
                root = ET.fromstring(container_xml)

                # 找到rootfile的full-path
                ns = {'root': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                rootfile = root.find('.//root:rootfile', ns)
                if rootfile is None:
                    # 尝试无命名空间
                    rootfile = root.find('.//rootfile')
                if rootfile is None:
                    for elem in root.iter():
                        if elem.tag.endswith('rootfile'):
                            rootfile = elem
                            break

                opf_path = rootfile.get('full-path') or rootfile.get('media-type')

                # 解析OPF文件获取元数据
                opf_xml = epub.read(opf_path)
                opf_root = ET.fromstring(opf_xml)

                # 提取标题
                title = self._extract_title(opf_root)

                # 提取内容
                content_parts = []
                content_parts.append(f"=== Title: {title} ===")

                # 提取所有文本内容
                for elem in opf_root.iter():
                    if elem.text and elem.text.strip():
                        content_parts.append(elem.text.strip())

                # 尝试提取章节内容
                content_parts.append("\n=== Chapters ===")

                # 找到spine中的itemref
                spine = opf_root.find('.//{http://www.idpf.org/2007/opf}spine')
                if spine is None:
                    spine = opf_root.find('.//spine')

                manifest = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
                if manifest is None:
                    manifest = opf_root.find('.//manifest')

                if spine is not None and manifest is not None:
                    # 构建id到href的映射
                    id_href_map = {}
                    for item in manifest:
                        item_id = item.get('id')
                        href = item.get('href')
                        if item_id and href:
                            id_href_map[item_id] = href

                    # 按顺序提取spine中的内容
                    for itemref in spine:
                        idref = itemref.get('idref')
                        if idref in id_href_map:
                            href = id_href_map[idref]
                            try:
                                # 处理路径
                                opf_dir = os.path.dirname(opf_path)
                                if opf_dir:
                                    content_path = f"{opf_dir}/{href}"
                                else:
                                    content_path = href

                                content_path = content_path.replace('\\', '/')

                                if content_path in epub.namelist():
                                    chapter_content = epub.read(content_path).decode('utf-8', errors='ignore')
                                    # 提取文本
                                    chapter_root = ET.fromstring(chapter_content)
                                    for elem in chapter_root.iter():
                                        if elem.text and elem.text.strip():
                                            content_parts.append(elem.text.strip())
                            except Exception:
                                pass  # 忽略无法解析的章节

                content = "\n".join(content_parts)

                return EPUBDocument(
                    title=title or "Unknown Title",
                    content=content,
                    metadata={
                        "file_name": path.name,
                        "file_size": os.path.getsize(file_path)
                    }
                )

        except zipfile.BadZipFile:
            raise ValueError("Invalid EPUB file: not a valid ZIP archive")
        except ET.ParseError as e:
            raise ValueError(f"EPUB parsing error: {str(e)}")

    def _extract_title(self, opf_root) -> str:
        """从OPF提取标题"""
        # 尝试多种方式获取标题
        ns = {'opf': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}

        # 方式1: dc:title
        title_elem = opf_root.find('.//{http://purl.org/dc/elements/1.1/}title')
        if title_elem is None:
            title_elem = opf_root.find('.//dc:title', ns)
        if title_elem is None:
            for elem in opf_root.iter():
                if elem.tag.endswith('title'):
                    title_elem = elem
                    break

        if title_elem is not None and title_elem.text:
            return title_elem.text.strip()

        return "Unknown Title"

    def get_chapter_list(self, file_path: str) -> List[Dict[str, str]]:
        """获取章节列表

        Args:
            file_path: 文件路径

        Returns:
            List[Dict]: 章节列表 [{"title": "...", "path": "..."}]
        """
        chapters = []

        try:
            with zipfile.ZipFile(file_path, 'r') as epub:
                container_xml = epub.read("META-INF/container.xml")
                root = ET.fromstring(container_xml)

                for elem in root.iter():
                    if elem.tag.endswith('rootfile'):
                        opf_path = elem.get('full-path')
                        break

                opf_xml = epub.read(opf_path)
                opf_root = ET.fromstring(opf_xml)

                spine = opf_root.find('.//{http://www.idpf.org/2007/opf}spine')
                if spine is None:
                    spine = opf_root.find('.//spine')

                manifest = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
                if manifest is None:
                    manifest = opf_root.find('.//manifest')

                if spine is not None and manifest is not None:
                    id_href_map = {}
                    id_title_map = {}

                    for item in manifest:
                        item_id = item.get('id')
                        href = item.get('href')
                        if item_id and href:
                            id_href_map[item_id] = href
                            # 尝试获取标题
                            title = item.get('title')
                            if title:
                                id_title_map[item_id] = title

                    for itemref in spine:
                        idref = itemref.get('idref')
                        if idref in id_href_map:
                            chapters.append({
                                "id": idref,
                                "path": id_href_map[idref],
                                "title": id_title_map.get(idref, f"Chapter {len(chapters)+1}")
                            })

        except Exception:
            pass

        return chapters


# 延迟导入
try:
    import zipfile
    import xml.etree.ElementTree as ET
except ImportError:
    zipfile = None
    ET = None
