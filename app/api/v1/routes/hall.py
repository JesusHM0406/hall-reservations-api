from fastapi import APIRouter, HTTPException

from app.api.deps import DBDep
from app.schemas.hall import HallCreate, HallRead
from app.services.hall import service_create_new_hall

router = APIRouter()

@router.post("/")
async def create_new_hall(db: DBDep, hall: HallCreate) -> HallRead:
  try:
    new_hall = await service_create_new_hall(db, hall.name, hall.description, hall.is_available)
  except ValueError as e:
    raise HTTPException(status_code=409, detail=f"{e}")

  return new_hall
