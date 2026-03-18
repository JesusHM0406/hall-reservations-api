"""Tests for reservation retrieval endpoints.

This file keeps retrieval-focused assertions (payload shape, not-found,
unauthenticated access, and /me behavior).
Role matrix RBAC assertions are centralized in test_reservation_rbac.py.
"""

from typing import Callable
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


class TestGetSingleReservation:
  """Tests for GET /reservations/{id}"""

  async def test_get_own_reservation_regular_user(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User can get their own reservation"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=tomorrow,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == reservation.id
    assert data["user_id"] == user.id
    assert data["user_name"] == user.name
    assert data["hall_id"] == hall.id
    assert data["hall_name"] == hall.name
    assert data["status"] == ReservationStatus.CONFIRMED.value
    assert data["reservation_date"] == tomorrow.isoformat()

  async def test_get_nonexistent_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Getting non-existent reservation returns 404"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)
    await db_session.flush()

    response = await client.get("/reservations/99999")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.RESERVATION_NOT_FOUND

  async def test_get_reservation_unauthenticated(
    self, 
    client: AsyncClient
  ):
    """Unauthenticated user cannot get reservation"""
    response = await client.get("/reservations/1")

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

class TestGetAllReservations:
  """Tests for GET /reservations/ (admin endpoint)"""

  async def test_get_all_reservations_unauthenticated(
    self, 
    client: AsyncClient
  ):
    """Unauthenticated user cannot access admin endpoint"""
    response = await client.get("/reservations/")

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

  async def test_get_all_reservations_admin_empty(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Admin can get empty list of reservations"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    await db_session.flush()

    response = await client.get("/reservations/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 0
    assert data["total"] == 0

  async def test_get_all_reservations_admin_with_data(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Admin can get list of regular user reservations"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user1 = User(id=1, name="user1", pw_hash="hash1", is_active=True)
    user2 = User(id=2, name="user2", pw_hash="hash2", is_active=True)
    db_session.add_all([admin, user1, user2])

    hall1 = Hall(name="Hall 1", description="Test", is_available=True)
    hall2 = Hall(name="Hall 2", description="Test", is_available=True)
    db_session.add_all([hall1, hall2])
    await db_session.flush()

    res1 = Reservation(user_id=user1.id, hall_id=hall1.id, reservation_date=tomorrow)
    res2 = Reservation(user_id=user2.id, hall_id=hall2.id, reservation_date=tomorrow)
    db_session.add_all([res1, res2])
    await db_session.flush()

    response = await client.get("/reservations/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2



class TestGetMyReservations:
  """Tests for GET /reservations/me"""

  async def test_get_my_reservations_empty(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """User can get empty list of their own reservations"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)
    await db_session.flush()

    response = await client.get("/reservations/me")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 0
    assert data["total"] == 0

  async def test_get_my_reservations_with_data(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User can get their own reservations"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall1 = Hall(name="Hall 1", description="Test", is_available=True)
    hall2 = Hall(name="Hall 2", description="Test", is_available=True)
    db_session.add_all([hall1, hall2])
    await db_session.flush()

    res1 = Reservation(user_id=user.id, hall_id=hall1.id, reservation_date=tomorrow)
    res2 = Reservation(user_id=user.id, hall_id=hall2.id, reservation_date=tomorrow + timedelta(days=1))
    db_session.add_all([res1, res2])
    await db_session.flush()

    response = await client.get("/reservations/me")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert all(item["user_id"] == user.id for item in data["items"])

  async def test_get_my_reservations_only_mine(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User only sees their own reservations, not others"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    db_session.add_all([user1, user2])

    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    my_res = Reservation(user_id=user1.id, hall_id=hall.id, reservation_date=tomorrow)
    other_res = Reservation(user_id=user2.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1))
    db_session.add_all([my_res, other_res])
    await db_session.flush()

    response = await client.get("/reservations/me")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert data["items"][0]["user_id"] == user1.id

  async def test_get_my_reservations_unauthenticated(
    self, 
    client: AsyncClient
  ):
    """Unauthenticated user cannot access /me endpoint"""
    response = await client.get("/reservations/me")

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

  async def test_get_my_reservations_admin(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Admin can get their own reservations via /me endpoint"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash2", is_active=True)
    db_session.add_all([admin, user])

    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    admin_res = Reservation(user_id=admin.id, hall_id=hall.id, reservation_date=tomorrow)
    user_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1))
    db_session.add_all([admin_res, user_res])
    await db_session.flush()

    response = await client.get("/reservations/me")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["user_id"] == admin.id

  async def test_get_my_reservations_superadmin(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Superadmin can get their own reservations via /me endpoint"""
    mock_auth(superadmin_user)

    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", role=UserRole.SUPERADMIN, is_active=True)
    db_session.add(superadmin)

    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    res = Reservation(user_id=superadmin.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res)
    await db_session.flush()

    response = await client.get("/reservations/me")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["user_id"] == superadmin.id
