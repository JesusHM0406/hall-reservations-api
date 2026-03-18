"""
Tests for Reservation Creation

This module contains tests for:
- POST /reservations/ - Create new reservation

Focuses on:
- Successful reservation creation
- Input validation (dates, hall_id)
- Business logic (user validation, hall validation, conflicts)
- Edge cases
- RBAC (authenticated users only)
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
from app.schemas.user import UserComplete
from .conftest import build_create_reservation_request


class TestCreateReservationSuccess:
  """Tests for successful reservation creation"""

  async def test_create_reservation_success_regular_user(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Regular user can successfully create a reservation"""
    mock_auth(regular_user)

    # Create user in db
    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    # Create available hall
    hall = Hall(name="Test Hall", description="Test Description", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation_data = build_create_reservation_request(hall.id, tomorrow)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 201
    data = response.json()
    assert data["hall_id"] == hall.id
    assert data["user_id"] == regular_user.id
    assert data["status"] == ReservationStatus.CONFIRMED.value
    assert data["reservation_date"] == tomorrow.isoformat()
    assert "id" in data

  async def test_create_reservation_admin_user(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    future_date: date
  ):
    """Admin can create reservations for themselves"""
    mock_auth(admin_user)

    # Create admin in db
    user = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", is_active=True, role=admin_user.role)
    db_session.add(user)

    hall = Hall(name="Admin Hall", description="Hall for admins", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation_data = build_create_reservation_request(hall.id, future_date)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == admin_user.id

  async def test_create_reservation_superadmin_user(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    future_date: date
  ):
    """Superadmin can create reservations for themselves"""
    mock_auth(superadmin_user)

    user = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", is_active=True, role=superadmin_user.role)
    db_session.add(user)

    hall = Hall(name="Superadmin Hall", description="Hall for superadmins", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation_data = build_create_reservation_request(hall.id, future_date)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == superadmin_user.id

  async def test_create_reservation_far_future_date(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    far_future_date: date
  ):
    """Can create reservation up to 6 months in advance"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Future Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation_data = build_create_reservation_request(hall.id, far_future_date)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 201

  async def test_create_reservation_max_future_date(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    max_future_date: date
  ):
    """Can create reservation up to 1 year in advance (max limit)"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Max Future Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation_data = build_create_reservation_request(hall.id, max_future_date)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 201


class TestCreateReservationValidation:
  """Tests for input validation"""

  async def test_create_reservation_past_date(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    past_date: date
  ):
    """Cannot create reservation with past date"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    # Use hardcoded dict to test invalid date validation (intentionally send past date)
    reservation_data: dict[str, Any] = {
      "hall_id": hall.id,
      "reservation_date": past_date.isoformat()
    }

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_reservation_today(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """Cannot create reservation for today"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    # Use hardcoded dict to test invalid date validation (intentionally send today's date)
    reservation_data: dict[str, Any] = {
      "hall_id": hall.id,
      "reservation_date": today.isoformat()
    }

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_reservation_too_far_future(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Cannot create reservation more than 1 year in advance"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    too_far_date = date.today() + timedelta(days=366)  # Over 1 year
    # Use hardcoded dict to test invalid date validation (intentionally send date > 1 year)
    reservation_data: dict[str, Any] = {
      "hall_id": hall.id,
      "reservation_date": too_far_date.isoformat()
    }

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_reservation_invalid_hall_id_zero(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot create reservation with hall_id = 0"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)
    await db_session.flush()

    # Use hardcoded dict to test invalid hall_id validation (intentionally send 0)
    reservation_data: dict[str, Any] = {
      "hall_id": 0,
      "reservation_date": tomorrow.isoformat()
    }

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_reservation_invalid_hall_id_negative(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot create reservation with negative hall_id"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)
    await db_session.flush()

    # Use hardcoded dict to test invalid hall_id validation (intentionally send negative)
    reservation_data: dict[str, Any] = {
      "hall_id": -1,
      "reservation_date": tomorrow.isoformat()
    }

    response = await client.post("/reservations/", json=reservation_data)


    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_reservation_missing_hall_id(
    self, 
    client: AsyncClient, 
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot create reservation without hall_id"""
    mock_auth(regular_user)

    reservation_data: dict[str, Any] = {
      "reservation_date": tomorrow.isoformat()
    }

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_reservation_missing_date(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Cannot create reservation without reservation_date"""
    mock_auth(regular_user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation_data: dict[str, Any] = {
      "hall_id": hall.id
    }

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

  async def test_create_reservation_invalid_date_format(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Cannot create reservation with invalid date format"""
    mock_auth(regular_user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation_data: dict[str, Any] = {
      "hall_id": hall.id,
      "reservation_date": "invalid-date"
    }

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


class TestCreateReservationBusinessLogic:
  """Tests for business logic validation"""

  async def test_create_reservation_nonexistent_hall(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot create reservation for nonexistent hall"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)
    await db_session.flush()

    reservation_data: dict[str, Any] = build_create_reservation_request(hall_id=99999, reservation_date=tomorrow)  # Non-existent hall_id

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.HALL_NOT_FOUND

  async def test_create_reservation_unavailable_hall(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot create reservation for unavailable hall"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Unavailable Hall", description="Test", is_available=False)
    db_session.add(hall)
    await db_session.flush()

    reservation_data = build_create_reservation_request(hall.id, tomorrow)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.UNAVAILABLE_HALL

  async def test_create_reservation_inactive_user(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    inactive_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Inactive user cannot create reservation"""
    mock_auth(inactive_user)

    user = User(id=inactive_user.id, name=inactive_user.name, pw_hash="hash", is_active=False)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation_data: dict[str, Any] = build_create_reservation_request(hall_id=hall.id, reservation_date=tomorrow)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INACTIVE_USER

  async def test_create_reservation_deleted_user(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    deleted_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Deleted user cannot create reservation"""
    mock_auth(deleted_user)

    user = User(id=deleted_user.id, name=deleted_user.name, pw_hash="hash", is_active=True, is_deleted=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation_data: dict[str, Any] = build_create_reservation_request(hall_id=hall.id, reservation_date=tomorrow)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.USER_NOT_FOUND


class TestCreateReservationConflicts:
  """Tests for reservation conflicts"""

  async def test_create_reservation_duplicate_confirmed(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot create reservation if hall is already reserved for that date"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    db_session.add_all([user1, user2])

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    # Create existing reservation
    existing_reservation = Reservation(
      user_id=user2.id,
      hall_id=hall.id,
      reservation_date=tomorrow,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(existing_reservation)
    await db_session.flush()

    # Try to create conflicting reservation
    reservation_data: dict[str, Any] = build_create_reservation_request(hall_id=hall.id, reservation_date=tomorrow)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == ErrorMessages.DUPLICATED_RESERVATION

  async def test_create_reservation_after_cancelled(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Can create reservation if previous one was cancelled"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    db_session.add_all([user1, user2])

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    # Create cancelled reservation
    cancelled_reservation = Reservation(
      user_id=user2.id,
      hall_id=hall.id,
      reservation_date=tomorrow,
      status=ReservationStatus.CANCELLED
    )
    db_session.add(cancelled_reservation)
    await db_session.flush()

    # Should be able to create new reservation (cancelled doesn't block)
    reservation_data: dict[str, Any] = build_create_reservation_request(hall_id=hall.id, reservation_date=tomorrow)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 201

  async def test_create_reservation_after_finished(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Can create reservation if previous one was finished"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    db_session.add_all([user1, user2])

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    # Create finished reservation
    finished_reservation = Reservation(
      user_id=user2.id,
      hall_id=hall.id,
      reservation_date=tomorrow,
      status=ReservationStatus.FINISHED
    )
    db_session.add(finished_reservation)
    await db_session.flush()

    # Should be able to create new reservation (finished doesn't block)
    reservation_data: dict[str, Any] = build_create_reservation_request(hall_id=hall.id, reservation_date=tomorrow)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 201

  async def test_create_reservation_same_user_different_halls(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User can create multiple reservations on same date for different halls"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall1 = Hall(name="Hall 1", description="Test", is_available=True)
    hall2 = Hall(name="Hall 2", description="Test", is_available=True)
    db_session.add_all([hall1, hall2])
    await db_session.flush()

    # Create first reservation
    reservation1 = Reservation(
      user_id=user.id,
      hall_id=hall1.id,
      reservation_date=tomorrow,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation1)
    await db_session.flush()

    # Should be able to create second reservation for different hall
    reservation_data: dict[str, Any] = build_create_reservation_request(hall_id=hall2.id, reservation_date=tomorrow)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 201

  async def test_create_reservation_same_hall_different_dates(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date,
    future_date: date
  ):
    """User can create multiple reservations for same hall on different dates"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    # Create first reservation
    reservation1 = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=tomorrow,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation1)
    await db_session.flush()

    # Should be able to create second reservation for different date
    reservation_data: dict[str, Any] = build_create_reservation_request(hall_id=hall.id, reservation_date=future_date)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 201


class TestCreateReservationAuth:
  """Tests for authentication and authorization"""

  async def test_create_reservation_unauthenticated(
    self, 
    client: AsyncClient,
    tomorrow: date
  ):
    """Unauthenticated user cannot create reservation"""
    reservation_data: dict[str, Any] = build_create_reservation_request(hall_id=1, reservation_date=tomorrow)

    response = await client.post("/reservations/", json=reservation_data)

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"
