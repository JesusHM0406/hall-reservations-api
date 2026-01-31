from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from datetime import date

from app.models.reservation import Reservation


async def crud_create_new_reservation(db: AsyncSession, user_id: int, hall_id: int, reservation_date: date):
  new_reservation = Reservation(user_id=user_id, hall_id=hall_id, reservation_date=reservation_date)
  db.add(new_reservation)
  return new_reservation

async def crud_get_reservation(db: AsyncSession, reservation_id: int):
  reservation = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
  return reservation.scalar_one_or_none()
