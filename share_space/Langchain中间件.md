# LangChain 中间件（Middleware）知识点补充

## 1. 核心概念

### 中间件的基本定义和作用
- **定义**：中间件是位于应用程序核心逻辑与外部系统之间的软件层，用于处理请求和响应的预处理、后处理和转换
- **作用**：
  - **请求预处理**：对输入数据进行验证、转换和增强
  - **响应后处理**：对输出数据进行格式化、过滤和优化
  - **错误处理**：统一捕获和处理异常
  - **横切关注点**：处理日志、认证、监控等通用功能
  - **模块化**：将复杂功能分解为可重用的组件

### 中间件与其他组件的关系
- **与模型的关系**：中间件可以处理模型的输入和输出，增强模型能力
- **与智能体的关系**：中间件可以监控和干预智能体的决策过程
- **与记忆的关系**：中间件可以管理记忆的读写和更新
- **与流式传输的关系**：中间件可以处理流式数据的传输和转换

### 中间件的应用场景
- **数据验证**：确保输入数据的正确性和完整性
- **内容过滤**：过滤敏感信息和不良内容
- **格式转换**：在不同数据格式之间进行转换
- **认证授权**：验证用户身份和权限
- **日志记录**：记录请求和响应信息
- **性能监控**：监控系统性能和资源使用
- **错误处理**：统一处理和响应错误

### 中间件的优势和局限性
- **优势**：
  - 提高代码复用性和可维护性
  - 实现关注点分离
  - 增强系统的可扩展性
  - 简化核心业务逻辑
- **局限性**：
  - 可能增加系统复杂性
  - 可能影响性能（特别是多个中间件链式调用时）
  - 中间件之间的依赖和冲突
  - 调试和测试的复杂性

## 2. 中间件类型

### 输入中间件（Input Middleware）
- **定义**：处理进入系统的输入数据
- **功能**：
  - 数据验证和清洗
  - 格式转换和标准化
  - 输入增强和补充
  - 权限验证和访问控制
- **示例**：
  ```python
  class InputValidationMiddleware:
      def __call__(self, input_data):
          # 验证输入数据
          if not input_data or not isinstance(input_data, dict):
              raise ValueError("Invalid input data")
          # 补充必要字段
          if "timestamp" not in input_data:
              input_data["timestamp"] = datetime.now().isoformat()
          return input_data
  ```

### 输出中间件（Output Middleware）
- **定义**：处理系统输出的数据
- **功能**：
  - 结果格式化和美化
  - 数据过滤和脱敏
  - 响应增强和包装
  - 错误处理和标准化
- **示例**：
  ```python
  class OutputFormattingMiddleware:
      def __call__(self, output_data):
          # 格式化输出数据
          if isinstance(output_data, dict):
              return {
                  "success": True,
                  "data": output_data,
                  "timestamp": datetime.now().isoformat()
              }
          return output_data
  ```

### 前后处理中间件（Pre/Post Processing Middleware）
- **定义**：同时处理输入和输出的中间件
- **功能**：
  - 输入预处理
  - 输出后处理
  - 执行前后的状态管理
  - 执行时间的监控
- **示例**：
  ```python
  class TimingMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              start_time = time.time()
              try:
                  result = func(*args, **kwargs)
                  return result
              finally:
                  end_time = time.time()
                  print(f"Execution time: {end_time - start_time:.4f} seconds")
          return wrapper
  ```

### 错误处理中间件（Error Handling Middleware）
- **定义**：专门处理系统错误的中间件
- **功能**：
  - 捕获和记录异常
  - 转换错误为友好的响应
  - 实现错误重试机制
  - 错误分类和处理策略
- **示例**：
  ```python
  class ErrorHandlingMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              try:
                  return func(*args, **kwargs)
              except Exception as e:
                  print(f"Error occurred: {str(e)}")
                  return {"success": False, "error": str(e)}
          return wrapper
  ```

### 认证中间件（Authentication Middleware）
- **定义**：处理用户认证和授权的中间件
- **功能**：
  - 验证用户身份
  - 检查权限和访问控制
  - 管理认证状态
  - 处理认证过期和刷新
- **示例**：
  ```python
  class AuthMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 检查认证信息
              auth_token = kwargs.get("auth_token")
              if not auth_token or not self.validate_token(auth_token):
                  raise PermissionError("Unauthorized")
              return func(*args, **kwargs)
          return wrapper
      
      def validate_token(self, token):
          # 验证令牌逻辑
          return True  # 简化示例
  ```

