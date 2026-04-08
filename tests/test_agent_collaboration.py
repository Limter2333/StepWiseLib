"""
Agent协作系统测试
=================
"""

import sys
import asyncio
import importlib.util
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# 直接加载collaboration模块，避免触发agents/__init__.py的循环依赖
def load_collaboration_module():
    spec = importlib.util.spec_from_file_location('collaboration', 'agents/orchestrator/collaboration.py')
    collaboration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collaboration)
    return collaboration

collaboration = load_collaboration_module()


def test_task_decomposer():
    """测试任务分解器"""
    TaskDecomposer = collaboration.TaskDecomposer
    CollaborationMode = collaboration.CollaborationMode
    TaskComplexity = collaboration.TaskComplexity

    decomposer = TaskDecomposer()

    # 测试1: 简单任务
    sub_tasks, mode = decomposer.decompose("帮我写一段代码")
    assert len(sub_tasks) == 1, f"简单任务应该有1个子任务，实际{sub_tasks}"
    assert sub_tasks[0].assigned_agent == "dev"
    print("    - Simple task decomposition OK")

    # 测试2: 复杂任务（多Agent）
    sub_tasks, mode = decomposer.decompose("帮我开发一个API并编写测试")
    assert len(sub_tasks) >= 2, f"复杂任务应该有多个子任务"
    agents = [st.assigned_agent for st in sub_tasks]
    assert "dev" in agents
    print("    - Complex task decomposition OK")

    # 测试3: 复杂度分析
    complexity = decomposer.analyze_complexity("帮我开发一个用户登录API并编写测试")
    assert complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]
    print("    - Complexity analysis OK")


def test_subtask():
    """测试子任务"""
    SubTask = collaboration.SubTask
    TaskStatus = collaboration.TaskStatus

    task = SubTask(
        id="test_1",
        description="测试任务",
        assigned_agent="dev"
    )

    assert task.status == TaskStatus.PENDING
    assert task.result is None
    print("    - SubTask creation OK")


def test_collaboration_task():
    """测试协作任务"""
    CollaborationTask = collaboration.CollaborationTask
    SubTask = collaboration.SubTask
    CollaborationMode = collaboration.CollaborationMode
    TaskComplexity = collaboration.TaskComplexity

    task = CollaborationTask(
        id="collab_1",
        original_request="帮我开发并测试",
        complexity=TaskComplexity.MODERATE,
        mode=CollaborationMode.SEQUENTIAL,
        sub_tasks=[
            SubTask(id="1", description="开发", assigned_agent="dev"),
            SubTask(id="2", description="测试", assigned_agent="test")
        ]
    )

    assert len(task.sub_tasks) == 2
    assert task.mode == CollaborationMode.SEQUENTIAL
    print("    - CollaborationTask creation OK")


def test_collaboration_monitor():
    """测试协作监控"""
    CollaborationMonitor = collaboration.CollaborationMonitor
    CollaborationTask = collaboration.CollaborationTask
    SubTask = collaboration.SubTask
    CollaborationMode = collaboration.CollaborationMode
    TaskComplexity = collaboration.TaskComplexity
    TaskStatus = collaboration.TaskStatus

    monitor = CollaborationMonitor()

    # 创建任务
    task = CollaborationTask(
        id="monitor_test",
        original_request="测试任务",
        complexity=TaskComplexity.SIMPLE,
        mode=CollaborationMode.SEQUENTIAL,
        sub_tasks=[
            SubTask(id="st_1", description="子任务", assigned_agent="dev")
        ]
    )

    # 测试开始
    monitor.start_task(task)
    status = monitor.get_task_status("monitor_test")
    assert status is not None
    assert status["status"] == TaskStatus.RUNNING.value
    print("    - Task start monitoring OK")

    # 测试子任务完成
    monitor.start_subtask("monitor_test", task.sub_tasks[0])
    monitor.complete_subtask("monitor_test", "st_1", "result_data")
    status = monitor.get_task_status("monitor_test")
    assert status["progress"] == 1.0
    print("    - Subtask completion monitoring OK")

    # 测试报告
    report = monitor.get_report()
    assert "total_tasks" in report
    assert "success_rate" in report
    print("    - Monitoring report generation OK")


def test_multi_agent_coordinator():
    """测试多Agent协调器"""
    MultiAgentCoordinator = collaboration.MultiAgentCoordinator
    CollaborationMode = collaboration.CollaborationMode

    coordinator = MultiAgentCoordinator()

    # 测试任务分解
    result = asyncio.run(coordinator.execute("帮我写代码"))
    assert result["success"] == True
    assert "task_id" in result
    assert result["complexity"] == "simple"
    print("    - Coordinator execution OK")


def test_complex_task():
    """测试复杂任务"""
    MultiAgentCoordinator = collaboration.MultiAgentCoordinator

    coordinator = MultiAgentCoordinator()

    # 复杂任务：开发+测试+文档
    result = asyncio.run(coordinator.execute(
        "帮我开发一个用户管理API，编写单元测试，并生成文档"
    ))

    assert result["success"] == True
    print(f"    - Complex task executed, subtasks: {len(result['monitor']['subtasks'])}")


def test_monitor_report():
    """测试监控报告"""
    MultiAgentCoordinator = collaboration.MultiAgentCoordinator

    coordinator = MultiAgentCoordinator()

    # 执行几个任务
    asyncio.run(coordinator.execute("写代码"))
    asyncio.run(coordinator.execute("写测试"))

    report = coordinator.get_monitor_report()
    assert report["total_tasks"] == 2
    assert "success_rate" in report
    print(f"    - System report: success_rate={report['success_rate']}")


if __name__ == "__main__":
    print("=" * 60)
    print("Agent Collaboration System Test")
    print("=" * 60)
    print()

    tests = [
        ("Task Decomposer", test_task_decomposer),
        ("SubTask", test_subtask),
        ("CollaborationTask", test_collaboration_task),
        ("CollaborationMonitor", test_collaboration_monitor),
        ("MultiAgentCoordinator", test_multi_agent_coordinator),
        ("Complex Task", test_complex_task),
        ("Monitor Report", test_monitor_report),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"[{name}]")
        try:
            test_func()
            passed += 1
            print("    PASS")
        except AssertionError as e:
            print(f"    FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"    ERROR: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Result: {passed}/{passed+failed} passed")
    if failed > 0:
        print(f"Failed: {failed}")
    print("=" * 60)
