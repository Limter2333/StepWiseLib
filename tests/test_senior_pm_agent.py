"""
Senior PM Agent Tests
"""

import pytest
from datetime import datetime, timedelta
from agents.senior_pm_agent.senior_pm_agent import (
    SeniorPMAgent,
    StrategyType,
    Sprint,
    Stakeholder,
    DecisionRecord,
    DecisionStatus,
    RiskLevel,
    get_senior_pm
)


class TestSeniorPMAgentCreation:
    """测试SeniorPM Agent创建"""

    def test_agent_creation(self):
        agent = SeniorPMAgent(project_name="Test Project")
        assert agent.name == "Senior PM Agent"
        assert agent.project_name == "Test Project"

    def test_get_senior_pm_singleton(self):
        agent1 = get_senior_pm()
        agent2 = get_senior_pm()
        assert agent1 is agent2


class TestStrategyManagement:
    """测试战略管理"""

    def test_create_strategy(self):
        agent = SeniorPMAgent()
        strategy = agent.create_strategy(
            name="Growth Strategy",
            strategy_type=StrategyType.GROWTH,
            vision="Become market leader",
            timeline="2024-2026"
        )

        assert strategy.id == "strategy_1"
        assert strategy.name == "Growth Strategy"
        assert strategy.type == StrategyType.GROWTH
        assert strategy.vision == "Become market leader"

    def test_get_strategy(self):
        agent = SeniorPMAgent()
        strategy = agent.create_strategy(
            name="Test Strategy",
            strategy_type=StrategyType.INNOVATION,
            vision="Test vision"
        )

        retrieved = agent.get_strategy(strategy.id)
        assert retrieved is not None
        assert retrieved.id == strategy.id


class TestSprintManagement:
    """测试Sprint管理"""

    def test_create_sprint(self):
        agent = SeniorPMAgent()
        start = datetime.now()
        end = start + timedelta(days=14)

        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete core features",
            start_date=start,
            end_date=end,
            capacity=20
        )

        assert sprint.id == "sprint_1"
        assert sprint.name == "Sprint 1"
        assert sprint.status == "planning"
        assert sprint.capacity == 20

    def test_start_sprint(self):
        agent = SeniorPMAgent()
        start = datetime.now()
        end = start + timedelta(days=14)

        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete core features",
            start_date=start,
            end_date=end
        )

        result = agent.start_sprint(sprint.id)
        assert result is True
        assert sprint.status == "active"

    def test_complete_sprint(self):
        agent = SeniorPMAgent()
        start = datetime.now()
        end = start + timedelta(days=14)

        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete core features",
            start_date=start,
            end_date=end
        )

        agent.start_sprint(sprint.id)
        result = agent.complete_sprint(sprint.id)

        assert result is True
        assert sprint.status == "completed"

    def test_add_task_to_sprint(self):
        agent = SeniorPMAgent()
        start = datetime.now()
        end = start + timedelta(days=14)

        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete core features",
            start_date=start,
            end_date=end
        )

        result = agent.add_task_to_sprint(sprint.id, "task_1")
        assert result is True
        assert "task_1" in sprint.task_ids

    def test_complete_task_in_sprint(self):
        agent = SeniorPMAgent()
        start = datetime.now()
        end = start + timedelta(days=14)

        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete core features",
            start_date=start,
            end_date=end
        )

        agent.add_task_to_sprint(sprint.id, "task_1")
        result = agent.complete_task_in_sprint(sprint.id, "task_1")

        assert result is True
        assert "task_1" in sprint.completed_task_ids

    def test_block_task_in_sprint(self):
        agent = SeniorPMAgent()
        start = datetime.now()
        end = start + timedelta(days=14)

        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete core features",
            start_date=start,
            end_date=end
        )

        agent.add_task_to_sprint(sprint.id, "task_1")
        result = agent.block_task_in_sprint(sprint.id, "task_1")

        assert result is True
        assert "task_1" in sprint.blocked_task_ids

    def test_get_sprint_metrics(self):
        agent = SeniorPMAgent()
        start = datetime.now()
        end = start + timedelta(days=14)

        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete core features",
            start_date=start,
            end_date=end
        )

        agent.add_task_to_sprint(sprint.id, "task_1")
        agent.add_task_to_sprint(sprint.id, "task_2")
        agent.complete_task_in_sprint(sprint.id, "task_1")

        metrics = agent.get_sprint_metrics(sprint.id)

        assert metrics["total_tasks"] == 2
        assert metrics["completed_tasks"] == 1
        assert metrics["completion_rate"] == 0.5


