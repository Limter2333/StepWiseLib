# LangChain 工具（Tools）知识点总结

## 1. 核心概念

### 工具的基本定义和作用
- **工具**：是 LangChain 中用于执行特定任务的功能模块，允许语言模型与外部系统交互
- **本质**：工具是函数的封装，包含名称、描述、参数定义和执行逻辑
- **作用**：
  - 扩展语言模型的能力，使其能够执行超出纯文本生成的任务
  - 作为智能体与外部世界交互的桥梁
  - 定义智能体输入与输出的边界范围
  - 执行具体的任务，如搜索、计算、API调用等

### 工具在 LangChain 中的角色
- **功能模块**：独立的功能单元，可被智能体或模型调用
- **能力增强**：为模型提供额外的能力，如访问实时信息、执行计算等
- **结果返回**：执行任务后返回结果，供智能体或模型进一步处理

### 工具与智能体的关系
- **依赖关系**：智能体依赖工具执行具体任务
- **决策依据**：智能体通过推理决定何时使用何种工具
- **结果利用**：智能体使用工具的执行结果来完成任务

## 2. 工具类型

### 自定义工具（Custom Tools）
- **定义方式**：
  - 使用 `@tool` 装饰器
  - 继承 `BaseTool` 类
  - 使用函数式工具定义
- **示例**：
  ```python
  from langchain_core.tools import tool

  @tool
  def add(a: int, b: int) -> int:
      """Add two numbers together."""
      return a + b
  ```

### 内置工具（Built-in Tools）
- **定义**：LangChain 提供的预定义工具
- **常见内置工具**：
  - `SerpAPIWrapper`：搜索工具
  - `PythonREPLTool`：执行 Python 代码
  - `ShellTool`：执行 shell 命令
  - `FileSystemTool`：文件系统操作

### 第三方工具集成
- **定义**：与外部服务和 API 的集成
- **示例**：
  - OpenAI 函数调用
  - AWS 服务集成
  - Google 服务集成
  - 自定义 API 集成

### 工具包（Toolkits）
- **定义**：相关工具的集合，用于特定领域的任务
- **示例**：
  - `GitHubToolkit`：GitHub 相关工具
  - `GmailToolkit`：Gmail 相关工具
  - `SQLDatabaseToolkit`：数据库相关工具
- **使用方式**：
  ```python
  from langchain_community.agent_toolkits import GitHubToolkit
  from langchain_community.tools.github.tool import GitHubClient

  github_client = GitHubClient(github_token="your-token")
  toolkit = GitHubToolkit.from_github_client(github_client)
  tools = toolkit.get_tools()
  ```

## 3. 工具创建

### 工具的基本结构
- **名称**：工具的唯一标识符
- **描述**：工具的功能说明，帮助智能体理解工具的用途
- **参数定义**：使用 JSON Schema 定义参数格式
- **执行逻辑**：工具的核心功能实现

### 工具的参数定义
- **使用类型注解**：Python 类型注解自动转换为 JSON Schema
- **示例**：
  ```python
  @tool
  def search(query: str, max_results: int = 5) -> str:
      """Search the web for information."""
      # 实现搜索逻辑
      return f"Search results for: {query}"
  ```

### 工具的实现方法
1. **使用 `@tool` 装饰器**：
   ```python
   from langchain_core.tools import tool

   @tool
   def multiply(a: int, b: int) -> int:
       """Multiply two numbers together."""
       return a * b
   ```

2. **继承 `BaseTool` 类**：
   ```python
   from langchain_core.tools import BaseTool
   from pydantic import BaseModel, Field

   class CalculatorInput(BaseModel):
       a: int = Field(..., description="First number")
       b: int = Field(..., description="Second number")

   class CalculatorTool(BaseTool):
       name = "calculator"
       description = "Multiply two numbers together"
       args_schema = CalculatorInput

       def _run(self, a: int, b: int) -> int:
           return a * b
   ```

