"""
配置模块

定义模型类型枚举和配置类，支持一键切换不同的 AI 模型。
通过简单的参数配置即可在千问 3、OpenAI GPT、Google Gemini 之间切换。
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ModelType(str, Enum):
    """
    支持的模型类型枚举
    
    属性:
        QWEN: 阿里云通义千问 模型
        OPENAI: OpenAI GPT 系列模型
        GEMINI: Google Gemini 系列模型
    """
    QWEN= "qwen"  # 千问
    OPENAI = "openai"  # OpenAI GPT
    GEMINI = "gemini"  # Google Gemini


class ModelConfig(BaseModel):
    """
    模型配置类
    
    用于配置不同模型的 API 参数，支持热切换。
    所有敏感信息（如 API Key）建议通过环境变量管理。
    
    Attributes:
        model_type: 模型类型，决定使用哪个 AI 服务提供商
        api_key: API 密钥
        base_url: API 基础 URL
        model_name: 具体模型名称
        timeout: 请求超时时间（秒）
        max_tokens: 最大生成 token 数
        temperature: 温度参数，控制随机性 (0-2)
    """
    
    # 模型类型
    model_type: ModelType = Field(
        default=ModelType.QWEN,
        description="模型类型：qwen, openai, gemini"
    )
    
    # API 密钥
    api_key: str = Field(
        default="",
        description="API 密钥，建议从环境变量读取"
    )
    
    # API 基础 URL
    base_url: str = Field(
        default="",
        description="API 基础 URL"
    )
    
    # 模型名称
    model_name: str = Field(
        default="",
        description="具体模型名称"
    )
    
    # 请求超时时间（秒）
    timeout: int = Field(
        default=60,
        description="请求超时时间（秒）"
    )
    
    # 最大生成 token 数
    max_tokens: int = Field(
        default=2048,
        description="最大生成 token 数"
    )
    
    # 温度参数
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="温度参数，控制随机性 (0-2)"
    )
    
    model_config = ConfigDict(use_enum_values=True)
    
    @classmethod
    def create_qwen3_config(
        cls,
        api_key: str,
        model_name: str = "qwen3-max-2026-01-23",
        # model_name: str = "qwen-image-max",
        timeout: int = 60,
    ) -> "ModelConfig":
        """
        创建千问 3 模型配置
        
        Args:
            api_key: 阿里云 DashScope API Key
            model_name: 模型名称，默认 "qwen-plus"
            timeout: 请求超时时间
            
        Returns:
            ModelConfig 实例
        """
        return cls(
            model_type=ModelType.QWEN,
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name=model_name,
            timeout=timeout,
        )
    
    @classmethod
    def create_openai_config(
        cls,
        api_key: str,
        model_name: str = "gpt-4o",
        timeout: int = 60,
    ) -> "ModelConfig":
        """
        创建 OpenAI 模型配置
        
        Args:
            api_key: OpenAI API Key
            model_name: 模型名称，默认 "gpt-4o"
            timeout: 请求超时时间
            
        Returns:
            ModelConfig 实例
        """
        return cls(
            model_type=ModelType.OPENAI,
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            model_name=model_name,
            timeout=timeout,
        )
    
    @classmethod
    def create_gemini_config(
        cls,
        api_key: str,
        model_name: str = "gemini-1.5-pro",
        timeout: int = 60,
    ) -> "ModelConfig":
        """
        创建 Google Gemini 模型配置
        
        Args:
            api_key: Google AI Studio API Key
            model_name: 模型名称，默认 "gemini-1.5-pro"
            timeout: 请求超时时间
            
        Returns:
            ModelConfig 实例
        """
        return cls(
            model_type=ModelType.GEMINI,
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            model_name=model_name,
            timeout=timeout,
        )
    
    def switch_model(
        self,
        model_type: ModelType | str,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        """
        动态切换模型
        
        Args:
            model_type: 新的模型类型
            api_key: 新的 API Key（可选，不提供则保持原值）
            model_name: 新的模型名称（可选，不提供则使用默认值）
        """
        if isinstance(model_type, str):
            model_type = ModelType(model_type.lower())
        
        self.model_type = model_type
        
        if api_key:
            self.api_key = api_key
        
        # 根据模型类型设置默认的 base_url 和 model_name
        if model_type == ModelType.QWEN:
            self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            self.model_name = model_name or "qwen-plus"
        elif model_type == ModelType.OPENAI:
            self.base_url = "https://api.openai.com/v1"
            self.model_name = model_name or "gpt-4o"
        elif model_type == ModelType.GEMINI:
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
            self.model_name = model_name or "gemini-1.5-pro"