class TestStakeholderManagement:
    """测试干系人管理"""

    def test_add_stakeholder(self):
        agent = SeniorPMAgent()
        stakeholder = agent.add_stakeholder(
            name="John Doe",
            role="CTO",
            influence=5,
            interest=4
        )

        assert stakeholder.id == "stakeholder_1"
        assert stakeholder.name == "John Doe"
        assert stakeholder.role == "CTO"
        assert stakeholder.influence == 5
        assert stakeholder.interest == 4

    def test_get_stakeholder_matrix(self):
        agent = SeniorPMAgent()

        # High influence, high interest -> manage_close
        agent.add_stakeholder("CEO", "CEO", influence=5, interest=5)
        # High influence, low interest -> keep_satisfied
        agent.add_stakeholder("Investor", "Investor", influence=5, interest=2)
        # Low influence, high interest -> keep_informed
        agent.add_stakeholder("Junior Dev", "Developer", influence=2, interest=4)

        matrix = agent.get_stakeholder_matrix()

        assert len(matrix["manage_close"]) == 1
        assert len(matrix["keep_satisfied"]) == 1
        assert len(matrix["keep_informed"]) == 1

    def test_get_communication_plan(self):
        agent = SeniorPMAgent()
        agent.add_stakeholder("CEO", "CEO", influence=5, interest=5)

        plan = agent.get_communication_plan()
        assert "weekly" in plan or "monthly" in plan


class TestRiskManagement:
    """测试风险管理"""

    def test_identify_risk(self):
        agent = SeniorPMAgent()
        risk = agent.identify_risk(
            title="Resource Shortage",
            description="Not enough developers",
            probability=0.6,
            impact=RiskLevel.HIGH,
            category="resource",
            mitigation_plan="Hire contractors",
            owner="PM"
        )

        assert risk.id == "risk_1"
        assert risk.title == "Resource Shortage"
        assert risk.probability == 0.6
        assert risk.impact == RiskLevel.HIGH

    def test_get_risk_matrix(self):
        agent = SeniorPMAgent()

        agent.identify_risk(
            title="Critical Risk",
            description="Critical",
            probability=0.8,
            impact=RiskLevel.CRITICAL,
            category="technical",
            mitigation_plan="Mitigation",
            owner="PM"
        )

        agent.identify_risk(
            title="Low Risk",
            description="Low",
            probability=0.2,
            impact=RiskLevel.LOW,
            category="external",
            mitigation_plan="Mitigation",
            owner="PM"
        )

        matrix = agent.get_risk_matrix()
        assert len(matrix["critical"]) >= 1
        assert len(matrix["low"]) >= 1

    def test_get_top_risks(self):
        agent = SeniorPMAgent()

        agent.identify_risk(
            title="Risk 1",
            description="Description",
            probability=0.9,
            impact=RiskLevel.HIGH,
            category="technical",
            mitigation_plan="Mitigation",
            owner="PM"
        )

        agent.identify_risk(
            title="Risk 2",
            description="Description",
            probability=0.3,
            impact=RiskLevel.LOW,
            category="external",
            mitigation_plan="Mitigation",
            owner="PM"
        )

        top = agent.get_top_risks(limit=1)
        assert len(top) == 1
        assert top[0].title == "Risk 1"  # Higher risk value


