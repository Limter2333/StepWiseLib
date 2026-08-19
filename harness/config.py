import os
from dataclasses import dataclass, field

import yaml


@dataclass
class LLMConfig:
    """LLM 客户端配置。

    设计意图：把 agent.py 里硬编码的模型名、base_url、API key 环境变量名
    全部抽到配置层，换模型/换网关时无需改代码。
    """

    base_url: str = "https://opencode.ai/zen/v1"
    model: str = "deepseek-v4-flash-free"
    api_key_env: str = "OPENCODE_ZEN_GETWAY"  # 从环境变量读取，key 不入库
    max_retries: int = 5  # 限流(429)重试次数，配合指数退避
    timeout: float = 60.0  # 单次请求超时（秒）


@dataclass
class AgentConfig:
    """Agent 运行参数。

    这里集中放置循环的"护栏"配置：步数上限、observation 截断长度等，
    都是防止模型失控把上下文/预算打爆的开关。
    """

    max_steps: int = 15  # 最大推理-行动步数，防止死循环
    observe_max_chars: int = 4000  # 工具返回文本的截断上限，防上下文爆炸
    working_dir: str = "."  # Agent 可操作的工作目录（后续沙箱校验的依据）
    require_confirm: list[str] = field(default_factory=list)  # 执行前需用户确认的工具名


@dataclass
class HarnessConfig:
    """顶层配置聚合：由 config.yaml 一次性构建出来供全项目使用。"""

    llm: LLMConfig = field(default_factory=LLMConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    permissions: dict[str, str] = field(default_factory=dict)  # 工具名 -> 权限级别，Phase5 使用

    @classmethod
    def from_yaml(cls, path: str) -> "HarnessConfig":
        """从 YAML 文件加载配置。

        - safe_load 只解析纯数据，不执行任何代码，避免恶意配置注入
        - or {} 保证空文件也能得到空 dict，而不是 None 导致下面的 .get 报错
        - **raw.get("llm", {})：把 YAML 的 llm 小节平铺成关键字参数，
          未写的字段自动落到 dataclass 默认值
        """
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return cls(
            llm=LLMConfig(**raw.get("llm", {})),
            agent=AgentConfig(**raw.get("agent", {})),
            permissions=raw.get("permissions", {}),
        )

    def resolve_working_dir(self) -> str:
        """把相对路径 working_dir 解析成绝对路径，统一沙箱校验的基准。"""
        return os.path.abspath(self.agent.working_dir)