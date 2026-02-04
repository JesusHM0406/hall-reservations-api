from fastapi import APIRouter, HTTPException, status
from app.api.deps import DBDep
from app.schemas.reservation import ReservationRead, ReservationCreate
from app.services.reservation import (
  service_create_new_reservation,
  service_get_all_reservations,
  service_get_reservation
)


router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_reservation(reservation: ReservationCreate, db: DBDep) -> ReservationRead:
  try:
    return await service_create_new_reservation(db, reservation.user_id, reservation.hall_id, reservation.reservation_date)
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{reservation_id}")
async def get_reservation(reservation_id: int, db: DBDep) -> ReservationRead:
  try:
    return await service_get_reservation(db, reservation_id)
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/")
async def get_all_reservations(db: DBDep) -> list[ReservationRead]:
  return await service_get_all_reservations(db)
