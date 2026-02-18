from fastapi import APIRouter, status

from app.api.deps import AdminDep, DBDep, UserDep
from app.models.reservation_status import ReservationStatus
from app.utils.filters_metadata import ReservationFilterNames
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
  async with db.begin():
    return await service_create_new_reservation(db, user.id, reservation.hall_id, reservation.reservation_date)

@router.get("/", response_model=Pagination)
async def get_reservations(
  db: DBDep,
  admin: AdminDep,
  page: int = 1,
  user_id: int | None = None,
  hall_id: int | None = None
) -> Pagination:
  filters = {
    ReservationFilterNames.USER.value: user_id,
    ReservationFilterNames.HALL.value: hall_id
  }

  async with db.begin():
    return await service_get_all_reservations(db, page, filters)

@router.get("/{id}", response_model=ReservationRead)
async def get_single_reservation(
  db: DBDep,
  id: int,
  admin: AdminDep
) -> ReservationRead:
  async with db.begin():
    return await service_get_reservation(db, id)

@router.patch("/{id}/finish", response_model=ReservationRead)
async def finish_reservation(
  db: DBDep,
  user: UserDep,
  id: int
) -> ReservationRead:
  async with db.begin():
    return await service_update_reservation_status(db, id, ReservationStatus.FINISHED.value, user.id)

@router.patch("/{id}/cancel", response_model=ReservationRead)
async def cancel_reservation(
  db: DBDep,
  user: UserDep,
  id: int
) -> ReservationRead:
  async with db.begin():
    return await service_update_reservation_status(db, id, ReservationStatus.CANCELLED.value, user.id)
