"""Unit tests for authentication and token services."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock
from jose import jwt, JWTError

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_stream_token,
    decode_stream_token,
    create_session,
    revoke_session,
    KONG_JWT_ISSUER,
)
from app.config import settings


def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(pwd, "invalid_hash_string") is False


def test_create_and_decode_access_token():
    token, expires_in = create_access_token(
        user_id=10,
        username="john_doe",
        user_type="EMPLOYEE",
        org_id=2,
        customer_id=None,
        roles=["OPERATOR"],
        permissions=["camera.live", "camera.playback"],
        session_id="test-session-uuid-1234",
        expires_in=3600,
    )

    assert isinstance(token, str)
    assert expires_in == 3600

    payload = decode_access_token(token)
    assert payload["iss"] == KONG_JWT_ISSUER
    assert payload["sub"] == "10"
    assert payload["username"] == "john_doe"
    assert payload["user_type"] == "EMPLOYEE"
    assert payload["org_id"] == 2
    assert payload["customer_id"] is None
    assert "OPERATOR" in payload["roles"]
    assert "camera.live" in payload["permissions"]
    assert payload["session_id"] == "test-session-uuid-1234"
    assert payload["type"] == "access"


def test_decode_expired_access_token():
    # Create an expired token (expires_in = -10 seconds)
    token, _ = create_access_token(
        user_id=10,
        username="john_doe",
        user_type="EMPLOYEE",
        org_id=None,
        customer_id=None,
        roles=["VIEWER"],
        permissions=[],
        session_id="test-session-uuid",
        expires_in=-10,
    )

    with pytest.raises(JWTError):
        decode_access_token(token)


def test_decode_tampered_access_token():
    token, _ = create_access_token(
        user_id=10,
        username="john_doe",
        user_type="EMPLOYEE",
        org_id=None,
        customer_id=None,
        roles=["VIEWER"],
        permissions=[],
        session_id="test-session-uuid",
    )

    # Tamper with the token string
    tampered = token[:-5] + "ABCDE"
    with pytest.raises(JWTError):
        decode_access_token(tampered)


def test_create_and_decode_stream_token():
    token = create_stream_token(
        cam_id="CAMKRTVM0001",
        username="operator1",
        expires_in=300,
    )

    assert isinstance(token, str)
    payload = decode_stream_token(token)
    assert payload["sub"] == "operator1"
    assert payload["path"] == "CAMKRTVM0001"
    assert payload["type"] == "stream"


def test_decode_expired_stream_token():
    token = create_stream_token(
        cam_id="CAMKRTVM0001",
        username="operator1",
        expires_in=-5,
    )
    with pytest.raises(JWTError):
        decode_stream_token(token)


@pytest.mark.asyncio
async def test_create_and_revoke_session():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()

    session_id = await create_session(
        db=mock_db,
        user_id=42,
        ip_address="192.168.1.50",
        device_name="Chrome on Linux",
        device_type="web",
        expires_in_seconds=3600,
    )

    assert isinstance(session_id, str)
    assert len(session_id) > 10
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()

    # Test revoke session
    mock_session_obj = MagicMock()
    mock_session_obj.is_active = True
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_session_obj
    mock_db.execute.return_value = mock_result

    await revoke_session(mock_db, session_id)
    assert mock_session_obj.is_active is False
    mock_db.flush.assert_called()
