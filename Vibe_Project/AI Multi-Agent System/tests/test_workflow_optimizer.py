"""
Workflow Optimizer Agent Tests
"""

import pytest
from agents.workflow_optimizer.workflow_optimizer import (
    WorkflowOptimizer,
    WorkflowType,
    OptimizationType,
    WorkflowStep,
    Workflow,
    OptimizationResult
)


class TestWorkflowType:
    """测试工作流类型枚举"""

    def test_workflow_type_values(self):
        assert WorkflowType.SEQUENTIAL.value == "sequential"
        assert WorkflowType.PARALLEL.value == "parallel"
        assert WorkflowType.CONDITIONAL.value == "conditional"
        assert WorkflowType.EVENT_DRIVEN.value == "event_driven"
        assert WorkflowType.APPROVAL.value == "approval"

    def test_workflow_type_count(self):
        assert len(WorkflowType) == 5


class TestOptimizationType:
    """测试优化类型枚举"""

    def test_optimization_type_values(self):
        assert OptimizationType.SPEED.value == "speed"
        assert OptimizationType.COST.value == "cost"
        assert OptimizationType.QUALITY.value == "quality"
        assert OptimizationType.THROUGHPUT.value == "throughput"

    def test_optimization_type_count(self):
        assert len(OptimizationType) == 4


class TestWorkflowStep:
    """测试工作流步骤数据类"""

    def test_step_creation(self):
        step = WorkflowStep(
            id="step_1",
            name="Design",
            description="Design phase",
            duration_minutes=60
        )

        assert step.id == "step_1"
        assert step.name == "Design"
        assert step.duration_minutes == 60
        assert step.cost == 0.0  # default
        assert step.dependencies == []  # default

    def test_step_with_dependencies(self):
        step = WorkflowStep(
            id="step_2",
            name="Build",
            description="Build phase",
            duration_minutes=120,
            dependencies=["step_1"],
            assignee="dev",
            automation_potential=0.8
        )

        assert step.dependencies == ["step_1"]
        assert step.assignee == "dev"
        assert step.automation_potential == 0.8


class TestWorkflow:
    """测试工作流数据类"""

    def test_workflow_creation(self):
        step = WorkflowStep(
            id="step_1",
            name="Test",
            description="Test",
            duration_minutes=30
        )
        workflow = Workflow(
            id="wf_1",
            name="Test Workflow",
            steps=[step],
            workflow_type=WorkflowType.SEQUENTIAL
        )

        assert workflow.id == "wf_1"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 1
        assert workflow.total_duration == 0.0  # default

    def test_workflow_with_cost(self):
        step = WorkflowStep(
            id="s1",
            name="Code",
            description="Code",
            duration_minutes=60,
            cost=100.0
        )
        workflow = Workflow(
            id="wf_2",
            name="Dev Workflow",
            steps=[step],
            workflow_type=WorkflowType.PARALLEL,
            total_duration=60.0,
            total_cost=100.0
        )

        assert workflow.total_duration == 60.0
        assert workflow.total_cost == 100.0


class TestOptimizationResult:
    """测试优化结果数据类"""

    def test_result_creation(self):
        step1 = WorkflowStep(id="s1", name="A", description="a", duration_minutes=30)
        step2 = WorkflowStep(id="s2", name="B", description="b", duration_minutes=30)

        original = Workflow(id="orig", name="Original", steps=[step1], workflow_type=WorkflowType.SEQUENTIAL)
        optimized = Workflow(id="opt", name="Optimized", steps=[step2], workflow_type=WorkflowType.PARALLEL)

        result = OptimizationResult(
            original_workflow=original,
            optimized_workflow=optimized
        )

        assert result.original_workflow.id == "orig"
        assert result.optimized_workflow.id == "opt"
        assert result.improvements == []  # default

    def test_result_with_savings(self):
        step1 = WorkflowStep(id="s1", name="A", description="a", duration_minutes=60)
        step2 = WorkflowStep(id="s2", name="B", description="b", duration_minutes=30)

        original = Workflow(id="orig", name="Original", steps=[step1], workflow_type=WorkflowType.SEQUENTIAL)
        optimized = Workflow(id="opt", name="Optimized", steps=[step2], workflow_type=WorkflowType.PARALLEL)

        result = OptimizationResult(
            original_workflow=original,
            optimized_workflow=optimized,
            improvements=[{"type": "parallel", "savings": 30}],
            time_savings_minutes=30.0,
            cost_savings=50.0,
            automation_opportunities=["step_1"],
            recommendations=["Use parallel processing"]
        )

        assert result.time_savings_minutes == 30.0
        assert result.cost_savings == 50.0
        assert len(result.automation_opportunities) == 1


class TestWorkflowOptimizer:
    """测试工作流优化智能体"""

    def test_agent_creation(self):
        agent = WorkflowOptimizer()
        assert agent.name == "Workflow Optimizer"

    def test_global_instance_exists(self):
        from agents.workflow_optimizer import workflow_optimizer
        assert workflow_optimizer.name == "Workflow Optimizer"

    def test_get_capabilities(self):
        agent = WorkflowOptimizer()
        caps = agent.get_capabilities()

        assert caps["name"] == "Workflow Optimizer"
        assert len(caps["workflow_types"]) > 0
        assert len(caps["optimization_types"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
