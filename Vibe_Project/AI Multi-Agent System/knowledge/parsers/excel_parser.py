"""
Excel解析器 - Excel Parser
==========================

支持解析 Excel 文件 (.xlsx, .xls)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import tempfile
import os


@dataclass
class ExcelDocument:
    """Excel文档结构"""
    sheets: List[str]  # 工作表名称列表
    content: str  # 解析后的文本内容
    metadata: Dict[str, Any]  # 元数据


class ExcelParser:
    """Excel解析器

    【功能】
    - 支持 .xlsx 和 .xls 格式
    - 解析所有工作表
    - 提取表格数据为文本
    - 支持大数据文件分块处理
    """

    def __init__(self):
        self.supported_extensions = [".xlsx", ".xls"]

    def parse(self, file_path: str) -> ExcelDocument:
        """解析Excel文件

        Args:
            file_path: 文件路径

        Returns:
            ExcelDocument: 解析结果
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported Excel format: {extension}")

        try:
            import pandas as pd

            # 读取Excel文件
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            content_parts = []

            # 解析每个工作表
            for sheet_name in sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)

                # 转换为文本
                content_parts.append(f"=== Sheet: {sheet_name} ===")
                content_parts.append(self._dataframe_to_text(df))
                content_parts.append("")

            content = "\n".join(content_parts)

            return ExcelDocument(
                sheets=sheet_names,
                content=content,
                metadata={
                    "file_name": path.name,
                    "file_size": os.path.getsize(file_path),
                    "sheet_count": len(sheet_names)
                }
            )

        except ImportError:
            raise ImportError("pandas is required for Excel parsing. Install with: pip install pandas openpyxl")

    def _dataframe_to_text(self, df) -> str:
        """将DataFrame转换为文本"""
        if df.empty:
            return "[Empty sheet]"

        # 获取列名
        headers = list(df.columns)
        header_line = " | ".join(str(h) for h in headers)

        # 获取行数据
        rows = []
        for idx, row in df.iterrows():
            row_values = []
            for val in row:
                if pd.isna(val):
                    row_values.append("")
                else:
                    row_values.append(str(val))
            rows.append(" | ".join(row_values))

        # 组合
        lines = [header_line]
        lines.extend(rows)

        return "\n".join(lines)

    def parse_chunked(self, file_path: str, chunk_size: int = 1000) -> List[ExcelDocument]:
        """分块解析大型Excel文件

        Args:
            file_path: 文件路径
            chunk_size: 每个块的行数

        Returns:
            List[ExcelDocument]: 分块结果
        """
        import pandas as pd

        path = Path(file_path)
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names

        results = []

        for sheet_name in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            # 分块
            total_rows = len(df)
            for start in range(0, total_rows, chunk_size):
                end = min(start + chunk_size, total_rows)
                chunk_df = df.iloc[start:end]

                content = self._dataframe_to_text(chunk_df)

                results.append(ExcelDocument(
                    sheets=[sheet_name],
                    content=content,
                    metadata={
                        "file_name": path.name,
                        "sheet_name": sheet_name,
                        "chunk_start": start,
                        "chunk_end": end,
                        "total_rows": total_rows
                    }
                ))

        return results


# 延迟导入pandas
try:
    import pandas as pd
except ImportError:
    pd = None
