# LangChain 短期记忆（Short-term Memory）知识点总结

## 1. 核心概念

### 记忆在 LangChain 中的作用
- **对话连贯性**：保持对话的上下文连续性，使智能体能够理解用户的后续问题
- **状态维护**：维护对话的状态，记录用户的偏好和需求
- **个性化交互**：基于历史交互为用户提供个性化的回应
- **学习能力**：从用户的反馈中学习，改进后续的响应

### 短期记忆与长期记忆的区别
| 特性 | 短期记忆 | 长期记忆 |
|------|----------|----------|
| 存储方式 | 内存缓存 | 持久化存储（数据库、文件等） |
| 生命周期 | 会话期间 | 跨越多个会话 |
| 存储容量 | 有限（受模型上下文长度限制） | 较大（理论上无限） |
| 访问速度 | 快速 | 相对较慢 |
| 主要用途 | 维护当前对话的上下文 | 存储长期知识和用户偏好 |

### 短期记忆的基本原理
- **存储机制**：将对话历史存储在内存中的数据结构（如列表）中
- **检索机制**：当需要时，将记忆内容格式化为模型可以理解的格式
- **更新机制**：每次交互后更新记忆内容
- **限制机制**：通过各种策略限制记忆长度，以适应模型的上下文窗口

### 记忆与对话历史的关系
- **对话历史**：是用户和智能体之间所有交互的记录
- **记忆**：是对话历史的管理系统，负责存储、检索和更新对话历史
- **格式转换**：记忆将对话历史转换为模型可以处理的格式
- **内容筛选**：记忆决定哪些对话内容应该被保留和传递给模型

## 2. 短期记忆类型

### ConversationBufferMemory（对话缓冲区记忆）
- **特点**：简单地将所有对话历史存储在缓冲区中
- **适用场景**：对话较短，不需要限制记忆长度的场景
- **示例**：
  ```python
  from langchain.memory import ConversationBufferMemory

  memory = ConversationBufferMemory()
  memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
  memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架"})
  
  print(memory.load_memory_variables({}))
  # 输出: {"history": "Human: 你好\nAI: 你好，有什么可以帮助你的？\nHuman: 什么是 LangChain？\nAI: LangChain 是一个用于构建 LLM 应用的框架"}
  ```

### ConversationBufferWindowMemory（对话窗口记忆）
- **特点**：只保留最近的 N 轮对话
- **适用场景**：对话较长，需要限制记忆长度的场景
- **参数**：
  - `k`：要保留的最近对话轮数
- **示例**：
  ```python
  from langchain.memory import ConversationBufferWindowMemory

  memory = ConversationBufferWindowMemory(k=2)  # 只保留最近 2 轮对话
  memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
  memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架"})
  memory.save_context({"input": "它有哪些功能？"}, {"output": "它提供了模型、提示、记忆、工具等组件"})
  
  print(memory.load_memory_variables({}))
  # 输出: {"history": "Human: 什么是 LangChain？\nAI: LangChain 是一个用于构建 LLM 应用的框架\nHuman: 它有哪些功能？\nAI: 它提供了模型、提示、记忆、工具等组件"}
  ```

### ConversationTokenBufferMemory（对话令牌缓冲区记忆）
- **特点**：根据令牌（token）数量限制记忆长度
- **适用场景**：需要精确控制输入到模型的令牌数量的场景
- **参数**：
  - `max_token_limit`：最大令牌数量
- **示例**：
  ```python
  from langchain.memory import ConversationTokenBufferMemory
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(model="gpt-3.5-turbo")
  memory = ConversationTokenBufferMemory(
      llm=model,
      max_token_limit=100  # 最大令牌数量为 100
  )
  memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
  memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架，它提供了模型、提示、记忆、工具等组件"})
  
  print(memory.load_memory_variables({}))
  # 输出: 只包含不超过 100 令牌的对话内容
  ```

### ConversationSummaryMemory（对话摘要记忆）
- **特点**：将对话历史总结为一个摘要
- **适用场景**：对话较长，需要压缩记忆内容的场景
- **参数**：
  - `llm`：用于生成摘要的语言模型
- **示例**：
  ```python
  from langchain.memory import ConversationSummaryMemory
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(model="gpt-3.5-turbo")
  memory = ConversationSummaryMemory(llm=model)
  memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
  memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架"})
  memory.save_context({"input": "它有哪些功能？"}, {"output": "它提供了模型、提示、记忆、工具等组件"})
  
  print(memory.load_memory_variables({}))
  # 输出: {"history": "The human greeted the AI, and the AI responded. The human asked what LangChain is, and the AI explained it's a framework for building LLM applications. The human then asked about its features, and the AI listed components like models, prompts, memory, and tools."}
  ```

