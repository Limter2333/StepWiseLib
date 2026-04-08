"""
MCP路由 - MCP Routes
====================

【功能】
- 获取/设置上下文
- 添加上下文片段
- 手动压缩上下文
- 获取上下文统计
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()


class AddContextRequest(BaseModel):
    """添加上下文请求"""
    content: str
    priority: int = 1  # 0-3, 0=LOW, 1=MEDIUM, 2=HIGH, 3=CRITICAL
    metadata: Optional[Dict[str, Any]] = None


class AddContextResponse(BaseModel):
    """添加上下文响应"""
    success: bool
    context_id: str
    current_tokens: int
    max_tokens: int


class ContextStatsResponse(BaseModel):
    """上下文统计响应"""
    session_id: str
    current_tokens: int
    max_tokens: int
    utilization: str
    segment_count: int
    total_adds: int
    total_compressions: int


class ContextSegmentResponse(BaseModel):
    """上下文片段响应"""
    id: str
    content: str
    priority: str
    tokens: int
    metadata: Dict[str, Any]


class MCPRoutes:
    """MCP路由处理类"""

    @staticmethod
    def get_context_manager(request: Request):
        """从request获取context_manager"""
        if not hasattr(request.state, "context_manager"):
            raise HTTPException(status_code=500, detail="Context manager not initialized")
        return request.state.context_manager


@router.post("/context/add", response_model=AddContextResponse)
async def add_context(request: Request, body: AddContextRequest):
    """添加上下文片段

    【参数】
    - content: 上下文内容
    - priority: 优先级 (0-LOW, 1-MEDIUM, 2-HIGH, 3-CRITICAL)
    - metadata: 元数据（可选）

    【返回】
    - context_id: 上下文的唯一ID
    - current_tokens: 当前token使用量
    """
    ctx_mgr = MCPRoutes.get_context_manager(request)

    from mcp.context_manager import ContextPriority
    priority_map = {
        0: ContextPriority.LOW,
        1: ContextPriority.MEDIUM,
        2: ContextPriority.HIGH,
        3: ContextPriority.CRITICAL
    }
    priority = priority_map.get(body.priority, ContextPriority.MEDIUM)

    context_id = ctx_mgr.add_context(
        content=body.content,
        priority=priority,
        metadata=body.metadata
    )

    stats = ctx_mgr.get_stats()

    return AddContextResponse(
        success=True,
        context_id=context_id,
        current_tokens=stats["current_tokens"],
        max_tokens=stats["max_tokens"]
    )


@router.get("/context/stats", response_model=ContextStatsResponse)
async def get_stats(request: Request):
    """获取上下文统计

    【返回】
    - session_id: 会话ID
    - current_tokens: 当前token使用量
    - max_tokens: 最大token限制
    - utilization: 使用率百分比
    - segment_count: 片段数量
    - total_adds: 累计添加次数
    - total_compressions: 累计压缩次数
    """
    ctx_mgr = MCPRoutes.get_context_manager(request)
    session_id = request.state.session_id
    stats = ctx_mgr.get_stats()

    return ContextStatsResponse(
        session_id=session_id,
        current_tokens=stats["current_tokens"],
        max_tokens=stats["max_tokens"],
        utilization=stats["utilization"],
        segment_count=stats["segment_count"],
        total_adds=stats["total_adds"],
        total_compressions=stats["total_compressions"]
    )


@router.get("/context/segments", response_model=List[ContextSegmentResponse])
async def get_segments(request: Request):
    """获取所有上下文片段"""
    ctx_mgr = MCPRoutes.get_context_manager(request)
    segments = ctx_mgr.get_context_with_metadata()

    return [
        ContextSegmentResponse(
            id=seg["id"],
            content=seg["content"],
            priority=seg["priority"],
            tokens=seg["tokens"],
            metadata=seg.get("metadata", {})
        )
        for seg in segments
    ]


@router.get("/context/content")
async def get_context_content(request: Request) -> Dict[str, Any]:
    """获取完整上下文内容"""
    ctx_mgr = MCPRoutes.get_context_manager(request)
    content = ctx_mgr.get_context()

    return {
        "session_id": request.state.session_id,
        "content": content,
        "stats": ctx_mgr.get_stats()
    }


@router.post("/context/clear")
async def clear_context(request: Request) -> Dict[str, Any]:
    """清空当前会话的上下文"""
    ctx_mgr = MCPRoutes.get_context_manager(request)
    ctx_mgr.clear()

    return {
        "success": True,
        "message": "Context cleared",
        "session_id": request.state.session_id
    }


@router.post("/context/compress")
async def compress_context(request: Request) -> Dict[str, Any]:
    """手动触发上下文压缩"""
    ctx_mgr = MCPRoutes.get_context_manager(request)

    original_tokens = ctx_mgr.window.total_tokens

    # 调用ContextManager内置的压缩方法
    ctx_mgr._compress()

    new_tokens = ctx_mgr.window.total_tokens

    return {
        "success": True,
        "original_tokens": original_tokens,
        "new_tokens": new_tokens,
        "saved_tokens": original_tokens - new_tokens,
        "session_id": request.state.session_id
    }


@router.get("/history")
async def get_history(request: Request, limit: int = 10) -> Dict[str, Any]:
    """获取上下文历史记录"""
    ctx_mgr = MCPRoutes.get_context_manager(request)
    history = ctx_mgr.get_history_summary(limit=limit)

    return {
        "session_id": request.state.session_id,
        "history": history,
        "total_entries": len(ctx_mgr.history)
    }
