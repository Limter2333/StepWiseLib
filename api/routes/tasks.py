"""
Task Queue API 路由
==================

异步任务队列管理接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import asyncio


router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskDefinition(BaseModel):
    """任务定义"""
    task_id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 - 1.0


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    name: str
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    agent: str  # dev, doc, test, rag, pm, conversation


class TaskUpdateRequest(BaseModel):
    """更新任务请求"""
    status: Optional[TaskStatus] = None
    progress: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskQueue:
    """任务队列管理器"""

    def __init__(self):
        self.tasks: Dict[str, TaskDefinition] = {}
        self._lock = asyncio.Lock()

    async def create_task(
        self,
        name: str,
        description: str,
        priority: TaskPriority,
        agent: str
    ) -> TaskDefinition:
        """创建任务"""
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        task = TaskDefinition(
            task_id=task_id,
            name=name,
            description=description,
            priority=priority,
            created_at=datetime.now(),
            status=TaskStatus.PENDING
        )

        async with self._lock:
            self.tasks[task_id] = task

        return task

    async def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """获取任务"""
        return self.tasks.get(task_id)

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[TaskDefinition]:
        """列出任务"""
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # 按创建时间倒序
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    async def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[float] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> Optional[TaskDefinition]:
        """更新任务"""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]

        if status:
            task.status = status
            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.now()
            elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                task.completed_at = datetime.now()

        if progress is not None:
            task.progress = max(0.0, min(1.0, progress))

        if result is not None:
            task.result = result

        if error:
            task.error = error

        return task

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    async def retry_task(self, task_id: str) -> Optional[TaskDefinition]:
        """重试失败的任务（创建新任务复制原任务参数）"""
        original = self.tasks.get(task_id)
        if not original:
            return None

        # 只能重试失败的任务
        if original.status != TaskStatus.FAILED:
            return None

        # 创建新任务，继承原任务的参数
        new_task = await self.create_task(
            name=f"{original.name} (重试)",
            description=original.description,
            priority=original.priority,
            agent=""  # agent信息不继承，需要重新指定
        )

        # 复制result作为新任务的metadata
        new_task.result = {"retry_from": task_id, "original_error": original.error}

        return new_task

    async def get_stats(self) -> Dict:
        """获取队列统计"""
        total = len(self.tasks)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)

        return {
            "total": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed
        }


# 全局任务队列实例
task_queue = TaskQueue()


# ========== API端点 ==========

@router.post("/", response_model=TaskDefinition)
async def create_task(request: TaskCreateRequest):
    """创建新任务

    Args:
        request: 任务创建请求

    Returns:
        创建的任务
    """
    task = await task_queue.create_task(
        name=request.name,
        description=request.description,
        priority=request.priority,
        agent=request.agent
    )
    return task


@router.get("/{task_id}", response_model=TaskDefinition)
async def get_task(task_id: str):
    """获取任务详情

    Args:
        task_id: 任务ID

    Returns:
        任务详情
    """
    task = await task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/", response_model=List[TaskDefinition])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    limit: int = 50
):
    """列出任务

    Args:
        status: 可选的状态过滤
        limit: 返回数量限制

    Returns:
        任务列表
    """
    return await task_queue.list_tasks(status=status, limit=limit)


@router.patch("/{task_id}", response_model=TaskDefinition)
async def update_task(
    task_id: str,
    request: TaskUpdateRequest
):
    """更新任务状态

    Args:
        task_id: 任务ID
        request: 更新请求

    Returns:
        更新后的任务
    """
    task = await task_queue.update_task(
        task_id=task_id,
        status=request.status,
        progress=request.progress,
        result=request.result,
        error=request.error
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """删除任务

    Args:
        task_id: 任务ID

    Returns:
        成功状态
    """
    success = await task_queue.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "task_id": task_id}


@router.post("/{task_id}/retry", response_model=TaskDefinition)
async def retry_task(task_id: str):
    """重试失败的任务

    创建一个新任务，继承原任务的参数，原任务必须状态为FAILED

    Args:
        task_id: 原任务ID

    Returns:
        新创建的重试任务
    """
    task = await task_queue.retry_task(task_id)
    if not task:
        # 检查任务是否存在
        existing = await task_queue.get_task(task_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")
        else:
            # 任务存在但不是FAILED状态
            raise HTTPException(
                status_code=400,
                detail=f"Only failed tasks can be retried. Current status: {existing.status.value}"
            )
    return task


@router.get("/stats/summary")
async def get_task_stats():
    """获取任务队列统计

    Returns:
        队列统计信息
    """
    return await task_queue.get_stats()
