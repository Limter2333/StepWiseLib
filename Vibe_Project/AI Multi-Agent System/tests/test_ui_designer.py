"""
UI Designer Agent Tests
"""

import pytest
from agents.ui_designer.ui_designer import (
    UIDesigner,
    DesignStyle,
    ComponentType,
    DesignTask,
    DesignResult
)


class TestDesignStyle:
    """测试设计风格枚举"""

    def test_style_values(self):
        assert DesignStyle.MINIMAL.value == "minimal"
        assert DesignStyle.MATERIAL.value == "material"
        assert DesignStyle.GLASSMORPHISM.value == "glassmorphism"
        assert DesignStyle.NEUMORPHISM.value == "neumorphism"
        assert DesignStyle.BRUTALIST.value == "brutalist"
        assert DesignStyle.RETRO.value == "retro"
        assert DesignStyle.FUTURISTIC.value == "futuristic"

    def test_style_count(self):
        assert len(DesignStyle) == 7


class TestComponentType:
    """测试组件类型枚举"""

    def test_component_values(self):
        assert ComponentType.BUTTON.value == "button"
        assert ComponentType.INPUT.value == "input"
        assert ComponentType.CARD.value == "card"
        assert ComponentType.MODAL.value == "modal"
        assert ComponentType.NAVIGATION.value == "navigation"
        assert ComponentType.TABLE.value == "table"
        assert ComponentType.FORM.value == "form"

    def test_component_count(self):
        assert len(ComponentType) == 7


class TestDesignTask:
    """测试设计任务数据类"""

    def test_task_creation(self):
        task = DesignTask(
            id="design_1",
            component_type=ComponentType.BUTTON,
            description="Create a primary button",
            style=DesignStyle.MINIMAL
        )

        assert task.id == "design_1"
        assert task.component_type == ComponentType.BUTTON
        assert task.style == DesignStyle.MINIMAL
        assert task.created_at is not None

    def test_task_with_color_scheme(self):
        task = DesignTask(
            id="design_2",
            component_type=ComponentType.CARD,
            description="Design a card component",
            style=DesignStyle.GLASSMORPHISM,
            color_scheme={"primary": "#007bff", "secondary": "#6c757d"}
        )

        assert task.color_scheme is not None
        assert task.color_scheme["primary"] == "#007bff"


class TestDesignResult:
    """测试设计结果数据类"""

    def test_result_creation(self):
        result = DesignResult(
            component_name="PrimaryButton",
            description="A minimal primary button",
            style="minimal"
        )

        assert result.component_name == "PrimaryButton"
        assert result.style == "minimal"
        assert result.specs == {}

    def test_result_with_full_data(self):
        result = DesignResult(
            component_name="ModalDialog",
            description="A glassmorphism modal",
            style="glassmorphism",
            specs={"width": "500px", "height": "300px"},
            css=".modal { backdrop-filter: blur(10px); }",
            html="<div class='modal'>Content</div>",
            interaction="fade-in on open",
            accessibility="aria-modal, focus trap",
            quality_score=92.0
        )

        assert result.css is not None
        assert result.html is not None
        assert result.interaction is not None
        assert result.accessibility is not None
        assert result.quality_score == 92.0


class TestUIDesigner:
    """测试UI设计智能体"""

    def test_agent_creation(self):
        agent = UIDesigner()
        assert agent.name == "UI Designer"

    def test_global_instance_exists(self):
        from agents.ui_designer import ui_designer
        assert ui_designer.name == "UI Designer"

    def test_get_capabilities(self):
        agent = UIDesigner()
        caps = agent.get_capabilities()

        assert caps["name"] == "UI Designer"
        assert len(caps["design_styles"]) > 0
        assert len(caps["component_types"]) > 0
        assert "MINIMAL" in caps["design_styles"] or "minimal" in caps["design_styles"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
