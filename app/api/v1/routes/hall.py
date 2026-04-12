from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from starlette.status import HTTP_201_CREATED

from app.api.deps import AdminDep, DBDep
from app.schemas.filters.hall import HallFilters
from app.schemas.hall import HallCreate, HallRead, HallSearchResponse, HallUpdate, HallUpdateAvailability
from app.services.hall import (
  service_create_new_hall,
  service_get_all_halls,
  service_get_hall_by_id,
  service_get_hall_by_name,
  service_search_halls,
  service_update_hall,
  service_update_hall_availability,
)
from app.utils.pagination import Pagination

router = APIRouter()

@router.post("/", response_model=HallRead, status_code=HTTP_201_CREATED)
async def create_new_hall(
  db: DBDep,
  admin: AdminDep,
  hall: HallCreate
) -> HallRead:
  return await service_create_new_hall(
    db=db,
    name=hall.name,
    description=hall.description,
    is_available=hall.is_available
  )

@router.get("/", response_model=Pagination[HallRead])
async def get_all_halls(
  db: DBDep,
  filters: Annotated[HallFilters, Depends()],
  page: int = 1
) -> Pagination[HallRead]:
  return await service_get_all_halls(
    db=db,
    page=page,
    filters=filters
  )

@router.get("/search", response_model=List[HallSearchResponse])
async def search_halls(db: DBDep, q: Annotated[str, Query(min_length=2)]) -> List[HallSearchResponse]:
  return await service_search_halls(db=db, search_query=q)

@router.get("/by-name/{name}", response_model=HallRead)
async def get_hall_by_name(db: DBDep, name: str) -> HallRead:
  return await service_get_hall_by_name(db=db, name=name)

@router.get("/{id}", response_model=HallRead)
async def get_hall_by_id(db: DBDep, id: int) -> HallRead:
  return await service_get_hall_by_id(db=db, id=id)

@router.patch("/{id}", response_model=HallRead)
async def update_hall(
  db: DBDep,
  admin: AdminDep,
  id: int,
  hall: HallUpdate
) -> HallRead:
  return await service_update_hall(
    db=db,
    name=hall.name,
    description=hall.description,
    is_available=hall.is_available,
    id=id
  )

@router.patch("/{id}/availability", response_model=HallRead)
async def update_hall_availability(
  db: DBDep,
  admin: AdminDep,
  id: int,
  update: HallUpdateAvailability
) -> HallRead:
  return await service_update_hall_availability(
    db=db,
    id=id,
    is_available=update.is_available
  )
