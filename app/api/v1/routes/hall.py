from fastapi import APIRouter

from app.api.deps import AdminDep, DBDep
from app.schemas.hall import HallCreate, HallRead, HallUpdate, HallUpdateAvailability
from app.services.hall import (
  service_create_new_hall,
  service_get_all_hall_paginated,
  service_get_all_halls,
  service_get_hall_by_id,
  service_get_hall_by_name,
  service_update_hall,
  service_update_hall_availability,
)
from app.utils.pagination_response import PaginationResponse

router = APIRouter()

@router.post("/")
async def create_new_hall(db: DBDep, admin: AdminDep, hall: HallCreate) -> HallRead:
  async with db.begin():
    return await service_create_new_hall(db, hall.name, hall.description, hall.is_available)

@router.get("/")
async def get_all_halls(db: DBDep) -> list[HallRead]:
  async with db.begin():
    return await service_get_all_halls(db)

@router.get("/paginated", response_model=PaginationResponse)
async def get_all_halls_paginated(db: DBDep, page: int = 1):
  return await service_get_all_hall_paginated(db, page)

@router.get("/{name}")
async def get_hall_by_name(db: DBDep, name: str) -> HallRead:
  async with db.begin():
    return await service_get_hall_by_name(db, name)

@router.get("/{id}")
async def get_hall_by_id(db: DBDep, id: int) -> HallRead:
  async with db.begin():
    return await service_get_hall_by_id(db, id)

@router.patch("/{id}")
async def update_hall(db: DBDep, admin: AdminDep, id: int, hall: HallUpdate) -> HallRead:
  async with db.begin():
    return await service_update_hall(db, hall.name, hall.description, hall.is_available, id)

@router.patch("/{id}/availability")
async def update_hall_availability(db: DBDep, admin: AdminDep, id: int, update: HallUpdateAvailability) -> HallRead:
  async with db.begin():
    return await service_update_hall_availability(db, id, update.is_available)
