"""
Product Manager Agent Tests
"""

import pytest
from agents.product_manager.product_manager import (
    ProductManager,
    Priority,
    EpicStatus,
    UserStory,
    Epic,
    ProductResult
)


class TestPriority:
    """测试优先级枚举"""

    def test_priority_values(self):
        assert Priority.P0_CRITICAL.value == "P0"
        assert Priority.P1_HIGH.value == "P1"
        assert Priority.P2_MEDIUM.value == "P2"
        assert Priority.P3_LOW.value == "P3"

    def test_priority_count(self):
        assert len(Priority) == 4


class TestEpicStatus:
    """测试Epic状态枚举"""

    def test_status_values(self):
        assert EpicStatus.ACTIVE.value == "active"
        assert EpicStatus.COMPLETED.value == "completed"
        assert EpicStatus.ARCHIVED.value == "archived"

    def test_status_count(self):
        assert len(EpicStatus) == 3


class TestUserStory:
    """测试用户故事数据类"""

    def test_user_story_creation(self):
        story = UserStory(
            id="us_1",
            as_a="developer",
            i_want="write clean code",
            so_that="maintainability is high",
            priority=Priority.P1_HIGH
        )

        assert story.id == "us_1"
        assert story.as_a == "developer"
        assert story.i_want == "write clean code"
        assert story.so_that == "maintainability is high"
        assert story.priority == Priority.P1_HIGH
        assert story.story_points == 0  # default
        assert story.acceptance_criteria == []  # default

    def test_user_story_with_full_data(self):
        story = UserStory(
            id="us_2",
            as_a="user",
            i_want="login functionality",
            so_that="access my account",
            priority=Priority.P0_CRITICAL,
            acceptance_criteria=["valid email", "valid password", "error handling"],
            story_points=5,
            labels=["auth", "security"]
        )

        assert len(story.acceptance_criteria) == 3
        assert story.story_points == 5
        assert len(story.labels) == 2


class TestEpic:
    """测试Epic数据类"""

    def test_epic_creation(self):
        epic = Epic(
            id="epic_1",
            title="User Authentication",
            description="Complete auth system"
        )

        assert epic.id == "epic_1"
        assert epic.title == "User Authentication"
        assert epic.status == EpicStatus.ACTIVE  # default

    def test_epic_with_stories(self):
        story = UserStory(
            id="us_1",
            as_a="user",
            i_want="login",
            so_that="access",
            priority=Priority.P0_CRITICAL
        )
        epic = Epic(
            id="epic_1",
            title="Auth",
            description="Auth system",
            user_stories=[story],
            status=EpicStatus.ACTIVE
        )

        assert len(epic.user_stories) == 1
        assert epic.user_stories[0].id == "us_1"


class TestProductResult:
    """测试产品规划结果数据类"""

    def test_result_creation(self):
        result = ProductResult(
            roadmap={"Q1": ["feature1"]},
            requirements="Build auth system"
        )

        assert result.roadmap is not None
        assert result.user_stories == []
        assert result.epics == []
        assert result.quality_score == 0.0

    def test_result_with_full_data(self):
        story = UserStory(
            id="us_1",
            as_a="user",
            i_want="login",
            so_that="access",
            priority=Priority.P0_CRITICAL
        )
        epic = Epic(
            id="epic_1",
            title="Auth",
            description="Auth",
            user_stories=[story]
        )
        result = ProductResult(
            roadmap={"Q1": ["auth"]},
            user_stories=[story],
            epics=[epic],
            milestones=[{"name": "v1.0", "date": "2026-04-01"}],
            requirements="Auth system",
            quality_score=92.0
        )

        assert len(result.user_stories) == 1
        assert len(result.epics) == 1
        assert len(result.milestones) == 1


class TestProductManager:
    """测试产品经理智能体"""

    def test_agent_creation(self):
        agent = ProductManager()
        assert agent.name == "Product Manager"

    def test_global_instance_exists(self):
        from agents.product_manager import product_manager
        assert product_manager.name == "Product Manager"

    def test_get_capabilities(self):
        agent = ProductManager()
        caps = agent.get_capabilities()

        assert caps["name"] == "Product Manager"
        assert "user_stories" in caps["deliverables"] or "user_story" in caps["deliverables"]
        assert "roadmap" in caps["deliverables"]
        assert len(caps["priorities"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
