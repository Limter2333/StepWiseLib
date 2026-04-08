"""
Agent调度器 - 任务路由
======================

根据任务类型自动分配给合适的Agent
13个Agent员工完整支持
支持Agent间共享上下文
"""

from typing import Dict, Optional, Any
from enum import Enum
import uuid

# 导入所有Agent
from agents.dev_agent import dev_agent
from agents.doc_agent import doc_agent
from agents.test_agent import test_agent
from agents.rag_agent import rag_agent
from agents.pm_agent import pm_agent
from agents.conversation_agent import conversation_agent
from agents.ops_agent import ops_agent
from agents.senior_pm_agent import senior_pm_agent
from agents.evaluator_agent import evaluator_agent

# New 9 Agents (now enabled - syntax errors fixed)
from agents.frontend_developer import frontend_developer
from agents.backend_architect import backend_architect
from agents.technical_writer import technical_writer
from agents.code_reviewer import code_reviewer
from agents.ui_designer import ui_designer
from agents.product_manager import product_manager
from agents.reality_checker import reality_checker
from agents.api_tester import api_tester
from agents.workflow_optimizer import workflow_optimizer

# 导入共享上下文
from agents.orchestrator.shared_context import get_shared_context, ContextScope


class TaskType(Enum):
    """任务类型枚举"""
    # Original 6
    CODE = "code"
    DOCUMENT = "document"
    TEST = "test"
    KNOWLEDGE = "knowledge"
    PROJECT = "project"
    CONVERSATION = "conversation"
    OPS = "ops"
    # New 7
    FRONTEND = "frontend"
    BACKEND = "backend"
    CODE_REVIEW = "code_review"
    UI_DESIGN = "ui_design"
    PRODUCT = "product"
    REALITY_CHECK = "reality_check"
    API_TEST = "api_test"
    WORKFLOW = "workflow"
    OTHER = "other"


