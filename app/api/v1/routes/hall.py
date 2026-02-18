from fastapi import APIRouter
from starlette.status import HTTP_201_CREATED

from app.api.deps import AdminDep, DBDep
from app.schemas.hall import HallCreate, HallRead, HallUpdate, HallUpdateAvailability
from app.services.hall import (
  service_create_new_hall,
  service_get_all_halls,
  service_get_hall_by_id,
  service_get_hall_by_name,
  service_update_hall,
  service_update_hall_availability,
)
from app.utils.filters_metadata import HallFilterNames
from app.utils.pagination import Pagination

router = APIRouter()

@router.post("/", response_model=HallRead, status_code=HTTP_201_CREATED)
async def create_new_hall(
  db: DBDep,
  admin: AdminDep,
  hall: HallCreate
) -> HallRead:
  async with db.begin():
    return await service_create_new_hall(db, hall.name, hall.description, hall.is_available)

@router.get("/", response_model=Pagination)
async def get_all_halls(
  db: DBDep,
  page: int = 1,
  available_filter: bool | None = None
) -> Pagination:
  current_filters = {
    HallFilterNames.AVAILABLE.value: available_filter
  }

  return await service_get_all_halls(db, page, current_filters)

@router.get("/{name}", response_model=HallRead)
async def get_hall_by_name(db: DBDep, name: str) -> HallRead:
  async with db.begin():
    return await service_get_hall_by_name(db, name)

@router.get("/{id}", response_model=HallRead)
async def get_hall_by_id(db: DBDep, id: int) -> HallRead:
  async with db.begin():
    return await service_get_hall_by_id(db, id)

@router.patch("/{id}", response_model=HallRead)
async def update_hall(
  db: DBDep,
  admin: AdminDep,
  id: int,
  hall: HallUpdate
) -> HallRead:
  async with db.begin():
    return await service_update_hall(db, hall.name, hall.description, hall.is_available, id)

@router.patch("/{id}/availability", response_model=HallRead)
async def update_hall_availability(
  db: DBDep,
  admin: AdminDep,
  id: int,
  update: HallUpdateAvailability
) -> HallRead:
  async with db.begin():
    return await service_update_hall_availability(db, id, update.is_available)