### ConversationSummaryBufferMemory（对话摘要缓冲区记忆）
- **特点**：结合了摘要和缓冲区的优点，保留最近的对话并对早期对话进行摘要
- **适用场景**：长对话，需要平衡详细度和长度的场景
- **参数**：
  - `llm`：用于生成摘要的语言模型
  - `max_token_limit`：最大令牌数量
- **示例**：
  ```python
  from langchain.memory import ConversationSummaryBufferMemory
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(model="gpt-3.5-turbo")
  memory = ConversationSummaryBufferMemory(
      llm=model,
      max_token_limit=200  # 最大令牌数量为 200
  )
  memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
  memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架"})
  memory.save_context({"input": "它有哪些功能？"}, {"output": "它提供了模型、提示、记忆、工具等组件"})
  memory.save_context({"input": "如何使用它？"}, {"output": "你可以通过安装 langchain 包并导入相应的模块来使用它"})
  
  print(memory.load_memory_variables({}))
  # 输出: 包含最近的对话和早期对话的摘要
  ```

## 3. 记忆的实现方法

### 基本记忆的创建和配置
- **创建记忆对象**：实例化相应的记忆类
- **配置参数**：根据需要设置记忆的参数
- **集成到链中**：将记忆对象传递给链或智能体

### 记忆的保存和加载
- **保存上下文**：使用 `save_context` 方法保存对话上下文
- **加载记忆**：使用 `load_memory_variables` 方法加载记忆内容
- **获取历史**：使用 `get_history` 方法获取完整的对话历史

### 记忆的清空和重置
- **清空记忆**：使用 `clear` 方法清空记忆内容
- **重置记忆**：创建新的记忆对象或调用 `clear` 方法

### 记忆的序列化和反序列化
- **序列化**：将记忆内容转换为可存储的格式
- **反序列化**：将存储的格式转换回记忆对象
- **示例**：
  ```python
  import pickle
  from langchain.memory import ConversationBufferMemory

  # 创建并使用记忆
  memory = ConversationBufferMemory()
  memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})

  # 序列化
  with open("memory.pkl", "wb") as f:
      pickle.dump(memory, f)

  # 反序列化
  with open("memory.pkl", "rb") as f:
      loaded_memory = pickle.load(f)

  print(loaded_memory.load_memory_variables({}))
  ```

## 4. 记忆与智能体

### 智能体如何使用记忆
- **决策依据**：智能体根据记忆中的对话历史做出决策
- **工具选择**：智能体参考记忆中的历史工具使用情况选择合适的工具
- **响应生成**：智能体基于记忆中的上下文生成连贯的响应

### 记忆在智能体决策中的作用
- **上下文理解**：记忆帮助智能体理解当前对话的上下文
- **意图识别**：记忆帮助智能体识别用户的长期意图
- **一致性保证**：记忆确保智能体的响应与之前的交互保持一致

### 记忆与工具的交互
- **工具调用记录**：记忆存储智能体之前的工具调用记录
- **工具结果利用**：智能体利用记忆中的工具结果进行后续决策
- **工具使用优化**：智能体根据记忆中的工具使用效果优化工具选择

### 工具访问记忆
- **工具获取记忆**：工具可以访问和使用记忆中的内容
- **记忆作为工具参数**：将记忆内容作为工具的输入参数
- **工具更新记忆**：工具可以修改或更新记忆内容
- **示例**：
  ```python
  from langchain_core.tools import tool
  from langchain.memory import ConversationBufferMemory

  # 创建记忆
  memory = ConversationBufferMemory()

  @tool
  def recall_memory() -> str:
      """回忆对话历史
      
      Returns:
          str: 对话历史的摘要
      """
      memory_content = memory.load_memory_variables({})["history"]
      if not memory_content:
          return "没有对话历史"
      return f"对话历史: {memory_content[:100]}..."

  @tool
  def clear_memory() -> str:
      """清空对话记忆
      
      Returns:
          str: 操作结果
      """
      memory.clear()
      return "对话记忆已清空"

  @tool
  def save_to_memory(content: str) -> str:
      """保存内容到记忆
      
      Args:
          content: 要保存的内容
      
      Returns:
          str: 操作结果
      """
      memory.save_context({"input": "保存内容"}, {"output": content})
      return f"内容已保存到记忆: {content}"
  ```

