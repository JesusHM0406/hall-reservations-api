from datetime import date

from app.core.messages import ErrorMessages
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
from app.models.user_role import UserRole
from app.schemas.filters.reservation import ReservationFilters, ReservationFilterLabels, ReservationFilterNames
from app.schemas.reservation import ReservationRead
from app.schemas.user import UserComplete
from app.utils.pagination import Pagination, get_pagination
from app.utils.pagination_filters import FilterFactory

STATUS_TRANSITIONS = {
    ReservationStatus.CONFIRMED: [ReservationStatus.CANCELLED, ReservationStatus.FINISHED],
    ReservationStatus.CANCELLED: [],
    ReservationStatus.FINISHED: []
}

async def service_create_new_reservation(
  *,
  db: AsyncSession,
  user_id: int,
  hall_id: int,
  reservation_date: date
) -> ReservationRead:
  today = date.today()
  if reservation_date < today or reservation_date == today:
    raise BusinessLogicError(ErrorMessages.INVALID_DATE)

  user = await crud_get_user_by_id(db=db, id=user_id)
  if not user or user.is_deleted:
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)
  if not user.is_active:
    raise BusinessLogicError(ErrorMessages.INACTIVE_USER)

  hall = await crud_get_hall_by_id(db=db, id=hall_id)
  if not hall:
    raise NotFoundError(ErrorMessages.HALL_NOT_FOUND)
  if not hall.is_available:
    raise BusinessLogicError(ErrorMessages.UNAVAILABLE_HALL)

  try:
    reservation = await crud_create_new_reservation(
      db=db,
      user_id=user_id,
      hall_id=hall_id,
      reservation_date=reservation_date
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
    raise ConflictError(ErrorMessages.DUPLICATED_RESERVATION)

async def service_get_reservation(
  *,
  db: AsyncSession,
  id: int,
  user: UserComplete
) -> ReservationRead:
  reservation = await crud_get_reservation(db=db, reservation_id=id)

  if not reservation:
    raise NotFoundError(ErrorMessages.RESERVATION_NOT_FOUND)

  if user.role != UserRole.ADMIN and reservation.user_id != user.id:
    raise BusinessLogicError(ErrorMessages.RESERVATION_FROM_OTHER_USER)

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
  *,
  db: AsyncSession,
  reservation_id: int,
  new_status: ReservationStatus,
  user_id: int
)-> ReservationRead:
  user = await crud_get_user_by_id(db=db, id=user_id)

  if not user or user.is_deleted:
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)

  reservation = await crud_get_reservation(db=db, reservation_id=reservation_id)

  if not reservation:
    raise NotFoundError(ErrorMessages.RESERVATION_NOT_FOUND)

  hall = await crud_get_hall_by_id(db=db, id=reservation.hall_id)

  if not hall:
    raise NotFoundError(ErrorMessages.DELETED_HALL)

  if reservation.user_id != user.id:
    raise BusinessLogicError(ErrorMessages.RESERVATION_USER_CONFLICT)

  if new_status not in STATUS_TRANSITIONS.get(reservation.status, []):
    raise BusinessLogicError(ErrorMessages.INVALID_TRANSITION)

  if (new_status == ReservationStatus.FINISHED and
    date.today() != reservation.reservation_date):
      raise BusinessLogicError(ErrorMessages.INVALID_FINALIZATION)

  updated_reservation = await crud_update_reservation_status(
    new_status=new_status,
    reservation=reservation
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
  *,
  db: AsyncSession,
  page: int,
  filters: ReservationFilters
) -> Pagination:
  reservation_status_filter_dict: dict[str, str] = {}

  for status in ReservationStatus:
    reservation_status_filter_dict[status.value] = status.value.capitalize()

  reservation_availables_filters = [
    FilterFactory.text(
      name=ReservationFilterNames.USER.value,
      label=ReservationFilterLabels.USER.value
    ),
    FilterFactory.text(
      name=ReservationFilterNames.HALL.value,
      label=ReservationFilterLabels.HALL.value
    ),
    FilterFactory.select(
      name=ReservationFilterNames.STATUS.value,
      label=ReservationFilterLabels.STATUS.value,
      options=reservation_status_filter_dict,
      current=filters.status
    )
  ]

  result = await crud_get_reservations(
    db=db,
    page=page,
    filters=filters
  )

  pagination = get_pagination(pagination=result, page=page, available_filters=reservation_availables_filters)

  return pagination
