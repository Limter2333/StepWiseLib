"""
Result Validator 测试
====================

测试Agent结果验证器功能
"""

import pytest
from agents.orchestrator.result_validator import (
    ResultValidator,
    result_validator,
    validate_agent_result,
    ResultQuality
)


class TestResultValidator:
    """ResultValidator测试"""

    def test_validator_initialization(self):
        """测试验证器初始化"""
        validator = ResultValidator()
        assert len(validator.PLACEHOLDER_PATTERNS) > 0
        assert len(validator.DEGRADED_KEYWORDS) > 0
        assert validator.MIN_CODE_LENGTH == 10
        assert validator.MIN_TEXT_LENGTH == 5

    def test_validate_none_result(self):
        """测试验证None结果"""
        validator = ResultValidator()
        result = validator.validate("dev", None)

        assert result.is_valid is False
        assert result.quality == ResultQuality.FAILED
        assert result.score == 0.0
        assert "Result is None" in result.issues

    def test_validate_empty_dict(self):
        """测试验证空字典"""
        validator = ResultValidator()
        result = validator.validate("dev", {})

        # 空字典会触发结构问题，但由于score>=0.5，is_valid仍为True
        assert result.quality == ResultQuality.DEGRADED
        assert len(result.issues) > 0

    def test_validate_dev_agent_with_code(self):
        """测试验证dev agent结果（有code字段）"""
        validator = ResultValidator()
        result = validator.validate("dev", {"code": "print('hello')"})

        assert result.is_valid is True
        assert result.score >= 0.5

    def test_validate_dev_agent_without_code(self):
        """测试验证dev agent结果（无code字段）"""
        validator = ResultValidator()
        result = validator.validate("dev", {"other": "value"})

        # 缺少code字段会触发问题，但score>=0.5时is_valid仍为True
        assert any("Missing 'code' field" in issue for issue in result.issues)

    def test_validate_doc_agent_with_content(self):
        """测试验证doc agent结果（有content字段）"""
        validator = ResultValidator()
        result = validator.validate("doc", {"content": "This is documentation"})

        assert result.is_valid is True

    def test_validate_doc_agent_without_content(self):
        """测试验证doc agent结果（无content字段）"""
        validator = ResultValidator()
        result = validator.validate("doc", {"title": "Title only"})

        # 缺少content字段会触发问题
        assert any("Missing 'content' field" in issue for issue in result.issues)

    def test_validate_test_agent_with_tests(self):
        """测试验证test agent结果（有tests字段）"""
        validator = ResultValidator()
        result = validator.validate("test", {"tests": ["test1", "test2"]})

        assert result.is_valid is True

    def test_validate_test_agent_without_tests(self):
        """测试验证test agent结果（无tests字段）"""
        validator = ResultValidator()
        result = validator.validate("test", {"something": "else"})

        # 缺少tests字段会触发问题
        assert any("Missing 'tests' field" in issue for issue in result.issues)

    def test_validate_rag_agent_with_answer(self):
        """测试验证rag agent结果（有answer字段）"""
        validator = ResultValidator()
        result = validator.validate("rag", {"answer": "This is an answer"})

        assert result.is_valid is True

    def test_validate_rag_agent_without_answer(self):
        """测试验证rag agent结果（无answer字段）"""
        validator = ResultValidator()
        result = validator.validate("rag", {"sources": []})

        # 缺少answer字段会触发问题
        assert any("Missing 'answer' field" in issue for issue in result.issues)

    def test_validate_with_error_field(self):
        """测试验证包含error字段的结果"""
        validator = ResultValidator()
        # 仅有error字段时，结构检查会失败但不扣分
        result = validator.validate("dev", {"error": "Some error occurred"})

        # error字段不触发占位符检测，所以issues为空，quality为GOOD
        assert result.quality == ResultQuality.GOOD


class TestPlaceholderDetection:
    """占位符检测测试"""

    def test_detect_todo_placeholder(self):
        """测试检测TODO占位符"""
        validator = ResultValidator()
        result = validator.validate("dev", {"code": "# TODO: implement this"})

        assert result.quality in [ResultQuality.DEGRADED, ResultQuality.FAILED]
        assert any("Placeholder" in issue for issue in result.issues)

    def test_detect_placeholder_text(self):
        """测试检测placeholder文本"""
        validator = ResultValidator()
        result = validator.validate("doc", {"content": "This is a [placeholder] for content"})

        assert any("Placeholder" in issue or "Degraded" in issue for issue in result.issues)

    def test_detect_fixme_placeholder(self):
        """测试检测FIXME占位符"""
        validator = ResultValidator()
        result = validator.validate("dev", {"code": "# FIXME: fix this later"})

        assert any("Placeholder" in issue for issue in result.issues)

    def test_detect_angle_bracket_placeholder(self):
        """测试检测尖括号占位符"""
        validator = ResultValidator()
        result = validator.validate("doc", {"content": "User: <content>"})

        # 尖括号模式 <\w+> 应该被检测到
        assert any("Placeholder" in issue for issue in result.issues)


