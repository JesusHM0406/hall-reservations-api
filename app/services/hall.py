from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import ErrorMessages
from app.crud.hall import (
  crud_create_new_hall,
  crud_get_all_halls,
  crud_get_hall_by_id,
  crud_get_hall_by_name,
  crud_search_halls,
  crud_update_hall,
  crud_update_hall_availability,
)
from app.crud.reservation import crud_has_confirmed_reservations
from app.exceptions.exceptions import ConflictError, NotFoundError
from app.schemas.filters.hall import HallFilters
from app.schemas.hall import HallRead, HallSearchResponse
from app.utils.pagination import Pagination, get_pagination


async def service_create_new_hall(
  *,
  db: AsyncSession,
  name: str,
  description: str,
  is_available: bool
) -> HallRead:
  # Trim and validate name (schema validation should have already done this, but defense in depth)
  name = name.strip()
  description = description.strip()
  
  if not name:
    raise ConflictError(ErrorMessages.EMPTY_HALL_NAME)
  
  if not description:
    raise ConflictError(ErrorMessages.EMPTY_HALL_DESCRIPTION)

  hall = await crud_get_hall_by_name(db=db, name=name)

  if hall:
    raise ConflictError(ErrorMessages.DUPLICATED_HALL_NAME)

  created_hall = await crud_create_new_hall(
    db=db,
    name=name,
    description=description,
    is_available=is_available
  )

  await db.flush()

  return HallRead(
    id=created_hall.id,
    name=name,
    description=description,
    is_available=is_available
  )

async def service_get_hall_by_id(*, db: AsyncSession, id: int) -> HallRead:
  hall = await crud_get_hall_by_id(db=db, id=id)

  if not hall:
    raise NotFoundError(ErrorMessages.HALL_NOT_FOUND)

  return HallRead(
    id=hall.id,
    name=hall.name,
    description=hall.description,
    is_available=hall.is_available
  )

async def service_get_hall_by_name(*, db: AsyncSession, name: str) -> HallRead:
  hall = await crud_get_hall_by_name(db=db, name=name)

  if not hall:
    raise NotFoundError(ErrorMessages.HALL_NOT_FOUND)

  return HallRead(
    id=hall.id,
    name=hall.name,
    description=hall.description,
    is_available=hall.is_available
  )

async def service_update_hall(
  *,
  db: AsyncSession,
  name: str | None,
  description: str | None,
  is_available: bool | None,
  id: int
) -> HallRead:
  hall = await crud_get_hall_by_id(db=db, id=id)

  if not hall:
    raise NotFoundError(ErrorMessages.HALL_NOT_FOUND)

  # Trim strings if provided
  if name is not None:
    name = name.strip()
    if not name:
      raise ConflictError(ErrorMessages.EMPTY_HALL_NAME)
  
  if description is not None:
    description = description.strip()
    if not description:
      raise ConflictError(ErrorMessages.EMPTY_HALL_DESCRIPTION)

  # Check if name is being updated and if it already exists for another hall
  if name and name != hall.name:
    existing_hall = await crud_get_hall_by_name(db=db, name=name)
    if existing_hall:
      raise ConflictError(ErrorMessages.DUPLICATED_HALL_NAME)

  # Check if hall is being disabled and has confirmed reservations
  if is_available is not None and not is_available and hall.is_available:
    # Only check if we're actually disabling (changing from True to False)
    has_confirmed = await crud_has_confirmed_reservations(db=db, hall_id=id)
    if has_confirmed:
      raise ConflictError(ErrorMessages.HALL_HAS_CONFIRMED_RESERVATIONS)

  updated_hall = await crud_update_hall(
    hall=hall,
    name=name,
    description=description,
    is_available=is_available
  )

  return HallRead(
    id=updated_hall.id,
    name=updated_hall.name,
    description=updated_hall.description,
    is_available=updated_hall.is_available
  )

async def service_update_hall_availability(
  *,
  db: AsyncSession,
  id: int,
  is_available: bool
) -> HallRead:
  hall = await crud_get_hall_by_id(db=db, id=id)

  if not hall:
    raise NotFoundError(ErrorMessages.HALL_NOT_FOUND)

  # Check if hall is being disabled and has confirmed reservations
  if not is_available and hall.is_available:
    # Only check if we're actually disabling (changing from True to False)
    has_confirmed = await crud_has_confirmed_reservations(db=db, hall_id=id)
    if has_confirmed:
      raise ConflictError(ErrorMessages.HALL_HAS_CONFIRMED_RESERVATIONS)

  updated_hall = await crud_update_hall_availability(
    hall=hall,
    is_available=is_available
  )

  return HallRead(
    id=updated_hall.id,
    name=updated_hall.name,
    is_available=updated_hall.is_available,
    description=updated_hall.description
  )

async def service_get_all_halls(
  *,
  db: AsyncSession,
  page: int,
  filters: HallFilters
) -> Pagination[HallRead]:
  result = await crud_get_all_halls(db=db, page=page, filters=filters)

  pagination = get_pagination(pagination=result, page=page)

  return pagination

async def service_search_halls(
  *,
  db: AsyncSession,
  search_query: str
) -> List[HallSearchResponse]:
  result = await crud_search_halls(db=db, search_query=search_query)

  data: list[HallSearchResponse] = [
    HallSearchResponse(
      id=row[0].id,
      name=row[0].name
    )
    for row in result
  ]

  return data