### 日志中间件（Logging Middleware）
- **定义**：记录系统操作和事件的中间件
- **功能**：
  - 记录请求和响应
  - 跟踪执行流程
  - 监控系统状态
  - 提供审计线索
- **示例**：
  ```python
  class LoggingMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              print(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
              result = func(*args, **kwargs)
              print(f"{func.__name__} returned: {result}")
              return result
          return wrapper
  ```

## 3. 中间件的实现方法

### 基本的中间件创建
- **函数式中间件**：
  ```python
  def simple_middleware(func):
      def wrapper(*args, **kwargs):
          # 预处理逻辑
          print("Before function call")
          result = func(*args, **kwargs)
          # 后处理逻辑
          print("After function call")
          return result
      return wrapper
  ```

- **类式中间件**：
  ```python
  class ClassBasedMiddleware:
      def __init__(self, config=None):
          self.config = config or {}
      
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 预处理逻辑
              print(f"Before function call with config: {self.config}")
              result = func(*args, **kwargs)
              # 后处理逻辑
              print("After function call")
              return result
          return wrapper
  ```

### 中间件的链式调用
- **装饰器链**：
  ```python
  @logging_middleware
  @auth_middleware
  @error_handling_middleware
  def process_request(request):
      # 业务逻辑
      return "Processed request"
  ```

- **中间件管道**：
  ```python
  class MiddlewarePipeline:
      def __init__(self):
          self.middlewares = []
      
      def add_middleware(self, middleware):
          self.middlewares.append(middleware)
      
      def execute(self, func, *args, **kwargs):
          # 构建中间件链
          current_func = func
          for middleware in reversed(self.middlewares):
              current_func = middleware(current_func)
          # 执行链
          return current_func(*args, **kwargs)
  ```

### 中间件的配置和参数
- **配置传递**：
  ```python
  class ConfigurableMiddleware:
      def __init__(self, **config):
          self.config = config
      
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 使用配置
              if self.config.get("enabled", True):
                  print(f"Middleware enabled with config: {self.config}")
              return func(*args, **kwargs)
          return wrapper
  ```

- **运行时参数**：
  ```python
  class ParameterizedMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 从 kwargs 中获取中间件参数
              middleware_params = kwargs.pop("middleware_params", {})
              print(f"Middleware params: {middleware_params}")
              return func(*args, **kwargs)
          return wrapper
  ```

### 中间件的优先级管理
- **优先级排序**：
  ```python
  class PriorityMiddleware:
      def __init__(self, priority=0):
          self.priority = priority
      
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              print(f"Middleware with priority {self.priority} executed")
              return func(*args, **kwargs)
          return wrapper
  ```

- **有序执行**：
  ```python
  def create_middleware_chain(middlewares):
      # 按优先级排序
      sorted_middlewares = sorted(middlewares, key=lambda m: m.priority)
      
      def chain(func):
          current_func = func
          for middleware in reversed(sorted_middlewares):
              current_func = middleware(current_func)
          return current_func
      
      return chain
  ```

## 4. 中间件与模型

### 模型调用的中间件处理
- **输入预处理**：
  ```python
  class ModelInputMiddleware:
      def __call__(self, func):
          def wrapper(model, input_data, **kwargs):
              # 预处理输入数据
              processed_input = self.process_input(input_data)
              return func(model, processed_input, **kwargs)
          return wrapper
      
      def process_input(self, input_data):
          # 处理逻辑
          if isinstance(input_data, str):
              # 去除多余空格
              return input_data.strip()
          return input_data
  ```

### 模型输入的预处理
- **数据标准化**：
  ```python
  class InputStandardizationMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 标准化输入
              if "input" in kwargs:
                  kwargs["input"] = self.standardize(kwargs["input"])
              return func(*args, **kwargs)
          return wrapper
      
      def standardize(self, input_data):
          # 标准化逻辑
          if isinstance(input_data, dict):
              # 确保所有键都是字符串
              return {str(k): v for k, v in input_data.items()}
          return input_data
  ```

### 模型输出的后处理
- **结果格式化**：
  ```python
  class ModelOutputMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              result = func(*args, **kwargs)
              # 后处理输出
              return self.process_output(result)
          return wrapper
      
      def process_output(self, output_data):
          # 处理逻辑
          if isinstance(output_data, str):
              # 首字母大写，添加句号
              return output_data.capitalize() + ("" if output_data.endswith(".") else ".")
          return output_data
  ```

