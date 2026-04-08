"""
Code Reviewer Agent Tests
"""

import pytest
from agents.code_reviewer.code_reviewer import (
    CodeReviewer,
    ReviewSeverity,
    ReviewCategory,
    ReviewIssue,
    ReviewResult
)


class TestReviewSeverity:
    """测试问题严重级别枚举"""

    def test_severity_values(self):
        assert ReviewSeverity.CRITICAL.value == "critical"
        assert ReviewSeverity.HIGH.value == "high"
        assert ReviewSeverity.MEDIUM.value == "medium"
        assert ReviewSeverity.LOW.value == "low"
        assert ReviewSeverity.INFO.value == "info"

    def test_severity_count(self):
        assert len(ReviewSeverity) == 5


class TestReviewCategory:
    """测试审查类别枚举"""

    def test_category_values(self):
        assert ReviewCategory.SECURITY.value == "security"
        assert ReviewCategory.PERFORMANCE.value == "performance"
        assert ReviewCategory.STYLE.value == "style"
        assert ReviewCategory.BEST_PRACTICE.value == "best_practice"
        assert ReviewCategory.ERROR_HANDLING.value == "error_handling"
        assert ReviewCategory.TESTING.value == "testing"
        assert ReviewCategory.DOCUMENTATION.value == "documentation"

    def test_category_count(self):
        assert len(ReviewCategory) == 7


class TestReviewIssue:
    """测试审查问题数据类"""

    def test_issue_creation(self):
        issue = ReviewIssue(
            category=ReviewCategory.SECURITY,
            severity=ReviewSeverity.HIGH,
            line=42,
            message="SQL injection vulnerability",
            suggestion="Use parameterized queries"
        )

        assert issue.category == ReviewCategory.SECURITY
        assert issue.severity == ReviewSeverity.HIGH
        assert issue.line == 42
        assert issue.suggestion == "Use parameterized queries"

    def test_issue_without_line(self):
        issue = ReviewIssue(
            category=ReviewCategory.STYLE,
            severity=ReviewSeverity.LOW,
            line=None,
            message="Line too long",
            suggestion="Split line"
        )

        assert issue.line is None

    def test_issue_with_snippet(self):
        issue = ReviewIssue(
            category=ReviewCategory.PERFORMANCE,
            severity=ReviewSeverity.MEDIUM,
            line=100,
            message="Inefficient loop",
            suggestion="Use list comprehension",
            code_snippet="result = []\nfor i in range(10):\n    result.append(i*2)"
        )

        assert issue.code_snippet is not None
        assert "for i in range" in issue.code_snippet


class TestReviewResult:
    """测试审查结果数据类"""

    def test_result_creation(self):
        result = ReviewResult(
            file_path="src/app.py",
            language="python"
        )

        assert result.file_path == "src/app.py"
        assert result.language == "python"
        assert result.issues == []  # default
        assert result.quality_score == 0.0  # default

    def test_result_with_issues(self):
        issue = ReviewIssue(
            category=ReviewCategory.ERROR_HANDLING,
            severity=ReviewSeverity.MEDIUM,
            line=50,
            message="No error handling",
            suggestion="Add try-except block"
        )
        result = ReviewResult(
            file_path="src/api.py",
            language="python",
            issues=[issue],
            metrics={"lines": 200, "complexity": 15},
            summary="3 issues found",
            quality_score=75.0,
            recommendations=["Add error handling", "Reduce complexity"]
        )

        assert len(result.issues) == 1
        assert result.metrics["complexity"] == 15
        assert result.quality_score == 75.0


class TestCodeReviewer:
    """测试代码审查智能体"""

    def test_agent_creation(self):
        agent = CodeReviewer()
        assert agent.name == "Code Reviewer"

    def test_global_instance_exists(self):
        from agents.code_reviewer import code_reviewer
        assert code_reviewer.name == "Code Reviewer"

    def test_specialty(self):
        agent = CodeReviewer()
        assert "Python" in agent.specialty
        assert "JavaScript" in agent.specialty

    def test_get_capabilities(self):
        agent = CodeReviewer()
        caps = agent.get_capabilities()

        assert caps["name"] == "Code Reviewer"
        assert len(caps["specialty"]) > 0
        assert len(caps["review_categories"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
