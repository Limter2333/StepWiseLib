# LangChain 结构化输出（Structured Output）知识点补充

## 1. 核心概念

### 结构化输出的基本定义和作用
- **定义**：结构化输出是指将模型的输出组织成预定义的、机器可读的格式，如 JSON、对象等
- **作用**：
  - **数据标准化**：确保输出格式一致，便于程序处理
  - **类型安全**：通过类型定义减少运行时错误
  - **易于验证**：可以验证输出是否符合预期结构
  - **便于集成**：更容易与其他系统和 API 集成

### 结构化输出与非结构化输出的区别
| 特性 | 结构化输出 | 非结构化输出 |
|------|------------|------------|
| 格式 | 预定义的结构（JSON、对象等） | 自由文本 |
| 机器可读性 | 高 | 低 |
| 验证性 | 容易验证 | 难以验证 |
| 灵活性 | 较低（受限于结构） | 较高 |
| 适用场景 | 数据提取、API 调用等 | 自由文本生成、对话等 |

### 结构化输出的应用场景
- **数据提取**：从文本中提取结构化信息
- **API 参数生成**：生成符合 API 要求的参数
- **表单填写**：自动填充结构化表单
- **决策制定**：将模型决策表示为结构化选项
- **工具调用**：生成工具调用的结构化参数
- **数据存储**：准备结构化数据用于数据库存储

### 结构化输出的优势和局限性
- **优势**：
  - 提高数据处理的可靠性
  - 减少下游代码的复杂性
  - 便于自动化测试
  - 增强系统的可维护性
- **局限性**：
  - 增加提示工程的复杂度
  - 可能限制模型的创造力
  - 需要额外的验证逻辑
  - 某些模型可能支持不完善

## 2. 结构化输出类型

### JSON 格式输出
- **定义**：使用 JSON（JavaScript Object Notation）格式组织输出
- **特点**：
  - 广泛支持，易于解析
  - 支持嵌套结构
  - 人类可读性好
- **示例**：
  ```python
  {
    "name": "张三",
    "age": 25,
    "email": "zhangsan@example.com",
    "hobbies": ["读书", "运动", "音乐"]
  }
  ```

### Pydantic 模型输出
- **定义**：使用 Pydantic 模型定义和验证输出结构
- **特点**：
  - 类型安全
  - 自动验证
  - 支持复杂的数据结构
  - 易于文档化
- **示例**：
  ```python
  from pydantic import BaseModel, Field
  from typing import List

  class Person(BaseModel):
      name: str = Field(description="姓名")
      age: int = Field(description="年龄", ge=0, le=150)
      email: str = Field(description="邮箱地址")
      hobbies: List[str] = Field(description="爱好列表")
  ```

### 字典格式输出
- **定义**：使用 Python 字典格式组织输出
- **特点**：
  - Python 原生支持
  - 灵活易用
  - 适合简单结构
- **示例**：
  ```python
  person = {
      "name": "张三",
      "age": 25,
      "email": "zhangsan@example.com",
      "hobbies": ["读书", "运动", "音乐"]
  }
  ```

### 数据类（Dataclass）输出
- **定义**：使用 Python 数据类（dataclass）定义输出结构
- **特点**：
  - 简洁的语法
  - 自动生成常用方法
  - 类型提示支持
- **示例**：
  ```python
  from dataclasses import dataclass
  from typing import List

  @dataclass
  class Person:
      name: str
      age: int
      email: str
      hobbies: List[str]
  ```

### 自定义结构化格式输出
- **定义**：根据特定需求自定义的结构化格式
- **特点**：
  - 高度灵活
  - 适应特殊需求
  - 可能需要自定义解析器
- **示例**：
  ```python
  # 自定义 XML 格式
  person_xml = """
  <person>
    <name>张三</name>
    <age>25</age>
    <email>zhangsan@example.com</email>
    <hobbies>
      <hobby>读书</hobby>
      <hobby>运动</hobby>
      <hobby>音乐</hobby>
    </hobbies>
  </person>
  """
  ```

## 3. 结构化输出的实现方法

### 使用 Pydantic 定义输出结构
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Address(BaseModel):
    street: str = Field(description="街道地址")
    city: str = Field(description="城市")
    zip_code: str = Field(description="邮政编码")

class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄", ge=0, le=150)
    email: str = Field(description="邮箱地址")
    address: Optional[Address] = Field(None, description="地址信息")
    hobbies: List[str] = Field(description="爱好列表", default_factory=list)

# 使用模型
person = Person(
    name="张三",
    age=25,
    email="zhangsan@example.com",
    hobbies=["读书", "运动"]
)

print(person.json())
```

### 使用 LangChain 的 StructuredOutputParser
```python
from langchain.output_parsers import StructuredOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# 定义输出结构
output_parser = StructuredOutputParser.from_response_schemas([
    {
        "name": "person",
        "description": "个人信息",
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "姓名"},
            "age": {"type": "integer", "description": "年龄"},
            "email": {"type": "string", "description": "邮箱"}
        }
    }
])

# 创建提示模板
prompt = PromptTemplate(
    template="回答用户问题并按以下格式输出:\n{format_instructions}\n用户问题: {question}",
    input_variables=["question"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()}
)

# 创建链
model = ChatOpenAI(model="gpt-3.5-turbo")
chain = prompt | model | output_parser

# 使用
result = chain.invoke({"question": "介绍一下张三，25岁，邮箱zhangsan@example.com"})
print(result)
```

### 使用 JsonOutputParser
```python
from langchain.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    email: str = Field(description="邮箱地址")

# 创建解析器
parser = JsonOutputParser(pydantic_object=Person)