### 模型错误的捕获和处理
- **错误处理**：
  ```python
  class ModelErrorMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              try:
                  return func(*args, **kwargs)
              except Exception as e:
                  # 处理模型错误
                  print(f"Model error: {str(e)}")
                  # 返回默认响应
                  return "I'm sorry, I encountered an error. Please try again."
          return wrapper
  ```

## 5. 中间件与智能体

### 智能体执行的中间件处理
- **执行监控**：
  ```python
  class AgentExecutionMiddleware:
      def __call__(self, func):
          def wrapper(agent, *args, **kwargs):
              print(f"Starting agent execution: {agent.__class__.__name__}")
              start_time = time.time()
              try:
                  result = func(agent, *args, **kwargs)
                  return result
              finally:
                  end_time = time.time()
                  print(f"Agent execution completed in {end_time - start_time:.2f} seconds")
          return wrapper
  ```

### 智能体决策的干预
- **决策调整**：
  ```python
  class AgentDecisionMiddleware:
      def __call__(self, func):
          def wrapper(agent, *args, **kwargs):
              # 执行前干预
              if hasattr(agent, "plan"):
                  print(f"Original plan: {agent.plan}")
                  # 可以修改计划
              result = func(agent, *args, **kwargs)
              # 执行后干预
              return result
          return wrapper
  ```

### 智能体工具调用的中间件
- **工具调用监控**：
  ```python
  class ToolCallMiddleware:
      def __call__(self, func):
          def wrapper(agent, tool_name, *args, **kwargs):
              print(f"Agent calling tool: {tool_name}")
              result = func(agent, tool_name, *args, **kwargs)
              print(f"Tool {tool_name} returned: {result}")
              return result
          return wrapper
  ```

### 智能体状态的监控
- **状态追踪**：
  ```python
  class AgentStateMiddleware:
      def __call__(self, func):
          def wrapper(agent, *args, **kwargs):
              # 记录执行前状态
              if hasattr(agent, "state"):
                  print(f"Agent state before: {agent.state}")
              result = func(agent, *args, **kwargs)
              # 记录执行后状态
              if hasattr(agent, "state"):
                  print(f"Agent state after: {agent.state}")
              return result
          return wrapper
  ```

## 6. 中间件与记忆

### 记忆读写的中间件处理
- **记忆访问控制**：
  ```python
  class MemoryAccessMiddleware:
      def __call__(self, func):
          def wrapper(memory, *args, **kwargs):
              # 检查访问权限
              operation = kwargs.get("operation", "read")
              print(f"Memory {operation} operation")
              return func(memory, *args, **kwargs)
          return wrapper
  ```

### 记忆内容的过滤和转换
- **内容过滤**：
  ```python
  class MemoryFilterMiddleware:
      def __call__(self, func):
          def wrapper(memory, *args, **kwargs):
              result = func(memory, *args, **kwargs)
              # 过滤敏感内容
              if isinstance(result, dict) and "content" in result:
                  result["content"] = self.filter_sensitive(result["content"])
              return result
          return wrapper
      
      def filter_sensitive(self, content):
          # 过滤逻辑
          sensitive_words = ["password", "token", "secret"]
          for word in sensitive_words:
              content = content.replace(word, "***")
          return content
  ```

### 记忆更新的验证
- **更新验证**：
  ```python
  class MemoryUpdateMiddleware:
      def __call__(self, func):
          def wrapper(memory, *args, **kwargs):
              # 验证更新数据
              if "data" in kwargs:
                  data = kwargs["data"]
                  if not self.validate_data(data):
                      raise ValueError("Invalid memory data")
              return func(memory, *args, **kwargs)
          return wrapper
      
      def validate_data(self, data):
          # 验证逻辑
          return isinstance(data, (dict, list, str))
  ```

### 记忆一致性的保证
- **一致性检查**：
  ```python
  class MemoryConsistencyMiddleware:
      def __call__(self, func):
          def wrapper(memory, *args, **kwargs):
              # 执行操作
              result = func(memory, *args, **kwargs)
              # 检查一致性
              if hasattr(memory, "check_consistency"):
                  memory.check_consistency()
              return result
          return wrapper
  ```

## 7. 中间件与流式传输

