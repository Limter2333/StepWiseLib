"""
Fatsia 客户端模块

提供统一的客户端接口，支持不同模型之间的无缝切换。
内部使用 LangChain 框架与各大 AI 模型进行交互。
"""

from typing import Optional, List, Dict, Any, Generator
import httpx

from .config import ModelConfig, ModelType
from .logger_config import logger, log_request, log_response, log_error


class FatsiaClient:
    """
    Fatsia 统一客户端
    
    提供简洁的 API 接口与各种大语言模型进行交互。
    支持同步和异步调用，支持流式输出。
    
    Attributes:
        config: 模型配置对象
        _client: HTTP 客户端实例
        
    Example:
        >>> from src.fatsia import FatsiaClient, ModelConfig
        >>> config = ModelConfig.create_qwen3_config(api_key="your-api-key")
        >>> client = FatsiaClient(config)
        >>> response = client.chat("你好，请介绍一下自己")
        >>> print(response)
    """
    
    def __init__(self, config: ModelConfig):
        """
        初始化 FatsiaClient
        
        Args:
            config: 模型配置对象，包含 API Key、模型类型等信息
        """
        self.config = config
        self._client = httpx.Client(timeout=config.timeout)
        logger.info(f"FatsiaClient 初始化完成，模型类型：{config.model_type}")
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        发送聊天消息并获取回复
        
        Args:
            message: 用户消息内容
            system_prompt: 系统提示词（可选），用于设定 AI 的角色和行为
            temperature: 温度参数（可选），覆盖配置中的默认值
            max_tokens: 最大生成 token 数（可选），覆盖配置中的默认值
            **kwargs: 其他传递给 API 的参数
            
        Returns:
            AI 的回复文本
            
        Raises:
            Exception: 当 API 调用失败时抛出异常
        """
        logger.debug(f"收到聊天请求：message={message[:50]}...")
        
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        # 准备请求参数
        request_body = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            **kwargs,
        }
        
        # 记录请求日志
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        log_request(
            method="POST",
            url=f"{self.config.base_url}/chat/completions",
            headers=headers,
            body=request_body,
        )
        
        try:
            # 发送请求
            response = self._client.post(
                url=f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=request_body,
            )
            
            # 记录响应日志
            log_response(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.json(),
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.info(f"聊天成功，回复：{content}")
            logger.info(f"聊天成功，回复长度：{len(content)}")
            return content
            
        except httpx.HTTPStatusError as e:
            log_error(
                error_type="HTTPStatusError",
                message=f"HTTP 错误：{e.response.status_code}",
                details={"response": e.response.text},
            )
            raise Exception(f"API 请求失败：{e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            log_error(
                error_type="RequestError",
                message=f"请求错误：{str(e)}",
                details={},
            )
            raise Exception(f"网络请求失败：{str(e)}")
        except KeyError as e:
            log_error(
                error_type="ParseError",
                message=f"解析响应失败：{str(e)}",
                details={"response": response.text if 'response' in locals() else "unknown"},
            )
            raise Exception(f"响应解析失败：{str(e)}")
    
    def chat_with_messages(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        发送多轮对话消息
        
        Args:
            messages: 消息列表，每个消息包含 role 和 content
            temperature: 温度参数（可选）
            max_tokens: 最大生成 token 数（可选）
            **kwargs: 其他参数
            
        Returns:
            AI 的回复文本
            
        Example:
            >>> messages = [
            ...     {"role": "system", "content": "你是一个助手"},
            ...     {"role": "user", "content": "你好"},
            ...     {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
            ...     {"role": "user", "content": "今天天气怎么样？"}
            ... ]
            >>> response = client.chat_with_messages(messages)
        """
        logger.debug(f"收到多轮对话请求，消息数：{len(messages)}")
        
        # 准备请求参数
        request_body = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            **kwargs,
        }
        
        # 记录请求日志
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        log_request(
            method="POST",
            url=f"{self.config.base_url}/chat/completions",
            headers=headers,
            body=request_body,
        )
        
        try:
            # 发送请求
            response = self._client.post(
                url=f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=request_body,
            )
            
            # 记录响应日志
            log_response(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.json(),
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.info(f"多轮对话成功，回复长度：{len(content)}")
            return content
            
        except Exception as e:
            log_error(
                error_type="ChatError",
                message=str(e),
                details={},
            )
            raise
    
    def stream_chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        流式聊天，逐步返回 AI 的回复
        
        Args:
            message: 用户消息
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数
            
        Yields:
            AI 回复的文本片段
        """
        logger.debug(f"收到流式聊天请求：message={message[:50]}...")
        
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        # 准备请求参数
        request_body = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": True,
            **kwargs,
        }
        
        # 记录请求日志
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        log_request(
            method="POST",
            url=f"{self.config.base_url}/chat/completions",
            headers=headers,
            body=request_body,
        )
        
        try:
            # 使用 stream=True 进行流式请求
            with self._client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=request_body,
            ) as response:
                response.raise_for_status()
                
                # 逐行处理 SSE 数据
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 去掉 "data: " 前缀
                        if data.strip() == "[DONE]":
                            break
                        
                        import json
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError):
                            continue
                            
        except Exception as e:
            log_error(
                error_type="StreamError",
                message=str(e),
                details={},
            )
            raise
    
    def switch_model(self, config: ModelConfig) -> None:
        """
        动态切换模型配置
        
        Args:
            config: 新的模型配置对象
        """
        self.config = config
        # 更新 HTTP 客户端的超时时间
        self._client.timeout = config.timeout
        logger.info(f"模型已切换到：{config.model_type}, 模型名称：{config.model_name}")
    
    def close(self) -> None:
        """关闭 HTTP 客户端连接"""
        self._client.close()
        logger.info("FatsiaClient 已关闭")
    
    def __enter__(self) -> "FatsiaClient":
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.close()