3. **使用函数式工具定义**：
   ```python
   from langchain_core.tools import create_tool

   def divide(a: int, b: int) -> float:
       """Divide two numbers."""
       return a / b

   divide_tool = create_tool(divide)
   ```

### 工具的描述和文档
- **重要性**：清晰的描述有助于智能体理解工具的用途
- **最佳实践**：
  - 描述工具的功能和用途
  - 说明参数的含义和格式
  - 描述返回值的格式和含义
  - 提供使用示例

## 4. 工具使用

### 工具的调用方式
1. **直接调用**：
   ```python
   result = add_tool.invoke({"a": 1, "b": 2})
   ```

2. **通过智能体调用**：
   ```python
   from langchain.agents import create_openai_functions_agent
   from langchain_core.prompts import ChatPromptTemplate

   prompt = ChatPromptTemplate.from_messages([
       ("system", "You are a helpful assistant"),
       ("human", "{input}"),
       ("ai", "{agent_scratchpad}")
   ])

   agent = create_openai_functions_agent(model, tools, prompt)
   result = agent.invoke({"input": "What is 5 + 7?"})
   ```

3. **批量调用**：
   ```python
   results = add_tool.batch([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
   ```

### 工具的参数传递
- **参数格式**：工具参数必须符合工具的参数定义
- **传递方式**：
  - 直接传递字典
  - 使用 Pydantic 模型
  - 通过消息传递

### 工具的结果处理
- **结果格式**：工具返回的结果会被转换为 `ToolMessage`
- **结果整合**：智能体或模型会将工具结果整合到对话中
- **示例**：
  ```python
  from langchain_core.messages import ToolMessage

  tool_msg = ToolMessage(
      content="The result is 42",
      tool_call_id="tool_call_1"
  )
  ```

### 工具的错误处理
- **异常处理**：工具应捕获并处理执行过程中的异常
- **错误返回**：返回有意义的错误信息
- **重试机制**：实现重试逻辑处理临时失败
- **示例**：
  ```python
  @tool
  def risky_operation(value: int) -> str:
      """Perform a risky operation."""
      try:
          # 执行风险操作
          if value < 0:
              raise ValueError("Value must be positive")
          return f"Success: {value}"
      except Exception as e:
          return f"Error: {str(e)}"
  ```

## 5. 工具与智能体

### 智能体如何使用工具
- **推理过程**：智能体分析任务，决定是否需要使用工具
- **工具选择**：根据任务需求选择合适的工具
- **参数生成**：为工具生成合适的参数
- **结果处理**：分析工具结果，决定是否需要进一步操作

### 工具选择机制
- **基于任务分析**：智能体根据任务类型选择合适的工具
- **基于工具描述**：智能体根据工具的描述选择最适合的工具
- **基于历史经验**：智能体根据过去的使用经验选择工具

### 工具结果的解释和整合
- **结果分析**：智能体分析工具返回的结果
- **结果整合**：将工具结果整合到对话中
- **结果呈现**：以用户友好的方式呈现工具结果

### 工具使用的最佳实践
- **工具设计**：设计简单、专注的工具
- **工具描述**：提供清晰、详细的工具描述
- **错误处理**：实现健壮的错误处理
- **结果格式**：返回结构化的结果格式

## 6. 工具与消息

### 工具调用的消息表示
- **`AIMessage`**：包含工具调用信息
  ```python
  from langchain_core.messages import AIMessage
  from langchain_core.tools import ToolCall

  tool_call_msg = AIMessage(
      content="",
      tool_calls=[
          ToolCall(
              name="search",
              args={"query": "LangChain documentation"}
          )
      ]
  )
  ```

### 工具响应的消息处理
- **`ToolMessage`**：包含工具执行结果
  ```python
  from langchain_core.messages import ToolMessage

  tool_msg = ToolMessage(
      content="LangChain is a framework for building LLM applications",
      tool_call_id=tool_call_msg.tool_calls[0].id
  )
  ```