# 创建提示
prompt = PromptTemplate(
    template="回答用户问题:\n{format_instructions}\n用户问题: {question}",
    input_variables=["question"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# 创建链
model = ChatOpenAI(model="gpt-3.5-turbo")
chain = prompt | model | parser

# 使用
result = chain.invoke({"question": "介绍一下张三，25岁，邮箱zhangsan@example.com"})
print(result)
```

### 使用 PydanticOutputParser
```python
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    email: str = Field(description="邮箱地址")

# 创建解析器
parser = PydanticOutputParser(pydantic_object=Person)

# 创建提示
prompt = PromptTemplate(
    template="回答用户问题:\n{format_instructions}\n用户问题: {question}",
    input_variables=["question"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# 创建链
model = ChatOpenAI(model="gpt-3.5-turbo")
chain = prompt | model | parser

# 使用
result = chain.invoke({"question": "介绍一下张三，25岁，邮箱zhangsan@example.com"})
print(result)
print(type(result))  # <class '__main__.Person'>
```

### 自定义输出解析器
```python
from langchain.output_parsers import BaseOutputParser
from typing import Any
import json

class CustomOutputParser(BaseOutputParser):
    def parse(self, text: str) -> Any:
        try:
            # 尝试解析 JSON
            return json.loads(text)
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("无法解析输出")
    
    def get_format_instructions(self) -> str:
        return "请以 JSON 格式输出结果"
```

## 4. 结构化输出与模型

### 模型如何支持结构化输出
- **提示工程**：通过精心设计的提示引导模型输出特定格式
- **Fine-tuning**：对模型进行微调以更好地输出结构化格式
- **函数调用**：使用模型的函数调用功能生成结构化参数
- **约束解码**：在解码过程中施加格式约束

### 提示工程对结构化输出的影响
```python
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# 良好的提示示例
good_prompt = PromptTemplate(
    template="""你是一个信息提取专家。请从以下文本中提取信息，并严格按照 JSON 格式输出。

文本: {text}

要求:
1. 只输出 JSON，不要其他内容
2. 确保所有字段都有值
3. 如果信息缺失，使用 null

JSON 格式:
{{
    "name": "姓名",
    "age": 年龄,
    "email": "邮箱"
}}""",
    input_variables=["text"]
)

model = ChatOpenAI(model="gpt-3.5-turbo")
chain = good_prompt | model

result = chain.invoke({"text": "张三今年25岁，他的邮箱是zhangsan@example.com"})
print(result.content)
```

### 不同模型提供商的结构化输出支持
| 提供商 | 结构化输出支持 | 特殊功能 |
|--------|---------------|---------|
| OpenAI | ✅ 完全支持 | 函数调用、JSON 模式 |
| Anthropic | ✅ 支持 | 提示引导 |
| Google Gemini | ✅ 支持 | 函数调用 |
| Mistral | ✅ 支持 | 函数调用 |
| 本地模型 | 视实现而定 | 可能需要特殊提示 |

### 结构化输出的验证和纠错
```python
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄", ge=0, le=150)
    email: str = Field(description="邮箱地址")

def validate_and_correct(output: dict) -> Person:
    try:
        return Person(**output)
    except ValidationError as e:
        print(f"验证错误: {e}")
        
        # 尝试纠错
        corrected = output.copy()
        
        # 修正年龄
        if "age" in corrected:
            try:
                corrected["age"] = int(corrected["age"])
                if corrected["age"] < 0:
                    corrected["age"] = 0
                elif corrected["age"] > 150:
                    corrected["age"] = 150
            except (ValueError, TypeError):
                corrected["age"] = 0
        
        # 再次验证
        return Person(**corrected)
```

## 5. 结构化输出与智能体

### 智能体决策的结构化表示
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Decision(BaseModel):
    thought: str = Field(description="思考过程")
    action: str = Field(description="决定采取的行动")
    reasoning: str = Field(description="决策理由")
    confidence: float = Field(description="决策置信度", ge=0, le=1)

class AgentDecision(BaseModel):
    decisions: List[Decision] = Field(description="决策列表")
    final_action: str = Field(description="最终行动")
    explanation: str = Field(description="最终解释")
```

### 工具调用的结构化参数
```python
from pydantic import BaseModel, Field
from typing import Any, Dict

class ToolCall(BaseModel):
    tool_name: str = Field(description="工具名称")
    parameters: Dict[str, Any] = Field(description="工具参数")
    reasoning: str = Field(description="调用理由")

# 使用示例
tool_call = ToolCall(
    tool_name="search",
    parameters={"query": "最新科技新闻", "limit": 5},
    reasoning="需要获取最新科技新闻来回答用户问题"
)
```

### 智能体状态的结构化存储
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class AgentState(BaseModel):
    session_id: str = Field(description="会话ID")
    current_step: int = Field(description="当前步骤")
    history: List[Dict[str, Any]] = Field(description="历史记录")
    goals: List[str] = Field(description="目标列表")
    completed_tasks: List[str] = Field(description="已完成任务")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    
    class Config:
        arbitrary_types_allowed = True
```

### 结构化输出与智能体规划
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Step(BaseModel):
    step_number: int = Field(description="步骤编号")
    description: str = Field(description="步骤描述")
    required_tools: List[str] = Field(description="需要的工具")
    estimated_time: Optional[int] = Field(None, description="预计时间（秒）")
    dependencies: List[int] = Field(default_factory=list, description="依赖的步骤")

class Plan(BaseModel):
    title: str = Field(description="计划标题")
    steps: List[Step] = Field(description="步骤列表")
    total_estimated_time: Optional[int] = Field(None, description="总预计时间")
    success_criteria: str = Field(description="成功标准")
```

## 6. 结构化输出与工具

### 工具输入的结构化验证
```python
from pydantic import BaseModel, Field, ValidationError
from typing import Any, Callable

def validate_input(schema: type):
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            try:
                # 验证输入
                if kwargs:
                    schema(**kwargs)
                elif args and len(args) == 1:
                    schema(**args[0])
                return func(*args, **kwargs)
            except ValidationError as e:
                raise ValueError(f"输入验证失败: {e}")
        return wrapper
    return decorator

# 使用示例
class SearchInput(BaseModel):
    query: str = Field(description="搜索查询", min_length=1, max_length=500)
    limit: int = Field(description="结果数量", ge=1, le=50, default=10)

@validate_input(SearchInput)
def search_tool(query: str, limit: int = 10) -> dict:
    return {"results": [f"结果{i}" for i in range(limit)]}
```

### 工具输出的结构化格式化
```python
from pydantic import BaseModel, Field
from typing import List, Any

class SearchResult(BaseModel):
    title: str = Field(description="标题")
    url: str = Field(description="URL")
    snippet: str = Field(description="摘要")
    relevance_score: float = Field(description="相关性分数", ge=0, le=1)

class SearchOutput(BaseModel):
    query: str = Field(description="原始查询")
    total_results: int = Field(description="总结果数")
    results: List[SearchResult] = Field(description="结果列表")
    execution_time: float = Field(description="执行时间（秒）")

# 格式化工具输出
def format_search_output(raw_output: dict, query: str, execution_time: float) -> SearchOutput:
    return SearchOutput(
        query=query,
        total_results=len(raw_output.get("results", [])),
        results=[
            SearchResult(**result) 
            for result in raw_output.get("results", [])
        ],
        execution_time=execution_time
    )
```

### 工具调用链的结构化记录
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class ToolCallRecord(BaseModel):
    tool_name: str = Field(description="工具名称")
    parameters: Dict[str, Any] = Field(description="参数")
    start_time: datetime = Field(description="开始时间")
    end_time: datetime = Field(description="结束时间")
    success: bool = Field(description="是否成功")
    result: Any = Field(description="结果")
    error: str = Field(default="", description="错误信息")

class ToolChainRecord(BaseModel):
    chain_id: str = Field(description="链ID")
    tool_calls: List[ToolCallRecord] = Field(description="工具调用列表")
    total_time: float = Field(description="总时间")
    success: bool = Field(description="整体是否成功")
    final_result: Any = Field(description="最终结果")
```

### 工具结果的结构化聚合
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from collections import defaultdict

class AggregatedResult(BaseModel):
    sources: List[str] = Field(description="来源列表")
    combined_data: Dict[str, Any] = Field(description="合并数据")
    conflicts: List[Dict[str, Any]] = Field(description="冲突信息")
    confidence: float = Field(description="置信度", ge=0, le=1)

def aggregate_tool_results(results: List[Dict[str, Any]]) -> AggregatedResult:
    combined = defaultdict(list)
    sources = []
    conflicts = []
    
    for result in results:
        source = result.get("source", "unknown")
        sources.append(source)
        
        for key, value in result.get("data", {}).items():
            combined[key].append((source, value))
    
    # 检测冲突
    final_data = {}
    for key, values in combined.items():
        unique_values = set(v for _, v in values)
        if len(unique_values) > 1:
            conflicts.append({"key": key, "values": values})
        else:
            final_data[key] = values[0][1]
    
    return AggregatedResult(
        sources=sources,
        combined_data=final_data,
        conflicts=conflicts,
        confidence=1.0 - (len(conflicts) / max(len(combined), 1))
    )
```

## 7. 结构化输出与记忆

### 记忆内容的结构化存储
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class MemoryItem(BaseModel):
    id: str = Field(description="记忆ID")
    content: str = Field(description="内容")
    metadata: Dict[str, Any] = Field(description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    importance: float = Field(description="重要性", ge=0, le=1, default=0.5)
    tags: List[str] = Field(default_factory=list, description="标签")

class MemoryStore(BaseModel):
    items: List[MemoryItem] = Field(description="记忆项列表")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    
    def add_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        import uuid
        item = MemoryItem(
            id=str(uuid.uuid4()),
            content=content,
            metadata=metadata or {}
        )
        self.items.append(item)
        self.last_updated = datetime.now()
        return item.id
```

### 记忆检索的结构化过滤
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime, timedelta

class MemoryFilter(BaseModel):
    min_importance: Optional[float] = Field(None, description="最小重要性")
    max_age: Optional[timedelta] = Field(None, description="最大年龄")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    content_contains: Optional[str] = Field(None, description="内容包含")

def filter_memories(memories: List[MemoryItem], filter_criteria: MemoryFilter) -> List[MemoryItem]:
    filtered = memories
    
    if filter_criteria.min_importance is not None:
        filtered = [m for m in filtered if m.importance >= filter_criteria.min_importance]
    
    if filter_criteria.max_age is not None:
        cutoff = datetime.now() - filter_criteria.max_age
        filtered = [m for m in filtered if m.timestamp >= cutoff]
    
    if filter_criteria.tags:
        filtered = [m for m in filtered if any(tag in m.tags for tag in filter_criteria.tags)]
    
    if filter_criteria.content_contains:
        filtered = [m for m in filtered if filter_criteria.content_contains.lower() in m.content.lower()]
    
    return filtered
```

### 记忆更新的结构化验证
```python
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any

class MemoryUpdate(BaseModel):
    memory_id: str = Field(description="记忆ID")
    content: Optional[str] = Field(None, description="新内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="新元数据")
    importance: Optional[float] = Field(None, description="新重要性", ge=0, le=1)
    tags: Optional[List[str]] = Field(None, description="新标签")

def validate_memory_update(update: Dict[str, Any]) -> MemoryUpdate:
    try:
        return MemoryUpdate(**update)
    except ValidationError as e:
        raise ValueError(f"记忆更新验证失败: {e}")

def apply_memory_update(memory: MemoryItem, update: MemoryUpdate) -> MemoryItem:
    if update.content is not None:
        memory.content = update.content
    if update.metadata is not None:
        memory.metadata.update(update.metadata)
    if update.importance is not None:
        memory.importance = update.importance
    if update.tags is not None:
        memory.tags = update.tags
    return memory
```

### 记忆摘要的结构化生成
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class MemorySummary(BaseModel):
    total_memories: int = Field(description="总记忆数")
    time_span: Dict[str, Any] = Field(description="时间跨度")
    key_topics: List[str] = Field(description="关键主题")
    important_memories: List[str] = Field(description="重要记忆摘要")
    sentiment_summary: str = Field(description="情感摘要")
    activity_patterns: Dict[str, Any] = Field(description="活动模式")

def generate_memory_summary(memories: List[MemoryItem]) -> MemorySummary:
    if not memories:
        return MemorySummary(
            total_memories=0,
            time_span={},
            key_topics=[],
            important_memories=[],
            sentiment_summary="无记忆",
            activity_patterns={}
        )
    
    sorted_memories = sorted(memories, key=lambda m: m.timestamp)
    important = sorted(memories, key=lambda m: m.importance, reverse=True)[:5]
    
    return MemorySummary(
        total_memories=len(memories),
        time_span={
            "start": sorted_memories[0].timestamp.isoformat(),
            "end": sorted_memories[-1].timestamp.isoformat()
        },
        key_topics=["示例主题1", "示例主题2"],
        important_memories=[m.content[:100] for m in important],
        sentiment_summary="中性",
        activity_patterns={"daily": 5, "weekly": 3}
    )
```

## 8. 内置解析器

### 常用的内置输出解析器
- **JsonOutputParser**：解析 JSON 格式输出
- **PydanticOutputParser**：解析为 Pydantic 模型
- **StructuredOutputParser**：解析为结构化数据
- **CommaSeparatedListOutputParser**：解析逗号分隔的列表
- **RegexParser**：使用正则表达式解析
- **EnumOutputParser**：解析为枚举值
- **DatetimeOutputParser**：解析日期时间

### 内置解析器的配置和使用
```python
from langchain.output_parsers import (
    JsonOutputParser,
    PydanticOutputParser,
    CommaSeparatedListOutputParser,
    EnumOutputParser,
    DatetimeOutputParser
)
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from enum import Enum

# 1. CommaSeparatedListOutputParser
list_parser = CommaSeparatedListOutputParser()
list_prompt = PromptTemplate(
    template="列出{number}个{topic}\n{format_instructions}",
    input_variables=["number", "topic"],
    partial_variables={"format_instructions": list_parser.get_format_instructions()}
)

# 2. EnumOutputParser
class Color(Enum):
    RED = "红色"
    BLUE = "蓝色"
    GREEN = "绿色"

enum_parser = EnumOutputParser(enum=Color)
enum_prompt = PromptTemplate(
    template="从以下选项中选择一个: {options}\n{format_instructions}",
    input_variables=["options"],
    partial_variables={"format_instructions": enum_parser.get_format_instructions()}
)

# 3. DatetimeOutputParser
datetime_parser = DatetimeOutputParser()
datetime_prompt = PromptTemplate(
    template="将以下日期转换为标准格式: {date_text}\n{format_instructions}",
    input_variables=["date_text"],
    partial_variables={"format_instructions": datetime_parser.get_format_instructions()}
)
```

### 内置解析器的组合
```python
from langchain.output_parsers import OutputFixingParser, RetryOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")

# 基础解析器
base_parser = PydanticOutputParser(pydantic_object=Person)

# 1. OutputFixingParser - 自动修复解析错误
model = ChatOpenAI(model="gpt-3.5-turbo")
fixing_parser = OutputFixingParser.from_llm(parser=base_parser, llm=model)

# 2. RetryOutputParser - 重试解析
retry_parser = RetryOutputParser.from_llm(parser=base_parser, llm=model, max_retries=3)

# 使用示例
bad_output = '{"name": "张三", "age": "二十五"}'  # age 是字符串

try:
    result = fixing_parser.parse(bad_output)
    print(result)
except Exception as e:
    print(f"解析失败: {e}")
```

### 内置解析器的扩展
```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Any

class CustomPydanticParser(PydanticOutputParser):
    def __init__(self, pydantic_object: type, strict: bool = True):
        super().__init__(pydantic_object=pydantic_object)
        self.strict = strict
    
    def parse(self, text: str) -> Any:
        try:
            return super().parse(text)
        except Exception as e:
            if not self.strict:
                print(f"解析警告: {e}，尝试宽松解析")
                return self._loose_parse(text)
            raise
    
    def _loose_parse(self, text: str) -> Any:
        # 宽松解析逻辑
        import json
        import re
        
        # 尝试提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            data = json.loads(json_match.group())
            # 尝试创建模型，忽略额外字段
            return self.pydantic_object(**data)
        
        raise ValueError("无法宽松解析")
```

## 9. 自定义解析器

### 自定义解析器的创建方法
```python
from langchain.output_parsers import BaseOutputParser
from typing import Any, Dict
import json
import re

class XMLParser(BaseOutputParser):
    def __init__(self, root_tag: str = "root"):
        self.root_tag = root_tag
    
    def parse(self, text: str) -> Dict[str, Any]:
        # 简单的 XML 解析器
        result = {}
        
        # 提取根标签内容
        pattern = f"<{self.root_tag}>(.*?)</{self.root_tag}>"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            raise ValueError(f"未找到根标签 <{self.root_tag}>")
        
        content = match.group(1)
        
        # 提取子标签
        tag_pattern = r"<(\w+)>(.*?)</\1>"
        for tag_match in re.finditer(tag_pattern, content, re.DOTALL):
            tag_name = tag_match.group(1)
            tag_value = tag_match.group(2).strip()
            result[tag_name] = tag_value
        
        return result
    
    def get_format_instructions(self) -> str:
        return f"请使用 XML 格式输出，根标签为 <{self.root_tag}>"
```

### 解析器接口和生命周期
```python
from langchain.output_parsers import BaseOutputParser
from typing import Any, Optional
from abc import abstractmethod

class LifecycleOutputParser(BaseOutputParser):
    def __init__(self):
        self._setup()
    
    def _setup(self):
        """初始化解析器"""
        pass
    
    @abstractmethod
    def _preprocess(self, text: str) -> str:
        """预处理输入文本"""
        return text
    
    @abstractmethod
    def _parse_core(self, text: str) -> Any:
        """核心解析逻辑"""
        pass
    
    @abstractmethod
    def _postprocess(self, result: Any) -> Any:
        """后处理解析结果"""
        return result
    
    def parse(self, text: str) -> Any:
        try:
            processed_text = self._preprocess(text)
            result = self._parse_core(processed_text)
            return self._postprocess(result)
        except Exception as e:
            self._handle_error(e)
            raise
    
    def _handle_error(self, error: Exception):
        """处理错误"""
        print(f"解析错误: {error}")
```

### 解析器的测试和调试
```python
def test_parser(parser: BaseOutputParser, test_cases: list):
    """测试解析器"""
    results = []
    
    for i, (input_text, expected) in enumerate(test_cases):
        try:
            result = parser.parse(input_text)
            success = result == expected
            results.append({
                "case": i + 1,
                "input": input_text[:50] + "..." if len(input_text) > 50 else input_text,
                "result": result,
                "expected": expected,
                "success": success
            })
        except Exception as e:
            results.append({
                "case": i + 1,
                "input": input_text[:50] + "..." if len(input_text) > 50 else input_text,
                "error": str(e),
                "success": False
            })
    
    return results

# 使用示例
class SimpleParser(BaseOutputParser):
    def parse(self, text: str) -> dict:
        return {"value": text.strip()}
    
    def get_format_instructions(self) -> str:
        return "直接输出文本"

test_cases = [
    ("  hello world  ", {"value": "hello world"}),
    ("test", {"value": "test"}),
]

results = test_parser(SimpleParser(), test_cases)
for r in results:
    print(r)
```

### 解析器的性能优化
```python
from langchain.output_parsers import BaseOutputParser
from typing import Any
import json
from functools import lru_cache

class CachedParser(BaseOutputParser):
    def __init__(self, max_cache_size: int = 100):
        self.cache = {}
        self.max_cache_size = max_cache_size
    
    @lru_cache(maxsize=100)
    def _parse_cached(self, text: str) -> Any:
        """带缓存的解析"""
        return json.loads(text)
    
    def parse(self, text: str) -> Any:
        # 使用缓存
        return self._parse_cached(text)
    
    def get_format_instructions(self) -> str:
        return "请输出 JSON"

# 流式解析器
class StreamingParser(BaseOutputParser):
    def __init__(self):
        self.buffer = ""
    
    def parse_chunk(self, chunk: str) -> Any:
        """解析数据块"""
        self.buffer += chunk
        
        # 尝试解析完整的对象
        try:
            result = json.loads(self.buffer)
            self.buffer = ""
            return result
        except json.JSONDecodeError:
            # 不完整，继续缓冲
            return None
    
    def parse(self, text: str) -> Any:
        return json.loads(text)
    
    def get_format_instructions(self) -> str:
        return "请输出 JSON"
```

## 10. 最佳实践

### 结构化输出的设计原则
- **清晰明确**：结构设计要清晰，字段含义要明确
- **适度灵活**：在保证结构的同时保留一定灵活性
- **可验证**：设计的结构应该易于验证
- **可扩展**：考虑未来可能的扩展需求
- **简洁性**：避免过度设计，保持结构简洁

**伪代码案例**：
```python
# 良好的结构设计
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    """用户信息 - 良好的设计"""
    user_id: str = Field(description="唯一用户ID")
    name: str = Field(description="用户姓名", min_length=1, max_length=100)
    email: str = Field(description="邮箱地址")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    preferences: Optional[dict] = Field(None, description="用户偏好设置")

# 避免过度设计
class OverlyComplexUser(BaseModel):
    """过度复杂的设计 - 不推荐"""
    internal_id: str
    display_name: str
    legal_name: str
    primary_email: str
    secondary_emails: List[str]
    phone_numbers: List[dict]
    addresses: List[dict]
    social_media: dict
    preferences: dict
    settings: dict
    metadata: dict
    audit_log: List[dict]
    # ... 更多字段
```

### 不同场景下的结构化输出选择
- **简单数据提取**：使用字典或简单的 Pydantic 模型
- **复杂验证**：使用 Pydantic 模型，利用其验证功能
- **API 集成**：使用与 API 匹配的结构
- **数据存储**：使用符合数据库 schema 的结构
- **工具调用**：使用与工具参数匹配的结构

**伪代码案例**：
```python
# 根据场景选择合适的结构

# 场景1: 简单数据提取 - 使用字典
def simple_extraction():
    return {
        "name": "张三",
        "age": 25
    }

# 场景2: 需要验证 - 使用 Pydantic
from pydantic import BaseModel, Field, EmailStr

class ValidatedUser(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=150)
    email: EmailStr

# 场景3: API 集成 - 匹配 API 结构
class APIUser(BaseModel):
    """匹配第三方 API 的用户结构"""
    first_name: str
    last_name: str
    age: int
    email_address: str

# 场景4: 工具调用 - 匹配工具参数
class SearchParams(BaseModel):
    """搜索工具的参数结构"""
    query: str
    limit: int = 10
    offset: int = 0
    filters: dict = {}
```

### 结构化输出的验证策略
- **多层验证**：在多个层面进行验证
- **错误恢复**：设计错误恢复机制
- **渐进式验证**：先进行简单验证，再进行复杂验证
- **验证反馈**：提供清晰的验证错误信息
- **自动修复**：对于小错误尝试自动修复

**伪代码案例**：
```python
# 多层验证策略
from pydantic import BaseModel, Field, ValidationError
from typing import Any

class MultiLayerValidator:
    def __init__(self, schema: type):
        self.schema = schema
    
    def validate(self, data: Any) -> Any:
        # 第1层: 基础类型检查
        data = self._basic_check(data)
        
        # 第2层: 结构验证
        data = self._schema_validate(data)
        
        # 第3层: 业务规则验证
        data = self._business_validate(data)
        
        return data
    
    def _basic_check(self, data: Any) -> Any:
        """基础检查"""
        if data is None:
            raise ValueError("数据不能为空")
        if not isinstance(data, dict):
            raise ValueError("数据必须是字典")
        return data
    
    def _schema_validate(self, data: dict) -> Any:
        """Schema 验证"""
        try:
            return self.schema(**data)
        except ValidationError as e:
            # 尝试自动修复
            return self._auto_fix(data, e)
    
    def _business_validate(self, data: Any) -> Any:
        """业务规则验证"""
        # 自定义业务逻辑
        if hasattr(data, 'age') and data.age < 18:
            raise ValueError("用户必须年满18岁")
        return data
    
    def _auto_fix(self, data: dict, error: ValidationError) -> Any:
        """自动修复"""
        fixed = data.copy()
        for err in error.errors():
            field = err['loc'][0] if err['loc'] else None
            if field == 'age' and isinstance(data.get(field), str):
                try:
                    fixed[field] = int(data[field])
                except ValueError:
                    pass
        return self.schema(**fixed)
```

### 结构化输出的错误处理
- **明确的错误类型**：定义清晰的错误类型
- **优雅降级**：设计降级方案
- **详细的错误信息**：提供足够的调试信息
- **重试机制**：对于可恢复的错误进行重试
- ** fallback 策略**：提供 fallback 输出

**伪代码案例**：
```python
# 结构化输出错误处理
from pydantic import BaseModel, ValidationError
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class StructuredOutputError(Exception):
    """结构化输出错误基类"""
    pass

class FormatError(StructuredOutputError):
    """格式错误"""
    pass

class ValidationError(StructuredOutputError):
    """验证错误"""
    pass

class OutputHandler:
    def __init__(self, schema: type, fallback: Any = None):
        self.schema = schema
        self.fallback = fallback
    
    def process(self, raw_output: str) -> Any:
        try:
            # 尝试解析
            parsed = self._parse(raw_output)
            
            # 尝试验证
            validated = self._validate(parsed)
            
            return validated
            
        except FormatError as e:
            logger.error(f"格式错误: {e}")
            return self._handle_format_error(raw_output)
            
        except ValidationError as e:
            logger.error(f"验证错误: {e}")
            return self._handle_validation_error(raw_output, e)
            
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return self.fallback
    
    def _parse(self, text: str) -> dict:
        """解析输出"""
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise FormatError(f"JSON 解析失败: {e}")
    
    def _validate(self, data: dict) -> Any:
        """验证数据"""
        try:
            return self.schema(**data)
        except Exception as e:
            raise ValidationError(f"验证失败: {e}")
    
    def _handle_format_error(self, text: str) -> Any:
        """处理格式错误"""
        # 尝试提取 JSON
        import re
        import json
        
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return self._validate(data)
            except:
                pass
        
        return self.fallback
    
    def _handle_validation_error(self, text: str, error: Exception) -> Any:
        """处理验证错误"""
        # 记录详细信息用于调试
        logger.debug(f"原始输出: {text}")
        logger.debug(f"错误详情: {error}")
        
        return self.fallback
```

## 11. 常见问题

### 结构化输出格式错误
- **问题**：模型输出的格式不符合预期
- **原因**：
  - 提示不够清晰
  - 模型对格式理解不足
  - 输出中包含额外文本
- **解决方案**：
  - 改进提示工程
  - 使用输出修复解析器
  - 添加格式验证和修复
  - 使用更严格的约束

**伪代码案例**：
```python
# 格式错误处理
import json
import re
from langchain.output_parsers import OutputFixingParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")

class FormatErrorHandler:
    def __init__(self, schema: type):
        self.schema = schema
        self.model = ChatOpenAI(model="gpt-3.5-turbo")
    
    def parse_with_recovery(self, text: str) -> Person:
        # 方法1: 尝试直接解析
        try:
            return self._direct_parse(text)
        except Exception as e:
            print(f"直接解析失败: {e}")
        
        # 方法2: 清理文本后解析
        try:
            cleaned = self._clean_text(text)
            return self._direct_parse(cleaned)
        except Exception as e:
            print(f"清理后解析失败: {e}")
        
        # 方法3: 使用 OutputFixingParser
        try:
            return self._fix_with_llm(text)
        except Exception as e:
            print(f"LLM 修复失败: {e}")
        
        # 方法4: 尝试提取 JSON
        try:
            extracted = self._extract_json(text)
            return self._direct_parse(extracted)
        except Exception as e:
            print(f"JSON 提取失败: {e}")
        
        raise ValueError("所有解析方法都失败了")
    
    def _direct_parse(self, text: str) -> Person:
        return Person(**json.loads(text))
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除 Markdown 代码块标记
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        
        # 移除前后空白
        return text.strip()
    
    def _extract_json(self, text: str) -> str:
        """提取 JSON"""
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return match.group()
        raise ValueError("未找到 JSON")
    
    def _fix_with_llm(self, text: str) -> Person:
        """使用 LLM 修复"""
        base_parser = type('', (), {'pydantic_object': self.schema})()
        fixer = OutputFixingParser.from_llm(
            parser=type('', (), {'parse': lambda self, t: json.loads(t)})(),
            llm=self.model
        )
        # 模拟修复逻辑
        fixed = self.model.invoke(f"修复以下 JSON 格式错误，只输出修复后的 JSON:\n{text}")
        return Person(**json.loads(fixed.content))
```

### 模型不遵守输出结构
- **问题**：模型完全忽略输出结构要求
- **原因**：
  - 模型能力不足
  - 提示优先级不够
  - 任务过于复杂
- **解决方案**：
  - 使用更强大的模型
  - 改进提示设计
  - 使用函数调用/工具调用
  - 分步骤处理

**伪代码案例**：
```python
# 处理模型不遵守结构的问题
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List, Dict

class StructuredOutputEnforcer:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4")  # 使用更强大的模型
    
    def generate_with_structure(self, task: str, examples: List[Dict] = None) -> Dict:
        """强制结构化输出"""
        
        # 策略1: 使用少样本提示
        if examples:
            prompt = self._create_few_shot_prompt(examples)
        else:
            prompt = self._create_strong_prompt()
        
        # 策略2: 使用函数调用
        result = self._use_function_calling(task, prompt)
        
        # 策略3: 验证并在必要时重试
        result = self._validate_and_retry(result, task, prompt)
        
        return result
    
    def _create_strong_prompt(self) -> PromptTemplate:
        """创建强提示"""
        return PromptTemplate(
            template="""你是一个严格的 JSON 输出器。

重要规则:
1. 只输出 JSON，不要任何其他文字
2. 不要添加解释、说明或 Markdown
3. 严格遵守以下 JSON 结构:
{{
    "answer": "你的回答",
    "confidence": 0.95
}}

任务: {task}

JSON 输出:""",
            input_variables=["task"]
        )
    
    def _create_few_shot_prompt(self, examples: List[Dict]) -> FewShotPromptTemplate:
        """创建少样本提示"""
        example_prompt = PromptTemplate(
            template="任务: {task}\n输出: {output}",
            input_variables=["task", "output"]
        )
        
        return FewShotPromptTemplate(
            examples=examples,
            example_prompt=example_prompt,
            prefix="严格按照示例格式输出 JSON:",
            suffix="任务: {task}\n输出:",
            input_variables=["task"]
        )
    
    def _use_function_calling(self, task: str, prompt: PromptTemplate) -> Dict:
        """使用函数调用"""
        from langchain.tools import tool
        
        @tool
        def output_structured_data(answer: str, confidence: float) -> Dict:
            """输出结构化数据"""
            return {"answer": answer, "confidence": confidence}
        
        # 绑定工具并强制使用
        model_with_tools = self.model.bind_tools(
            [output_structured_data],
            tool_choice="output_structured_data"
        )
        
        chain = prompt | model_with_tools
        
        result = chain.invoke({"task": task})
        
        # 提取工具调用结果
        if result.tool_calls:
            return result.tool_calls[0]["args"]
        
        return json.loads(result.content)
    
    def _validate_and_retry(self, result: Dict, task: str, prompt: PromptTemplate, max_retries: int = 3) -> Dict:
        """验证并在必要时重试"""
        for attempt in range(max_retries):
            try:
                # 验证结构
                if "answer" not in result or "confidence" not in result:
                    raise ValueError("缺少必需字段")
                
                if not isinstance(result["confidence"], (int, float)):
                    raise ValueError("confidence 必须是数字")
                
                return result
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                print(f"验证失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                # 改进提示并重试
                improved_prompt = PromptTemplate(
                    template=f"""{prompt.template}

注意: 之前的输出验证失败，错误: {e}
请确保严格遵守 JSON 结构。""",
                    input_variables=["task"]
                )
                
                chain = improved_prompt | self.model
                result = json.loads(chain.invoke({"task": task}).content)
        
        return result
```

### 解析器性能问题
- **问题**：解析器处理速度慢或内存占用高
- **原因**：
  - 过度复杂的验证逻辑
  - 大量的正则表达式匹配
  - 没有利用缓存
  - 同步处理大文档
- **解决方案**：
  - 优化验证逻辑
  - 使用更快的解析库
  - 添加缓存机制
  - 使用流式处理
  - 并行处理

**伪代码案例**：
```python
# 解析器性能优化
import json
import re
from functools import lru_cache
from typing import Any, List, Dict
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class ParseResult:
    success: bool
    data: Any = None
    error: str = ""
    time_taken: float = 0.0

class OptimizedParser:
    def __init__(self, use_cache: bool = True, max_workers: int = 4):
        self.use_cache = use_cache
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 预编译正则表达式
        self.json_pattern = re.compile(r'\{[\s\S]*\}', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```(?:json)?\s*([\s\S]*?)\s*```', re.MULTILINE)
    
    @lru_cache(maxsize=1000)
    def parse_cached(self, text: str) -> ParseResult:
        """带缓存的解析"""
        import time
        start = time.time()
        
        try:
            data = self._fast_parse(text)
            return ParseResult(
                success=True,
                data=data,
                time_taken=time.time() - start
            )
        except Exception as e:
            return ParseResult(
                success=False,
                error=str(e),
                time_taken=time.time() - start
            )
    
    def parse(self, text: str) -> ParseResult:
        """解析入口"""
        if self.use_cache:
            return self.parse_cached(text)
        return self.parse_cached.__wrapped__(self, text)
    
    def _fast_parse(self, text: str) -> Dict:
        """快速解析"""
        # 尝试1: 直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试2: 提取代码块
        match = self.code_block_pattern.search(text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试3: 提取 JSON
        match = self.json_pattern.search(text)
        if match:
            return json.loads(match.group())
        
        raise ValueError("无法解析 JSON")
    
    def parse_batch(self, texts: List[str]) -> List[ParseResult]:
        """批量解析"""
        # 并行处理
        futures = [self.executor.submit(self.parse, text) for text in texts]
        return [future.result() for future in futures]
    
    def parse_stream(self, chunk_generator):
        """流式解析"""
        buffer = ""
        for chunk in chunk_generator:
            buffer += chunk
            
            # 尝试解析完整的对象
            try:
                result = self._fast_parse(buffer)
                buffer = ""
                yield ParseResult(success=True, data=result)
            except:
                # 继续缓冲
                continue
        
        # 处理剩余的 buffer
        if buffer.strip():
            try:
                result = self._fast_parse(buffer)
                yield ParseResult(success=True, data=result)
            except Exception as e:
                yield ParseResult(success=False, error=str(e))

# 使用示例
parser = OptimizedParser()

# 单个解析
result = parser.parse('{"name": "张三", "age": 25}')
print(result)

# 批量解析
texts = ['{"a": 1}', '{"b": 2}', '{"c": 3}']
results = parser.parse_batch(texts)
print(results)
```

### 复杂结构的处理
- **问题**：嵌套结构、可选字段、联合类型等复杂结构难以处理
- **原因**：
  - 模型难以生成复杂结构
  - 验证逻辑复杂
  - 错误定位困难
- **解决方案**：
  - 分步骤生成结构
  - 使用简单的基础结构
  - 增加类型提示和示例
  - 使用递归验证
  - 提供清晰的错误信息

**伪代码案例**：
```python
# 复杂结构处理
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
import json

class Address(BaseModel):
    """地址 - 简单结构"""
    street: str = Field(description="街道")
    city: str = Field(description="城市")
    zip_code: str = Field(description="邮编")

class Contact(BaseModel):
    """联系方式 - 联合类型"""
    type: str = Field(description="类型: email/phone")
    value: str = Field(description="值")

class Person(BaseModel):
    """个人信息 - 嵌套结构"""
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    address: Optional[Address] = Field(None, description="地址")
    contacts: List[Contact] = Field(default_factory=list, description="联系方式")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

class ComplexStructureHandler:
    def __init__(self):
        pass
    
    def generate_step_by_step(self, data: Dict) -> Person:
        """分步骤生成复杂结构"""
        
        # 步骤1: 生成基础信息
        basic = self._generate_basic(data)
        
        # 步骤2: 生成地址
        address = self._generate_address(data.get("address_data"))
        
        # 步骤3: 生成联系方式
        contacts = self._generate_contacts(data.get("contacts_data"))
        
        # 步骤4: 组合所有部分
        return Person(
            **basic,
            address=address,
            contacts=contacts,
            metadata=data.get("metadata", {})
        )
    
    def _generate_basic(self, data: Dict) -> Dict:
        """生成基础信息"""
        return {
            "name": data.get("name", ""),
            "age": data.get("age", 0)
        }
    
    def _generate_address(self, data: Optional[Dict]) -> Optional[Address]:
        """生成地址"""
        if not data:
            return None
        return Address(**data)
    
    def _generate_contacts(self, data_list: Optional[List[Dict]]) -> List[Contact]:
        """生成联系方式"""
        if not data_list:
            return []
        
        contacts = []
        for i, data in enumerate(data_list):
            try:
                contacts.append(Contact(**data))
            except Exception as e:
                print(f"跳过第 {i+1} 个联系方式: {e}")
        
        return contacts
    
    def validate_with_details(self, data: Dict) -> tuple[bool, List[str]]:
        """带详细错误信息的验证"""
        errors = []
        
        # 验证基础字段
        if "name" not in data:
            errors.append("缺少必需字段: name")
        elif not isinstance(data["name"], str):
            errors.append("name 必须是字符串")
        
        if "age" not in data:
            errors.append("缺少必需字段: age")
        elif not isinstance(data["age"], int):
            errors.append("age 必须是整数")
        elif data["age"] < 0 or data["age"] > 150:
            errors.append("age 必须在 0-150 之间")
        
        # 验证嵌套结构
        if "address" in data and data["address"]:
            addr_errors = self._validate_address(data["address"])
            errors.extend([f"address.{e}" for e in addr_errors])
        
        # 验证列表
        if "contacts" in data:
            for i, contact in enumerate(data["contacts"]):
                contact_errors = self._validate_contact(contact)
                errors.extend([f"contacts[{i}].{e}" for e in contact_errors])
        
        return len(errors) == 0, errors
    
    def _validate_address(self, data: Dict) -> List[str]:
        """验证地址"""
        errors = []
        required_fields = ["street", "city", "zip_code"]
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必需字段: {field}")
        return errors
    
    def _validate_contact(self, data: Dict) -> List[str]:
        """验证联系方式"""
        errors = []
        if "type" not in data:
            errors.append("缺少必需字段: type")
        elif data["type"] not in ["email", "phone"]:
            errors.append("type 必须是 'email' 或 'phone'")
        if "value" not in data:
            errors.append("缺少必需字段: value")
        return errors
```

## 12. 代码示例

### 基本结构化输出示例
```python
from langchain.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# 定义数据模型
class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    email: str = Field(description="邮箱")

# 创建解析器
parser = JsonOutputParser(pydantic_object=Person)

# 创建提示模板
prompt = PromptTemplate(
    template="回答用户问题:\n{format_instructions}\n用户问题: {question}",
    input_variables=["question"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# 创建链
model = ChatOpenAI(model="gpt-3.5-turbo")
chain = prompt | model | parser

# 使用
result = chain.invoke({"question": "介绍一下张三，25岁，邮箱zhangsan@example.com"})
print(result)
print(f"类型: {type(result)}")
```

### Pydantic 模型示例
```python
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class Gender(str, Enum):
    MALE = "男"
    FEMALE = "女"
    OTHER = "其他"

class Hobby(BaseModel):
    name: str = Field(description="爱好名称")
    level: int = Field(description="熟练程度 1-5", ge=1, le=5)

class Person(BaseModel):
    """详细的个人信息模型"""
    name: str = Field(description="姓名", min_length=1, max_length=100)
    age: int = Field(description="年龄", ge=0, le=150)
    gender: Gender = Field(description="性别")
    email: EmailStr = Field(description="邮箱地址")
    phone: Optional[str] = Field(None, description="电话号码")
    hobbies: List[Hobby] = Field(default_factory=list, description="爱好列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            raise ValueError('电话号码必须以 + 开头')
        return v
    
    @validator('hobbies')
    def validate_hobbies(cls, v):
        if len(v) > 10:
            raise ValueError('爱好不能超过10个')
        return v

# 使用
person = Person(
    name="张三",
    age=25,
    gender=Gender.MALE,
    email="zhangsan@example.com",
    phone="+8613800138000",
    hobbies=[
        Hobby(name="读书", level=5),
        Hobby(name="运动", level=4)
    ]
)

print(person.json(indent=2))
```

### 自定义解析器示例
```python
from langchain.output_parsers import BaseOutputParser
from typing import Any, Dict
import re
import xml.etree.ElementTree as ET

class XMLParser(BaseOutputParser):
    """自定义 XML 解析器"""
    
    def __init__(self, root_tag: str = "data"):
        self.root_tag = root_tag
    
    def parse(self, text: str) -> Dict[str, Any]:
        # 清理文本
        text = text.strip()
        
        # 尝试提取 XML
        xml_match = re.search(r'<\?xml.*?\?>\s*<[\s\S]*', text, re.DOTALL)
        if not xml_match:
            xml_match = re.search(f'<{self.root_tag}[\\s\\S]*</{self.root_tag}>', text, re.DOTALL)
        
        if not xml_match:
            raise ValueError("未找到 XML 内容")
        
        xml_content = xml_match.group()
        
        # 解析 XML
        root = ET.fromstring(xml_content)
        
        # 转换为字典
        return self._element_to_dict(root)
    
    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """将 XML 元素转换为字典"""
        result = {}
        
        # 处理属性
        if element.attrib:
            result.update(element.attrib)
        
        # 处理子元素
        children = list(element)
        if children:
            # 检查是否有重复的子标签
            child_tags = set(child.tag for child in children)
            for tag in child_tags:
                matching = [child for child in children if child.tag == tag]
                if len(matching) > 1:
                    # 多个相同标签，转为列表
                    result[tag] = [self._element_to_dict(child) for child in matching]
                else:
                    # 单个标签
                    child = matching[0]
                    if list(child):
                        result[tag] = self._element_to_dict(child)
                    else:
                        result[tag] = child.text
        else:
            # 没有子元素，使用文本内容
            if element.text and element.text.strip():
                result = element.text.strip()
        
        return result
    
    def get_format_instructions(self) -> str:
        return f"请使用 XML 格式输出，根标签为 <{self.root_tag}>"

# 使用示例
parser = XMLParser(root_tag="person")
xml_text = """
<person>
    <name>张三</name>
    <age>25</age>
    <email>zhangsan@example.com</email>
    <hobbies>
        <hobby>读书</hobby>
        <hobby>运动</hobby>
    </hobbies>
</person>
"""

result = parser.parse(xml_text)
print(result)
```

### 复杂场景的结构化输出示例
```python
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# 定义复杂的嵌套结构
class Step(BaseModel):
    """执行步骤"""
    step_number: int = Field(description="步骤编号")
    description: str = Field(description="步骤描述")
    tool_name: Optional[str] = Field(None, description="使用的工具")
    tool_parameters: Optional[Dict[str, Any]] = Field(None, description="工具参数")
    estimated_time: int = Field(description="预计时间（秒）")

class Plan(BaseModel):
    """执行计划"""
    title: str = Field(description="计划标题")
    steps: List[Step] = Field(description="步骤列表")
    total_estimated_time: int = Field(description="总预计时间")
    success_criteria: List[str] = Field(description="成功标准")
    risk_factors: List[str] = Field(default_factory=list, description="风险因素")

class AgentDecision(BaseModel):
    """智能体决策"""
    decision_id: str = Field(description="决策ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="决策时间")
    thought_process: str = Field(description="思考过程")
    plan: Plan = Field(description="执行计划")
    confidence: float = Field(description="置信度", ge=0, le=1)
    alternative_plans: List[Plan] = Field(default_factory=list, description="备选计划")

# 创建解析器
parser = PydanticOutputParser(pydantic_object=AgentDecision)

# 创建提示
prompt = PromptTemplate(
    template="""你是一个智能体规划专家。

任务: {task}

请制定一个详细的执行计划。

{format_instructions}""",
    input_variables=["task"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# 创建链
model = ChatOpenAI(model="gpt-4")
chain = prompt | model | parser

# 使用
result = chain.invoke({
    "task": "帮我规划一次周末旅行，从北京到上海，包括交通、住宿和景点"
})

print(f"决策ID: {result.decision_id}")
print(f"置信度: {result.confidence}")
print(f"计划标题: {result.plan.title}")
print(f"总时间: {result.plan.total_estimated_time}秒")
print("\n步骤:")
for step in result.plan.steps:
    print(f"  {step.step_number}. {step.description} ({step.estimated_time}秒)")
```

## 13. 高级用法

### 嵌套结构化输出
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Address(BaseModel):
    street: str = Field(description="街道")
    city: str = Field(description="城市")
    zip_code: str = Field(description="邮编")

class Contact(BaseModel):
    type: str = Field(description="类型")
    value: str = Field(description="值")

class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    address: Optional[Address] = Field(None, description="地址")
    contacts: List[Contact] = Field(default_factory=list, description="联系方式")

# 创建嵌套结构
person = Person(
    name="张三",
    age=25,
    address=Address(
        street="人民路123号",
        city="北京",
        zip_code="100000"
    ),
    contacts=[
        Contact(type="email", value="zhangsan@example.com"),
        Contact(type="phone", value="+8613800138000")
    ]
)

print(person.json(indent=2))
```

### 条件结构化输出
```python
from pydantic import BaseModel, Field
from typing import Union, Literal

class EmailNotification(BaseModel):
    type: Literal["email"] = "email"
    email_address: str = Field(description="邮箱地址")
    subject: str = Field(description="邮件主题")

class SMSNotification(BaseModel):
    type: Literal["sms"] = "sms"
    phone_number: str = Field(description="电话号码")
    message: str = Field(description="短信内容")

class PushNotification(BaseModel):
    type: Literal["push"] = "push"
    device_id: str = Field(description="设备ID")
    title: str = Field(description="推送标题")
    body: str = Field(description="推送内容")

# 联合类型
Notification = Union[EmailNotification, SMSNotification, PushNotification]

def create_notification(notification_type: str, **kwargs) -> Notification:
    if notification_type == "email":
        return EmailNotification(**kwargs)
    elif notification_type == "sms":
        return SMSNotification(**kwargs)
    elif notification_type == "push":
        return PushNotification(**kwargs)
    raise ValueError(f"未知的通知类型: {notification_type}")

# 使用
email_notification = create_notification(
    "email",
    email_address="user@example.com",
    subject="测试邮件"
)

print(email_notification)
```

### 动态结构化输出
```python
from pydantic import BaseModel, Field, create_model
from typing import Dict, Any, Type

def create_dynamic_model(model_name: str, fields: Dict[str, tuple]) -> Type[BaseModel]:
    """动态创建 Pydantic 模型"""
    return create_model(model_name, **fields)

# 定义字段
fields = {
    "name": (str, Field(description="姓名")),
    "age": (int, Field(description="年龄", ge=0)),
    "email": (str, Field(description="邮箱"))
}

# 动态创建模型
DynamicPerson = create_dynamic_model("DynamicPerson", fields)

# 使用动态模型
person = DynamicPerson(
    name="张三",
    age=25,
    email="zhangsan@example.com"
)

print(person)

# 更灵活的动态模型
class DynamicStructuredOutput:
    def __init__(self):
        self.models = {}
    
    def define_model(self, name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
        """从 schema 定义模型"""
        fields = {}
        for field_name, field_schema in schema.items():
            field_type = field_schema.get("type", str)
            field_description = field_schema.get("description", "")
            field_default = field_schema.get("default", ...)
            
            if field_type == "string":
                py_type = str
            elif field_type == "integer":
                py_type = int
            elif field_type == "number":
                py_type = float
            elif field_type == "boolean":
                py_type = bool
            else:
                py_type = str
            
            fields[field_name] = (py_type, Field(default=field_default, description=field_description))
        
        model = create_dynamic_model(name, fields)
        self.models[name] = model
        return model
    
    def parse(self, model_name: str, data: Dict[str, Any]) -> BaseModel:
        """解析数据"""
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未定义")
        
        return self.models[model_name](**data)

# 使用
dso = DynamicStructuredOutput()

# 定义模型
user_schema = {
    "username": {"type": "string", "description": "用户名"},
    "email": {"type": "string", "description": "邮箱"},
    "is_active": {"type": "boolean", "description": "是否激活", "default": True}
}

dso.define_model("User", user_schema)

# 解析数据
user_data = {
    "username": "zhangsan",
    "email": "zhangsan@example.com"
}

user = dso.parse("User", user_data)
print(user)
```

### 多模态结构化输出
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

class TextContent(BaseModel):
    type: ContentType = ContentType.TEXT
    text: str = Field(description="文本内容")
    language: Optional[str] = Field(None, description="语言")

class ImageContent(BaseModel):
    type: ContentType = ContentType.IMAGE
    url: str = Field(description="图片URL")
    caption: Optional[str] = Field(None, description="图片说明")
    width: Optional[int] = Field(None, description="宽度")
    height: Optional[int] = Field(None, description="高度")

class AudioContent(BaseModel):
    type: ContentType = ContentType.AUDIO
    url: str = Field(description="音频URL")
    duration: Optional[float] = Field(None, description="时长（秒）")
    transcript: Optional[str] = Field(None, description="转录文本")

class VideoContent(BaseModel):
    type: ContentType = ContentType.VIDEO
    url: str = Field(description="视频URL")
    duration: Optional[float] = Field(None, description="时长（秒）")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")

# 多模态内容
MultimodalContent = Union[TextContent, ImageContent, AudioContent, VideoContent]

class MultimodalResponse(BaseModel):
    response_id: str = Field(description="响应ID")
    timestamp: str = Field(description="时间戳")
    contents: List[MultimodalContent] = Field(description="内容列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

# 使用示例
response = MultimodalResponse(
    response_id="resp_001",
    timestamp="2024-01-01T00:00:00Z",
    contents=[
        TextContent(text="这是一段文本说明"),
        ImageContent(url="https://example.com/image.jpg", caption="示例图片"),
        AudioContent(url="https://example.com/audio.mp3", duration=10.5)
    ],
    metadata={"source": "multimodal_api"}
)

print(response.json(indent=2))
```