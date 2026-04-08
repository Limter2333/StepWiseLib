"""
PM Agent - 项目管理智能体
=========================

职责:
- 项目进度追踪
- 里程碑管理
- 风险管理
- 报告生成
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ProjectTask:
    """项目任务"""
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 - 1.0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Milestone:
    """里程碑"""
    id: str
    name: str
    description: str
    target_date: datetime
    tasks: List[str] = field(default_factory=list)  # task IDs
    status: str = "pending"  # pending, in_progress, achieved, missed
    achieved_at: Optional[datetime] = None


@dataclass
class Risk:
    """风险"""
    id: str
    title: str
    description: str
    severity: str = "medium"  # low, medium, high, critical
    probability: float = 0.5  # 0.0 - 1.0
    impact: str = "medium"  # low, medium, high
    mitigation: str = ""
    status: str = "open"  # open, mitigated, closed


class ProjectReport:
    """项目报告"""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.generated_at = datetime.now()

    def to_markdown(self, tasks: List[ProjectTask], milestones: List[Milestone], risks: List[Risk]) -> str:
        """生成Markdown报告"""
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        overdue = sum(1 for t in tasks if t.due_date and t.due_date < datetime.now() and t.status != TaskStatus.COMPLETED)

        content = f"""# {self.project_name} - Project Report

Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Tasks | {len(tasks)} |
| Completed | {completed} ({completed/len(tasks)*100:.1f}%) |
| In Progress | {in_progress} |
| Overdue | {overdue} |

## Progress

"""

        # 按状态分组
        for status in TaskStatus:
            status_tasks = [t for t in tasks if t.status == status]
            if status_tasks:
                content += f"""### {status.value.replace('_', ' ').title()}

"""
                for task in status_tasks:
                    content += f"- [{task.priority.name}] {task.title}"
                    if task.assignee:
                        content += f" (@{task.assignee})"
                    if task.due_date:
                        content += f" - Due: {task.due_date.strftime('%Y-%m-%d')}"
                    content += "\n"
                content += "\n"

        # 里程碑
        if milestones:
            content += """## Milestones

"""
            for ms in milestones:
                content += f"""### {ms.name}

- Target: {ms.target_date.strftime('%Y-%m-%d')}
- Status: {ms.status}
"""
                if ms.achieved_at:
                    content += f"- Achieved: {ms.achieved_at.strftime('%Y-%m-%d')}\n"
                content += "\n"

        # 风险
        if risks:
            content += """## Risks

"""
            for risk in risks:
                if risk.status == "open":
                    content += f"""- [{risk.severity.upper()}] {risk.title}
  - Probability: {risk.probability*100:.0f}%
  - Mitigation: {risk.mitigation or 'N/A'}