### 工具结果的消息整合
- **消息序列**：
  1. 用户消息（`HumanMessage`）
  2. 助手消息（`AIMessage`）- 包含工具调用
  3. 工具消息（`ToolMessage`）- 包含工具结果
  4. 助手消息（`AIMessage`）- 包含最终回答

## 7. 工具与模型

### 模型如何理解和使用工具
- **提示设计**：通过提示让模型理解工具的用途
- **工具信息**：模型接收工具的描述和参数信息
- **调用格式**：模型生成符合格式的工具调用请求

### 工具调用的提示设计
- **系统提示**：包含工具的描述和使用说明
- **示例提示**：
  ```python
  system_prompt = """
  You are a helpful assistant. You have access to the following tools:
  
  1. search: Search the web for information
     - query: str - The search query
  
  2. calculator: Perform mathematical calculations
     - a: int - First number
     - b: int - Second number
  
  Use the tools when needed to answer the user's questions.
  """
  ```

### 模型对工具结果的处理
- **结果分析**：模型分析工具返回的结果
- **结果整合**：将工具结果整合到最终回答中
- **上下文理解**：结合工具结果和对话历史生成回答

## 8. 最佳实践

### 工具的设计原则
- **单一职责**：每个工具只做一件事
- **清晰描述**：提供详细的工具描述
- **健壮性**：处理各种输入情况
- **可测试性**：便于测试和调试
- **安全性**：避免安全风险，如代码注入

### 工具的命名和描述规范
- **名称**：简洁明了，反映工具的功能
- **描述**：详细准确，说明工具的用途和参数
- **参数定义**：清晰定义参数类型和含义
- **示例**：提供使用示例

### 工具的错误处理策略
- **异常捕获**：捕获并处理执行过程中的异常
- **错误信息**：返回有意义的错误信息
- **重试机制**：实现重试逻辑处理临时失败
- **降级策略**：提供备选方案处理永久失败

### 工具的性能优化
- **执行时间**：减少工具执行时间
- **参数传递**：优化参数传递方式
- **结果缓存**：合理缓存工具结果
- **批量处理**：支持批量操作提高效率

## 9. 常见问题

### 工具调用失败
- **原因**：
  - 网络问题
  - API 限制
  - 参数错误
  - 权限问题
- **解决方案**：
  - 添加错误处理
  - 实现重试机制
  - 提供备用方案
  - 监控工具状态

### 工具参数错误
- **原因**：
  - 参数格式不正确
  - 缺少必要参数
  - 参数类型错误
- **解决方案**：
  - 添加参数验证
  - 提供默认值
  - 清晰的参数说明
  - 输入验证
- **代码示例**：
  ```python
  from langchain_core.tools import BaseTool
  from pydantic import BaseModel, Field, field_validator

  class SearchInput(BaseModel):
      query: str = Field(..., description="搜索查询词")
      max_results: int = Field(default=5, ge=1, le=50, description="最大结果数")
      language: str = Field(default="zh", description="搜索语言")
      
      @field_validator('query')
      def validate_query(cls, v):
          if not v or len(v.strip()) == 0:
              raise ValueError("查询词不能为空")
          return v.strip()

  class SearchTool(BaseTool):
      name = "search"
      description = "搜索网络信息"
      args_schema = SearchInput

      def _run(self, query: str, max_results: int = 5, language: str = "zh") -> str:
          # 模拟搜索逻辑
          return f"搜索结果 for '{query}' (语言: {language}, 结果数: {max_results}): 这是搜索结果"
  ```

### 工具结果解析错误
- **原因**：
  - 结果格式不符合预期
  - 结果为空
  - 结果包含错误信息
- **解决方案**：
  - 添加结果验证
  - 处理边界情况
  - 标准化结果格式
  - 错误处理
