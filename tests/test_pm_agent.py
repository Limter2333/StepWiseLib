"""
PM Agent Tests
"""

import pytest
from datetime import datetime, timedelta
from agents.pm_agent.pm_agent import (
    PMAgent,
    ProjectTask,
    Milestone,
    Risk,
    TaskStatus,
    TaskPriority,
    ProjectReport,
    ProductSpec
)


class TestPMAgentCreation:
    """测试PMAgent创建"""

    def test_agent_creation(self):
        agent = PMAgent(project_name="Test Project")
        assert agent.name == "PM Agent"
        assert agent.project_name == "Test Project"
        assert len(agent.tasks) == 0

    def test_agent_creation_default_name(self):
        agent = PMAgent()
        assert agent.project_name == "AI Multi-Agent System"


class TestTaskStatus:
    """测试任务状态枚举"""

    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_status_count(self):
        assert len(TaskStatus) == 5


class TestTaskPriority:
    """测试任务优先级枚举"""

    def test_task_priority_values(self):
        assert TaskPriority.CRITICAL.value == 1
        assert TaskPriority.HIGH.value == 2
        assert TaskPriority.MEDIUM.value == 3
        assert TaskPriority.LOW.value == 4

    def test_task_priority_values_comparable(self):
        # TaskPriority values are integers, higher number = lower priority
        assert TaskPriority.CRITICAL.value == 1
        assert TaskPriority.HIGH.value == 2
        assert TaskPriority.MEDIUM.value == 3
        assert TaskPriority.LOW.value == 4


class TestProjectTask:
    """测试项目任务数据类"""

    def test_task_creation(self):
        task = ProjectTask(
            id="task_1",
            title="Test Task",
            description="Description"
        )

        assert task.id == "task_1"
        assert task.title == "Test Task"
        assert task.description == "Description"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.progress == 0.0

    def test_task_with_priority(self):
        task = ProjectTask(
            id="task_2",
            title="Urgent Task",
            description="High priority",
            priority=TaskPriority.HIGH
        )

        assert task.priority == TaskPriority.HIGH

    def test_task_with_due_date(self):
        future = datetime.now() + timedelta(days=7)
        task = ProjectTask(
            id="task_3",
            title="Task with deadline",
            description="",
            due_date=future
        )

        assert task.due_date == future


class TestMilestone:
    """测试里程碑数据类"""

    def test_milestone_creation(self):
        target = datetime.now() + timedelta(days=30)
        ms = Milestone(
            id="ms_1",
            name="v1.0 Release",
            description="First major release",
            target_date=target
        )

        assert ms.id == "ms_1"
        assert ms.name == "v1.0 Release"
        assert ms.target_date == target
        assert ms.status == "pending"
        assert ms.tasks == []

    def test_milestone_with_tasks(self):
        target = datetime.now() + timedelta(days=14)
        ms = Milestone(
            id="ms_2",
            name="Sprint 1",
            description="First sprint",
            target_date=target,
            tasks=["task_1", "task_2"]
        )

        assert len(ms.tasks) == 2


class TestRisk:
    """测试风险数据类"""

    def test_risk_creation(self):
        risk = Risk(
            id="risk_1",
            title="Resource Shortage",
            description="Not enough developers"
        )

        assert risk.id == "risk_1"
        assert risk.title == "Resource Shortage"
        assert risk.severity == "medium"
        assert risk.probability == 0.5
        assert risk.status == "open"

    def test_risk_with_custom_values(self):
        risk = Risk(
            id="risk_2",
            title="Tech Risk",
            description="New technology may fail",
            severity="high",
            probability=0.7,
            mitigation="Have backup plan"
        )

        assert risk.severity == "high"
        assert risk.probability == 0.7
        assert risk.mitigation == "Have backup plan"


class TestPMAgentTaskCreation:
    """测试PMAgent任务创建"""

    def test_create_task(self):
        agent = PMAgent()

        task = agent.create_task(
            title="New Feature",
            description="Implement new feature"
        )

        assert task is not None
        assert task.title == "New Feature"
        assert "task_" in task.id

    def test_create_task_with_priority(self):
        agent = PMAgent()

        task = agent.create_task(
            title="Urgent",
            priority=TaskPriority.CRITICAL
        )

        assert task.priority == TaskPriority.CRITICAL

    def test_create_task_with_assignee(self):
        agent = PMAgent()

        task = agent.create_task(
            title="Assign to dev",
            assignee="developer_1"
        )

        assert task.assignee == "developer_1"

    def test_create_task_with_due_date(self):
        agent = PMAgent()
        future = datetime.now() + timedelta(days=5)

        task = agent.create_task(
            title="Deadline task",
            due_date=future
        )

        assert task.due_date == future

    def test_create_task_with_dependencies(self):
        agent = PMAgent()

        task = agent.create_task(
            title="Dependent task",
            dependencies=["task_1", "task_2"]
        )

        assert len(task.dependencies) == 2

    def test_create_multiple_tasks(self):
        agent = PMAgent()

        task1 = agent.create_task(title="Task 1")
        task2 = agent.create_task(title="Task 2")

        assert task1.id != task2.id


