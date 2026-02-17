from fastapi import APIRouter

from app.api.deps import DBDep
from app.schemas.hall import HallCreate, HallRead, HallUpdate, HallUpdateAvailability
from app.services.hall import (
  service_create_new_hall,
  service_delete_hall,
  service_get_all_halls,
  service_get_hall_by_id,
  service_get_hall_by_name,
  service_update_hall,
  service_update_hall_availability,
)

router = APIRouter()

@router.post("/")
async def create_new_hall(db: DBDep, hall: HallCreate) -> HallRead:
  async with db.begin():
    return await service_create_new_hall(db, hall.name, hall.description, hall.is_available)

@router.get("/")
async def get_all_halls(db: DBDep) -> list[HallRead]:
  async with db.begin():
    return await service_get_all_halls(db)

@router.get("/{name}")
async def get_hall_by_name(name: str, db: DBDep) -> HallRead:
  async with db.begin():
    return await service_get_hall_by_name(db, name)

@router.get("/{id}")
async def get_hall_by_id(id: int, db: DBDep) -> HallRead:
  async with db.begin():
    return await service_get_hall_by_id(db, id)

@router.patch("/{id}")
async def update_hall(id: int, hall: HallUpdate, db: DBDep) -> HallRead:
  async with db.begin():
    return await service_update_hall(db, hall.name, hall.description, hall.is_available, id)

@router.patch("/{id}/availability")
async def update_hall_availability(db: DBDep, id: int, update: HallUpdateAvailability) -> HallRead:
  async with db.begin():
    return await service_update_hall_availability(db, id, update.is_available)

@router.delete("/{id}", status_code=204)
async def delete_hall(id: int, db: DBDep):
  async with db.begin():
    await service_delete_hall(db, id)
