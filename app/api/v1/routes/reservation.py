from fastapi import APIRouter, HTTPException, status
from app.api.deps import DBDep
from app.schemas.reservation import ReservationRead, ReservationCreate, ReservationUpdate
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
  try:
    return await service_create_new_reservation(db, reservation.user_id, reservation.hall_id, reservation.reservation_date)
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/")
async def get_reservations(db: DBDep, user_id: int | None = None, hall_id: int | None = None) -> list[ReservationRead]:
  try:
    if user_id:
      return await service_get_all_reservations_by_user_id(db, user_id)

    if hall_id:
      return await service_get_all_reservations_by_hall_id(db, hall_id)

    return await service_get_all_reservations(db)
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{reservation_id}")
async def get_single_reservation(reservation_id: int, db: DBDep) -> ReservationRead:
  try:
    return await service_get_reservation(db, reservation_id)
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.patch("/{reservation_id}")
async def update_reservation_status(db: DBDep, update: ReservationUpdate, reservation_id: int) -> ReservationRead:
  try:
    return await service_update_reservation_status(db, reservation_id, update.status, update.user_id)
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