class TestPMAgentTaskUpdate:
    """测试PMAgent任务更新"""

    def test_update_task_status(self):
        agent = PMAgent()
        task = agent.create_task(title="To update")

        result = agent.update_task(task.id, status=TaskStatus.IN_PROGRESS)

        assert result is True
        assert task.status == TaskStatus.IN_PROGRESS

    def test_update_task_progress(self):
        agent = PMAgent()
        task = agent.create_task(title="To update")

        result = agent.update_task(task.id, progress=0.5)

        assert result is True
        assert task.progress == 0.5

    def test_update_task_to_completed(self):
        agent = PMAgent()
        task = agent.create_task(title="To complete")

        result = agent.update_task(task.id, status=TaskStatus.COMPLETED)

        assert result is True
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.progress == 1.0

    def test_update_nonexistent_task(self):
        agent = PMAgent()

        result = agent.update_task("nonexistent", status=TaskStatus.COMPLETED)

        assert result is False

    def test_update_task_progress_bounds(self):
        agent = PMAgent()
        task = agent.create_task(title="Bounds test")

        agent.update_task(task.id, progress=1.5)
        assert task.progress == 1.0

        agent.update_task(task.id, progress=-0.5)
        assert task.progress == 0.0


class TestPMAgentMilestone:
    """测试PMAgent里程碑管理"""

    def test_create_milestone(self):
        agent = PMAgent()
        target = datetime.now() + timedelta(days=30)

        ms = agent.create_milestone(
            name="v1.0",
            description="Version 1.0",
            target_date=target
        )

        assert ms is not None
        assert ms.name == "v1.0"
        assert "ms_" in ms.id

    def test_create_milestone_with_tasks(self):
        agent = PMAgent()
        task = agent.create_task(title="Linked task")
        target = datetime.now() + timedelta(days=14)

        ms = agent.create_milestone(
            name="Sprint 1",
            description="First sprint",
            target_date=target,
            task_ids=[task.id]
        )

        assert task.id in ms.tasks


class TestPMAgentRisk:
    """测试PMAgent风险管理"""

    def test_add_risk(self):
        agent = PMAgent()

        risk = agent.add_risk(
            title="Budget Risk",
            description="May exceed budget"
        )

        assert risk is not None
        assert risk.title == "Budget Risk"
        assert "risk_" in risk.id

    def test_add_risk_with_severity(self):
        agent = PMAgent()

        risk = agent.add_risk(
            title="Critical Risk",
            description="Could fail entire project",
            severity="critical"
        )

        assert risk.severity == "critical"


class TestPMAgentProgress:
    """测试PMAgent进度追踪"""

    def test_get_progress_empty(self):
        agent = PMAgent()

        progress = agent.get_progress()

        assert progress["tasks"] == 0
        assert progress["progress"] == 0.0

    def test_get_progress_with_tasks(self):
        agent = PMAgent()
        agent.create_task(title="Task 1")
        agent.create_task(title="Task 2")
        agent.create_task(title="Task 3")

        progress = agent.get_progress()

        assert progress["total_tasks"] == 3
        assert progress["completed"] == 0

    def test_get_progress_with_completed(self):
        agent = PMAgent()
        t1 = agent.create_task(title="Task 1")
        agent.create_task(title="Task 2")

        agent.update_task(t1.id, status=TaskStatus.COMPLETED)

        progress = agent.get_progress()

        assert progress["completed"] == 1
        assert progress["completion_rate"] == 0.5


class TestPMAgentOverdue:
    """测试逾期任务"""

    def test_get_overdue_tasks(self):
        agent = PMAgent()
        past = datetime.now() - timedelta(days=1)

        task = agent.create_task(
            title="Overdue task",
            due_date=past
        )

        overdue = agent.get_overdue_tasks()

        assert len(overdue) == 1
        assert overdue[0].id == task.id

    def test_get_overdue_completed_not_included(self):
        agent = PMAgent()
        past = datetime.now() - timedelta(days=1)

        task = agent.create_task(
            title="Completed but overdue",
            due_date=past
        )
        agent.update_task(task.id, status=TaskStatus.COMPLETED)

        overdue = agent.get_overdue_tasks()

        assert len(overdue) == 0


