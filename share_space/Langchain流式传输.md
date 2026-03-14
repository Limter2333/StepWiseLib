# LangChain 流式传输（Streaming）知识点补充

## 1. 核心概念

### 流式传输的基本定义和作用
- **定义**：流式传输是一种数据传输方式，允许模型在生成完整响应之前，逐步返回部分结果
- **作用**：
  - **实时更新**：用户可以实时看到模型的输出过程
  - **增强响应能力**：减少用户等待时间，提升交互体验
  - **渐进式显示**：逐字/逐句显示模型输出，模拟人类思考过程
  - **实时监控**：能够实时观察 LLM 和 Agent 的运行状态

### 流式传输与非流式传输的区别
| 特性 | 流式传输 | 非流式传输 |
|------|----------|------------|
| 响应方式 | 逐步返回部分结果 | 等待完整结果后一次性返回 |
| 等待时间 | 几乎实时开始显示 | 需等待全部处理完成 |
| 用户体验 | 更流畅，有交互感 | 可能有较长等待时间 |
| 内存消耗 | 较低（边生成边处理） | 较高（需存储完整结果） |
| 适用场景 | 对话式应用、实时交互 | 批处理、后台任务 |

### 流式传输的应用场景
- **对话机器人**：实时显示回复，提升用户体验
- **智能体系统**：实时展示思考过程和工具调用
- **长文本生成**：避免长时间无响应
- **实时数据处理**：如实时翻译、实时分析
- **交互式教学**：逐步展示解题过程

### 流式传输的优势和局限性
- **优势**：
  - 改善用户体验，减少等待感
  - 允许用户在生成过程中中断
  - 降低内存占用
  - 实时监控模型状态
- **局限性**：
  - 实现复杂度较高
  - 可能增加网络开销
  - 对前端处理要求更高
  - 某些复杂任务可能不适合流式处理

## 2. 流式传输类型

### Token 级流式传输（Token Streaming）
- **定义**：逐 token（词元）返回模型输出
- **特点**：最细粒度的流式传输，实时性最强
- **适用场景**：需要最实时反馈的场景，如聊天机器人
- **示例**：
  ```python
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)
  
  for chunk in model.stream("请解释什么是 LangChain"):
      print(chunk.content, end="", flush=True)
  ```

### 消息级流式传输（Message Streaming）
- **定义**：以完整消息为单位返回
- **特点**：粒度较粗，但更易于处理
- **适用场景**：结构化输出、多轮对话
- **示例**：
  ```python
  from langchain_openai import ChatOpenAI
  from langchain_core.messages import HumanMessage

  model = ChatOpenAI(model="gpt-3.5-turbo")
  
  # 使用 stream_mode="messages"
  for msg in model.stream([HumanMessage(content="请解释什么是 LangChain")], stream_mode="messages"):
      print(msg.content)
  ```

### 事件级流式传输（Event Streaming）
- **定义**：返回包含事件类型的流式数据
- **特点**：包含更多元数据，如思考过程、工具调用等
- **适用场景**：智能体系统、需要监控内部状态的场景
- **示例**：
  ```python
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(model="gpt-3.5-turbo")
  
  # 使用 stream_mode="updates"
  for event in model.stream("请解释什么是 LangChain", stream_mode="updates"):
      if "delta" in event:
          print(event["delta"].get("content", ""), end="", flush=True)
  ```

### 自定义流式传输（Custom Streaming）
- **定义**：根据特定需求自定义流式传输逻辑
- **特点**：高度灵活，可适应特定场景
- **适用场景**：特殊业务需求、多模态应用
- **示例**：
  ```python
  from langchain_openai import ChatOpenAI
  from langchain_core.callbacks import StreamingStdOutCallbackHandler

  # 自定义回调
  class CustomStreamingCallback(StreamingStdOutCallbackHandler):
      def on_llm_new_token(self, token: str, **kwargs) -> None:
          # 自定义处理逻辑
          print(f"[自定义] {token}", end="", flush=True)

  model = ChatOpenAI(
      model="gpt-3.5-turbo",
      streaming=True,
      callbacks=[CustomStreamingCallback()]
  )

  model.invoke("请解释什么是 LangChain")
  ```

