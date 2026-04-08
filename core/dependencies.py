"""
依赖注入模块
=============

【架构改进 - ADR-001】
解决全局单例问题，使用FastAPI Depends()进行依赖注入
"""

from functools import lru_cache
from typing import Generator, Optional
import asyncio

# 导入核心模块
from core.guardrails import guardrails, Guardrails
from core.token_manager import token_manager, TokenManager
from memory.short_term import short_term_memory, ShortTermMemory
from memory.long_term import long_term_memory, LongTermMemory


# ============================================================================
# Guardrails 依赖注入
# ============================================================================

@lru_cache()
def get_guardrails() -> Guardrails:
    """获取Guardrails单例（带缓存）"""
    return guardrails


async def get_guardrails_async() -> Guardrails:
    """异步获取Guardrails"""
    return guardrails


# ============================================================================
# Token Manager 依赖注入
# ============================================================================

@lru_cache()
def get_token_manager() -> TokenManager:
    """获取TokenManager单例（带缓存）"""
    return token_manager


# ============================================================================
# Short Term Memory 依赖注入
# ============================================================================

@lru_cache()
def get_short_term_memory() -> ShortTermMemory:
    """获取ShortTermMemory单例（带缓存）"""
    return short_term_memory


# ============================================================================
# Long Term Memory 依赖注入
# ============================================================================

@lru_cache()
def get_long_term_memory() -> LongTermMemory:
    """获取LongTermMemory单例（带缓存）"""
    return long_term_memory


# ============================================================================
# RAG Pipeline 依赖注入
# ============================================================================

_rag_pipeline_instance: Optional["RAGPipeline"] = None
_rag_pipeline_lock = asyncio.Lock()


async def get_rag_pipeline() -> "RAGPipeline":
    """获取RAGPipeline单例（线程安全）"""
    global _rag_pipeline_instance

    if _rag_pipeline_instance is None:
        async with _rag_pipeline_lock:
            if _rag_pipeline_instance is None:
                from knowledge.rag_pipeline import RAGPipeline
                _rag_pipeline_instance = RAGPipeline()

    return _rag_pipeline_instance


# ============================================================================
# VectorStore 依赖注入
# ============================================================================

@lru_cache()
def get_chroma_handler() -> "ChromaDBHandler":
    """获取ChromaDBHandler单例"""
    from knowledge.vectorstore.chromadb_handler import ChromaDBHandler
    return ChromaDBHandler()


# ============================================================================
# Agent依赖注入
# ============================================================================

@lru_cache()
def get_task_router():
    """获取TaskRouter单例"""
    from agents.orchestrator.task_router import task_router
    return task_router


@lru_cache()
def get_conversation_agent():
    """获取ConversationAgent单例"""
    from agents.conversation_agent.conversation_agent import conversation_agent
    return conversation_agent


@lru_cache()
def get_dev_agent():
    """获取DevAgent单例"""
    from agents.dev_agent import dev_agent
    return dev_agent


@lru_cache()
def get_doc_agent():
    """获取DocAgent单例"""
    from agents.doc_agent import doc_agent
    return doc_agent


@lru_cache()
def get_test_agent():
    """获取TestAgent单例"""
    from agents.test_agent import test_agent
    return test_agent


@lru_cache()
def get_rag_agent():
    """获取RAGAgent单例"""
    from agents.rag_agent import rag_agent
    return rag_agent


@lru_cache()
def get_pm_agent():
    """获取PMAgent单例"""
    from agents.pm_agent import pm_agent
    return pm_agent


# ============================================================================
# 错误日志依赖注入
# ============================================================================

@lru_cache()
def get_error_logger():
    """获取ErrorLogger单例"""
    from logs.error_logs.error_logger import error_logger
    return error_logger
