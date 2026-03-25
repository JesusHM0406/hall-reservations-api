"""
Tests for Hall Management endpoints (Admin operations)

This module contains tests for:
- POST /halls/ - Create new hall
- PATCH /halls/{id} - Update hall
- PATCH /halls/{id}/availability - Update hall availability

Focuses on:
- Admin/Superadmin permissions (RBAC)
- Input validation
- Business logic (duplicate names, etc.)
- Edge cases
"""

from typing import Any, Callable

from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.models.hall import Hall
from app.models.reservation import Reservation
from app.models.reservation_status import ReservationStatus
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserComplete


class TestCreateHall:
  """Tests for POST /halls/ endpoint"""

  async def test_create_hall_success_admin(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Admin can successfully create a hall"""
    mock_auth(admin_user)

    hall_data: dict[str, Any] = {
      "name": "Main Hall",
      "description": "Large hall for events",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Main Hall"
    assert data["description"] == "Large hall for events"
    assert data["is_available"] is True
    assert "id" in data

  async def test_create_hall_success_superadmin(self, client: AsyncClient, superadmin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Superadmin can successfully create a hall"""
    mock_auth(superadmin_user)

    hall_data: dict[str, Any] = {
      "name": "Conference Room",
      "description": "Small conference room",
      "is_available": False
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Conference Room"
    assert data["is_available"] is False

  async def test_create_hall_duplicate_name(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Creating a hall with duplicate name should fail"""
    mock_auth(admin_user)

    # Create first hall
    existing_hall = Hall(
      name="Existing Hall",
      description="Already exists",
      is_available=True
    )
    db_session.add(existing_hall)
    await db_session.flush()

    # Try to create duplicate
    hall_data: dict[str, Any] = {
      "name": "Existing Hall",
      "description": "Different description",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == ErrorMessages.DUPLICATED_HALL_NAME

  async def test_create_hall_empty_name(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Creating a hall with empty name should fail"""
    mock_auth(admin_user)

    hall_data: dict[str, Any] = {
      "name": "",
      "description": "Valid long description",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_hall_whitespace_name(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Creating a hall with only whitespace name should fail"""
    mock_auth(admin_user)

    hall_data: dict[str, Any] = {
      "name": "   ",
      "description": "Valid long description",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_hall_empty_description(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Creating a hall with empty description should fail"""
    mock_auth(admin_user)

    hall_data: dict[str, Any] = {
      "name": "Valid Name",
      "description": "",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_hall_whitespace_description(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Creating a hall with only whitespace description should fail"""
    mock_auth(admin_user)

    hall_data: dict[str, Any] = {
      "name": "Valid Name",
      "description": "   ",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_hall_trims_whitespace(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Creating a hall should trim leading/trailing whitespace"""
    mock_auth(admin_user)

    hall_data: dict[str, Any] = {
      "name": "  Trimmed Hall  ",
      "description": "  This should be trimmed  ",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Trimmed Hall"
    assert data["description"] == "This should be trimmed"

  async def test_create_hall_long_name(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Creating a hall with name > 100 chars should fail"""
    mock_auth(admin_user)

    hall_data: dict[str, Any] = {
      "name": "A" * 101,
      "description": "Valid long description",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_hall_long_description(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Creating a hall with description > 1000 chars should fail"""
    mock_auth(admin_user)

    hall_data: dict[str, Any] = {
      "name": "ABCDEFGHIJ" * 11,
      "description": "Valid long description",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_hall_regular_user_forbidden(self, client: AsyncClient, regular_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Regular user cannot create a hall"""
    mock_auth(regular_user)

    hall_data: dict[str, Any] = {
      "name": "Test Hall",
      "description": "Description for the Hall",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS

  async def test_create_hall_unauthenticated(self, client: AsyncClient):
    """Unauthenticated user cannot create a hall"""
    hall_data: dict[str, Any] = {
      "name": "Test Hall",
      "description": "Description for the Hall",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

  async def test_create_hall_inactive_admin(self, client: AsyncClient, inactive_admin: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Inactive admin cannot create a hall"""
    mock_auth(inactive_admin)

    hall_data: dict[str, Any] = {
      "name": "Test Hall",
      "description": "Description for the Hall",
      "is_available": True
    }

    response = await client.post("/halls/", json=hall_data)

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INACTIVE_USER

  async def test_create_hall_missing_fields(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Creating a hall with missing required fields should fail"""
    mock_auth(admin_user)

    # Missing description
    response = await client.post("/halls/", json={
      "name": "Test Hall",
      "is_available": True
    })
    assert response.status_code == 422

    # Missing name
    response = await client.post("/halls/", json={
      "description": "Test Description for the Hall",
      "is_available": True
    })
    assert response.status_code == 422

    # Missing is_available
    response = await client.post("/halls/", json={
      "name": "Test Hall",
      "description": "Test Description for the Hall"
    })
    assert response.status_code == 422


class TestUpdateHall:
  """Tests for PATCH /halls/{id} endpoint"""

  async def test_update_hall_name_admin(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Admin can update hall name"""
    mock_auth(admin_user)

    hall = Hall(name="Old Name", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": "New Name",
      "description": None,
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Description"  # Unchanged
    assert data["is_available"] is True  # Unchanged

  async def test_update_hall_description_admin(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Admin can update hall description"""
    mock_auth(admin_user)

    hall = Hall(name="Hall", description="Old Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": None,
      "description": "New Description for the Hall",
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "New Description for the Hall"
    assert data["name"] == "Hall"  # Unchanged

  async def test_update_hall_availability_admin(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Admin can update hall availability via update endpoint"""
    mock_auth(admin_user)

    hall = Hall(name="Hall", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": None,
      "description": None,
      "is_available": False
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False

  async def test_update_hall_all_fields(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Admin can update all fields at once"""
    mock_auth(admin_user)

    hall = Hall(name="Old Name", description="Old Desc", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": "New Name",
      "description": "New Description for the Hall",
      "is_available": False
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New Description for the Hall"
    assert data["is_available"] is False

  async def test_update_hall_not_found(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Updating non-existent hall returns 404"""
    mock_auth(admin_user)

    update_data: dict[str, Any] = {
      "name": "New Name",
      "description": None,
      "is_available": None
    }

    response = await client.patch("/halls/99999", json=update_data)

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.HALL_NOT_FOUND

  async def test_update_hall_duplicate_name(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Updating hall name to existing name should fail"""
    mock_auth(admin_user)

    hall1 = Hall(name="Hall 1", description="Desc 1", is_available=True)
    hall2 = Hall(name="Hall 2", description="Desc 2", is_available=True)
    db_session.add_all([hall1, hall2])
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": "Hall 2",  # Already exists
      "description": None,
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall1.id}", json=update_data)

    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == ErrorMessages.DUPLICATED_HALL_NAME

  async def test_update_hall_same_name(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Updating hall with same name should succeed"""
    mock_auth(admin_user)

    hall = Hall(name="Hall Name", description="Old Desc", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": "Hall Name",  # Same name
      "description": "New Description for the Hall",
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Hall Name"
    assert data["description"] == "New Description for the Hall"

  async def test_update_hall_empty_name(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Updating hall with empty name should fail"""
    mock_auth(admin_user)

    hall = Hall(name="Hall Name", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": "",
      "description": None,
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_update_hall_whitespace_name(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Updating hall with whitespace-only name should fail"""
    mock_auth(admin_user)

    hall = Hall(name="Hall Name", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": "   ",
      "description": None,
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_update_hall_whitespace_description(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Updating hall with whitespace-only description should fail"""
    mock_auth(admin_user)

    hall = Hall(name="Hall Name", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": None,
      "description": "   ",
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_hall_trims_whitespace(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Updating hall should trim leading/trailing whitespace"""
    mock_auth(admin_user)

    hall = Hall(name="Old Name", description="Old Desc", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": "  New Name  ",
      "description": "  New Description For the Hall   ",
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New Description For the Hall"

  async def test_create_hall_regular_user_forbidden(self, client: AsyncClient, db_session: AsyncSession, regular_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Regular user cannot update a hall"""
    mock_auth(regular_user)

    hall = Hall(name="Hall", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": "New Name",
      "description": None,
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS

  async def test_create_hall_unauthenticated(self, client: AsyncClient, db_session: AsyncSession) -> None:
    """Unauthenticated user cannot update a hall"""
    hall = Hall(name="Hall", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {
      "name": "New Name",
      "description": None,
      "is_available": None
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

  async def test_disable_hall_with_confirmed_reservations_should_fail(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Disabling a hall with confirmed reservations should fail"""
    mock_auth(admin_user)

    # Create user, hall, and reservation
    user = User(name="Test User", pw_hash="hash", role=UserRole.USER, is_active=True)
    hall = Hall(name="Test Hall", description="Description", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() + timedelta(days=1),
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    # Try to disable the hall
    update_data: dict[str, Any] = {
      "name": None,
      "description": None,
      "is_available": False
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == ErrorMessages.HALL_HAS_CONFIRMED_RESERVATIONS

  async def test_disable_hall_with_only_cancelled_reservations_should_succeed(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Disabling a hall with only cancelled reservations should succeed"""
    mock_auth(admin_user)

    # Create user, hall, and cancelled reservation
    user = User(name="Test User", pw_hash="hash", role=UserRole.USER, is_active=True)
    hall = Hall(name="Test Hall", description="Description", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() + timedelta(days=1),
      status=ReservationStatus.CANCELLED
    )
    db_session.add(reservation)
    await db_session.flush()

    # Try to disable the hall
    update_data: dict[str, Any] = {
      "name": None,
      "description": None,
      "is_available": False
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False

  async def test_disable_hall_with_only_finished_reservations_should_succeed(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Disabling a hall with only finished reservations should succeed"""
    mock_auth(admin_user)

    # Create user, hall, and finished reservation
    user = User(name="Test User", pw_hash="hash", role=UserRole.USER, is_active=True)
    hall = Hall(name="Test Hall", description="Description", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() - timedelta(days=1),
      status=ReservationStatus.FINISHED
    )
    db_session.add(reservation)
    await db_session.flush()

    # Try to disable the hall
    update_data: dict[str, Any] = {
      "name": None,
      "description": None,
      "is_available": False
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False

  async def test_disable_hall_with_mixed_non_confirmed_reservations_should_succeed(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Disabling a hall with cancelled and finished reservations should succeed"""
    mock_auth(admin_user)

    # Create user, hall, and multiple reservations
    user = User(name="Test User", pw_hash="hash", role=UserRole.USER, is_active=True)
    hall = Hall(name="Test Hall", description="Description", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation1 = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() - timedelta(days=1),
      status=ReservationStatus.FINISHED
    )
    reservation2 = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() + timedelta(days=2),
      status=ReservationStatus.CANCELLED
    )
    db_session.add_all([reservation1, reservation2])
    await db_session.flush()

    # Try to disable the hall
    update_data: dict[str, Any] = {
      "name": None,
      "description": None,
      "is_available": False
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False

  async def test_enable_hall_with_confirmed_reservations_should_succeed(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Enabling a hall should always succeed regardless of reservations"""
    mock_auth(admin_user)

    # Create user, hall (already disabled), and reservation
    user = User(name="Test User", pw_hash="hash", role=UserRole.USER, is_active=True)
    hall = Hall(name="Test Hall", description="Description", is_available=False)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() + timedelta(days=1),
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    # Try to enable the hall
    update_data: dict[str, Any] = {
      "name": None,
      "description": None,
      "is_available": True
    }

    response = await client.patch(f"/halls/{hall.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is True


class TestUpdateHallAvailability:
  """Tests for PATCH /halls/{id}/availability endpoint"""

  async def test_update_availability_to_false(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Admin can update hall availability to false"""
    mock_auth(admin_user)

    hall = Hall(name="Hall", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {"is_available": False}

    response = await client.patch(f"/halls/{hall.id}/availability", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False
    assert data["name"] == "Hall"  # Other fields unchanged

  async def test_update_availability_to_true(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Admin can update hall availability to true"""
    mock_auth(admin_user)

    hall = Hall(name="Hall", description="Description", is_available=False)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {"is_available": True}

    response = await client.patch(f"/halls/{hall.id}/availability", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is True

  async def test_update_availability_not_found(self, client: AsyncClient, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Updating availability of non-existent hall returns 404"""
    mock_auth(admin_user)

    update_data: dict[str, Any] = {"is_available": False}

    response = await client.patch("/halls/99999/availability", json=update_data)

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.HALL_NOT_FOUND

  async def test_update_availability_regular_user_forbidden(self, client: AsyncClient, db_session: AsyncSession, regular_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Regular user cannot update hall availability"""
    mock_auth(regular_user)

    hall = Hall(name="Hall", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {"is_available": False}

    response = await client.patch(f"/halls/{hall.id}/availability", json=update_data)

    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS

  async def test_update_availability_unauthenticated(self, client: AsyncClient, db_session: AsyncSession):
    """Unauthenticated user cannot update hall availability"""
    hall = Hall(name="Hall", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    update_data: dict[str, Any] = {"is_available": False}

    response = await client.patch(f"/halls/{hall.id}/availability", json=update_data)

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

  async def test_update_availability_missing_field(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Updating availability without is_available field should fail"""
    mock_auth(admin_user)

    hall = Hall(name="Hall", description="Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    response = await client.patch(f"/halls/{hall.id}/availability", json={})

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_disable_availability_with_confirmed_reservations_should_fail(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Disabling availability for a hall with confirmed reservations should fail"""
    mock_auth(admin_user)

    # Create user, hall, and reservation
    user = User(name="Test User", pw_hash="hash", role=UserRole.USER, is_active=True)
    hall = Hall(name="Test Hall", description="Description", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() + timedelta(days=1),
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    # Try to disable the hall
    update_data: dict[str, Any] = {"is_available": False}

    response = await client.patch(f"/halls/{hall.id}/availability", json=update_data)

    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == ErrorMessages.HALL_HAS_CONFIRMED_RESERVATIONS

  async def test_disable_availability_with_only_cancelled_reservations_should_succeed(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Disabling availability for a hall with only cancelled reservations should succeed"""
    mock_auth(admin_user)

    # Create user, hall, and cancelled reservation
    user = User(name="Test User", pw_hash="hash", role=UserRole.USER, is_active=True)
    hall = Hall(name="Test Hall", description="Description", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() + timedelta(days=1),
      status=ReservationStatus.CANCELLED
    )
    db_session.add(reservation)
    await db_session.flush()

    # Try to disable the hall
    update_data: dict[str, Any] = {"is_available": False}

    response = await client.patch(f"/halls/{hall.id}/availability", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False

  async def test_disable_availability_with_only_finished_reservations_should_succeed(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Disabling availability for a hall with only finished reservations should succeed"""
    mock_auth(admin_user)

    # Create user, hall, and finished reservation
    user = User(name="Test User", pw_hash="hash", role=UserRole.USER, is_active=True)
    hall = Hall(name="Test Hall", description="Description", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() - timedelta(days=1),
      status=ReservationStatus.FINISHED
    )
    db_session.add(reservation)
    await db_session.flush()

    # Try to disable the hall
    update_data: dict[str, Any] = {"is_available": False}

    response = await client.patch(f"/halls/{hall.id}/availability", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False

  async def test_enable_availability_with_confirmed_reservations_should_succeed(self, client: AsyncClient, db_session: AsyncSession, admin_user: UserComplete, mock_auth: Callable[[UserComplete], None]):
    """Enabling availability for a hall should always succeed regardless of reservations"""
    mock_auth(admin_user)

    # Create user, hall (already disabled), and reservation
    user = User(name="Test User", pw_hash="hash", role=UserRole.USER, is_active=True)
    hall = Hall(name="Test Hall", description="Description", is_available=False)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=date.today() + timedelta(days=1),
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    # Try to enable the hall
    update_data: dict[str, Any] = {"is_available": True}

    response = await client.patch(f"/halls/{hall.id}/availability", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is True