## 3. 流式传输的实现方法

### 基本的流式传输配置
- **配置参数**：
  - `streaming`：是否启用流式传输
  - `stream_mode`：流式传输模式
    - `"updates"`：事件级流式传输，返回包含事件类型的流式数据
    - `"messages"`：消息级流式传输，以完整消息为单位返回
    - `"custom"`：自定义流式传输，允许用户完全控制流式逻辑
  - `callbacks`：回调函数列表
- **示例**：
  ```python
  from langchain_openai import ChatOpenAI

  # 基本流式配置
  model = ChatOpenAI(
      model="gpt-3.5-turbo",
      streaming=True,
      stream_mode="updates"
  )
  ```

### 流式传输模式详解
- **stream_mode="messages"**：消息级流式传输
  - **特点**：以完整消息为单位返回，粒度较粗但更易于处理
  - **适用场景**：结构化输出、多轮对话、需要完整消息的场景
  - **示例**：
    ```python
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    model = ChatOpenAI(model="gpt-3.5-turbo")
    
    # 使用 stream_mode="messages"
    for msg in model.stream([HumanMessage(content="请解释什么是 LangChain")], stream_mode="messages"):
        print(msg.content)
    ```

- **stream_mode="updates"**：事件级流式传输
  - **特点**：返回包含事件类型的流式数据，包含更多元数据
  - **适用场景**：智能体系统、需要监控内部状态的场景、实时反馈
  - **示例**：
    ```python
    from langchain_openai import ChatOpenAI

    model = ChatOpenAI(model="gpt-3.5-turbo")
    
    # 使用 stream_mode="updates"
    for event in model.stream("请解释什么是 LangChain", stream_mode="updates"):
        if "delta" in event:
            print(event["delta"].get("content", ""), end="", flush=True)
    ```

- **stream_mode="custom"**：自定义流式传输
  - **特点**：允许用户完全控制流式逻辑，高度灵活
  - **适用场景**：特殊业务需求、多模态应用、复杂交互场景
  - **示例**：
    ```python
    from langchain_openai import ChatOpenAI
    from langchain_core.callbacks import BaseCallbackHandler

    class CustomStreamingCallback(BaseCallbackHandler):
        def on_llm_new_token(self, token, **kwargs):
            # 自定义处理逻辑
            print(f"[自定义] {token}", end="", flush=True)

    model = ChatOpenAI(
        model="gpt-3.5-turbo",
        streaming=True,
        stream_mode="custom",
        callbacks=[CustomStreamingCallback()]
    )

    model.invoke("请解释什么是 LangChain")
    ```

### 流式传输回调函数（Callback）
- **内置回调**：
  - `StreamingStdOutCallbackHandler`：标准输出回调
  - `StreamingBytesCallbackHandler`：字节流回调
  - `AwaitableCallbackHandler`：可等待回调
- **自定义回调**：
  ```python
  from langchain_core.callbacks import BaseCallbackHandler

  class MyStreamingCallback(BaseCallbackHandler):
      def on_llm_start(self, serialized, prompts, **kwargs):
          print("开始生成...")
      
      def on_llm_new_token(self, token, **kwargs):
          print(token, end="", flush=True)
      
      def on_llm_end(self, response, **kwargs):
          print("\n生成完成！")

  # 使用自定义回调
  model = ChatOpenAI(
      model="gpt-3.5-turbo",
      streaming=True,
      callbacks=[MyStreamingCallback()]
  )
  ```

### 流式传输事件处理
- **事件类型**：
  - `start`：流式开始
  - `token`：新 token 生成
  - `end`：流式结束
  - `error`：错误事件
