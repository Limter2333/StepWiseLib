"""
JSON Parser - JSON文档解析器
===========================

解析JSON文件，提取文本内容
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class JSONDocument:
    """JSON文档"""
    path: str
    content: str  # 展平的文本内容
    raw_data: Dict[Any, Any]  # 原始JSON数据
    keys: List[str]  # 所有键的列表
    is_array: bool  # 是否为数组
    item_count: int  # 顶级元素数量


class JSONParser:
    """JSON解析器

    【功能】
    - 解析JSON文件
    - 提取键值对为文本
    - 支持嵌套结构扁平化
    - 保留数组结构
    """

    def __init__(self):
        self.supported_extensions = [".json"]

    def parse(self, file_path: str) -> JSONDocument:
        """解析JSON文件

        Args:
            file_path: 文件路径

        Returns:
            JSONDocument对象
        """
        extension = Path(file_path).suffix.lower()
        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported JSON format: {extension}")

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            data = json.load(f)

        # 展平内容
        flat_content = self._flatten_to_text(data, file_path)
        keys = self._extract_keys(data)
        is_array = isinstance(data, list)
        item_count = len(data) if is_array else len(data.keys())

        return JSONDocument(
            path=file_path,
            content=flat_content,
            raw_data=data,
            keys=keys,
            is_array=is_array,
            item_count=item_count
        )

    def _flatten_to_text(self, data: Any, path: str = "") -> str:
        """将JSON数据展平为可读文本

        Args:
            data: JSON数据
            path: 当前路径（用于嵌套显示）

        Returns:
            展平的文本内容
        """
        parts = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, (dict, list)):
                    parts.append(f"{key}:")
                    parts.append(self._flatten_to_text(value, current_path))
                else:
                    parts.append(f"{key}: {value}")

        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    parts.append(f"[{i}]:")
                    parts.append(self._flatten_to_text(item, f"{path}[{i}]"))
                else:
                    parts.append(f"[{i}]: {item}")

        else:
            parts.append(str(data))

        return "\n".join(parts)

    def _extract_keys(self, data: Any, prefix: str = "") -> List[str]:
        """提取所有键名

        Args:
            data: JSON数据
            prefix: 键名前缀

        Returns:
            键名列表
        """
        keys = []

        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                keys.append(full_key)
                if isinstance(value, (dict, list)):
                    keys.extend(self._extract_keys(value, full_key))

        elif isinstance(data, list):
            for i, item in enumerate(data):
                keys.extend(self._extract_keys(item, f"{prefix}[{i}]"))

        return keys


def get_json_parser() -> JSONParser:
    """获取JSON解析器单例"""
    return JSONParser()
