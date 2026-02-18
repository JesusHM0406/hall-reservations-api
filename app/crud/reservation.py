import math
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.models.hall import Hall
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User
from app.utils.filters_metadata import ReservationFilterNames
from app.utils.pagination_crud import PaginationCRUD


async def crud_create_new_reservation(db: AsyncSession, user_id: int, hall_id: int, reservation_date: date):
  new_reservation = Reservation(user_id=user_id, hall_id=hall_id, reservation_date=reservation_date)
  db.add(new_reservation)
  return new_reservation

async def crud_get_reservation(db: AsyncSession, reservation_id: int):
  stmt = (
    select(Reservation)
    .options(
      joinedload(Reservation.user).load_only(User.name),
      joinedload(Reservation.hall).load_only(Hall.name)
    )
    .where(Reservation.id == reservation_id)
  )

  reservation = await db.execute(stmt)
  return reservation.scalar_one_or_none()

async def crud_update_reservation_status(new_status: ReservationStatus, reservation: Reservation):
  reservation.status = new_status
  return reservation

async def crud_get_reservations(
  db: AsyncSession,
  page: int,
  filters: dict
) -> PaginationCRUD:
  stmt = select(Reservation).order_by(Reservation.id.desc())
  total_records_stmt = select(func.count()).select_from(Reservation)

  user_id = filters.get(ReservationFilterNames.USER.value)
  hall_id = filters.get(ReservationFilterNames.HALL.value)

  if user_id is not None:
    stmt = stmt.where(Reservation.user_id == user_id)
    total_records_stmt = total_records_stmt.where(Reservation.user_id == user_id)
  elif hall_id is not None:
    stmt = stmt.where(Reservation.hall_id == hall_id)
    total_records_stmt = total_records_stmt.where(Reservation.hall_id == hall_id)

  total_res = await db.execute(total_records_stmt)
  total_records = total_res.scalar() or 0

  pages = math.ceil(total_records / settings.PAGINATION_LIMIT_PER_PAGE) if total_records > 0 else 1

  current_page = max(1, min(page, pages))

  current_offset = (current_page - 1) * settings.PAGINATION_LIMIT_PER_PAGE

  stmt = stmt.limit(settings.PAGINATION_LIMIT_PER_PAGE).offset(current_offset)

  result = await db.execute(stmt)
  result_items = result.scalars().all()
  data = [
    {
      "id": item.id,
      "user_id": item.user_id,
      "hall_id": item.hall_id,
      "status": item.status.value if hasattr(item.status, 'value') else item.status,
      "reservation_date": item.reservation_date
    }
    for item in result_items
  ]

  return PaginationCRUD(items=list(data), total=total_records, per_page=settings.PAGINATION_LIMIT_PER_PAGE, pages=pages, current_page=current_page)