- **事件处理示例**：
  ```python
  def handle_streaming_events():
      events = []
      
      def on_event(event):
          events.append(event)
          if event["type"] == "token":
              print(event["data"], end="", flush=True)
          elif event["type"] == "end":
              print("\n流式结束")
          elif event["type"] == "error":
              print(f"\n错误: {event['data']}")
      
      return on_event, events

  on_event, events = handle_streaming_events()
  # 传递给流式方法
  ```

### 流式传输的停止和恢复
- **停止流式传输**：
  ```python
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)
  
  # 流式生成
  generator = model.stream("请写一个很长的故事")
  
  # 手动停止
  for i, chunk in enumerate(generator):
      print(chunk.content, end="", flush=True)
      if i > 10:  # 只获取前 10 个 chunk
          break
  ```

- **恢复流式传输**：
  - 流式传输一旦停止，通常需要重新开始
  - 可以通过保存状态来实现恢复

## 4. 流式传输与模型

### 模型如何支持流式传输
- **底层实现**：使用 Server-Sent Events (SSE) 或 WebSocket
- **API 支持**：大多数现代 LLM API 都支持流式传输
- **配置要求**：需要在模型初始化时启用流式选项

### 流式传输与同步/异步调用
- **同步流式**：
  ```python
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)
  
  # 同步流式
  for chunk in model.stream("请解释什么是 LangChain"):
      print(chunk.content, end="", flush=True)
  ```

- **异步流式**：
  ```python
  import asyncio
  from langchain_openai import ChatOpenAI

  async def async_stream():
      model = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)
      async for chunk in model.astream("请解释什么是 LangChain"):
          print(chunk.content, end="", flush=True)

  asyncio.run(async_stream())
  ```

### 不同模型提供商的流式传输支持
| 提供商 | 流式支持 | 特殊配置 |
|--------|----------|----------|
| OpenAI | ✅ 完全支持 | `stream=True` |
| Anthropic | ✅ 支持 | `stream=True` |
| Google Gemini | ✅ 支持 | `stream=True` |
| Mistral | ✅ 支持 | `stream=True` |
| Ollama | ✅ 支持 | `stream=True` |
| 本地模型 | 视实现而定 | 可能需要特殊配置 |

### 流式传输的性能优化
- **减少网络延迟**：使用更接近模型服务器的部署位置
- **批量处理**：适当调整 chunk 大小
- **压缩传输**：使用压缩减少网络带宽
- **缓存策略**：对重复内容使用缓存
- **并行处理**：在前端使用 Web Workers 处理流式数据

## 5. 流式传输与智能体

### 智能体的流式传输配置
- **基本配置**：
  ```python
  from langchain.agents import create_openai_functions_agent
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(
      model="gpt-3.5-turbo",
      streaming=True
  )

  # 创建智能体
  agent = create_openai_functions_agent(model, tools, prompt)
  ```

### 智能体思考过程的流式展示
- **思考过程流式**：
  ```python
  from langchain.agents import create_openai_functions_agent
  from langchain_core.prompts import ChatPromptTemplate

  # 包含思考过程的提示
  prompt = ChatPromptTemplate.from_messages([
      ("system", "你是一个 helpful 的助手，思考过程要清晰"),
      ("human", "{input}"),
      ("ai", "思考: {agent_scratchpad}\n回答:")
  ])

  agent = create_openai_functions_agent(model, tools, prompt)
  ```

### 工具调用的流式展示
- **工具调用流式**：
  ```python
  from langchain_core.tools import tool

  @tool
  def search(query: str) -> str:
      """搜索网络信息"""
      # 模拟搜索过程
      import time
      time.sleep(1)  # 模拟网络延迟
      return f"搜索结果: {query}"

  # 智能体使用工具时会流式展示工具调用过程
  ```

### 流式传输与智能体决策
- **实时决策**：流式传输允许观察智能体的决策过程
- **干预机制**：可以在决策过程中进行干预
- **透明度**：提高智能体行为的可解释性

