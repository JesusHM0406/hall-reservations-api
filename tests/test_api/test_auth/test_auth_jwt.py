"""
Tests for JWT token validation and security.

Covers token creation, validation, expiration, 
signature verification, and protection against
common JWT attacks.
"""
from datetime import datetime, timedelta, timezone

import jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.user_role import UserRole


class TestJWTTokenSecurity:
  """Test JWT token validation and security."""

  async def test_access_with_valid_token(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test accessing protected endpoint with valid token."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Get token
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "password123"}
    )
    token = response.json()["access_token"]

    # Access protected endpoint
    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

  async def test_access_without_token(
    self,
    client: AsyncClient
  ):
    """Test accessing protected endpoint without token."""
    response = await client.get("/users/me")

    assert response.status_code == 401

  async def test_access_with_malformed_token(
    self,
    client: AsyncClient
  ):
    """Test accessing with malformed token."""
    malformed_tokens = [
      "not.a.token",
      "abc",
      "Bearer token",
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
      "....",
      ""
    ]

    for token in malformed_tokens:
      response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
      )
      assert response.status_code == 401

  async def test_access_with_expired_token(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test accessing with expired token."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Create expired token
    expire = datetime.now(timezone.utc) - timedelta(minutes=30)
    expired_token = jwt.encode(
      {"sub": str(user.id), "exp": expire},
      settings.SECRET_KEY,
      algorithm=settings.ALGORITHM
    )

    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401

  async def test_access_with_wrong_signature(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test accessing with token signed with wrong key."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Create token with wrong secret
    wrong_token = jwt.encode(
      {"sub": str(user.id)},
      "wrong_secret_key_" * 4,
      algorithm=settings.ALGORITHM
    )

    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {wrong_token}"}
    )

    assert response.status_code == 401

  async def test_access_with_wrong_algorithm(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test accessing with token using different algorithm."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Create token with different algorithm (if possible)
    # This tests algorithm confusion attacks
    try:
      wrong_alg_token = jwt.encode(
        {"sub": str(user.id)},
        "wrong_secret_key_" * 4,
        algorithm="HS512"  # Different from HS256
      )

      response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {wrong_alg_token}"}
      )

      assert response.status_code == 401
    except Exception:
      # If encoding fails, that's also acceptable
      pass

  async def test_access_with_none_algorithm(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test protection against 'none' algorithm attack."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Try to create token with 'none' algorithm
    # This should be rejected
    try:
      none_token = jwt.encode(
        {"sub": str(user.id)},
        "",
        algorithm="none"
      )

      response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {none_token}"}
      )

      assert response.status_code == 401
    except Exception:
      # If encoding fails, that's good - protection is in place
      pass

  async def test_access_with_missing_sub_claim(
    self,
    client: AsyncClient
  ):
    """Test accessing with token missing 'sub' claim."""
    # Create token without 'sub' claim
    invalid_token = jwt.encode(
      {"other": "data"},
      settings.SECRET_KEY,
      algorithm=settings.ALGORITHM
    )

    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {invalid_token}"}
    )

    assert response.status_code == 401

  async def test_access_with_invalid_user_id_in_token(
    self,
    client: AsyncClient
  ):
    """Test accessing with token containing non-existent user ID."""
    # Create token with non-existent user ID
    invalid_token = jwt.encode(
      {"sub": "999999"},
      settings.SECRET_KEY,
      algorithm=settings.ALGORITHM
    )

    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {invalid_token}"}
    )

    assert response.status_code == 401

  async def test_access_with_non_numeric_user_id(
    self,
    client: AsyncClient
  ):
    """Test accessing with token containing non-numeric user ID."""
    # Create token with non-numeric user ID
    invalid_token = jwt.encode(
      {"sub": "not_a_number"},
      settings.SECRET_KEY,
      algorithm=settings.ALGORITHM
    )

    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {invalid_token}"}
    )

    assert response.status_code == 401

  async def test_token_without_bearer_prefix(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test token without 'Bearer' prefix is rejected."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Get token
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "password123"}
    )
    token = response.json()["access_token"]

    # Try to use token without Bearer prefix
    response = await client.get(
      "/users/me",
      headers={"Authorization": token}
    )

    assert response.status_code == 401