class TestDecisionManagement:
    """测试决策管理"""

    def test_create_decision(self):
        agent = SeniorPMAgent()
        decision = agent.create_decision(
            title="Choose Tech Stack",
            description="Need to decide between React and Vue",
            decision="Use React",
            rationale="Larger ecosystem",
            alternatives=["Use Vue", "Use Angular"],
            impact="high"
        )

        assert decision.id == "decision_1"
        assert decision.title == "Choose Tech Stack"
        assert decision.status == DecisionStatus.PENDING

    def test_approve_decision(self):
        agent = SeniorPMAgent()
        decision = agent.create_decision(
            title="Test Decision",
            description="Test",
            decision="Approve",
            rationale="Test"
        )

        result = agent.approve_decision(decision.id, decided_by="PM")
        assert result is True
        assert decision.status == DecisionStatus.APPROVED
        assert decision.decided_by == "PM"

    def test_get_pending_decisions(self):
        agent = SeniorPMAgent()

        agent.create_decision(
            title="Pending 1",
            description="Test",
            decision="Decision 1",
            rationale="Rationale"
        )

        agent.create_decision(
            title="Pending 2",
            description="Test",
            decision="Decision 2",
            rationale="Rationale"
        )

        pending = agent.get_pending_decisions()
        assert len(pending) == 2


class TestReporting:
    """测试报告生成"""

    def test_generate_executive_report(self):
        agent = SeniorPMAgent(project_name="Test Project")

        # Add some data
        agent.create_strategy(
            name="Test Strategy",
            strategy_type=StrategyType.GROWTH,
            vision="Test vision"
        )

        agent.add_stakeholder("CEO", "CEO", influence=5, interest=5)

        report = agent.generate_executive_report()

        assert "Test Project" in report
        assert "Executive Report" in report
        assert "Total Strategies" in report
        assert "Stakeholders" in report

    def test_generate_executive_report_html(self):
        agent = SeniorPMAgent(project_name="HTML Report Test")

        # Add some data
        agent.create_strategy(
            name="Test Strategy",
            strategy_type=StrategyType.GROWTH,
            vision="Test vision"
        )

        agent.add_stakeholder("CEO", "CEO", influence=5, interest=5)
        agent.add_stakeholder("Investor", "Investor", influence=4, interest=2)

        start = datetime.now()
        end = start + timedelta(days=14)
        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete core features",
            start_date=start,
            end_date=end
        )
        agent.start_sprint(sprint.id)

        agent.identify_risk(
            title="Technical Risk",
            description="API may fail",
            probability=0.6,
            impact=RiskLevel.HIGH,
            category="technical",
            mitigation_plan="Add fallback",
            owner="CTO"
        )

        html = agent.generate_executive_report_html()

        # HTML structure checks
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "<title>" in html
        assert "HTML Report Test" in html
        assert "Executive Report" in html
        assert "<style>" in html
        assert "Strategies" in html
        assert "Sprint 1" in html
        assert "Technical Risk" in html
        assert "CEO" in html  # stakeholder
        assert "</html>" in html

    def test_generate_sprint_burndown(self):
        agent = SeniorPMAgent()
        start = datetime.now()
        end = start + timedelta(days=14)

        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete features",
            start_date=start,
            end_date=end
        )

        agent.add_task_to_sprint(sprint.id, "task_1")
        agent.add_task_to_sprint(sprint.id, "task_2")

        burndown = agent.generate_sprint_burndown(sprint.id)

        assert "days" in burndown
        assert "remaining" in burndown
        assert "ideal" in burndown

    def test_get_velocity_trend(self):
        agent = SeniorPMAgent()

        # Create completed sprints
        for i in range(3):
            start = datetime.now() - timedelta(days=28 + i*14)
            end = start + timedelta(days=14)
            sprint = agent.create_sprint(
                name=f"Sprint {i+1}",
                goal="Test",
                start_date=start,
                end_date=end
            )
            sprint.status = "completed"
            sprint.velocity = 10 + i * 2

        trend = agent.get_velocity_trend()

        assert "sprints" in trend
        assert "velocity" in trend
        assert len(trend["velocity"]) == 3


class TestRetrospective:
    """测试回顾功能"""

    def test_add_retrospective(self):
        agent = SeniorPMAgent()
        start = datetime.now()
        end = start + timedelta(days=14)

        sprint = agent.create_sprint(
            name="Sprint 1",
            goal="Complete features",
            start_date=start,
            end_date=end
        )

        notes = "Team did well. Need to improve communication."
        actions = ["Daily standups", "Better documentation"]

        result = agent.add_retrospective(sprint.id, notes, actions)

        assert result is True
        assert sprint.retrospective_notes == notes
        assert sprint.metrics["improvement_actions"] == actions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
