"""
Chief Orchestrator - 核心调度者
================================

【学习要点】
1. 什么是Orchestrator/调度者模式?
   - 单一入口点协调多个Agent
   - 任务分解与分配
   - 结果聚合与质量把控

2. LangGraph状态机
   - State: 共享状态（任务进度、上下文等）
   - Node: 执行单元（Agent）
   - Edge: 流转条件

3. 多Agent协作模式
   - 顺序执行: A -> B -> C
   - 并行执行: A || B || C
   - 条件分支: if X then A else B
"""

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import operator

# 导入实际Agent实现
from agents.dev_agent import dev_agent
from agents.doc_agent import doc_agent
from agents.test_agent import test_agent
from agents.rag_agent import rag_agent
from agents.pm_agent import pm_agent
from agents.conversation_agent import conversation_agent
from agents.orchestrator.result_validator import validate_agent_result


# ========== 状态定义 ==========
class AgentState(TypedDict):
    """智能体共享状态

    【学习要点】TypedDict vs dataclass
    - 声明式定义结构
    - 适合定义配置和状态
    - 可用于类型提示
    """
    messages: Sequence[HumanMessage | AIMessage | SystemMessage]
    current_task: str
    task_result: dict
    active_agents: list
    task_history: list


# ========== Agent定义 ==========
class AgentRegistry:
    """Agent注册表

    【学习要点】注册表模式
    - 集中管理所有Agent
    - 支持动态加载
    - 便于扩展
    """

    def __init__(self):
        self.agents = {}

    def register(self, name: str, agent: callable):
        """注册Agent"""
        self.agents[name] = agent
        print(f"[Registry] Registered agent: {name}")

    def get(self, name: str) -> callable:
        """获取Agent"""
        return self.agents.get(name)

    def list_agents(self) -> list:
        """列出所有Agent"""
        return list(self.agents.keys())


# 全局注册表
agent_registry = AgentRegistry()


