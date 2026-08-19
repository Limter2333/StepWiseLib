# StepWiseLib-SoftSpace → Harness 工程改造计划

> 目标：把「硬编码的单体 Agent 脚本」重构成「可复用、可扩展的 Agent 运行时框架（Harness）」。
> 参考范式：smolagents / Anthropic Agent Harness 设计模式，保持本项目「可学习」的克制风格，不过度工程化。

---

## 〇、目标架构总览

```
当前（单体）                         改造后（Harness）
agent.py(硬编码循环)        →        harness/agent.py (AgentRunner 通用循环)
tools.py(裸函数列表)        →        harness/tools/ (ToolSpec + @tool + Registry)
prompt_template.py(写死)    →        harness/prompt.py (可插拔 PromptProvider)
OpenAI(硬编码 client)       →        harness/llm/ (BaseLLMClient 抽象)
无内存管理                  →        harness/memory/ (短期压缩 + 长期持久化)
输入即 exit                 →        harness/interactive.py (多轮 CLI)
无日志                      →        harness/observability.py (trace + 统计)
配置硬编码                  →        config.yaml + harness/config.py
```

目标目录结构：

```
.
├── harness/
│   ├── __init__.py
│   ├── config.py          # 配置 dataclass，从 config.yaml 加载
│   ├── events.py          # AgentEvent / ToolCallResult 等数据类
│   ├── agent.py           # AgentRunner：通用 Thought-Action-Observation 循环
│   ├── prompt.py          # 提示词模板与渲染（当前 prompt_template.py 迁移至此）
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py        # BaseLLMClient 抽象 + ChatMessage
│   │   └── openai_client.py  # OpenAI/Zen 兼容实现（含流式与重试）
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py        # ToolSpec + @tool 装饰器 + schema 生成
│   │   ├── registry.py    # ToolRegistry：注册/发现/校验
│   │   └── builtin.py     # read_file / write_to_file / run_terminal_command
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── base.py        # MemoryProvider 抽象
│   │   ├── short_term.py  # 滑动窗口 + 摘要压缩
│   │   └── long_term.py   # 基于 rag 模块的向量记忆
│   ├── permissions.py     # PermissionPolicy：白名单/询问/自动放行
│   ├── hooks.py           # Hook 机制：on_step / on_tool_call / on_final
│   └── observability.py   # 结构化日志 + token 统计 + trace 记录
├── rag/                   # 保留不动，通过 @tool 注册为 harness 工具
├── agent.py               # 瘦身为入口：组装各组件并启动
├── prompt_template.py     # 删除（迁移到 harness/prompt.py）
├── tools.py               # 删除（迁移到 harness/tools/builtin.py）
├── config.yaml            # 新增：模型/限流/权限/记忆等配置
└── tests/                 # 新增：单元测试
```

---

## 一、Phase 1：基础抽象层（events / config）

### 目标
先定义数据契约，让后续所有模块依赖抽象而非具体实现。

### `harness/events.py`
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class EventType(Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL = "final"
    ERROR = "error"

@dataclass
class AgentEvent:
    type: EventType
    content: str
    step: int
    metadata: dict = field(default_factory=dict)

@dataclass
class ToolCallResult:
    ok: bool
    output: str
    tool_name: str = ""
    args: tuple = ()
    duration_ms: float = 0.0
    error: str | None = None
```

### `harness/config.py`
```python
from dataclasses import dataclass
import yaml

@dataclass
class LLMConfig:
    base_url: str = "https://opencode.ai/zen/v1"
    model: str = "deepseek-v4-flash-free"
    api_key_env: str = "OPENCODE_ZEN_GETWAY"
    max_retries: int = 5
    timeout: float = 60.0

@dataclass
class AgentConfig:
    max_steps: int = 15
    observe_max_chars: int = 4000      # observation 截断上限
    working_dir: str = "."
    require_confirm: list[str] = ...   # 需要询问的工具白名单

@dataclass
class HarnessConfig:
    llm: LLMConfig
    agent: AgentConfig
    # 从 config.yaml 加载
    @classmethod
    def from_yaml(cls, path: str) -> "HarnessConfig": ...
```

**验收**：`uv run python -c "from harness.config import HarnessConfig; print(HarnessConfig.from_yaml('config.yaml'))"` 能打印出正确配置。

---

## 二、Phase 2：工具层抽象（ToolSpec / @tool / Registry）

### 目标
替代 `tools.py` 的裸函数列表，实现「声明式工具 + 自动 schema + 参数校验」。

### `harness/tools/base.py`
```python
from dataclasses import dataclass, field
from typing import Callable, Any, get_type_hints
from pydantic import create_model, BaseModel, ValidationError

@dataclass
class ToolSpec:
    name: str
    description: str
    func: Callable
    parameters: dict                          # JSON Schema
    permission_level: str = "safe"            # safe / confirm / admin

    def validate(self, *args) -> tuple:
        """用 pydantic 动态生成的模型校验参数"""
        model = create_model(f"{self.name}_args", **self.parameters_fields)
        try:
            valid = model(*args)
        except ValidationError as e:
            raise ToolArgumentError(str(e))
        return tuple(valid.model_dump().values())

def tool(name: str = "", description: str = "",
         permission: str = "safe", **param_schema):
    """装饰器：把普通函数注册为 ToolSpec"""
    def decorator(func):
        return ToolSpec(
            name=name or func.__name__,
            description=description or func.__doc__,
            func=func,
            parameters=_auto_schema(func, param_schema),
            permission_level=permission,
        )
    return decorator
```

### `harness/tools/registry.py`
```python
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def auto_register(self, *specs: ToolSpec) -> None:
        for s in specs: self.register(s)

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]

    def invoke(self, name: str, args: tuple) -> ToolCallResult:
        spec = self._tools[name]
        validated = spec.validate(*args)
        return spec.func(*validated)

    def list_for_prompt(self) -> str:
        # 生成系统提示词里的工具列表（name + schema + description）
        ...
