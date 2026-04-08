"""
Ralph Loop - User Stories Module
================================

User Story 格式:
{
  "id": "STORY-001",
  "title": "Story title",
  "description": "As a... I want... So that...",
  "acceptance_criteria": [
    {"criterion": "Given... When... Then...", "status": "pass|fail|pending", "evidence": "..."}
  ],
  "priority": "P0|P1|P2",
  "status": "todo|in_progress|done",
  "agent": "claude|dev|test|...",
  "created_at": "ISO date",
  "updated_at": "ISO date"
}
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any


class UserStory:
    """User Story"""

    def __init__(
        self,
        story_id: str,
        title: str,
        description: str,
        priority: str = "P1",
        agent: str = "claude"
    ):
        self.id = story_id
        self.title = title
        self.description = description
        self.priority = priority
        self.agent = agent
        self.acceptance_criteria: List[Dict] = []
        self.status = "todo"
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def add_criterion(self, criterion: str) -> None:
        """添加验收标准"""
        self.acceptance_criteria.append({
            "criterion": criterion,
            "status": "pending",
            "evidence": ""
        })

    def mark_criterion(self, index: int, status: str, evidence: str = "") -> None:
        """标记验收标准状态"""
        if 0 <= index < len(self.acceptance_criteria):
            self.acceptance_criteria[index]["status"] = status
            self.acceptance_criteria[index]["evidence"] = evidence
            self.updated_at = datetime.now().isoformat()

    def all_criteria_passed(self) -> bool:
        """所有标准都通过"""
        return all(c["status"] == "pass" for c in self.acceptance_criteria)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "priority": self.priority,
            "agent": self.agent,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "UserStory":
        story = cls(
            story_id=data["id"],
            title=data["title"],
            description=data["description"],
            priority=data.get("priority", "P1"),
            agent=data.get("agent", "claude")
        )
        story.acceptance_criteria = data.get("acceptance_criteria", [])
        story.status = data.get("status", "todo")
        story.created_at = data.get("created_at", datetime.now().isoformat())
        story.updated_at = data.get("updated_at", datetime.now().isoformat())
        return story


class StoryStore:
    """Story 存储"""

    def __init__(self, stories_dir: str = ".ralph/stories"):
        self.stories_dir = Path(stories_dir)
        self.stories_dir.mkdir(parents=True, exist_ok=True)

    def save(self, story: UserStory) -> None:
        """保存 Story"""
        filepath = self.stories_dir / f"{story.id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(story.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self, story_id: str) -> Optional[UserStory]:
        """加载 Story"""
        filepath = self.stories_dir / f"{story_id}.json"
        if not filepath.exists():
            return None
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        return UserStory.from_dict(data)

    def list_all(self) -> List[UserStory]:
        """列出所有 Story"""
        stories = []
        for filepath in self.stories_dir.glob("*.json"):
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            stories.append(UserStory.from_dict(data))
        return sorted(stories, key=lambda s: (s.priority, s.id))

    def list_by_status(self, status: str) -> List[UserStory]:
        """按状态筛选"""
        return [s for s in self.list_all() if s.status == status]

    def list_by_priority(self, priority: str) -> List[UserStory]:
        """按优先级筛选"""
        return [s for s in self.list_all() if s.priority == priority]

    def get_next_todo(self) -> Optional[UserStory]:
        """获取下一个待办 Story"""
        todos = self.list_by_status("todo")
        if not todos:
            return None
        # 按优先级排序
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        return sorted(todos, key=lambda s: priority_order.get(s.priority, 3))[0]


class RalphLoop:
    """Ralph Loop 主控制器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.stories_dir = self.project_root / ".ralph" / "stories"
        self.logs_dir = self.project_root / ".ralph" / "logs"
        self.store = StoryStore(str(self.stories_dir))

    def create_story(
        self,
        title: str,
        description: str,
        criteria: List[str],
        priority: str = "P1",
        agent: str = "claude"
    ) -> UserStory:
        """创建新 Story"""
        # 生成 ID
        existing = self.store.list_all()
        next_num = len(existing) + 1
        story_id = f"STORY-{next_num:03d}"

        story = UserStory(
            story_id=story_id,
            title=title,
            description=description,
            priority=priority,
            agent=agent
        )

        for c in criteria:
            story.add_criterion(c)

        self.store.save(story)
        self._log(f"Created {story_id}: {title}")
        return story

    def start_story(self, story_id: str) -> UserStory:
        """开始处理 Story"""
        story = self.store.load(story_id)
        if story:
            story.status = "in_progress"
            self.store.save(story)
            self._log(f"Started {story_id}")
        return story

    def complete_story(self, story_id: str) -> UserStory:
        """标记 Story 完成"""
        story = self.store.load(story_id)
        if story:
            story.status = "done"
            self.store.save(story)
            self._log(f"Completed {story_id}")
        return story

    def verify_criterion(
        self,
        story_id: str,
        criterion_index: int,
        passed: bool,
        evidence: str = ""
    ) -> UserStory:
        """验证验收标准"""
        story = self.store.load(story_id)
        if story:
            status = "pass" if passed else "fail"
            story.mark_criterion(criterion_index, status, evidence)
            if story.all_criteria_passed():
                story.status = "done"
            self.store.save(story)
            self._log(f"{story_id} criterion {criterion_index}: {status}")
        return story

    def get_status(self) -> Dict[str, Any]:
        """获取整体状态"""
        stories = self.store.list_all()
        return {
            "total": len(stories),
            "todo": len([s for s in stories if s.status == "todo"]),
            "in_progress": len([s for s in stories if s.status == "in_progress"]),
            "done": len([s for s in stories if s.status == "done"]),
            "completion_rate": len([s for s in stories if s.status == "done"]) / max(len(stories), 1)
        }

    def _log(self, message: str) -> None:
        """写入日志"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.logs_dir / "ralph.log"
        timestamp = datetime.now().isoformat()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def generate_report(self) -> str:
        """生成状态报告"""
        status = self.get_status()
        stories = self.store.list_all()

        lines = [
            "=" * 60,
            "Ralph Loop Status Report",
            "=" * 60,
            f"Total Stories: {status['total']}",
            f"  Todo: {status['todo']}",
            f"  In Progress: {status['in_progress']}",
            f"  Done: {status['done']}",
            f"Completion Rate: {status['completion_rate']:.1%}",
            "",
            "Stories:",
            "-" * 60
        ]

        for s in stories:
            lines.append(f"[{s.status.upper():11}] {s.id} ({s.priority}) {s.title}")
            for i, c in enumerate(s.acceptance_criteria):
                lines.append(f"  {i+1}. [{c['status']:7}] {c['criterion']}")

        lines.append("=" * 60)
        return "\n".join(lines)
