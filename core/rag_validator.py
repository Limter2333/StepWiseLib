"""
RAG输入验证与清洗
================

【功能】
1. 查询验证 - 类型、长度、格式检查
2. 文本清洗 - 去除噪声、规范化空白
3. 注入防护 - 检测恶意输入模式
4. 语义验证 - 检测无意义查询

【使用场景】
- RAG查询前预处理
- API输入验证
- 知识库检索优化
"""

from typing import Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import re
import unicodedata


class ValidationLevel(Enum):
    """验证级别"""
    LENIENT = "lenient"    # 宽松：只做基本检查
    NORMAL = "normal"      # 正常：完整验证
    STRICT = "strict"      # 严格：额外安全检查


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    cleaned_query: str
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    sanitized: bool = False  # 是否进行了清洗


class QueryValidator:
    """查询验证器

    基于ValidationLevel提供不同级别的验证:
    - LENIENT: 长度检查 + 基本清洗
    - NORMAL: 完整验证 + 注入检测
    - STRICT: 额外安全检查 + 强制清洗
    """

    # 查询长度限制
    MIN_QUERY_LENGTH = 1
    MAX_QUERY_LENGTH = 1000

    # 无意义查询模式
    NONSENSICAL_PATTERNS = [
        r"^[\s\d\W]+$",  # 只有数字和符号
        r"^.{0,2}$",     # 太短（少于3个字符）
    ]

    # 潜在恶意模式（用于警告，非拦截）
    SUSPICIOUS_PATTERNS = [
        r"<script",       # XSS尝试
        r"javascript:",   # JavaScript协议
        r"on\w+\s*=",     # 事件处理器
        r"\\x",           # 十六进制编码
        r"\\u[0-9a-fA-F]{4}",  # Unicode编码
    ]

    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level

    def validate(self, query: str) -> ValidationResult:
        """验证并清洗查询

        Args:
            query: 原始查询

        Returns:
            ValidationResult: 验证结果
        """
        warnings = []
        sanitized = False

        # 1. 类型检查
        if not isinstance(query, str):
            return ValidationResult(
                is_valid=False,
                cleaned_query="",
                error_message="Query must be a string"
            )

        # 2. 基本空值检查
        if not query or not query.strip():
            return ValidationResult(
                is_valid=False,
                cleaned_query="",
                error_message="Query cannot be empty"
            )

        # 3. 长度检查
        if len(query) > self.MAX_QUERY_LENGTH:
            if self.level == ValidationLevel.STRICT:
                return ValidationResult(
                    is_valid=False,
                    cleaned_query="",
                    error_message=f"Query exceeds maximum length of {self.MAX_QUERY_LENGTH} characters"
                )
            else:
                # 截断而非拒绝
                query = query[:self.MAX_QUERY_LENGTH]
                warnings.append(f"Query truncated to {self.MAX_QUERY_LENGTH} characters")

        if len(query.strip()) < self.MIN_QUERY_LENGTH:
            return ValidationResult(
                is_valid=False,
                cleaned_query="",
                error_message=f"Query must be at least {self.MIN_QUERY_LENGTH} character(s)"
            )

        # 4. 文本清洗
        cleaned = self._clean_text(query)

        # 5. 无意义查询检测
        if self._is_nonsensical(cleaned):
            if self.level == ValidationLevel.LENIENT:
                warnings.append("Query appears nonsensical but proceeding")
            else:
                return ValidationResult(
                    is_valid=False,
                    cleaned_query=cleaned,
                    error_message="Query appears to be nonsensical"
                )

        # 6. 恶意模式检测（仅警告）
        suspicious = self._detect_suspicious_patterns(cleaned)
        if suspicious:
            warnings.extend([f"Warning: {s}" for s in suspicious])

        # 7. STRICT级别额外检查
        if self.level == ValidationLevel.STRICT:
            cleaned, was_sanitized = self._strict_sanitize(cleaned)
            if was_sanitized:
                sanitized = True
                warnings.append("Query was sanitized for security")

        return ValidationResult(
            is_valid=True,
            cleaned_query=cleaned.strip(),
            warnings=warnings,
            sanitized=sanitized
        )

    def _clean_text(self, text: str) -> str:
        """清洗文本

        - Unicode规范化
        - 控制字符移除
        - 规范化空白
        """
        # Unicode NFKC规范化（将全角转为半角等）
        text = unicodedata.normalize('NFKC', text)

        # 移除控制字符（换行、制表符等保留）
        # text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

        # 规范化空白（多个空格合并）
        text = re.sub(r'\s+', ' ', text)

        return text

    def _is_nonsensical(self, query: str) -> bool:
        """检测无意义查询"""
        query_lower = query.lower().strip()

        for pattern in self.NONSENSICAL_PATTERNS:
            if re.match(pattern, query_lower):
                return True

        # 检查是否全是停用词
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'of', 'to', 'and', 'or', 'in', 'on', 'at'}
        words = set(re.findall(r'\w+', query_lower))
        meaningful_words = words - stopwords
        if len(meaningful_words) == 0:
            return True

        return False

    def _detect_suspicious_patterns(self, query: str) -> List[str]:
        """检测可疑模式"""
        found = []
        query_lower = query.lower()

        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                found.append(pattern)

        return found

    def _strict_sanitize(self, query: str) -> Tuple[str, bool]:
        """严格清洗"""
        original = query
        was_sanitized = False

        # 移除HTML标签
        if re.search(r'<[^>]+>', query):
            query = re.sub(r'<[^>]+>', '', query)
            was_sanitized = True

        # 移除SQL注入常见模式
        sql_patterns = [
            r"('\s*(or|and)\s*')",
            r"(union\s+select)",
            r"(drop\s+table)",
            r"(insert\s+into)",
            r"(delete\s+from)",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                query = re.sub(pattern, ' ', query, flags=re.IGNORECASE)
                was_sanitized = True

        return query, was_sanitized


class DocumentValidator:
    """文档验证器"""

    MIN_CONTENT_LENGTH = 10
    MAX_CONTENT_LENGTH = 10_000_000  # 10MB

    # 允许的文档类型
    ALLOWED_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.txt', '.md',
        '.xlsx', '.xls', '.pptx',
        '.csv', '.json', '.yaml', '.yml',
        '.xml', '.rtf', '.epub'
    }

    def validate_content(self, content: str, source: str = "") -> ValidationResult:
        """验证文档内容"""
        if not isinstance(content, str):
            return ValidationResult(
                is_valid=False,
                cleaned_query="",
                error_message="Content must be a string"
            )

        if len(content) < self.MIN_CONTENT_LENGTH:
            return ValidationResult(
                is_valid=False,
                cleaned_query="",
                error_message=f"Content too short (min: {self.MIN_CONTENT_LENGTH} chars)"
            )

        if len(content) > self.MAX_CONTENT_LENGTH:
            return ValidationResult(
                is_valid=False,
                cleaned_query="",
                error_message=f"Content too large (max: {self.MAX_CONTENT_LENGTH} chars)"
            )

        # 清洗内容
        cleaned = self._clean_content(content)

        return ValidationResult(
            is_valid=True,
            cleaned_query=cleaned
        )

    def validate_extension(self, file_path: str) -> bool:
        """验证文件扩展名"""
        import os
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.ALLOWED_EXTENSIONS

    def _clean_content(self, content: str) -> str:
        """清洗文档内容"""
        # Unicode规范化
        content = unicodedata.normalize('NFKC', content)

        # 移除空字节
        content = content.replace('\x00', '')

        return content


