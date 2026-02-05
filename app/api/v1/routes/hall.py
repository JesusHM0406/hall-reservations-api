from fastapi import APIRouter

from app.api.deps import DBDep
from app.schemas.hall import HallCreate, HallRead, HallUpdate
from app.services.hall import (
  service_create_new_hall,
  service_delete_hall,
  service_get_all_halls,
  service_get_hall_by_id,
  service_get_hall_by_name,
  service_update_hall,
)

router = APIRouter()

@router.post("/")
async def create_new_hall(db: DBDep, hall: HallCreate) -> HallRead:
  async with db.begin():
    return await service_create_new_hall(db, hall.name, hall.description, hall.is_available)

@router.get("/")
async def get_hall_by_name(name: str, db: DBDep) -> HallRead:
  async with db.begin():
    return await service_get_hall_by_name(db, name)

@router.get("/all")
async def get_all_halls(db: DBDep) -> list[HallRead]:
  async with db.begin():
    return await service_get_all_halls(db)

@router.get("/{hall_id}")
async def get_hall_by_id(hall_id: int, db: DBDep) -> HallRead:
  async with db.begin():
    return await service_get_hall_by_id(db, hall_id)

@router.patch("/{hall_id}")
async def update_hall(hall_id: int, hall: HallUpdate, db: DBDep) -> HallRead:
  async with db.begin():
    return await service_update_hall(db, hall.name, hall.description, hall.is_available, hall_id)

@router.delete("/{hall_id}", status_code=204)
async def delete_hall(hall_id: int, db: DBDep):
  async with db.begin():
    await service_delete_hall(db, hall_id)