### 流式数据的中间件处理
- **流式数据转换**：
  ```python
  class StreamingDataMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 获取流式生成器
              generator = func(*args, **kwargs)
              # 包装生成器
              return self.process_stream(generator)
          return wrapper
      
      def process_stream(self, generator):
          for chunk in generator:
              # 处理每个 chunk
              processed_chunk = self.process_chunk(chunk)
              yield processed_chunk
      
      def process_chunk(self, chunk):
          # 处理逻辑
          if isinstance(chunk, str):
              return chunk.strip()
          return chunk
  ```

### 流式事件的拦截和修改
- **事件处理**：
  ```python
  class StreamingEventMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 获取流式事件
              event_generator = func(*args, **kwargs)
              # 处理事件
              for event in event_generator:
                  processed_event = self.process_event(event)
                  if processed_event:
                      yield processed_event
          return wrapper
      
      def process_event(self, event):
          # 处理逻辑
          if event.get("type") == "error":
              # 转换错误事件
              event["message"] = f"Error: {event.get('message', 'Unknown error')}"
          return event
  ```

### 流式传输的错误处理
- **错误恢复**：
  ```python
  class StreamingErrorMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              try:
                  yield from func(*args, **kwargs)
              except Exception as e:
                  # 生成错误事件
                  yield {"type": "error", "message": str(e)}
          return wrapper
  ```

### 流式数据的转换和增强
- **数据增强**：
  ```python
  class StreamingEnhancementMiddleware:
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              for chunk in func(*args, **kwargs):
                  # 增强数据
                  enhanced_chunk = self.enhance(chunk)
                  yield enhanced_chunk
          return wrapper
      
      def enhance(self, chunk):
          # 增强逻辑
          if isinstance(chunk, dict):
              chunk["enhanced"] = True
              chunk["timestamp"] = datetime.now().isoformat()
          return chunk
  ```

## 8. 内置中间件

### 常用的内置中间件
- **LangChain 内置中间件**：
  - `CallbackManager`：管理回调函数
  - `BaseCallbackHandler`：基础回调处理器
  - `StreamingStdOutCallbackHandler`：标准输出流式处理
  - `AwaitableCallbackHandler`：可等待的回调处理器
  - `LLMChain`：模型链中间件

### 内置中间件的配置和使用
- **配置示例**：
  ```python
  from langchain.callbacks import CallbackManager, StreamingStdOutCallbackHandler
  from langchain_openai import ChatOpenAI

  # 配置回调中间件
  callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

  # 使用中间件
  model = ChatOpenAI(
      model="gpt-3.5-turbo",
      streaming=True,
      callback_manager=callback_manager
  )
  ```

### 内置中间件的组合
- **组合使用**：
  ```python
  from langchain.callbacks import CallbackManager, StreamingStdOutCallbackHandler
  from langchain.callbacks.tracers import LangChainTracer

  # 组合多个中间件
  callback_manager = CallbackManager([
      StreamingStdOutCallbackHandler(),
      LangChainTracer()
  ])
  ```

### 内置中间件的扩展
- **扩展内置中间件**：
  ```python
  from langchain.callbacks import StreamingStdOutCallbackHandler

  class CustomStreamingCallback(StreamingStdOutCallbackHandler):
      def on_llm_new_token(self, token, **kwargs):
          # 扩展逻辑
          print(f"[Custom] {token}", end="", flush=True)
  ```

## 9. 自定义中间件

### 自定义中间件的创建方法
- **基于装饰器**：
  ```python
  def custom_middleware(func):
      def wrapper(*args, **kwargs):
          # 自定义逻辑
          print("Custom middleware executed")
          return func(*args, **kwargs)
      return wrapper
  ```

- **基于类**：
  ```python
  class CustomMiddleware:
      def __init__(self, config=None):
          self.config = config or {}
      
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 自定义逻辑
              print(f"Custom middleware with config: {self.config}")
              return func(*args, **kwargs)
          return wrapper
  ```

### 中间件接口和生命周期
- **生命周期方法**：
  ```python
  class LifecycleMiddleware:
      def __init__(self):
          self.setup()
      
      def setup(self):
          # 初始化
          print("Middleware setup")
      
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 前置处理
              self.before_execute(*args, **kwargs)
              try:
                  result = func(*args, **kwargs)
                  # 后置处理
                  self.after_execute(result)
                  return result
              except Exception as e:
                  # 错误处理
                  self.on_error(e)
                  raise
          return wrapper
      
      def before_execute(self, *args, **kwargs):
          print("Before execute")
      
      def after_execute(self, result):
          print("After execute")
      
      def on_error(self, error):
          print(f"On error: {error}")
  ```

