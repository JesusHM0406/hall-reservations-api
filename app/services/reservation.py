from datetime import date, datetime, timezone

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

STATUS_TRANSITIONS: dict[ReservationStatus, list[ReservationStatus]] = {
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
  # Validate date (redundant with schema validation but provides defense in depth)
  today = datetime.now(timezone.utc).date()
  if reservation_date <= today:
    raise BusinessLogicError(ErrorMessages.INVALID_DATE)

  # Validate user exists and is active
  user = await crud_get_user_by_id(db=db, id=user_id)
  if not user or user.is_deleted:
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)
  if not user.is_active:
    raise BusinessLogicError(ErrorMessages.INACTIVE_USER)

  # Validate hall exists and is available
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

  # Get the reservation owner's role to enforce permission boundaries
  reservation_owner = await crud_get_user_by_id(db=db, id=reservation.user_id)
  
  if not reservation_owner or reservation_owner.is_deleted:
    raise NotFoundError(ErrorMessages.USER_NOT_FOUND)

  # Permission checks:
  # 1. Users can only see their own reservations
  # 2. Admins can see user and admin reservations, but NOT superadmin reservations
  # 3. Superadmins can see all reservations
  is_own_reservation = reservation.user_id == user.id
  is_superadmin = user.role == UserRole.SUPERADMIN
  is_admin = user.role == UserRole.ADMIN
  reservation_owner_is_superadmin = reservation_owner.role == UserRole.SUPERADMIN

  if not is_own_reservation:
    if not is_admin and not is_superadmin:
      # Regular users can't see others' reservations
      raise BusinessLogicError(ErrorMessages.RESERVATION_FROM_OTHER_USER)
    
    if is_admin and reservation_owner_is_superadmin:
      # Admins can't see superadmin reservations
      raise NotFoundError(ErrorMessages.RESERVATION_NOT_FOUND)

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
  
  if not user.is_active:
    raise BusinessLogicError(ErrorMessages.INACTIVE_USER)

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

  # Validate date-specific transitions
  today = datetime.now(timezone.utc).date()
  
  if new_status == ReservationStatus.FINISHED:
    # Can only finish on the reservation date
    if today != reservation.reservation_date:
      raise BusinessLogicError(ErrorMessages.INVALID_FINALIZATION)
  
  if new_status == ReservationStatus.CANCELLED:
    # Cannot cancel reservations in the past (but can cancel today's reservation)
    if reservation.reservation_date < today:
      raise BusinessLogicError(ErrorMessages.CANNOT_CANCEL_PAST_RESERVATION)

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
  filters: ReservationFilters,
  requesting_user: UserComplete
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
    filters=filters,
    requesting_user_role=requesting_user.role
  )

  pagination = get_pagination(pagination=result, page=page, available_filters=reservation_availables_filters)

  return pagination
