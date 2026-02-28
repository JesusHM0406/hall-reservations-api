"""
Tests for Reservation RBAC (Role-Based Access Control)

This module contains comprehensive tests for role-based access control:
- Regular users can only see/modify their own reservations
- Admins can see/modify user and admin reservations, but NOT superadmin reservations
- Superadmins can see/modify ALL reservations
- All roles can create reservations for themselves
- Ownership validation for status transitions

Critical Security Rules:
- Admins CANNOT see or modify superadmin information
- Only superadmins can access superadmin data
- Regular users CANNOT use protected admin endpoints
"""

from typing import Callable
from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.models.hall import Hall
from app.models.reservation import Reservation
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserComplete


class TestRBACGetSingleReservation:
  """RBAC tests for getting a single reservation"""

  async def test_user_cannot_see_other_user_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User CANNOT see another user's reservation"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user1, user2, hall])
    await db_session.flush()

    reservation = Reservation(user_id=user2.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.RESERVATION_FROM_OTHER_USER

  async def test_user_cannot_see_admin_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User CANNOT see admin's reservation"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash2", role=UserRole.ADMIN, is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user, admin, hall])
    await db_session.flush()

    reservation = Reservation(user_id=admin.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.RESERVATION_FROM_OTHER_USER

  async def test_user_cannot_see_superadmin_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    superadmin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User CANNOT see superadmin's reservation"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash2", role=UserRole.SUPERADMIN, is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user, superadmin, hall])
    await db_session.flush()

    reservation = Reservation(user_id=superadmin.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.RESERVATION_FROM_OTHER_USER

  async def test_admin_can_see_user_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    admin_user: UserComplete,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Admin CAN see regular user's reservation"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash2", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    reservation = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 200

  async def test_admin_can_see_other_admin_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Admin CAN see another admin's reservation"""
    mock_auth(admin_user)

    admin1 = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    admin2 = User(id=100, name="admin2", pw_hash="hash2", role=UserRole.ADMIN, is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin1, admin2, hall])
    await db_session.flush()

    reservation = Reservation(user_id=admin2.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 200

  async def test_admin_CANNOT_see_superadmin_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    admin_user: UserComplete,
    superadmin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Admin CANNOT see superadmin's reservation - CRITICAL SECURITY RULE"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash2", role=UserRole.SUPERADMIN, is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, superadmin, hall])
    await db_session.flush()

    reservation = Reservation(user_id=superadmin.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 404  # Pretend it doesn't exist
    assert response.json()["message"] == ErrorMessages.RESERVATION_NOT_FOUND

  async def test_superadmin_can_see_user_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Superadmin CAN see user reservation"""
    mock_auth(superadmin_user)

    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", role=UserRole.SUPERADMIN, is_active=True)
    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash2", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([superadmin, user, hall])
    await db_session.flush()

    reservation = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 200

  async def test_superadmin_can_see_admin_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Superadmin CAN see admin reservation"""
    mock_auth(superadmin_user)

    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", role=UserRole.SUPERADMIN, is_active=True)
    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash2", role=UserRole.ADMIN, is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([superadmin, admin, hall])
    await db_session.flush()

    reservation = Reservation(user_id=admin.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 200

  async def test_superadmin_can_see_other_superadmin_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    superadmin_user_2: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Superadmin CAN see another superadmin's reservation"""
    mock_auth(superadmin_user)

    superadmin1 = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", role=UserRole.SUPERADMIN, is_active=True)
    superadmin2 = User(id=superadmin_user_2.id, name=superadmin_user_2.name, pw_hash="hash2", role=UserRole.SUPERADMIN, is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([superadmin1, superadmin2, hall])
    await db_session.flush()

    reservation = Reservation(user_id=superadmin2.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    assert response.status_code == 200


class TestRBACGetAllReservations:
  """RBAC tests for GET /reservations/ (admin endpoint)"""

  async def test_user_CANNOT_access_admin_endpoint(
    self, 
    client: AsyncClient,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Regular user CANNOT access GET /reservations/ endpoint"""
    mock_auth(regular_user)

    response = await client.get("/reservations/")

    assert response.status_code == 403
    assert response.json()["detail"] == ErrorMessages.NOT_ENOUGH_PERMISSIONS

  async def test_admin_can_access_admin_endpoint(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Admin CAN access GET /reservations/ endpoint"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    await db_session.flush()

    response = await client.get("/reservations/")

    assert response.status_code == 200

  async def test_superadmin_can_access_admin_endpoint(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Superadmin CAN access GET /reservations/ endpoint"""
    mock_auth(superadmin_user)

    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", role=UserRole.SUPERADMIN, is_active=True)
    db_session.add(superadmin)
    await db_session.flush()

    response = await client.get("/reservations/")

    assert response.status_code == 200

  async def test_admin_list_excludes_superadmin_reservations(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date,
    future_date: date,
    far_future_date: date
  ):
    """Admin list EXCLUDES superadmin reservations - CRITICAL SECURITY RULE"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True)
    superadmin1 = User(id=999, name="superadmin1", pw_hash="hash2", role=UserRole.SUPERADMIN, is_active=True)
    superadmin2 = User(id=997, name="superadmin2", pw_hash="hash3", role=UserRole.SUPERADMIN, is_active=True)  # Changed from 998 to 997
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, superadmin1, superadmin2, hall])
    await db_session.flush()

    user_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    super1_res = Reservation(user_id=superadmin1.id, hall_id=hall.id, reservation_date=future_date)  # Different date
    super2_res = Reservation(user_id=superadmin2.id, hall_id=hall.id, reservation_date=far_future_date)  # Different date
    db_session.add_all([user_res, super1_res, super2_res])
    await db_session.flush()

    response = await client.get("/reservations/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1  # Only user reservation
    assert len(data["items"]) == 1
    assert data["items"][0]["user_id"] == user.id

  async def test_superadmin_list_includes_all_reservations(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Superadmin list INCLUDES all reservations including superadmin ones"""
    mock_auth(superadmin_user)

    superadmin1 = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", role=UserRole.SUPERADMIN, is_active=True)
    superadmin2 = User(id=997, name="superadmin2", pw_hash="hash2", role=UserRole.SUPERADMIN, is_active=True)
    admin = User(id=998, name="admin", pw_hash="hash3", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash4", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([superadmin1, superadmin2, admin, user, hall])
    await db_session.flush()

    from datetime import timedelta
    res1 = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    res2 = Reservation(user_id=admin.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1))
    res3 = Reservation(user_id=superadmin2.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=2))
    db_session.add_all([res1, res2, res3])
    await db_session.flush()

    response = await client.get("/reservations/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3  # All reservations
    assert len(data["items"]) == 3


class TestRBACStatusTransitions:
  """RBAC tests for status transitions (cancel/finish)"""

  async def test_user_cannot_cancel_other_user_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User CANNOT cancel another user's reservation"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user1, user2, hall])
    await db_session.flush()

    reservation = Reservation(user_id=user2.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.RESERVATION_USER_CONFLICT

  async def test_user_cannot_finish_other_user_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """User CANNOT finish another user's reservation"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user1, user2, hall])
    await db_session.flush()

    reservation = Reservation(user_id=user2.id, hall_id=hall.id, reservation_date=today)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.RESERVATION_USER_CONFLICT

  async def test_admin_cannot_cancel_user_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Admin CANNOT cancel user's reservation (ownership rule)"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash2", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    reservation = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.RESERVATION_USER_CONFLICT

  async def test_admin_cannot_cancel_superadmin_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    superadmin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Admin CANNOT cancel superadmin's reservation - CRITICAL SECURITY RULE"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash2", role=UserRole.SUPERADMIN, is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, superadmin, hall])
    await db_session.flush()

    reservation = Reservation(user_id=superadmin.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.RESERVATION_USER_CONFLICT

  async def test_superadmin_cannot_cancel_user_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Superadmin CANNOT cancel user's reservation (ownership rule applies to all)"""
    mock_auth(superadmin_user)

    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", role=UserRole.SUPERADMIN, is_active=True)
    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash2", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([superadmin, user, hall])
    await db_session.flush()

    reservation = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 400
    assert response.json()["message"] == ErrorMessages.RESERVATION_USER_CONFLICT

  async def test_user_can_cancel_own_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User CAN cancel their own reservation"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 200

  async def test_admin_can_cancel_own_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Admin CAN cancel their own reservation"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, hall])
    await db_session.flush()

    reservation = Reservation(user_id=admin.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 200

  async def test_superadmin_can_cancel_own_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Superadmin CAN cancel their own reservation"""
    mock_auth(superadmin_user)

    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", role=UserRole.SUPERADMIN, is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([superadmin, hall])
    await db_session.flush()

    reservation = Reservation(user_id=superadmin.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 200
