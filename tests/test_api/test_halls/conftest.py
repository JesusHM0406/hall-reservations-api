"""
Fixtures for Hall Management tests

Provides reusable components for setting up test scenarios.
"""

from typing import Any, Callable, Generator

import pytest
from app.main import app
from app.models.user_role import UserRole
from app.schemas.user import UserComplete
from app.api.deps import get_current_user


@pytest.fixture
def admin_user() -> UserComplete:
  """Fixture providing an active admin user mock"""
  return UserComplete(
    id=999,
    name="admin",
    role=UserRole.ADMIN,
    is_active=True,
    is_deleted=False
  )


@pytest.fixture
def superadmin_user() -> UserComplete:
  """Fixture providing an active superadmin user mock"""
  return UserComplete(
    id=999,
    name="superadmin",
    role=UserRole.SUPERADMIN,
    is_active=True,
    is_deleted=False
  )


@pytest.fixture
def regular_user() -> UserComplete:
  """Fixture providing a regular user mock"""
  return UserComplete(
    id=1,
    name="user",
    role=UserRole.USER,
    is_active=True,
    is_deleted=False
  )


@pytest.fixture
def inactive_admin() -> UserComplete:
  """Fixture providing an inactive admin user mock"""
  return UserComplete(
    id=999,
    name="admin",
    role=UserRole.ADMIN,
    is_active=False,
    is_deleted=False
  )


@pytest.fixture
def mock_auth(admin_user: UserComplete) -> Generator[Callable[[UserComplete], None], Any, Any]:
  """
  Fixture to set up and tear down authentication overrides.
  
  Usage:
    def test_something(self, client, mock_auth):
      mock_auth(admin_user)
      # test code here
  """
  def set_user(user: UserComplete) -> None:
    app.dependency_overrides[get_current_user] = lambda: user
  
  yield set_user
  
  # Cleanup is handled by client fixture's teardown
