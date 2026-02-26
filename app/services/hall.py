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
from app.exceptions.exceptions import ConflictError, NotFoundError
from app.schemas.filters.hall import HallFilters, HallFilterLabels, HallFilterNames, HallStatusFilter
from app.schemas.hall import HallRead, HallSearchResponse
from app.utils.pagination import Pagination, get_pagination
from app.utils.pagination_filters import FilterFactory


async def service_create_new_hall(
  *,
  db: AsyncSession,
  name: str,
  description: str,
  is_available: bool
) -> HallRead:
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
) -> Pagination:
  hall_status_filter_dict: dict[str, str] = {}

  for status in HallStatusFilter:
    hall_status_filter_dict[status.value] = status.value.capitalize()

  hall_available_filters = [
    FilterFactory.select(
      name=HallFilterNames.STATUS.value,
      label=HallFilterLabels.STATUS.value,
      options=hall_status_filter_dict,
      current=filters.status
    )
  ]

  result = await crud_get_all_halls(db=db, page=page, filters=filters)

  pagination = get_pagination(pagination=result, page=page, available_filters=hall_available_filters)

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
      name=row[0].name,
      rank=row[1]
    )
    for row in result
  ]

  return data