### 记忆与消息的集成
- **消息格式**：记忆将消息转换为模型可以理解的格式
- **消息顺序**：记忆保持消息的正确顺序
- **消息过滤**：记忆过滤掉不必要的消息，保留重要信息

## 5. 记忆与对话

### 对话历史的构建和管理
- **历史构建**：记忆逐步构建对话历史
- **历史管理**：记忆根据配置管理对话历史的长度和内容
- **历史检索**：记忆提供接口检索对话历史

### 记忆对对话连贯性的影响
- **上下文保持**：记忆确保对话的上下文连贯
- **指代解析**：记忆帮助智能体理解用户的指代（如 "它"、"那个" 等）
- **话题跟踪**：记忆帮助智能体跟踪对话的话题变化

### 长对话的记忆管理
- **长度控制**：使用窗口记忆或令牌缓冲区记忆控制记忆长度
- **内容压缩**：使用摘要记忆压缩记忆内容
- **重点保留**：确保重要信息不被丢失

### 多轮对话的记忆优化
- **记忆选择**：根据对话类型选择合适的记忆类型
- **参数调优**：根据对话长度和复杂度调优记忆参数
- **性能平衡**：平衡记忆的详细度和模型的处理能力

## 6. 记忆的参数配置

### 记忆长度的设置
- **轮数限制**：使用 `k` 参数设置保留的对话轮数
- **令牌限制**：使用 `max_token_limit` 参数设置最大令牌数量
- **动态调整**：根据对话情况动态调整记忆长度

### 记忆清理策略
- **自动清理**：当记忆达到限制时自动清理旧内容
- **优先级清理**：根据内容的重要性决定清理顺序
- **定期清理**：定期清理不相关的记忆内容

### 记忆编码方式
- **文本编码**：将记忆内容编码为文本格式
- **结构化编码**：将记忆内容编码为结构化格式
- **压缩编码**：将记忆内容压缩以减少存储空间

### 记忆检索策略
- **全量检索**：检索所有记忆内容
- **部分检索**：根据需要检索部分记忆内容
- **关键词检索**：根据关键词检索相关记忆内容

## 7. 最佳实践

### 不同场景下的记忆选择
| 场景 | 推荐记忆类型 | 原因 |
|------|--------------|------|
| 短对话 | ConversationBufferMemory | 简单直接，无需限制 |
| 中长对话 | ConversationBufferWindowMemory | 限制记忆长度，保持相关性 |
| 长对话 | ConversationSummaryBufferMemory | 平衡详细度和长度 |
| 令牌敏感 | ConversationTokenBufferMemory | 精确控制令牌数量 |
| 需要摘要 | ConversationSummaryMemory | 压缩记忆内容 |

### 记忆性能优化
- **选择合适的记忆类型**：根据对话长度和复杂度选择合适的记忆类型
- **优化参数设置**：根据模型的上下文窗口大小调整记忆参数
- **避免冗余信息**：确保记忆内容简洁有效
- **使用异步处理**：对于需要生成摘要的记忆，使用异步处理提高性能

### 记忆与提示的配合
- **提示设计**：设计适合记忆的提示模板
- **记忆集成**：将记忆内容自然地集成到提示中
- **提示优化**：根据记忆内容优化提示结构

### 记忆的安全性考虑
- **敏感信息处理**：避免在记忆中存储敏感信息
- **隐私保护**：确保记忆内容的隐私性
- **访问控制**：控制对记忆内容的访问权限

## 8. 常见模式

### 长对话记忆管理模式
启用短期记忆后，长对话可能会超出 LLM 的上下文窗口。常见的解决方案有：

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| 修剪消息 (Trim messages) ✂️ | 移除最初或最后的 N 条消息（在调用 LLM 之前） | 对话较长但只需要最近信息的场景 |
| 删除消息 (Delete messages) 🗑️ | 从 LangGraph 状态中永久删除消息 | 需要彻底清理旧对话的场景 |
| 总结消息 (Summarize messages) 📝 | 总结历史记录中较早的消息，并用摘要替换它们 | 需要保留对话要点但减少长度的场景 |
| 自定义策略 (Custom strategies) ⚙️ | 自定义策略（例如：消息过滤等） | 需要特定记忆管理逻辑的场景 |

### 模式实现示例

#### 1. 修剪消息
```python
from langchain.memory import ConversationBufferWindowMemory

# 只保留最近 3 轮对话
memory = ConversationBufferWindowMemory(k=3)
```

