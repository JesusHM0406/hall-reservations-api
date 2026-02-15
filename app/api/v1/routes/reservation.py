from typing import Annotated

from fastapi import APIRouter, status, Depends
from app.api.deps import DBDep, get_current_active_admin, get_current_active_user
from app.models.reservation_status import ReservationStatus
from app.schemas.reservation import ReservationApprove, ReservationRead, ReservationCreate, ReservationUpdate
from app.schemas.user import UserComplete
from app.services.reservation import (
  service_create_new_reservation,
  service_get_all_reservations,
  service_get_all_reservations_by_user_id,
  service_get_all_reservations_by_hall_id,
  service_get_reservation,
  service_update_reservation_status
)


router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_reservation(reservation: ReservationCreate, db: DBDep) -> ReservationRead:
  async with db.begin():
    return await service_create_new_reservation(db, reservation.user_id, reservation.hall_id, reservation.reservation_date)

@router.get("/")
async def get_reservations(db: DBDep, user_id: int | None = None, hall_id: int | None = None) -> list[ReservationRead]:
  async with db.begin():
    if user_id:
      return await service_get_all_reservations_by_user_id(db, user_id)

    if hall_id:
      return await service_get_all_reservations_by_hall_id(db, hall_id)

    return await service_get_all_reservations(db)

@router.get("/{id}")
async def get_single_reservation(id: int, db: DBDep) -> ReservationRead:
  async with db.begin():
    return await service_get_reservation(db, id)

@router.patch("/{id}")
async def update_reservation_status(db: DBDep, user: Annotated[UserComplete, Depends(get_current_active_user)], update: ReservationUpdate, id: int) -> ReservationRead:
  async with db.begin():
    return await service_update_reservation_status(db, id, update.status, user.id)

@router.patch("/{id}/approve")
async def approve_reservation(db: DBDep, admin: Annotated[UserComplete, Depends(get_current_active_admin)], approve: ReservationApprove, id: int) -> ReservationRead:
  async with db.begin():
    return await service_update_reservation_status(db, id, ReservationStatus.CONFIRMED.value, approve.user_id)
