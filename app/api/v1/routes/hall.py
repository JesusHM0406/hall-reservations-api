from fastapi import APIRouter, HTTPException

from app.api.deps import DBDep
from app.schemas.hall import HallCreate, HallRead
from app.services.hall import service_create_new_hall, service_get_hall_by_name

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
