import abc
from typing import Any
from harness.events import AgentEvent, ToolCallResult


class Hook(abc.ABC):
    """钩子抽象基类。
    
    设计意图：提供可扩展的事件监听机制，让外部代码
    （如日志、UI、统计）可以响应 Agent 运行过程中的事件，
    而不需要修改核心循环逻辑。
    """
    
    @abc.abstractmethod
    def on_event(self, event: AgentEvent) -> None:
        """处理 Agent 事件。
        
        Args:
            event: Agent 事件对象
        """
        pass
    
    def on_tool_call(self, result: ToolCallResult) -> None:
        """处理工具调用结果（可选覆盖）。
        
        默认实现：忽略工具调用结果。
        """
        pass
    
    def on_error(self, error: Exception, step: int) -> None:
        """处理错误（可选覆盖）。
        
        默认实现：忽略错误。
        """
        pass


class CompositeHook(Hook):
    """组合钩子：同时触发多个钩子。
    
    设计意图：支持同时注册多个钩子，简化多钩子场景的管理。
    """
    
    def __init__(self):
        self._hooks: list[Hook] = []
    
    def add(self, hook: Hook) -> None:
        """添加一个钩子。"""
        self._hooks.append(hook)
    
    def remove(self, hook: Hook) -> None:
        """移除一个钩子。"""
        self._hooks.remove(hook)
    
    def on_event(self, event: AgentEvent) -> None:
        """触发所有钩子的 on_event。"""
        for hook in self._hooks:
            try:
                hook.on_event(event)
            except Exception as e:
                # 钩子异常不应该影响主流程
                print(f"⚠️ 钩子 {hook.__class__.__name__} 执行出错：{e}")
    
    def on_tool_call(self, result: ToolCallResult) -> None:
        """触发所有钩子的 on_tool_call。"""
        for hook in self._hooks:
            try:
                hook.on_tool_call(result)
            except Exception:
                pass
    
    def on_error(self, error: Exception, step: int) -> None:
        """触发所有钩子的 on_error。"""
        for hook in self._hooks:
            try:
                hook.on_error(error, step)
            except Exception:
                pass