# ========== 任务节点 ==========
def orchestrator_node(state: AgentState) -> AgentState:
    """核心调度节点

    这是整个系统的入口点，负责：
    1. 理解用户需求
    2. 分解任务
    3. 分配给合适的Agent
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    print(f"[Orchestrator] Processing: {last_message[:100]}...")

    # 任务分解逻辑
    task_result = {
        "original_request": last_message,
        "sub_tasks": [],
        "assigned_agents": []
    }

    return {
        **state,
        "task_result": task_result
    }


def routing_decision(state: AgentState) -> str:
    """基于任务类型路由到合适的Agent

    【LangGraph条件路由】
    返回值决定下一个执行的节点
    """
    task = state["current_task"].lower()

    # RAG/知识库相关 -> RAG Agent
    if any(kw in task for kw in ["知识", "rag", "检索", "查询", "document", "knowledge", "query"]):
        return "rag_agent"

    # 文档/报告相关 -> Doc Agent
    if any(kw in task for kw in ["文档", "报告", "doc", "report", "生成文档", "写文档"]):
        return "doc_agent"

    # 测试相关 -> Test Agent
    if any(kw in task for kw in ["测试", "test", "单元测试", "集成测试", "测试用例"]):
        return "test_agent"

    # 项目管理/规划相关 -> PM Agent
    if any(kw in task for kw in ["规划", "计划", "pm", "项目管理", "roadmap", "进度"]):
        return "pm_agent"

    # 对话/聊天相关 -> Conversation Agent
    if any(kw in task for kw in ["对话", "聊天", "chat", "conversation", "回复", "消息"]):
        return "conversation_agent"

    # 开发任务 -> Dev Agent (默认)
    if any(kw in task for kw in ["代码", "开发", "code", "dev", "实现", "功能", "bug", "修复"]):
        return "dev_agent"

    # 未知任务 -> conversation_agent (兜底)
    return "conversation_agent"


async def _call_dev_agent(task: str) -> dict:
    """调用开发Agent"""
    try:
        result = await dev_agent.generate_code(
            description=task,
            language="python"
        )
        # 验证结果
        validation = validate_agent_result("dev_agent", {
            "code": result.code,
            "tests": result.tests,
            "documentation": result.documentation
        })
        return {
            "success": True,
            "code": result.code,
            "quality_score": result.quality_score,
            "validation": {
                "is_valid": validation.is_valid,
                "quality": validation.quality.value,
                "score": validation.score
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _call_doc_agent(task: str) -> dict:
    """调用文档Agent"""
    try:
        result = await doc_agent.generate_readme(
            project_name="Project",
            description=task,
            features=["Feature 1", "Feature 2"]
        )
        # 验证结果
        validation = validate_agent_result("doc_agent", {"content": result})
        return {
            "success": True,
            "content": result,
            "validation": {
                "is_valid": validation.is_valid,
                "quality": validation.quality.value,
                "score": validation.score
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _call_test_agent(task: str) -> dict:
    """调用测试Agent"""
    try:
        result = await test_agent.generate_unit_tests(
            module_name="example_module",
            class_name="ExampleClass",
            methods=["method1", "method2"]
        )
        return {
            "success": True,
            "tests": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _call_rag_agent(task: str) -> dict:
    """调用RAG Agent"""
    try:
        result = await rag_agent.query(question=task)
        return {
            "success": True,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", [])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _call_pm_agent(task: str) -> dict:
    """调用PM Agent"""
    try:
        result = pm_agent.get_progress()
        return {
            "success": True,
            "progress": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _call_conversation_agent(task: str, session_id: str = "default") -> dict:
    """调用对话Agent"""
    try:
        result = await conversation_agent.send_message(
            session_id=session_id,
            message=task
        )
        return {
            "success": True,
            "response": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def dev_agent_node(state: AgentState) -> AgentState:
    """开发Agent节点"""
    print("[Dev Agent] Executing task...")
    task = state["current_task"]
    # 在同步节点中启动异步调用
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已经在运行中，创建task
            future = asyncio.ensure_future(_call_dev_agent(task))
            result = future.result(timeout=60)
        else:
            result = loop.run_until_complete(_call_dev_agent(task))
    except:
        result = {"success": False, "error": "Execution failed"}
    return {
        **state,
        "task_result": {
            **state["task_result"],
            "dev_output": result
        },
        "active_agents": state.get("active_agents", []) + ["dev_agent"]
    }


def doc_agent_node(state: AgentState) -> AgentState:
    """文档Agent节点"""
    print("[Doc Agent] Writing documentation...")
    task = state["current_task"]
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.ensure_future(_call_doc_agent(task))
            result = future.result(timeout=60)
        else:
            result = loop.run_until_complete(_call_doc_agent(task))
    except:
        result = {"success": False, "error": "Execution failed"}
    return {
        **state,
        "task_result": {
            **state["task_result"],
            "doc_output": result
        },
        "active_agents": state.get("active_agents", []) + ["doc_agent"]
    }


def test_agent_node(state: AgentState) -> AgentState:
    """测试Agent节点"""
    print("[Test Agent] Running tests...")
    task = state["current_task"]
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.ensure_future(_call_test_agent(task))
            result = future.result(timeout=60)
        else:
            result = loop.run_until_complete(_call_test_agent(task))
    except:
        result = {"success": False, "error": "Execution failed"}
    return {
        **state,
        "task_result": {
            **state["task_result"],
            "test_output": result
        },
        "active_agents": state.get("active_agents", []) + ["test_agent"]
    }


def rag_agent_node(state: AgentState) -> AgentState:
    """RAG Agent节点"""
    print("[RAG Agent] Processing knowledge base...")
    task = state["current_task"]
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.ensure_future(_call_rag_agent(task))
            result = future.result(timeout=60)
        else:
            result = loop.run_until_complete(_call_rag_agent(task))
    except:
        result = {"success": False, "error": "Execution failed"}
    return {
        **state,
        "task_result": {
            **state["task_result"],
            "rag_output": result
        },
        "active_agents": state.get("active_agents", []) + ["rag_agent"]
    }


def pm_agent_node(state: AgentState) -> AgentState:
    """PM Agent节点"""
    print("[PM Agent] Updating project status...")
    task = state["current_task"]
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.ensure_future(_call_pm_agent(task))
            result = future.result(timeout=60)
        else:
            result = loop.run_until_complete(_call_pm_agent(task))
    except:
        result = {"success": False, "error": "Execution failed"}
    return {
        **state,
        "task_result": {
            **state["task_result"],
            "pm_output": result
        },
        "active_agents": state.get("active_agents", []) + ["pm_agent"]
    }


def conversation_agent_node(state: AgentState) -> AgentState:
    """对话Agent节点"""
    print("[Conversation Agent] Managing dialogue...")
    task = state["current_task"]
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.ensure_future(_call_conversation_agent(task))
            result = future.result(timeout=60)
        else:
            result = loop.run_until_complete(_call_conversation_agent(task))
    except:
        result = {"success": False, "error": "Execution failed"}
    return {
        **state,
        "task_result": {
            **state["task_result"],
            "conv_output": result
        },
        "active_agents": state.get("active_agents", []) + ["conversation_agent"]
    }


def result_aggregator_node(state: AgentState) -> AgentState:
    """结果聚合节点"""
    print("[Orchestrator] Aggregating results...")
    return state


# ========== 构建工作流图 ==========
def build_workflow():
    """构建LangGraph工作流

    【学习要点】LangGraph工作流
    - StateGraph: 创建状态图
    - add_node: 添加节点（执行单元）
    - add_edge: 添加边（流转关系）
    - add_conditional_edges: 条件分支
    """

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("dev_agent", dev_agent_node)
    workflow.add_node("doc_agent", doc_agent_node)
    workflow.add_node("test_agent", test_agent_node)
    workflow.add_node("rag_agent", rag_agent_node)
    workflow.add_node("pm_agent", pm_agent_node)
    workflow.add_node("conversation_agent", conversation_agent_node)
    workflow.add_node("aggregator", result_aggregator_node)

    # 设置入口
    workflow.set_entry_point("orchestrator")

    # 【关键修复】使用条件路由替代直接END
    # 条件路由根据任务类型分发到不同Agent
    workflow.add_conditional_edges(
        "orchestrator",
        routing_decision,
        {
            "dev_agent": "dev_agent",
            "doc_agent": "doc_agent",
            "test_agent": "test_agent",
            "rag_agent": "rag_agent",
            "pm_agent": "pm_agent",
            "conversation_agent": "conversation_agent",
        }
    )

    # 各个Agent -> 聚合器
    workflow.add_edge("dev_agent", "aggregator")
    workflow.add_edge("doc_agent", "aggregator")
    workflow.add_edge("test_agent", "aggregator")
    workflow.add_edge("rag_agent", "aggregator")
    workflow.add_edge("pm_agent", "aggregator")
    workflow.add_edge("conversation_agent", "aggregator")

    # 聚合器 -> 结束
    workflow.add_edge("aggregator", END)

    return workflow.compile()


# 创建工作流实例
workflow = build_workflow()


# ========== 调度接口 ==========
async def execute_task(task_description: str) -> dict:
    """执行任务

    Args:
        task_description: 任务描述

    Returns:
        执行结果
    """
    initial_state = AgentState(
        messages=[HumanMessage(content=task_description)],
        current_task=task_description,
        task_result={},
        active_agents=[],
        task_history=[]
    )

    result = await workflow.ainvoke(initial_state)
    return result["task_result"]
