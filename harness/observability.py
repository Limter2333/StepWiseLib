import time
from dataclasses import dataclass, field
from typing import Optional
from harness.events import AgentEvent, EventType, ToolCallResult
from .hooks import Hook


@dataclass
class StepRecord:
    """单步执行记录。"""
    step: int
    tool: Optional[str] = None
    duration_ms: float = 0.0
    token_estimate: int = 0
    decision: str = ""
    event_type: str = ""


@dataclass
class RunSummary:
    """一次运行的汇总统计。"""
    total_steps: int = 0
    tool_calls: int = 0
    total_duration_ms: float = 0.0
    token_estimate: int = 0
    success: bool = False
    error_count: int = 0
    steps: list[StepRecord] = field(default_factory=list)


class AgentLogger(Hook):
    """Agent 日志记录器。
    
    设计意图：记录 Agent 运行过程中的所有事件，提供：
    - 结构化日志输出
    - Token 用量估算
    - 运行汇总统计
    """
    
    def __init__(self, verbose: bool = True):
        """初始化日志记录器。
        
        Args:
            verbose: 是否输出详细日志到控制台
        """
        self._verbose = verbose
        self._summary = RunSummary()
        self._current_step: int = 0
        self._step_start: float = 0.0
    
    def on_event(self, event: AgentEvent) -> None:
        """处理 Agent 事件并记录。"""
        self._current_step = event.step
        
        # 记录步骤开始时间
        if event.type == EventType.THOUGHT:
            self._step_start = time.time()
        
        # 估算 token 数
        token_est = len(event.content) // 2  # 简单估算中文
        self._summary.token_estimate += token_est
        
        # 记录步骤
        record = StepRecord(
            step=event.step,
            event_type=event.type.value,
            token_estimate=token_est,
            duration_ms=(time.time() - self._step_start) * 1000 if self._step_start else 0
        )
        self._summary.steps.append(record)
        
        # 控制台输出
        if self._verbose:
            self._print_event(event)
    
    def on_tool_call(self, result: ToolCallResult) -> None:
        """记录工具调用。"""
        self._summary.tool_calls += 1
        
        # 更新当前步骤的工具信息
        for record in reversed(self._summary.steps):
            if record.step == self._current_step:
                record.tool = result.tool_name
                record.duration_ms = result.duration_ms
                break
        
        if self._verbose and result.tool_name:
            print(f"  🔧 工具调用：{result.tool_name} ({result.duration_ms:.0f}ms)")
    
    def on_error(self, error: Exception, step: int) -> None:
        """记录错误。"""
        self._summary.error_count += 1
        
        if self._verbose:
            print(f"  ❌ 错误（步骤 {step}）：{error}")
    
    def _print_event(self, event: AgentEvent) -> None:
        """打印事件到控制台。"""
        icon = {
            EventType.THOUGHT: "💭",
            EventType.ACTION: "🔧",
            EventType.OBSERVATION: "🔍",
            EventType.FINAL: "✅",
            EventType.ERROR: "❌",
        }.get(event.type, "📌")
        
        # 截断过长内容
        content = event.content[:200] + "..." if len(event.content) > 200 else event.content
        content = content.replace("\n", " ")
        
        print(f"{icon} [{event.type.value}] {content}")
    
    def get_summary(self) -> str:
        """获取运行汇总文本。"""
        duration_s = self._summary.total_duration_ms / 1000
        return (
            f"运行完成：共 {self._summary.total_steps} 步，"
            f"调用工具 {self._summary.tool_calls} 次，"
            f"耗时 {duration_s:.1f}s，"
            f"预估输入 {self._summary.token_estimate} tokens"
        )
    
    def reset(self) -> None:
        """重置统计信息（用于多次运行）。"""
        self._summary = RunSummary()
        self._current_step = 0
        self._step_start = 0.0
