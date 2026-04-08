"""
Health API 路由
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any
import sys
import os

router = APIRouter(redirect_slashes=True)

# 服务启动时间（用于计算 uptime）
_start_time = datetime.now()


@router.get("/")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI Multi-Agent System"
    }


@router.get("/ping")
async def ping():
    """简单的 ping/pong 用于存活探针"""
    return {"ping": "pong", "timestamp": datetime.now().isoformat()}


@router.get("/uptime")
async def get_uptime():
    """获取服务运行时间"""
    delta = datetime.now() - _start_time
    return {
        "uptime_seconds": delta.total_seconds(),
        "uptime_human": str(delta).split(".")[0],
        "started_at": _start_time.isoformat(),
        "current_time": datetime.now().isoformat()
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """就绪检查"""
    checks = {
        "api": "ok",
        "vectorstore": "unknown",
        "memory": "unknown",
        "llm": "unknown"
    }

    try:
        # 检查向量存储
        from knowledge.vectorstore.chromadb_handler import ChromaDBHandler
        chroma = ChromaDBHandler()
        stats = chroma.get_collection_stats()
        checks["vectorstore"] = "ok" if stats else "error"
    except Exception as e:
        checks["vectorstore"] = f"error: {str(e)[:50]}"

    try:
        # 检查记忆系统
        from memory.short_term import short_term_memory
        stats = short_term_memory.get_stats()
        checks["memory"] = "ok" if stats else "error"
    except Exception as e:
        checks["memory"] = f"error: {str(e)[:50]}"

    try:
        # 检查LLM
        from core.llm import get_llm
        llm = get_llm()
        checks["llm"] = "configured" if llm else "not_configured"
    except Exception as e:
        checks["llm"] = f"error: {str(e)[:50]}"

    all_ok = all(v == "ok" or v == "configured" for v in checks.values())

    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks
    }


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """获取系统统计"""
    stats = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": os.name,
    }

    try:
        from memory.short_term import short_term_memory
        stats["memory"] = short_term_memory.get_stats()
    except:
        stats["memory"] = "error"

    try:
        from core.token_manager import token_manager
        stats["token"] = token_manager.get_status()
    except:
        stats["token"] = "error"

    return stats
