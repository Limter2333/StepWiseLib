"""
Workflow Optimizer Agent - 工作流优化智能体
=========================================

职责:
- 流程分析
- 瓶颈识别
- 效率优化
- 自动化建议
- 协作流程改进
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WorkflowType(Enum):
    """工作流类型"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    EVENT_DRIVEN = "event_driven"
    APPROVAL = "approval"


class OptimizationType(Enum):
    """优化类型"""
    SPEED = "speed"
    COST = "cost"
    QUALITY = "quality"
    THROUGHPUT = "throughput"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    name: str
    description: str
    duration_minutes: float
    cost: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    automation_potential: float = 0.0  # 0-1


@dataclass
class Workflow:
    """工作流"""
    id: str
    name: str
    steps: List[WorkflowStep]
    workflow_type: WorkflowType
    total_duration: float = 0.0
    total_cost: float = 0.0


@dataclass
class OptimizationResult:
    """优化结果"""
    original_workflow: Workflow
    optimized_workflow: Workflow
    improvements: List[Dict] = field(default_factory=list)
    time_savings_minutes: float = 0.0
    cost_savings: float = 0.0
    automation_opportunities: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class WorkflowOptimizer:
    """工作流优化智能体

    【能力】
    - 分析工作流
    - 识别瓶颈
    - 提出优化方案
    - 自动化建议
    - 协作流程改进
    """

    def __init__(self):
        self.name = "Workflow Optimizer"
        self.specialty = ["流程优化", "效率提升", "自动化", "协作改进"]
        self.workflows: List[Workflow] = []

    def analyze_workflow(
        self,
        steps: List[Dict],
        workflow_type: str = "sequential"
    ) -> Workflow:
        """分析工作流

        Args:
            steps: 步骤列表
            workflow_type: 工作流类型

        Returns:
            Workflow: 分析后的工作流
        """
        workflow_steps = []
        total_duration = 0.0
        total_cost = 0.0

        for i, step_data in enumerate(steps):
            step = WorkflowStep(
                id=f"STEP-{i + 1:03d}",
                name=step_data.get("name", f"Step {i + 1}"),
                description=step_data.get("description", ""),
                duration_minutes=step_data.get("duration_minutes", 30),
                cost=step_data.get("cost", 0.0),
                dependencies=step_data.get("dependencies", []),
                assignee=step_data.get("assignee"),
                automation_potential=step_data.get("automation_potential", 0.5)
            )
            workflow_steps.append(step)
            total_duration += step.duration_minutes
            total_cost += step.cost

        workflow = Workflow(
            id=f"WF-{len(self.workflows) + 1:03d}",
            name=steps[0].get("workflow_name", "Unnamed Workflow") if steps else "Workflow",
            steps=workflow_steps,
            workflow_type=WorkflowType(workflow_type),
            total_duration=total_duration,
            total_cost=total_cost
        )

        self.workflows.append(workflow)
        return workflow

    def identify_bottlenecks(
        self,
        workflow: Workflow
    ) -> List[Dict]:
        """识别瓶颈

        Args:
            workflow: 工作流

        Returns:
            List[Dict]: 瓶颈列表
        """
        bottlenecks = []

        # 按耗时排序
        sorted_steps = sorted(
            workflow.steps,
            key=lambda s: s.duration_minutes,
            reverse=True
        )

        # 识别前3个耗时步骤
        for step in sorted_steps[:3]:
            if step.duration_minutes > 10:  # 超过10分钟的步骤视为瓶颈
                bottleneck = {
                    "step_id": step.id,
                    "step_name": step.name,
                    "duration_minutes": step.duration_minutes,
                    "percentage": (step.duration_minutes / workflow.total_duration * 100)
                    if workflow.total_duration > 0 else 0,
                    "severity": "high" if step.duration_minutes > 60 else "medium",
                    "cause": self._analyze_bottleneck_cause(step),
                    "suggestion": self._generate_bottleneck_suggestion(step)
                }
                bottlenecks.append(bottleneck)

        # 检查依赖关系中的空闲时间
        bottlenecks.extend(self._check_wait_times(workflow))

        return bottlenecks

    def _analyze_bottleneck_cause(self, step: WorkflowStep) -> str:
        """分析瓶颈原因"""
        causes = []

        if step.duration_minutes > 60:
            causes.append("Long execution time")
        if step.automation_potential > 0.7:
            causes.append("High automation potential but manual")
        if not step.assignee:
            causes.append("Unassigned - may cause delays")
        if len(step.dependencies) > 2:
            causes.append("Complex dependencies")

        return "; ".join(causes) if causes else "Complex operation requiring significant time"

    def _generate_bottleneck_suggestion(self, step: WorkflowStep) -> str:
        """生成瓶颈解决建议"""
        suggestions = []

        if step.automation_potential > 0.5:
            suggestions.append(
                f"Consider automating '{step.name}' "
                f"(potential: {step.automation_potential:.0%})"
            )

        if step.duration_minutes > 30:
            suggestions.append(f"Break down into smaller parallel tasks")

        if not step.assignee:
            suggestions.append("Assign to team member or consider automation")

        return suggestions[0] if suggestions else "Review and optimize"

    def _check_wait_times(self, workflow: Workflow) -> List[Dict]:
        """检查等待时间"""
        wait_issues = []

        # 简单检查：步骤之间如果有依赖，检查是否有等待
        for step in workflow.steps:
            if step.dependencies and step.duration_minutes < 5:
                wait_issues.append({
                    "step_id": step.id,
                    "step_name": step.name,
                    "issue": "Short task with dependencies - may cause waiting",
                    "suggestion": "Consider combining with preceding task"
                })

        return wait_issues

    def optimize_workflow(
        self,
        workflow: Workflow,
        optimization_type: str = "speed"
    ) -> OptimizationResult:
        """优化工作流

        Args:
            workflow: 原始工作流
            optimization_type: 优化类型 (speed/cost/quality/throughput)

        Returns:
            OptimizationResult: 优化结果
        """
        improvements = []
        time_savings = 0.0
        cost_savings = 0.0
        automation_opportunities = []

        # 并行化建议
        parallel_suggestions = self._suggest_parallelization(workflow)
        improvements.extend(parallel_suggestions)

        # 自动化建议
        automation_suggestions = self._suggest_automation(workflow)
        improvements.extend(automation_suggestions)
        automation_opportunities = [s["step_name"] for s in automation_suggestions]

        # 简化依赖
        dependency_suggestions = self._simplify_dependencies(workflow)
        improvements.extend(dependency_suggestions)

        # 计算节省
        for improvement in improvements:
            if "time_savings" in improvement:
                time_savings += improvement["time_savings"]
            if "cost_savings" in improvement:
                cost_savings += improvement["cost_savings"]

        # 生成优化后的工作流
        optimized_steps = self._apply_optimizations(workflow, improvements)

        optimized_workflow = Workflow(
            id=workflow.id + "_OPT",
            name=workflow.name + " (Optimized)",
            steps=optimized_steps,
            workflow_type=workflow.workflow_type,
            total_duration=workflow.total_duration - time_savings,
            total_cost=workflow.total_cost - cost_savings
        )

        recommendations = self._generate_recommendations(workflow, improvements)

        return OptimizationResult(
            original_workflow=workflow,
            optimized_workflow=optimized_workflow,
            improvements=improvements,
            time_savings_minutes=time_savings,
            cost_savings=cost_savings,
            automation_opportunities=automation_opportunities,
            recommendations=recommendations
        )

    def _suggest_parallelization(self, workflow: Workflow) -> List[Dict]:
        """建议并行化"""
        suggestions = []

        # 查找可以并行的独立步骤
        independent_steps = []
        for step in workflow.steps:
            if not step.dependencies and step.duration_minutes > 10:
                independent_steps.append(step)

        if len(independent_steps) >= 2:
            suggestions.append({
                "type": "parallelization",
                "description": f"Run {len(independent_steps)} steps in parallel",
                "steps": [s.id for s in independent_steps],
                "time_savings": sum(s.duration_minutes for s in independent_steps) * 0.4,
                "priority": "high"
            })

        return suggestions

    def _suggest_automation(self, workflow: Workflow) -> List[Dict]:
        """建议自动化"""
        suggestions = []

        for step in workflow.steps:
            if step.automation_potential > 0.7:
                suggestions.append({
                    "type": "automation",
                    "description": f"Automate '{step.name}'",
                    "step_id": step.id,
                    "step_name": step.name,
                    "automation_potential": step.automation_potential,
                    "time_savings": step.duration_minutes * 0.8,  # 假设自动化可节省80%时间
                    "cost_savings": step.cost * 0.7,
                    "priority": "high" if step.automation_potential > 0.9 else "medium"
                })

        return suggestions

    def _simplify_dependencies(self, workflow: Workflow) -> List[Dict]:
        """简化依赖"""
        suggestions = []

        for step in workflow.steps:
            if len(step.dependencies) > 2:
                suggestions.append({
                    "type": "dependency_simplification",
                    "description": f"Reduce dependencies for '{step.name}'",
                    "step_id": step.id,
                    "current_dependencies": len(step.dependencies),
                    "suggested_approach": "Consider breaking into smaller, less coupled steps",
                    "time_savings": 5,  # 简化依赖可节省约5分钟
                    "priority": "low"
                })

        return suggestions

    def _apply_optimizations(
        self,
        workflow: Workflow,
        improvements: List[Dict]
    ) -> List[WorkflowStep]:
        """应用优化"""
        optimized_steps = []

        for step in workflow.steps:
            # 检查是否有针对此步骤的自动化优化
            auto_improvement = next(
                (i for i in improvements
                 if i.get("type") == "automation" and i.get("step_id") == step.id),
                None
            )

            if auto_improvement:
                # 克隆步骤并应用优化
                new_step = WorkflowStep(
                    id=step.id,
                    name=step.name,
                    description=step.description + " (automated)",
                    duration_minutes=step.duration_minutes * (1 - auto_improvement.get("time_savings", 0) / step.duration_minutes if step.duration_minutes > 0 else 0),
                    cost=step.cost * (1 - auto_improvement.get("cost_savings", 0) / step.cost if step.cost > 0 else 0),
                    dependencies=step.dependencies,
                    assignee=None,  # 自动化后不需要分配
                    automation_potential=1.0
                )
                optimized_steps.append(new_step)
            else:
                optimized_steps.append(step)

        return optimized_steps

    def _generate_recommendations(
        self,
        workflow: Workflow,
        improvements: List[Dict]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        # 基于优化类型生成建议
        high_priority = [i for i in improvements if i.get("priority") == "high"]

        if high_priority:
            recommendations.append(
                f"Focus on {len(high_priority)} high-priority improvements first"
            )

        automation_count = sum(1 for i in improvements if i.get("type") == "automation")
        if automation_count > 0:
            recommendations.append(
                f"Automation could save approximately "
                f"{sum(i.get('time_savings', 0) for i in improvements):.0f} minutes"
            )

        parallel_count = sum(1 for i in improvements if i.get("type") == "parallelization")
        if parallel_count > 0:
            recommendations.append(
                f"Parallel execution could reduce total time by up to 40%"
            )

        return recommendations

    def compare_workflows(
        self,
        workflow_a: Workflow,
        workflow_b: Workflow
    ) -> Dict:
        """对比两个工作流

        Returns:
            Dict: 对比结果
        """
        return {
            "workflow_a": {
                "id": workflow_a.id,
                "name": workflow_a.name,
                "duration": workflow_a.total_duration,
                "cost": workflow_a.total_cost,
                "step_count": len(workflow_a.steps)
            },
            "workflow_b": {
                "id": workflow_b.id,
                "name": workflow_b.name,
                "duration": workflow_b.total_duration,
                "cost": workflow_b.total_cost,
                "step_count": len(workflow_b.steps)
            },
            "comparison": {
                "time_difference": workflow_a.total_duration - workflow_b.total_duration,
                "cost_difference": workflow_a.total_cost - workflow_b.total_cost,
                "step_difference": len(workflow_a.steps) - len(workflow_b.steps),
                "winner": "B" if workflow_b.total_duration < workflow_a.total_duration else "A"
            }
        }

    def generate_workflow_diagram(
        self,
        workflow: Workflow,
        format: str = "mermaid"
    ) -> str:
        """生成工作流图

        Args:
            format: 格式 (mermaid/plain_text)

        Returns:
            str: 工作流图代码
        """
        if format == "mermaid":
            lines = ["```mermaid", "graph TD"]

            for step in workflow.steps:
                lines.append(f"    {step.id}[{step.name}]")

                for dep in step.dependencies:
                    lines.append(f"    {dep} --> {step.id}")

                if step.duration_minutes > 30:
                    lines.append(f"    {step.id} -.- \"(bottleneck)\"")

            lines.append("```")
            return "\n".join(lines)

        else:  # plain_text
            lines = [f"# {workflow.name}", ""]
            lines.append(f"Type: {workflow.workflow_type.value}")
            lines.append(f"Total Duration: {workflow.total_duration:.0f} minutes")
            lines.append(f"Total Cost: ${workflow.total_cost:.2f}", "")
            lines.append("## Steps", "")

            for step in workflow.steps:
                deps = f" (depends on: {', '.join(step.dependencies)})" if step.dependencies else ""
                lines.append(f"- {step.id}: {step.name} ({step.duration_minutes:.0f} min){deps}")

            return "\n".join(lines)

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "workflow_types": [w.value for w in WorkflowType],
            "optimization_types": [o.value for o in OptimizationType],
            "output_formats": ["mermaid", "json", "markdown", "plain_text"]
        }


# 全局实例
workflow_optimizer = WorkflowOptimizer()