### 中间件的测试和调试
- **测试中间件**：
  ```python
  def test_middleware():
      # 创建测试函数
      @custom_middleware
      def test_func():
          return "Test result"
      
      # 执行测试
      result = test_func()
      assert result == "Test result"
      print("Middleware test passed")
  ```

### 中间件的性能优化
- **性能优化**：
  ```python
  class PerformanceOptimizedMiddleware:
      def __init__(self):
          self.cache = {}
      
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              # 缓存键
              cache_key = str(args) + str(kwargs)
              # 检查缓存
              if cache_key in self.cache:
                  return self.cache[cache_key]
              # 执行函数
              result = func(*args, **kwargs)
              # 缓存结果
              self.cache[cache_key] = result
              return result
          return wrapper
  ```

## 10. 最佳实践

### 中间件的设计原则
- **单一职责**：每个中间件只负责一个功能
- **可组合性**：中间件应该可以轻松组合使用
- **无副作用**：中间件不应该修改原始输入数据
- **可配置性**：中间件应该支持灵活的配置
- **可测试性**：中间件应该易于测试

**伪代码案例**：
```python
# 单一职责原则：每个中间件只做一件事
class ValidationMiddleware:
    def __call__(self, func):
        def wrapper(data, **kwargs):
            if not self.validate(data):
                raise ValueError("Invalid data")
            return func(data, **kwargs)
        return wrapper
    
    def validate(self, data):
        return data is not None

class LoggingMiddleware:
    def __call__(self, func):
        def wrapper(data, **kwargs):
            print(f"Processing data: {data}")
            result = func(data, **kwargs)
            print(f"Result: {result}")
            return result
        return wrapper

# 可组合性原则：轻松组合多个中间件
@LoggingMiddleware()
@ValidationMiddleware()
def process_data(data):
    return f"Processed: {data}"
```

### 中间件的使用场景选择
- **选择合适的中间件类型**：
  - 数据验证：使用输入中间件
  - 错误处理：使用错误处理中间件
  - 日志记录：使用日志中间件
  - 认证授权：使用认证中间件

**伪代码案例**：
```python
# 根据不同场景选择合适的中间件

# 场景1：用户API请求处理
class AuthenticationMiddleware:
    def __call__(self, func):
        def wrapper(request, **kwargs):
            if not self.authenticate(request):
                raise PermissionError("Authentication failed")
            return func(request, **kwargs)
        return wrapper
    
    def authenticate(self, request):
        return request.get("token") == "valid_token"

class RateLimitMiddleware:
    def __call__(self, func):
        def wrapper(request, **kwargs):
            if self.is_rate_limited(request):
                raise Exception("Rate limit exceeded")
            return func(request, **kwargs)
        return wrapper
    
    def is_rate_limited(self, request):
        return False  # 简化示例

# 场景选择：API请求需要认证和限流
@RateLimitMiddleware()
@AuthenticationMiddleware()
def handle_api_request(request):
    return "API response"
```

### 中间件的性能考虑
- **减少中间件数量**：只使用必要的中间件
- **优化中间件执行**：避免复杂的计算和IO操作
- **使用缓存**：对于重复计算的结果使用缓存
- **异步处理**：对于IO密集型操作使用异步

**伪代码案例**：
```python
# 性能优化示例
import time
from functools import lru_cache

# 使用缓存优化
class CachedMiddleware:
    def __init__(self):
        self.cache = {}
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            cache_key = str(args) + str(kwargs)
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            result = func(*args, **kwargs)
            self.cache[cache_key] = result
            return result
        return wrapper

# 使用lru_cache装饰器
class LRUCachedMiddleware:
    def __call__(self, func):
        @lru_cache(maxsize=100)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

# 异步处理示例
import asyncio

class AsyncMiddleware:
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            # 异步前置处理
            await asyncio.sleep(0.01)  # 模拟异步操作
            result = await func(*args, **kwargs)
            # 异步后置处理
            await asyncio.sleep(0.01)
            return result
        return wrapper

# 减少中间件数量：只在需要时启用
def create_middleware_chain(enable_logging=False, enable_caching=False):
    middlewares = []
    
    if enable_logging:
        middlewares.append(LoggingMiddleware())
    
    if enable_caching:
        middlewares.append(CachedMiddleware())
    
    return middlewares
```

### 中间件的错误处理策略
- **统一错误处理**：使用错误处理中间件统一处理错误
- **错误分类**：根据错误类型采取不同的处理策略
- **错误恢复**：实现错误重试和降级机制
- **错误记录**：详细记录错误信息以便调试

