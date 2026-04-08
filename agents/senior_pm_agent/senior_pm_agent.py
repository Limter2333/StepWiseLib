"""
Senior PM Agent - 高级项目管理智能体
=====================================

职责:
- 战略规划与路线图制定
- 跨团队协调与资源调度
- 风险预测与预防
- 决策记录与复盘
- Sprint规划与执行追踪

【学习要点】
1. 战略思维 - 从全局视角规划项目
2. 风险矩阵 - 识别、评估、缓解风险
3. 干系人管理 - 沟通策略与期望管理
4. 决策框架 - 结构化决策流程
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class StrategyType(Enum):
    """战略类型"""
    GROWTH = "growth"           # 增长战略
    STABILITY = "stability"     # 稳定战略
    TRANSFORMATION = "transformation"  # 转型战略
    INNOVATION = "innovation"   # 创新战略
    COST_REDUCTION = "cost_reduction"  # 成本优化战略


class RiskLevel(Enum):
    """风险等级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DecisionStatus(Enum):
    """决策状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    REVISED = "revised"


@dataclass
class Stakeholder:
    """干系人"""
    id: str
    name: str
    role: str
    influence: int  # 1-5 影响程度
    interest: int   # 1-5 关注程度
    engagement_level: str = "neutral"  # disengaged, neutral, supportive, leading
    communication_frequency: str = "weekly"  # daily, weekly, monthly, quarterly
    expectations: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)


@dataclass
class Sprint:
    """Sprint周期"""
    id: str
    name: str
    goal: str
    start_date: datetime
    end_date: datetime
    velocity: float = 0.0  # 故事点数
    capacity: int = 0  # 可用人力天数
    status: str = "planning"  # planning, active, completed, cancelled
    task_ids: List[str] = field(default_factory=list)
    completed_task_ids: List[str] = field(default_factory=list)
    blocked_task_ids: List[str] = field(default_factory=list)
    retrospective_notes: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionRecord:
    """决策记录"""
    id: str
    title: str
    description: str
    decision: str
    rationale: str
    alternatives: List[str] = field(default_factory=list)
    stakeholders_consulted: List[str] = field(default_factory=list)
    status: DecisionStatus = DecisionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    decided_at: Optional[datetime] = None
    decided_by: str = ""
    review_date: Optional[datetime] = None
    impact: str = ""  # high, medium, low
    outcome: str = ""  # 决策结果/复盘


@dataclass
class Risk:
    """风险记录"""
    id: str
    title: str
    description: str
    probability: float  # 0.0 - 1.0
    impact: RiskLevel
    category: str  # technical, resource, external, schedule, quality
    mitigation_plan: str
    contingency_plan: str
    owner: str
    status: str = "identified"  # identified, analyzing, mitigated, materialized, closed
    created_at: datetime = field(default_factory=datetime.now)
    identified_by: str = ""
    affected_sprints: List[str] = field(default_factory=list)


@dataclass
class ProjectStrategy:
    """项目战略"""
    id: str
    name: str
    type: StrategyType
    vision: str
    timeline: str = ""
    objectives: List[str] = field(default_factory=list)
    key_results: List[str] = field(default_factory=list)
    success_metrics: Dict[str, float] = field(default_factory=dict)
    resource_requirements: Dict[str, int] = field(default_factory=dict)


class SeniorPMAgent:
    """高级PM智能体

    【能力】
    - 战略规划与路线图制定
    - 多Sprint规划与追踪
    - 干系人分析与沟通策略
    - 风险预测与管理
    - 结构化决策流程
    - 项目复盘与持续改进
    """

    def __init__(self, project_name: str = "AI Multi-Agent System"):
        self.name = "Senior PM Agent"
        self.project_name = project_name

        # 核心数据存储
        self.strategies: Dict[str, ProjectStrategy] = {}
        self.sprints: Dict[str, Sprint] = {}
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.decisions: Dict[str, DecisionRecord] = {}
        self.risks: Dict[str, Risk] = {}

        # 计数器
        self.strategy_counter = 0
        self.sprint_counter = 0
        self.risk_counter = 0

        # 当前活动Sprint
        self.active_sprint_id: Optional[str] = None

    # ========== 战略管理 ==========

    def create_strategy(
        self,
        name: str,
        strategy_type: StrategyType,
        vision: str,
        objectives: Optional[List[str]] = None,
        timeline: str = ""
    ) -> ProjectStrategy:
        """创建项目战略"""
        self.strategy_counter += 1
        strategy = ProjectStrategy(
            id=f"strategy_{self.strategy_counter}",
            name=name,
            type=strategy_type,
            vision=vision,
            objectives=objectives or [],
            timeline=timeline
        )
        self.strategies[strategy.id] = strategy
        return strategy

    def get_strategy(self, strategy_id: str) -> Optional[ProjectStrategy]:
        """获取战略"""
        return self.strategies.get(strategy_id)

    def update_strategy_progress(
        self,
        strategy_id: str,
        key_result: str,
        achieved: bool = True
    ) -> bool:
        """更新战略进展"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return False

        if key_result in strategy.key_results and achieved:
            # 可以添加完成状态跟踪
            pass
        return True

    # ========== Sprint管理 ==========

    def create_sprint(
        self,
        name: str,
        goal: str,
        start_date: datetime,
        end_date: datetime,
        capacity: int = 10
    ) -> Sprint:
        """创建Sprint"""
        self.sprint_counter += 1
        sprint = Sprint(
            id=f"sprint_{self.sprint_counter}",
            name=name,
            goal=goal,
            start_date=start_date,
            end_date=end_date,
            capacity=capacity
        )
        self.sprints[sprint.id] = sprint
        return sprint

    def start_sprint(self, sprint_id: str) -> bool:
        """启动Sprint"""
        sprint = self.sprints.get(sprint_id)
        if not sprint or sprint.status != "planning":
            return False

        # 结束当前活动Sprint
        if self.active_sprint_id:
            current = self.sprints.get(self.active_sprint_id)
            if current and current.status == "active":
                self.complete_sprint(self.active_sprint_id)

        sprint.status = "active"
        self.active_sprint_id = sprint_id
        return True

    def complete_sprint(self, sprint_id: str) -> bool:
        """完成Sprint"""
        sprint = self.sprints.get(sprint_id)
        if not sprint or sprint.status != "active":
            return False

        sprint.status = "completed"

        # 计算velocity
        sprint.velocity = len(sprint.completed_task_ids)

        if self.active_sprint_id == sprint_id:
            self.active_sprint_id = None

        return True

    def add_task_to_sprint(self, sprint_id: str, task_id: str) -> bool:
        """添加任务到Sprint"""
        sprint = self.sprints.get(sprint_id)
        if not sprint or sprint.status == "completed":
            return False

        if task_id not in sprint.task_ids:
            sprint.task_ids.append(task_id)
        return True

    def complete_task_in_sprint(self, sprint_id: str, task_id: str) -> bool:
        """标记任务完成"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return False

        if task_id in sprint.task_ids and task_id not in sprint.completed_task_ids:
            sprint.completed_task_ids.append(task_id)
        return True

    def block_task_in_sprint(self, sprint_id: str, task_id: str) -> bool:
        """阻塞Sprint中的任务"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return False

        if task_id not in sprint.blocked_task_ids:
            sprint.blocked_task_ids.append(task_id)
        return True

    def get_sprint_metrics(self, sprint_id: str) -> Dict:
        """获取Sprint指标"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return {}

        total_tasks = len(sprint.task_ids)
        completed = len(sprint.completed_task_ids)
        blocked = len(sprint.blocked_task_ids)

        completion_rate = completed / total_tasks if total_tasks > 0 else 0
        blockage_rate = blocked / total_tasks if total_tasks > 0 else 0

        days_remaining = (sprint.end_date - datetime.now()).days
        on_track = blockage_rate < 0.2 and completion_rate >= (1 - blockage_rate * 2)

        return {
            "sprint_id": sprint_id,
            "name": sprint.name,
            "status": sprint.status,
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "blocked_tasks": blocked,
            "completion_rate": completion_rate,
            "blockage_rate": blockage_rate,
            "velocity": sprint.velocity,
            "days_remaining": days_remaining,
            "on_track": on_track,
            "goal": sprint.goal
        }

    # ========== 干系人管理 ==========

    def add_stakeholder(
        self,
        name: str,
        role: str,
        influence: int = 3,
        interest: int = 3
    ) -> Stakeholder:
        """添加干系人"""
        stakeholder_id = f"stakeholder_{len(self.stakeholders) + 1}"
        stakeholder = Stakeholder(
            id=stakeholder_id,
            name=name,
            role=role,
            influence=max(1, min(5, influence)),
            interest=max(1, min(5, interest))
        )
        self.stakeholders[stakeholder_id] = stakeholder
        return stakeholder

    def get_stakeholder_matrix(self) -> Dict[str, List[Stakeholder]]:
        """获取干系人矩阵（按影响力-关注度分组）"""
        matrix = {
            "keep_satisfied": [],  # 高影响力，低关注
            "manage_close": [],    # 高影响力，高关注
            "monitor": [],         # 低影响力，低关注
            "keep_informed": []   # 低影响力，高关注
        }

        for stakeholder in self.stakeholders.values():
            if stakeholder.influence >= 3 and stakeholder.interest >= 3:
                matrix["manage_close"].append(stakeholder)
            elif stakeholder.influence >= 3 and stakeholder.interest < 3:
                matrix["keep_satisfied"].append(stakeholder)
            elif stakeholder.influence < 3 and stakeholder.interest < 3:
                matrix["monitor"].append(stakeholder)
            else:
                matrix["keep_informed"].append(stakeholder)

        return matrix

    def get_communication_plan(self) -> Dict[str, Dict]:
        """生成沟通计划"""
        plan = {}
        for stakeholder in self.stakeholders.values():
            freq = stakeholder.communication_frequency
            if freq not in plan:
                plan[freq] = {"stakeholders": [], "topics": []}

            plan[freq]["stakeholders"].append(stakeholder.name)
            plan[freq]["topics"].extend(stakeholder.expectations[:2])

        return plan

    # ========== 风险管理 ==========

    def identify_risk(
        self,
        title: str,
        description: str,
        probability: float,
        impact: RiskLevel,
        category: str,
        mitigation_plan: str,
        owner: str
    ) -> Risk:
        """识别风险"""
        self.risk_counter += 1
        risk = Risk(
            id=f"risk_{self.risk_counter}",
            title=title,
            description=description,
            probability=probability,
            impact=impact,
            category=category,
            mitigation_plan=mitigation_plan,
            contingency_plan="",
            owner=owner
        )
        self.risks[risk.id] = risk
        return risk

    def get_risk_matrix(self) -> Dict[str, List[Risk]]:
        """获取风险矩阵"""
        matrix = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }

        for risk in self.risks.values():
            if risk.status in ["closed", "mitigated"]:
                continue

            exposure = risk.probability
            if risk.impact == RiskLevel.CRITICAL or exposure > 0.7:
                matrix["critical"].append(risk)
            elif risk.impact == RiskLevel.HIGH or exposure > 0.5:
                matrix["high"].append(risk)
            elif risk.impact == RiskLevel.MEDIUM or exposure > 0.3:
                matrix["medium"].append(risk)
            else:
                matrix["low"].append(risk)

        return matrix

    def get_top_risks(self, limit: int = 5) -> List[Risk]:
        """获取TOP风险（按风险值排序）"""
        risk_values = []
        for risk in self.risks.values():
            if risk.status in ["closed", "mitigated"]:
                continue

            impact_score = {
                RiskLevel.CRITICAL: 4,
                RiskLevel.HIGH: 3,
                RiskLevel.MEDIUM: 2,
                RiskLevel.LOW: 1
            }.get(risk.impact, 2)

            risk_value = risk.probability * impact_score
            risk_values.append((risk, risk_value))

        risk_values.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in risk_values[:limit]]

    # ========== 决策管理 ==========

    def create_decision(
        self,
        title: str,
        description: str,
        decision: str,
        rationale: str,
        alternatives: Optional[List[str]] = None,
        stakeholders_consulted: Optional[List[str]] = None,
        impact: str = "medium"
    ) -> DecisionRecord:
        """创建决策记录"""
        decision_id = f"decision_{len(self.decisions) + 1}"
        record = DecisionRecord(
            id=decision_id,
            title=title,
            description=description,
            decision=decision,
            rationale=rationale,
            alternatives=alternatives or [],
            stakeholders_consulted=stakeholders_consulted or [],
            impact=impact
        )
        self.decisions[decision_id] = record
        return record

    def approve_decision(
        self,
        decision_id: str,
        decided_by: str
    ) -> bool:
        """批准决策"""
        record = self.decisions.get(decision_id)
        if not record:
            return False

        record.status = DecisionStatus.APPROVED
        record.decided_at = datetime.now()
        record.decided_by = decided_by
        return True

    def get_pending_decisions(self) -> List[DecisionRecord]:
        """获取待决策列表"""
        return [
            d for d in self.decisions.values()
            if d.status == DecisionStatus.PENDING
        ]

    def add_retrospective(
        self,
        sprint_id: str,
        notes: str,
        improvement_actions: Optional[List[str]] = None
    ) -> bool:
        """添加Sprint回顾"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return False

        sprint.retrospective_notes = notes
        if improvement_actions:
            sprint.metrics["improvement_actions"] = improvement_actions
        return True

    # ========== 报告生成 ==========

    def generate_executive_report(self) -> str:
        """生成执行报告"""
        active_sprints = [s for s in self.sprints.values() if s.status == "active"]
        completed_sprints = [s for s in self.sprints.values() if s.status == "completed"]

        top_risks = self.get_top_risks()
        pending_decisions = self.get_pending_decisions()
        stakeholder_matrix = self.get_stakeholder_matrix()

        report = f"""# {self.project_name} - Executive Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Status

| Metric | Value |
|--------|-------|
| Total Strategies | {len(self.strategies)} |
| Active Sprints | {len(active_sprints)} |
| Completed Sprints | {len(completed_sprints)} |
| Identified Risks | {len(self.risks)} |
| Pending Decisions | {len(pending_decisions)} |
| Stakeholders | {len(self.stakeholders)} |

## Active Sprints

"""

        for sprint in active_sprints:
            metrics = self.get_sprint_metrics(sprint.id)
            report += f"""### {sprint.name}

- **Goal**: {sprint.goal}
- **Status**: {sprint.status}
- **Completion Rate**: {metrics['completion_rate']*100:.1f}%
- **On Track**: {'Yes' if metrics['on_track'] else 'No'}
- **Days Remaining**: {metrics['days_remaining']}

"""

        report += """## Top Risks

"""
        for i, risk in enumerate(top_risks, 1):
            report += f"""{i}. [{risk.impact.value.upper()}] {risk.title}
   - Probability: {risk.probability*100:.0f}%
   - Mitigation: {risk.mitigation_plan[:100]}...

"""

        report += """## Stakeholder Summary

| Category | Count |
|----------|-------|
"""
        for category, stakeholders in stakeholder_matrix.items():
            report += f"| {category} | {len(stakeholders)} |\n"

        report += """
## Pending Decisions

"""
        for decision in pending_decisions:
            report += f"""- **{decision.title}**
  - Created: {decision.created_at.strftime('%Y-%m-%d')}
  - Impact: {decision.impact}

"""

        return report

    def generate_executive_report_html(self) -> str:
        """生成HTML格式的执行报告"""
        active_sprints = [s for s in self.sprints.values() if s.status == "active"]
        completed_sprints = [s for s in self.sprints.values() if s.status == "completed"]
        top_risks = self.get_top_risks()
        pending_decisions = self.get_pending_decisions()
        stakeholder_matrix = self.get_stakeholder_matrix()

        # Calculate completion rates
        total_sprints = len(active_sprints) + len(completed_sprints)
        completion_rate = len(completed_sprints) / total_sprints * 100 if total_sprints > 0 else 0

        # Risk level colors
        risk_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745"
        }

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.project_name} - Executive Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .timestamp {{ opacity: 0.8; font-size: 14px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #666; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        .card.strategies .value {{ color: #667eea; }}
        .card.sprints .value {{ color: #28a745; }}
        .card.risks .value {{ color: #dc3545; }}
        .card.decisions .value {{ color: #ffc107; }}
        .card.stakeholders .value {{ color: #17a2b8; }}
        .section {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; font-size: 18px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #f5f5f5; }}
        .sprint-card {{ background: #f8f9fa; border-radius: 6px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #667eea; }}
        .sprint-card.completed {{ border-left-color: #28a745; }}
        .sprint-card .title {{ font-weight: bold; color: #333; margin-bottom: 8px; }}
        .sprint-card .meta {{ display: flex; gap: 15px; font-size: 13px; color: #666; }}
        .sprint-card .progress-bar {{ height: 6px; background: #e9ecef; border-radius: 3px; margin-top: 10px; overflow: hidden; }}
        .sprint-card .progress-fill {{ height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 3px; }}
        .risk-item {{ display: flex; align-items: flex-start; gap: 10px; padding: 10px; border-radius: 6px; margin-bottom: 8px; }}
        .risk-badge {{ padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; color: white; text-transform: uppercase; }}
        .risk-item .description {{ flex: 1; font-size: 14px; color: #333; }}
        .stakeholder-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }}
        .stakeholder-chip {{ padding: 8px 12px; border-radius: 20px; font-size: 13px; display: inline-flex; align-items: center; gap: 6px; }}
        .chip-manage_close {{ background: #e7f3ff; color: #007bff; }}
        .chip-keep_satisfied {{ background: #fff3e0; color: #ff9800; }}
        .chip-keep_informed {{ background: #e8f5e9; color: #4caf50; }}
        .chip-monitor {{ background: #f5f5f5; color: #9e9e9e; }}
        .decision-item {{ padding: 12px; background: #f8f9fa; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #ffc107; }}
        .decision-item .title {{ font-weight: bold; color: #333; margin-bottom: 4px; }}
        .decision-item .meta {{ font-size: 12px; color: #666; }}
        .empty-state {{ text-align: center; padding: 30px; color: #999; }}
        .completion-ring {{ position: relative; width: 100px; height: 100px; margin: 0 auto; }}
        .completion-ring svg {{ transform: rotate(-90deg); }}
        .completion-ring circle {{ fill: none; stroke-width: 8; }}
        .completion-ring .bg {{ stroke: #e9ecef; }}
        .completion-ring .fg {{ stroke: #667eea; stroke-linecap: round; transition: stroke-dashoffset 0.5s; }}
        .completion-ring .text {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 20px; font-weight: bold; color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.project_name}</h1>
            <div class="timestamp">Executive Report • Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>

        <div class="grid">
            <div class="card strategies">
                <h3>Strategies</h3>
                <div class="value">{len(self.strategies)}</div>
            </div>
            <div class="card sprints">
                <h3>Completed Sprints</h3>
                <div class="value">{len(completed_sprints)} / {total_sprints}</div>
            </div>
            <div class="card risks">
                <h3>Active Risks</h3>
                <div class="value">{len(top_risks)}</div>
            </div>
            <div class="card decisions">
                <h3>Pending Decisions</h3>
                <div class="value">{len(pending_decisions)}</div>
            </div>
            <div class="card stakeholders">
                <h3>Stakeholders</h3>
                <div class="value">{len(self.stakeholders)}</div>
            </div>
        </div>
"""

        # Active Sprints Section
        html += '<div class="section"><h2>Active Sprints</h2>'
        if active_sprints:
            for sprint in active_sprints:
                metrics = self.get_sprint_metrics(sprint.id)
                progress_pct = metrics['completion_rate'] * 100
                on_track = "Yes" if metrics['on_track'] else "No"
                on_track_color = "#28a745" if metrics['on_track'] else "#dc3545"
                html += f"""
                <div class="sprint-card">
                    <div class="title">{sprint.name}</div>
                    <div class="meta">
                        <span>Goal: {sprint.goal[:50]}...</span>
                    </div>
                    <div class="meta" style="margin-top: 8px;">
                        <span style="color: {on_track_color};">On Track: {on_track}</span>
                        <span>Days Left: {metrics['days_remaining']}</span>
                        <span>Completion: {progress_pct:.1f}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress_pct}%;"></div>
                    </div>
                </div>"""
        else:
            html += '<div class="empty-state">No active sprints</div>'
        html += '</div>'

        # Top Risks Section
        html += '<div class="section"><h2>Top Risks</h2>'
        if top_risks:
            for risk in top_risks[:5]:
                color = risk_colors.get(risk.impact.value, "#6c757d")
                html += f"""
                <div class="risk-item">
                    <span class="risk-badge" style="background: {color};">{risk.impact.value.upper()}</span>
                    <div class="description">
                        <div style="font-weight: bold;">{risk.title}</div>
                        <div style="font-size: 12px; color: #666; margin-top: 4px;">Probability: {risk.probability*100:.0f}% • {risk.category}</div>
                    </div>
                </div>"""
        else:
            html += '<div class="empty-state">No active risks identified</div>'
        html += '</div>'

        # Stakeholder Matrix Section
        html += '<div class="section"><h2>Stakeholder Matrix</h2><div class="stakeholder-grid">'
        for category, stakeholders in stakeholder_matrix.items():
            if stakeholders:
                chip_class = f"chip-{category}"
                for sh in stakeholders:
                    html += f'<span class="stakeholder-chip {chip_class}">● {sh.name} ({sh.role})</span>'
        html += '</div></div>'

        # Pending Decisions Section
        html += '<div class="section"><h2>Pending Decisions</h2>'
        if pending_decisions:
            for decision in pending_decisions:
                html += f"""
                <div class="decision-item">
                    <div class="title">{decision.title}</div>
                    <div class="meta">Impact: {decision.impact} • Created: {decision.created_at.strftime('%Y-%m-%d')}</div>
                </div>"""
        else:
            html += '<div class="empty-state">No pending decisions</div>'
        html += '</div>'

        html += """
    </div>
</body>
</html>"""
        return html

    def generate_sprint_burndown(
        self,
        sprint_id: str
    ) -> Dict[str, List[float]]:
        """生成Sprint燃尽图数据"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return {}

        total_tasks = len(sprint.task_ids)
        if total_tasks == 0:
            return {"days": [], "remaining": [], "ideal": []}

        days = []
        remaining = []
        ideal = []

        start = sprint.start_date
        end = sprint.end_date
        total_days = (end - start).days

        for i in range(total_days + 1):
            day_date = start + timedelta(days=i)
            days.append(day_date.strftime('%m-%d'))

            completed = len([t for t in sprint.completed_task_ids
                          if sprint.task_ids.index(t) <= i])
            remaining.append(total_tasks - completed)
            ideal.append(total_tasks - (total_tasks * i / total_days))

        return {"days": days, "remaining": remaining, "ideal": ideal}

    def get_velocity_trend(self) -> Dict[str, List[float]]:
        """获取团队速度趋势"""
        completed = [s for s in self.sprints.values() if s.status == "completed"]

        if len(completed) < 2:
            return {"sprints": [], "velocity": []}

        recent = sorted(completed, key=lambda s: s.end_date)[-5:]

        return {
            "sprints": [s.name for s in recent],
            "velocity": [s.velocity for s in recent]
        }

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "project": self.project_name,
            "features": [
                "strategy_planning",
                "sprint_management",
                "stakeholder_management",
                "risk_management",
                "decision_tracking",
                "executive_reporting",
                "velocity_tracking",
                "burndown_analysis"
            ]
        }


# 全局实例
_senior_pm_instance: Optional[SeniorPMAgent] = None


def get_senior_pm() -> SeniorPMAgent:
    """获取全局Senior PM实例"""
    global _senior_pm_instance
    if _senior_pm_instance is None:
        _senior_pm_instance = SeniorPMAgent()
    return _senior_pm_instance


# 初始化全局实例
senior_pm_agent = get_senior_pm()