- **代码示例**：
  ```python
  from langchain_core.tools import tool
  import json

  @tool
  def process_user_data(user_id: str) -> str:
      """处理用户数据
      
      Args:
          user_id: 用户ID
      """
      try:
          # 获取用户数据
          raw_data = get_user_data.run({"user_id": user_id})
          
          # 检查结果是否为空
          if not raw_data:
              return "错误: 获取到空的用户数据"
          
          # 检查结果是否包含错误信息
          if raw_data.startswith("Error:"):
              return f"错误: {raw_data}"
          
          # 解析 JSON 数据
          try:
              user_data = json.loads(raw_data)
          except json.JSONDecodeError as e:
              return f"错误: 数据格式错误 - {str(e)}"
          
          # 验证必要字段
          required_fields = ["id", "name", "email"]
          for field in required_fields:
              if field not in user_data:
                  return f"错误: 缺少必要字段 '{field}'"
          
          # 处理边界情况
          age = user_data.get("age", "未知")
          
          # 标准化结果
          return f"用户信息: {user_data['name']} (ID: {user_data['id']}), 邮箱: {user_data['email']}, 年龄: {age}"
          
      except Exception as e:
          return f"错误: 处理用户数据时发生异常 - {str(e)}"
  ```

### 工具使用效率问题
- **原因**：
  - 工具调用频率过高
  - 工具执行时间过长
  - 重复调用相同工具
- **解决方案**：
  - 优化工具设计
  - 缓存结果
  - 批量处理
  - 智能调用策略
- **代码示例**：
  ```python
  from langchain_core.tools import tool
  from functools import lru_cache
  import time

  # 模拟耗时操作
  def mock_api_call(query: str) -> str:
      """模拟 API 调用"""
      print(f"正在调用 API 查询: {query}")
      time.sleep(1)  # 模拟网络延迟
      return f"API 结果: {query} 的信息"

  @tool
  def search_with_cache(query: str) -> str:
      """带缓存的搜索工具
      
      Args:
          query: 搜索查询词
      """
      # 使用 lru_cache 缓存结果
      @lru_cache(maxsize=100)
      def cached_search(q: str) -> str:
          return mock_api_call(q)
      
      return cached_search(query)
  ```

## 10. 代码示例

### 自定义工具创建示例
```python
# 使用 @tool 装饰器
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """Search the web for information about a topic."""
    # 模拟搜索结果
    return f"Search results for '{query}': This is sample search data."

# 继承 BaseTool 类
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    city: str = Field(..., description="The city to get weather for")

class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get the current weather for a city"
    args_schema = WeatherInput

    def _run(self, city: str) -> str:
        # 模拟天气数据
        return f"The current weather in {city} is 72°F and sunny."
```

### 智能体与工具集成示例
```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate

# 初始化模型
model = ChatOpenAI(model="gpt-3.5-turbo")

# 创建工具
@tool
def calculate(a: int, b: int, operation: str) -> str:
    """Perform a mathematical operation on two numbers.
    
    Args:
        a: First number
        b: Second number
        operation: Operation to perform (add, subtract, multiply, divide)
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

# 创建提示
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use the calculate tool to answer math questions."),
    ("human", "{input}"),
    ("ai", "{agent_scratchpad}")
])

# 创建智能体
agent = create_openai_functions_agent(model, tools, prompt)

# 测试智能体
result = agent.invoke({"input": "What is 15 multiplied by 3?"})
print(result["output"])
```

### 批量处理工具示例
```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import List

class BatchSearchInput(BaseModel):
    queries: List[str] = Field(..., description="搜索查询词列表")
    max_results: int = Field(default=3, description="每个查询的最大结果数")

class BatchSearchTool(BaseTool):
    name = "batch_search"
    description = "批量搜索工具"
    args_schema = BatchSearchInput

    def _run(self, queries: List[str], max_results: int = 3) -> str:
        """批量执行搜索"""
        import time
        import json
        
        print(f"批量处理 {len(queries)} 个查询")
        start_time = time.time()
        
        # 模拟批量 API 调用
        results = {}
        for query in queries:
            # 模拟 API 调用延迟
            time.sleep(0.2)  # 批量处理比单个处理更快
            results[query] = f"搜索结果 for '{query}' (最多 {max_results} 条)"
        
        end_time = time.time()
        print(f"批量处理完成，耗时: {end_time - start_time:.2f} 秒")
        
        # 返回格式化结果
        return json.dumps({
            "results": results,
            "processing_time": f"{end_time - start_time:.2f} 秒",
            "query_count": len(queries)
        })
```

