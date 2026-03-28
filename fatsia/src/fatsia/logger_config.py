"""
日志配置模块

负责配置和管理整个项目的日志系统，所有 API 交互的报文都会记录到日志文件中。
日志文件保存在 ../logs/fatsia 目录下，按日期自动分割。
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


def setup_logger(
    name: str = "fatsia",
    log_dir: str = "../logs/fatsia",
    level: int = logging.DEBUG,
) -> logging.Logger:
    """
    设置并返回一个配置好的 logger 实例
    
    Args:
        name: logger 的名称，默认为 "fatsia"
        log_dir: 日志文件存储目录，相对于当前工作目录，默认为 "../logs/fatsia"
        level: 日志级别，默认为 DEBUG
        
    Returns:
        配置好的 logging.Logger 实例
    """
    # 获取项目根目录（src 的父目录）
    base_dir = Path(__file__).parent.parent.parent
    log_path = base_dir / log_dir
    
    # 确保日志目录存在
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 如果已经有处理器，不再重复添加
    if logger.handlers:
        return logger
    
    # 创建按天分割的文件处理器
    log_file = log_path / "fatsia.log"
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="D",  # 按天分割
        interval=1,
        backupCount=30,  # 保留 30 天的日志
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上级别
    
    # 设置日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到 logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 创建全局 logger 实例
logger = setup_logger()


def log_request(method: str, url: str, headers: dict, body: dict | None = None) -> None:
    """
    记录 HTTP 请求报文
    
    Args:
        method: HTTP 方法 (GET, POST 等)
        url: 请求 URL
        headers: 请求头
        body: 请求体（可选）
    """
    logger.info("=" * 80)
    logger.info("【HTTP REQUEST】")
    logger.info(f"Method: {method}")
    logger.info(f"URL: {url}")
    logger.info("Headers:")
    # 隐藏敏感信息
    safe_headers = {k: v for k, v in headers.items()}
    if "Authorization" in safe_headers:
        auth_value = safe_headers["Authorization"]
        if isinstance(auth_value, str) and auth_value.startswith("Bearer "):
            safe_headers["Authorization"] = f"Bearer {auth_value[:20]}...{auth_value[-5:]}"
    for key, value in safe_headers.items():
        logger.info(f"  {key}: {value}")
    if body:
        logger.info("Body:")
        logger.info(f"  {body}")
    logger.info("=" * 80)


def log_response(status_code: int, headers: dict, body: dict | str) -> None:
    """
    记录 HTTP 响应报文
    
    Args:
        status_code: HTTP 状态码
        headers: 响应头
        body: 响应体
    """
    logger.info("=" * 80)
    logger.info("【HTTP RESPONSE】")
    logger.info(f"Status Code: {status_code}")
    logger.info("Headers:")
    for key, value in headers.items():
        logger.info(f"  {key}: {value}")
    logger.info("Body:")
    if isinstance(body, (dict, list)):
        import json
        logger.info(f"  {json.dumps(body, ensure_ascii=False, indent=2)}")
    else:
        logger.info(f"  {body}")
    logger.info("=" * 80)


def log_error(error_type: str, message: str, details: dict | None = None) -> None:
    """
    记录错误信息
    
    Args:
        error_type: 错误类型
        message: 错误消息
        details: 详细信息（可选）
    """
    logger.error("=" * 80)
    logger.error(f"【ERROR】{error_type}")
    logger.error(f"Message: {message}")
    if details:
        logger.error("Details:")
        logger.error(f"  {details}")
    logger.error("=" * 80)
