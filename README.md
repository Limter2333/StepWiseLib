# StepWiseLib-SoftSpace

一个可扩展的 ReAct Agent 框架，支持工具调用、RAG 检索、权限控制和可观测性。

## 一、项目结构

```
.
├── agent.py              # Agent 入口脚本
├── config.yaml           # 全局配置文件
├── pyproject.toml        # 项目配置与依赖
├── uv.lock              # 依赖锁定文件
├── harness/             # 核心框架
│   ├── __init__.py      # 统一导出
│   ├── config.py        # 配置管理
│   ├── events.py        # 事件定义
│   ├── agent.py         # AgentRunner 核心循环
│   ├── permissions.py   # 权限管理
│   ├── hooks.py         # 钩子机制
│   ├── observability.py # 可观测性
│   ├── llm/             # LLM 抽象层
│   │   ├── __init__.py
│   │   ├── base.py      # BaseLLMClient 抽象
│   │   └── openai_client.py  # OpenAI 兼容实现
│   ├── tools/           # 工具层
│   │   ├── __init__.py
│   │   ├── base.py      # ToolSpec + @tool 装饰器
│   │   ├── registry.py  # ToolRegistry 工具注册表
│   │   └── builtin.py   # 内置工具
│   └── memory/          # 记忆管理
│       ├── __init__.py
│       ├── base.py      # MemoryProvider 抽象
│       └── short_term.py  # 滑动窗口记忆
├── rag/                 # RAG 检索模块
│   ├── __init__.py
│   ├── rag.py           # 向量检索实现
│   ├── doc.md           # 默认知识库
│   └── rag.ipynb        # 演示 notebook
└── tests/               # 单元测试
    ├── test_tools.py
    ├── test_config.py
    └── test_permissions.py
```

## 二、环境要求

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) 包管理工具

## 三、快速开始

1. 安装依赖

   ```bash
   pip install uv
   uv sync
   ```

2. 配置 API Key

   创建 `.env` 文件：

   ```dotenv
   # Zen Gateway API Key（必需）
   OPENCODE_ZEN_GETWAY=your_api_key
   ```

3. 运行 Agent

   ```bash
   uv run agent.py .
   ```

   输入任务即可开始对话。

## 四、架构设计

### 核心组件

- **LLM 抽象层** (`harness/llm/`)：支持切换不同的 LLM 后端
- **工具层** (`harness/tools/`)：声明式工具定义 + 自动注册
- **记忆管理** (`harness/memory/`)：滑动窗口 + 摘要压缩
- **权限控制** (`harness/permissions.py`)：工具级别的权限管理
- **可观测性** (`harness/observability.py`)：结构化日志 + 统计

### 工作流程

```
用户输入 → AgentRunner.run()
    ↓
构建消息历史
    ↓
┌─→ 调用 LLM → 解析响应
│   ↓
│  检查是否为 Final Answer
│   ↓
│  解析 Action → 权限检查 → 执行工具
│   ↓
│  截断 Observation → 添加到消息
│   ↓
└─── 继续循环（直到 Final Answer 或达到 max_steps）
```

### 可用工具

- `read_file(file_path)` - 读取文件
- `write_to_file(file_path, content)` - 写入文件
- `run_terminal_command(command)` - 执行命令（需确认）
- `retrieve(query)` - RAG 知识库检索

## 五、配置说明

配置文件 `config.yaml`：

```yaml
llm:
  model: deepseek-v4-flash-free
  base_url: https://opencode.ai/zen/v1
  api_key_env: OPENCODE_ZEN_GETWAY
  max_retries: 5
  timeout: 60.0

agent:
  max_steps: 15
  observe_max_chars: 4000
  working_dir: .
  require_confirm:
    - run_terminal_command

permissions:
  run_terminal_command: confirm
  write_to_file: confirm
```

## 六、扩展指南

### 添加新工具

```python
from harness.tools import tool

@tool(description="我的新工具", permission="safe")
def my_tool(param: str) -> str:
    """工具功能说明"""
    return f"结果: {param}"
```

### 添加钩子

```python
from harness.hooks import Hook
from harness.events import AgentEvent

class MyHook(Hook):
    def on_event(self, event: AgentEvent):
        print(f"事件: {event.type} - {event.content[:50]}")
```

### 切换 LLM

```python
from harness.llm import BaseLLMClient

class MyLLMClient(BaseLLMClient):
    def chat(self, messages, stream_callback=None):
        # 实现你的 LLM 调用逻辑
        pass
```

## 七、测试

```bash
uv run pytest tests/
```

## 八、RAG 知识库

`rag/doc.md` 为默认知识库，首次调用 `retrieve` 时自动建立索引。

更新知识库：

```python
from rag import get_retriever
get_retriever().index_document("rag/doc.md")
```

运行演示：

```bash
uv run --with jupyter jupyter lab rag/rag.ipynb
```
