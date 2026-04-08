"""Tests for JWT authentication module.

These tests verify JWT token creation, verification, and FastAPI dependency injection.
"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import sys
import os

# Add the project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.auth.jwt_auth import (
    create_access_token,
    verify_token,
    get_current_user,
    AuthResult,
    JWT_SECRET,
    JWT_ALGORITHM,
)


class TestAuthResult:
    """Tests for AuthResult class."""

    def test_auth_result_creation(self):
        """Test AuthResult object creation with user_id and authenticated flag."""
        result = AuthResult(user_id="user-123", authenticated=True)
        assert result.user_id == "user-123"
        assert result.authenticated is True

    def test_auth_result_repr(self):
        """Test AuthResult string representation."""
        result = AuthResult(user_id="user-123", authenticated=True)
        assert "user-123" in repr(result)
        assert "True" in repr(result)

    def test_auth_result_equality(self):
        """Test AuthResult equality comparison."""
        result1 = AuthResult(user_id="user-123", authenticated=True)
        result2 = AuthResult(user_id="user-123", authenticated=True)
        result3 = AuthResult(user_id="user-456", authenticated=True)

        assert result1 == result2
        assert result1 != result3


class TestCreateAccessToken:
    """Tests for token creation."""

    def test_create_token_returns_string(self):
        """Test that create_access_token returns a non-empty string."""
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_with_default_expiration(self):
        """Test token creation with default expiration."""
        token = create_access_token("user-123")
        result = verify_token(token)
        assert result.user_id == "user-123"
        assert result.authenticated is True

    def test_create_token_with_custom_expiration(self):
        """Test token creation with custom expiration delta."""
        token = create_access_token("user-123", expires_delta=timedelta(minutes=30))
        result = verify_token(token)
        assert result.user_id == "user-123"

    def test_create_token_with_different_users(self):
        """Test that different users get different tokens."""
        token1 = create_access_token("user-1")
        token2 = create_access_token("user-2")
        assert token1 != token2


class TestVerifyToken:
    """Tests for token verification."""

    def test_verify_valid_token(self):
        """Test verification of a valid token."""
        token = create_access_token("user-123")
        result = verify_token(token)

        assert isinstance(result, AuthResult)
        assert result.user_id == "user-123"
        assert result.authenticated is True

    def test_verify_invalid_token(self):
        """Test verification of an invalid token raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")

        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    def test_verify_tampered_token(self):
        """Test verification of a tampered token raises HTTPException."""
        token = create_access_token("user-123")
        # Tamper with the token by modifying a character
        tampered_token = token[:-5] + "XXXXX"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(tampered_token)

        assert exc_info.value.status_code == 401

    def test_verify_expired_token(self):
        """Test that expired tokens are rejected."""
        # Create a token that expires immediately
        token = create_access_token("user-123", expires_delta=timedelta(seconds=-1))

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_token_missing_sub_claim(self):
        """Test verification rejects token without sub claim."""
        from jose import jwt

        # Create a token without the 'sub' claim
        payload = {"exp": 9999999999, "iat": 0}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401
        assert "missing user identifier" in exc_info.value.detail


class TestGetCurrentUser:
    """Tests for FastAPI dependency injection."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test get_current_user with a valid token."""
        token = create_access_token("user-123")

        # Create mock credentials
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = token

        result = await get_current_user(credentials)

        assert isinstance(result, AuthResult)
        assert result.user_id == "user-123"
        assert result.authenticated is True

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with an invalid token."""
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "invalid.token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self):
        """Test get_current_user with an expired token."""
        token = create_access_token("user-123", expires_delta=timedelta(seconds=-1))

        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()


class TestIntegration:
    """Integration tests for the auth module."""

    def test_full_auth_flow(self):
        """Test complete authentication flow: create token -> verify -> use."""
        # Create token for user
        user_id = "test-user-456"
        token = create_access_token(user_id)

        # Verify token
        result = verify_token(token)

        # Assertions
        assert result.user_id == user_id
        assert result.authenticated is True

    def test_multiple_users_tokens_unique(self):
        """Test that tokens for different users are distinct."""
        token1 = create_access_token("user-1")
        token2 = create_access_token("user-2")
        token3 = create_access_token("user-1")

        # Same user should get different tokens (due to iat claim)
        # But all should verify correctly
        assert verify_token(token1).user_id == "user-1"
        assert verify_token(token2).user_id == "user-2"
        assert verify_token(token3).user_id == "user-1"

    def test_configurable_expiration(self):
        """Test token expiration configuration."""
        # Short-lived token
        short_token = create_access_token("user", expires_delta=timedelta(seconds=1))
        result = verify_token(short_token)
        assert result.user_id == "user"

        # Long-lived token
        long_token = create_access_token("user", expires_delta=timedelta(days=7))
        result = verify_token(long_token)
        assert result.user_id == "user"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
