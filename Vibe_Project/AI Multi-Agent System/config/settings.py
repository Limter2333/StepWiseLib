"""
配置管理模块 Settings
=====================

【学习要点】
1. 为什么需要配置管理？
   - 环境分离（开发/测试/生产）
   - 敏感信息保护（API密钥等）
   - 统一配置避免硬编码

2. 配置方式
   - .env文件: 环境变量
   - YAML/JSON: 配置文件
   - config.py: Python配置对象

3. 12-Factor App原则
   - 配置与代码分离
   - 环境变量作为配置源
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """应用配置

    【学习要点】Pydantic Settings
    - 自动环境变量绑定
    - 类型验证
    - 默认值设置
    - 敏感信息隐藏

    环境变量命名规则: SNAKE_CASE
    例如: database_url -> DATABASE_URL
    """

    # ========== 项目基础配置 ==========
    PROJECT_NAME: str = "AI Multi-Agent System"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ========== API配置 ==========
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # ========== LangChain/LangGraph配置 ==========
    LLM_PROVIDER: str = "anthropic"  # anthropic / openai / local
    LLM_MODEL: str = "claude-3-sonnet-20240229"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096

    # ========== 向量数据库配置 ==========

    # ChromaDB (学习/开发用)
    CHROMA_PERSIST_DIR: str = "G:/claude_code_project/data/chromadb"
    CHROMA_COLLECTION_NAME: str = "knowledge_base"

    # Milvus (生产用)
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""
    MILVUS_COLLECTION_NAME: str = "knowledge_base"

    # ========== 文档解析配置 ==========
    SUPPORTED_DOC_TYPES: List[str] = ["pdf", "docx", "txt", "html", "url"]
    CHUNK_SIZE: int = 500          # 文本块大小
    CHUNK_OVERLAP: int = 50        # 文本块重叠
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ========== RAG配置 ==========
    RAG_TOP_K: int = 5             # 检索返回数量
    RAG_SCORE_THRESHOLD: float = 0.5  # 相似度阈值

    # ========== Token配置 ==========
    MAX_TOKENS_PER_CYCLE: int = 1500
    TOKEN_RESET_HOURS: int = 5

    # ========== 记忆配置 ==========
    SHORT_TERM_MEMORY_TTL: int = 3600    # 1小时
    LONG_TERM_MEMORY_DB: str = "G:/claude_code_project/data/memory.db"

    # ========== MCP配置 ==========
    MCP_SERVERS: List[str] = ["filesystem", "web_search"]

    # ========== 安全配置 ==========
    GUARDRAIL_ENABLED: bool = True
    MAX_INPUT_LENGTH: int = 10000

    # =========: 日志配置 ==========
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "G:/claude_code_project/logs"

    # MiniMax API配置 (通过环境变量ANTHROPIC_API_KEY等传入)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_BASE_URL: Optional[str] = None
    ANTHROPIC_MODEL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # 允许额外字段（如MiniMax特定配置）
    )


# 全局配置实例
settings = Settings()


# ========== 配置使用示例 ==========
"""
【学习要点】如何在代码中使用配置

from config.settings import settings

# 1. 直接访问
db_url = settings.DATABASE_URL

# 2. 环境变量覆盖
# DATABASE_URL=postgresql://... python app.py
# 会自动覆盖默认值

# 3. 类型验证
# settings.API_PORT = "not_a_number"  # 会抛出ValidationError
"""
