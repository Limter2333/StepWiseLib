"""
LangChain 封装模块

提供 LangChain 兼容的接口，可以使用 LangChain 的标准方式调用各种模型。
支持千问 3、OpenAI、Gemini 等模型的无缝切换。
"""

from typing import Any, Dict, Iterator, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult

from .config import ModelConfig, ModelType
from .logger_config import logger, log_request, log_response, log_error


class FatsiaChatModel(BaseChatModel):
    """
    LangChain 聊天模型封装
    
    继承自 LangChain 的 BaseChatModel，提供与 LangChain 生态系统的完整兼容性。
    可以使用 LangChain 的各种功能，如 Chains、Agents、Memory 等。
    
    Attributes:
        config: 模型配置对象
        _client: 内部 HTTP 客户端
        
    Example:
        >>> from src.fatsia import FatsiaChatModel, ModelConfig
        >>> config = ModelConfig.create_qwen3_config(api_key="your-key")
        >>> llm = FatsiaChatModel(config=config)
        >>> from langchain_core.messages import HumanMessage
        >>> response = llm.invoke([HumanMessage(content="你好")])
    """
    
    config: ModelConfig
    _client: Any = None
    
    def __init__(self, config: ModelConfig, **kwargs: Any):
        """
        初始化 LangChain 聊天模型
        
        Args:
            config: 模型配置对象
            **kwargs: 其他传递给父类的参数
        """
        super().__init__(config=config, **kwargs)
        self._init_client()
        logger.info(f"FatsiaChatModel 初始化完成，模型：{config.model_name}")
    
    def _init_client(self) -> None:
        """初始化 HTTP 客户端"""
        import httpx
        self._client = httpx.Client(timeout=self.config.timeout)
    
    @property
    def _llm_type(self) -> str:
        """返回 LLM 类型名称"""
        return f"fatsia_{self.config.model_type}"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """返回用于识别此 LLM 的参数"""
        return {
            "model_type": self.config.model_type,
            "model_name": self.config.model_name,
            "base_url": self.config.base_url,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        生成聊天的核心方法（同步版本）
        
        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: LangChain 运行管理器
            **kwargs: 其他参数
            
        Returns:
            ChatResult 包含生成的消息
        """
        logger.debug(f"开始生成聊天响应，消息数：{len(messages)}")
        
        # 转换 LangChain 消息格式为 API 格式
        api_messages = self._convert_messages(messages)
        
        # 准备请求参数
        request_body = {
            "model": self.config.model_name,
            "messages": api_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        # 添加停止词
        if stop:
            request_body["stop"] = stop
        
        # 添加额外参数
        request_body.update(kwargs)
        
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
            message_data = result["choices"][0]["message"]
            
            # 创建 AI 消息
            ai_message = AIMessage(content=message_data["content"])
            
            # 创建生成结果
            generation = ChatGeneration(message=ai_message)
            
            logger.info(f"聊天生成成功")
            return ChatResult(generations=[generation])
            
        except Exception as e:
            log_error(
                error_type="GenerateError",
                message=str(e),
                details={},
            )
            raise
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        异步生成聊天的核心方法
        
        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 运行管理器
            **kwargs: 其他参数
            
        Returns:
            ChatResult 包含生成的消息
        """
        # 注意：这里使用同步实现，实际生产环境建议使用异步 HTTP 客户端
        return self._generate(messages, stop, run_manager, **kwargs)
    
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        """
        流式生成聊天响应
        
        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 运行管理器
            **kwargs: 其他参数
            
        Yields:
            ChatGeneration 包含生成的消息片段
        """
        logger.debug("开始流式生成")
        
        # 转换消息格式
        api_messages = self._convert_messages(messages)
        
        # 准备请求参数
        request_body = {
            "model": self.config.model_name,
            "messages": api_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
        }
        
        if stop:
            request_body["stop"] = stop
        
        request_body.update(kwargs)
        
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
            # 流式请求
            with self._client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=request_body,
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        
                        import json
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield ChatGeneration(
                                    message=AIMessage(content=content)
                                )
                        except (json.JSONDecodeError, KeyError):
                            continue
                            
        except Exception as e:
            log_error(
                error_type="StreamError",
                message=str(e),
                details={},
            )
            raise
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """
        将 LangChain 消息格式转换为 API 格式
        
        Args:
            messages: LangChain 消息列表
            
        Returns:
            API 格式的消息列表
        """
        api_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                api_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                api_messages.append({"role": "assistant", "content": msg.content})
            else:
                # 处理其他类型的消息
                api_messages.append({"role": "user", "content": str(msg.content)})
        
        logger.debug(f"消息格式转换完成，共 {len(api_messages)} 条")
        return api_messages
    
    def switch_model(self, config: ModelConfig) -> None:
        """
        切换模型配置
        
        Args:
            config: 新的模型配置
        """
        self.config = config
        if self._client:
            self._client.close()
        self._init_client()
        logger.info(f"LangChain 模型已切换到：{config.model_name}")
    
    def close(self) -> None:
        """关闭客户端连接"""
        if self._client:
            self._client.close()
            logger.info("FatsiaChatModel 已关闭")
