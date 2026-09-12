import re
import time
from typing import Optional, Callable

from harness.config import AgentConfig
from harness.events import AgentEvent, EventType, ToolCallResult
from harness.llm.base import BaseLLMClient, ChatMessage
from harness.tools.base import ToolSpec
from harness.tools.registry import ToolRegistry
from harness.memory.base import MemoryProvider
from harness.permissions import PermissionDecision, PermissionPolicy
from harness.hooks import Hook, CompositeHook
from harness.prompt import PromptProvider, ReActPromptProvider


class AgentRunner:
    """通用 Agent 运行器。
    
    设计意图：实现标准的 Thought-Action-Observation 循环，
    支持可插拔的 LLM、工具、记忆、权限和钩子组件。
    """
    
    def __init__(
        self,
        llm: BaseLLMClient,
        registry: ToolRegistry,
        memory: Optional[MemoryProvider] = None,
        config: Optional[AgentConfig] = None,
        hooks: Optional[list[Hook]] = None,
        permission_policy: Optional[PermissionPolicy] = None,
        prompt_provider: Optional[PromptProvider] = None,
    ):
        """初始化 AgentRunner。
        
        Args:
            llm: LLM 客户端
            registry: 工具注册表
            memory: 记忆管理器（可选）
            config: Agent 配置
            hooks: 钩子列表
            permission_policy: 权限策略
            prompt_provider: 提示词提供者（可选，默认使用 ReAct）
        """
        self._llm = llm
        self._registry = registry
        self._memory = memory
        self._config = config or AgentConfig()
        self._hooks = CompositeHook()
        self._permissions = permission_policy or PermissionPolicy()
        self._prompt_provider = prompt_provider or ReActPromptProvider()
        
        # 注册钩子
        if hooks:
            for hook in hooks:
                self._hooks.add(hook)
    
    def run(self, task: str, user_input_callback: Optional[Callable[[str], str]] = None) -> str:
        """运行 Agent 执行任务。
        
        Args:
            task: 用户任务描述
            user_input_callback: 用户输入回调（用于权限确认）
            
        Returns:
            最终答案或错误信息
        """
        # 构建系统提示词
        tool_list = self._registry.to_prompt_list()
        system_prompt = self._prompt_provider.get_system_prompt(tool_list=tool_list)
        
        # 初始化消息历史
        messages = [ChatMessage(role="system", content=system_prompt)]
        
        # 添加记忆历史
        if self._memory:
            messages.extend(self._memory.history())
        
        # 添加用户任务
        messages.append(ChatMessage(role="user", content=f"<question>{task}</question>"))
        
        # 主循环
        for step in range(self._config.max_steps):
            # 发送思考事件
            self._emit(AgentEvent(
                type=EventType.THOUGHT,
                content=f"开始第 {step + 1} 步推理",
                step=step
            ))
            
            # 调用 LLM
            try:
                content = self._llm.chat(
                    messages, 
                    stream_callback=self._on_stream
                )
            except Exception as e:
                self._emit_error(e, step)
                return f"LLM 调用失败：{str(e)}"
            
            # 检查是否有最终答案
            if "<final_answer>" in content:
                final_match = re.search(r"<final_answer>(.*?)</final_answer>", content, re.DOTALL)
                if final_match:
                    final_answer = final_match.group(1).strip()
                    self._emit(AgentEvent(
                        type=EventType.FINAL,
                        content=final_answer,
                        step=step
                    ))
                    
                    # 保存到记忆
                    if self._memory:
                        self._memory.add(ChatMessage(role="assistant", content=content))
                    
                    return final_answer
            
            # 解析动作
            action_match = re.search(r"<action>(.*?)</action>", content, re.DOTALL)
            if not action_match:
                # 解析失败，让模型重试
                error_msg = "模型未输出 <action>，请重新尝试。"
                messages.append(ChatMessage(role="assistant", content=content))
                messages.append(ChatMessage(role="user", content=f"<observation>{error_msg}</observation>"))
                self._emit(AgentEvent(
                    type=EventType.ERROR,
                    content=error_msg,
                    step=step
                ))
                continue
            
            action_text = action_match.group(1).strip()
            tool_name, args = self._parse_action(action_text)
            
            self._emit(AgentEvent(
                type=EventType.ACTION,
                content=f"{tool_name}({', '.join(str(a) for a in args)})",
                step=step,
                metadata={"tool_name": tool_name, "args": args}
            ))
            
            # 权限检查
            tool_spec = self._registry.get(tool_name)
            if not tool_spec:
                observation = f"工具 '{tool_name}' 不存在。可用工具：{', '.join(self._registry.list_names())}"
            else:
                decision = self._permissions.check(tool_spec)
                
                if decision == PermissionDecision.DENY:
                    observation = f"工具 '{tool_name}' 的执行被权限策略拒绝"
                elif decision == PermissionDecision.CONFIRM:
                    # 需要用户确认
                    if user_input_callback:
                        confirm = user_input_callback(f"是否执行工具 {tool_name}？")
                        if confirm.lower() != 'y':
                            observation = "操作被用户取消"
                        else:
                            observation = self._registry.invoke(tool_name, tuple(args))
                    else:
                        observation = f"工具 '{tool_name}' 需要确认，但未提供用户输入回调"
                else:
                    # ALLOW
                    observation = self._registry.invoke(tool_name, tuple(args))
            
            # 截断 observation
            if len(observation) > self._config.observe_max_chars:
                observation = observation[:self._config.observe_max_chars] + "... (已截断)"
            
            # 发送 observation 事件
            self._emit(AgentEvent(
                type=EventType.OBSERVATION,
                content=observation,
                step=step
            ))
            
            # 添加到消息历史
            messages.append(ChatMessage(role="assistant", content=content))
            messages.append(ChatMessage(role="user", content=f"<observation>{observation}</observation>"))
        
        # 达到最大步数
        return f"已达最大步数 {self._config.max_steps}，未完成任务"
    
    def _emit(self, event: AgentEvent) -> None:
        """触发事件。"""
        self._hooks.on_event(event)
    
    def _emit_error(self, error: Exception, step: int) -> None:
        """触发错误事件。"""
        self._hooks.on_error(error, step)
    
    def _on_stream(self, token: str) -> None:
        """流式输出回调。"""
        print(token, end="", flush=True)
    
    def _parse_action(self, action_str: str) -> tuple[str, list]:
        """解析动作字符串。
        
        格式：tool_name(arg1, arg2, ...)
        """
        # 简单解析：匹配 tool_name(args)
        match = re.match(r'(\w+)\((.*)\)', action_str, re.DOTALL)
        if not match:
            raise ValueError(f"无效的动作格式：{action_str}")
        
        tool_name = match.group(1)
        args_str = match.group(2).strip()
        
        # 解析参数
        args = self._parse_args(args_str)
        
        return tool_name, args
    
    def _parse_args(self, args_str: str) -> list:
        """解析参数字符串。"""
        if not args_str:
            return []
        
        args = []
        current = ""
        in_string = False
        string_char = None
        paren_depth = 0
        
        for i, char in enumerate(args_str):
            if not in_string:
                if char in ['"', "'"]:
                    in_string = True
                    string_char = char
                    current += char
                elif char == '(':
                    paren_depth += 1
                    current += char
                elif char == ')':
                    paren_depth -= 1
                    current += char
                elif char == ',' and paren_depth == 0:
                    args.append(self._parse_single_arg(current.strip()))
                    current = ""
                else:
                    current += char
            else:
                current += char
                if char == string_char and (i == 0 or args_str[i - 1] != '\\'):
                    in_string = False
                    string_char = None
        
        if current.strip():
            args.append(self._parse_single_arg(current.strip()))
        
        return args
    
    def _parse_single_arg(self, arg_str: str):
        """解析单个参数。"""
        arg_str = arg_str.strip()
        
        # 字符串字面量
        if (arg_str.startswith('"') and arg_str.endswith('"')) or \
           (arg_str.startswith("'") and arg_str.endswith("'")):
            return arg_str[1:-1]
        
        # 数字
        try:
            if '.' in arg_str:
                return float(arg_str)
            return int(arg_str)
        except ValueError:
            pass
        
        # 布尔值
        if arg_str.lower() in ('true', 'false'):
            return arg_str.lower() == 'true'
        
        # 默认返回字符串
        return arg_str