"""

        return content

    def to_json(self, tasks: List[ProjectTask], milestones: List[Milestone], risks: List[Risk]) -> str:
        """生成JSON报告"""
        return json.dumps({
            "project": self.project_name,
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "total_tasks": len(tasks),
                "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
                "in_progress": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
                "overdue": sum(1 for t in tasks if t.due_date and t.due_date < datetime.now())
            },
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority.name,
                    "progress": t.progress,
                    "due_date": t.due_date.isoformat() if t.due_date else None
                }
                for t in tasks
            ],
            "milestones": [
                {
                    "id": m.id,
                    "name": m.name,
                    "target_date": m.target_date.isoformat(),
                    "status": m.status
                }
                for m in milestones
            ],
            "risks": [
                {
                    "id": r.id,
                    "title": r.title,
                    "severity": r.severity,
                    "probability": r.probability,
                    "status": r.status
                }
                for r in risks
            ]
        }, indent=2)


class ProductSpec:
    """产品规范检查器"""

    # 核心Agent列表（必须实现）
    REQUIRED_AGENTS = [
        "dev_agent", "doc_agent", "test_agent", "rag_agent",
        "pm_agent", "conversation_agent", "evaluator_agent", "ops_agent"
    ]

    # 核心模块（必须实现）
    REQUIRED_MODULES = [
        "guardrails", "token_manager", "short_term_memory",
        "long_term_memory", "prompt_engine"
    ]

    # 支持的文档格式（至少14种）
    REQUIRED_PARSERS = [
        "pdf", "docx", "xlsx", "pptx", "csv", "json",
        "yaml", "xml", "rtf", "epub", "markdown", "text", "web", "txt"
    ]

    # 质量门槛
    TEST_COVERAGE_THRESHOLD = 0.80  # 80%
    INTENT_ACCURACY_THRESHOLD = 0.85  # 85%
    API_TEST_PASS_RATE = 1.0  # 100%

    @classmethod
    def validate_delivery(cls, checklist: Dict[str, bool]) -> tuple[bool, List[str]]:
        """验证交付物是否满足产品规范

        Returns:
            (是否通过, 失败原因列表)
        """
        failures = []

        # 检查核心Agent
        missing_agents = [a for a in cls.REQUIRED_AGENTS if not checklist.get(f"agent_{a}")]
        if missing_agents:
            failures.append(f"缺少Agent: {', '.join(missing_agents)}")

        # 检查核心模块
        missing_modules = [m for m in cls.REQUIRED_MODULES if not checklist.get(f"module_{m}")]
        if missing_modules:
            failures.append(f"缺少模块: {', '.join(missing_modules)}")

        # 检查文档解析器
        missing_parsers = [p for p in cls.REQUIRED_PARSERS if not checklist.get(f"parser_{p}")]
        if missing_parsers:
            failures.append(f"缺少解析器: {', '.join(missing_parsers)}")

        # 检查质量指标
        if checklist.get("test_coverage", 0) < cls.TEST_COVERAGE_THRESHOLD:
            failures.append(f"测试覆盖率不达标: {checklist['test_coverage']:.1%} < {cls.TEST_COVERAGE_THRESHOLD:.0%}")

        return (len(failures) == 0, failures)


class PMAgent:
    """PM智能体

    【能力】
    - 创建和管理任务
    - 跟踪里程碑
    - 风险评估
    - 生成项目报告
    - 产品规范验证

    【产品规范遵循】
    - 严格遵循PRODUCT.md定义的范围
    - 所有交付物必须通过ProductSpec验证
    - 禁止实现规范外的功能（除非评审通过）
    """

    def __init__(self, project_name: str = "AI Multi-Agent System"):
        self.name = "PM Agent"
        self.project_name = project_name
        self.tasks: Dict[str, ProjectTask] = {}
        self.milestones: Dict[str, Milestone] = {}
        self.risks: Dict[str, Risk] = {}
        self.task_counter = 0
        self.spec = ProductSpec()
        self.delivery_checklist: Dict[str, bool] = {}

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee: Optional[str] = None,
        due_date: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        status: Optional[TaskStatus] = None,
        progress: float = 0.0
    ) -> ProjectTask:
        """创建任务"""
        self.task_counter += 1
        task = ProjectTask(
            id=f"task_{self.task_counter}",
            title=title,
            description=description,
            priority=priority,
            assignee=assignee,
            due_date=due_date,
            status=status or TaskStatus.PENDING,
            progress=progress,
            dependencies=dependencies or []
        )
        self.tasks[task.id] = task
        return task

    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[float] = None,
        **kwargs
    ) -> bool:
        """更新任务"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        if status:
            task.status = status
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
                task.progress = 1.0

        if progress is not None:
            task.progress = min(1.0, max(0.0, progress))

        task.updated_at = datetime.now()

        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        return True

    def create_milestone(
        self,
        name: str,
        description: str,
        target_date: datetime,
        task_ids: Optional[List[str]] = None
    ) -> Milestone:
        """创建里程碑"""
        milestone = Milestone(
            id=f"ms_{len(self.milestones) + 1}",
            name=name,
            description=description,
            target_date=target_date,
            tasks=task_ids or []
        )
        self.milestones[milestone.id] = milestone
        return milestone

    def add_risk(
        self,
        title: str,
        description: str,
        severity: str = "medium",
        probability: float = 0.5,
        mitigation: str = ""
    ) -> Risk:
        """添加风险"""
        risk = Risk(
            id=f"risk_{len(self.risks) + 1}",
            title=title,
            description=description,
            severity=severity,
            probability=probability,
            mitigation=mitigation
        )
        self.risks[risk.id] = risk
        return risk

    def get_progress(self) -> Dict:
        """获取项目进度"""
        total = len(self.tasks)
        if total == 0:
            return {"progress": 0.0, "tasks": 0}

        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        total_progress = sum(t.progress for t in self.tasks.values())

        return {
            "total_tasks": total,
            "completed": completed,
            "in_progress": sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS),
            "overall_progress": total_progress / total,
            "completion_rate": completed / total
        }

    def get_overdue_tasks(self) -> List[ProjectTask]:
        """获取逾期任务"""
        now = datetime.now()
        return [
            t for t in self.tasks.values()
            if t.due_date and t.due_date < now and t.status != TaskStatus.COMPLETED
        ]

    def generate_report(self, format: str = "markdown") -> str:
        """生成项目报告"""
        report = ProjectReport(self.project_name)
        tasks_list = list(self.tasks.values())
        milestones_list = list(self.milestones.values())
        risks_list = list(self.risks.values())

        if format == "json":
            return report.to_json(tasks_list, milestones_list, risks_list)
        return report.to_markdown(tasks_list, milestones_list, risks_list)

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "project": self.project_name,
            "features": [
                "task_management",
                "milestone_tracking",
                "risk_assessment",
                "progress_reporting",
                "deadline_tracking"
            ]
        }


# 全局实例 - 项目初始化
pm_agent = PMAgent()

# 创建初始任务
pm_agent.create_task(
    title="项目基础框架搭建",
    description="创建项目目录结构、配置文件",
    priority=TaskPriority.HIGH,
    status=TaskStatus.COMPLETED,
    progress=1.0
)

pm_agent.create_task(
    title="核心模块实现",
    description="Token管理、Guardrails、记忆系统、Prompt引擎",
    priority=TaskPriority.HIGH,
    status=TaskStatus.COMPLETED,
    progress=1.0
)

pm_agent.create_task(
    title="Agent实现",
    description="Dev/Doc/Test/RAG/PM/Conversation Agent",
    priority=TaskPriority.HIGH,
    status=TaskStatus.IN_PROGRESS,
    progress=0.7
)

pm_agent.create_task(
    title="RAG知识库完善",
    description="端到端RAG流程、向量存储优化",
    priority=TaskPriority.MEDIUM,
    status=TaskStatus.PENDING
)
