# StepWiseLib-SoftSpace 功能缺失分析

> 用途：作为学习 Agent 工作原理的 Demo，本项目已实现最基础的 **ReAct 循环 + 4 个工具 + RAG 检索**。本文按「Agent 工作原理」的完整框架，逐块列出缺失或薄弱的功能，供后续迭代学习。

---

## 〇、当前已具备的功能（基线）

| 模块 | 已实现 | 对应文件 |
| --- | --- | --- |
| ReAct 主循环 | Thought → Action → Observation → Final Answer | `agent.py` |
| LLM 调用 | OpenAI 兼容接口、流式输出、429 指数退避重试 | `agent.py` |
| 工具调用 | `read_file` / `write_to_file` / `run_terminal_command` | `tools.py` |
| RAG 检索 | 向量召回（sentence-transformers）+ CrossEncoder 重排 | `rag/rag.py` |
| 系统提示词 | ReAct 模板 + 工具列表 + 环境信息注入 | `prompt_template.py` |

---

## 一、Agent 核心循环（最优先补全）

| 缺失功能 | 说明 | 为什么需要 |
| --- | --- | --- |
| 1. 最大迭代步数限制 `max_steps` | 目前 `while True` 无上限，模型可能死循环 | 生产必须有的护栏，防止无限消耗 token |
| 2. 多轮对话 | `main()` 只处理一次输入即退出，无法连续对话 | 学习 Agent 需演示「连续上下文 + 追问」 |
| 3. 上下文窗口管理 | 消息列表无限增长，超长后直接超模型 token 上限 | 真实场景必须：截断 / 摘要 / 滑动窗口 |
| 4. Observation 截断 | 工具返回超长文本（如 `read_file` 大文件）全部塞回 prompt | 防止上下文爆炸，应截断并提示模型 |
| 5. 输出格式容错 | 模型不输出 `<action>` 直接抛 `RuntimeError` 终止 | 应支持「重试 + 修正提示」而非直接崩掉 |
| 6. 并行工具调用 | 每次只能执行一个工具 | ReAct 变体（如 ReWoo）支持多工具并行 |

---

## 二、记忆（Memory）

| 缺失功能 | 说明 |
| --- | --- |
| 短期记忆管理 | 仅靠 messages 数组，无会话历史持久化 / 压缩策略 |
| 长期记忆 | 无「跨会话持久化」的记忆（如 SQLite / 向量库存事实与偏好） |
| 记忆总结与遗忘 | 无 core-memory 管理、无过期清理 |
| 知识库写入 | 只能检索 `doc.md`，Agent 无法把新学到的东西写入知识库 |

---

## 三、规划与推理（Planning & Reasoning）

| 缺失功能 | 说明 |
| --- | --- |
| Plan-and-Execute 模式 | 先产出多步计划再逐步执行，区别于「走一步看一步」的 ReAct |
| 计划修正 / Re-planning | 执行失败时回退调整计划 |
| Reflection / 自我反思 | 执行后让模型评估自身答案并改进（Self-Refine） |
| 任务分解 | 复杂任务拆成子任务，无 CoT / ToT（思维树）演示 |

---

## 四、工具层（Tools）

| 缺失功能 | 说明 |
| --- | --- |
| 工具参数 Schema 校验 | 靠 `inspect.signature` 生成描述，但调用前不校验参数类型/必填 |
| 工具注册机制 | 手动写 `tools = [...]` 列表，无 `@tool` 装饰器 + 自动发现的模式 |
| Web 搜索 / 网页抓取 | 只有本地 RAG，无实时联网能力 |
| 代码解释器 | 无沙箱 Python 执行（`run_terminal_command` 有安全风险） |
| 数据库查询 | 无 SQL / 结构化数据查询工具 |
| 多模态工具 | 无图片/音频理解 |
| 更安全的终端执行 | `subprocess.run(shell=True)` 直接拼命令，无白名单/超时/沙箱 |

---

## 五、多 Agent 协作

| 缺失功能 | 说明 |
| --- | --- |
| 多 Agent 架构 | 无 Planner / Executor / Supervisor / Critic 等角色分工 |
| Agent 间通信 | 无消息总线或共享状态（如共享工作目录、共享记忆） |
| 团队协作模式 | 例如「Code Agent 写代码 + Review Agent 审查 + Test Agent 测试」 |

---

## 六、RAG 增强

| 缺失功能 | 说明 |
| --- | --- |
| 分片策略优化 | 目前按空行切分，无 chunk_size / overlap 控制 |
| 混合检索 | 无 BM25 + 向量检索融合（RAG Fusion） |
| 增量索引 | 文档变更需全量重建，无增量 update / upsert |
| 多知识库管理 | 单 collection，无法按知识库路由 |
| 嵌入模型缓存 | 每次进程启动重新加载模型，未持久化向量库到磁盘（`EphemeralClient`） |
| RAG 评估 | 无检索质量评估（hit rate / MRR） |

---

## 七、工程化与可靠性

| 缺失功能 | 说明 |
| --- | --- |
| 单元测试 | 无测试文件，`parse_action`、`retrieve`、工具函数均无用例 |
| 日志与可观测性 | 仅 `print`，无 structured log / trace / token 用量统计 |
| 配置管理 | 模型名、base_url、API key 硬编码在 `agent.py` |
| Prompt 版本管理 | 模板文件单一，无 A/B 评估 |
| 成本与限流控制 | 只有 429 重试，无并发限制 / 预算控制 |
| 沙箱安全 | 文件写入无路径限制，可越权写任意绝对路径 |

---

## 八、交互与前端

| 缺失功能 | 说明 |
| --- | --- |
| CLI 多轮交互循环 | 单次任务即退出，无法连续问答 |
| Web / 聊天界面 | 无 Gradio / Streamlit / FastAPI 接口 |
| 运行进度可视化 | Thought/Action 仅有文字打印，无状态机视图 |

---

## 九、建议的迭代路线（学习顺序）

1. **P0 补护栏**：`max_steps` 上限、`run()` 改为多轮循环、Observation 截断 → 体验立即变稳
2. **P1 结构化输出**：改用原生 Function Calling / JSON Schema，替换手写 XML 正则解析（学习价值高）
3. **P2 记忆**：短期记忆压缩 + 长期记忆持久化
4. **P3 规划**：Plan-and-Execute 与 ReAct 对比实现
5. **P4 多 Agent**：Executor/Reviewer 双角色协作
6. **P5 工程化**：测试、日志、配置化、Web UI

---

*文档由代码分析生成，供学习参考；具体功能取舍视学习目标而定。*
