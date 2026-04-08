"""
Product Manager Agent - 产品经理智能体
=====================================

职责:
- 产品路线图规划
- 用户故事创建
- 需求分析
- 优先级排序
- 里程碑设定
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Priority(Enum):
    """优先级"""
    P0_CRITICAL = "P0"  # 必须完成
    P1_HIGH = "P1"      # 应该完成
    P2_MEDIUM = "P2"      # 可以完成
    P3_LOW = "P3"        # 暂不完成


class EpicStatus(Enum):
    """Epic状态"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class UserStory:
    """用户故事"""
    id: str
    as_a: str      # 角色
    i_want: str    # 需求
    so_that: str   # 目的
    priority: Priority
    acceptance_criteria: List[str] = field(default_factory=list)
    story_points: int = 0
    labels: List[str] = field(default_factory=list)


@dataclass
class Epic:
    """Epic"""
    id: str
    title: str
    description: str
    user_stories: List[UserStory] = field(default_factory=list)
    status: EpicStatus = EpicStatus.ACTIVE
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class ProductResult:
    """产品规划结果"""
    roadmap: Dict = field(default_factory=dict)
    user_stories: List[UserStory] = field(default_factory=list)
    epics: List[Epic] = field(default_factory=list)
    milestones: List[Dict] = field(default_factory=list)
    requirements: str = ""
    quality_score: float = 0.0