```

### `harness/tools/builtin.py`
把现有 `tools.py` 三个函数迁移为 `@tool`，并**补安全措施**：

```python
@tool(permission="safe")
def read_file(file_path: str) -> str:
    """读取文件内容。file_path 为绝对路径。"""
    ...

@tool(permission="confirm")          # 写文件需要确认
def write_to_file(file_path: str, content: str) -> str: ...

@tool(permission="admin", requires_confirm=True)
def run_terminal_command(command: str) -> str:
    """执行终端命令。加入超时与 shell=False 参数化（尽力而为）。"""
    import subprocess
    try:
        r = subprocess.run(command, shell=True, capture_output=True,
                           text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "命令执行超时（30s）"
    ...
```

**同时把 RAG 包装成工具**：
```python
from rag import retrieve as _retrieve
tool_retrieve = tool(name="retrieve", permission="safe")(_retrieve)
```

**验收**：`pytest tests/test_tools.py` 中，`read_file(123)` 应被参数校验拒绝，`run_terminal_command` 超时应有提示。

---

## 三、Phase 3：LLM 抽象（BaseLLMClient）

### 目标
把 `agent.py` 里的 `OpenAI` client、流式、429 重试抽成可替换的客户端。

### `harness/llm/base.py`
```python
from dataclasses import dataclass
from typing import Iterable

@dataclass
class ChatMessage:
    role: str            # system / user / assistant
    content: str

class BaseLLMClient(abc.ABC):
    @abc.abstractmethod
    def chat(self, messages: list[ChatMessage],
             stream_callback=None) -> str:
        """发起对话，可选流式回调，返回完整回复。内部处理重试。"""
```

### `harness/llm/openai_client.py`
```python
class OpenAIClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self._client = OpenAI(base_url=config.base_url,
                              api_key=os.getenv(config.api_key_env))
        self._cfg = config

    def chat(self, messages, stream_callback=None) -> str:
        for attempt in range(self._cfg.max_retries):
            try:
                stream = self._client.chat.completions.create(
                    model=self._cfg.model, messages=messages, stream=True)
                parts, full = [], ""
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        parts.append(chunk.choices[0].delta.content)
                        if stream_callback: stream_callback(parts[-1])
                return "".join(parts)
            except Exception as e:
                if getattr(e, "status_code", None) != 429 or attempt == self._cfg.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)   # 指数退避
```

**验收**：`AgentRunner` 只依赖 `BaseLLMClient`，换本地 `vLLM` 后端只需新增一个 client 类。

---

## 四、Phase 4：通用 AgentRunner（重构核心循环）

### 目标
把循环从 `agent.py` 抽出，支持 hooks、事件、截断、步数上限。

### `harness/agent.py`
```python
class AgentRunner:
    def __init__(self, llm: BaseLLMClient, registry: ToolRegistry,
                 prompt_provider, memory: MemoryProvider,
                 config: AgentConfig, hooks: list[Hook] = None):
        ...

    def run(self, task: str, permission_policy=None) -> str:
        messages = [system] + memory.history() + [user task]
        for step in range(self.config.max_steps):
            content = self.llm.chat(messages, stream_callback=...)
            event = self._parse(content, step)
            self._emit(event)
            if event.type == EventType.FINAL:
                memory.commit(messages)          # 记忆写回
                return event.content
            if event.type == EventType.ERROR:
                # 解析失败：把错误反馈给模型重试，而不是直接抛异常
                messages.append(assistant content)
                messages.append(user f"<observation>解析失败: ...</observation>")
                continue
            # 权限检查
            decision = permission_policy.check(spec)
            if decision == DENY:
                obs = "权限被拒绝，请换一种方式完成。"
            else:
                obs = registry.invoke(name, args)   # 执行工具
            obs = truncate(obs, config.observe_max_chars)   # 截断
            messages.append(user f"<observation>{obs}</observation>")
        return f"已达最大步数 {max_steps}，未完成任务"
