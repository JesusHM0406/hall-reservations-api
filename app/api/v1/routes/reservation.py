from fastapi import APIRouter, HTTPException, status
from app.api.deps import DBDep
from app.schemas.reservation import ReservationRead, ReservationCreate
from app.services.reservation import (
  service_create_new_reservation
)


router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_reservation(reservation: ReservationCreate, db: DBDep) -> ReservationRead:
  try:
    return await service_create_new_reservation(db, reservation.user_id, reservation.hall_id, reservation.reservation_date)
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
