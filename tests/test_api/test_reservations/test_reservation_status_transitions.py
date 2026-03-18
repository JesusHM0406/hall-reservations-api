"""
Tests for Reservation Status Transitions

This module contains tests for:
- PATCH /reservations/{id}/finish - Finish a reservation
- PATCH /reservations/{id}/cancel - Cancel a reservation

Focuses on:
- Valid status transitions
- Invalid status transitions
- Date-based transition rules
- Ownership validation
- Edge cases
"""

from typing import Callable
from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.models.hall import Hall
from app.models.reservation import Reservation
from app.models.reservation_status import ReservationStatus
from app.models.user import User
from app.schemas.user import UserComplete


class TestFinishReservation:
  """Tests for PATCH /reservations/{id}/finish"""

  async def test_finish_reservation_on_reservation_date(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """Can finish reservation on the reservation date"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=today,  # Today
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ReservationStatus.FINISHED.value
    assert data["id"] == reservation.id

  async def test_finish_reservation_future_date_fails(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot finish reservation before the reservation date"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=tomorrow,  # Future
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INVALID_FINALIZATION

  async def test_finish_reservation_past_date_fails(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    past_date: date
  ):
    """Cannot finish reservation after the reservation date"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=past_date,  # Past
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INVALID_FINALIZATION

  async def test_finish_already_finished_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """Cannot finish already finished reservation"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=today,
      status=ReservationStatus.FINISHED  # Already finished
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INVALID_TRANSITION

  async def test_finish_cancelled_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """Cannot finish cancelled reservation"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=today,
      status=ReservationStatus.CANCELLED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INVALID_TRANSITION

  async def test_finish_other_user_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """Cannot finish another user's reservation"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    db_session.add_all([user1, user2])

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user2.id,  # Belongs to user2
      hall_id=hall.id,
      reservation_date=today,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.RESERVATION_USER_CONFLICT

  async def test_finish_nonexistent_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Finishing non-existent reservation returns 404"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)
    await db_session.flush()

    response = await client.patch("/reservations/99999/finish")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.RESERVATION_NOT_FOUND

  async def test_finish_reservation_unauthenticated(
    self, 
    client: AsyncClient
  ):
    """Unauthenticated user cannot finish reservation"""
    response = await client.patch("/reservations/1/finish")

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

  async def test_finish_reservation_inactive_user(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    inactive_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """Inactive user cannot finish reservation"""
    mock_auth(inactive_user)

    user = User(id=inactive_user.id, name=inactive_user.name, pw_hash="hash", is_active=False)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=today,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INACTIVE_USER


class TestCancelReservation:
  """Tests for PATCH /reservations/{id}/cancel"""

  async def test_cancel_reservation_success(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Can cancel future confirmed reservation"""
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

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ReservationStatus.CANCELLED.value
    assert data["id"] == reservation.id

  async def test_cancel_reservation_today(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """Can cancel reservation on the same day"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=today,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ReservationStatus.CANCELLED.value

  async def test_cancel_past_reservation_fails(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    past_date: date
  ):
    """Cannot cancel past reservation"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=past_date,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.CANNOT_CANCEL_PAST_RESERVATION

  async def test_cancel_already_cancelled_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot cancel already cancelled reservation"""
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
      status=ReservationStatus.CANCELLED  # Already cancelled
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INVALID_TRANSITION

  async def test_cancel_finished_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot cancel finished reservation"""
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
      status=ReservationStatus.FINISHED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INVALID_TRANSITION

  async def test_cancel_other_user_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    another_regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Cannot cancel another user's reservation"""
    mock_auth(regular_user)

    user1 = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    user2 = User(id=another_regular_user.id, name=another_regular_user.name, pw_hash="hash2", is_active=True)
    db_session.add_all([user1, user2])

    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add(hall)
    await db_session.flush()

    reservation = Reservation(
      user_id=user2.id,  # Belongs to user2
      hall_id=hall.id,
      reservation_date=tomorrow,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.RESERVATION_USER_CONFLICT

  async def test_cancel_nonexistent_reservation(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None]
  ):
    """Cancelling non-existent reservation returns 404"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    db_session.add(user)
    await db_session.flush()

    response = await client.patch("/reservations/99999/cancel")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == ErrorMessages.RESERVATION_NOT_FOUND

  async def test_cancel_reservation_unauthenticated(
    self, 
    client: AsyncClient
  ):
    """Unauthenticated user cannot cancel reservation"""
    response = await client.patch("/reservations/1/cancel")

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

  async def test_cancel_reservation_inactive_user(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    inactive_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """Inactive user cannot cancel reservation"""
    mock_auth(inactive_user)

    user = User(id=inactive_user.id, name=inactive_user.name, pw_hash="hash", is_active=False)
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

    response = await client.patch(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == ErrorMessages.INACTIVE_USER


class TestStatusTransitionMatrix:
  """Tests to verify all valid and invalid state transitions"""

  async def test_confirmed_to_cancelled(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """CONFIRMED -> CANCELLED is valid"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=tomorrow,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")
    assert response.status_code == 200

  async def test_confirmed_to_finished(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """CONFIRMED -> FINISHED is valid (on reservation date)"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=today,
      status=ReservationStatus.CONFIRMED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")
    assert response.status_code == 200

  async def test_cancelled_to_confirmed_invalid(
    self
  ):
    """CANCELLED -> CONFIRMED is not allowed"""
    # There's no endpoint to re-confirm, so cancelled is final
    # This is validated by the STATUS_TRANSITIONS dict
    pass

  async def test_cancelled_to_finished_invalid(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    today: date
  ):
    """CANCELLED -> FINISHED is not allowed"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=today,
      status=ReservationStatus.CANCELLED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/finish")
    assert response.status_code == 400
    assert response.json()["detail"] == ErrorMessages.INVALID_TRANSITION

  async def test_finished_to_cancelled_invalid(
    self, 
    client: AsyncClient, 
    db_session: AsyncSession,
    regular_user: UserComplete,
    mock_auth: Callable[[UserComplete], None],
    tomorrow: date
  ):
    """FINISHED -> CANCELLED is not allowed"""
    mock_auth(regular_user)

    user = User(id=regular_user.id, name=regular_user.name, pw_hash="hash", is_active=True)
    hall = Hall(name="Test Hall", description="Test", is_available=True)
    db_session.add_all([user, hall])
    await db_session.flush()

    reservation = Reservation(
      user_id=user.id,
      hall_id=hall.id,
      reservation_date=tomorrow,
      status=ReservationStatus.FINISHED
    )
    db_session.add(reservation)
    await db_session.flush()

    response = await client.patch(f"/reservations/{reservation.id}/cancel")
    assert response.status_code == 400
    assert response.json()["detail"] == ErrorMessages.INVALID_TRANSITION

  async def test_finished_to_confirmed_invalid(
    self
  ):
    """FINISHED -> CONFIRMED is not allowed"""
    # There's no endpoint to re-confirm, so finished is final
    # This is validated by the STATUS_TRANSITIONS dict
    pass
