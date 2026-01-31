from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.hall import crud_get_hall_by_id
from app.crud.reservation import crud_create_new_reservation
from app.crud.user import crud_get_user_by_id
from app.schemas.reservation import ReservationRead


async def service_create_new_reservation(db: AsyncSession, user_id: int, hall_id: int, reservation_date: date):
  async with db.begin():
    today = date.today()
    if reservation_date < today or reservation_date == today:
      raise ValueError("The date is invalid; it must be at least one day after the current date.")

    user = await crud_get_user_by_id(db, user_id)
    if not user:
      raise ValueError("The user doen't exist.")

    hall = await crud_get_hall_by_id(db, hall_id)
    if not hall:
      raise ValueError("The hall doen't exist.")

    try:
      reservation = await crud_create_new_reservation(db, user_id, hall_id, reservation_date)
      await db.flush()

      return ReservationRead(id=reservation.id, user_id=user_id, user_name=user.name, hall_id=hall_id, hall_name=hall.name, status=reservation.status, reservation_date=reservation.reservation_date)
    except IntegrityError:
      raise ValueError("There's already an active reservation in that date.")