class ChunkValidator:
    """文本块验证器"""

    MIN_CHUNK_LENGTH = 10
    MAX_CHUNK_LENGTH = 5000

    def validate(self, chunk_content: str) -> Tuple[bool, str]:
        """验证文本块"""
        if not chunk_content or not chunk_content.strip():
            return False, "Chunk is empty"

        if len(chunk_content) < self.MIN_CHUNK_LENGTH:
            return False, f"Chunk too short (min: {self.MIN_CHUNK_LENGTH})"

        if len(chunk_content) > self.MAX_CHUNK_LENGTH:
            return False, f"Chunk too long (max: {self.MAX_CHUNK_LENGTH})"

        return True, ""


# ========== 全局实例 ==========

_default_validator: Optional[QueryValidator] = None
_document_validator: Optional[DocumentValidator] = None


def get_query_validator(level: ValidationLevel = ValidationLevel.NORMAL) -> QueryValidator:
    """获取查询验证器（单例）"""
    global _default_validator
    if _default_validator is None:
        _default_validator = QueryValidator(level)
    return _default_validator


def get_document_validator() -> DocumentValidator:
    """获取文档验证器（单例）"""
    global _document_validator
    if _document_validator is None:
        _document_validator = DocumentValidator()
    return _document_validator


# ========== 使用示例 ==========
"""
【使用流程】

# 1. 获取验证器
validator = get_query_validator(ValidationLevel.NORMAL)

# 2. 验证查询
result = validator.validate("What is the capital of France?")

if result.is_valid:
    print(f"Cleaned query: {result.cleaned_query}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")
else:
    print(f"Invalid: {result.error_message}")

# 3. 文档验证
doc_validator = get_document_validator()
doc_result = doc_validator.validate_content(document.content)
"""


if __name__ == "__main__":
    # 快速测试
    validator = QueryValidator(ValidationLevel.NORMAL)

    test_queries = [
        "What is the capital of France?",
        "   ",  # 空查询
        "a",  # 太短
        "中文字符测试",
        "<script>alert('xss')</script>",  # XSS尝试
        "What's the weather like today?",
        "The",  # 只有停用词
    ]

    for q in test_queries:
        result = validator.validate(q)
        print(f"Query: {repr(q)}")
        print(f"  Valid: {result.is_valid}")
        if result.is_valid:
            print(f"  Cleaned: {repr(result.cleaned_query)}")
            print(f"  Warnings: {result.warnings}")
            print(f"  Sanitized: {result.sanitized}")
        else:
            print(f"  Error: {result.error_message}")
        print()