**伪代码案例**：
```python
# 错误处理策略示例
import time
import logging

# 统一错误处理
class UnifiedErrorHandler:
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                return {"error": "Bad Request", "message": str(e), "code": 400}
            except PermissionError as e:
                return {"error": "Unauthorized", "message": str(e), "code": 401}
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                return {"error": "Internal Server Error", "message": "An error occurred", "code": 500}
        return wrapper

# 错误重试机制
class RetryMiddleware:
    def __init__(self, max_retries=3, delay=1):
        self.max_retries = max_retries
        self.delay = delay
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < self.max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= self.max_retries:
                        raise
                    logging.warning(f"Attempt {retries} failed, retrying in {self.delay}s...")
                    time.sleep(self.delay)
        return wrapper

# 错误降级机制
class FallbackMiddleware:
    def __init__(self, fallback_value=None):
        self.fallback_value = fallback_value
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.warning(f"Operation failed, using fallback: {e}")
                return self.fallback_value
        return wrapper

# 组合使用
@UnifiedErrorHandler()
@RetryMiddleware(max_retries=2)
@FallbackMiddleware(fallback_value={"data": "default"})
def risky_operation():
    # 模拟可能失败的操作
    if random.random() < 0.5:
        raise ValueError("Operation failed")
    return {"data": "success"}
```

## 11. 常见问题

### 中间件执行顺序问题
- **问题**：中间件执行顺序影响结果
- **解决方案**：
  - 明确定义中间件的执行顺序
  - 使用优先级机制管理执行顺序
  - 测试不同顺序的效果

**伪代码案例**：
```python
# 中间件执行顺序问题示例
class MiddlewareA:
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print("Middleware A - before")
            result = func(*args, **kwargs)
            print("Middleware A - after")
            return result
        return wrapper

class MiddlewareB:
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print("Middleware B - before")
            result = func(*args, **kwargs)
            print("Middleware B - after")
            return result
        return wrapper

# 顺序1：A在B外面
print("顺序1: A -> B")
@MiddlewareA()
@MiddlewareB()
def test1():
    print("函数执行")

test1()
# 输出:
# Middleware A - before
# Middleware B - before
# 函数执行
# Middleware B - after
# Middleware A - after

# 顺序2：B在A外面
print("\n顺序2: B -> A")
@MiddlewareB()
@MiddlewareA()
def test2():
    print("函数执行")

test2()
# 输出:
# Middleware B - before
# Middleware A - before
# 函数执行
# Middleware A - after
# Middleware B - after

# 使用优先级管理顺序
class PriorityMiddleware:
    def __init__(self, priority=0):
        self.priority = priority
    
    def __call__(self, name):
        def decorator(func):
            def wrapper(*args, **kwargs):
                print(f"Middleware {name} (priority {self.priority})")
                return func(*args, **kwargs)
            return wrapper
        return decorator

def apply_by_priority(middlewares, func):
    sorted_middlewares = sorted(middlewares, key=lambda m: m.priority)
    for middleware in reversed(sorted_middlewares):
        func = middleware(func)
    return func
```

### 中间件性能开销
- **问题**：过多的中间件导致性能下降
- **解决方案**：
  - 减少不必要的中间件
  - 优化中间件实现
  - 使用缓存减少重复计算
  - 考虑中间件的执行频率

**伪代码案例**：
```python
# 性能开销问题示例
import time
from functools import wraps

# 测量中间件性能
def measure_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f}s")
        return result
    return wrapper

# 有性能问题的中间件
class SlowMiddleware:
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 模拟耗时操作
            time.sleep(0.1)
            return func(*args, **kwargs)
        return wrapper

# 优化后的中间件
class FastMiddleware:
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 快速操作
            return func(*args, **kwargs)
        return wrapper

# 性能对比
@measure_performance
@SlowMiddleware()
def slow_function():
    return "Slow result"

@measure_performance
@FastMiddleware()
def fast_function():
    return "Fast result"

# 条件性使用中间件
def conditional_middleware(condition):
    def decorator(middleware_class):
        def decorator2(func):
            if condition:
                return middleware_class()(func)
            return func
        return decorator2
    return decorator

# 只在开发环境使用调试中间件
is_development = True

@conditional_middleware(is_development)(SlowMiddleware)
def conditional_function():
    return "Result"

# 使用缓存优化
class CachedPerformanceMiddleware:
    def __init__(self):
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = str(args) + str(kwargs)
            
            if cache_key in self.cache:
                self.cache_hits += 1
                return self.cache[cache_key]
            
            self.cache_misses += 1
            result = func(*args, **kwargs)
            self.cache[cache_key] = result
            return result
        return wrapper
    
    def get_stats(self):
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }
```

