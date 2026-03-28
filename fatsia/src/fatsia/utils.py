"""
工具函数模块

提供常用的辅助函数，如环境变量加载、配置加载等。
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

from .logger_config import logger


def load_env_file(env_file: str = ".env") -> None:
    """
    加载环境变量文件
    
    Args:
        env_file: 环境变量文件路径，默认为 ".env"
        
    Note:
        如果文件不存在则静默跳过，不抛出异常
    """
    env_path = Path(env_file)
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            logger.info(f"已加载环境变量文件：{env_file}")
        except ImportError:
            logger.warning("python-dotenv 未安装，无法加载 .env 文件")
    else:
        logger.debug(f"环境变量文件不存在：{env_file}")


def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    获取环境变量值
    
    Args:
        name: 环境变量名称
        default: 默认值（如果环境变量不存在）
        
    Returns:
        环境变量的值，如果不存在则返回默认值
    """
    value = os.getenv(name, default)
    if value is None:
        logger.warning(f"环境变量 '{name}' 未设置")
    return value


def load_json_config(config_file: str) -> Dict[str, Any]:
    """
    从 JSON 文件加载配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置字典
        
    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON 格式错误
    """
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在：{config_file}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    logger.info(f"已加载配置文件：{config_file}")
    return config


def save_json_config(config: Dict[str, Any], config_file: str) -> None:
    """
    保存配置到 JSON 文件
    
    Args:
        config: 配置字典
        config_file: 配置文件路径
    """
    config_path = Path(config_file)
    
    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    logger.info(f"配置已保存到：{config_file}")


def format_token_count(count: int) -> str:
    """
    格式化 token 数量显示
    
    Args:
        count: token 数量
        
    Returns:
        格式化后的字符串，如 "1.5K", "2.3M"
    """
    if count < 1000:
        return str(count)
    elif count < 1_000_000:
        return f"{count / 1000:.1f}K"
    else:
        return f"{count / 1_000_000:.1f}M"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 要截断的文本
        max_length: 最大长度
        suffix: 截断后添加的后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