class ProductManager:
    """产品经理智能体

    【能力】
    - 创建用户故事
    - 规划产品路线图
    - 优先级排序
    - 需求分析
    - 里程碑规划
    """

    def __init__(self):
        self.name = "Product Manager"
        self.specialty = ["产品规划", "用户故事", "敏捷", "路线图"]
        self.epics: List[Epic] = []
        self.user_stories: List[UserStory] = []

    def create_user_story(
        self,
        role: str,
        requirement: str,
        goal: str,
        priority: str = "P1"
    ) -> UserStory:
        """创建用户故事

        Args:
            role: 用户角色 (as a...)
            requirement: 需求 (I want...)
            goal: 目标 (so that...)
            priority: 优先级

        Returns:
            UserStory: 用户故事
        """
        story = UserStory(
            id=f"US-{len(self.user_stories) + 1:03d}",
            as_a=role,
            i_want=requirement,
            so_that=goal,
            priority=Priority[priority.replace("P", "P_").upper()],
            acceptance_criteria=self._generate_acceptance_criteria(requirement)
        )

        self.user_stories.append(story)
        return story

    def create_epic(
        self,
        title: str,
        description: str,
        stories: Optional[List[UserStory]] = None
    ) -> Epic:
        """创建Epic"""
        epic = Epic(
            id=f"EPIC-{len(self.epics) + 1:03d}",
            title=title,
            description=description,
            user_stories=stories or []
        )

        self.epics.append(epic)
        return epic

    def create_roadmap(
        self,
        timeline_months: int = 12,
        quarters: Optional[List[str]] = None
    ) -> Dict:
        """创建产品路线图

        Args:
            timeline_months: 时间线（月）
            quarters: 季度划分

        Returns:
            Dict: 路线图
        """
        quarters_list = quarters or ["Q1", "Q2", "Q3", "Q4"]

        roadmap = {
            "timeline": {
                "start": datetime.now().strftime("%Y-%m-%d"),
                "end": f"{(datetime.now().year + timeline_months // 12)}-{datetime.now().strftime('%m-%d')}",
                "quarters": quarters_list
            },
            "phases": []
        }

        # 按优先级分组
        p0_stories = [s for s in self.user_stories if s.priority == Priority.P0_CRITICAL]
        p1_stories = [s for s in self.user_stories if s.priority == Priority.P1_HIGH]

        # 创建阶段
        roadmap["phases"] = [
            {
                "name": "Foundation",
                "quarter": quarters_list[0] if len(quarters_list) > 0 else "Q1",
                "description": "Core infrastructure and P0 features",
                "stories": [s.id for s in p0_stories[:5]]
            },
            {
                "name": "Growth",
                "quarter": quarters_list[1] if len(quarters_list) > 1 else "Q2",
                "description": "P1 features and user experience improvements",
                "stories": [s.id for s in p1_stories[:5]]
            },
            {
                "name": "Scale",
                "quarter": quarters_list[2] if len(quarters_list) > 2 else "Q3",
                "description": "Advanced features and optimization",
                "stories": []
            }
        ]

        return roadmap

    def prioritize_stories(
        self,
        stories: List[UserStory],
        criteria: Optional[Dict] = None
    ) -> List[UserStory]:
        """故事优先级排序

        按以下标准排序：
        1. 业务价值
        2. 技术复杂度
        3. 用户影响
        """
        # 简单排序：P0 > P1 > P2 > P3
        priority_order = {
            Priority.P0_CRITICAL: 0,
            Priority.P1_HIGH: 1,
            Priority.P2_MEDIUM: 2,
            Priority.P3_LOW: 3
        }

        return sorted(stories, key=lambda s: priority_order.get(s.priority, 99))

    def create_milestones(
        self,
        epic: Epic,
        milestone_names: List[str]
    ) -> List[Dict]:
        """创建里程碑"""
        milestones = []

        for i, name in enumerate(milestone_names):
            milestone = {
                "id": f"MS-{len(self.user_stories) + 1:03d}-{i + 1}",
                "name": name,
                "epic_id": epic.id,
                "target_date": None,  # 待设置
                "status": "planned",
                "completion_criteria": [f"Complete {len(epic.user_stories) // len(milestone_names) or 1} stories"]
            }
            milestones.append(milestone)

        return milestones

    def analyze_requirements(
        self,
        raw_requirements: str
    ) -> Dict:
        """需求分析

        Args:
            raw_requirements: 原始需求描述

        Returns:
            Dict: 分析后的需求结构
        """
        # 简单的需求解析
        requirements_list = [
            r.strip() for r in raw_requirements.split("\n")
            if r.strip() and not r.strip().startswith("#")
        ]

        analysis = {
            "functional_requirements": [],
            "non_functional_requirements": [],
            "assumptions": [],
            "constraints": [],
            "risks": []
        }

        for req in requirements_list:
            lower_req = req.lower()
            if any(kw in lower_req for kw in ["must", "should", "shall"]):
                analysis["functional_requirements"].append(req)
            elif any(kw in lower_req for kw in ["performance", "security", "scalability"]):
                analysis["non_functional_requirements"].append(req)
            elif lower_req.startswith("assume"):
                analysis["assumptions"].append(req)
            elif lower_req.startswith("limit"):
                analysis["constraints"].append(req)

        return analysis

    def _generate_acceptance_criteria(self, requirement: str) -> List[str]:
        """生成验收标准"""
        criteria = [
            f"Given a user, When they access {requirement}, Then they should be able to complete the action"
        ]

        # 添加常见验收点
        common_criteria = [
            "System responds within 2 seconds",
            "User receives confirmation of action",
            "Error messages are clear and actionable"
        ]

        return criteria + common_criteria[:2]

    def get_product_metrics(self) -> Dict:
        """获取产品指标"""
        return {
            "total_stories": len(self.user_stories),
            "p0_count": sum(1 for s in self.user_stories if s.priority == Priority.P0_CRITICAL),
            "p1_count": sum(1 for s in self.user_stories if s.priority == Priority.P1_HIGH),
            "total_epics": len(self.epics),
            "estimated_velocity": sum(s.story_points for s in self.user_stories),
        }

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "priorities": [p.value for p in Priority],
            "deliverables": ["user_stories", "epics", "roadmap", "milestones", "requirements"]
        }


# 全局实例
product_manager = ProductManager()
