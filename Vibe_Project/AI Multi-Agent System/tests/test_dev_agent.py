"""
Dev Agent Tests
"""

import pytest
from datetime import datetime
from agents.dev_agent.dev_agent import (
    DevAgent,
    DevTask,
    CodeResult,
    TaskType
)


class TestDevAgentCreation:
    """测试DevAgent创建"""

    def test_agent_creation(self):
        agent = DevAgent()
        assert agent.name == "Dev Agent"
        assert "Python" in agent.specialty
        assert "FastAPI" in agent.specialty

    def test_agent_specialty(self):
        agent = DevAgent()
        assert "LangChain" in agent.specialty
        assert "系统设计" in agent.specialty


class TestTaskType:
    """测试任务类型枚举"""

    def test_task_type_values(self):
        assert TaskType.CODE_GENERATION.value == "code_generation"
        assert TaskType.CODE_REVIEW.value == "code_review"
        assert TaskType.BUG_FIX.value == "bug_fix"
        assert TaskType.REFACTOR.value == "refactor"
        assert TaskType.UNIT_TEST.value == "unit_test"
        assert TaskType.ARCHITECTURE.value == "architecture"

    def test_task_type_count(self):
        assert len(TaskType) == 6


class TestDevTask:
    """测试开发任务"""

    def test_dev_task_creation(self):
        task = DevTask(
            id="test_1",
            task_type=TaskType.CODE_GENERATION,
            description="Create a login function"
        )

        assert task.id == "test_1"
        assert task.task_type == TaskType.CODE_GENERATION
        assert task.description == "Create a login function"
        assert task.language == "python"
        assert isinstance(task.created_at, datetime)

    def test_dev_task_with_language(self):
        task = DevTask(
            id="test_2",
            task_type=TaskType.CODE_REVIEW,
            description="Review authentication",
            language="javascript"
        )

        assert task.language == "javascript"

    def test_dev_task_with_framework(self):
        task = DevTask(
            id="test_3",
            task_type=TaskType.CODE_GENERATION,
            description="Create API",
            framework="fastapi"
        )

        assert task.framework == "fastapi"

    def test_dev_task_with_requirements(self):
        task = DevTask(
            id="test_4",
            task_type=TaskType.CODE_GENERATION,
            description="Create user service",
            requirements=["auth", "validation"]
        )

        assert len(task.requirements) == 2
        assert "auth" in task.requirements


class TestCodeResult:
    """测试代码结果"""

    def test_code_result_creation(self):
        result = CodeResult(
            code="print('hello')",
            language="python"
        )

        assert result.code == "print('hello')"
        assert result.language == "python"
        assert result.quality_score == 0.0

    def test_code_result_with_file_path(self):
        result = CodeResult(
            code="class MyClass: pass",
            language="python",
            file_path="my_class.py"
        )

        assert result.file_path == "my_class.py"

    def test_code_result_with_imports(self):
        result = CodeResult(
            code="import os",
            language="python",
            imports=["os", "sys"]
        )

        assert len(result.imports) == 2

    def test_code_result_with_tests(self):
        result = CodeResult(
            code="def add(a, b): return a + b",
            language="python",
            tests="def test_add(): assert add(1, 2) == 3"
        )

        assert result.tests is not None

    def test_code_result_with_documentation(self):
        result = CodeResult(
            code="def add(a, b): return a + b",
            language="python",
            documentation="# Add function\nAdds two numbers"
        )

        assert result.documentation is not None

    def test_code_result_quality_score(self):
        result = CodeResult(
            code="x = 1",
            language="python",
            quality_score=0.85
        )

        assert result.quality_score == 0.85


