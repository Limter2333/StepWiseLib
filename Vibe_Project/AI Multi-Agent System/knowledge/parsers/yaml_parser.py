"""
YAML Parser - YAML文档解析器
===========================

解析YAML文件，提取文本内容
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class YAMLDocument:
    """YAML文档"""
    path: str
    content: str  # 展平的文本内容
    raw_data: Any  # 原始YAML数据
    keys: List[str]  # 所有顶级键的列表
    is_array: bool  # 是否为数组
    item_count: int  # 顶级元素数量


class YAMLParser:
    """YAML解析器

    【功能】
    - 解析YAML文件
    - 提取键值对为文本
    - 支持嵌套结构扁平化
    - 保留列表结构
    """

    def __init__(self):
        self.supported_extensions = [".yaml", ".yml"]

    def parse(self, file_path: str) -> YAMLDocument:
        """解析YAML文件

        Args:
            file_path: 文件路径

        Returns:
            YAMLDocument对象
        """
        extension = Path(file_path).suffix.lower()
        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported YAML format: {extension}")

        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except ImportError:
            # 如果没有pyyaml，使用简单解析
            data = self._simple_parse(file_path)

        if data is None:
            data = {}

        # 展平内容
        flat_content = self._flatten_to_text(data)
        keys = list(data.keys()) if isinstance(data, dict) else []
        is_array = isinstance(data, list)
        item_count = len(data) if isinstance(data, (dict, list)) else 0

        return YAMLDocument(
            path=file_path,
            content=flat_content,
            raw_data=data,
            keys=keys,
            is_array=is_array,
            item_count=item_count
        )

    def _simple_parse(self, file_path: str) -> Dict:
        """简单YAML解析（无pyyaml时使用）

        Args:
            file_path: 文件路径

        Returns:
            解析的字典
        """
        result = {}
        current_key = None
        current_list = None

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.rstrip()
                if not line or line.startswith('#'):
                    continue

                # 检测缩进级别
                stripped = line.lstrip()
                indent = len(line) - len(stripped)

                if ':' in stripped:
                    key = stripped.split(':')[0].strip()
                    value = stripped.split(':', 1)[1].strip()

                    if value:
                        result[key] = value
                    else:
                        result[key] = {}
                        current_key = key
                elif current_key:
                    if isinstance(result.get(current_key), list):
                        result[current_key].append(line.strip())

        return result

    def _flatten_to_text(self, data: Any, prefix: str = "") -> str:
        """将YAML数据展平为可读文本

        Args:
            data: YAML数据
            prefix: 当前路径前缀

        Returns:
            展平的文本内容
        """
        parts = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    parts.append(f"{key}:")
                    parts.append(self._flatten_to_text(value, current_path))
                else:
                    parts.append(f"{key}: {value}")

        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    parts.append(f"- Item {i}:")
                    parts.append(self._flatten_to_text(item, f"{prefix}[{i}]"))
                else:
                    parts.append(f"- {item}")

        else:
            parts.append(str(data))

        return "\n".join(parts)


def get_yaml_parser() -> YAMLParser:
    """获取YAML解析器单例"""
    return YAMLParser()
