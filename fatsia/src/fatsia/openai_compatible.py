"""
OpenAI 兼容接口模块

提供与 OpenAI Python SDK 完全兼容的接口，使得用户可以像使用 OpenAI SDK 一样
使用千问 3、Gemini 等其他模型。支持一键切换模型提供商。
"""

from typing import Any, Dict, Iterator, List, Optional, Union
from pydantic import BaseModel

from .config import ModelConfig, ModelType
from .logger_config import logger, log_request, log_response, log_error


class ChatCompletionMessage(BaseModel):
    """聊天完成消息对象"""
    role: str
    content: str


class ChatCompletionChoice(BaseModel):
    """聊天完成选项"""
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str] = None


class ChatCompletionUsage(BaseModel):
    """Token 使用统计"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletion(BaseModel):
    """聊天完成响应"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None


class ChatCompletionChunk(BaseModel):
    """流式聊天完成块"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


class FatsiaOpenAIClient:
    """
    OpenAI 兼容客户端
    
    提供与 OpenAI Python SDK v1.0+ 完全兼容的接口。
    可以直接替换 OpenAI 客户端实例，无需修改业务代码。
    
    Attributes:
        config: 模型配置对象
        
    Example:
        >>> from src.fatsia import FatsiaOpenAIClient, ModelConfig
        >>> config = ModelConfig.create_qwen3_config(api_key="your-key")
        >>> client = FatsiaOpenAIClient(config)
        >>> 
        >>> # 使用方式与 OpenAI SDK 完全相同
        >>> response = client.chat.completions.create(
        ...     model="qwen-plus",
        ...     messages=[{"role": "user", "content": "你好"}]
        ... )
        >>> print(response.choices[0].message.content)
    """
    
    def __init__(self, config: ModelConfig):
        """
        初始化兼容客户端
        
        Args:
            config: 模型配置对象
        """
        self.config = config
        self.chat = ChatCompletions(self)
        logger.info(f"FatsiaOpenAIClient 初始化完成，模型：{config.model_name}")
    
    def switch_model(self, config: ModelConfig) -> None:
        """切换模型配置"""
        self.config = config
        self.chat._update_config(config)
        logger.info(f"模型已切换到：{config.model_name}")


class ChatCompletions:
    """
    聊天完成接口
    
    模拟 OpenAI SDK 的 chat.completions 接口
    """
    
    def __init__(self, client: FatsiaOpenAIClient):
        self._client = client
        self._http_client = None
        self._init_http_client()
    
    def _init_http_client(self) -> None:
        """初始化 HTTP 客户端"""
        import httpx
        self._http_client = httpx.Client(timeout=self._client.config.timeout)
    
    def _update_config(self, config: ModelConfig) -> None:
        """更新配置并重新初始化 HTTP 客户端"""
        self._client.config = config
        if self._http_client:
            self._http_client.close()
        self._init_http_client()
    
    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Iterator[ChatCompletionChunk]]:
        """
        创建聊天完成
        
        Args:
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式输出
            **kwargs: 其他参数
            
        Returns:
            非流模式返回 ChatCompletion 对象
            流模式返回 ChatCompletionChunk 迭代器
        """
        logger.debug(f"创建聊天完成请求，model={model}, stream={stream}")
        
        # 使用配置中的模型名称（如果传入的 model 与配置不同，则使用传入的）
        model_name = model if model else self._client.config.model_name
        
        # 准备请求参数
        request_body = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature or self._client.config.temperature,
            "max_tokens": max_tokens or self._client.config.max_tokens,
            "stream": stream,
            **kwargs,
        }
        
        # 记录请求日志
        headers = {
            "Authorization": f"Bearer {self._client.config.api_key}",
            "Content-Type": "application/json",
        }
        log_request(
            method="POST",
            url=f"{self._client.config.base_url}/chat/completions",
            headers=headers,
            body=request_body,
        )
        
        try:
            if stream:
                return self._create_stream(request_body, headers, model_name)
            else:
                return self._create_non_stream(request_body, headers, model_name)
                
        except Exception as e:
            log_error(
                error_type="CreateError",
                message=str(e),
                details={},
            )
            raise
    
    def _create_non_stream(
        self,
        request_body: Dict[str, Any],
        headers: Dict[str, str],
        model_name: str,
    ) -> ChatCompletion:
        """非流式请求处理"""
        import time
        
        response = self._http_client.post(
            url=f"{self._client.config.base_url}/chat/completions",
            headers=headers,
            json=request_body,
        )
        
        # 记录响应日志
        log_response(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.json(),
        )
        
        response.raise_for_status()
        data = response.json()
        
        # 构建兼容的响应对象
        return ChatCompletion(
            id=data.get("id", f"chatcmpl-{int(time.time())}"),
            created=data.get("created", int(time.time())),
            model=model_name,
            choices=[
                ChatCompletionChoice(
                    index=choice.get("index", 0),
                    message=ChatCompletionMessage(
                        role=choice["message"]["role"],
                        content=choice["message"]["content"],
                    ),
                    finish_reason=choice.get("finish_reason"),
                )
                for choice in data.get("choices", [])
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=data.get("usage", {}).get("completion_tokens", 0),
                total_tokens=data.get("usage", {}).get("total_tokens", 0),
            ) if data.get("usage") else None,
        )
    
    def _create_stream(
        self,
        request_body: Dict[str, Any],
        headers: Dict[str, str],
        model_name: str,
    ) -> Iterator[ChatCompletionChunk]:
        """流式请求处理"""
        import time
        import json
        
        with self._http_client.stream(
            "POST",
            f"{self._client.config.base_url}/chat/completions",
            headers=headers,
            json=request_body,
        ) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk_data = json.loads(data)
                        
                        # 构建兼容的流式响应块
                        choices = []
                        for choice in chunk_data.get("choices", []):
                            delta = choice.get("delta", {})
                            choices.append({
                                "index": choice.get("index", 0),
                                "delta": {
                                    "role": delta.get("role"),
                                    "content": delta.get("content"),
                                },
                                "finish_reason": choice.get("finish_reason"),
                            })
                        
                        yield ChatCompletionChunk(
                            id=chunk_data.get("id", f"chatcmpl-{int(time.time())}"),
                            created=chunk_data.get("created", int(time.time())),
                            model=model_name,
                            choices=choices,
                        )
                    except (json.JSONDecodeError, KeyError):
                        continue
    
    def __del__(self) -> None:
        """析构函数，关闭 HTTP 客户端"""
        if hasattr(self, "_http_client") and self._http_client:
            self._http_client.close()


# 便捷函数：创建兼容客户端
def create_compatible_client(
    api_key: str,
    base_url: Optional[str] = None,
    model_type: ModelType = ModelType.QWEN,
    model_name: Optional[str] = None,
) -> FatsiaOpenAIClient:
    """
    创建 OpenAI 兼容客户端的便捷函数
    
    Args:
        api_key: API 密钥
        base_url: API 基础 URL（可选，不提供则使用默认值）
        model_type: 模型类型
        model_name: 模型名称
        
    Returns:
        FatsiaOpenAIClient 实例
        
    Example:
        >>> # 创建千问 3 客户端
        >>> qwen_client = create_compatible_client(
        ...     api_key="qwen-key",
        ...     model_type=ModelType.QWEN
        ... )
        >>> 
        >>> # 创建 OpenAI 客户端
        >>> openai_client = create_compatible_client(
        ...     api_key="openai-key",
        ...     model_type=ModelType.OPENAI
        ... )
    """
    config = ModelConfig(
        model_type=model_type,
        api_key=api_key,
        base_url=base_url or "",
        model_name=model_name or "",
    )
    
    # 根据模型类型设置默认值
    if model_type == ModelType.QWEN:
        config.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        config.model_name = model_name or "qwen-plus"
    elif model_type == ModelType.OPENAI:
        config.base_url = "https://api.openai.com/v1"
        config.model_name = model_name or "gpt-4o"
    elif model_type == ModelType.GEMINI:
        config.base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        config.model_name = model_name or "gemini-1.5-pro"
    
    return FatsiaOpenAIClient(config)