class TestReportGeneration:
    """测试报告生成"""

    def test_generate_markdown_report(self):
        agent = PMAgent()
        agent.create_task(title="Task 1")
        agent.create_task(title="Task 2")

        report = agent.generate_report(format="markdown")

        assert "# AI Multi-Agent System - Project Report" in report or "Test Project" in report or "AI Multi-Agent System" in report
        assert "Task 1" in report
        assert "Task 2" in report

    def test_generate_json_report(self):
        agent = PMAgent()
        agent.create_task(title="JSON Task")

        report = agent.generate_report(format="json")

        import json
        data = json.loads(report)
        assert "project" in data
        assert data["summary"]["total_tasks"] == 1


class TestProductSpec:
    """测试产品规范验证"""

    def test_product_spec_required_agents(self):
        assert "dev_agent" in ProductSpec.REQUIRED_AGENTS
        assert "doc_agent" in ProductSpec.REQUIRED_AGENTS
        assert "test_agent" in ProductSpec.REQUIRED_AGENTS
        assert "pm_agent" in ProductSpec.REQUIRED_AGENTS

    def test_product_spec_required_modules(self):
        assert "guardrails" in ProductSpec.REQUIRED_MODULES
        assert "token_manager" in ProductSpec.REQUIRED_MODULES

    def test_product_spec_required_parsers(self):
        assert "pdf" in ProductSpec.REQUIRED_PARSERS
        assert "docx" in ProductSpec.REQUIRED_PARSERS
        assert len(ProductSpec.REQUIRED_PARSERS) >= 14

    def test_validate_delivery_passes(self):
        # Complete checklist - all agents, modules, parsers, and coverage
        checklist = {
            "agent_dev_agent": True,
            "agent_doc_agent": True,
            "agent_test_agent": True,
            "agent_rag_agent": True,
            "agent_pm_agent": True,
            "agent_conversation_agent": True,
            "agent_evaluator_agent": True,
            "agent_ops_agent": True,
            "module_guardrails": True,
            "module_token_manager": True,
            "module_short_term_memory": True,
            "module_long_term_memory": True,
            "module_prompt_engine": True,
            "parser_pdf": True,
            "parser_docx": True,
            "parser_xlsx": True,
            "parser_pptx": True,
            "parser_csv": True,
            "parser_json": True,
            "parser_yaml": True,
            "parser_xml": True,
            "parser_rtf": True,
            "parser_epub": True,
            "parser_markdown": True,
            "parser_text": True,
            "parser_web": True,
            "parser_txt": True,
            "test_coverage": 0.85
        }

        passed, failures = ProductSpec.validate_delivery(checklist)

        assert passed is True
        assert len(failures) == 0

    def test_validate_delivery_fails_missing_agent(self):
        checklist = {
            "agent_dev_agent": True,
            # missing doc_agent
            "module_guardrails": True,
            "parser_pdf": True,
            "test_coverage": 0.85
        }

        passed, failures = ProductSpec.validate_delivery(checklist)

        assert passed is False
        assert any("doc_agent" in f for f in failures)

    def test_validate_delivery_fails_low_coverage(self):
        # Complete agents and modules but low coverage
        checklist = {
            "agent_dev_agent": True,
            "agent_doc_agent": True,
            "agent_test_agent": True,
            "agent_rag_agent": True,
            "agent_pm_agent": True,
            "agent_conversation_agent": True,
            "agent_evaluator_agent": True,
            "agent_ops_agent": True,
            "module_guardrails": True,
            "module_token_manager": True,
            "module_short_term_memory": True,
            "module_long_term_memory": True,
            "module_prompt_engine": True,
            "parser_pdf": True,
            "parser_docx": True,
            "parser_xlsx": True,
            "parser_pptx": True,
            "parser_csv": True,
            "parser_json": True,
            "parser_yaml": True,
            "parser_xml": True,
            "parser_rtf": True,
            "parser_epub": True,
            "parser_markdown": True,
            "parser_text": True,
            "parser_web": True,
            "parser_txt": True,
            "test_coverage": 0.5  # below 80%
        }

        passed, failures = ProductSpec.validate_delivery(checklist)

        assert passed is False
        assert any("覆盖率" in f or "coverage" in f.lower() for f in failures)


class TestCapabilities:
    """测试能力获取"""

    def test_get_capabilities(self):
        agent = PMAgent()

        caps = agent.get_capabilities()

        assert caps["name"] == "PM Agent"
        assert "task_management" in caps["features"]
        assert "milestone_tracking" in caps["features"]
        assert "progress_reporting" in caps["features"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
