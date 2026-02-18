from datetime import date

from app.models.reservation_status import ReservationStatus
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.hall import crud_get_hall_by_id
from app.crud.reservation import (
  crud_create_new_reservation,
  crud_get_reservation,
  crud_get_reservations,
  crud_update_reservation_status,
)
from app.crud.user import crud_get_user_by_id
from app.exceptions.exceptions import BusinessLogicError, ConflictError, NotFoundError
from app.schemas.reservation import ReservationRead
from app.utils.filters_metadata import ReservationFilterNames
from app.utils.pagination import Pagination, get_pagination


async def service_create_new_reservation(
  db: AsyncSession,
  user_id: int,
  hall_id: int,
  reservation_date: date
) -> ReservationRead:
  today = date.today()
  if reservation_date < today or reservation_date == today:
    raise BusinessLogicError("The date is invalid; it must be at least one day after the current date.")

  user = await crud_get_user_by_id(db=db, id=user_id)
  if not user:
    raise NotFoundError("The user doesn't exist.")
  if not user.is_active:
    raise BusinessLogicError("The user is inactive.")

  hall = await crud_get_hall_by_id(db=db, id=hall_id)
  if not hall:
    raise NotFoundError("The hall doesn't exist.")
  if not hall.is_available:
    raise BusinessLogicError("The hall isn't available in this moment.")

  try:
    reservation = await crud_create_new_reservation(
      db,
      user_id,
      hall_id,
      reservation_date
    )
    await db.flush()

    return ReservationRead(
      id=reservation.id,
      user_id=user_id,
      user_name=user.name,
      hall_id=hall_id,
      hall_name=hall.name,
      status=reservation.status,
      reservation_date=reservation.reservation_date
    )
  except IntegrityError:
    raise ConflictError("There's already an active reservation in that date.")

async def service_get_reservation(
  db: AsyncSession,
  id: int
) -> ReservationRead:
  reservation = await crud_get_reservation(db, id)

  if not reservation:
    raise NotFoundError("Reservation not found.")

  return ReservationRead(
    id=reservation.id,
    user_id=reservation.user_id,
    user_name=reservation.user.name,
    hall_id=reservation.hall_id,
    hall_name=reservation.hall.name,
    status=reservation.status,
    reservation_date=reservation.reservation_date
  )

async def service_update_reservation_status(
  db: AsyncSession,
  reservation_id: int,
  new_status: str,
  user_id: int
)-> ReservationRead:
  transitions_map = {
    ReservationStatus.CANCELLED.value: {
      "has_transitions": False
    },
    ReservationStatus.CONFIRMED.value: {
      "has_transitions": True,
      "transitions": [
        ReservationStatus.CANCELLED.value,
        ReservationStatus.FINISHED.value,
        ReservationStatus.EXPIRED.value
      ]
    },
    ReservationStatus.EXPIRED.value: {
      "has_transitions": False
    },
    ReservationStatus.FINISHED.value: {
      "has_transitions": False
    }
  }

  user = await crud_get_user_by_id(db=db, id=user_id)

  if not user:
    raise NotFoundError("User not found.")

  reservation = await crud_get_reservation(db, reservation_id)

  if not reservation:
    raise NotFoundError("Reservation not found.")

  hall = await crud_get_hall_by_id(db=db, id=reservation.hall_id)

  if not hall:
    raise NotFoundError("It appears the hall was deleted.")

  if reservation.user_id != user.id:
    raise BusinessLogicError("The reservation is not from this user.")

  if not transitions_map[reservation.status.value]["has_transitions"]:
    raise BusinessLogicError("You cannot change the status of this reservation; it has already been cancelled, finished, or expired.")

  if new_status not in [
    ReservationStatus.CANCELLED.value,
    ReservationStatus.CONFIRMED.value,
    ReservationStatus.EXPIRED.value,
    ReservationStatus.FINISHED.value
  ]:
    raise BusinessLogicError("Invalid status.")

  if new_status not in transitions_map[reservation.status.value]["transitions"]:
    raise BusinessLogicError(f"The status cannot be set as {new_status} because the reservation has a {reservation.status.value} status.")

  if (new_status == ReservationStatus.FINISHED.value and
    date.today() != reservation.reservation_date):
    raise BusinessLogicError("The reservation cannot be finalized because today is not the reservation date.")

  status_enum = ReservationStatus(new_status)

  updated_reservation = await crud_update_reservation_status(
    status_enum,
    reservation
  )

  return ReservationRead(
    id=reservation.id,
    user_id=user.id,
    user_name=user.name,
    hall_id=hall.id,
    hall_name=hall.name,
    status=updated_reservation.status,
    reservation_date=reservation.reservation_date
  )

async def service_get_all_reservations(
  db: AsyncSession,
  page: int,
  filters: dict
) -> Pagination:

  result = await crud_get_reservations(
    db,
    page,
    {
      ReservationFilterNames.USER.value: filters.get("user_id"),
      ReservationFilterNames.HALL.value: filters.get("hall_id")
    }
  )

  pagination = get_pagination(result, page)

  return pagination
