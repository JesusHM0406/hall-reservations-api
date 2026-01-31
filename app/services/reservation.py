from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.hall import crud_get_hall_by_id
from app.crud.reservation import crud_create_new_reservation, crud_get_all_reservations, crud_get_all_reservations_by_user_id, crud_get_reservation
from app.crud.user import crud_get_user_by_id
from app.schemas.reservation import ReservationRead


async def service_create_new_reservation(db: AsyncSession, user_id: int, hall_id: int, reservation_date: date) -> ReservationRead:
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

async def service_get_reservation(db: AsyncSession, id: int) -> ReservationRead:
  async with db.begin():
    reservation = await crud_get_reservation(db, id)

    if not reservation:
      raise ValueError("Reservation not found.")

    user = await crud_get_user_by_id(db, reservation.user_id)
    if not user:
    # This is obviously provisional.
      raise ValueError("It appears the user was deleted.")

    hall = await crud_get_hall_by_id(db, reservation.hall_id)
    if not hall:
    # The same
      raise ValueError("Hall not found.")

  return ReservationRead(id=reservation.id, user_id=reservation.user_id, user_name=user.name, hall_id=reservation.hall_id, hall_name=hall.name, status=reservation.status, reservation_date=reservation.reservation_date)

async def service_get_all_reservations(db: AsyncSession):
  async with db.begin():
    result = await crud_get_all_reservations(db)

  # This might fail because I'm currently performing a "hard delete" of users.
  data = [ReservationRead(id=reservation.id, user_id=reservation.user_id, user_name=reservation.user.name, hall_id=reservation.hall_id, hall_name=reservation.hall.name, status=reservation.status, reservation_date=reservation.reservation_date) for reservation in result]

  return data

async def service_get_all_reservations_by_user_id(db: AsyncSession, user_id: int):
  async with db.begin():
    user = await crud_get_user_by_id(db, user_id)

    if not user:
      raise ValueError("User not found.")

    result = await crud_get_all_reservations_by_user_id(db, user_id)

  # Perhaps I can remove the "joinedload" that retrieves the username because I am currently retrieving the user.
  data = [ReservationRead(id=reservation.id, user_id=reservation.user_id, user_name=reservation.user.name, hall_id=reservation.hall_id, hall_name=reservation.hall.name, status=reservation.status, reservation_date=reservation.reservation_date) for reservation in result]

  return data
