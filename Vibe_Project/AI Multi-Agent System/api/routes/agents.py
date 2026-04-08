"""
Agents API 路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from agents.dev_agent import dev_agent, TaskType
from agents.doc_agent import doc_agent, DocType
from agents.test_agent import test_agent
from agents.rag_agent import rag_agent
from agents.pm_agent import pm_agent, TaskStatus, TaskPriority
from agents.senior_pm_agent import get_senior_pm
from agents.conversation_agent import conversation_agent
from agents.orchestrator.task_router import task_router
from agents.orchestrator.result_validator import validate_agent_result, result_validator
from logs.error_logs import error_logger, ErrorLevel

router = APIRouter()


class ReadmeGenerateRequest(BaseModel):
    """生成README请求"""
    project_name: str
    description: str
    features: List[str]
    tech_stack: Optional[List[str]] = None


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    agent: str  # dev / doc / test / rag / pm / conversation
    task_type: str
    description: str
    params: Optional[dict] = {}


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    result: Optional[dict] = None


# ========== Agent状态 ==========

@router.get("/status")
async def get_agents_status():
    """获取所有Agent状态"""
    agents_info = task_router.list_agents()

    return {
        "orchestrator": {
            "name": "Chief Orchestrator",
            "status": "active",
            "task_router": "working"
        },
        "agents": agents_info
    }


# ========== Dev Agent ==========

@router.post("/dev/generate")
async def dev_generate_code(
    description: str,
    language: str = "python",
    framework: Optional[str] = None
):
    """代码生成"""
    try:
        result = await dev_agent.generate_code(
            description=description,
            language=language,
            framework=framework
        )

        # 验证结果质量
        validation = validate_agent_result("dev_agent", {
            "code": result.code,
            "tests": result.tests,
            "documentation": result.documentation
        })

        return {
            "success": True,
            "code": result.code,
            "language": result.language,
            "tests": result.tests,
            "documentation": result.documentation,
            "quality_score": result.quality_score,
            "validation": {
                "is_valid": validation.is_valid,
                "quality": validation.quality.value,
                "issues": validation.issues,
                "suggestions": validation.suggestions,
                "score": validation.score
            }
        }

    except Exception as e:
        error_logger.log(
            error_type="DevAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dev/review")
async def dev_review_code(
    code: str,
    language: str = "python"
):
    """代码审查"""
    try:
        result = await dev_agent.review_code(
            code=code,
            language=language
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        error_logger.log(
            error_type="CodeReviewError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


# ========== Doc Agent ==========

@router.post("/doc/generate-readme")
async def doc_generate_readme(request: ReadmeGenerateRequest):
    """生成README"""
    try:
        content = await doc_agent.generate_readme(
            project_name=request.project_name,
            description=request.description,
            features=request.features,
            tech_stack=request.tech_stack
        )

        # 验证结果质量
        validation = validate_agent_result("doc_agent", {"content": content})

        return {
            "success": True,
            "content": content,
            "validation": {
                "is_valid": validation.is_valid,
                "quality": validation.quality.value,
                "issues": validation.issues,
                "suggestions": validation.suggestions,
                "score": validation.score
            }
        }

    except Exception as e:
        error_logger.log(
            error_type="DocAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/doc/generate-api-doc")
async def doc_generate_api_doc(endpoints: List[dict]):
    """生成API文档"""
    try:
        content = await doc_agent.generate_api_doc(endpoints=endpoints)

        return {
            "success": True,
            "content": content
        }

    except Exception as e:
        error_logger.log(
            error_type="DocAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


# ========== Test Agent ==========

@router.post("/test/generate-unit-tests")
async def test_generate_unit_tests(
    module_name: str,
    class_name: str,
    methods: List[str]
):
    """生成单元测试"""
    try:
        tests = await test_agent.generate_unit_tests(
            module_name=module_name,
            class_name=class_name,
            methods=methods
        )

        return {
            "success": True,
            "tests": tests
        }

    except Exception as e:
        error_logger.log(
            error_type="TestAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


# ========== PM Agent ==========

@router.post("/pm/create-task")
async def pm_create_task(
    title: str,
    description: str = "",
    priority: str = "MEDIUM",
    assignee: Optional[str] = None
):
    """创建任务"""
    try:
        task = pm_agent.create_task(
            title=title,
            description=description,
            priority=TaskPriority[priority],
            assignee=assignee
        )

        return {
            "success": True,
            "task_id": task.id,
            "title": task.title,
            "status": task.status.value
        }

    except Exception as e:
        error_logger.log(
            error_type="PMAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pm/tasks")
async def pm_list_tasks():
    """列出所有任务"""
    try:
        progress = pm_agent.get_progress()
        tasks = [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority.name,
                "progress": t.progress
            }
            for t in pm_agent.tasks.values()
        ]

        return {
            "success": True,
            "tasks": tasks,
            "progress": progress
        }

    except Exception as e:
        error_logger.log(
            error_type="PMAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pm/report")
async def pm_generate_report(format: str = "markdown"):
    """生成项目报告"""
    try:
        report = pm_agent.generate_report(format=format)

        return {
            "success": True,
            "report": report
        }

    except Exception as e:
        error_logger.log(
            error_type="PMAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


# ========== Senior PM Agent ==========

@router.get("/senior-pm/report")
async def senior_pm_generate_report(format: str = "html"):
    """生成SeniorPM项目执行报告"""
    try:
        senior_pm = get_senior_pm()

        if format == "html":
            report = senior_pm.generate_executive_report_html()
            return {
                "success": True,
                "format": "html",
                "report": report
            }
        else:
            report = senior_pm.generate_executive_report()
            return {
                "success": True,
                "format": "markdown",
                "report": report
            }

    except Exception as e:
        error_logger.log(
            error_type="SeniorPMAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/senior-pm/sprint")
async def senior_pm_create_sprint(
    name: str,
    goal: str,
    start_date: str,
    end_date: str,
    capacity: int = 20
):
    """创建Sprint"""
    try:
        senior_pm = get_senior_pm()
        from datetime import datetime
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        sprint = senior_pm.create_sprint(
            name=name,
            goal=goal,
            start_date=start,
            end_date=end,
            capacity=capacity
        )

        return {"success": True, "sprint_id": sprint.id}

    except Exception as e:
        error_logger.log(
            error_type="SeniorPMAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/senior-pm/stakeholder")
async def senior_pm_add_stakeholder(
    name: str,
    role: str,
    influence: int,
    interest: int
):
    """添加干系人"""
    try:
        senior_pm = get_senior_pm()
        stakeholder = senior_pm.add_stakeholder(
            name=name,
            role=role,
            influence=influence,
            interest=interest
        )

        return {"success": True, "stakeholder_id": stakeholder.id}

    except Exception as e:
        error_logger.log(
            error_type="SeniorPMAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/senior-pm/risk")
async def senior_pm_identify_risk(
    title: str,
    description: str,
    probability: float,
    impact: str,
    category: str,
    mitigation_plan: str,
    owner: str
):
    """识别风险"""
    try:
        senior_pm = get_senior_pm()
        from agents.senior_pm_agent.senior_pm_agent import RiskLevel

        risk = senior_pm.identify_risk(
            title=title,
            description=description,
            probability=probability,
            impact=RiskLevel(impact),
            category=category,
            mitigation_plan=mitigation_plan,
            owner=owner
        )

        return {"success": True, "risk_id": risk.id}

    except Exception as e:
        error_logger.log(
            error_type="SeniorPMAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/senior-pm/strategy")
async def senior_pm_create_strategy(
    name: str,
    strategy_type: str,
    vision: str,
    timeline: str
):
    """创建战略"""
    try:
        senior_pm = get_senior_pm()
        from agents.senior_pm_agent.senior_pm_agent import StrategyType

        strategy = senior_pm.create_strategy(
            name=name,
            strategy_type=StrategyType(strategy_type),
            vision=vision,
            timeline=timeline
        )

        return {"success": True, "strategy_id": strategy.id}

    except Exception as e:
        error_logger.log(
            error_type="SeniorPMAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


# ========== RAG Agent ==========

@router.post("/rag/create-kb")
async def rag_create_knowledge_base(
    name: str,
    use_milvus: bool = False
):
    """创建知识库"""
    try:
        kb = rag_agent.create_knowledge_base(name=name, use_milvus=use_milvus)

        return {
            "success": True,
            "name": name,
            "use_milvus": use_milvus
        }

    except Exception as e:
        error_logger.log(
            error_type="RAGAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/knowledge-bases")
async def rag_list_knowledge_bases():
    """列出知识库"""
    try:
        kbs = rag_agent.list_knowledge_bases()

        return {
            "success": True,
            "knowledge_bases": kbs
        }

    except Exception as e:
        error_logger.log(
            error_type="RAGAgentError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


# ========== Task Router ==========

@router.post("/route")
async def route_task(
    description: str
):
    """自动路由任务到合适的Agent"""
    try:
        result = await task_router.execute_task(description)

        return result

    except Exception as e:
        error_logger.log(
            error_type="RouteError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


# ========== Agent Collaboration ==========

from agents.orchestrator.collaboration import AgentCollaborationAPI

_collab_api = AgentCollaborationAPI()


class CollaborateRequest(BaseModel):
    """协作任务请求"""
    task_description: str
    context: Optional[Dict[str, Any]] = None


@router.post("/collaborate/submit")
async def submit_collaborative_task(request: CollaborateRequest):
    """提交多Agent协作任务

    系统自动分析任务复杂度并分解为子任务，协调多个Agent完成。

    Args:
        task_description: 任务描述

    Returns:
        task_id: 任务ID
    """
    try:
        # 输入验证
        if not request.task_description or not request.task_description.strip():
            raise HTTPException(status_code=400, detail="Task description cannot be empty")

        task_id = await _collab_api.submit_task(
            task_description=request.task_description.strip(),
            context=request.context
        )

        return {
            "success": True,
            "task_id": task_id,
            "message": "Task submitted for collaborative execution"
        }

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="CollaborateError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collaborate/report")
async def get_collaboration_report():
    """获取协作系统报告

    Returns:
        系统级协作统计报告
    """
    try:
        report = _collab_api.get_system_report()

        return {
            "success": True,
            **report
        }

    except Exception as e:
        error_logger.log(
            error_type="CollaborateError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collaborate/{task_id}")
async def get_collaborative_task_result(task_id: str):
    """获取协作任务结果

    Args:
        task_id: 任务ID

    Returns:
        任务状态和结果
    """
    try:
        result = await _collab_api.get_task_result(task_id)

        if not result:
            raise HTTPException(status_code=404, detail="Task not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="CollaborateError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


# ========== Agent Shared Context API ==========

from agents.orchestrator.shared_context import (
    get_shared_context,
    SharedContext,
    ContextScope,
    AgentContext
)

_shared_ctx = get_shared_context()


class ContextSetRequest(BaseModel):
    """设置上下文请求"""
    key: str
    value: Any
    scope: str = "task"
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    ttl_seconds: Optional[int] = 3600


@router.post("/context/set")
async def context_set(request: ContextSetRequest):
    """设置共享上下文值

    将值存储到共享上下文黑板，供其他Agent使用。

    Args:
        key: 键名（建议格式: agent_id:key_name）
        value: 值（任意JSON可序列化对象）
        scope: 作用域 (global/session/task/agent)
        agent_id: Agent ID
        task_id: 任务ID
        session_id: 会话ID
        ttl_seconds: 过期时间（秒）
    """
    try:
        _shared_ctx.set(
            key=request.key,
            value=request.value,
            scope=ContextScope(request.scope),
            agent_id=request.agent_id,
            task_id=request.task_id,
            session_id=request.session_id,
            ttl_seconds=request.ttl_seconds
        )
        return {"success": True, "message": f"Key '{request.key}' set successfully"}

    except Exception as e:
        error_logger.log(
            error_type="ContextSetError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/get")
async def context_get(
    key: str,
    scope: str = "task",
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """获取共享上下文值

    从共享上下文黑板读取值。

    Args:
        key: 键名
        scope: 作用域
        agent_id: Agent ID
        task_id: 任务ID
        session_id: 会话ID
    """
    try:
        value = _shared_ctx.get(
            key=key,
            scope=ContextScope(scope),
            agent_id=agent_id,
            task_id=task_id,
            session_id=session_id
        )
        return {
            "success": True,
            "key": key,
            "value": value,
            "scope": scope
        }

    except Exception as e:
        error_logger.log(
            error_type="ContextGetError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/context/delete")
async def context_delete(
    key: str,
    scope: str = "task",
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """删除共享上下文值"""
    try:
        _shared_ctx.delete(
            key=key,
            scope=ContextScope(scope),
            agent_id=agent_id,
            task_id=task_id,
            session_id=session_id
        )
        return {"success": True, "message": f"Key '{key}' deleted"}

    except Exception as e:
        error_logger.log(
            error_type="ContextDeleteError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/keys")
async def context_keys(
    scope: str = "task",
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """列出共享上下文中的所有键

    Args:
        scope: 作用域
        agent_id: Agent ID
        task_id: 任务ID
        session_id: 会话ID
    """
    try:
        keys = _shared_ctx.keys(
            scope=ContextScope(scope),
            agent_id=agent_id,
            task_id=task_id,
            session_id=session_id
        )
        return {
            "success": True,
            "scope": scope,
            "keys": keys
        }

    except Exception as e:
        error_logger.log(
            error_type="ContextKeysError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/all")
async def context_get_all(
    scope: str = "task",
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """获取指定作用域的所有键值对"""
    try:
        data = _shared_ctx.get_all(
            scope=ContextScope(scope),
            agent_id=agent_id,
            task_id=task_id,
            session_id=session_id
        )
        return {
            "success": True,
            "scope": scope,
            "data": data
        }

    except Exception as e:
        error_logger.log(
            error_type="ContextGetAllError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/context/clear")
async def context_clear(
    scope: str = "task",
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """清空指定作用域的共享上下文

    Args:
        scope: 作用域
        agent_id: Agent ID
        task_id: 任务ID
        session_id: 会话ID

    Returns:
        删除的条目数量
    """
    try:
        count = _shared_ctx.clear(
            scope=ContextScope(scope),
            agent_id=agent_id,
            task_id=task_id,
            session_id=session_id
        )
        return {
            "success": True,
            "message": f"Cleared {count} entries",
            "deleted_count": count
        }

    except Exception as e:
        error_logger.log(
            error_type="ContextClearError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/stats")
async def context_stats():
    """获取共享上下文统计信息

    Returns:
        全局、会话、任务、Agent级别的条目数量
    """
    try:
        stats = _shared_ctx.get_stats()
        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        error_logger.log(
            error_type="ContextStatsError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))