class TaskRouter:
    """任务路由器

    核心功能：
    - 分析任务类型
    - 分配给合适的Agent
    - 聚合结果
    """

    def __init__(self):
        self.agents = {
            # Original 6
            "dev": dev_agent,
            "doc": doc_agent,
            "test": test_agent,
            "rag": rag_agent,
            "pm": pm_agent,
            "conversation": conversation_agent,
            "ops": ops_agent,
            "senior_pm": senior_pm_agent,
            "evaluator": evaluator_agent,
            # New 9 Agents (now enabled)
            "frontend": frontend_developer,
            "backend": backend_architect,
            "technical_writer": technical_writer,
            "code_reviewer": code_reviewer,
            "ui_designer": ui_designer,
            "product_manager": product_manager,
            "reality_checker": reality_checker,
            "api_tester": api_tester,
            "workflow_optimizer": workflow_optimizer,
        }

    def route(self, task_description: str) -> TaskType:
        """路由任务

        分析任务描述，返回合适的任务类型
        """
        if not task_description or not task_description.strip():
            return TaskType.OTHER

        desc_lower = task_description.lower()

        # 前端相关
        if any(kw in desc_lower for kw in ["frontend", "前端", "react", "vue", "html", "css", "组件", "component"]):
            return TaskType.FRONTEND

        # 后端架构相关
        if any(kw in desc_lower for kw in ["backend", "后端", "architecture", "架构", "database", "数据库", "schema", "api design"]):
            return TaskType.BACKEND

        # 代码审查相关
        if any(kw in desc_lower for kw in ["review", "审查", "security", "安全", "quality", "质量", "scan", "扫描"]):
            return TaskType.CODE_REVIEW

        # 运维相关 - 移前(更具体)
        if any(kw in desc_lower for kw in ["deploy", "部署", "ops", "运维", "infrastructure", "基础设施", "monitor", "监控"]):
            return TaskType.OPS

        # 项目管理相关 - 移前(更具体)
        if any(kw in desc_lower for kw in ["project", "项目", "milestone", "进度", "task", "任务", "pm"]):
            return TaskType.PROJECT

        # UI设计相关 - 移后(宽泛关键词)
        if any(kw in desc_lower for kw in ["ui design", "ui设计", "user interface", "界面设计", "组件规格", "layout design"]):
            return TaskType.UI_DESIGN

        # 产品相关
        if any(kw in desc_lower for kw in ["product", "产品", "roadmap", "用户故事", "user story", "需求", "requirement", "epic"]):
            return TaskType.PRODUCT

        # 现实核查相关
        if any(kw in desc_lower for kw in ["verify", "核查", "fact", "事实", "feasibility", "可行性", "risk", "风险", "assumption", "假设"]):
            return TaskType.REALITY_CHECK

        # API测试相关
        if any(kw in desc_lower for kw in ["api test", "endpoint", "contract", "契约", "load test", "performance", "性能测试"]):
            return TaskType.API_TEST

        # 工作流优化相关
        if any(kw in desc_lower for kw in ["workflow", "工作流", "process", "流程", "optimize", "优化", "bottleneck", "瓶颈", "automation", "自动化"]):
            return TaskType.WORKFLOW

        # 代码相关
        if any(kw in desc_lower for kw in ["code", "代码", "implement", "开发", "function", "功能", "bug", "fix"]):
            return TaskType.CODE

        # 文档相关
        if any(kw in desc_lower for kw in ["doc", "文档", "write", "撰写", "readme", "文档生成"]):
            return TaskType.DOCUMENT

        # 测试相关
        if any(kw in desc_lower for kw in ["test", "测试", "unit", "单元测试"]):
            return TaskType.TEST

        # 知识库相关
        if any(kw in desc_lower for kw in ["knowledge", "知识库", "index", "索引", "search", "检索", "rag"]):
            return TaskType.KNOWLEDGE

        # 对话相关
        if any(kw in desc_lower for kw in ["chat", "对话", "message", "消息", "session"]):
            return TaskType.CONVERSATION

        return TaskType.OTHER

    def get_agent_for_task(self, task_type: TaskType):
        """获取适合任务的Agent"""
        mapping = {
            TaskType.CODE: self.agents["dev"],
            TaskType.DOCUMENT: self.agents["doc"],
            TaskType.TEST: self.agents["test"],
            TaskType.KNOWLEDGE: self.agents["rag"],
            TaskType.PROJECT: self.agents["pm"],
            TaskType.CONVERSATION: self.agents["conversation"],
            TaskType.OPS: self.agents["ops"],
            # New Agents (now enabled)
            TaskType.FRONTEND: self.agents["frontend"],
            TaskType.BACKEND: self.agents["backend"],
            TaskType.CODE_REVIEW: self.agents["code_reviewer"],
            TaskType.UI_DESIGN: self.agents["ui_designer"],
            TaskType.PRODUCT: self.agents["product_manager"],
            TaskType.REALITY_CHECK: self.agents["reality_checker"],
            TaskType.API_TEST: self.agents["api_tester"],
            TaskType.WORKFLOW: self.agents["workflow_optimizer"],
        }
        return mapping.get(task_type, None)

    async def execute_task(self, task_description: str, **kwargs) -> Dict:
        """执行任务

        Args:
            task_description: 任务描述
            **kwargs: 任务参数
                - task_id: 任务ID（可选，用于跨Agent上下文共享）
                - session_id: 会话ID（可选）
                - store_context: 是否存储结果到共享上下文（默认True）
                - read_context: 是否读取共享上下文（默认True）

        Returns:
            执行结果
        """
        # 0. 初始化上下文
        shared_ctx = get_shared_context()
        task_id = kwargs.get("task_id", str(uuid.uuid4())[:8])
        session_id = kwargs.get("session_id", "default")
        store_context = kwargs.get("store_context", True)
        read_context = kwargs.get("read_context", True)

        # 1. 路由
        task_type = self.route(task_description)
        agent = self.get_agent_for_task(task_type)

        # 2. 执行
        if agent is None:
            return {
                "success": False,
                "error": f"No agent for task type: {task_type.value}"
            }

        # 3. 获取Agent ID
        agent_id = getattr(agent, 'name', str(agent.__class__.__name__))

        # 4. 如果允许读取上下文，从共享上下文获取之前的相关结果
        context_data = {}
        if read_context:
            context_data = shared_ctx.get_all(
                scope=ContextScope.TASK,
                task_id=task_id,
                session_id=session_id
            )
            # 也获取全局上下文
            global_data = shared_ctx.get_all(scope=ContextScope.GLOBAL)
            context_data.update(global_data)

        # 5. 调用对应的Agent方法
        try:
            if task_type == TaskType.CODE:
                result = await agent.generate_code(
                    description=task_description,
                    context=context_data,  # 传递共享上下文
                    **kwargs
                )
            elif task_type == TaskType.DOCUMENT:
                result = await agent.generate_readme(
                    project_name=kwargs.get("project_name", "Project"),
                    description=task_description,
                    features=kwargs.get("features", []),
                    context=context_data,
                    **kwargs
                )
            elif task_type == TaskType.TEST:
                result = await agent.generate_unit_tests(
                    context=context_data,
                    **kwargs
                )
            elif task_type == TaskType.KNOWLEDGE:
                result = await agent.query(
                    question=task_description,
                    **kwargs
                )
            elif task_type == TaskType.PROJECT:
                result = agent.get_progress()
            elif task_type == TaskType.CONVERSATION:
                result = await agent.send_message(
                    session_id=kwargs.get("session_id", "default"),
                    message=task_description,
                    **kwargs
                )
            elif task_type == TaskType.OPS:
                result = await agent.deploy(
                    environment=kwargs.get("environment", "development"),
                    version=kwargs.get("version", "latest"),
                    deployment_type=kwargs.get("deployment_type", "rolling")
                )
            # New Agents (now enabled)
            elif task_type == TaskType.FRONTEND:
                result = await agent.generate_component(
                    description=task_description,
                    **kwargs
                )
            elif task_type == TaskType.BACKEND:
                result = await agent.design_system(
                    description=task_description,
                    requirements=kwargs.get("requirements", []),
                    **kwargs
                )
            elif task_type == TaskType.CODE_REVIEW:
                result = await agent.review_code(
                    code=kwargs.get("code", ""),
                    language=kwargs.get("language", "python"),
                    **kwargs
                )
            elif task_type == TaskType.UI_DESIGN:
                result = await agent.design_component(
                    description=task_description,
                    component_type=kwargs.get("component_type", "button"),
                    style=kwargs.get("style", "minimal"),
                    **kwargs
                )
            elif task_type == TaskType.PRODUCT:
                result = agent.create_user_story(
                    role=kwargs.get("role", "user"),
                    requirement=task_description,
                    goal=kwargs.get("goal", ""),
                    **kwargs
                )
            elif task_type == TaskType.REALITY_CHECK:
                result = await agent.check_fact(
                    statement=task_description,
                    context=kwargs.get("context"),
                )
            elif task_type == TaskType.API_TEST:
                result = await agent.generate_test_cases(
                    endpoints=kwargs.get("endpoints", []),
                    base_url=kwargs.get("base_url", "http://localhost:8000"),
                )
            elif task_type == TaskType.WORKFLOW:
                result = await agent.analyze_workflow(
                    steps=kwargs.get("steps", []),
                    workflow_type=kwargs.get("workflow_type", "sequential"),
                )
            else:
                result = {"message": "Task type not supported yet"}

            # 6. 如果允许，存储结果到共享上下文
            if store_context and isinstance(result, dict):
                shared_ctx.set(
                    key=f"{agent_id}:last_result",
                    value=result,
                    scope=ContextScope.TASK,
                    agent_id=agent_id,
                    task_id=task_id,
                    session_id=session_id,
                    ttl_seconds=kwargs.get("ttl_seconds", 3600)
                )
                # 也存储任务类型，方便后续Agent判断
                shared_ctx.set(
                    key="current_task_type",
                    value=task_type.value,
                    scope=ContextScope.TASK,
                    task_id=task_id,
                    session_id=session_id
                )

            return {
                "success": True,
                "task_type": task_type.value,
                "task_id": task_id,
                "agent": agent_id,
                "result": result,
                "context_used": bool(context_data),
                "context_stored": store_context
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type.value,
                "task_id": task_id
            }

    def list_agents(self) -> Dict:
        """列出所有Agent及其能力"""
        return {
            name: agent.get_capabilities()
            for name, agent in self.agents.items()
        }


# 全局实例
task_router = TaskRouter()