## 6. 流式传输与记忆

### 记忆内容的流式访问
- **流式读取记忆**：
  ```python
  from langchain.memory import ConversationBufferMemory

  memory = ConversationBufferMemory()
  memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮助你的？"})
  
  # 流式访问记忆内容
  history = memory.load_memory_variables({})["history"]
  for line in history.split("\n"):
      print(line)
  ```

### 记忆更新的流式通知
- **实时通知**：当记忆更新时通过流式方式通知
- **状态同步**：确保前端显示的记忆与后端一致

### 长对话的流式处理
- **分段处理**：将长对话分成多个部分流式处理
- **摘要整合**：使用摘要记忆减少传输量

### 记忆状态的流式监控
- **实时监控**：监控记忆的使用情况和更新状态
- **容量管理**：当记忆接近容量限制时及时通知

## 7. 流式传输的 UI 集成

### Web 应用中的流式展示
- **JavaScript 示例**：
  ```javascript
  // 前端流式处理
  async function streamResponse() {
      const response = await fetch('/api/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: '请解释什么是 LangChain' })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let result = '';

      while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          result += chunk;
          document.getElementById('output').textContent = result;
      }
  }
  ```

### 移动端的流式展示
- **移动端优化**：
  - 使用 WebSocket 减少移动端网络波动影响
  - 实现离线缓存机制
  - 自适应屏幕大小的流式展示

### 流式传输的进度显示
- **进度指示器**：
  - 显示生成进度条
  - 估计剩余时间
  - 提供取消按钮

### 流式传输的错误处理 UI
- **错误展示**：
  - 优雅处理网络中断
  - 提供重试机制
  - 显示友好的错误信息

## 8. 最佳实践

### 不同场景下的流式传输选择
| 场景 | 推荐流式类型 | 原因 |
|------|--------------|------|
| 聊天机器人 | Token 级流式 | 实时性强，用户体验好 |
| 智能体系统 | 事件级流式 | 包含更多状态信息 |
| 长文本生成 | 消息级流式 | 减少网络开销 |
| 多模态应用 | 自定义流式 | 灵活处理不同类型数据 |

### 流式传输性能优化
- **网络优化**：
  - 使用 CDN 减少延迟
  - 启用 HTTP/2 或 HTTP/3
  - 压缩传输数据
- **客户端优化**：
  - 使用 Web Workers 处理流式数据
  - 实现节流（throttling）避免 UI 阻塞
  - 优化渲染性能

### 流式传输与用户体验
- **交互设计**：
  - 显示打字指示器
  - 提供实时反馈
  - 允许用户中断生成
- **视觉效果**：
  - 平滑的文本显示动画
  - 适当的暂停和分段
  - 清晰的错误状态指示

### 流式传输的错误处理策略
- **网络错误**：
  - 自动重试机制
  - 断点续传
  - 降级到非流式模式
- **模型错误**：
  - 优雅处理模型中断
  - 提供错误原因和建议
  - 保存部分结果

## 9. 常见问题

### 流式传输延迟问题
- **原因**：
  - 网络延迟
  - 模型处理速度
  - 服务器负载
- **解决方案**：
  - 使用更接近用户的服务器
  - 优化模型参数
  - 实现预加载机制

### 流式传输中断处理
- **原因**：
  - 网络中断
  - 服务器错误
  - 客户端崩溃
- **解决方案**：
  - 实现重连机制
  - 保存中间状态
  - 提供手动恢复选项

### 流式传输与内存管理
- **问题**：
  - 长时间流式传输导致内存增长
  - 大量并发流式连接
- **解决方案**：
  - 定期清理缓存
  - 限制单个流式连接的时间
  - 使用流式处理避免一次性加载大文件

### 流式传输的兼容性问题
- **问题**：
  - 旧浏览器不支持 SSE 或 WebSocket
  - 代理服务器拦截流式传输
- **解决方案**：
  - 提供非流式 fallback
  - 使用兼容的传输协议
  - 检测客户端能力并自适应

