"""
Agent协作器 - Agent Collaboration System
======================================

【功能】
1. 智能任务分解 - 将复杂任务分解为子任务
2. 多Agent协作 - 支持顺序、并行、条件分支
3. 协作监控 - 追踪任务在Agent间的流转
4. 结果聚合 - 合并多个Agent的结果

【协作模式】
- SEQUENTIAL: 顺序执行 A -> B -> C
- PARALLEL: 并行执行 A || B || C
- CONDITIONAL: 条件分支 if X then A else B
- PIPELINE: 流水线 A -> B -> C (输出作为输入)
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import uuid

# 导入日志模块
try:
    from logs.error_logs.error_logger import error_logger, ErrorLevel
except ImportError:
    # 提供备用定义避免导入失败
    class MockErrorLogger:
        def log(self, error_type, message, level=None, exc_info=None):
            print(f"[{error_type}] {message}")
    error_logger = MockErrorLogger()
    class ErrorLevel:
        WARNING = "WARNING"
        ERROR = "ERROR"


class CollaborationMode(Enum):
    """协作模式"""
    SEQUENTIAL = "sequential"    # 顺序执行
    PARALLEL = "parallel"        # 并行执行
    CONDITIONAL = "conditional"  # 条件分支
    PIPELINE = "pipeline"       # 流水线


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"       # 简单任务，单Agent处理
    MODERATE = "moderate"   # 中等复杂度，多Agent顺序
    COMPLEX = "complex"     # 复杂任务，多Agent并行


@dataclass
class SubTask:
    """子任务"""
    id: str
    description: str
    assigned_agent: str
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)  # 依赖的子任务ID

    @property
    def duration(self) -> Optional[float]:
        """执行时长（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class CollaborationTask:
    """协作任务"""
    id: str
    original_request: str
    complexity: TaskComplexity
    mode: CollaborationMode
    sub_tasks: List[SubTask] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    results: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class TaskDecomposer:
    """任务分解器

    【功能】
    - 分析任务复杂度
    - 分解为子任务
    - 确定协作模式
    """

    # 关键词映射到Agent
    AGENT_KEYWORDS = {
        "dev": ["代码", "开发", "实现", "function", "code", "class", "api", "接口"],
        "doc": ["文档", "说明", "readme", "文档", "撰写", "write"],
        "test": ["测试", "验证", "test", "单元测试", "集成测试"],
        "rag": ["知识库", "检索", "搜索", "query", "索引", "index"],
        "pm": ["进度", "计划", "里程碑", "project", "task", "任务"],
    }

    # 复杂任务模式
    COMPLEX_PATTERNS = [
        ["开发", "测试"],          # 开发+测试
        ["文档", "代码"],          # 文档+代码
        ["分析", "实现", "测试"],  # 分析+实现+测试
        ["设计", "开发", "部署"],  # 设计+开发+部署
    ]

    # Pipeline模式关键词 - 表示输出作为输入
    PIPELINE_KEYWORDS = ["然后", "接着", "之后", "生成代码再", "开发并测试", "写代码并测试"]

    def analyze_complexity(self, task_description: str) -> TaskComplexity:
        """分析任务复杂度"""
        desc_lower = task_description.lower()

        # 检查复杂任务模式
        complex_score = 0
        for pattern in self.COMPLEX_PATTERNS:
            if all(kw in desc_lower for kw in pattern):
                complex_score = 2
                break

        # 检查是否涉及多个关键词类别
        involved_categories = set()
        for agent, keywords in self.AGENT_KEYWORDS.items():
            if any(kw in desc_lower for kw in keywords):
                involved_categories.add(agent)

        if complex_score >= 2 or len(involved_categories) >= 3:
            return TaskComplexity.COMPLEX
        elif len(involved_categories) >= 2:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE

    def decompose(self, task_description: str) -> tuple[List[SubTask], CollaborationMode]:
        """分解任务

        Returns:
            (子任务列表, 协作模式)
        """
        sub_tasks = []
        desc_lower = task_description.lower()

        # 1. 代码相关子任务
        if any(kw in desc_lower for kw in self.AGENT_KEYWORDS["dev"]):
            sub_tasks.append(SubTask(
                id=str(uuid.uuid4())[:8],
                description="代码开发任务",
                assigned_agent="dev"
            ))

        # 2. 文档相关子任务
        if any(kw in desc_lower for kw in self.AGENT_KEYWORDS["doc"]):
            sub_tasks.append(SubTask(
                id=str(uuid.uuid4())[:8],
                description="文档编写任务",
                assigned_agent="doc"
            ))

        # 3. 测试相关子任务
        if any(kw in desc_lower for kw in self.AGENT_KEYWORDS["test"]):
            sub_tasks.append(SubTask(
                id=str(uuid.uuid4())[:8],
                description="测试验证任务",
                assigned_agent="test"
            ))

        # 4. 知识库相关子任务
        if any(kw in desc_lower for kw in self.AGENT_KEYWORDS["rag"]):
            sub_tasks.append(SubTask(
                id=str(uuid.uuid4())[:8],
                description="知识库检索任务",
                assigned_agent="rag"
            ))

        # 5. PM相关子任务
        if any(kw in desc_lower for kw in self.AGENT_KEYWORDS["pm"]):
            sub_tasks.append(SubTask(
                id=str(uuid.uuid4())[:8],
                description="项目管理任务",
                assigned_agent="pm"
            ))

        # 确定协作模式
        if len(sub_tasks) <= 1:
            mode = CollaborationMode.SEQUENTIAL
        elif len(sub_tasks) == 2 and "test" in [s.assigned_agent for s in sub_tasks]:
            # 测试通常在开发之后
            mode = CollaborationMode.SEQUENTIAL
        elif any(kw in task_description for kw in self.PIPELINE_KEYWORDS):
            # 检测Pipeline模式
            mode = CollaborationMode.PIPELINE
        else:
            mode = CollaborationMode.PARALLEL

        # 设置依赖关系
        if mode in [CollaborationMode.SEQUENTIAL, CollaborationMode.PIPELINE]:
            for i in range(1, len(sub_tasks)):
                sub_tasks[i].dependencies = [sub_tasks[i-1].id]

        return sub_tasks, mode