#### 2. 删除消息
```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
# 保存对话
memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
# 清空记忆（删除所有消息）
memory.clear()
```

#### 3. 总结消息
```python
from langchain.memory import ConversationSummaryMemory
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-3.5-turbo")
# 使用摘要记忆
memory = ConversationSummaryMemory(llm=model)
```

#### 4. 自定义策略
```python
from langchain.memory import BaseMemory
from typing import Dict, Any, List

class CustomMemory(BaseMemory):
    """自定义记忆策略"""
    
    def __init__(self):
        self.messages = []
    
    @property
    def memory_variables(self) -> List[str]:
        return ["history"]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # 自定义加载逻辑：只返回包含关键词的消息
        filtered_messages = [msg for msg in self.messages if "重要" in msg]
        return {"history": "\n".join(filtered_messages)}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        # 自定义保存逻辑：只保存长度大于 10 的消息
        if len(inputs.get("input", "")) > 10:
            self.messages.append(f"Human: {inputs['input']}")
        if len(outputs.get("output", "")) > 10:
            self.messages.append(f"AI: {outputs['output']}")
    
    def clear(self):
        self.messages = []
```

## 9. 常见问题

### 记忆溢出问题
- **症状**：记忆内容超过模型的上下文窗口
- **原因**：对话过长或记忆设置不当
- **解决方案**：
  - 使用窗口记忆或令牌缓冲区记忆
  - 增加模型的上下文窗口大小
  - 定期清理记忆内容

### 记忆更新不及时
- **症状**：智能体的响应与最新的对话内容不一致
- **原因**：记忆更新机制故障或延迟
- **解决方案**：
  - 确保每次交互后都调用 `save_context`
  - 检查记忆的更新逻辑
  - 使用同步更新机制

### 记忆与模型上下文长度的冲突
- **症状**：记忆内容加上新的输入超过模型的上下文长度
- **原因**：记忆长度设置过大或模型上下文窗口过小
- **解决方案**：
  - 调整记忆的长度限制
  - 使用摘要记忆压缩内容
  - 选择上下文窗口更大的模型

### 记忆内容的隐私保护
- **症状**：记忆中存储了敏感的用户信息
- **原因**：记忆无差别存储所有对话内容
- **解决方案**：
  - 在存储前过滤敏感信息
  - 使用加密存储记忆内容
  - 定期清理包含敏感信息的记忆

## 10. 代码示例

### 各种短期记忆的创建和使用示例
```python
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationTokenBufferMemory,
    ConversationSummaryMemory,
    ConversationSummaryBufferMemory
)
from langchain_openai import ChatOpenAI

# 初始化模型
model = ChatOpenAI(model="gpt-3.5-turbo")

# 1. ConversationBufferMemory
print("=== ConversationBufferMemory ===")
buffer_memory = ConversationBufferMemory()
buffer_memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
buffer_memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架"})
print(buffer_memory.load_memory_variables({}))

# 2. ConversationBufferWindowMemory
print("\n=== ConversationBufferWindowMemory ===")
window_memory = ConversationBufferWindowMemory(k=2)
window_memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
window_memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架"})
window_memory.save_context({"input": "它有哪些功能？"}, {"output": "它提供了模型、提示、记忆、工具等组件"})
print(window_memory.load_memory_variables({}))

# 3. ConversationTokenBufferMemory
print("\n=== ConversationTokenBufferMemory ===")
token_memory = ConversationTokenBufferMemory(llm=model, max_token_limit=100)
token_memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
token_memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架，它提供了模型、提示、记忆、工具等组件"})
print(token_memory.load_memory_variables({}))

# 4. ConversationSummaryMemory
print("\n=== ConversationSummaryMemory ===")
summary_memory = ConversationSummaryMemory(llm=model)
summary_memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
summary_memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架"})
summary_memory.save_context({"input": "它有哪些功能？"}, {"output": "它提供了模型、提示、记忆、工具等组件"})
print(summary_memory.load_memory_variables({}))

# 5. ConversationSummaryBufferMemory
print("\n=== ConversationSummaryBufferMemory ===")
summary_buffer_memory = ConversationSummaryBufferMemory(llm=model, max_token_limit=200)
summary_buffer_memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
summary_buffer_memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架"})
summary_buffer_memory.save_context({"input": "它有哪些功能？"}, {"output": "它提供了模型、提示、记忆、工具等组件"})
summary_buffer_memory.save_context({"input": "如何使用它？"}, {"output": "你可以通过安装 langchain 包并导入相应的模块来使用它"})
print(summary_buffer_memory.load_memory_variables({}))
```

