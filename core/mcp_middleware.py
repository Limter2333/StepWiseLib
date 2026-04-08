"""
MCP中间件 - MCP Middleware
==========================

【功能】
在API请求中自动管理上下文窗口
- 请求开始: 加载/创建上下文
- 请求结束: 保存上下文
- 自动压缩: 防止超出token限制
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Callable, Optional
import uuid

from mcp.context_manager import (
    ContextManager,
    ContextPriority,
    get_context_manager
)


class MCPContextMiddleware(BaseHTTPMiddleware):
    """MCP上下文中间件

    【工作流程】
    1. 请求进入 → 从请求头获取session_id
    2. 获取对应session的ContextManager
    3. 将ContextManager附加到request.state
    4. 请求处理完后自动保存上下文
    """

    # 每个会话的上下文管理器缓存
    _session_contexts: dict = {}

    def __init__(self, app, max_tokens: int = 4000):
        super().__init__(app)
        self.max_tokens = max_tokens

    async def dispatch(self, request: Request, call_next: Callable):
        # 生成或获取session_id
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            session_id = str(uuid.uuid4())

        # 获取或创建该session的上下文管理器
        if session_id not in self._session_contexts:
            self._session_contexts[session_id] = ContextManager(
                max_tokens=self.max_tokens
            )

        context_manager = self._session_contexts[session_id]

        # 附加到request.state
        request.state.context_manager = context_manager
        request.state.session_id = session_id

        # 处理请求
        response = await call_next(request)

        # 在响应头中返回session_id（如果是新生成的）
        if "X-Session-ID" not in request.headers:
            response.headers["X-Session-ID"] = session_id

        return response

    @classmethod
    def get_context_manager(cls, session_id: str) -> Optional[ContextManager]:
        """获取指定session的上下文管理器"""
        return cls._session_contexts.get(session_id)

    @classmethod
    def clear_session(cls, session_id: str):
        """清除指定session的上下文"""
        if session_id in cls._session_contexts:
            del cls._session_contexts[session_id]

    @classmethod
    def clear_all(cls):
        """清除所有session的上下文"""
        cls._session_contexts.clear()