### 中间件冲突和依赖
- **问题**：中间件之间存在冲突或依赖
- **解决方案**：
  - 明确中间件的依赖关系
  - 确保中间件的独立性
  - 测试中间件的组合效果
  - 使用依赖注入管理中间件

**伪代码案例**：
```python
# 中间件冲突和依赖示例
from functools import wraps

# 有冲突的中间件示例
class ConflictMiddlewareA:
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 修改kwargs，可能与其他中间件冲突
            kwargs["shared_data"] = "from A"
            return func(*args, **kwargs)
        return wrapper

class ConflictMiddlewareB:
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 也修改同一个key，导致冲突
            kwargs["shared_data"] = "from B"
            return func(*args, **kwargs)
        return wrapper

# 使用命名空间避免冲突
class NamespaceMiddleware:
    def __init__(self, namespace):
        self.namespace = namespace
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 使用命名空间
            kwargs[f"{self.namespace}_data"] = f"from {self.namespace}"
            return func(*args, **kwargs)
        return wrapper

# 明确依赖关系的中间件
class DependentMiddleware:
    def __init__(self, depends_on=None):
        self.depends_on = depends_on or []
    
    def check_dependencies(self, applied_middlewares):
        for dep in self.depends_on:
            if dep not in applied_middlewares:
                raise ValueError(f"Middleware depends on {dep}, but it's not applied")

# 中间件管理器
class MiddlewareManager:
    def __init__(self):
        self.middlewares = []
        self.applied_middlewares = []
    
    def add_middleware(self, middleware, name=None):
        if name:
            middleware.name = name
        self.middlewares.append(middleware)
    
    def apply(self, func):
        current_func = func
        for middleware in reversed(self.middlewares):
            # 检查依赖
            if hasattr(middleware, 'check_dependencies'):
                middleware.check_dependencies(self.applied_middlewares)
            current_func = middleware(current_func)
            if hasattr(middleware, 'name'):
                self.applied_middlewares.append(middleware.name)
        return current_func

# 使用示例
manager = MiddlewareManager()

# 添加有依赖的中间件
dep_middleware = DependentMiddleware(depends_on=["auth"])
dep_middleware.name = "logger"

# 先添加依赖的中间件
auth_middleware = ConflictMiddlewareA()
auth_middleware.name = "auth"

manager.add_middleware(auth_middleware, "auth")
manager.add_middleware(dep_middleware, "logger")

@manager.apply
def protected_function():
    return "Protected"
```

### 中间件调试和排错
- **问题**：中间件执行过程难以调试
- **解决方案**：
  - 添加详细的日志记录
  - 使用调试中间件
  - 分段测试中间件
  - 使用断点调试工具

**伪代码案例**：
```python
# 中间件调试和排错示例
import logging
from functools import wraps
import traceback

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 调试中间件：记录详细信息
class DebugMiddleware:
    def __init__(self, name="Debug"):
        self.name = name
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"[{self.name}] Entering {func.__name__}")
            logger.debug(f"[{self.name}] Args: {args}")
            logger.debug(f"[{self.name}] Kwargs: {kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"[{self.name}] Result: {result}")
                return result
            except Exception as e:
                logger.error(f"[{self.name}] Error: {e}")
                logger.error(f"[{self.name}] Traceback: {traceback.format_exc()}")
                raise
        return wrapper

# 追踪中间件执行顺序
class TraceMiddleware:
    def __init__(self, name):
        self.name = name
        self.execution_order = []
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.execution_order.append(f"{self.name} - before")
            try:
                result = func(*args, **kwargs)
                self.execution_order.append(f"{self.name} - after")
                return result
            except Exception as e:
                self.execution_order.append(f"{self.name} - error: {e}")
                raise
        return wrapper
    
    def get_order(self):
        return self.execution_order

# 分段测试中间件
def test_middleware_individually(middleware, test_func, *args, **kwargs):
    """单独测试一个中间件"""
    logger.info(f"Testing middleware: {middleware.__class__.__name__}")
    
    wrapped = middleware(test_func)
    try:
        result = wrapped(*args, **kwargs)
        logger.info(f"Test passed. Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

# 示例使用
@DebugMiddleware("Auth")
def auth_function(user_id):
    return f"Authenticated user {user_id}"

@DebugMiddleware("Logging")
@DebugMiddleware("Auth")
def complex_function(data):
    return f"Processed {data}"

# 使用追踪中间件
trace1 = TraceMiddleware("Middleware1")
trace2 = TraceMiddleware("Middleware2")

@trace1
@trace2
def traced_function():
    return "Done"

traced_function()
print("Execution order:", trace1.get_order())
print("Execution order:", trace2.get_order())

# 断点调试示例（使用pdb）
class BreakpointMiddleware:
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import pdb
            pdb.set_trace()  # 在这里设置断点
            return func(*args, **kwargs)
        return wrapper

@BreakpointMiddleware()
def function_to_debug(x):
    return x * 2
```

