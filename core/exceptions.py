"""
统一异常处理模块
=================

【架构改进 - ADR-003】
解决各API路由重复异常处理的问题
"""

from fastapi import HTTPException, status
from typing import Optional, Any
import traceback
import uuid


class APIException(HTTPException):
    """统一API异常基类"""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_id: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.error_id = error_id or str(uuid.uuid4())[:8]
        self.message = message
        self.details = details
        super().__init__(
            status_code=status_code,
            detail={
                "error_id": self.error_id,
                "message": self.message,
                "details": self.details
            }
        )


class NotFoundError(APIException):
    """资源未找到"""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.NOT_FOUND,
            message=f"{resource} not found",
            details={"resource": resource, "id": resource_id}
        )


class ValidationError(APIException):
    """验证失败"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.BAD_REQUEST,
            message=message,
            details={"field": field} if field else None
        )


class UnauthorizedError(APIException):
    """未授权"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            status_code=status.UNAUTHORIZED,
            message=message
        )


class ForbiddenError(APIException):
    """禁止访问"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            status_code=status.FORBIDDEN,
            message=message
        )


class RateLimitError(APIException):
    """限流"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.TOO_MANY_REQUESTS,
            message="Rate limit exceeded",
            details={"retry_after": retry_after}
        )


class InternalServerError(APIException):
    """内部错误"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            status_code=status.INTERNAL_SERVER_ERROR,
            message=message
        )


class ServiceUnavailableError(APIException):
    """服务不可用"""
    def __init__(self, service: str):
        super().__init__(
            status_code=status.SERVICE_UNAVAILABLE,
            message=f"Service unavailable: {service}",
            details={"service": service}
        )


def generate_error_id() -> str:
    """生成错误ID"""
    return str(uuid.uuid4())[:8]


def format_exception(exc: Exception) -> dict:
    """格式化异常信息"""
    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
        "error_id": generate_error_id()
    }
