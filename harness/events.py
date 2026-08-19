from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(Enum):
    """Agent 循环中的事件类型。

    这是整个 Harness 的「消息字典」：循环每产生一个动作都会发出对应事件，
    日志、Web UI、统计等外部监听者依靠它来区分不同阶段。
    """

    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL = "final"
    ERROR = "error"


@dataclass
class AgentEvent:
    """一条 Agent 运行轨迹上的节点记录。

    设计意图：让循环内部（agent.py）与外部消费者（日志/UI/统计）解耦。
    循环只负责"发出事件"，至于事件被打印、入库还是画成流程图，都与它无关。
    """

    type: EventType  # 事件类型，见 EventType
    content: str  # 事件内容，如思考文本、动作文本、观察结果
    step: int  # 事件发生在第几步，便于按步骤追踪
    metadata: dict = field(default_factory=dict)  # 预留扩展位，如 token 数、耗时等


@dataclass
class ToolCallResult:
    """一次工具调用的结果封装。

    用统一结构承接工具返回值（成功/失败都走同一通道），
    避免 AgentRunner 里到处用裸字符串+异常判断，逻辑更可控。
    """

    ok: bool  # 是否执行成功
    output: str  # 工具返回的文本结果（给模型作为 observation）
    tool_name: str = ""  # 被调用的工具名，便于统计与审计
    args: tuple = ()  # 实际传入的参数快照，便于复盘
    duration_ms: float = 0.0  # 耗时（毫秒），供观测层统计
    error: str | None = None  # 失败时的错误信息，成功时为 None