### 记忆与智能体的集成示例
```python
from langchain.agents import create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

# 初始化模型
model = ChatOpenAI(model="gpt-3.5-turbo")

# 创建记忆
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# 创建提示
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个 helpful 的助手"),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("ai", "{agent_scratchpad}")
])

# 创建工具
from langchain_core.tools import tool

@tool
def calculate(a: int, b: int, operation: str) -> str:
    """执行数学运算
    
    Args:
        a: 第一个数字
        b: 第二个数字
        operation: 运算类型 (add, subtract, multiply, divide)
    """
    if operation == "add":
        return str(a + b)
    elif operation == "subtract":
        return str(a - b)
    elif operation == "multiply":
        return str(a * b)
    elif operation == "divide":
        if b == 0:
            return "Error: Division by zero"
        return str(a / b)
    else:
        return f"Error: Unknown operation {operation}"

tools = [calculate]

# 创建智能体
agent = create_openai_functions_agent(model, tools, prompt)

# 测试智能体与记忆的集成
print("=== 测试智能体与记忆的集成 ===")

# 第一轮对话
result = agent.invoke({
    "input": "5 加 3 等于多少？",
    "chat_history": memory.load_memory_variables({})["chat_history"]
})
print(f"AI: {result['output']}")

# 保存到记忆
memory.save_context({"input": "5 加 3 等于多少？"}, {"output": result['output']})

# 第二轮对话（测试记忆）
result = agent.invoke({
    "input": "刚才的结果乘以 2 是多少？",
    "chat_history": memory.load_memory_variables({})["chat_history"]
})
print(f"AI: {result['output']}")

# 保存到记忆
memory.save_context({"input": "刚才的结果乘以 2 是多少？"}, {"output": result['output']})
```

### 记忆参数调优示例
```python
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI

# 初始化模型
model = ChatOpenAI(model="gpt-3.5-turbo")

# 测试不同的 max_token_limit 值
print("=== 测试不同的 max_token_limit 值 ===")

for max_tokens in [100, 200, 300]:
    print(f"\nmax_token_limit = {max_tokens}:")
    memory = ConversationSummaryBufferMemory(
        llm=model,
        max_token_limit=max_tokens
    )
    
    # 模拟多轮对话
    for i in range(5):
        memory.save_context(
            {"input": f"问题 {i+1}: 什么是 LangChain？"},
            {"output": f"回答 {i+1}: LangChain 是一个用于构建 LLM 应用的框架，它提供了模型、提示、记忆、工具等组件。"}
        )
    
    memory_content = memory.load_memory_variables({})["history"]
    print(f"记忆内容长度: {len(memory_content)}")
    print(f"记忆内容: {memory_content[:100]}...")

# 测试不同的摘要模型
print("\n=== 测试不同的摘要模型 ===")

models = ["gpt-3.5-turbo", "gpt-4"]
for model_name in models:
    print(f"\n使用模型: {model_name}:")
    model = ChatOpenAI(model=model_name)
    memory = ConversationSummaryMemory(llm=model)
    
    memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
    memory.save_context({"input": "什么是 LangChain？"}, {"output": "LangChain 是一个用于构建 LLM 应用的框架"})
    memory.save_context({"input": "它有哪些功能？"}, {"output": "它提供了模型、提示、记忆、工具等组件"})
    
    summary = memory.load_memory_variables({})["history"]
    print(f"摘要内容: {summary}")
```

## 11. 高级用法

### 自定义记忆实现
- **继承 BaseMemory 类**：创建自定义的记忆类
- **实现必要方法**：实现 `load_memory_variables` 和 `save_context` 方法
- **添加自定义功能**：根据需要添加自定义功能

### 记忆与向量存储的结合
- **向量记忆**：将记忆内容转换为向量存储
- **相似度搜索**：根据相似度检索相关的记忆内容
- **混合记忆**：结合传统记忆和向量存储的优点

### 多模态记忆管理
- **文本记忆**：存储文本对话内容
- **图像记忆**：存储图像相关的信息
- **音频记忆**：存储音频相关的信息
- **多模态融合**：融合不同模态的记忆内容

### 记忆的动态调整策略
- **自适应记忆**：根据对话情况自动调整记忆策略
- **上下文感知**：根据当前上下文调整记忆内容
- **个性化记忆**：根据用户特点调整记忆管理策略