"""
Fatsia - 多模型 AI 交互库

主入口模块，导出所有公共 API
"""

from .config import ModelConfig, ModelType
from .client import FatsiaClient
from .langchain_wrapper import FatsiaChatModel
from .openai_compatible import FatsiaOpenAIClient, create_compatible_client
from .logger_config import logger, log_request, log_response, log_error
from .utils import load_env_file, get_env_var

__version__ = "0.1.0"
__author__ = "Fatsia Team"

__all__ = [
    # 核心类
    "ModelConfig",
    "ModelType",
    "FatsiaClient",
    "FatsiaChatModel",
    "FatsiaOpenAIClient",
    
    # 工具函数
    "create_compatible_client",
    "load_env_file",
    "get_env_var",
    
    # 日志相关
    "logger",
    "log_request",
    "log_response",
    "log_error",
]
