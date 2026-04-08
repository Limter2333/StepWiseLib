"""
Code Reviewer Agent - 代码审查智能体
=====================================

职责:
- 代码质量分析
- 安全漏洞检测
- 性能问题识别
- 代码风格检查
- 最佳实践建议
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.prompt_engine import prompt_manager
from core.guardrails import guardrails
from core.llm import get_llm
from logs.error_logs import error_logger, ErrorLevel


class ReviewSeverity(Enum):
    """问题严重级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReviewCategory(Enum):
    """审查类别"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    BEST_PRACTICE = "best_practice"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


@dataclass
class ReviewIssue:
    """审查问题"""
    category: ReviewCategory
    severity: ReviewSeverity
    line: Optional[int]
    message: str
    suggestion: str
    code_snippet: Optional[str] = None


@dataclass
class ReviewResult:
    """审查结果"""
    file_path: str
    language: str
    issues: List[ReviewIssue] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)
    summary: str = ""
    quality_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


class CodeReviewer:
    """代码审查智能体

    【能力】
    - 代码质量评估
    - 安全漏洞扫描
    - 性能问题识别
    - 代码风格检查
    - 提出改进建议
    """

    def __init__(self):
        self.name = "Code Reviewer"
        self.specialty = ["代码质量", "安全", "性能", "Python", "JavaScript"]
        self.review_history: List[ReviewResult] = []

    async def review_code(
        self,
        code: str,
        language: str = "python",
        focus_areas: Optional[List[str]] = None
    ) -> ReviewResult:
        """代码审查

        Args:
            code: 待审查代码
            language: 编程语言
            focus_areas: 重点审查领域 (security/performance/style)

        Returns:
            ReviewResult: 审查结果
        """
        guard_result = guardrails.check_input(code)
        if not guard_result.passed:
            raise ValueError(f"Input blocked")

        issues = []

        try:
            # 基础检查
            issues.extend(self._check_security(code, language))
            issues.extend(self._check_performance(code, language))
            issues.extend(self._check_best_practices(code, language))
            issues.extend(self._check_error_handling(code, language))

            # 使用LLM进行深度分析
            llm_issues = await self._llm_code_review(code, language, focus_areas)
            issues.extend(llm_issues)

            quality_score = self._calculate_quality_score(issues)

        except Exception as e:
            error_logger.log(
                error_type="ReviewError",
                message=f"Code review failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            quality_score = 0.5

        summary = self._generate_summary(issues)
        recommendations = self._generate_recommendations(issues)

        result = ReviewResult(
            file_path="review",
            language=language,
            issues=issues,
            metrics=self._calculate_metrics(code, issues),
            summary=summary,
            quality_score=quality_score,
            recommendations=recommendations
        )

        self.review_history.append(result)
        return result

    async def _llm_code_review(
        self,
        code: str,
        language: str,
        focus_areas: Optional[List[str]]
    ) -> List[ReviewIssue]:
        """使用LLM进行代码审查"""
        try:
            llm = get_llm()
            system_prompt = """You are a senior code reviewer. Analyze the code for:
- Security vulnerabilities (SQL injection, XSS, etc.)
- Performance issues (N+1 queries, memory leaks, etc.)
- Code smells and style issues
- Error handling problems
- Best practice violations

Return issues in JSON format."""

            user_prompt = f"""Review this {language} code:

```{language}
{code[:2000]}  # Limit code length
```

Focus areas: {', '.join(focus_areas or ['all'])}

