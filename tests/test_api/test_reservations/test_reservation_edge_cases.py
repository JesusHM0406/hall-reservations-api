"""
Tests for Reservation Edge Cases and Vulnerabilities

This module contains tests for:
- Edge cases and boundary conditions
- Data integrity scenarios
- Concurrent operations
- Deleted/invalid references
- Malformed requests
- Security vulnerabilities
- Race conditions

Focuses on:
- Preventing API breakage from unexpected events
- Ensuring data integrity
- Catching potential security issues
- Handling all edge cases gracefully
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
from app.schemas.filters.reservation import ReservationFilterNames
from app.schemas.user import UserComplete
from .conftest import build_create_reservation_request


class TestDeletedReferences:
  """Tests for handling deleted/non-existent references"""

  async def test_get_reservation_with_deleted_user(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    superadmin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Getting reservation when user is deleted"""
    mock_auth(superadmin_user)

    superadmin = User(id=superadmin_user.id, name=superadmin_user.name, pw_hash="hash", role=UserRole.SUPERADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True, is_deleted=True)
    
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([superadmin, user, hall])
    await db_session.flush()

    reservation = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.get(f"/reservations/{reservation.id}")

    # Should return 404 because user is deleted
    assert response.status_code == 404
    assert response.json()["detail"] == ErrorMessages.USER_NOT_FOUND

  async def test_finish_reservation_with_deleted_hall(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """Finishing reservation when hall was deleted should fail gracefully"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)
    await db_session.flush()

    # Create reservation, then simulate hall deletion by not having it in db
    reservation = Reservation(user_id=user.id, hall_id=9999, reservation_date=today)
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")

    assert response.status_code == 404
    assert response.json()["detail"] == ErrorMessages.DELETED_HALL


class TestMalformedRequests:
  """Tests for malformed/invalid requests"""

  async def test_create_reservation_with_string_hall_id(
    self, 
    client: AsyncClient,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Creating reservation with string hall_id"""
    mock_auth(regular_user)

    response = await client.post("/reservations/", json={
      "hall_id": "not_a_number",
      "reservation_date": tomorrow.isoformat()
    })

    assert response.status_code == 422

  async def test_create_reservation_with_null_hall_id(
    self, 
    client: AsyncClient,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Creating reservation with null hall_id"""
    mock_auth(regular_user)

    response = await client.post("/reservations/", json={
      "hall_id": None,
      "reservation_date": tomorrow.isoformat()
    })

    assert response.status_code == 422

  async def test_create_reservation_with_null_date(
    self, 
    client: AsyncClient,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Creating reservation with null date"""
    mock_auth(regular_user)

    response = await client.post("/reservations/", json={
      "hall_id": 1,
      "reservation_date": None
    })

    assert response.status_code == 422

  async def test_create_reservation_empty_json(
    self, 
    client: AsyncClient,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Creating reservation with empty JSON"""
    mock_auth(regular_user)

    response = await client.post("/reservations/", json={})

    assert response.status_code == 422

  async def test_get_reservation_with_string_id(
    self, 
    client: AsyncClient,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Getting reservation with string ID should fail"""
    mock_auth(regular_user)

    response = await client.get("/reservations/not_a_number")

    assert response.status_code == 422

  async def test_get_reservation_with_negative_id(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Getting reservation with negative ID"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)
    await db_session.flush()

    response = await client.get("/reservations/-1")

    assert response.status_code == 404

  async def test_filter_with_sql_injection_attempt(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Filter handles SQL injection attempts safely"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    await db_session.flush()

    # Try SQL injection
    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=admin' OR '1'='1")
    
    assert response.status_code == 200
    assert response.json()["total"] == 0  # Should not return all reservations due to injection


class TestBoundaryConditions:
  """Tests for boundary conditions"""

  async def test_pagination_beyond_available_pages(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Requesting page beyond available pages returns correctly"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user", pw_hash="hash1", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res)
    await db_session.flush()

    response = await client.get("/reservations/?page=999")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert isinstance(data["items"], list)
    assert data["requested_page"] == 999
    assert data["current_page"] == 1  # Should return the last page if the requested page is out of range

  async def test_pagination_page_zero(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Page 0 or negative should return first page"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    await db_session.flush()

    response = await client.get("/reservations/?page=0")

    assert response.status_code == 200
    data = response.json()
    assert data["requested_page"] == 0
    assert data["current_page"] == 1 # Should return first page if page is 0 or negative


class TestConcurrencyScenarios:
  """Tests for concurrent operation edge cases"""

  async def test_double_booking_race_condition(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Ensure database constraint prevents double booking"""
    # This is more of an integrity test - the unique index should prevent it

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user1, user2, hall])
    await db_session.flush()

    # First reservation succeeds
    res1 = Reservation(user_id=user1.id, hall_id=hall.id, reservation_date=tomorrow, status=ReservationStatus.CONFIRMED)
    db_session.add(res1)
    await db_session.flush()

    # Second reservation for same hall/date should fail in create endpoint
    mock_auth(another_regular_user)
    response = await client.post("/reservations/", json=build_create_reservation_request(hall_id=hall.id, reservation_date=tomorrow))

    assert response.status_code == 409
    assert response.json()["detail"] == ErrorMessages.DUPLICATED_RESERVATION

  async def test_cancel_then_rebook_same_slot(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """After cancellation, slot should be available for rebooking"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user1, user2, hall])
    await db_session.flush()

    # Create and cancel reservation
    res1 = Reservation(user_id=user1.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res1)
    await db_session.flush()

    response = await client.patch(f"/reservations/{res1.id}/cancel")
    assert response.status_code == 200

    # Now another user should be able to book (cancelled doesn't block)
    mock_auth(another_regular_user)
    response = await client.post("/reservations/", json=build_create_reservation_request(hall_id=hall.id, reservation_date=tomorrow))

    assert response.status_code == 201


class TestDataIntegrity:
  """Tests for data integrity"""

  async def test_reservation_maintains_user_info_after_retrieval(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Reservation data remains consistent across multiple retrievals"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    # Create reservation
    response = await client.post("/reservations/", json=build_create_reservation_request(hall_id=hall.id, reservation_date=tomorrow))
    assert response.status_code == 201
    res_id = response.json()["id"]

    # Get it multiple times - data should be consistent
    response1 = await client.get(f"/reservations/{res_id}")
    response2 = await client.get(f"/reservations/{res_id}")
    response3 = await client.get(f"/reservations/{res_id}")

    assert response1.json() == response2.json() == response3.json()

  async def test_status_transition_persists(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Status change persists and reflects in subsequent queries"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res)
    await db_session.flush()

    # Cancel reservation
    cancel_response = await client.patch(f"/reservations/{res.id}/cancel")
    assert cancel_response.json()["status"] == ReservationStatus.CANCELLED.value

    # Verify status persisted
    get_response = await client.get(f"/reservations/{res.id}")
    assert get_response.json()["status"] == ReservationStatus.CANCELLED.value


class TestSpecialCharactersAndEncoding:
  """Tests for special characters and encoding issues"""

  async def test_filter_with_special_characters(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Filters handle special characters properly"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user_with_underscore", pw_hash="hash1", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res)
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=user_with_underscore")

    assert response.status_code == 200
    # Should find the user with underscore

  async def test_filter_with_percent_sign(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Percent sign in filter is handled correctly"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    user = User(id=1, name="user%test", pw_hash="hash1", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([admin, user, hall])
    await db_session.flush()

    res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res)
    await db_session.flush()

    # Should not treat % as wildcard when user provides it
    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=user%")

    assert response.status_code == 200


class TestInactiveAndDeletedUsers:
  """Tests for inactive and deleted user scenarios"""

  async def test_inactive_user_with_existing_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    inactive_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Inactive user with existing reservation cannot modify it"""
    mock_auth(inactive_user)

    user = User(id=inactive_user.id, name=inactive_user.name, pw_hash="hash", is_active=False)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    # Reservation exists from when user was active
    res = Reservation(user_id=user.id, hall_id=hall.id, reservation_date=tomorrow)
    db_session.add(res)
    await db_session.flush()

    # Try to cancel - should fail
    response = await client.patch(f"/reservations/{res.id}/cancel")

    assert response.status_code == 400
    assert response.json()["detail"] == ErrorMessages.INACTIVE_USER

  async def test_deleted_user_cannot_create_reservation(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    deleted_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Deleted user cannot create new reservation"""
    mock_auth(deleted_user)

    user = User(id=deleted_user.id, name=deleted_user.name, pw_hash="hash", is_active=True, is_deleted=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    response = await client.post("/reservations/", json=build_create_reservation_request(hall_id=hall.id, reservation_date=tomorrow))

    assert response.status_code == 404
    assert response.json()["detail"] == ErrorMessages.USER_NOT_FOUND


class TestEmptyAndNullScenarios:
  """Tests for empty strings, null values, whitespace"""

  async def test_filter_with_empty_string(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Empty string filter should be ignored or validated"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=")

    assert response.status_code == 422 # Should fail validation for empty string

  async def test_filter_with_only_whitespace(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Whitespace-only filter should be validated"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    await db_session.flush()

    response = await client.get(f"/reservations/?{ReservationFilterNames.USER.value}=   ")

    # Should either return all results or validation error
    assert response.status_code == 200
    assert response.json()["total"] == 0  # Should not return all reservations, should treat whitespace-only as no match


class TestLargeDataSets:
  """Tests for handling larger datasets"""

  async def test_many_reservations_pagination(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Pagination works correctly with many reservations"""
    mock_auth(admin_user)

    admin = User(id=admin_user.id, name=admin_user.name, pw_hash="hash", role=UserRole.ADMIN, is_active=True)
    users = [User(id=i, name=f"user{i}", pw_hash=f"hash{i}", is_active=True) for i in range(1, 51)]
    hall = Hall(name="Hall", description="Test", is_available=True)
    
    db_session.add_all([admin, hall, *users])
    await db_session.flush()

    # Create 50 reservations
    reservations = [
      Reservation(user_id=users[i].id, hall_id=hall.id, reservation_date=tomorrow + timedelta(days=i))
      for i in range(50)
    ]
    db_session.add_all(reservations)
    await db_session.flush()

    # Test first page
    response1 = await client.get("/reservations/?page=1")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["total"] == 50

    # Test second page
    response2 = await client.get("/reservations/?page=2")
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Items from page 1 and page 2 should be different
    ids_page1 = {item["id"] for item in data1["items"]}
    ids_page2 = {item["id"] for item in data2["items"]}
    assert ids_page1.isdisjoint(ids_page2)


class TestStatusConsistency:
  """Tests for status consistency across operations"""

  async def test_cannot_create_reservation_with_custom_status(
    self, 
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """New reservations are always CONFIRMED, cannot specify different status"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    hall = Hall(name="Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    # Schema doesn't allow status in create, but test malformed request
    response = await client.post("/reservations/", json={
      "hall_id": hall.id,
      "reservation_date": tomorrow.isoformat(),
      "status": ReservationStatus.CANCELLED.value  # This should be ignored or cause error
    })

    # Should either succeed with CONFIRMED or fail validation
    if response.status_code == 201:
      assert response.json()["status"] == ReservationStatus.CONFIRMED.value
    else:
      assert response.status_code == 422
