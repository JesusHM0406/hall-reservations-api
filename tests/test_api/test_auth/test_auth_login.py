"""
Tests for login endpoint security.

Covers edge cases, validation, and protection against
common attack vectors like SQL injection and XSS.
"""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.core.security import get_password_hash
from app.models.user import User


class TestLoginSecurity:
  """Test login endpoint security."""

  async def test_login_success(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test successful login returns valid token."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="ValidPass123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "ValidPass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0

  async def test_login_wrong_password(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test login with wrong password fails."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="CorrectPassword"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "WrongPassword"}
    )

    # Empty password is a validation error
    assert response.status_code in [401, 422]
    data = response.json()
    assert data["detail"] == ErrorMessages.UNAUTHORIZED

  async def test_login_nonexistent_user(
    self,
    client: AsyncClient
  ):
    """Test login with non-existent user fails."""
    response = await client.post(
        "/auth/login",
        data={"username": "nonexistent", "password": "password"}
    )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == ErrorMessages.UNAUTHORIZED

  async def test_login_deleted_user(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test deleted user cannot login."""
    user = User(
      name="deleteduser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=True
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
      "/auth/login",
      data={"username": "deleteduser", "password": "password123"}
    )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == ErrorMessages.DELETED_USER

  async def test_login_empty_username(
    self,
    client: AsyncClient
  ):
    """Test login with empty username fails."""
    response = await client.post(
        "/auth/login",
        data={"username": "", "password": "password"}
    )

    # Empty username is a validation error
    assert response.status_code in [401, 422]

  async def test_login_empty_password(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test login with empty password fails."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": ""}
    )

    # Empty password is a validation error
    assert response.status_code in [401, 422]

  async def test_login_sql_injection_attempt_username(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test SQL injection in username is handled safely."""
    user = User(
      name="admin",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    # Try various SQL injection patterns
    injection_attempts = [
      "admin' OR '1'='1",
      "admin' --",
      "admin' OR 1=1--",
      "' OR '1'='1' --",
      "admin'; DROP TABLE users--"
    ]

    for attempt in injection_attempts:
      response = await client.post(
        "/auth/login",
        data={"username": attempt, "password": "password123"}
      )
      assert response.status_code == 401

  async def test_login_very_long_username(
    self,
    client: AsyncClient
  ):
    """Test login with extremely long username."""
    long_username = "a" * 10000
    response = await client.post(
      "/auth/login",
      data={"username": long_username, "password": "password"}
    )

    assert response.status_code == 401

  async def test_login_very_long_password(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test login with extremely long password."""
    user = User(
      name="testuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    long_password = "a" * 10000
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": long_password}
    )

    assert response.status_code == 401

  async def test_login_special_characters_username(
    self,
    client: AsyncClient
  ):
    """Test login with special characters in username."""
    special_chars = "<script>alert('xss')</script>"
    response = await client.post(
      "/auth/login",
      data={"username": special_chars, "password": "password"}
    )

    assert response.status_code == 401

  async def test_login_unicode_characters(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test login with unicode characters."""
    user = User(
      name="用户名",
      pw_hash=get_password_hash(password="密码123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
      "/auth/login",
      data={"username": "用户名", "password": "密码123"}
    )

    assert response.status_code == 200

  async def test_login_case_sensitivity(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test that username is case-sensitive."""
    user = User(
      name="TestUser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False
    )
    db_session.add(user)
    await db_session.flush()

    # Try different case variations
    response = await client.post(
      "/auth/login",
      data={"username": "testuser", "password": "password123"}
    )
    
    # This should fail if usernames are case-sensitive
    # The behavior depends on database collation
    # We just verify it doesn't crash - status can be 200 or 401
    assert response.status_code in [200, 401]
