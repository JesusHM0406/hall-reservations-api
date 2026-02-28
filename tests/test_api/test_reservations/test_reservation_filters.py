"""
Tests for Reservation Filtering

This module contains tests for:
- Filter by user name
- Filter by hall name
- Filter by status
- Combined filters
- Filter validation
- Pagination with filters

Focuses on:
- Filter functionality
- Case-insensitive filtering
- Partial matching
- RBAC enforcement with filters
- Empty results
- Filter validation
"""

from typing import Callable
from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hall import Hall
from app.models.reservation import Reservation
from app.models.reservation_status import ReservationStatus
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.filters.reservation import ReservationFilterNames
from app.schemas.user import UserComplete


class TestFilterByUserName:
  """Tests for filtering by user name"""

  async def test_filter_by_user_name_exact_match(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter by exact user name"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user1 = User(id=1, name="alice", pw_hash="hash1", is_active=True)
    user2 = User(id=2, name="bob", pw_hash="hash2", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user1, user2, hall])
    await db_session.flush()

    res1 = Reservation(user_id=user1.id, hall_id=hall.id, reservation_date=tomorrow)
    res2 = Reservation(user_id=user2.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1))
    db_session.add_all([res1, res2])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=alice")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["user_name"] == "alice"

  async def test_filter_by_user_name_partial_match(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter supports partial matching (ILIKE)"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user1 = User(id=1, name="john_doe", pw_hash="hash1", is_active=True)
    user2 = User(id=2, name="john_smith", pw_hash="hash2", is_active=True)
    user3 = User(id=3, name="alice", pw_hash="hash3", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user1, user2, user3, hall])
    await db_session.flush()

    res1 = Reservation(user_id=user1.id, hall_id=hall.id, reservation_date=tomorrow)
    res2 = Reservation(user_id=user2.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1))
    res3 = Reservation(user_id=user3.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=2))
    db_session.add_all([res1, res2, res3])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=john")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all("john" in item["user_name"].lower() for item in data["items"])

  async def test_filter_by_user_name_case_insensitive(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter is case insensitive"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="Alice", pw_hash="hash1", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res)
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=alice")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1

  async def test_filter_by_user_name_no_results(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter returns empty when no matches"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="alice", pw_hash="hash1", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res)
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=nonexistent")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0

  async def test_filter_by_user_name_too_short(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """User name filter must be at least 3 characters"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=ab")

    assert response.status_code == 422

  async def test_filter_by_user_name_with_rbac(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date,
    future_date: date
  ):
    """Filter respects RBAC - admin cannot see superadmin reservations"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="alice_user", pw_hash="hash1", is_active=True)
    superadmin = User(id=999, name="alice_super", pw_hash="hash2", role=UserRole.SUPERADMIN, is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, superadmin, hall])
    await db_session.flush()

    user_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    super_res = Reservation(user_id=superadmin.id, hall_id=hall.id, reservation_date=future_date)  # Different date
    db_session.add_all([user_res, super_res])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=alice")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1  # Only user reservation, not superadmin
    assert data["items"][0]["user_name"] == "alice_user"


class TestFilterByHallName:
  """Tests for filtering by hall name"""

  async def test_filter_by_hall_name_exact_match(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter by exact hall name"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True)
    
    hall1 = Hall(name="Main Hall", description="Test", is_available=True)
    hall2 = Hall(name="Conference Room", description="Test", is_available=True)
    db_session.add_all([admin, user, hall1, hall2])
    await db_session.flush()

    res1 = Reservation(user_id=user.id, hall_id=hall1.id, reservation_date=tomorrow)
    res2 = Reservation(user_id=user.id, hall_id=hall2.id, reservation_date=tomorrow + timedelta(days=1))
    db_session.add_all([res1, res2])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.HALL.value}=Main Hall")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["hall_name"] == "Main Hall"

  async def test_filter_by_hall_name_partial_match(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter supports partial matching"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True)
    
    hall1 = Hall(name="Conference Room A", description="Test", is_available=True)
    hall2 = Hall(name="Conference Room B", description="Test", is_available=True)
    hall3 = Hall(name="Main Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall1, hall2, hall3])
    await db_session.flush()

    res1 = Reservation(user_id=user.id, hall_id=hall1.id, reservation_date=tomorrow)
    res2 = Reservation(user_id=user.id, hall_id=hall2.id, reservation_date=tomorrow)
    res3 = Reservation(user_id=user.id, hall_id=hall3.id, reservation_date=tomorrow)
    db_session.add_all([res1, res2, res3])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.HALL.value}=Conference")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all("Conference" in item["hall_name"] for item in data["items"])

  async def test_filter_by_hall_name_case_insensitive(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter is case insensitive"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True)
    
    hall = Hall(name="Main Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res)
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.HALL.value}=main hall")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1

  async def test_filter_by_hall_name_too_short(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Hall name filter must be at least 3 characters"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.HALL.value}=ab")

    assert response.status_code == 422


class TestFilterByStatus:
  """Tests for filtering by reservation status"""

  async def test_filter_by_confirmed_status(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter by confirmed status"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    confirmed_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow, status=ReservationStatus.CONFIRMED)
    cancelled_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1), status=ReservationStatus.CANCELLED)
    finished_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=2), status=ReservationStatus.FINISHED)
    db_session.add_all([confirmed_res, cancelled_res, finished_res])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.STATUS.value}={ReservationStatus.CONFIRMED.value}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == ReservationStatus.CONFIRMED.value

  async def test_filter_by_cancelled_status(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter by cancelled status"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    confirmed_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow, status=ReservationStatus.CONFIRMED)
    cancelled_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1), status=ReservationStatus.CANCELLED)
    db_session.add_all([confirmed_res, cancelled_res])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.STATUS.value}={ReservationStatus.CANCELLED.value}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == ReservationStatus.CANCELLED.value

  async def test_filter_by_finished_status(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter by finished status"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    confirmed_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow, status=ReservationStatus.CONFIRMED)
    finished_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1), status=ReservationStatus.FINISHED)
    db_session.add_all([confirmed_res, finished_res])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.STATUS.value}={ReservationStatus.FINISHED.value}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == ReservationStatus.FINISHED.value

  async def test_filter_by_invalid_status(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Invalid status returns validation error"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.STATUS.value}=invalid_status")

    assert response.status_code == 422