```

### `harness/hooks.py`
```python
class Hook(abc.ABC):
    @abc.abstractmethod
    def on_event(self, event: AgentEvent): ...
    # 实现：on_step / on_tool_call / on_final，供 UI、日志、统计复用
```

**验收**：删除 `agent.py` 原循环后，用 10 行入口代码跑通同样的 `retrieve` 问答任务，且达到 `max_steps` 时会优雅退出而非死循环。

---

## 五、Phase 5：权限与安全层

### 目标
把「只有 terminal 需要确认」升级为统一的权限策略，并落地沙箱限制。

### `harness/permissions.py`
```python
class PermissionDecision(Enum):
    ALLOW = 0
    CONFIRM = 1
    DENY = 2

class PermissionPolicy:
    def __init__(self, rules: dict[str, str]):   # 工具名 -> 策略
        self.rules = rules

    def check(self, spec: ToolSpec) -> PermissionDecision:
        level = spec.permission_level
        if level == "admin":  return PermissionDecision.CONFIRM
        if level == "safe":   return PermissionDecision.ALLOW
        return PermissionDecision.DENY
```

### 沙箱约束（建议随 Phase 一起做）
- `read_file` / `write_to_file`：校验路径在 `working_dir` 内，越界直接拒绝
- `run_terminal_command`：白名单命令表（`ls`/`python`/`git`…）+ 30s 超时
- 所有工具统一走 `PermissionPolicy`，CLI 交互式确认复用现有 input 逻辑

---

## 六、Phase 6：记忆与上下文管理

### 目标
补上「短期上下文压缩」与「长期记忆持久化」，解决消息无限增长。

### `harness/memory/short_term.py`
```python
class SlidingWindowMemory(MemoryProvider):
    def __init__(self, max_messages=20, summarize_after=10, llm=None):
        ...
    def history(self) -> list[ChatMessage]:
        # 超长时：保留 system + 最近 N 条 + 一条「先前对话摘要」
    def commit(self, messages): ...
```
摘要逻辑：超过阈值时调用 LLM 把早期对话压缩成一段 `summary`，此后 prompt 携带 `先前对话摘要：...`。

### `harness/memory/long_term.py`
复用 `rag/` 的向量能力：
```python
class VectorMemory(MemoryProvider):
    def remember(self, fact: str):   # 写入向量库（新 collection: memory）
    def recall(self, query: str, top_k=3) -> str:  # 检索相关记忆注入 prompt
```
入口命令：`uv run python -m harness.memory.cli add "用户喜欢 Python"`，下次对话可召回。

---

## 七、Phase 7：可观测性

### `harness/observability.py`
```python
@dataclass
class StepRecord:
    step: int
    tool: str
    duration_ms: float
    token_estimate: int
    decision: str

class AgentLogger:
    def on_event(self, event): ...      # 结构化打印 / 写 JSONL
    def summarize(self) -> str:         # 汇总：步数、工具调用、耗时、预估成本
```

**实现要点**
- 每个 `AgentEvent` 打点：时间戳 + 类型 + 内容长度
- token 统计：`len(content) // 2` 估算中文，或从响应中读取 usage（zen 接口如支持）
- 运行结束输出总结：`共 4 步，调用工具 3 次，耗时 12.3s，预估输入 5k tokens`
- 可选：记录 trace 到 `output/traces/*.jsonl`

---

## 八、Phase 8：入口与多轮交互

### `agent.py` 瘦身（原 main）
```python
def main():
    cfg = HarnessConfig.from_yaml("config.yaml")
    llm = OpenAIClient(cfg.llm)
    registry = ToolRegistry(); registry.auto_register(*builtin_tools(), rag_tool)
    memory = SlidingWindowMemory(llm=llm)
    runner = AgentRunner(llm, registry, memory, cfg.agent, hooks=[AgentLogger()])
    while True:                       # 多轮对话
        task = input("请输入任务（quit 退出）：")
        if task.strip().lower() in ("quit", "exit"): break
        print(runner.run(task))
```

### `config.yaml`
```yaml
llm:
  model: deepseek-v4-flash-free
  base_url: https://opencode.ai/zen/v1
  api_key_env: OPENCODE_ZEN_GETWAY
  max_retries: 5
agent:
  max_steps: 15
  observe_max_chars: 4000
  working_dir: .
  require_confirm: [run_terminal_command]
permissions:
  run_terminal_command: confirm
  write_to_file: confirm
```

