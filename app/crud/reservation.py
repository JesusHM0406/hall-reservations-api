from datetime import date
import math

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reservation import Reservation, ReservationStatus
from app.utils.pagination_crud import PaginationCRUD

LIMIT_PER_PAGE = 10

async def crud_create_new_reservation(db: AsyncSession, user_id: int, hall_id: int, reservation_date: date):
  new_reservation = Reservation(user_id=user_id, hall_id=hall_id, reservation_date=reservation_date)
  db.add(new_reservation)
  return new_reservation

async def crud_get_reservation(db: AsyncSession, reservation_id: int):
  reservation = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
  return reservation.scalar_one_or_none()

async def crud_update_reservation_status(new_status: ReservationStatus, reservation: Reservation):
  reservation.status = new_status
  return reservation

async def crud_get_reservations(
  db: AsyncSession,
  page: int,
  filter_id: int | None = None,
  user_filter: bool = False,
  hall_filter: bool = False
) -> PaginationCRUD:
  stmt = select(Reservation).order_by(Reservation.id.desc())
  total_records_stmt = select(func.count()).select_from(Reservation)

  if filter_id:
    if user_filter:
      stmt = stmt.where(Reservation.user_id == filter_id)
      total_records_stmt = total_records_stmt.where(Reservation.user_id == filter_id)
    elif hall_filter:
      stmt = stmt.where(Reservation.hall_id == filter_id)
      total_records_stmt = total_records_stmt.where(Reservation.hall_id == filter_id)

  total_res = await db.execute(total_records_stmt)
  total_records = total_res.scalar() or 0

  pages = math.ceil(total_records / LIMIT_PER_PAGE) if total_records > 0 else 1

  current_page = max(1, min(page, pages))

  current_offset = (current_page - 1) * LIMIT_PER_PAGE

  stmt = stmt.limit(LIMIT_PER_PAGE).offset(current_offset)

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

  return PaginationCRUD(items=list(data), total=total_records, per_page=LIMIT_PER_PAGE, pages=pages, current_page=current_page)
