from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.hall import Hall
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User

async def crud_create_new_reservation(db: AsyncSession, user_id: int, hall_id: int, reservation_date: date):
  new_reservation = Reservation(user_id=user_id, hall_id=hall_id, reservation_date=reservation_date)
  db.add(new_reservation)
  return new_reservation

async def crud_get_reservation(db: AsyncSession, reservation_id: int):
  reservation = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
  return reservation.scalar_one_or_none()

async def crud_get_all_reservations(db: AsyncSession):
  stmt = (
    select(Reservation)
    .options(
      joinedload(Reservation.user).load_only(User.name),
      joinedload(Reservation.hall).load_only(Hall.name)
    )
  )

  result = await db.scalars(stmt)

  return result.all()

async def crud_get_all_reservations_by_user_id(db: AsyncSession, user_id: int):
  stmt = (
    select(Reservation)
    .options(
      joinedload(Reservation.hall).load_only(Hall.name)
    )
    .where(Reservation.user_id == user_id)
  )

  result = await db.scalars(stmt)

  return result.all()

async def crud_get_reservations_by_hall_id(db: AsyncSession, hall_id: int):
  stmt = select(Reservation).options(joinedload(Reservation.user).load_only(User.name)).where(Reservation.hall_id == hall_id)
  result = await db.scalars(stmt)
  return result.all()

async def crud_update_reservation_status(new_status: ReservationStatus, reservation: Reservation):
  reservation.status = new_status
  return reservation