---

## 九、Phase 9：测试与评测

### 测试清单
| 文件 | 覆盖点 |
| --- | --- |
| `tests/test_tools.py` | 参数校验（类型错误、缺参）、路径沙箱越界拒绝 |
| `tests/test_actions.py` | 迁移现有 `parse_action`，覆盖多行字符串/转义/嵌套括号 |
| `tests/test_registry.py` | 注册冲突、未知工具报错 |
| `tests/test_memory.py` | 窗口滑动、摘要触发条件 |
| `tests/test_agent.py` | mock LLM：死循环达 max_steps、解析失败重试、权限拒绝 |

### 评测（可选）
- `eval/` 放 20 条任务，跑完后人工/LLM 打分，比较 prompt 版本差异
- 用 `AgentLogger.summarize()` 统计每次 run 的稳定指标（完成率、步数、成本）

---

## 十、改造顺序与工作量参考

| 阶段 | 内容 | 预计改动 | 依赖 |
| --- | --- | --- | --- |
| P1 | events / config | 新增 2 文件 | 无 |
| P2 | 工具层抽象 | 新增 tools/，删 tools.py | P1 |
| P3 | LLM 抽象 | 新增 llm/ | P1 |
| P4 | AgentRunner | 重写 agent.py 循环 | P1-P3 |
| P5 | 权限/安全 | 新增 permissions.py + 沙箱 | P2, P4 |
| P6 | 记忆 | 新增 memory/ | P3, P4 |
| P7 | 观测 | 新增 observability.py + hooks | P4 |
| P8 | 入口/多轮/配置 | 改 agent.py + config.yaml | 全部 |
| P9 | 测试 | 新增 tests/ | 全部 |

> 建议按 P1 → P9 顺序推进，每阶段结束以「验收」小项为准（均可 `uv run` 验证）。保持代码量与现有风格一致，避免引入过重框架（如 Celery、K8s 类），否则偏离「学习 Harness 原理」的初衷。

---

## 十一、补充：学习价值补全（本项目的灵魂）

| 阶段 | 内容 | 说明 |
| --- | --- | --- |
| P10 | 对比实验 | 同一任务分别跑 ReAct 与 Plan-and-Execute，输出对比记录（步数/正确率/成本），这是比任何文档都有效的原理教学 |
| P11 | 架构图 + 教学注释 | README 加 Mermaid 流程图；代码关键处补「为什么这样设计」的注释 |
| P12 | 原理解析文档 | 写一篇讲解 Agent 五大部件（模型/工具/记忆/规划/观测）如何协作的文章，配本项目代码示例 |

## 十二、补充：工程化补全

| 阶段 | 内容 | 说明 |
| --- | --- | --- |
| P13 | 工具链规范化 | 加 `ruff`（lint）+ `mypy`（类型检查），在 `pyproject.toml` 配好命令 |
| P14 | CI | GitHub Actions：push 时自动跑 lint + pytest |
| P15 | 打包入口 | `pyproject.toml` 配 `[project.scripts]`，让 `uv run agent <dir>` 直接运行，不再 `uv run agent.py` |
| P16 | `.env.example` | 提交一份占位配置，避免新人不知道要配什么 key |
| P17 | Dockerfile / devcontainer | 固定 Python 3.14 环境，避免依赖漂移 |

## 十三、补充：RAG 专项（计划只复用现有模块，未深入）

| 阶段 | 内容 | 说明 |
| --- | --- | --- |
| P18 | RAG 增强 | 分片加 overlap、BM25+向量混合检索、向量库落盘持久化（当前 `EphemeralClient` 每次重启重建索引） |

## 十四、补充：安全与健壮性

| 阶段 | 内容 | 说明 |
| --- | --- | --- |
| P19 | 优雅退出 | `Ctrl+C` 中断时正常收尾，不报丑陋堆栈 |
| P20 | 进程清理 | `run_terminal_command` 超时后清理子进程，防止僵尸进程 |

## 十五、补充：交互演示

| 阶段 | 内容 | 说明 |
| --- | --- | --- |
| P21 | Web UI | 可选 Gradio/Streamlit，可视化 Thought/Action 步骤，学习演示效果更好 |

## 十六、优先级建议

> 第一梯队：**P10 对比实验 + P13 工具链 + P14 CI + P18 RAG 持久化**
> 第二梯队：P16、P19、P20、P11、P12
> 第三梯队（可选）：P15、P17、P21

---

*本文档与 `MISSING_FEATURES.md` 配套：前者是「缺什么」，本文是「怎么改」。*
