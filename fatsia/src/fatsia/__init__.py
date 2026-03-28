"""
Fatsia - 支持多模型切换的 LangChain 交互库

支持模型：
- 千问 3 (Qwen3)
- OpenAI GPT 系列
- Google Gemini 系列

所有交互都支持完整的报文日志记录
"""

__version__ = "0.1.0"
__author__ = "Fatsia Team"

from .config import ModelConfig, ModelType
from .client import FatsiaClient
from .langchain_wrapper import FatsiaChatModel
from .openai_compatible import FatsiaOpenAIClient, create_compatible_client
from .logger_config import logger
from .utils import load_env_file

__all__ = [
    "ModelConfig",
    "ModelType",
    "FatsiaClient",
    "FatsiaChatModel",
    "FatsiaOpenAIClient",
    "create_compatible_client",
    "load_env_file",
    "logger",
]