### 智能调用策略示例
```python
from langchain_core.tools import tool
from typing import Optional
import time

# 模拟不同性能的工具
@tool
def fast_tool(query: str) -> str:
    """快速工具 - 响应快但结果简单"""
    time.sleep(0.1)  # 快速响应
    return f"快速结果: {query}"

@tool
def slow_tool(query: str) -> str:
    """慢速工具 - 响应慢但结果详细"""
    time.sleep(1)  # 慢速响应
    return f"详细结果: {query} 的详细信息，包含更多内容..."

@tool
def smart_tool(query: str, detail_level: str = "auto") -> str:
    """智能工具 - 根据需求选择合适的工具
    
    Args:
        query: 查询词
        detail_level: 详细程度 (auto, fast, detailed)
    """
    # 智能选择策略
    if detail_level == "fast":
        # 明确要求快速
        return fast_tool.run({"query": query})
    elif detail_level == "detailed":
        # 明确要求详细
        return slow_tool.run({"query": query})
    else:
        # 自动模式：根据查询长度和复杂度决定
        query_length = len(query)
        
        # 简单查询使用快速工具
        if query_length < 10:
            print("使用快速工具处理简单查询")
            return fast_tool.run({"query": query})
        else:
            print("使用详细工具处理复杂查询")
            return slow_tool.run({"query": query})
```

### 综合示例：高效且健壮的工具设计
```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import time
import json
from functools import lru_cache

class SmartSearchInput(BaseModel):
    queries: List[str] = Field(..., description="搜索查询词列表")
    detail_level: str = Field(default="auto", description="详细程度 (auto, fast, detailed)")
    max_results: int = Field(default=5, ge=1, le=20, description="最大结果数")
    
    @field_validator('queries')
    def validate_queries(cls, v):
        if not v:
            raise ValueError("查询列表不能为空")
        if len(v) > 10:
            raise ValueError("查询数量不能超过 10 个")
        return v
    
    @field_validator('detail_level')
    def validate_detail_level(cls, v):
        valid_levels = ["auto", "fast", "detailed"]
        if v not in valid_levels:
            raise ValueError(f"详细程度必须是 {valid_levels} 之一")
        return v

class SmartSearchTool(BaseTool):
    name = "smart_search"
    description = "智能搜索工具，支持批量查询和结果缓存"
    args_schema = SmartSearchInput

    def __init__(self):
        super().__init__()
        self.cache = {}

    @lru_cache(maxsize=100)
    def _cached_search(self, query: str, detail_level: str, max_results: int) -> str:
        """带缓存的搜索实现"""
        # 模拟搜索逻辑
        if detail_level == "fast":
            time.sleep(0.1)  # 快速响应
            return f"快速搜索结果 for '{query}' (前 {max_results} 条)"
        else:
            time.sleep(0.5)  # 详细响应
            return f"详细搜索结果 for '{query}' (前 {max_results} 条): 包含详细信息..."

    def _run(self, queries: List[str], detail_level: str = "auto", max_results: int = 5) -> str:
        """执行智能搜索"""
        start_time = time.time()
        results = {}
        
        # 批量处理查询
        for query in queries:
            # 确定实际的详细程度
            actual_detail = detail_level
            if detail_level == "auto":
                actual_detail = "fast" if len(query) < 10 else "detailed"
            
            # 使用缓存执行搜索
            results[query] = self._cached_search(query, actual_detail, max_results)
        
        end_time = time.time()
        
        # 构建响应
        response = {
            "results": results,
            "statistics": {
                "query_count": len(queries),
                "processing_time": f"{end_time - start_time:.2f} 秒",
                "average_time_per_query": f"{(end_time - start_time) / len(queries):.2f} 秒"
            }
        }
        
        return json.dumps(response, ensure_ascii=False, indent=2)
```