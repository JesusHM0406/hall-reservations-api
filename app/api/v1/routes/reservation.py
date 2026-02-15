from fastapi import APIRouter, status

from app.api.deps import AdminDep, DBDep, UserDep
from app.models.reservation_status import ReservationStatus
from app.schemas.reservation import (
  ReservationCreate,
  ReservationRead,
)
from app.services.reservation import (
  service_create_new_reservation,
  service_get_all_reservations,
  service_get_all_reservations_by_hall_id,
  service_get_all_reservations_by_user_id,
  service_get_reservation,
  service_update_reservation_status,
)

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_reservation(reservation: ReservationCreate, user: UserDep, db: DBDep) -> ReservationRead:
  async with db.begin():
    return await service_create_new_reservation(db, user.id, reservation.hall_id, reservation.reservation_date)

@router.get("/")
async def get_reservations(db: DBDep, admin: AdminDep, user_id: int | None = None, hall_id: int | None = None) -> list[ReservationRead]:
  async with db.begin():
    if user_id:
      return await service_get_all_reservations_by_user_id(db, user_id)

    if hall_id:
      return await service_get_all_reservations_by_hall_id(db, hall_id)

    return await service_get_all_reservations(db)

@router.get("/{id}")
async def get_single_reservation(id: int, admin: AdminDep, db: DBDep) -> ReservationRead:
  async with db.begin():
    return await service_get_reservation(db, id)

@router.patch("/{id}/finish")
async def finish_reservation(db: DBDep, user: UserDep, id: int) -> ReservationRead:
  async with db.begin():
    return await service_update_reservation_status(db, id, ReservationStatus.FINISHED.value, user.id)

@router.patch("/{id}/cancel")
async def cancel_reservation(db: DBDep, user: UserDep, id: int) -> ReservationRead:
  async with db.begin():
    return await service_update_reservation_status(db, id, ReservationStatus.CANCELLED.value, user.id)