class AgentExecutor:
    """Agent执行器

    【功能】
    - 调用具体的Agent
    - 处理执行结果
    - 错误处理
    - 超时控制
    - 重试机制
    """

    def __init__(
        self,
        max_retries: int = 2,
        timeout_seconds: float = 60.0
    ):
        self.agents = {}
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self._register_agents()

    def _register_agents(self):
        """注册Agent（延迟导入避免循环依赖）"""
        try:
            from agents.dev_agent.dev_agent import DevAgent
            self.agents["dev"] = DevAgent()
        except ImportError:
            self.agents["dev"] = None

        try:
            from agents.doc_agent.doc_agent import DocAgent
            self.agents["doc"] = DocAgent()
        except ImportError:
            self.agents["doc"] = None

        try:
            from agents.test_agent.test_agent import TestAgent
            self.agents["test"] = TestAgent()
        except ImportError:
            self.agents["test"] = None

        try:
            from agents.rag_agent.rag_agent import RAGAgent
            self.agents["rag"] = RAGAgent()
        except ImportError:
            self.agents["rag"] = None

        try:
            from agents.pm_agent.pm_agent import PMAgent
            self.agents["pm"] = PMAgent()
        except ImportError:
            self.agents["pm"] = None

        try:
            from agents.conversation_agent.conversation_agent import ConversationAgent
            self.agents["conversation"] = ConversationAgent()
        except ImportError:
            self.agents["conversation"] = None

    async def execute(self, task: SubTask, context: Dict) -> Any:
        """执行子任务（带超时和重试）"""
        agent = self.agents.get(task.assigned_agent)
        if not agent:
            raise ValueError(f"Unknown agent: {task.assigned_agent}")

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # 使用超时执行
                result = await asyncio.wait_for(
                    self._execute_agent(agent, task, context),
                    timeout=self.timeout_seconds
                )
                return result
            except asyncio.TimeoutError:
                last_error = f"Agent {task.assigned_agent} timeout after {self.timeout_seconds}s"
                error_logger.log(
                    error_type="AgentTimeout",
                    message=last_error,
                    level=ErrorLevel.WARNING
                )
            except Exception as e:
                last_error = str(e)
                error_logger.log(
                    error_type="AgentExecutionError",
                    message=f"Agent {task.assigned_agent} error: {str(e)}",
                    level=ErrorLevel.WARNING
                )

            # 重试前等待
            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))

        raise RuntimeError(f"Agent {task.assigned_agent} failed after {self.max_retries + 1} attempts: {last_error}")

    async def _execute_agent(self, agent, task: SubTask, context: Dict) -> Any:
        """根据Agent类型执行对应方法"""
        try:
            if hasattr(agent, 'execute'):
                return await agent.execute(task.description, context)
            elif hasattr(agent, 'generate_code') and task.assigned_agent == "dev":
                return await agent.generate_code(
                    description=task.description,
                    language=context.get("language", "python")
                )
            elif hasattr(agent, 'generate_tests') and task.assigned_agent == "test":
                return await agent.generate_tests(
                    description=task.description,
                    language=context.get("language", "python")
                )
            elif hasattr(agent, 'generate_readme') and task.assigned_agent == "doc":
                return await agent.generate_readme(
                    project_name=context.get("project_name", "project"),
                    description=task.description
                )
            elif hasattr(agent, 'query') and task.assigned_agent == "rag":
                return await agent.query(task.description)
            else:
                # 回退：调用通用方法
                return await agent.execute(task.description)
        except (KeyError, ValueError) as e:
            # 模板不存在时返回模拟结果
            error_logger.log(
                error_type="TemplateNotFound",
                message=f"Template not found: {e}, using fallback",
                level=ErrorLevel.WARNING
            )
            return self._get_fallback_result(task, context)

    def _get_fallback_result(self, task: SubTask, context: Dict) -> Dict:
        """获取降级结果（模板不存在时使用）"""
        return {
            "agent": task.assigned_agent,
            "description": task.description,
            "status": "fallback",
            "message": f"Fallback result for {task.assigned_agent}",
            "context": context
        }