## 10. 代码示例

### 基本的流式传输示例
```python
from langchain_openai import ChatOpenAI

# 初始化模型
model = ChatOpenAI(
    model="gpt-3.5-turbo",
    streaming=True
)

# 流式生成
print("开始流式生成:")
for chunk in model.stream("请解释什么是 LangChain，以及它的主要组件"):
    print(chunk.content, end="", flush=True)
print("\n生成完成！")
```

### 智能体流式传输示例
```python
from langchain.agents import create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# 创建工具
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

# 初始化模型
model = ChatOpenAI(
    model="gpt-3.5-turbo",
    streaming=True
)

# 创建提示
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个 helpful 的助手，思考过程要清晰"),
    ("human", "{input}"),
    ("ai", "思考: {agent_scratchpad}\n回答:")
])

# 创建智能体
agent = create_openai_functions_agent(model, tools, prompt)

# 流式执行智能体
print("智能体开始思考:")
for chunk in agent.stream({"input": "5 加 3 等于多少，然后乘以 2"}):
    if "output" in chunk:
        print(chunk["output"], end="", flush=True)
print("\n智能体执行完成！")
```

### 自定义回调函数示例
```python
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler

# 自定义回调类
class CustomStreamingCallback(BaseCallbackHandler):
    def __init__(self):
        self.content = ""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        print("🔄 模型开始生成...")
    
    def on_llm_new_token(self, token, **kwargs):
        self.content += token
        print(f"📝 {token}", end="", flush=True)
    
    def on_llm_end(self, response, **kwargs):
        print(f"\n✅ 生成完成！总长度: {len(self.content)} 字符")
    
    def on_llm_error(self, error, **kwargs):
        print(f"❌ 生成错误: {error}")

# 初始化模型
model = ChatOpenAI(
    model="gpt-3.5-turbo",
    streaming=True,
    callbacks=[CustomStreamingCallback()]
)

# 执行生成
model.invoke("请解释什么是 LangChain 及其主要功能")
```

### 流式传输 UI 集成示例
```python
# 后端 API 示例 (FastAPI)
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI

app = FastAPI()

@app.post("/stream")
async def stream_response(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    
    model = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)
    
    async def generate():
        async for chunk in model.astream(prompt):
            yield chunk.content
    
    return StreamingResponse(generate(), media_type="text/plain")

# 前端示例 (JavaScript)
"""
async function streamResponse() {
    const prompt = document.getElementById('prompt').value;
    const output = document.getElementById('output');
    output.textContent = '';
    
    const response = await fetch('/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        output.textContent += chunk;
    }
}
"""
```

## 11. 高级用法

### 自定义流式传输协议
- **协议设计**：
  - 定义消息格式和类型
  - 实现错误处理机制
  - 支持断点续传
- **示例**：
  ```python
  class CustomStreamProtocol:
      def __init__(self):
          self.messages = []
      
      def send(self, data, message_type="text"):
          # 自定义消息格式
          message = {
              "type": message_type,
              "data": data,
              "timestamp": time.time()
          }
          self.messages.append(message)
          return json.dumps(message)
      
      def receive(self, message):
          # 处理接收到的消息
          pass
  ```

### 流式传输的压缩和加密
- **压缩**：
  - 使用 gzip 压缩传输数据
  - 减少网络带宽使用
- **加密**：
  - 实现端到端加密
  - 保护敏感数据传输

### 多模态流式传输
- **文本 + 图像**：
  - 流式传输文本的同时传输图像
  - 实现多模态同步显示
- **语音 + 文本**：
  - 实时语音转文本
  - 文本转语音的流式输出

### 流式传输的实时分析
- **情感分析**：
  - 实时分析流式文本的情感
  - 调整模型输出策略
- **内容审核**：
  - 实时检测敏感内容
  - 及时中断不良内容生成
- **性能监控**：
  - 实时监控生成速度
  - 优化模型参数