class TestDevAgentTaskCreation:
    """测试DevAgent任务创建"""

    def test_create_task(self):
        agent = DevAgent()

        task = agent.create_task(
            description="Create user authentication",
            task_type=TaskType.CODE_GENERATION,
            language="python"
        )

        assert task is not None
        assert "dev_" in task.id
        assert task.task_type == TaskType.CODE_GENERATION
        assert agent.current_task == task

    def test_create_task_with_framework(self):
        agent = DevAgent()

        task = agent.create_task(
            description="Create REST API",
            task_type=TaskType.CODE_GENERATION,
            language="python",
            framework="fastapi"
        )

        assert task.framework == "fastapi"

    def test_create_task_with_requirements(self):
        agent = DevAgent()

        task = agent.create_task(
            description="Create data processing",
            task_type=TaskType.CODE_GENERATION,
            requirements=["async", "validation"]
        )

        assert len(task.requirements) == 2


class TestCodeReview:
    """测试代码审查"""

    @pytest.mark.asyncio
    async def test_review_code_basic(self):
        agent = DevAgent()

        result = await agent.review_code(
            code="def hello(): print('Hello, World!')",
            language="python"
        )

        assert "issues" in result
        assert "suggestions" in result
        assert "quality_score" in result
        assert result["language"] == "python"

    @pytest.mark.asyncio
    async def test_review_code_too_short(self):
        agent = DevAgent()

        result = await agent.review_code(
            code="x = 1",
            language="python"
        )

        assert "Code is too short" in result["issues"]

    @pytest.mark.asyncio
    async def test_review_code_with_todo(self):
        agent = DevAgent()

        result = await agent.review_code(
            code="def hello():\n    # TODO: implement",
            language="python"
        )

        assert any("TODO" in s for s in result["suggestions"])

    @pytest.mark.asyncio
    async def test_review_code_security_eval(self):
        agent = DevAgent()

        result = await agent.review_code(
            code="result = eval(user_input)",
            language="python"
        )

        assert any("eval()" in issue for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_review_code_security_exec(self):
        agent = DevAgent()

        result = await agent.review_code(
            code="exec('print(1)')",
            language="python"
        )

        assert any("exec()" in issue for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_review_code_security_password(self):
        agent = DevAgent()

        result = await agent.review_code(
            code="password = 'hardcoded123'",
            language="python"
        )

        assert any("password" in s.lower() for s in result["suggestions"])

    @pytest.mark.asyncio
    async def test_review_code_long(self):
        agent = DevAgent()

        # Create code longer than 500 lines
        long_code = "\n".join([f"line_{i} = {i}" for i in range(600)])

        result = await agent.review_code(
            code=long_code,
            language="python"
        )

        assert any("splitting" in s.lower() for s in result["suggestions"])


class TestCapabilities:
    """测试能力获取"""

    def test_get_capabilities(self):
        agent = DevAgent()

        caps = agent.get_capabilities()

        assert caps["name"] == "Dev Agent"
        assert "Python" in caps["specialty"]
        assert "python" in caps["supported_languages"]
        assert "javascript" in caps["supported_languages"]
        assert "fastapi" in caps["supported_frameworks"]
        assert "code_generation" in caps["task_types"]

    def test_supported_languages(self):
        agent = DevAgent()
        caps = agent.get_capabilities()

        assert "typescript" in caps["supported_languages"]
        assert "java" in caps["supported_languages"]

    def test_supported_frameworks(self):
        agent = DevAgent()
        caps = agent.get_capabilities()

        assert "langchain" in caps["supported_frameworks"]
        assert "react" in caps["supported_frameworks"]
        assert "django" in caps["supported_frameworks"]


class TestHelperMethods:
    """测试辅助方法"""

    def test_to_camel_case_simple(self):
        agent = DevAgent()

        result = agent._to_camel_case("hello world")

        assert result == "HelloWorld"

    def test_to_camel_case_with_underscore(self):
        agent = DevAgent()

        result = agent._to_camel_case("hello_world_test")

        assert result == "HelloWorldTest"

    def test_to_camel_case_single(self):
        agent = DevAgent()

        result = agent._to_camel_case("hello")

        assert result == "Hello"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
