# Fatsia

Fatsia 八角金盘🌱 是一个多模型 AI 交互库，支持通过 LangChain 与各大主流 AI 模型进行交互。项目特点包括：

- 🤖 **多模型支持**：阿里云通义千问 3、OpenAI GPT 系列、Google Gemini 系列
- 🔀 **一键切换**：通过简单的配置即可在不同模型之间切换
- 📝 **完整日志**：所有 API 交互的报文都会记录到日志文件
- 🔌 **兼容接口**：完全兼容 OpenAI Python SDK 接口规范
- 🦜 **LangChain 集成**：原生支持 LangChain 框架

## 安装

### 从源码安装

```bash
cd fatsia
pip install -e .
```

### 依赖安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 配置环境变量

复制环境变量示例文件并填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
QWEN_API_KEY=your_qwen_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. 基础使用

#### 使用 FatsiaClient（推荐）

```python
from fatsia import FatsiaClient, ModelConfig

# 创建千问 3 配置
config = ModelConfig.create_qwen3_config(
    api_key="your-qwen-api-key",
    model_name="qwen-plus"
)

# 创建客户端并发送消息
with FatsiaClient(config) as client:
    response = client.chat("你好，请介绍一下自己")
    print(response)
```

#### 使用 OpenAI 兼容接口

```python
from fatsia import FatsiaOpenAIClient, ModelConfig

# 创建配置（使用千问 3）
config = ModelConfig.create_qwen3_config(api_key="your-key")

# 创建客户端
client = FatsiaOpenAIClient(config)

# 使用方式与 OpenAI SDK 完全相同
response = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"}
    ]
)

print(response.choices[0].message.content)
```

#### 使用 LangChain 集成

```python
from fatsia import FatsiaChatModel, ModelConfig
from langchain_core.messages import HumanMessage, SystemMessage

# 创建配置
config = ModelConfig.create_qwen3_config(api_key="your-key")

# 创建 LangChain 聊天模型
llm = FatsiaChatModel(config=config)

# 使用 LangChain 标准接口
messages = [
    SystemMessage(content="你是一个数学老师"),
    HumanMessage(content="什么是微积分？")
]

response = llm.invoke(messages)
print(response.content)
```

## 功能示例

### 流式聊天

```python
from fatsia import FatsiaClient, ModelConfig

config = ModelConfig.create_qwen3_config(api_key="your-key")

with FatsiaClient(config) as client:
    for chunk in client.stream_chat("写一首关于春天的诗"):
        print(chunk, end="", flush=True)
```

### 多轮对话

```python
from fatsia import FatsiaClient, ModelConfig

config = ModelConfig.create_qwen3_config(api_key="your-key")

with FatsiaClient(config) as client:
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
        {"role": "user", "content": "我想学习 Python"}
    ]
    
    response = client.chat_with_messages(messages)
    print(response)
```

### 动态切换模型

```python
from fatsia import FatsiaClient, ModelConfig, ModelType

# 初始使用千问 3
config = ModelConfig.create_qwen3_config(api_key="qwen-key")
client = FatsiaClient(config)

response = client.chat("你好")
print(f"千问 3: {response}")

# 切换到 OpenAI
openai_config = ModelConfig.create_openai_config(api_key="openai-key")
client.switch_model(openai_config)

response = client.chat("你好")
print(f"OpenAI: {response}")

client.close()
```

## 模型配置

### 千问 3 配置

```python
config = ModelConfig.create_qwen3_config(
    api_key="your-qwen-key",
    model_name="qwen-plus",  # 可选：qwen-turbo, qwen-max, qwen-plus
    timeout=60
)
```

### OpenAI 配置

```python
config = ModelConfig.create_openai_config(
    api_key="your-openai-key",
    model_name="gpt-4o",  # 可选：gpt-4o, gpt-4-turbo, gpt-3.5-turbo
    timeout=60
)
```

### Google Gemini 配置

```python
config = ModelConfig.create_gemini_config(
    api_key="your-gemini-key",
    model_name="gemini-1.5-pro",  # 可选：gemini-1.5-pro, gemini-1.5-flash
    timeout=60
)
```

## 日志系统

Fatsia 会自动将所有 API 请求和响应的报文记录到日志文件中。

- **日志目录**: `../logs/fatsia/`
- **日志文件**: `fatsia.log`（按天自动分割）
- **日志级别**: DEBUG（文件）、INFO（控制台）

### 日志内容示例

```
2026-03-25 10:30:00 - fatsia - INFO - [client.py:78] - ================================================================================
2026-03-25 10:30:00 - fatsia - INFO - [client.py:79] - 【HTTP REQUEST】
2026-03-25 10:30:00 - fatsia - INFO - [client.py:80] - Method: POST
2026-03-25 10:30:00 - fatsia - INFO - [client.py:81] - URL: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
2026-03-25 10:30:00 - fatsia - INFO - [client.py:82] - Headers:
2026-03-25 10:30:00 - fatsia - INFO - [client.py:86] -   Authorization: Bearer sk-...abc12
2026-03-25 10:30:00 - fatsia - INFO - [client.py:88] - Body:
2026-03-25 10:30:00 - fatsia - INFO - [client.py:89] -   {'model': 'qwen-plus', 'messages': [...]}
```

## 项目结构

```
fatsia/
├── src/
│   └── fatsia/
│       ├── __init__.py          # 包入口
│       ├── config.py            # 配置类和枚举
│       ├── client.py            # 统一客户端
│       ├── langchain_wrapper.py # LangChain 封装
│       ├── openai_compatible.py # OpenAI 兼容接口
│       ├── logger_config.py     # 日志配置
│       ├── utils.py             # 工具函数
│       └── examples.py          # 示例代码
├── tests/                       # 测试文件
├── logs/                        # 日志目录
├── .env.example                 # 环境变量示例
├── requirements.txt             # 依赖列表
├── pyproject.toml              # 项目配置
└── README.md                   # 本文档
```

## 运行示例

```bash
# 进入项目目录
cd fatsia

# 设置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 运行示例程序
python -m fatsia.examples
```

## 开发指南

### 添加新的模型支持

1. 在 `ModelType` 枚举中添加新类型
2. 在 `ModelConfig` 中添加对应的配置方法
3. 更新客户端以支持新模型的 API 格式

### 自定义日志配置

```python
from fatsia.logger_config import setup_logger

# 创建自定义 logger
logger = setup_logger(
    name="my_app",
    log_dir="../logs/my_app",
    level=logging.DEBUG
)
```

## 常见问题

### Q: 如何获取 API Key？

- **千问 3**: 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/apiKey)
- **OpenAI**: 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
- **Gemini**: 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)

### Q: 日志文件在哪里？

日志文件位于项目根目录的 `../logs/fatsia/` 目录下，默认文件名为 `fatsia.log`。

### Q: 如何在生产环境管理 API Key？

建议使用环境变量或密钥管理服务（如 AWS Secrets Manager、Azure Key Vault 等），不要将 API Key 硬编码在代码中。

## License

MIT License