class TestCombinedFilters:
  """Tests for using multiple filters together"""

  async def test_filter_by_user_and_hall(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter by both user name and hall name"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user1 = User(id=1, name="alice", pw_hash="hash1", is_active=True)
    user2 = User(id=2, name="bob", pw_hash="hash2", is_active=True)
    
    hall1 = Hall(name="Main Hall", description="Test", is_available=True)
    hall2 = Hall(name="Conference Room", description="Test", is_available=True)
    db_session.add_all([admin, user1, user2, hall1, hall2])
    await db_session.flush()

    res1 = Reservation(user_id=user1.id, hall_id=hall1.id, reservation_date=tomorrow)
    res2 = Reservation(user_id=user1.id, hall_id=hall2.id, reservation_date=tomorrow + timedelta(days=1))
    res3 = Reservation(user_id=user2.id, hall_id=hall1.id, reservation_date=tomorrow + timedelta(days=2))
    db_session.add_all([res1, res2, res3])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=alice&{ReservationFilterNames.HALL.value}=Main")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["user_name"] == "alice"
    assert data["items"][0]["hall_name"] == "Main Hall"

  async def test_filter_by_user_and_status(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter by user name and status"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="alice", pw_hash="hash1", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    confirmed_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow, status=ReservationStatus.CONFIRMED)
    cancelled_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1), status=ReservationStatus.CANCELLED)
    db_session.add_all([confirmed_res, cancelled_res])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=alice&{ReservationFilterNames.STATUS.value}={ReservationStatus.CONFIRMED.value}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == ReservationStatus.CONFIRMED.value

  async def test_filter_by_hall_and_status(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter by hall name and status"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True)
    
    hall = Hall(name="Main Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    confirmed_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow, status=ReservationStatus.CONFIRMED)
    cancelled_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1), status=ReservationStatus.CANCELLED)
    db_session.add_all([confirmed_res, cancelled_res])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.HALL.value}=Main&{ReservationFilterNames.STATUS.value}={ReservationStatus.CANCELLED.value}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == ReservationStatus.CANCELLED.value

  async def test_filter_by_all_three(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filter by user name, hall name, and status"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user1 = User(id=1, name="alice", pw_hash="hash1", is_active=True)
    user2 = User(id=2, name="bob", pw_hash="hash2", is_active=True)
    
    hall1 = Hall(name="Main Hall", description="Test", is_available=True)
    hall2 = Hall(name="Conference Room", description="Test", is_available=True)
    db_session.add_all([admin, user1, user2, hall1, hall2])
    await db_session.flush()

    target_res = Reservation(user_id=user1.id, hall_id=hall1.id, reservation_date=tomorrow, status=ReservationStatus.CONFIRMED)
    other_res1 = Reservation(user_id=user1.id, hall_id=hall1.id, reservation_date=tomorrow + timedelta(days=1), status=ReservationStatus.CANCELLED)
    other_res2 = Reservation(user_id=user1.id, hall_id=hall2.id, reservation_date=tomorrow + timedelta(days=2), status=ReservationStatus.CONFIRMED)
    other_res3 = Reservation(user_id=user2.id, hall_id=hall1.id, reservation_date=tomorrow + timedelta(days=3), status=ReservationStatus.CONFIRMED)
    db_session.add_all([target_res, other_res1, other_res2, other_res3])
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=alice&{ReservationFilterNames.HALL.value}=Main&{ReservationFilterNames.STATUS.value}={ReservationStatus.CONFIRMED.value}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["user_name"] == "alice"
    assert data["items"][0]["hall_name"] == "Main Hall"
    assert data["items"][0]["status"] == ReservationStatus.CONFIRMED.value


class TestFilterOnMeEndpoint:
  """Tests for filters on /reservations/me endpoint"""

  async def test_me_endpoint_filter_by_hall(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User can filter their own reservations by hall"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    
    hall1 = Hall(name="Main Hall", description="Test", is_available=True)
    hall2 = Hall(name="Conference Room", description="Test", is_available=True)
    db_session.add_all([user, hall1, hall2])
    await db_session.flush()

    res1 = Reservation(user_id=user.id, hall_id=hall1.id, reservation_date=tomorrow)
    res2 = Reservation(user_id=user.id, hall_id=hall2.id, reservation_date=tomorrow + timedelta(days=1))
    db_session.add_all([res1, res2])
    await db_session.flush()

    response = await client.get(f"/reservations/me?{ReservationFilterNames.HALL.value}=Main")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["hall_name"] == "Main Hall"

  async def test_me_endpoint_filter_by_status(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User can filter their own reservations by status"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    confirmed_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow, status=ReservationStatus.CONFIRMED)
    cancelled_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1), status=ReservationStatus.CANCELLED)
    db_session.add_all([confirmed_res, cancelled_res])
    await db_session.flush()

    response = await client.get(f"/reservations/me?{ReservationFilterNames.STATUS.value}={ReservationStatus.CONFIRMED.value}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == ReservationStatus.CONFIRMED.value

  async def test_me_endpoint_user_name_filter_overridden(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """User name filter is overridden by authenticated user on /me endpoint"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    other_user = User(id=999, name="other_user", pw_hash="hash2", is_active=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user, other_user, hall])
    await db_session.flush()

    my_res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    other_res = Reservation(user_id=other_user.id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=1))
    db_session.add_all([my_res, other_res])
    await db_session.flush()

    # Try to filter by other user's name - should be ignored
    response = await client.get(f"/reservations/me?{ReservationFilterNames.USER.value}=other_user")

    assert response.status_code == 200
    data = response.json()
    # Should only see own reservation
    assert data["total"] == 1
    assert data["items"][0]["user_name"] == regular_user.name