## 12. 代码示例

### 基本中间件示例
```python
# 基本中间件

def logging_middleware(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper

@logging_middleware
def add(a, b):
    return a + b

# 测试
result = add(5, 3)
print(f"Result: {result}")
```

### 自定义中间件示例
```python
# 自定义中间件类

class TimingMiddleware:
    def __init__(self, name):
        self.name = name
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            print(f"{self.name} took {end_time - start_time:.4f} seconds")
            return result
        return wrapper

@TimingMiddleware("Add function")
def add(a, b):
    import time
    time.sleep(0.1)  # 模拟耗时操作
    return a + b

# 测试
result = add(5, 3)
print(f"Result: {result}")
```

### 中间件链式调用示例
```python
# 中间件链式调用

def middleware1(func):
    def wrapper(*args, **kwargs):
        print("Middleware 1 executed")
        return func(*args, **kwargs)
    return wrapper

def middleware2(func):
    def wrapper(*args, **kwargs):
        print("Middleware 2 executed")
        return func(*args, **kwargs)
    return wrapper

def middleware3(func):
    def wrapper(*args, **kwargs):
        print("Middleware 3 executed")
        return func(*args, **kwargs)
    return wrapper

@middleware1
@middleware2
@middleware3
def process_data(data):
    print(f"Processing data: {data}")
    return f"Processed {data}"

# 测试
result = process_data("test")
print(f"Result: {result}")
```

### 复杂场景的中间件组合示例
```python
# 复杂场景的中间件组合

class AuthMiddleware:
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            if not kwargs.get("authenticated", False):
                raise PermissionError("Unauthorized")
            return func(*args, **kwargs)
        return wrapper

class InputValidationMiddleware:
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            data = kwargs.get("data")
            if not data:
                raise ValueError("No data provided")
            return func(*args, **kwargs)
        return wrapper

class ErrorHandlingMiddleware:
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return {"error": str(e)}
        return wrapper

@ErrorHandlingMiddleware()
@AuthMiddleware()
@InputValidationMiddleware()
def process_sensitive_data(data, authenticated=False):
    return f"Processed sensitive data: {data}"

# 测试
print(process_sensitive_data(data="secret", authenticated=True))
print(process_sensitive_data(data="secret", authenticated=False))
print(process_sensitive_data(authenticated=True))
```

## 13. 高级用法

### 中间件的动态加载和卸载
- **动态加载**：
  ```python
  def load_middleware(name):
      # 动态导入中间件
      module = __import__(name)
      return module.Middleware()
  
  # 动态加载中间件
  middleware = load_middleware("my_middleware")
  ```

### 中间件的条件执行
- **条件执行**：
  ```python
  class ConditionalMiddleware:
      def __init__(self, condition):
          self.condition = condition
      
      def __call__(self, func):
          def wrapper(*args, **kwargs):
              if self.condition(*args, **kwargs):
                  print("Middleware executed")
              return func(*args, **kwargs)
          return wrapper
  ```

### 中间件的嵌套和组合
- **嵌套组合**：
  ```python
  def create_complex_middleware():
      def middleware(func):
          @middleware1
          @middleware2
          def wrapper(*args, **kwargs):
              return func(*args, **kwargs)
          return wrapper
      return middleware
  ```

### 中间件的异步处理
- **异步中间件**：
  ```python
  async def async_middleware(func):
      async def wrapper(*args, **kwargs):
          print("Before async execution")
          result = await func(*args, **kwargs)
          print("After async execution")
          return result
      return wrapper
  
  @async_middleware
  async def async_task():
      await asyncio.sleep(1)
      return "Task completed"
  ```