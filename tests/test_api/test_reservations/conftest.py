"""
Fixtures for Reservation tests

Provides reusable components for setting up test scenarios.
"""

from typing import Any, Callable, Generator
from datetime import date, timedelta

import pytest
from app.main import app
from app.models.user_role import UserRole
from app.schemas.user import UserComplete
from app.schemas.reservation import ReservationCreate
from app.api.deps import get_current_user


@pytest.fixture
def regular_user() -> UserComplete:
  """Fixture providing a regular user mock"""
  return UserComplete(
    id=1,
    name="regular_user",
    role=UserRole.USER,
    is_active=True,
    is_deleted=False
  )


@pytest.fixture
def another_regular_user() -> UserComplete:
  """Fixture providing another regular user mock"""
  return UserComplete(
    id=2,
    name="another_user",
    role=UserRole.USER,
    is_active=True,
    is_deleted=False
  )


@pytest.fixture
def admin_user() -> UserComplete:
  """Fixture providing an active admin user mock"""
  return UserComplete(
    id=998,
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
def superadmin_user_2() -> UserComplete:
  """Fixture providing a second superadmin user mock"""
  return UserComplete(
    id=997,
    name="superadmin2",
    role=UserRole.SUPERADMIN,
    is_active=True,
    is_deleted=False
  )


@pytest.fixture
def inactive_user() -> UserComplete:
  """Fixture providing an inactive user mock"""
  return UserComplete(
    id=3,
    name="inactive_user",
    role=UserRole.USER,
    is_active=False,
    is_deleted=False
  )


@pytest.fixture
def deleted_user() -> UserComplete:
  """Fixture providing a deleted user mock"""
  return UserComplete(
    id=4,
    name="deleted_user",
    role=UserRole.USER,
    is_active=True,
    is_deleted=True
  )


@pytest.fixture
def mock_auth() -> Generator[Callable[[UserComplete], None], Any, Any]:
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


@pytest.fixture
def tomorrow() -> date:
  """Fixture providing tomorrow's date"""
  return date.today() + timedelta(days=1)


@pytest.fixture
def future_date() -> date:
  """Fixture providing a date 7 days in the future"""
  return date.today() + timedelta(days=7)


@pytest.fixture
def far_future_date() -> date:
  """Fixture providing a date 6 months in the future"""
  return date.today() + timedelta(days=180)


@pytest.fixture
def max_future_date() -> date:
  """Fixture providing the maximum allowed future date (1 year)"""
  return date.today() + timedelta(days=365)


@pytest.fixture
def past_date() -> date:
  """Fixture providing yesterday's date"""
  return date.today() - timedelta(days=1)


@pytest.fixture
def today() -> date:
  """Fixture providing today's date"""
  return date.today()


# ============================================================================
# Helper functions for building schema-compliant request/response objects
# ============================================================================
# These helpers prevent test failures when API schema field names change

def build_create_reservation_request(
  hall_id: int,
  reservation_date: date
) -> dict[str, Any]:
  """
  Build a ReservationCreate request payload using the schema definition.
  
  This creates a ReservationCreate instance and serializes it to JSON-compatible
  format. If the schema structure changes, this automatically adapts.
  
  Args:
    hall_id: Hall ID for the reservation
    reservation_date: Date for the reservation
    
  Returns:
    Dictionary with the schema-compliant field names and types
  """
  # Create schema instance with provided data
  schema_instance = ReservationCreate(
    hall_id=hall_id,
    reservation_date=reservation_date
  )
  
  # Serialize to dict with proper JSON types (dates become ISO strings)
  return schema_instance.model_dump(mode="json")
