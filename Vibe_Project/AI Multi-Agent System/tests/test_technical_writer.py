"""
Technical Writer Agent Tests
"""

import pytest
from agents.technical_writer.technical_writer import (
    TechnicalWriter,
    DocType,
    DocTask,
    DocResult
)


class TestDocType:
    """测试文档类型枚举"""

    def test_doc_type_values(self):
        assert DocType.README.value == "readme"
        assert DocType.API_DOC.value == "api_doc"
        assert DocType.USER_GUIDE.value == "user_guide"
        assert DocType.TECHNICAL_DESIGN.value == "technical_design"
        assert DocType.CHANGELOG.value == "changelog"
        assert DocType.ARCHITECTURE.value == "architecture"
        assert DocType.TUTORIAL.value == "tutorial"
        assert DocType.FAQ.value == "faq"

    def test_doc_type_count(self):
        assert len(DocType) == 8


class TestDocTask:
    """测试文档任务数据类"""

    def test_task_creation(self):
        task = DocTask(
            id="doc_1",
            doc_type=DocType.README,
            title="Project README",
            description="Main project documentation"
        )

        assert task.id == "doc_1"
        assert task.doc_type == DocType.README
        assert task.title == "Project README"
        assert task.audience == "developers"  # default
        assert task.language == "en"  # default
        assert task.created_at is not None

    def test_task_with_custom_settings(self):
        task = DocTask(
            id="doc_2",
            doc_type=DocType.API_DOC,
            title="API Reference",
            description="Complete API documentation",
            audience="users",
            language="zh"
        )

        assert task.audience == "users"
        assert task.language == "zh"


class TestDocResult:
    """测试文档结果数据类"""

    def test_result_creation(self):
        result = DocResult(
            content="# Project\n\nThis is a project.",
            doc_type="readme",
            title="Project README"
        )

        assert result.content is not None
        assert result.doc_type == "readme"
        assert result.format == "markdown"  # default

    def test_result_with_sections(self):
        result = DocResult(
            content="Full content",
            doc_type="api_doc",
            title="API Docs",
            format="markdown",
            sections=["Authentication", "Endpoints", "Error Codes"],
            quality_score=88.5
        )

        assert len(result.sections) == 3
        assert result.quality_score == 88.5


class TestTechnicalWriter:
    """测试技术文档智能体"""

    def test_agent_creation(self):
        agent = TechnicalWriter()
        assert agent.name == "Technical Writer"

    def test_global_instance_exists(self):
        from agents.technical_writer import technical_writer
        assert technical_writer.name == "Technical Writer"

    def test_specialty(self):
        agent = TechnicalWriter()
        assert "Markdown" in agent.specialty
        assert "OpenAPI" in agent.specialty

    def test_get_capabilities(self):
        agent = TechnicalWriter()
        caps = agent.get_capabilities()

        assert caps["name"] == "Technical Writer"
        assert len(caps["doc_types"]) > 0
        assert len(caps["specialty"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