Return a JSON array of issues with:
- category: security|performance|style|best_practice|error_handling
- severity: critical|high|medium|low|info
- line: line number (or null)
- message: issue description
- suggestion: how to fix
"""

            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.3
            )

            # 解析LLM返回
            issues = self._parse_llm_issues(response.content, language)
            return issues

        except Exception as e:
            error_logger.log(
                error_type="LLMCallError",
                message=f"LLM code review failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            return []

    def _check_security(self, code: str, language: str) -> List[ReviewIssue]:
        """安全检查"""
        issues = []

        # 通用安全检查
        dangerous_patterns = [
            ("eval(", "Avoid using eval() - security risk", ReviewSeverity.HIGH),
            ("exec(", "Avoid using exec() - security risk", ReviewSeverity.HIGH),
            ("pickle.loads", "Pickle can execute arbitrary code - use JSON", ReviewSeverity.HIGH),
            ("os.system", "os.system can be risky - use subprocess", ReviewSeverity.MEDIUM),
            ("hardcoded_password", "Hardcoded password detected", ReviewSeverity.CRITICAL),
            ("SQL", "Potential SQL injection - use parameterized queries", ReviewSeverity.HIGH),
        ]

        for pattern, message, severity in dangerous_patterns:
            if pattern.lower() in code.lower():
                issues.append(ReviewIssue(
                    category=ReviewCategory.SECURITY,
                    severity=severity,
                    line=None,
                    message=message,
                    suggestion=f"Replace {pattern} with secure alternative",
                    code_snippet=None
                ))

        return issues

    def _check_performance(self, code: str, language: str) -> List[ReviewIssue]:
        """性能检查"""
        issues = []

        # Python特定检查
        if language == "python":
            if "for" in code and "append" in code:
                issues.append(ReviewIssue(
                    category=ReviewCategory.PERFORMANCE,
                    severity=ReviewSeverity.LOW,
                    line=None,
                    message="Consider using list comprehension for better performance",
                    suggestion="[x for x in items] instead of for loop with append"
                ))

            if "select *" in code.lower():
                issues.append(ReviewIssue(
                    category=ReviewCategory.PERFORMANCE,
                    severity=ReviewSeverity.MEDIUM,
                    line=None,
                    message="Avoid SELECT * - specify needed columns",
                    suggestion="List specific columns in SELECT query"
                ))

        return issues

    def _check_best_practices(self, code: str, language: str) -> List[ReviewIssue]:
        """最佳实践检查"""
        issues = []

        # 检查TODO/FIXME
        if "TODO" in code:
            issues.append(ReviewIssue(
                category=ReviewCategory.BEST_PRACTICE,
                severity=ReviewSeverity.INFO,
                line=None,
                message="TODO comment found",
                suggestion="Complete or create tracking issue for this task"
            ))

        # 检查是否有文档字符串
        if language == "python" and '"""' not in code and "def " in code:
            issues.append(ReviewIssue(
                category=ReviewCategory.DOCUMENTATION,
                severity=ReviewSeverity.LOW,
                line=None,
                message="Function without docstring",
                suggestion="Add docstring to document function purpose"
            ))

        return issues

    def _check_error_handling(self, code: str, language: str) -> List[ReviewIssue]:
        """错误处理检查"""
        issues = []

        # 检查是否有裸except
        if "except:" in code and "except Exception" not in code:
            issues.append(ReviewIssue(
                category=ReviewCategory.ERROR_HANDLING,
                severity=ReviewSeverity.MEDIUM,
                line=None,
                message="Bare except clause found",
                suggestion="Catch specific exceptions"
            ))

        return issues

    def _parse_llm_issues(self, llm_response: str, language: str) -> List[ReviewIssue]:
        """解析LLM返回的问题"""
        issues = []

        try:
            import json
            # 尝试解析JSON
            data = json.loads(llm_response)
            if isinstance(data, list):
                for item in data:
                    issues.append(ReviewIssue(
                        category=ReviewCategory(item.get("category", "best_practice")),
                        severity=ReviewSeverity(item.get("severity", "low")),
                        line=item.get("line"),
                        message=item.get("message", ""),
                        suggestion=item.get("suggestion", ""),
                        code_snippet=item.get("code_snippet")
                    ))
        except:
            # 如果不是JSON，尝试简单解析
            pass

        return issues

    def _calculate_quality_score(self, issues: List[ReviewIssue]) -> float:
        """计算质量分数"""
        if not issues:
            return 1.0

        weights = {
            ReviewSeverity.CRITICAL: 0.2,
            ReviewSeverity.HIGH: 0.15,
            ReviewSeverity.MEDIUM: 0.1,
            ReviewSeverity.LOW: 0.05,
            ReviewSeverity.INFO: 0.0
        }

        penalty = sum(weights.get(i.severity, 0.1) for i in issues)
        return max(0.0, 1.0 - penalty)

    def _calculate_metrics(self, code: str, issues: List[ReviewIssue]) -> Dict:
        """计算审查指标"""
        lines = code.count("\n") + 1

        return {
            "lines_of_code": lines,
            "total_issues": len(issues),
            "critical_issues": sum(1 for i in issues if i.severity == ReviewSeverity.CRITICAL),
            "high_issues": sum(1 for i in issues if i.severity == ReviewSeverity.HIGH),
            "issues_by_category": {
                cat.value: sum(1 for i in issues if i.category == cat)
                for cat in ReviewCategory
            }
        }

    def _generate_summary(self, issues: List[ReviewIssue]) -> str:
        """生成审查总结"""
        if not issues:
            return "No issues found. Code looks good!"

        critical = sum(1 for i in issues if i.severity == ReviewSeverity.CRITICAL)
        high = sum(1 for i in issues if i.severity == ReviewSeverity.HIGH)

        summary_parts = []
        if critical > 0:
            summary_parts.append(f"{critical} critical issue(s) need immediate attention")
        if high > 0:
            summary_parts.append(f"{high} high priority issue(s) should be fixed soon")

        remaining = len(issues) - critical - high
        if remaining > 0:
            summary_parts.append(f"{remaining} minor issue(s) for future improvement")

        return ". ".join(summary_parts) if summary_parts else "Some issues found."

    def _generate_recommendations(self, issues: List[ReviewIssue]) -> List[str]:
        """生成建议"""
        recs = []

        by_category = {}
        for issue in issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)

        for category, category_issues in by_category.items():
            if category == ReviewCategory.SECURITY:
                recs.append("Address all security issues before deployment")
            elif category == ReviewCategory.PERFORMANCE:
                recs.append("Optimize performance-critical code sections")
            elif category == ReviewCategory.ERROR_HANDLING:
                recs.append("Improve error handling with specific exceptions")

        return recs

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "supported_languages": ["python", "javascript", "typescript", "java", "go"],
            "review_categories": [c.value for c in ReviewCategory],
            "severity_levels": [s.value for s in ReviewSeverity]
        }


# 全局实例
code_reviewer = CodeReviewer()