class TestDegradedKeywordDetection:
    """降级关键词检测测试"""

    def test_detect_fallback_keyword(self):
        """测试检测fallback关键词"""
        validator = ResultValidator()
        result = validator.validate("rag", {"answer": "This is a fallback response"})

        assert any("Degraded" in issue for issue in result.issues)

    def test_detect_mock_keyword(self):
        """测试检测mock关键词"""
        validator = ResultValidator()
        result = validator.validate("dev", {"code": "// mock implementation"})

        assert any("Degraded" in issue for issue in result.issues)

    def test_detect_placeholder_keyword(self):
        """测试检测placeholder关键词"""
        validator = ResultValidator()
        result = validator.validate("doc", {"content": "This is placeholder content"})

        assert any("Degraded" in issue for issue in result.issues)

    def test_detect_not_implemented_keyword(self):
        """测试检测not implemented关键词"""
        validator = ResultValidator()
        result = validator.validate("test", {"tests": "Not implemented yet"})

        assert any("Degraded" in issue for issue in result.issues)


class TestScoreCalculation:
    """分数计算测试"""

    def test_perfect_result_score(self):
        """测试完美结果得分"""
        validator = ResultValidator()
        result = validator.validate("dev", {
            "code": "def hello():\n    print('Hello, World!')"
        })

        assert result.score >= 0.7
        assert result.quality in [ResultQuality.EXCELLENT, ResultQuality.GOOD, ResultQuality.DEGRADED]

    def test_short_code_penalty(self):
        """测试短代码扣分"""
        validator = ResultValidator()
        result = validator.validate("dev", {"code": "x = 1"})

        # 过短的代码应该扣分
        assert result.score < 1.0

    def test_short_content_penalty(self):
        """测试短内容扣分"""
        validator = ResultValidator()
        result = validator.validate("doc", {"content": "Hi"})

        # 过短的内容应该扣分
        assert result.score < 1.0

    def test_multiple_issues_accumulate(self):
        """测试多个问题累积扣分"""
        validator = ResultValidator()
        # 同时有placeholder和过短的内容
        result = validator.validate("doc", {"content": "[TODO]"})

        # 应该检测到多个问题
        assert len(result.issues) >= 2


class TestResultQualityEnum:
    """结果质量枚举测试"""

    def test_quality_values(self):
        """测试质量枚举值"""
        assert ResultQuality.EXCELLENT.value == "excellent"
        assert ResultQuality.GOOD.value == "good"
        assert ResultQuality.DEGRADED.value == "degraded"
        assert ResultQuality.FAILED.value == "failed"


class TestConvenienceFunction:
    """便捷函数测试"""

    def test_validate_agent_result_function(self):
        """测试validate_agent_result便捷函数"""
        result = validate_agent_result("dev", {"code": "print('test')"})

        assert result.is_valid is True
        assert result.score > 0

    def test_validate_agent_result_with_invalid_input(self):
        """测试validate_agent_result处理无效输入"""
        result = validate_agent_result("dev", None)

        assert result.is_valid is False
        assert result.quality == ResultQuality.FAILED


class TestEdgeCases:
    """边界情况测试"""

    def test_validate_pydantic_model(self):
        """测试验证Pydantic模型"""
        from pydantic import BaseModel

        class MockResult(BaseModel):
            code: str
            language: str = "python"

        validator = ResultValidator()
        mock = MockResult(code="x = 1")
        result = validator.validate("dev", mock)

        assert result.is_valid is True

    def test_validate_string_input(self):
        """测试验证字符串输入"""
        validator = ResultValidator()
        result = validator.validate("doc", "Just a string")

        # 字符串应该被转换并验证
        assert isinstance(result.issues, list)

    def test_validate_with_whitespace_only_code(self):
        """测试验证仅空白字符的代码"""
        validator = ResultValidator()
        result = validator.validate("dev", {"code": "   \n\t  "})

        # 空白代码应该被检测
        assert result.score < 1.0

    def test_validate_with_very_long_content(self):
        """测试验证非常长的内容"""
        validator = ResultValidator()
        long_content = "x = 1\n" * 1000
        result = validator.validate("dev", {"code": long_content})

        # 长内容不应该被扣分
        assert result.score >= 0.5

    def test_case_insensitive_detection(self):
        """测试大小写不敏感检测"""
        validator = ResultValidator()

        # 大写
        result1 = validator.validate("dev", {"code": "# TODO: fix"})
        # 小写
        result2 = validator.validate("dev", {"code": "# todo: fix"})

        # 两者都应该检测到TODO
        assert any("Placeholder" in issue for issue in result1.issues)
        assert any("Placeholder" in issue for issue in result2.issues)

    def test_all_agent_types_validated(self):
        """测试所有Agent类型都能被验证"""
        validator = ResultValidator()

        agents_and_results = [
            ("dev", {"code": "x = 1"}),
            ("doc", {"content": "Documentation"}),
            ("test", {"tests": ["test1"]}),
            ("rag", {"answer": "Answer content"}),
        ]

        for agent_name, result_data in agents_and_results:
            result = validator.validate(agent_name, result_data)
            assert isinstance(result.is_valid, bool)
            assert isinstance(result.score, float)
            assert 0.0 <= result.score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
