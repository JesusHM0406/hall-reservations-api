"""
Tests for role-based access control and user status validation.

Verifies that deleted/inactive users cannot access endpoints
and that role-based permissions are properly enforced.
"""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.core.security import get_password_hash
from app.models.user import User
from app.models.user_role import UserRole


class TestUserStatusSecurity:
  """Test security around user status (active/deleted)."""

  async def test_deleted_user_cannot_access_endpoints(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test deleted user cannot access protected endpoints."""
    user = User(
      name="deleteduser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Get token before deletion
    response = await client.post(
      "/auth/login",
      data={"username": "deleteduser", "password": "password123"}
    )
    token = response.json()["access_token"]

    # Mark user as deleted
    user.is_deleted = True
    await db_session.flush()

    # Try to access endpoint with old token
    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.USER_NOT_FOUND

  async def test_inactive_user_cannot_access_endpoints(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test inactive user cannot access protected endpoints."""
    user = User(
      name="inactiveuser",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.USER
    )
    db_session.add(user)
    await db_session.flush()

    # Get token before deactivation
    response = await client.post(
      "/auth/login",
      data={"username": "inactiveuser", "password": "password123"}
    )
    token = response.json()["access_token"]

    # Deactivate user
    user.is_active = False
    await db_session.flush()

    # Try to access endpoint with old token
    response = await client.get(
      "/users/me",
      headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INACTIVE_USER


class TestAccessControlSecurity:
  """Test role-based access control security."""

  async def test_regular_user_cannot_access_admin_endpoints(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test regular user cannot access admin endpoints."""
    user = User(
      name="regularuser",
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
      data={"username": "regularuser", "password": "password123"}
    )
    token = response.json()["access_token"]

    # Try to access admin endpoint (e.g., list all users)
    response = await client.get(
      "/users/",
      headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS

  async def test_admin_can_access_admin_endpoints(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test admin can access admin endpoints."""
    admin = User(
      name="admin",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.ADMIN
    )
    db_session.add(admin)
    await db_session.flush()

    # Get token
    response = await client.post(
      "/auth/login",
      data={"username": "admin", "password": "password123"}
    )
    token = response.json()["access_token"]

    # Access admin endpoint
    response = await client.get(
      "/users/",
      headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

  async def test_superadmin_can_access_admin_endpoints(
    self,
    client: AsyncClient,
    db_session: AsyncSession
  ):
    """Test superadmin can access admin endpoints."""
    superadmin = User(
      name="superadmin",
      pw_hash=get_password_hash(password="password123"),
      is_active=True,
      is_deleted=False,
      role=UserRole.SUPERADMIN
    )
    db_session.add(superadmin)
    await db_session.flush()

    # Get token
    response = await client.post(
      "/auth/login",
      data={"username": "superadmin", "password": "password123"}
    )
    token = response.json()["access_token"]

    # Access admin endpoint
    response = await client.get(
      "/users/",
      headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
