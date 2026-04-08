"""JWT Bearer Token Authentication for FastAPI.

This module provides JWT authentication middleware and dependency injection
for the AI Multi-Agent System. It supports token creation, verification,
and optional endpoint protection via FastAPI dependencies.
"""

from typing import Optional

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os

# Configuration from environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

security = HTTPBearer()


class AuthResult:
    """Authentication result containing user identity and auth status.

    Attributes:
        user_id: The unique identifier of the authenticated user.
        authenticated: Boolean indicating if authentication was successful.
    """

    def __init__(self, user_id: str, authenticated: bool):
        self.user_id = user_id
        self.authenticated = authenticated

    def __repr__(self) -> str:
        return f"AuthResult(user_id={self.user_id!r}, authenticated={self.authenticated})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AuthResult):
            return NotImplemented
        return self.user_id == other.user_id and self.authenticated == other.authenticated


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for the given user.

    Args:
        user_id: The unique identifier of the user.
        expires_delta: Optional custom expiration time delta. If not provided,
                      defaults to JWT_EXPIRATION_HOURS from configuration.

    Returns:
        Encoded JWT token string.

    Example:
        >>> token = create_access_token("user-123")
        >>> len(token) > 0
        True
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> AuthResult:
    """Verify and decode a JWT token.

    Args:
        token: The JWT token string to verify.

    Returns:
        AuthResult object containing user_id and authentication status.

    Raises:
        HTTPException: 401 status with detail message if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user identifier",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AuthResult(user_id=user_id, authenticated=True)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AuthResult:
    """FastAPI dependency for authenticated endpoints.

    This dependency can be used to protect endpoints that require
    a valid JWT Bearer token. It extracts and verifies the token
    from the Authorization header.

    Args:
        credentials: HTTPBearer credentials extracted from request header.

    Returns:
        AuthResult containing the authenticated user's ID.

    Raises:
        HTTPException: 401 if token is missing, invalid, or expired.

    Example:
        >>> @app.get("/protected")
        ... async def protected_route(user: AuthResult = Depends(get_current_user)):
        ...     return {"user_id": user.user_id}
    """
    token = credentials.credentials
    return verify_token(token)
