from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.api.deps import AdminDep, DBDep, UserDep
from app.models.reservation_status import ReservationStatus
from app.schemas.filters.reservation import ReservationFilters
from app.utils.pagination import Pagination
from app.schemas.reservation import (
  ReservationCreate,
  ReservationRead,
)
from app.services.reservation import (
  service_create_new_reservation,
  service_get_all_reservations,
  service_get_reservation,
  service_update_reservation_status,
)

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ReservationRead)
async def create_reservation(
  db: DBDep,
  reservation: ReservationCreate,
  user: UserDep
) -> ReservationRead:
  return await service_create_new_reservation(
    db=db,
    user_id=user.id,
    hall_id=reservation.hall_id,
    reservation_date=reservation.reservation_date
  )

@router.get("/", response_model=Pagination)
async def get_reservations(
  db: DBDep,
  admin: AdminDep,
  filters: Annotated[ReservationFilters, Depends()],
  page: int = 1
) -> Pagination:
  return await service_get_all_reservations(
    db=db,
    page=page,
    filters=filters,
    requesting_user=admin
  )

@router.get("/me", response_model=Pagination)
async def get_reservations_for_the_current_user(
  db: DBDep,
  user: UserDep,
  filters: Annotated[ReservationFilters, Depends()],
  page: int = 1
) -> Pagination:
  filters.user_name = user.name

  return await service_get_all_reservations(
    db=db,
    page=page,
    filters=filters,
    requesting_user=user
  )

@router.get("/{id}", response_model=ReservationRead)
async def get_single_reservation(
  db: DBDep,
  id: int,
  user: UserDep
) -> ReservationRead:
  return await service_get_reservation(db=db, id=id, user=user)

@router.patch("/{id}/finish", response_model=ReservationRead)
async def finish_reservation(
  db: DBDep,
  user: UserDep,
  id: int
) -> ReservationRead:
  return await service_update_reservation_status(
    db=db,
    reservation_id=id,
    new_status=ReservationStatus.FINISHED,
    user_id=user.id
  )

@router.patch("/{id}/cancel", response_model=ReservationRead)
async def cancel_reservation(
  db: DBDep,
  user: UserDep,
  id: int
) -> ReservationRead:
  return await service_update_reservation_status(
    db=db,
    reservation_id=id,
    new_status=ReservationStatus.CANCELLED,
    user_id=user.id
  )
