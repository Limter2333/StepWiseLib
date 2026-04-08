"""
Agent结果验证器 - ADR-005
=========================

检测Agent返回的降级结果/占位符内容
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import re


class ResultQuality(Enum):
    """结果质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    quality: ResultQuality
    issues: List[str]
    suggestions: List[str]
    score: float  # 0.0 - 1.0


class ResultValidator:
    """Agent结果验证器

    检测常见降级模式：
    - 占位符内容（TODO, PLACEHOLDER, ...）
    - 重复内容
    - 过短/过长的响应
    - 异常错误信息
    """

    # 占位符模式
    PLACEHOLDER_PATTERNS = [
        r'TODO',
        r'PLACEHOLDER',
        r'FIXME',
        r'XXX',
        r'\[.*?\]',  # [placeholder], [insert], etc.
        r'<\w+>',    # <content>, <text>, etc.
    ]

    # 降级关键词
    DEGRADED_KEYWORDS = [
        'fallback',
        'mock',
        'placeholder',
        'dummy',
        'not implemented',
        'unavailable',
    ]

    # 最小有效长度
    MIN_CODE_LENGTH = 10
    MIN_TEXT_LENGTH = 5

    def __init__(self):
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.PLACEHOLDER_PATTERNS
        ]

    def validate(self, agent_name: str, result: Any) -> ValidationResult:
        """验证Agent结果

        Args:
            agent_name: Agent名称
            result: Agent返回结果

        Returns:
            验证结果
        """
        issues = []
        suggestions = []

        if result is None:
            return ValidationResult(
                is_valid=False,
                quality=ResultQuality.FAILED,
                issues=["Result is None"],
                suggestions=["Check agent execution"],
                score=0.0
            )

        # 转换为字典（如果是Pydantic模型）
        if hasattr(result, 'model_dump'):
            result_dict = result.model_dump()
        elif hasattr(result, 'dict'):
            result_dict = result.dict()
        elif isinstance(result, dict):
            result_dict = result
        else:
            result_dict = {"value": str(result)}

        # 1. 检查占位符模式
        placeholder_issues = self._check_placeholders(result_dict)
        issues.extend(placeholder_issues)

        # 2. 检查降级关键词
        degraded_issues = self._check_degraded_keywords(result_dict)
        issues.extend(degraded_issues)

        # 3. 检查结构完整性
        structure_issues = self._check_structure(agent_name, result_dict)
        issues.extend(structure_issues)

        # 4. 计算质量分数
        score = self._calculate_score(agent_name, result_dict, issues)

        # 5. 确定质量等级
        if issues:
            quality = ResultQuality.DEGRADED
            is_valid = score >= 0.5
        else:
            quality = ResultQuality.GOOD if score >= 0.7 else ResultQuality.EXCELLENT
            is_valid = True

        return ValidationResult(
            is_valid=is_valid,
            quality=quality,
            issues=issues,
            suggestions=suggestions,
            score=score
        )

    def _check_placeholders(self, result: Dict) -> List[str]:
        """检查占位符模式"""
        issues = []
        result_str = str(result).lower()

        for pattern in self._compiled_patterns:
            if pattern.search(result_str):
                issues.append(f"Placeholder pattern detected: {pattern.pattern}")

        return issues

    def _check_degraded_keywords(self, result: Dict) -> List[str]:
        """检查降级关键词"""
        issues = []
        result_str = str(result).lower()

        for keyword in self.DEGRADED_KEYWORDS:
            if keyword in result_str:
                issues.append(f"Degraded keyword detected: {keyword}")

        return issues

    def _check_structure(self, agent_name: str, result: Dict) -> List[str]:
        """检查结果结构完整性"""
        issues = []

        # 根据Agent类型检查必要字段
        if agent_name == "dev":
            # 代码生成应该包含code字段
            if 'code' not in result and 'error' not in result:
                issues.append("Missing 'code' field in dev agent result")

        elif agent_name == "doc":
            # 文档生成应该包含content字段
            if 'content' not in result and 'error' not in result:
                issues.append("Missing 'content' field in doc agent result")

        elif agent_name == "test":
            # 测试生成应该包含tests字段
            if 'tests' not in result and 'error' not in result:
                issues.append("Missing 'tests' field in test agent result")

        elif agent_name == "rag":
            # RAG查询应该包含answer字段
            if 'answer' not in result and 'error' not in result:
                issues.append("Missing 'answer' field in rag agent result")

        return issues

    def _calculate_score(self, agent_name: str, result: Dict, issues: List[str]) -> float:
        """计算质量分数"""
        base_score = 1.0

        # 每个占位符问题扣0.2
        placeholder_count = sum(1 for i in issues if 'Placeholder' in i)
        base_score -= placeholder_count * 0.2

        # 每个降级关键词扣0.15
        degraded_count = sum(1 for i in issues if 'Degraded' in i)
        base_score -= degraded_count * 0.15

        # 结构问题扣0.3
        structure_count = sum(1 for i in issues if 'Missing' in i)
        base_score -= structure_count * 0.3

        # 检查代码/内容长度
        if 'code' in result:
            code = result['code']
            if isinstance(code, str) and len(code) < self.MIN_CODE_LENGTH:
                base_score -= 0.2

        if 'content' in result:
            content = result['content']
            if isinstance(content, str) and len(content) < self.MIN_TEXT_LENGTH:
                base_score -= 0.2

        return max(0.0, min(1.0, base_score))


# 全局实例
result_validator = ResultValidator()


def validate_agent_result(agent_name: str, result: Any) -> ValidationResult:
    """验证Agent结果的便捷函数"""
    return result_validator.validate(agent_name, result)