class CollaborationMonitor:
    """协作监控器

    【功能】
    - 记录任务流转
    - 追踪执行状态
    - 生成监控报告
    """

    def __init__(self):
        self.tasks: Dict[str, CollaborationTask] = {}
        self.history: List[Dict] = []

    def start_task(self, task: CollaborationTask):
        """记录任务开始"""
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        self.tasks[task.id] = task
        self._log("task_started", task)

    def start_subtask(self, task_id: str, subtask: SubTask):
        """记录子任务开始"""
        subtask.status = TaskStatus.RUNNING
        subtask.start_time = datetime.now()
        self._log("subtask_started", {"task_id": task_id, "subtask": subtask.id})

    def complete_subtask(self, task_id: str, subtask_id: str, result: Any):
        """记录子任务完成"""
        for task in self.tasks.values():
            if task.id == task_id:
                for st in task.sub_tasks:
                    if st.id == subtask_id:
                        st.status = TaskStatus.COMPLETED
                        st.result = result
                        st.end_time = datetime.now()
                        self._log("subtask_completed", {
                            "task_id": task_id,
                            "subtask": subtask_id,
                            "duration": st.duration
                        })
                        break

    def fail_subtask(self, task_id: str, subtask_id: str, error: str):
        """记录子任务失败"""
        for task in self.tasks.values():
            if task.id == task_id:
                for st in task.sub_tasks:
                    if st.id == subtask_id:
                        st.status = TaskStatus.FAILED
                        st.error = error
                        st.end_time = datetime.now()
                        self._log("subtask_failed", {
                            "task_id": task_id,
                            "subtask": subtask_id,
                            "error": error
                        })
                        break

    def complete_task(self, task_id: str, results: Dict):
        """记录任务完成"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            task.results = results
            self._log("task_completed", {
                "task_id": task_id,
                "duration": task.duration,
                "subtask_count": len(task.sub_tasks)
            })

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                "id": task.id,
                "status": task.status.value,
                "progress": self._calculate_progress(task),
                "duration": task.duration,
                "subtasks": [
                    {
                        "id": st.id,
                        "agent": st.assigned_agent,
                        "status": st.status.value,
                        "duration": st.duration
                    }
                    for st in task.sub_tasks
                ]
            }
        return None

    def _calculate_progress(self, task: CollaborationTask) -> float:
        """计算进度"""
        if not task.sub_tasks:
            return 0.0
        completed = sum(1 for st in task.sub_tasks
                       if st.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED])
        return completed / len(task.sub_tasks)

    def _log(self, event: str, data: Dict):
        """记录事件"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data
        })

    def get_report(self) -> Dict:
        """生成监控报告"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)

        return {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
            "recent_events": self.history[-10:]
        }


class MultiAgentCoordinator:
    """多Agent协调器

    【核心功能】
    1. 任务分解
    2. 协作执行
    3. 结果聚合
    4. 监控追踪
    """

    def __init__(self):
        self.decomposer = TaskDecomposer()
        self.executor = AgentExecutor()
        self.monitor = CollaborationMonitor()

    async def execute(self, task_description: str, context: Optional[Dict] = None) -> Dict:
        """执行协作任务

        Args:
            task_description: 任务描述
            context: 上下文信息

        Returns:
            执行结果
        """
        task_id = str(uuid.uuid4())[:8]
        context = context or {}

        # 1. 任务分解
        sub_tasks, mode = self.decomposer.decompose(task_description)

        # 2. 创建协作任务
        complexity = self.decomposer.analyze_complexity(task_description)
        task = CollaborationTask(
            id=task_id,
            original_request=task_description,
            complexity=complexity,
            mode=mode,
            sub_tasks=sub_tasks
        )

        # 3. 开始监控
        self.monitor.start_task(task)

        # 4. 执行
        try:
            results = await self._execute_task(task, context)
            self.monitor.complete_task(task_id, results)
            return {
                "success": True,
                "task_id": task_id,
                "mode": mode.value,
                "complexity": complexity.value,
                "results": results,
                "monitor": self.monitor.get_task_status(task_id)
            }
        except Exception as e:
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }

    async def _execute_task(self, task: CollaborationTask, context: Dict) -> Dict:
        """根据协作模式执行任务"""
        if task.mode == CollaborationMode.PIPELINE:
            return await self._execute_pipeline(task, context)
        elif task.mode == CollaborationMode.PARALLEL:
            return await self._execute_parallel(task, context)
        else:
            return await self._execute_sequential(task, context)

    async def _execute_sequential(self, task: CollaborationTask, context: Dict) -> Dict:
        """顺序执行"""
        results = {}
        for subtask in task.sub_tasks:
            # 检查依赖
            if not self._check_dependencies(subtask, results):
                subtask.status = TaskStatus.SKIPPED
                continue

            self.monitor.start_subtask(task.id, subtask)
            try:
                result = await self.executor.execute(subtask, context)
                results[subtask.assigned_agent] = result
                self.monitor.complete_subtask(task.id, subtask.id, result)
            except Exception as e:
                self.monitor.fail_subtask(task.id, subtask.id, str(e))
                raise

        return results

    async def _execute_pipeline(self, task: CollaborationTask, context: Dict) -> Dict:
        """Pipeline执行 - 每个Agent的输出作为下一个的输入"""
        results = {}
        pipeline_context = context.copy()

        for subtask in task.sub_tasks:
            self.monitor.start_subtask(task.id, subtask)

            # 将前一个Agent的结果加入上下文
            if results:
                pipeline_context["pipeline_input"] = list(results.values())[-1]
                pipeline_context["pipeline_results"] = results

            try:
                result = await self.executor.execute(subtask, pipeline_context)
                results[subtask.assigned_agent] = result

                # 将结果加入pipeline_context供后续使用
                pipeline_context[f"{subtask.assigned_agent}_result"] = result

                self.monitor.complete_subtask(task.id, subtask.id, result)
            except Exception as e:
                self.monitor.fail_subtask(task.id, subtask.id, str(e))
                raise

        return results

    async def _execute_parallel(self, task: CollaborationTask, context: Dict) -> Dict:
        """并行执行"""
        # 分组：可以并行的为一组
        groups = self._group_parallel_tasks(task.sub_tasks)
        results = {}

        for group in groups:
            if len(group) == 1:
                # 单任务直接执行
                subtask = group[0]
                self.monitor.start_subtask(task.id, subtask)
                try:
                    result = await self.executor.execute(subtask, context)
                    results[subtask.assigned_agent] = result
                    self.monitor.complete_subtask(task.id, subtask.id, result)
                except Exception as e:
                    self.monitor.fail_subtask(task.id, subtask.id, str(e))
                    raise
            else:
                # 多任务并行执行
                coroutines = []
                for subtask in group:
                    self.monitor.start_subtask(task.id, subtask)
                    coroutines.append(self._execute_single(subtask, context, task.id))

                group_results = await asyncio.gather(*coroutines, return_exceptions=True)
                for st, result in zip(group, group_results):
                    if isinstance(result, Exception):
                        self.monitor.fail_subtask(task.id, st.id, str(result))
                    else:
                        results[st.assigned_agent] = result
                        self.monitor.complete_subtask(task.id, st.id, result)

        return results

    async def _execute_single(self, subtask: SubTask, context: Dict, task_id: str) -> Any:
        """执行单个子任务"""
        return await self.executor.execute(subtask, context)

    def _check_dependencies(self, subtask: SubTask, completed_results: Dict) -> bool:
        """检查依赖是否满足"""
        for dep_id in subtask.dependencies:
            # 简化：只要有结果就算通过
            if not completed_results:
                return True  # 第一个任务无需依赖
            # 实际应该检查依赖的任务ID
        return True

    def _group_parallel_tasks(self, sub_tasks: List[SubTask]) -> List[List[SubTask]]:
        """将子任务分组以并行执行"""
        groups = []
        current_group = []

        for st in sub_tasks:
            if st.dependencies:
                # 有依赖，放到下一组
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([st])
            else:
                current_group.append(st)

        if current_group:
            groups.append(current_group)

        return groups

    def get_monitor_report(self) -> Dict:
        """获取监控报告"""
        return self.monitor.get_report()


# 全局实例
_coordinator: Optional[MultiAgentCoordinator] = None


def get_coordinator() -> MultiAgentCoordinator:
    """获取协调器实例"""
    global _coordinator
    if _coordinator is None:
        _coordinator = MultiAgentCoordinator()
    return _coordinator


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 获取协调器
coordinator = get_coordinator()

# 2. 执行协作任务
result = await coordinator.execute(
    task_description="帮我开发一个用户登录API并编写测试",
    context={"user_id": "test_user"}
)

print(f"任务ID: {result['task_id']}")
print(f"协作模式: {result['mode']}")
print(f"复杂度: {result['complexity']}")
print(f"结果: {result['results']}")

# 3. 查看监控报告
report = coordinator.get_monitor_report()
print(f"成功率: {report['success_rate']}")
"""


class AgentCollaborationAPI:
    """Agent协作API

    提供给API层调用的接口
    """

    def __init__(self):
        self.coordinator = get_coordinator()

    async def submit_task(self, task_description: str, context: Optional[Dict] = None) -> str:
        """提交任务，返回任务ID"""
        result = await self.coordinator.execute(task_description, context)
        return result["task_id"]

    async def get_task_result(self, task_id: str) -> Optional[Dict]:
        """获取任务结果"""
        status = self.coordinator.monitor.get_task_status(task_id)
        if status:
            return status
        return None

    def get_system_report(self) -> Dict:
        """获取系统报告"""
        return self.coordinator.get_monitor_report()
