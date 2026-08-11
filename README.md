# 一个简易的 ReAct 架构代码

基于 ReAct（Reasoning + Acting）范式的简易 Agent，支持通过工具调用完成任务，并内置 RAG 检索工具，可从本地知识库（`rag/doc.md`）检索相关信息辅助回答。

## 一、项目结构

```
.
├── agent.py           # ReAct Agent 主程序
├── tools.py           # 基础工具：读文件、写文件、执行终端命令
├── prompt_template.py # ReAct 系统提示词模板
├── pyproject.toml     # 项目配置与依赖声明
├── uv.lock            # 依赖锁定文件（uv sync 时按此还原版本）
└── rag/
    ├── __init__.py    # 导出 retrieve 工具
    ├── rag.py         # RAG 检索实现（索引 + 召回 + 重排）
    ├── doc.md         # 默认知识库文档
    └── rag.ipynb      # RAG 演示 notebook
```

## 二、环境要求

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) 包管理工具

## 三、环境配置

1. 安装 uv（若未安装）

   ```commandline
   pip install uv
   ```

2. 安装依赖

   ```commandline
   uv sync
   ```

   该命令会根据 `pyproject.toml` 和 `uv.lock` 创建虚拟环境并安装所有依赖。

3. 配置 API Key

   在项目根目录创建 `.env` 文件（已加入 `.gitignore`，不会提交）：

   ```dotenv
   # OpenRouter API Key：运行 agent.py 必需
   OPENROUTER_API_KEY=your_openrouter_api_key

   # Gemini API Key：运行 rag/rag.ipynb 演示时可选
   GEMINI_API_KEY=your_gemini_api_key
   ```

## 四、运行 Agent

```commandline
uv run agent.py <project_directory>
```

- `<project_directory>`：Agent 可操作的目标目录（绝对路径），运行时会列出该目录下文件
- 启动后输入任务，Agent 会自动选择工具完成
- Agent 可用的工具（见 `tools.py` 和 `rag/rag.py`）：
  - `read_file`：读取文件内容
  - `write_to_file`：写入文件
  - `run_terminal_command`：执行终端命令（执行前会请求确认）
  - `retrieve`：从本地知识库（`rag/doc.md`）检索相关片段

示例：询问知识库中的故事内容

```
$ uv run agent.py .
请输入任务：哆啦A梦使用的3个秘密道具分别是什么？
```

Agent 会通过 `retrieve` 工具检索知识库，再基于检索结果给出最终答案。

## 五、模型配置

Agent 默认通过 Zen-Gateway（`https://opencode.ai/zen/v1`）调用模型，模型与 API Key 可在 `agent.py` 中修改：

```python
agent = ReActAgent(tools=tools, model="deepseek-v4-flash-free", project_directory=project_dir)
```

## 六、更新知识库

`rag/doc.md` 为默认知识库，首次调用 `retrieve` 时自动建立索引。修改文档后需重新索引，可调用：

```python
from rag import get_retriever
get_retriever().index_document("rag/doc.md")
```

如需 RAG 检索流程演示，可运行 `rag/rag.ipynb`：

```commandline
uv run --with jupyter jupyter lab
```
