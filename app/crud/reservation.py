from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload

from app.core.config import settings
from app.models.hall import Hall
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User
from app.schemas.filters.reservation import ReservationFilters
from app.schemas.reservation import ReservationRead
from app.utils.pagination import get_pagination_computed_fields
from app.utils.pagination_crud import PaginationCRUD


async def crud_create_new_reservation(
  *,
  db: AsyncSession,
  user_id: int,
  hall_id: int,
  reservation_date: date
):
  new_reservation = Reservation(
    user_id=user_id,
    hall_id=hall_id,
    reservation_date=reservation_date
  )
  db.add(new_reservation)
  return new_reservation

async def crud_get_reservation(*, db: AsyncSession, reservation_id: int):
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

async def crud_update_reservation_status(
  *,
  new_status: ReservationStatus,
  reservation: Reservation
):
  reservation.status = new_status
  return reservation

async def crud_get_reservations(
  *,
  db: AsyncSession,
  page: int,
  filters: ReservationFilters
) -> PaginationCRUD:
  stmt = select(Reservation).order_by(Reservation.id.desc())
  total_records_stmt = select(func.count()).select_from(Reservation)

  if filters.user_name:
    stmt = stmt.join(Reservation.user).where(User.name.ilike(f"%{filters.user_name}%"))
    total_records_stmt = total_records_stmt.join(Reservation.user).where(User.name.ilike(f"%{filters.user_name}%"))
    stmt = stmt.options(contains_eager(Reservation.user).load_only(User.name))
  else:
    stmt = stmt.options(joinedload(Reservation.user).load_only(User.name))

  if filters.hall_name:
    stmt = stmt.join(Reservation.hall).where(Hall.name.ilike(f"%{filters.hall_name}%"))
    total_records_stmt = total_records_stmt.join(Reservation.hall).where(Hall.name.ilike(f"%{filters.hall_name}%"))
    stmt = stmt.options(contains_eager(Reservation.hall).load_only(Hall.name))
  else:
    stmt = stmt.options(joinedload(Reservation.hall).load_only(Hall.name))

  if filters.status:
    stmt = stmt.where(Reservation.status == filters.status)
    total_records_stmt = total_records_stmt.where(Reservation.status == filters.status)

  total_res = await db.execute(total_records_stmt)
  total_records = total_res.scalar() or 0

  computed_fields = get_pagination_computed_fields(
    total_records=total_records,
    page=page
  )

  stmt = stmt.limit(settings.PAGINATION_LIMIT_PER_PAGE).offset(computed_fields.current_offset)

  result = await db.execute(stmt)
  result_items = result.scalars().all()
  data = [
    ReservationRead(
      id=item.id,
      user_id=item.user_id,
      user_name=item.user.name,
      hall_id=item.hall_id,
      hall_name=item.hall.name,
      status=item.status.value if hasattr(item.status, 'value') else item.status,
      reservation_date=item.reservation_date,
    )
    for item in result_items
  ]

  return PaginationCRUD(
    items=list(data),
    total=total_records,
    per_page=settings.PAGINATION_LIMIT_PER_PAGE,
    pages=computed_fields.pages,
    current_page=computed_fields.current_page
  )

async def crud_finish_reservations(*, db: AsyncSession):
  now = date.today()

  stmt = (
    update(Reservation)
    .where(
      Reservation.status == ReservationStatus.CONFIRMED,
      Reservation.reservation_date < now
    )
    .values(status=ReservationStatus.FINISHED)
  )

  await db.execute(stmt)
