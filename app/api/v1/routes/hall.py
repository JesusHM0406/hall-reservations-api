from fastapi import APIRouter, HTTPException

from app.api.deps import DBDep
from app.schemas.hall import HallCreate, HallRead, HallUpdate
from app.services.hall import service_create_new_hall, service_delete_hall, service_get_hall_by_id, service_get_hall_by_name, service_update_hall

router = APIRouter()

@router.post("/")
async def create_new_hall(db: DBDep, hall: HallCreate) -> HallRead:
  try:
    new_hall = await service_create_new_hall(db, hall.name, hall.description, hall.is_available)
  except ValueError as e:
    raise HTTPException(status_code=409, detail=f"{e}")

  return new_hall

@router.get("/")
async def get_hall_by_name(name: str, db: DBDep) -> HallRead:
  try:
    hall = await service_get_hall_by_name(db, name)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=f"{e}")

  return hall

@router.get("/{hall_id}")
async def get_hall_by_id(hall_id: int, db: DBDep) -> HallRead:
  try:
    hall = await service_get_hall_by_id(db, hall_id)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=f"{e}")

  return hall

@router.patch("/{hall_id}")
async def update_hall(hall_id: int, hall: HallUpdate, db: DBDep) -> HallRead:
  try:
    updated_hall = await service_update_hall(db, hall.name, hall.description, hall.is_available, hall_id)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=f"{e}")

  return updated_hall

@router.delete("/{hall_id}", status_code=204)
async def delete_hall(hall_id: int, db: DBDep):
  try:
    await service_delete_hall(db, hall_id)
  except ValueError as e:
    raise HTTPException(status_code=404, detail=f"{e}")

  return
