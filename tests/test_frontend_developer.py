"""
Frontend Developer Agent Tests
"""

import pytest
from agents.frontend_developer.frontend_developer import (
    FrontendDeveloper,
    FrontendFramework,
    TaskType,
    FrontendTask,
    FrontendResult
)


class TestFrontendFramework:
    """测试前端框架枚举"""

    def test_framework_values(self):
        assert FrontendFramework.REACT.value == "react"
        assert FrontendFramework.VUE.value == "vue"
        assert FrontendFramework.ANGULAR.value == "angular"
        assert FrontendFramework.HTML_CSS.value == "html_css"
        assert FrontendFramework.NEXTJS.value == "nextjs"
        assert FrontendFramework.FLUTTER.value == "flutter"

    def test_framework_count(self):
        assert len(FrontendFramework) == 6


class TestTaskType:
    """测试前端任务类型枚举"""

    def test_task_type_values(self):
        assert TaskType.COMPONENT.value == "component"
        assert TaskType.PAGE.value == "page"
        assert TaskType.RESPONSIVE.value == "responsive"
        assert TaskType.ANIMATION.value == "animation"
        assert TaskType.STATE_MANAGEMENT.value == "state_management"

    def test_task_type_count(self):
        assert len(TaskType) == 5


class TestFrontendTask:
    """测试前端任务数据类"""

    def test_task_creation(self):
        task = FrontendTask(
            id="fe_1",
            task_type=TaskType.COMPONENT,
            description="Create a button component",
            framework=FrontendFramework.REACT
        )

        assert task.id == "fe_1"
        assert task.task_type == TaskType.COMPONENT
        assert task.framework == FrontendFramework.REACT
        assert task.created_at is not None

    def test_task_with_requirements(self):
        task = FrontendTask(
            id="fe_2",
            task_type=TaskType.PAGE,
            description="Landing page",
            framework=FrontendFramework.VUE,
            requirements=["responsive", "SEO friendly", "fast load"]
        )

        assert len(task.requirements) == 3
        assert "responsive" in task.requirements

    def test_task_default_requirements(self):
        task = FrontendTask(
            id="fe_3",
            task_type=TaskType.ANIMATION,
            description="Fade in animation",
            framework=FrontendFramework.HTML_CSS
        )

        assert task.requirements == []


class TestFrontendResult:
    """测试前端结果数据类"""

    def test_result_creation(self):
        result = FrontendResult(
            code="<button>Click</button>",
            framework="react",
            component_name="Button"
        )

        assert result.code is not None
        assert result.framework == "react"
        assert result.component_name == "Button"
        assert result.css is None  # default

    def test_result_with_full_data(self):
        result = FrontendResult(
            code="const Button = () => <button>Click</button>",
            framework="react",
            component_name="Button",
            css=".button { background: blue; }",
            tests="describe('Button', () => {...})",
            documentation="# Button Component",
            quality_score=88.0
        )

        assert result.css is not None
        assert result.tests is not None
        assert result.documentation is not None
        assert result.quality_score == 88.0


class TestFrontendDeveloper:
    """测试前端开发智能体"""

    def test_agent_creation(self):
        agent = FrontendDeveloper()
        assert agent.name == "Frontend Developer"

    def test_global_instance_exists(self):
        from agents.frontend_developer import frontend_developer
        assert frontend_developer.name == "Frontend Developer"

    def test_get_capabilities(self):
        agent = FrontendDeveloper()
        caps = agent.get_capabilities()

        assert caps["name"] == "Frontend Developer"
        assert len(caps["supported_frameworks"]) > 0
        assert len(caps["task_types"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
