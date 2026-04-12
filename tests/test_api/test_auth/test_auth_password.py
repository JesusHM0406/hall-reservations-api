"""
Tests for password hashing and security.

Verifies that passwords are properly hashed, never stored
in plain text, and never exposed in responses.
"""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.models.user_role import UserRole


class TestPasswordSecurity:
  """Test password security features."""

  async def test_password_is_hashed(
    self,
    db_session: AsyncSession
  ):
    """Test that passwords are properly hashed in database."""
    plain_password = "MySecurePassword123"
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password=plain_password),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    # Verify password hash is not the plain password
    assert user.pw_hash != plain_password
    # Verify hash starts with expected bcrypt/argon2 prefix
    assert user.pw_hash.startswith("$")  # Both bcrypt and argon2 hashes start with $
    assert len(user.pw_hash) > 50  # Hashed passwords are long

  async def test_same_password_different_hashes(
    self
  ):
    """Test that same password produces different hashes (salt)."""
    password = "SamePassword123"
    hash1 = get_password_hash(password=password)
    hash2 = get_password_hash(password=password)

    # Hashes should be different due to salt
    assert hash1 != hash2

  async def test_password_not_returned_in_responses(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that password/hash is never returned in API responses."""
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

    # Get user info
    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "password" not in data
    assert "pw_hash" not in data
    assert "password_hash" not in data
